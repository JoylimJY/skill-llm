import os
import json
import random
import string
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Create the crypto-self-learning skill directory structure ──────────────
skill_base = WORKSPACE / "skills" / "crypto-self-learning"
scripts_dir = skill_base / "scripts"
data_dir = skill_base / "data"

for d in [scripts_dir, data_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ── 2. Create the actual skill scripts ────────────────────────────────────────

# log_trade.py
log_trade_script = '''#!/usr/bin/env python3
"""Log a crypto trade with full context for self-learning analysis."""
import argparse
import json
import uuid
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"

def load_trades():
    if TRADES_FILE.exists():
        with open(TRADES_FILE) as f:
            return json.load(f)
    return {"trades": []}

def save_trades(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(TRADES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Log a crypto trade")
    parser.add_argument("--symbol", help="Trading pair (e.g. BTCUSDT)")
    parser.add_argument("--direction", choices=["LONG", "SHORT"], help="Trade direction")
    parser.add_argument("--entry", type=float, help="Entry price")
    parser.add_argument("--exit", type=float, help="Exit price")
    parser.add_argument("--pnl_percent", type=float, help="PnL percentage")
    parser.add_argument("--leverage", type=int, default=1, help="Leverage used")
    parser.add_argument("--reason", default="", help="Entry reason")
    parser.add_argument("--indicators", default="{}", help="JSON indicators at entry")
    parser.add_argument("--market_context", default="{}", help="JSON market context")
    parser.add_argument("--result", choices=["WIN", "LOSS"], help="Trade result")
    parser.add_argument("--notes", default="", help="Post-trade notes")
    parser.add_argument("--list", action="store_true", help="List recent trades")
    parser.add_argument("--last", type=int, default=20, help="Number of recent trades to show")
    parser.add_argument("--stats", action="store_true", help="Show summary stats")
    args = parser.parse_args()

    data = load_trades()

    if args.list:
        trades = data["trades"][-args.last:]
        if not trades:
            print("No trades logged yet.")
            return
        print(f"\\n{'ID':8} {'Symbol':10} {'Dir':6} {'Entry':10} {'Exit':10} {'PnL%':7} {'Result':6}")
        print("-" * 65)
        for t in trades:
            print(f"{t['id'][:8]:8} {t['symbol']:10} {t['direction']:6} "
                  f"{t['entry']:10.2f} {t['exit']:10.2f} {t['pnl_percent']:7.2f} {t['result']:6}")
        return

    if args.stats:
        trades = data["trades"]
        if not trades:
            print("No trades yet.")
            return
        wins = [t for t in trades if t["result"] == "WIN"]
        print(f"\\nTotal trades: {len(trades)}")
        print(f"Win rate: {len(wins)/len(trades)*100:.1f}%")
        print(f"Wins: {len(wins)}, Losses: {len(trades)-len(wins)}")
        total_pnl = sum(t["pnl_percent"] for t in trades)
        print(f"Total PnL: {total_pnl:.2f}%")
        return

    required = ["symbol", "direction", "entry", "exit", "pnl_percent", "result"]
    for field in required:
        if getattr(args, field) is None:
            print(f"ERROR: --{field} is required for logging a trade.")
            sys.exit(1)

    try:
        indicators = json.loads(args.indicators)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON for --indicators: {e}")
        sys.exit(1)

    try:
        market_context = json.loads(args.market_context)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON for --market_context: {e}")
        sys.exit(1)

    trade = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": args.symbol,
        "direction": args.direction,
        "entry": args.entry,
        "exit": args.exit,
        "pnl_percent": args.pnl_percent,
        "leverage": args.leverage,
        "reason": args.reason,
        "indicators": indicators,
        "market_context": market_context,
        "result": args.result,
        "notes": args.notes,
    }

    data["trades"].append(trade)
    save_trades(data)
    print(f"✅ Trade logged: {args.symbol} {args.direction} {args.result} ({args.pnl_percent:+.2f}%)")
    print(f"   Trade ID: {trade['id']}")
    print(f"   Total trades logged: {len(data['trades'])}")

if __name__ == "__main__":
    main()
'''

# analyze.py
analyze_script = '''#!/usr/bin/env python3
"""Analyze trade patterns to discover what works and what doesn\'t."""
import argparse
import json
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
TRADES_FILE = SCRIPT_DIR.parent / "data" / "trades.json"

def load_trades():
    if not TRADES_FILE.exists():
        print("No trades file found. Log some trades first.")
        return []
    with open(TRADES_FILE) as f:
        data = json.load(f)
    return data.get("trades", [])

def win_rate(trades):
    if not trades:
        return 0.0, 0
    wins = sum(1 for t in trades if t["result"] == "WIN")
    return wins / len(trades) * 100, len(trades)

def analyze(trades, min_trades=3):
    print(f"\\n{'='*60}")
    print(f"📊 TRADE ANALYSIS ({len(trades)} trades)")
    print(f"{'='*60}")

    # Overall
    wr, n = win_rate(trades)
    print(f"\\nOverall Win Rate: {wr:.1f}% (n={n})")

    # By direction
    print("\\n── By Direction ──")
    for direction in ["LONG", "SHORT"]:
        subset = [t for t in trades if t.get("direction") == direction]
        wr, n = win_rate(subset)
        if n > 0:
            print(f"  {direction}: {wr:.1f}% win rate (n={n})")

    # By symbol
    symbols = set(t.get("symbol") for t in trades)
    print("\\n── By Symbol ──")
    for sym in sorted(symbols):
        subset = [t for t in trades if t.get("symbol") == sym]
        wr, n = win_rate(subset)
        if n >= min_trades:
            print(f"  {sym}: {wr:.1f}% win rate (n={n})")

    # By RSI range (from indicators)
    print("\\n── By RSI Range ──")
    rsi_buckets = defaultdict(list)
    for t in trades:
        rsi = t.get("indicators", {}).get("rsi")
        if rsi is not None:
            if rsi < 30:
                rsi_buckets["RSI < 30 (oversold)"].append(t)
            elif rsi < 50:
                rsi_buckets["RSI 30-50"].append(t)
            elif rsi < 70:
                rsi_buckets["RSI 50-70"].append(t)
            else:
                rsi_buckets["RSI > 70 (overbought)"].append(t)
    for bucket, bucket_trades in sorted(rsi_buckets.items()):
        wr, n = win_rate(bucket_trades)
        if n >= min_trades:
            print(f"  {bucket}: {wr:.1f}% win rate (n={n})")

    # By leverage
    print("\\n── By Leverage ──")
    lev_buckets = defaultdict(list)
    for t in trades:
        lev = t.get("leverage", 1)
        if lev <= 3:
            lev_buckets["1-3x"].append(t)
        elif lev <= 10:
            lev_buckets["4-10x"].append(t)
        else:
            lev_buckets[">10x"].append(t)
    for bucket, bucket_trades in sorted(lev_buckets.items()):
        wr, n = win_rate(bucket_trades)
        if n >= min_trades:
            print(f"  Leverage {bucket}: {wr:.1f}% win rate (n={n})")

    # By day of week
    print("\\n── By Day of Week ──")
    day_buckets = defaultdict(list)
    for t in trades:
        day = t.get("market_context", {}).get("day")
        if day:
            day_buckets[day].append(t)
    for day, day_trades in sorted(day_buckets.items()):
        wr, n = win_rate(day_trades)
        if n >= min_trades:
            print(f"  {day.title()}: {wr:.1f}% win rate (n={n})")

    print(f"\\n{'='*60}\\n")

def main():
    parser = argparse.ArgumentParser(description="Analyze trade performance")
    parser.add_argument("--symbol", help="Filter by symbol")
    parser.add_argument("--direction", choices=["LONG", "SHORT"], help="Filter by direction")
    parser.add_argument("--min-trades", type=int, default=3, help="Minimum trades for a pattern")
    args = parser.parse_args()

    trades = load_trades()
    if not trades:
        return

    if args.symbol:
        trades = [t for t in trades if t.get("symbol") == args.symbol]
        print(f"Filtering by symbol: {args.symbol}")
    if args.direction:
        trades = [t for t in trades if t.get("direction") == args.direction]
        print(f"Filtering by direction: {args.direction}")

    analyze(trades, min_trades=args.min_trades)

if __name__ == "__main__":
    main()
'''

# generate_rules.py
generate_rules_script = '''#!/usr/bin/env python3
"""Generate actionable trading rules from trade history patterns."""
import json
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
TRADES_FILE = SCRIPT_DIR.parent / "data" / "trades.json"
RULES_FILE = SCRIPT_DIR.parent / "data" / "generated_rules.json"

def load_trades():
    if not TRADES_FILE.exists():
        print("No trades found. Log some trades first.")
        return []
    with open(TRADES_FILE) as f:
        return json.load(f).get("trades", [])

def win_rate(trades):
    if not trades:
        return 0.0
    return sum(1 for t in trades if t["result"] == "WIN") / len(trades) * 100

def generate_rules(trades, min_trades=3, avoid_threshold=40.0, prefer_threshold=65.0):
    rules = []

    # Direction rules
    for direction in ["LONG", "SHORT"]:
        subset = [t for t in trades if t.get("direction") == direction]
        if len(subset) >= min_trades:
            wr = win_rate(subset)
            if wr < avoid_threshold:
                rules.append({
                    "type": "AVOID",
                    "condition": f"{direction} trades",
                    "win_rate": round(wr, 1),
                    "n": len(subset),
                    "text": f"🚫 AVOID: {direction} trades (win rate: {wr:.0f}%, n={len(subset)})"
                })
            elif wr >= prefer_threshold:
                rules.append({
                    "type": "PREFER",
                    "condition": f"{direction} trades",
                    "win_rate": round(wr, 1),
                    "n": len(subset),
                    "text": f"✅ PREFER: {direction} trades (win rate: {wr:.0f}%, n={len(subset)})"
                })

    # RSI rules
    rsi_buckets = {
        "RSI < 30 (oversold)": [t for t in trades if t.get("indicators", {}).get("rsi", 50) < 30],
        "RSI > 70 (overbought)": [t for t in trades if t.get("indicators", {}).get("rsi", 50) > 70],
        "RSI 30-50": [t for t in trades if 30 <= t.get("indicators", {}).get("rsi", 50) < 50],
        "RSI 50-70": [t for t in trades if 50 <= t.get("indicators", {}).get("rsi", 50) <= 70],
    }
    for label, subset in rsi_buckets.items():
        if len(subset) >= min_trades:
            wr = win_rate(subset)
            if wr < avoid_threshold:
                rules.append({
                    "type": "AVOID",
                    "condition": label,
                    "win_rate": round(wr, 1),
                    "n": len(subset),
                    "text": f"🚫 AVOID: LONG when {label} (win rate: {wr:.0f}%, n={len(subset)})"
                })
            elif wr >= prefer_threshold:
                rules.append({
                    "type": "PREFER",
                    "condition": label,
                    "win_rate": round(wr, 1),
                    "n": len(subset),
                    "text": f"✅ PREFER: trades when {label} (win rate: {wr:.0f}%, n={len(subset)})"
                })

    # Leverage rules
    high_lev = [t for t in trades if t.get("leverage", 1) > 10]
    if len(high_lev) >= min_trades:
        wr = win_rate(high_lev)
        rule_type = "AVOID" if wr < avoid_threshold else ("PREFER" if wr >= prefer_threshold else "CAUTION")
        emoji = "🚫" if rule_type == "AVOID" else ("✅" if rule_type == "PREFER" else "⚠️")
        rules.append({
            "type": rule_type,
            "condition": "leverage > 10x",
            "win_rate": round(wr, 1),
            "n": len(high_lev),
            "text": f"{emoji} {rule_type}: Trades with leverage > 10x (win rate: {wr:.0f}%, n={len(high_lev)})"
        })

    # Day-of-week rules
    day_buckets = defaultdict(list)
    for t in trades:
        day = t.get("market_context", {}).get("day")
        if day:
            day_buckets[day].append(t)
    for day, subset in day_buckets.items():
        if len(subset) >= min_trades:
            wr = win_rate(subset)
            if wr < avoid_threshold:
                rules.append({
                    "type": "AVOID",
                    "condition": f"trading on {day}",
                    "win_rate": round(wr, 1),
                    "n": len(subset),
                    "text": f"🚫 AVOID: Trading on {day.title()} (win rate: {wr:.0f}%, n={len(subset)})"
                })
            elif wr >= prefer_threshold:
                rules.append({
                    "type": "PREFER",
                    "condition": f"trading on {day}",
                    "win_rate": round(wr, 1),
                    "n": len(subset),
                    "text": f"✅ PREFER: Trading on {day.title()} (win rate: {wr:.0f}%, n={len(subset)})"
                })

    # Symbol rules
    symbols = set(t.get("symbol") for t in trades)
    for sym in symbols:
        subset = [t for t in trades if t.get("symbol") == sym]
        if len(subset) >= min_trades:
            wr = win_rate(subset)
            if wr < avoid_threshold:
                rules.append({
                    "type": "AVOID",
                    "condition": f"{sym}",
                    "win_rate": round(wr, 1),
                    "n": len(subset),
                    "text": f"🚫 AVOID: Trading {sym} (win rate: {wr:.0f}%, n={len(subset)})"
                })

    return rules

def main():
    trades = load_trades()
    if not trades:
        return

    print(f"\\n🧠 GENERATING RULES FROM {len(trades)} TRADES")
    print("=" * 50)

    rules = generate_rules(trades)

    if not rules:
        print("Not enough data to generate reliable rules yet.")
        print("Need at least 3 trades in a pattern to generate a rule.")
        return

    print(f"\\nGenerated {len(rules)} rules:\\n")
    for rule in rules:
        print(f"  {rule[\'text\']}")

    # Save rules to file
    rules_data = {
        "generated_at": __import__(\'datetime\').datetime.utcnow().isoformat() + "Z",
        "total_trades_analyzed": len(trades),
        "rules": rules
    }
    RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RULES_FILE, "w") as f:
        json.dump(rules_data, f, indent=2)

    print(f"\\n✅ Rules saved to: {RULES_FILE}")
    print("\\nRun update_memory.py to apply these rules to your MEMORY.md")

if __name__ == "__main__":
    main()
'''

# update_memory.py
update_memory_script = '''#!/usr/bin/env python3
"""Apply learned rules to a MEMORY.md file."""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
RULES_FILE = SCRIPT_DIR.parent / "data" / "generated_rules.json"

SECTION_HEADER = "## 🧠 Learned Rules"

def load_rules():
    if not RULES_FILE.exists():
        print(f"ERROR: No rules file found at {RULES_FILE}")
        print("Run generate_rules.py first to generate rules.")
        sys.exit(1)
    with open(RULES_FILE) as f:
        return json.load(f)

def build_rules_section(rules_data):
    lines = []
    lines.append(SECTION_HEADER)
    lines.append(f"")
    lines.append(f"> Auto-generated from {rules_data[\'total_trades_analyzed\']} trades on {rules_data[\'generated_at\'][:10]}")
    lines.append(f"")
    
    by_type = {"AVOID": [], "PREFER": [], "CAUTION": []}
    for rule in rules_data.get("rules", []):
        t = rule.get("type", "CAUTION")
        if t in by_type:
            by_type[t].append(rule["text"])
    
    if by_type["PREFER"]:
        lines.append("### ✅ What Works")
        for r in by_type["PREFER"]:
            lines.append(f"- {r}")
        lines.append("")
    
    if by_type["AVOID"]:
        lines.append("### 🚫 What to Avoid")
        for r in by_type["AVOID"]:
            lines.append(f"- {r}")
        lines.append("")
    
    if by_type["CAUTION"]:
        lines.append("### ⚠️ Use Caution")
        for r in by_type["CAUTION"]:
            lines.append(f"- {r}")
        lines.append("")
    
    return "\\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Update MEMORY.md with learned rules")
    parser.add_argument("--memory-path", required=True, help="Path to MEMORY.md file")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    memory_path = Path(args.memory_path)
    if not memory_path.exists():
        print(f"ERROR: Memory file not found: {memory_path}")
        print("Please provide a valid path to an existing MEMORY.md file.")
        sys.exit(1)

    rules_data = load_rules()

    with open(memory_path) as f:
        content = f.read()

    new_section = build_rules_section(rules_data)

    if SECTION_HEADER in content:
        # Replace existing section
        start = content.index(SECTION_HEADER)
        # Find the next ## heading or end of file
        rest = content[start + len(SECTION_HEADER):]
        next_section = rest.find("\\n## ")
        if next_section >= 0:
            end = start + len(SECTION_HEADER) + next_section
            updated = content[:start] + new_section + "\\n" + content[end:]
        else:
            updated = content[:start] + new_section
        action = "Updated"
    else:
        # Append new section
        updated = content.rstrip() + "\\n\\n" + new_section
        action = "Appended"

    if args.dry_run:
        print(f"\\n[DRY RUN] Would {action.lower()} Learned Rules section in: {memory_path}")
        print("\\n── Preview ──")
        print(new_section)
        return

    with open(memory_path, "w") as f:
        f.write(updated)

    print(f"✅ {action} \'{SECTION_HEADER}\' section in: {memory_path}")
    print(f"   Rules applied: {len(rules_data.get(\'rules\', []))}")

if __name__ == "__main__":
    main()
'''

# weekly_review.py
weekly_review_script = '''#!/usr/bin/env python3
"""Weekly performance review with trend comparison."""
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = Path(__file__).parent
TRADES_FILE = SCRIPT_DIR.parent / "data" / "trades.json"

def main():
    if not TRADES_FILE.exists():
        print("No trades found.")
        return
    with open(TRADES_FILE) as f:
        trades = json.load(f).get("trades", [])
    
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    
    this_week = [t for t in trades if datetime.fromisoformat(t["timestamp"].replace("Z", "+00:00")) >= week_ago]
    last_week = [t for t in trades if two_weeks_ago <= datetime.fromisoformat(t["timestamp"].replace("Z", "+00:00")) < week_ago]
    
    def stats(ts):
        if not ts: return 0, 0, 0
        wins = sum(1 for t in ts if t["result"] == "WIN")
        wr = wins/len(ts)*100
        pnl = sum(t["pnl_percent"] for t in ts)
        return len(ts), wr, pnl
    
    nt, wr, pnl = stats(this_week)
    nl, wrl, pnll = stats(last_week)
    
    print(f"\\n📈 WEEKLY REVIEW")
    print(f"{'='*40}")
    print(f"This week:  {nt} trades | {wr:.1f}% win rate | {pnl:+.2f}% PnL")
    print(f"Last week:  {nl} trades | {wrl:.1f}% win rate | {pnll:+.2f}% PnL")
    
if __name__ == "__main__":
    main()
'''

# Write scripts
scripts = {
    "log_trade.py": log_trade_script,
    "analyze.py": analyze_script,
    "generate_rules.py": generate_rules_script,
    "update_memory.py": update_memory_script,
    "weekly_review.py": weekly_review_script,
}

for name, content in scripts.items():
    path = scripts_dir / name
    path.write_text(content)
    os.chmod(path, 0o755)

# ── 3. Create the MEMORY.md file (the shared strategy document) ───────────────
team_docs_dir = WORKSPACE / "team" / "strategy"
team_docs_dir.mkdir(parents=True, exist_ok=True)

memory_content = """# 🧠 Trading Strategy Memory

## Core Philosophy
- Always trade with the trend
- Risk no more than 2% per trade
- Cut losses quickly, let winners run

## Entry Rules
- Confirm trend on higher timeframe before entry
- Wait for pullback to key levels
- Use volume confirmation

## Exit Rules
- Scale out at key resistance levels
- Move stop to breakeven after +1R
- Never average down on losses

## Risk Management
- Maximum 3 concurrent positions
- Reduce size in choppy markets
- No trading during major news events

## Current Focus Assets
- BTCUSDT: Primary focus, best liquidity
- ETHUSDT: Secondary, high correlation to BTC
- SOLUSDT: Emerging opportunity
"""

(team_docs_dir / "MEMORY.md").write_text(memory_content)

# ── 4. Create distractor files throughout workspace ───────────────────────────

# Config files
config_dir = WORKSPACE / "config"
config_dir.mkdir(exist_ok=True)

(config_dir / "trading_config.yaml").write_text("""
exchange: binance
symbols: [BTCUSDT, ETHUSDT, SOLUSDT]
max_leverage: 20
default_stop_loss: 0.02
""")

(config_dir / "alerts.json").write_text(json.dumps({
    "telegram_enabled": False,
    "discord_enabled": False,
    "alert_levels": ["critical", "warning"]
}, indent=2))

# Old log files
logs_dir = WORKSPACE / "logs"
logs_dir.mkdir(exist_ok=True)
for i in range(3):
    (logs_dir / f"trading_log_2024_week{i+1:02d}.txt").write_text(
        f"Week {i+1} trading log - manual notes\n"
        f"Opened 5 positions, closed 4\n"
        f"Net PnL: {random.uniform(-2, 5):.2f}%\n"
    )

# Performance spreadsheet stub
reports_dir = WORKSPACE / "reports"
reports_dir.mkdir(exist_ok=True)
(reports_dir / "q1_2025_performance.csv").write_text(
    "date,symbol,pnl,result\n"
    "2025-01-15,BTCUSDT,2.3,WIN\n"
    "2025-01-18,ETHUSDT,-1.5,LOSS\n"
    "2025-01-22,BTCUSDT,3.1,WIN\n"
)
(reports_dir / "analysis_notes.txt").write_text(
    "Q1 2025 Review Notes\n"
    "- BTC performed best on Tuesdays\n"
    "- Avoid trading during US CPI releases\n"
    "- Oversold RSI setups showed 70% win rate\n"
)

# Market data stubs
market_dir = WORKSPACE / "market_data"
market_dir.mkdir(exist_ok=True)
for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
    (market_dir / f"{sym}_ohlcv.json").write_text(json.dumps({
        "symbol": sym,
        "timeframe": "1h",
        "note": "historical ohlcv stub - use exchange API for live data"
    }, indent=2))

# Strategy documents
strategy_dir = WORKSPACE / "team" / "strategy"
(strategy_dir / "entry_checklist.md").write_text(
    "# Entry Checklist\n"
    "- [ ] Trend aligned on 4H\n"
    "- [ ] RSI not overbought/oversold\n"
    "- [ ] Volume confirms move\n"
    "- [ ] Risk/reward > 2:1\n"
)
(strategy_dir / "risk_limits.json").write_text(json.dumps({
    "max_daily_loss_pct": 5.0,
    "max_position_size_pct": 10.0,
    "hard_leverage_cap": 20
}, indent=2))

# Indicator scripts (distractors)
indicators_dir = WORKSPACE / "indicators"
indicators_dir.mkdir(exist_ok=True)
(indicators_dir / "rsi_calculator.py").write_text(
    "# RSI Calculator - standalone utility\n"
    "# Use: python3 rsi_calculator.py --prices prices.csv\n"
    "import sys\n"
    "print('RSI calculator stub - not integrated with self-learning')\n"
)
(indicators_dir / "macd_signals.py").write_text(
    "# MACD signal generator\n"
    "print('MACD signals stub')\n"
)

# Archived trades (old format, NOT the correct trades.json location)
archive_dir = WORKSPACE / "archive" / "old_trades"
archive_dir.mkdir(parents=True, exist_ok=True)
(archive_dir / "trades_2024.json").write_text(json.dumps({
    "version": "1.0",
    "note": "Old format - not compatible with self-learning system",
    "entries": [
        {"date": "2024-12-01", "asset": "BTC", "profit": 1.5}
    ]
}, indent=2))

# Ensure trades.json does NOT exist yet (agent must create via log_trade.py)
trades_json = data_dir / "trades.json"
if trades_json.exists():
    trades_json.unlink()

print("✅ Workspace generated successfully")
print(f"   Skill base: {skill_base}")
print(f"   Scripts: {list(scripts_dir.iterdir())}")
print(f"   Memory file: {team_docs_dir / 'MEMORY.md'}")
print(f"   Distractor files: ~15 files across workspace")