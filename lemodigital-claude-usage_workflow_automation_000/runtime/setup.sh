#!/bin/bash
set -e

echo "=== Setting up claude-usage skill ==="

SKILL_DIR="/opt/skills/claude-usage"
mkdir -p "$SKILL_DIR/scripts"

# Check if the script was cloned successfully; if not, create it from scratch
# using the documented logic from SKILL.md
if [ ! -f "$SKILL_DIR/scripts/claude-usage.py" ]; then
    echo "Script not found from git clone, creating from documented specification..."
    cat > "$SKILL_DIR/scripts/claude-usage.py" << 'PYEOF'
#!/usr/bin/env python3
"""
Claude Max Usage Calculator
Implements credit calculation per she-llac.com/claude-limits specification.

Credits formula:
  credits = (input_tokens + cache_write_tokens) * input_rate + output_tokens * output_rate

Rates (per token, expressed as fraction/15):
  Haiku:  input=2/15,  output=10/15
  Sonnet: input=6/15,  output=30/15
  Opus:   input=10/15, output=50/15

Cache reads are FREE.
Non-Claude models: 0 credits.

Plan budgets:
  pro: 550,000/5h,  5,000,000/week
  5x:  3,300,000/5h, 41,666,700/week
  20x: 11,000,000/5h, 83,333,300/week
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

CONFIG_PATH = Path.home() / ".claude-usage-config.json"
SESSIONS_DIR = Path.home() / ".openclaw" / "agents" / "main" / "sessions"

# Credit rates per token
MODEL_RATES = {
    "haiku": {"input": 2/15, "output": 10/15},
    "sonnet": {"input": 6/15, "output": 30/15},
    "opus": {"input": 10/15, "output": 50/15},
}

PLAN_BUDGETS = {
    "pro": {"per_5h": 550_000, "weekly": 5_000_000},
    "5x":  {"per_5h": 3_300_000, "weekly": 41_666_700},
    "20x": {"per_5h": 11_000_000, "weekly": 83_333_300},
}

def get_model_family(model_name: str):
    """Determine model family from model name string."""
    name = model_name.lower()
    if "opus" in name:
        return "opus"
    elif "sonnet" in name:
        return "sonnet"
    elif "haiku" in name:
        return "haiku"
    else:
        return None  # Non-Claude model

def calculate_credits(input_tokens, output_tokens, cache_write_tokens, cache_read_tokens, model_family):
    """Calculate credits consumed. Cache reads are free. Non-Claude = 0."""
    if model_family is None:
        return 0.0
    rates = MODEL_RATES[model_family]
    credits = (input_tokens + cache_write_tokens) * rates["input"] + output_tokens * rates["output"]
    return credits

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

def save_config(reset_time: str, plan: str):
    config = load_config()
    config["reset_time"] = reset_time
    config["plan"] = plan
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Config saved: plan={plan}, reset_time={reset_time}")

def parse_reset_time(reset_str: str) -> datetime:
    """Parse reset time string to UTC datetime."""
    dt = datetime.strptime(reset_str, "%Y-%m-%d %H:%M")
    return dt.replace(tzinfo=timezone.utc)

def load_sessions(reset_dt: datetime):
    """Load all session JSONL files and return records after reset_dt."""
    sessions = defaultdict(lambda: {
        "key": "",
        "id": "",
        "credits": 0.0,
        "models": defaultdict(float),
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_write_tokens": 0,
        "cache_read_tokens": 0,
        "timestamps": [],
    })

    if not SESSIONS_DIR.exists():
        return sessions

    for jfile in SESSIONS_DIR.glob("*.jsonl"):
        with open(jfile) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ts_str = rec.get("timestamp", "")
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                except Exception:
                    continue

                if ts < reset_dt:
                    continue

                sess_key = rec.get("session_key", rec.get("session_id", "unknown"))
                sess_id = rec.get("session_id", "")
                model_name = rec.get("model", "")
                model_family = get_model_family(model_name)

                usage = rec.get("usage", {})
                inp = usage.get("input_tokens", 0)
                out = usage.get("output_tokens", 0)
                cw = usage.get("cache_creation_input_tokens", 0)
                cr = usage.get("cache_read_input_tokens", 0)

                credits = calculate_credits(inp, out, cw, cr, model_family)

                s = sessions[sess_key]
                s["key"] = sess_key
                s["id"] = sess_id
                s["credits"] += credits
                s["input_tokens"] += inp
                s["output_tokens"] += out
                s["cache_write_tokens"] += cw
                s["cache_read_tokens"] += cr
                s["timestamps"].append(ts.isoformat())
                
                family_label = model_family if model_family else f"non-claude({model_name})"
                s["models"][family_label] += credits

    return sessions

def get_5h_window_credits(sessions_data, now: datetime):
    """Credits used in the last 5-hour sliding window."""
    # Re-scan raw records for the 5h window
    window_start = now - timedelta(hours=5)
    total = 0.0
    if not SESSIONS_DIR.exists():
        return total
    for jfile in SESSIONS_DIR.glob("*.jsonl"):
        with open(jfile) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts_str = rec.get("timestamp", "")
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                except Exception:
                    continue
                if ts < window_start:
                    continue
                model_name = rec.get("model", "")
                model_family = get_model_family(model_name)
                usage = rec.get("usage", {})
                inp = usage.get("input_tokens", 0)
                out = usage.get("output_tokens", 0)
                cw = usage.get("cache_creation_input_tokens", 0)
                cr = usage.get("cache_read_input_tokens", 0)
                total += calculate_credits(inp, out, cw, cr, model_family)
    return total

def main():
    parser = argparse.ArgumentParser(description="Claude Max Usage Calculator")
    parser.add_argument("reset_time", nargs="?", help="Weekly reset time (YYYY-MM-DD HH:MM)")
    parser.add_argument("--plan", default=None, choices=["pro", "5x", "20x"])
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--tz", default="UTC")
    parser.add_argument("--top", type=int, default=None)
    parser.add_argument("--session", default=None)
    parser.add_argument("--json", action="store_true", dest="json_out")
    args = parser.parse_args()

    config = load_config()

    # Determine reset_time and plan
    reset_time_str = args.reset_time or config.get("reset_time")
    plan = args.plan or config.get("plan", "5x")

    if args.save:
        if not reset_time_str:
            print("ERROR: Provide reset time to save.", file=sys.stderr)
            sys.exit(1)
        save_config(reset_time_str, plan)
        if not args.json_out:
            return

    if not reset_time_str:
        print("ERROR: No reset time. Run with a reset time and --save first.", file=sys.stderr)
        sys.exit(1)

    reset_dt = parse_reset_time(reset_time_str)
    budget = PLAN_BUDGETS[plan]
    weekly_budget = budget["weekly"]
    per_5h_budget = budget["per_5h"]

    now = datetime.now(timezone.utc)
    sessions_data = load_sessions(reset_dt)

    if not sessions_data:
        if args.json_out:
            print(json.dumps({"error": "No sessions found"}))
        else:
            print("No sessions found in the current week.")
        return

    total_credits = sum(s["credits"] for s in sessions_data.values())
    weekly_pct = (total_credits / weekly_budget) * 100

    # Sort sessions by credits descending
    ranked_sessions = sorted(sessions_data.values(), key=lambda s: s["credits"], reverse=True)

    if args.session:
        # Single session detail
        query = args.session.lower()
        matched = [s for s in ranked_sessions if query in s["key"].lower() or query in s["id"].lower()]
        if not matched:
            if args.json_out:
                print(json.dumps({"error": f"No session matching '{args.session}'"}))
            else:
                print(f"No session matching '{args.session}'")
            return
        s = matched[0]
        sess_pct_weekly = (s["credits"] / weekly_budget) * 100
        sess_pct_total = (s["credits"] / total_credits * 100) if total_credits > 0 else 0
        result = {
            "session_key": s["key"],
            "session_id": s["id"],
            "credits": round(s["credits"], 4),
            "pct_weekly_budget": round(sess_pct_weekly, 4),
            "pct_of_total_usage": round(sess_pct_total, 4),
            "tokens": {
                "input": s["input_tokens"],
                "output": s["output_tokens"],
                "cache_write": s["cache_write_tokens"],
                "cache_read": s["cache_read_tokens"],
            },
            "model_breakdown": {k: round(v, 4) for k, v in s["models"].items()},
        }
        if args.json_out:
            print(json.dumps(result, indent=2))
        else:
            print(f"Session: {s['key']} ({s['id']})")
            print(f"  Credits: {s['credits']:.2f} ({sess_pct_weekly:.2f}% of weekly budget)")
            print(f"  % of total usage: {sess_pct_total:.2f}%")
            print(f"  Tokens: input={s['input_tokens']}, output={s['output_tokens']}, cache_write={s['cache_write_tokens']}, cache_read={s['cache_read_tokens']}")
            for m, c in s["models"].items():
                print(f"    {m}: {c:.2f} credits")
        return

    # Weekly overview
    credits_5h = get_5h_window_credits(sessions_data, now)
    pct_5h = (credits_5h / per_5h_budget) * 100

    display_sessions = ranked_sessions
    if args.top:
        display_sessions = ranked_sessions[:args.top]

    result = {
        "plan": plan,
        "weekly_reset": reset_time_str,
        "total_credits_used": round(total_credits, 4),
        "weekly_budget": weekly_budget,
        "weekly_pct": round(weekly_pct, 4),
        "credits_last_5h": round(credits_5h, 4),
        "per_5h_budget": per_5h_budget,
        "pct_5h": round(pct_5h, 4),
        "sessions": [
            {
                "rank": i + 1,
                "session_key": s["key"],
                "session_id": s["id"],
                "credits": round(s["credits"], 4),
                "pct_weekly": round((s["credits"] / weekly_budget) * 100, 4),
                "model_breakdown": {k: round(v, 4) for k, v in s["models"].items()},
            }
            for i, s in enumerate(display_sessions)
        ],
    }

    if args.json_out:
        print(json.dumps(result, indent=2))
    else:
        print(f"Claude Max Usage — Plan: {plan}")
        print(f"Weekly: {total_credits:.0f} / {weekly_budget:,} credits ({weekly_pct:.2f}%)")
        print(f"Last 5h: {credits_5h:.0f} / {per_5h_budget:,} credits ({pct_5h:.2f}%)")
        print(f"\nTop sessions:")
        for i, s in enumerate(display_sessions, 1):
            print(f"  {i}. {s['key']}: {s['credits']:.2f} credits")

if __name__ == "__main__":
    main()
PYEOF
fi

chmod +x "$SKILL_DIR/scripts/claude-usage.py"

# Verify Python version
python3 --version

# Test the script is executable
python3 "$SKILL_DIR/scripts/claude-usage.py" --help || true

echo "=== Setup complete ==="
echo "SKILL_DIR=$SKILL_DIR"
echo "Sessions dir: $(ls ~/.openclaw/agents/main/sessions/ 2>/dev/null || echo 'not yet created')"