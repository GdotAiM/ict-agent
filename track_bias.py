"""
Bias Accuracy Tracker — Records and evaluates daily bias calls.

Usage:
    python track_bias.py record          Record today's morning biases
    python track_bias.py evaluate        Evaluate yesterday's biases vs actual
    python track_bias.py report          Generate full accuracy report
"""
import sys
import os
import json
import sqlite3
from datetime import datetime, date, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(override=True)

DB_PATH = os.getenv("ICT_AGENT_DB", "ict_agent.db")


def get_conn():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_table(conn):
    """Ensure bias_accuracy table exists."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bias_accuracy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            morning_bias TEXT NOT NULL,
            morning_price REAL,
            evening_price REAL,
            actual_direction TEXT,
            bias_correct TEXT,
            price_move_pct REAL,
            analysis_entries INTEGER DEFAULT 0,
            bias_flips INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def record_morning_bias(symbol, bias, price=None, notes=""):
    """Record morning bias call for a symbol."""
    conn = get_conn()
    ensure_table(conn)

    today = date.today().isoformat()
    cursor = conn.cursor()

    # Check if already recorded
    cursor.execute(
        "SELECT id FROM bias_accuracy WHERE date=? AND symbol=?",
        (today, symbol)
    )
    if cursor.fetchone():
        print(f"  {symbol}: Already recorded for {today}")
        conn.close()
        return

    cursor.execute("""
        INSERT INTO bias_accuracy
        (date, symbol, morning_bias, morning_price, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (today, symbol, bias.upper(), price, notes))

    conn.commit()
    conn.close()
    print(f"  {symbol}: {bias.upper()} @ {price}")


def evaluate_daily_biases(target_date=None):
    """Evaluate yesterday's biases against actual price movement."""
    from tools.smc_data import get_candles_from_tv

    if target_date is None:
        target_date = (date.today() - timedelta(days=1)).isoformat()

    conn = get_conn()
    ensure_table(conn)
    cursor = conn.cursor()

    # Get morning biases
    cursor.execute("""
        SELECT symbol, morning_bias, morning_price
        FROM bias_accuracy
        WHERE date=? AND evening_price IS NULL
    """, (target_date,))
    rows = cursor.fetchall()

    if not rows:
        print(f"No un-evaluated biases found for {target_date}")
        conn.close()
        return

    print(f"Evaluating {len(rows)} biases for {target_date}...")
    print()

    results = []
    for row in rows:
        symbol = row['symbol']
        morning_bias = row['morning_bias']
        morning_price = row['morning_price']

        # Get evening price (latest close)
        df = get_candles_from_tv(symbol.replace('=X', ''), '1h')
        if df is None or len(df) < 2:
            print(f"  {symbol}: No price data")
            continue

        evening_price = float(df['close'].iloc[-1])
        price_move = ((evening_price - morning_price) / morning_price) * 100

        # Determine actual direction
        if abs(price_move) < 0.05:
            actual_dir = "NEUTRAL"
        elif price_move > 0:
            actual_dir = "BULLISH"
        else:
            actual_dir = "BEARISH"

        # Check accuracy
        if morning_bias == actual_dir:
            correct = "CORRECT"
        else:
            correct = "WRONG"

        # Update database
        cursor.execute("""
            UPDATE bias_accuracy
            SET evening_price = ?, actual_direction = ?, bias_correct = ?, price_move_pct = ?
            WHERE date = ? AND symbol = ?
        """, (evening_price, actual_dir, correct, price_move, target_date, symbol))

        results.append({
            'symbol': symbol,
            'morning_bias': morning_bias,
            'actual_direction': actual_dir,
            'correct': correct,
            'move': price_move,
            'morning': morning_price,
            'evening': evening_price,
        })

    conn.commit()
    conn.close()

    return results


