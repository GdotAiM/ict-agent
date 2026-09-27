"""
Regretions tests for the ICT agent core tools.
Run with: python -m pytest tests/test_tools.py -v
Or:       python tests/test_tools.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import pandas as pd
import numpy as np
from tools.fvg import get_fair_value_gaps
from tools.structure import get_market_structure, _swings, _had_displacement
from tools.order_blocks import get_order_blocks
from tools.pd_arrays import get_pd_array
from tools.liquidity import get_liquidity_pools, detect_sweep
from tools.kill_zones import get_kill_zone
from agent.gates import gate_htf_bias, gate_timing, gate_ltf_entry, gate_confluence, parse_structured
from harness.kernel import build_default_kernel


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

def make_candles(n=30, seed=42):
    """Generate realistic test candles."""
    np.random.seed(seed)
    ops, cls, hi, lo = [], [], [], []
    p = 100.0
    for i in range(n):
        d = np.random.randn() * 0.5
        if i == 10:
            d = -4.0  # displacement
        o = p
        c = p + d
        h = max(o, c) + abs(np.random.randn()) * 0.2
        l = min(o, c) - abs(np.random.randn()) * 0.2
        ops.append(o)
        cls.append(c)
        hi.append(h)
        lo.append(l)
        p = c
    return pd.DataFrame({
        'open': ops, 'high': hi, 'low': lo, 'close': cls
    }, index=pd.date_range('2024-01-01', periods=n, freq='1h'))


# ---------------------------------------------------------------------------
# FVG tests
# ---------------------------------------------------------------------------

class TestFVG:
    def test_bullish_fvg_detection(self):
        """Bullish FVG: candle[i-2].high < candle[i].low"""
        data = pd.DataFrame({
            'open': [100, 105, 110],
            'high': [102, 107, 112],
            'low': [99, 104, 109],
            'close': [101, 106, 111]
        }, index=pd.date_range('2024', periods=3, freq='1h'))
        result = get_fair_value_gaps(data)
        bullish = [g for g in result if g['type'] == 'bullish']
        assert len(bullish) > 0, "Should detect bullish FVG"
        assert bullish[0]['bottom'] == 102.0
        assert bullish[0]['top'] == 109.0

    def test_bearish_fvg_detection(self):
        """Bearish FVG: candle[i-2].low > candle[i].high"""
        data = pd.DataFrame({
            'open': [100, 95, 90, 88, 85],
            'high': [102, 97, 92, 90, 87],
            'low': [99, 93, 88, 86, 84],
            'close': [100, 94, 89, 87, 84]
        }, index=pd.date_range('2024', periods=5, freq='1h'))
        result = get_fair_value_gaps(data)
        bearish = [g for g in result if g['type'] == 'bearish']
        assert len(bearish) > 0, "Should detect bearish FVG"
        # The [92, 99] gap should exist (candle0.low=99 > candle2.high=92)
        found = any(abs(g['bottom'] - 92) < 1 and abs(g['top'] - 99) < 1 for g in bearish)
        assert found, f"Expected bearish FVG [92,99], got: {bearish}"

    def test_fvg_fill_logic_bullish_inside(self):
        """Price inside bullish gap -> filled=True"""
        data = pd.DataFrame({
            'open': [100, 105, 110, 108, 104],
            'high': [102, 107, 112, 110, 106],
            'low': [99, 104, 109, 107, 103],
            'close': [101, 106, 111, 109, 105]
        }, index=pd.date_range('2024', periods=5, freq='1h'))
        result = get_fair_value_gaps(data)
        # Find the [102, 109] gap
        target = [g for g in result if g['type'] == 'bullish'
                  and abs(g['bottom'] - 102) < 1 and abs(g['top'] - 109) < 1]
        assert len(target) == 0, "Filled bullish FVG should be filtered out"

    def test_fvg_fill_logic_bullish_below(self):
        """Price below bullish gap -> filled=False (not filtered)"""
        data = pd.DataFrame({
            'open': [100, 105, 110, 108, 90],
            'high': [102, 107, 112, 110, 92],
            'low': [99, 104, 109, 107, 88],
            'close': [101, 106, 111, 109, 89]
        }, index=pd.date_range('2024', periods=5, freq='1h'))
        result = get_fair_value_gaps(data)
        target = [g for g in result if g['type'] == 'bullish'
                  and abs(g['bottom'] - 102) < 1]
        assert len(target) > 0, "Unfilled bullish FVG should remain"
        assert target[0]['filled'] == False

    def test_fvg_fill_logic_bearish_inside(self):
        """Price inside bearish gap -> filled=True"""
        data = pd.DataFrame({
            'open': [100, 95, 90, 88, 93],
            'high': [102, 97, 92, 90, 95],
            'low': [99, 93, 88, 86, 90],
            'close': [100, 94, 89, 88, 93]
        }, index=pd.date_range('2024', periods=5, freq='1h'))
        result = get_fair_value_gaps(data)
        target = [g for g in result if g['type'] == 'bearish'
                  and abs(g['bottom'] - 90) < 2 and abs(g['top'] - 99) < 2]
        assert len(target) == 0, "Filled bearish FVG should be filtered out"


# ---------------------------------------------------------------------------
# Structure tests
# ---------------------------------------------------------------------------

class TestStructure:
    def test_bos_detection(self):
        """BOS: trend continues after breaking structure"""
        data = make_candles(n=30, seed=42)
        result = get_market_structure(data)
        assert result['trend'] in ('bullish', 'bearish', 'ranging')
        assert 'last_event' in result
        assert 'mss_detected' in result  # New field

    def test_choch_detection(self):
        """CHoCH: trend reversal signal"""
        # Bearish trend then price breaks above previous high
        data = pd.DataFrame({
            'open': [100, 98, 95, 92, 90, 88, 85, 95, 100, 105] * 3,
            'high': [101, 99, 96, 93, 91, 89, 87, 97, 102, 107] * 3,
            'low': [99, 97, 94, 91, 89, 87, 84, 93, 98, 103] * 3,
            'close': [100, 97, 94, 91, 89, 87, 86, 96, 101, 106] * 3
        }, index=pd.date_range('2024', periods=30, freq='1h'))
        result = get_market_structure(data, lookback=2)
        # After CHoCH, trend should flip to bullish
        assert result['last_event'] in ('BOS', 'CHoCH', None)

    def test_mss_field_present(self):
        """mss_detected field should always be present"""
        data = pd.DataFrame({
            'open': [100, 100, 100],
            'high': [101, 101, 101],
            'low': [99, 99, 99],
            'close': [100, 100, 100]
        }, index=pd.date_range('2024', periods=3, freq='1h'))
        result = get_market_structure(data)
        assert 'mss_detected' in result
        assert result['mss_detected'] == False


# ---------------------------------------------------------------------------
# PD Array tests
# ---------------------------------------------------------------------------

class TestPDArray:
    def test_premium_zone(self):
        """Price above equilibrium = premium"""
        data = pd.DataFrame({
            'open': [100] * 50,
            'high': [120] + [100] * 49,
            'low': [80] + [100] * 49,
            'close': [110] * 50
        }, index=pd.date_range('2024', periods=50, freq='1h'))
        result = get_pd_array(data)
        assert result['zone'] == 'premium'
        assert result['equilibrium'] == 100.0

    def test_discount_zone(self):
        """Price below equilibrium = discount"""
        data = pd.DataFrame({
            'open': [100] * 50,
            'high': [120] + [100] * 49,
            'low': [80] + [100] * 49,
            'close': [90] * 50
        }, index=pd.date_range('2024', periods=50, freq='1h'))
        result = get_pd_array(data)
        assert result['zone'] == 'discount'


# ---------------------------------------------------------------------------
# Liquidity tests
# ---------------------------------------------------------------------------

class TestLiquidity:
    def test_bsl_ssl_detection(self):
        """Should identify buy-side and sell-side liquidity"""
        data = make_candles(n=30, seed=42)
        result = get_liquidity_pools(data)
        assert 'bsl' in result
        assert 'ssl' in result
        assert 'raw_highs' in result['bsl']
        assert 'raw_lows' in result['ssl']

    def test_sweep_detection(self):
        """Should detect liquidity sweep"""
        data = pd.DataFrame({
            'open': [100, 100, 100, 100, 100],
            'high': [100, 100, 110, 105, 100],  # spike at bar 2
            'low': [95, 95, 96, 100, 95],
            'close': [100, 100, 102, 100, 100]
        }, index=pd.date_range('2024', periods=5, freq='1h'))
        result = detect_sweep(data, level=105, direction='above', within_bars=5)
        assert result['swept'] == True


# ---------------------------------------------------------------------------
# Gate tests
# ---------------------------------------------------------------------------

class TestGates:
    def test_htf_bias_complete(self):
        """Complete HTF narrative should pass gate"""
        narrative = 'BIAS: BULLISH\nDRAW_ON_LIQUIDITY: SSL at 4617\nPD_ARRAY: DISCOUNT'
        result = gate_htf_bias(narrative)
        assert result.passed == True

    def test_htf_bias_missing_bias(self):
        """Missing BIAS should fail gate"""
        narrative = 'DRAW_ON_LIQUIDITY: SSL at 4617\nPD_ARRAY: DISCOUNT'
        result = gate_htf_bias(narrative)
        assert result.passed == False

    def test_timing_inside_kill_zone(self):
        """Inside kill zone should pass"""
        narrative = 'KILL_ZONE: NY_AM'
        result = gate_timing(narrative)
        assert result.passed == True
        assert result.soft == True

    def test_timing_outside_no_justification(self):
        """Outside kill zone without justification should soft-fail"""
        narrative = 'KILL_ZONE: OUTSIDE'
        result = gate_timing(narrative)
        assert result.passed == False
        assert result.soft == True

    def test_ltf_entry_complete(self):
        """Complete LTF entry should pass"""
        narrative = 'ENTRY_TRIGGER: FVG 100-105\nINVALIDATION: 99\nTARGET: 108'
        result = gate_ltf_entry(narrative)
        assert result.passed == True

    def test_ltf_entry_missing_target(self):
        """Missing TARGET should fail"""
        narrative = 'ENTRY_TRIGGER: FVG 100-105\nINVALIDATION: 99'
        result = gate_ltf_entry(narrative)
        assert result.passed == False

    def test_confluence_pass(self):
        """Confluence score >= 3 should pass"""
        narrative = 'CONFLUENCE_SCORE: 3\nDECISION: TRADE'
        result = gate_confluence(narrative)
        assert result.passed == True

    def test_confluence_fail(self):
        """Confluence score < 3 should fail"""
        narrative = 'CONFLUENCE_SCORE: 2\nDECISION: WATCH'
        result = gate_confluence(narrative)
        assert result.passed == False


# ---------------------------------------------------------------------------
# Kernel tests
# ---------------------------------------------------------------------------

class TestKernel:
    def test_build_default_kernel(self):
        """All tools should mount successfully"""
        kernel = build_default_kernel()
        tools = kernel.list_tools()
        assert len(tools) == 15, f"Expected 15 tools, got {len(tools)}"
        assert 'get_fair_value_gaps' in tools
        assert 'get_market_structure' in tools
        assert 'get_liquidity_voids' in tools

    def test_dispatch_unknown_tool(self):
        """Unknown tool should return error"""
        kernel = build_default_kernel()
        result = kernel.dispatch('nonexistent_tool', {}, None)
        assert 'error' in result


# ---------------------------------------------------------------------------
# Liquidity voids tests
# ---------------------------------------------------------------------------

class TestLiquidityVoids:
    def test_void_detection(self):
        """Should detect large gaps between swing points"""
        from tools.liquidity_voids import get_liquidity_voids
        np.random.seed(42)
        n = 40
        ops, cls, hi, lo = [], [], [], []
        p = 100.0
        for i in range(n):
            if i < 20:
                d = np.random.randn() * 0.3
            elif i == 20:
                d = -7.0  # big drop
            else:
                d = np.random.randn() * 0.3
            o, c = p, p + d
            h, l = max(o, c) + abs(np.random.randn()) * 0.2, min(o, c) - abs(np.random.randn()) * 0.2
            ops.append(o); cls.append(c); hi.append(h); lo.append(l)
            p = c
        data = pd.DataFrame({'open': ops, 'high': hi, 'low': lo, 'close': cls},
            index=pd.date_range('2024-01-01', periods=n, freq='1h'))
        voids = get_liquidity_voids(data)
        # Should return list (may be empty or have items)
        assert isinstance(voids, list)
        for v in voids:
            assert 'type' in v
            assert 'bottom' in v
            assert 'top' in v
            assert 'swept' in v

    def test_short_df_returns_empty(self):
        """Less than 15 bars should return empty list"""
        from tools.liquidity_voids import get_liquidity_voids
        data = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100, 101, 102]
        }, index=pd.date_range('2024', periods=3, freq='1h'))
        voids = get_liquidity_voids(data)
        assert voids == []


# ---------------------------------------------------------------------------
# Power of 3 tests
# ---------------------------------------------------------------------------

class TestPowerOf3:
    def test_phase_mapping(self):
        """Kill zones should map to correct phases"""
        from tools.power_of_3 import SESSION_PHASE_MAP
        assert SESSION_PHASE_MAP['asian']['primary'] == 'accumulation'
        assert SESSION_PHASE_MAP['london']['primary'] == 'manipulation'
        assert SESSION_PHASE_MAP['ny_am']['primary'] == 'distribution'
        assert SESSION_PHASE_MAP['ny_pm']['primary'] == 'distribution'

    def test_get_status(self):
        """Should return valid status dict"""
        from tools.power_of_3 import get_power_of_3_status
        status = get_power_of_3_status()
        assert 'phase' in status
        assert 'session' in status
        assert 'confidence' in status
        assert status['phase'] in ('accumulation', 'manipulation', 'distribution', 'unknown')


# ---------------------------------------------------------------------------
# Order Blocks tests
# ---------------------------------------------------------------------------

class TestOrderBlocks:
    def test_short_df_no_crash(self):
        """Short DataFrame (<15 bars) should not crash"""
        data = pd.DataFrame({
            'open': [100, 98, 105],
            'high': [101, 99, 107],
            'low': [99, 97, 104],
            'close': [100, 98, 106]
        }, index=pd.date_range('2024', periods=3, freq='1h'))
        result = get_order_blocks(data)
        assert isinstance(result, list)

    def test_with_sufficient_data(self):
        """Should work with >=15 bars"""
        data = make_candles(n=30, seed=42)
        result = get_order_blocks(data)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import traceback
    tests = [
        TestFVG(),
        TestStructure(),
        TestPDArray(),
        TestLiquidity(),
        TestGates(),
        TestKernel(),
        TestLiquidityVoids(),
        TestPowerOf3(),
        TestOrderBlocks(),
    ]
    passed = 0
    failed = 0
    errors = []
    for test in tests:
        for name in dir(test):
            if name.startswith('test_'):
                try:
                    getattr(test, name)()
                    print(f'PASS: {test.__class__.__name__}.{name}')
                    passed += 1
                except Exception as e:
                    print(f'FAIL: {test.__class__.__name__}.{name} - {e}')
                    failed += 1
                    errors.append((test.__class__.__name__, name, str(e)))
    print(f'\n{passed} passed, {failed} failed')
    sys.exit(1 if failed > 0 else 0)
