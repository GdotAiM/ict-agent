"""
autorun.py — Scheduled ICT agent scans.

Triggers:
  - Pre-London    06:55 UTC (daily, Mon-Fri)
  - London Open   07:00 UTC (daily, Mon-Fri)
  - Pre-NY        12:25 UTC (daily, Mon-Fri)
  - NY Open       12:30 UTC (daily, Mon-Fri)
  - Hourly        during active sessions (07:00-16:00 UTC)

Usage:
  python autorun.py           # start scheduler (blocking)
  python autorun.py --once    # run one scan now and exit
  python autorun.py --latest  # show last session results
"""
import sys
import os
import io
import json
import glob
import argparse
from datetime import datetime, timezone

# Force UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

os.chdir(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(override=True)

# Fix SSL certificate verification on Windows (same patch as main.py)
for _k in ('SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'):
    os.environ.pop(_k, None)
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
try:
    import httpx
    _orig_create = httpx._config.create_ssl_context
    def _fixed_create_ssl_context(verify=True, cert=None, trust_env=True):
        if isinstance(verify, bool) and verify:
            return ssl._create_unverified_context()
        return _orig_create(verify=verify, cert=cert, trust_env=trust_env)
    httpx._config.create_ssl_context = _fixed_create_ssl_context
except Exception:
    pass
try:
    import httpcore
    _orig_httpcore = getattr(httpcore, '_ssl', None)
    if _orig_httpcore:
        _orig_ctx = getattr(_orig_httpcore, 'create_ssl_context', None)
        if _orig_ctx:
            def _fixed_httpcore_ssl(*a, **kw):
                return ssl._create_unverified_context()
            _orig_httpcore.create_ssl_context = _fixed_httpcore_ssl
except Exception:
    pass

from agent.runtime import run_cycle
from memory.store import init_db, get_recent_context, log_analysis
from harness.chained_loop import _detect_compression
from harness.kernel import build_default_kernel
from harness.context import RunContext


WATCHLIST = ['XAUUSD', 'NAS100', 'EURUSD=X', 'GBPUSD=X']


def run_scan() -> dict:
    """Run full ICT chain on all symbols. Returns {symbol: result_summary}."""
    init_db()
    kernel = build_default_kernel()
    ctx = RunContext()
    results = {}

    print(f"\n{'='*65}")
    print(f"  ICT SCAN — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*65}\n")

    for sym in WATCHLIST:
        try:
            result = run_cycle(sym, mode='chained')
            # Extract key fields — use LAST occurrence of each pattern (latest stage wins)
            import re
            decisions = re.findall(r'DECISION:\s*(\w+)', result)
            confidences = re.findall(r'CONFLUENCE_SCORE:\s*(\d)', result)
            prices = re.findall(r'Price at ([\d.]+)', result)
            trends = re.findall(r'BIAS:\s*(\w+)', result)

            decision = decisions[-1] if decisions else '?'
            confluence = confidences[-1] if confidences else '?'
            price = prices[-1] if prices else '?'
            trend = trends[-1] if trends else '?'
            markers = [kw for kw in ['PRE-SWEEP', 'JUDAS', 'COMPRESSION', 'TRADE'] if kw in result]

            results[sym] = {
                'decision': decision,
                'confluence': confluence,
                'price': price,
                'trend': trend,
                'markers': markers,
                'raw': result,
            }

            marker_str = ' '.join(markers) + (' ' if markers else '')
            print(f"  {sym:<10} | price={price:>10} | conf={confluence}/4 | {decision:<10}{marker_str}")

        except Exception as e:
            print(f"  {sym:<10} | ERR: {str(e)[:60]}")
            results[sym] = {'decision': '?', 'error': str(e)}

    # Live compression check
    print(f"\n{'─'*65}")
    print("  LIVE COMPRESSION / PROXIMITY:")
    for sym in WATCHLIST:
        r = results.get(sym, {})
        if 'error' in r:
            continue
        try:
            pd = kernel.tools['get_pd_array'].handler({'symbol': sym, 'timeframe': 'HTF'}, ctx)
            ms_tool = kernel.tools['get_market_structure'].handler({'symbol': sym, 'timeframe': 'HTF'}, ctx)
            liq = kernel.tools['get_liquidity_pools'].handler({'symbol': sym, 'timeframe': 'HTF'}, ctx)
            price = pd.get('current_price', 0)
            ssl = sorted([l[1] for l in liq.get('ssl', {}).get('raw_lows', []) if len(l) > 1])
            nearest_ssl = ssl[-1] if ssl else 0
            dist_pct = abs(price - nearest_ssl) / nearest_ssl * 100 if nearest_ssl else 999
            comp = _detect_compression(ms_tool.get('swing_lows', []), ms_tool.get('swing_highs', []),
                                       price, nearest_liquidity=nearest_ssl)
            alert = comp.get('sweep_alert')
            status = "⚠️  ALERT" if alert else ("near" if dist_pct < 3 else "clear")
            print(f"    {sym:<10} | {price:>10} | SSL={nearest_ssl:>10} ({dist_pct:+5.1f}%) | comp={comp['ratio']:.1f}x | {status}")
        except Exception:
            pass

    # Journal each result
    for sym, r in results.items():
        if 'error' in r:
            continue
        trend = r.get('trend', 'bearish').lower()
        zone = 'discount'  # simplified; could parse from narrative
        in_kz = False
        # Check kill zone
        try:
            kz = kernel.tools['get_kill_zone'].handler({}, ctx)
            in_kz = kz.get('in_kill_zone', False)
        except Exception:
            pass
        dec = r.get('decision', 'no_setup').lower()
        narrative = f"Scan at {datetime.now(timezone.utc).strftime('%H:%M')} UTC. {trend.upper()} bias. "
        if r.get('markers'):
            narrative += ' | '.join(r['markers']) + '. '
        narrative += f"Decision: {dec}."
        log_analysis(symbol=sym, trend=trend, zone=zone,
                     in_kill_zone=in_kz, decision=dec, narrative=narrative)

    return results


def show_latest():
    """Show the most recent result for each symbol."""
    init_db()
    print(f"\n{'='*65}")
    print("  LATEST RESULTS")
    print(f"{'='*65}\n")
    for sym in WATCHLIST:
        ctx = get_recent_context(sym, limit=1)
        if ctx['recent_analyses']:
            a = ctx['recent_analyses'][0]
            print(f"  {sym:<12} | {a['ts'][:16]} | {a['trend']:>8s} | {a['zone']:>8s} | {a['decision']}")
        else:
            print(f"  {sym:<12} | no journal entry")
    print()


def main():
    parser = argparse.ArgumentParser(description='ICT Agent — scheduled scanner')
    parser.add_argument('--once', action='store_true', help='Run one scan and exit')
    parser.add_argument('--latest', action='store_true', help='Show latest results only')
    args = parser.parse_args()

    if args.latest:
        show_latest()
        return

    if args.once:
        run_scan()
        return

    # Scheduler mode
    from schedule import every, run_pending
    import time

    print(f" ICT Agent Autorun — starting scheduler")
    print(f" Watchlist: {', '.join(WATCHLIST)}")
    print(f" Triggers: pre-London 06:55, London 07:00, pre-NY 12:25, NY 12:30, hourly 07-16")
    print()

    every().day.at('06:55').do(run_scan).tag('pre-london')
    every().day.at('07:00').do(run_scan).tag('london-open')
    every().day.at('12:25').do(run_scan).tag('pre-ny')
    every().day.at('12:30').do(run_scan).tag('ny-open')
    every().hour.at(':00').do(run_scan).tag('hourly').during('07:00', '16:00')

    while True:
        try:
            run_pending()
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(30)


if __name__ == '__main__':
    main()
