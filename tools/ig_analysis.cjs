#!/usr/bin/env node
/**
 * IG (Institutional Gravity) Analysis — Friday TGIF Wrap-Up
 * 
 * Runs a full ICT top-down chain on each instrument, then appends
 * the TGIF weekly-profile assessment. Use on Fridays after the main
 * scan completes:
 * 
 *   python ig_analysis.cjs NAS100
 *   python ig_analysis.cjs --all
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const AGENT_DIR = __dirname;
const NODE_BIN = process.execPath.replace('node.exe','').replace('Node\', '');
const NODE_CMD = process.platform === 'win32' ? 'node' : 'node';
const PYTHON = 'python';

// Symbol → TradingView broker prefix mapping
const TV_SYMBOLS = {
  NAS100: 'NAS100',
  SPY: 'SPY',
  XAUUSD: 'XAUUSD',
  EURUSD: 'EURUSD',
  GBPUSD: 'GBPUSD',
  DXY: 'DXY',
};

async function main() {
  const args = process.argv.slice(2);
  const allMode = args.includes('--all');
  const symbols = allMode
    ? Object.keys(TV_SYMBOLS)
    : args.filter(a => !a.startsWith('--'));

  if (symbols.length === 0 && !allMode) {
    console.error('Usage: python ig_analysis.cjs [SYMBOL ...]');
    console.error('       python ig_analysis.cjs --all');
    process.exit(1);
  }

  const results = {};
  for (const sym of symbols) {
    const tvSym = TV_SYMBOLS[sym];
    if (!tvSym) {
      console.error(`Unknown symbol: ${sym}`);
      continue;
    }
    console.log(`\n=== IG Analysis: ${sym} ===`);
    try {
      // Run the full ICT chain
      const cmd = `${PYTHON} "${path.join(AGENT_DIR, 'main.py')}" --chained ${sym}`;
      const out = execSync(cmd, { 
        cwd: AGENT_DIR,
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 120000,
      });
      results[sym] = { success: true, output: out };
      console.log(out);
    } catch (e) {
      results[sym] = { success: false, error: e.message };
      console.error(`Error running ${sym}: ${e.message}`);
    }
  }

  console.log('\n=== Summary ===');
  for (const [sym, r] of Object.entries(results)) {
    const status = r.success ? 'OK' : `ERR: ${r.error?.substring(0, 60)}`;
    console.log(`  ${sym}: ${status}`);
  }
}

main().catch(err => { console.error(err); process.exit(1); });