def generate_report(target_date=None):
    """Generate full accuracy report."""
    from tools.smc_data import get_candles_from_tv

    if target_date is None:
        target_date = (date.today() - timedelta(days=1)).isoformat()

    conn = get_conn()
    ensure_table(conn)
    cursor = conn.cursor()

    # Get all biases for the date
    cursor.execute("""
        SELECT * FROM bias_accuracy
        WHERE date = ?
        ORDER BY symbol
    """, (target_date,))
    rows = cursor.fetchall()

    if not rows:
        print(f"No data found for {target_date}")
        print("Run 'record' first, then 'evaluate'")
        conn.close()
        return

    # Count stats
    total = len(rows)
    correct = sum(1 for r in rows if r['bias_correct'] == 'CORRECT')
    wrong = sum(1 for r in rows if r['bias_correct'] == 'WRONG')
    mixed = sum(1 for r in rows if r['bias_correct'] == 'MIXED')
    unevaluated = sum(1 for r in rows if r['bias_correct'] is None)

    accuracy = (correct / total * 100) if total > 0 else 0

    # Print report
    print("=" * 80)
    print(f"📊 BIAS ACCURACY REPORT — {target_date}")
    print("=" * 80)
    print()

    print("OVERALL METRICS")
    print("-" * 80)
    print(f"  Total Bias Calls:   {total}")
    print(f"  Correct:            {correct}")
    print(f"  Wrong:              {wrong}")
    print(f"  Mixed/Neutral:      {mixed}")
    print(f"  Unevaluated:        {unevaluated}")
    if total > 0 and unevaluated == 0:
        print(f"  Accuracy:           {accuracy:.1f}%")
    print()

    print("PER-SYMBOL BREAKDOWN")
    print("-" * 80)
    print()
    print("  Symbol      Morning   Evening     Move      Bias    Actual    Result")
    print("  ----------  --------  ----------  --------  ------  --------  --------")

    for row in rows:
        sym = row['symbol']
        morning = row['morning_price']
        evening = row['evening_price']
        move = row['price_move_pct']
        bias = row['morning_bias']
        actual = row['actual_direction']
        result = row['bias_correct']

        fmt_m = f"{morning:.4f}" if morning and morning < 100 else f"{morning:.2f}" if morning else "?"
        fmt_e = f"{evening:.4f}" if evening and evening < 100 else f"{evening:.2f}" if evening else "?"
        move_str = f"{move:+.3f}%" if move is not None else "?"
        result_str = f"✓ {result}" if result == "CORRECT" else f"✗ {result}" if result else "⏳ PENDING"

        print(f"  {sym:<6}  {fmt_m:>8}  {fmt_e:>10}  {move_str:>9}  {bias:<6}  {actual:<8}  {result_str}")

    print()

    if unevaluated == 0 and total > 0:
        print(f"FINAL SCORE: {correct}/{total} biases correct ({accuracy:.0f}%)")
        print()

    # Insights
    print("KEY INSIGHTS")
    print("-" * 80)
    print()

    if unevaluated > 0:
        print(f"  ⏳ {unevaluated} bias(es) still need evaluation (run 'evaluate' command)")
    else:
        # Analyze patterns
        correct_symbols = [r['symbol'] for r in rows if r['bias_correct'] == 'CORRECT']
        wrong_symbols = [r['symbol'] for r in rows if r['bias_correct'] == 'WRONG']

        if correct_symbols:
            print(f"  ✓ Strong performers: {', '.join(correct_symbols)}")
        if wrong_symbols:
            print(f"  ✗ Missed calls: {', '.join(wrong_symbols)}")

        # Check for flips
        print()
        print("  Note: Full flip analysis requires session log review.")

    print()
    print("=" * 80)

    conn.close()

    # Also generate markdown file
    generate_markdown_report(target_date, rows, total, correct, wrong, mixed, accuracy)


def generate_markdown_report(date_str, rows, total, correct, wrong, mixed, accuracy):
    """Generate markdown report file."""
    md_path = Path("sessions") / f"bias_accuracy_{date_str}.md"
    md_path.parent.mkdir(exist_ok=True)

    lines = [
        f"# Bias Accuracy Report — {date_str}",
        "",
        "## Overall Metrics",
        "",
        f"- **Total Calls:** {total}",
        f"- **Correct:** {correct}",
        f"- **Wrong:** {wrong}",
        f"- **Mixed/Neutral:** {mixed}",
        f"- **Accuracy:** {accuracy:.1f}%",
        "",
        "## Per-Symbol Breakdown",
        "",
        "| Symbol | Morning | Evening | Move | Bias | Actual | Result |",
        "|--------|---------|---------|------|------|--------|--------|",
    ]

    for row in rows:
        sym = row['symbol']
        morning = row['morning_price']
        evening = row['evening_price']
        move = row['price_move_pct']
        bias = row['morning_bias']
        actual = row['actual_direction']
        result = row['bias_correct']

        fmt_m = f"{morning:.4f}" if morning and morning < 100 else f"{morning:.2f}" if morning else "?"
        fmt_e = f"{evening:.4f}" if evening and evening < 100 else f"{evening:.2f}" if evening else "?"
        move_str = f"{move:+.3f}%" if move is not None else "?"
        result_str = "✓" if result == "CORRECT" else "✗" if result else "⏳"

        lines.append(f"| {sym} | {fmt_m} | {fmt_e} | {move_str} | {bias} | {actual} | {result_str} |")

    lines.extend([
        "",
        "## Key Insights",
        "",
        f"**Final Score: {correct}/{total} ({accuracy:.0f}%)**",
        "",
        "---",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*",
    ])

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\nMarkdown report saved: {md_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Track ICT agent bias accuracy')
    parser.add_argument('action', choices=['record', 'evaluate', 'report'],
                       help='Action to perform')
    parser.add_argument('--symbol', '-s', help='Symbol to record (e.g., EURUSD=X)')
    parser.add_argument('--bias', '-b', help='Bias direction: BULLISH or BEARISH')
    parser.add_argument('--price', '-p', type=float, help='Price at time of call')
    parser.add_argument('--date', '-d', help='Target date (YYYY-MM-DD), default: yesterday')
    parser.add_argument('--notes', '-n', help='Optional notes')

    args = parser.parse_args()

    # Import timedelta for evaluate
    from datetime import timedelta

    if args.action == 'record':
        if not args.symbol or not args.bias:
            print("Usage: python track_bias.py record --symbol EURUSD=X --bias BEARISH [--price 1.15] [--notes '...']")
            sys.exit(1)
        record_morning_bias(args.symbol, args.bias, args.price, args.notes or "")

    elif args.action == 'evaluate':
        target = args.date or (date.today() - timedelta(days=1)).isoformat()
        results = evaluate_daily_biases(target)
        if results:
            print(f"\nEvaluated {len(results)} biases for {target}")
            for r in results:
                status = "✓" if r['correct'] == 'CORRECT' else "✗"
                print(f"  {r['symbol']}: {r['morning_bias']} → {r['actual_direction']} {status} ({r['move']:+.3f}%)")

    elif args.action == 'report':
        target = args.date or (date.today() - timedelta(days=1)).isoformat()
        generate_report(target)


if __name__ == '__main__':
    main()
