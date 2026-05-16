import os
import stat
import json
import textwrap
from pathlib import Path

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Create the skill directory structure ──────────────────────────────────────
skill_dir = Path.home() / ".openclaw" / "skills" / "market-watch" / "scripts"
skill_dir.mkdir(parents=True, exist_ok=True)

openclaw_conf = Path.home() / ".openclaw"
(openclaw_conf / "config").mkdir(parents=True, exist_ok=True)

# ── Write mock register-price-alert.py ───────────────────────────────────────
register_price = skill_dir / "register-price-alert.py"
register_price.write_text(textwrap.dedent(r'''
#!/usr/bin/env python3
"""Mock register-price-alert.py — functional stub matching SKILL.md interface."""
import argparse, json, os, time
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--market", required=True, choices=["crypto", "astock"])
    parser.add_argument("--condition", required=True)
    parser.add_argument("--target", required=True, type=float)
    parser.add_argument("--context-summary", default="")
    parser.add_argument("--session-key", default="")
    parser.add_argument("--reply-channel", default="")
    parser.add_argument("--reply-to", default="")
    parser.add_argument("--transcript-file", default="")
    parser.add_argument("--transcript-msg-id", default="")
    args = parser.parse_args()

    alerts_dir = Path.home() / ".openclaw" / "agents" / args.agent / "private"
    alerts_dir.mkdir(parents=True, exist_ok=True)
    alerts_file = alerts_dir / "market-alerts.json"

    alerts = []
    if alerts_file.exists():
        try:
            alerts = json.loads(alerts_file.read_text())
        except Exception:
            alerts = []

    ts = int(time.time())
    alert_id = f"{args.asset.lower()}-{ts}"
    alert = {
        "id": alert_id,
        "type": "price",
        "status": "active",
        "one_shot": True,
        "context_summary": args.context_summary,
        "session_key": args.session_key,
        "agent_id": args.agent,
        "reply_channel": args.reply_channel,
        "reply_to": args.reply_to,
        "transcript_file": args.transcript_file,
        "transcript_msg_id": args.transcript_msg_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "asset": args.asset.upper(),
        "market": args.market,
        "condition": args.condition,
        "target_price": args.target,
    }
    alerts.append(alert)
    alerts_file.write_text(json.dumps(alerts, ensure_ascii=False, indent=2))
    print(f"[OK] Price alert registered: {alert_id}")
    print(f"     {args.asset.upper()} {args.condition} {args.target}")
    print(f"     Alerts file: {alerts_file}")

if __name__ == "__main__":
    main()
''').lstrip())

# ── Write mock register-news-alert.py ─────────────────────────────────────────
register_news = skill_dir / "register-news-alert.py"
register_news.write_text(textwrap.dedent(r'''
#!/usr/bin/env python3
"""Mock register-news-alert.py — functional stub matching SKILL.md interface."""
import argparse, json, os, time
from pathlib import Path

VALID_SOURCES = {"jin10", "wallstreetcn", "coindesk", "cointelegraph", "theblock", "decrypt"}
ALL_SOURCES = sorted(VALID_SOURCES)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True)
    parser.add_argument("--keywords", required=True)
    parser.add_argument("--keyword-mode", default="any", choices=["any", "all"])
    parser.add_argument("--sources", default="")
    parser.add_argument("--poll-interval", type=int, default=300)
    parser.add_argument("--one-shot", action="store_true")
    parser.add_argument("--context-summary", default="")
    parser.add_argument("--session-key", default="")
    parser.add_argument("--reply-channel", default="")
    parser.add_argument("--reply-to", default="")
    parser.add_argument("--transcript-file", default="")
    parser.add_argument("--transcript-msg-id", default="")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if args.sources:
        sources = [s.strip() for s in args.sources.split(",") if s.strip()]
        invalid = set(sources) - VALID_SOURCES
        if invalid:
            print(f"[WARN] Unknown sources ignored: {invalid}")
            sources = [s for s in sources if s in VALID_SOURCES]
    else:
        sources = ALL_SOURCES

    alerts_dir = Path.home() / ".openclaw" / "agents" / args.agent / "private"
    alerts_dir.mkdir(parents=True, exist_ok=True)
    alerts_file = alerts_dir / "market-alerts.json"

    alerts = []
    if alerts_file.exists():
        try:
            alerts = json.loads(alerts_file.read_text())
        except Exception:
            alerts = []

    ts = int(time.time())
    alert_id = f"news-{ts}"
    alert = {
        "id": alert_id,
        "type": "news",
        "status": "active",
        "one_shot": args.one_shot,
        "context_summary": args.context_summary,
        "session_key": args.session_key,
        "agent_id": args.agent,
        "reply_channel": args.reply_channel,
        "reply_to": args.reply_to,
        "transcript_file": args.transcript_file,
        "transcript_msg_id": args.transcript_msg_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "keywords": keywords,
        "keyword_mode": args.keyword_mode,
        "sources": sources,
        "poll_interval": args.poll_interval,
    }
    alerts.append(alert)
    alerts_file.write_text(json.dumps(alerts, ensure_ascii=False, indent=2))
    print(f"[OK] News alert registered: {alert_id}")
    print(f"     Keywords: {keywords}, mode={args.keyword_mode}, one_shot={args.one_shot}")
    print(f"     Sources: {sources}")

if __name__ == "__main__":
    main()
''').lstrip())

# ── Write mock cancel-alert.py ────────────────────────────────────────────────
cancel_alert = skill_dir / "cancel-alert.py"
cancel_alert.write_text(textwrap.dedent(r'''
#!/usr/bin/env python3
"""Mock cancel-alert.py — functional stub matching SKILL.md interface."""
import argparse, json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", required=True)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--id", default="")
    parser.add_argument("--asset", default="")
    parser.add_argument("--type", default="")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    alerts_dir = Path.home() / ".openclaw" / "agents" / args.agent / "private"
    alerts_file = alerts_dir / "market-alerts.json"

    alerts = []
    if alerts_file.exists():
        try:
            alerts = json.loads(alerts_file.read_text())
        except Exception:
            alerts = []

    if args.list:
        active = [a for a in alerts if a.get("status") == "active"]
        print(f"Active alerts for agent '{args.agent}': {len(active)}")
        for a in active:
            print(f"  [{a['type']}] id={a['id']} status={a['status']}")
            if a['type'] == 'price':
                print(f"    asset={a.get('asset')} condition={a.get('condition')} target={a.get('target_price')}")
            else:
                print(f"    keywords={a.get('keywords')} mode={a.get('keyword_mode')} one_shot={a.get('one_shot')}")
        return

    # cancellation logic
    changed = False
    for a in alerts:
        if a.get("status") != "active":
            continue
        if getattr(args, "all"):
            a["status"] = "cancelled"; changed = True
        elif args.id and a["id"] == args.id:
            a["status"] = "cancelled"; changed = True
        elif args.asset and a.get("asset", "").upper() == args.asset.upper():
            a["status"] = "cancelled"; changed = True
        elif getattr(args, "type") and a["type"] == getattr(args, "type"):
            a["status"] = "cancelled"; changed = True

    if changed:
        alerts_file.write_text(json.dumps(alerts, ensure_ascii=False, indent=2))
        print("[OK] Alert(s) cancelled.")

if __name__ == "__main__":
    main()
''').lstrip())

# ── Write mock daemon.sh ──────────────────────────────────────────────────────
daemon_sh = skill_dir / "daemon.sh"
daemon_sh.write_text(textwrap.dedent(r'''
#!/usr/bin/env bash
# Mock daemon.sh — matches SKILL.md interface for start/stop/restart/status/log

AGENT=""
CMD=""

# Parse positional args
while [[ $# -gt 0 ]]; do
  case "$1" in
    start|stop|restart|status|log) CMD="$1" ;;
    --agent) AGENT="$2"; shift ;;
    --lines) LINES="$2"; shift ;;
  esac
  shift
done

# Try to detect agent from alerts file if not specified
if [[ -z "$AGENT" ]]; then
  # Look for any agent under ~/.openclaw/agents/
  for d in "$HOME/.openclaw/agents"/*/; do
    if [[ -d "$d" ]]; then
      AGENT=$(basename "$d")
      break
    fi
  done
fi

if [[ -z "$AGENT" ]]; then
  echo "[ERROR] Could not determine agent name. Use --agent <name>."
  exit 1
fi

PRICE_PID="/tmp/market-watch-${AGENT}-price.pid"
NEWS_PID="/tmp/market-watch-${AGENT}-news.pid"
PRICE_LOG="/tmp/market-watch-${AGENT}.log"
NEWS_LOG="/tmp/market-watch-${AGENT}-news.log"
ALERTS_FILE="$HOME/.openclaw/agents/${AGENT}/private/market-alerts.json"

check_active_types() {
  python3 -c "
import json, sys
try:
    alerts = json.load(open('${ALERTS_FILE}'))
    types = {a['type'] for a in alerts if a.get('status') == 'active'}
    print(' '.join(types))
except:
    print('')
" 2>/dev/null
}

do_start() {
  ACTIVE_TYPES=$(check_active_types)
  STARTED=0
  if echo "$ACTIVE_TYPES" | grep -qw price; then
    if [[ ! -f "$PRICE_PID" ]]; then
      echo $$ > "$PRICE_PID"
      echo "[$(date -Iseconds)] price monitor started (mock)" >> "$PRICE_LOG"
      echo "[OK] Price monitor started (PID=$$)"
      STARTED=$((STARTED+1))
    else
      echo "[INFO] Price monitor already running"
    fi
  fi
  if echo "$ACTIVE_TYPES" | grep -qw news; then
    if [[ ! -f "$NEWS_PID" ]]; then
      echo $$ > "$NEWS_PID"
      echo "[$(date -Iseconds)] news monitor started (mock)" >> "$NEWS_LOG"
      echo "[OK] News monitor started (PID=$$)"
      STARTED=$((STARTED+1))
    else
      echo "[INFO] News monitor already running"
    fi
  fi
  if [[ $STARTED -eq 0 && -z "$ACTIVE_TYPES" ]]; then
    echo "[WARN] No active alerts found; no processes started."
  fi
}

do_stop() {
  for PID_FILE in "$PRICE_PID" "$NEWS_PID"; do
    if [[ -f "$PID_FILE" ]]; then
      rm -f "$PID_FILE"
      echo "[OK] Stopped: $PID_FILE"
    fi
  done
}

do_status() {
  echo "=== Market Watch Status (agent: $AGENT) ==="
  for PID_FILE in "$PRICE_PID" "$NEWS_PID"; do
    if [[ -f "$PID_FILE" ]]; then
      echo "  RUNNING: $PID_FILE (PID=$(cat $PID_FILE))"
    else
      echo "  STOPPED: $PID_FILE"
    fi
  done
  echo ""
  python3 -c "
import json
try:
    alerts = json.load(open('${ALERTS_FILE}'))
    active = [a for a in alerts if a.get('status') == 'active']
    print(f'Active alerts: {len(active)}')
    for a in active:
        print(f'  [{a[\"type\"]}] {a[\"id\"]}')
except Exception as e:
    print(f'Could not read alerts: {e}')
" 2>/dev/null
}

case "$CMD" in
  start)   do_start ;;
  stop)    do_stop ;;
  restart) do_stop; do_start ;;
  status)  do_status ;;
  log)
    LINES=${LINES:-40}
    for LOG in "$PRICE_LOG" "$NEWS_LOG"; do
      if [[ -f "$LOG" ]]; then
        echo "=== $LOG (last $LINES lines) ==="
        tail -n "$LINES" "$LOG"
      fi
    done
    ;;
  *)
    echo "Usage: daemon.sh {start|stop|restart|status|log} [--agent NAME] [--lines N]"
    exit 1
    ;;
esac
''').lstrip())

# ── Distractor files to simulate realistic workspace ───────────────────────────
distractor_dir = workspace / "portfolio"
distractor_dir.mkdir(exist_ok=True)

(distractor_dir / "holdings.csv").write_text(
    "asset,amount,avg_cost_usdt\nBTC,0.5,58000\nETH,3.0,3200\nHYPE,150,25.0\nSOL,10,145\n"
)

(distractor_dir / "strategy_notes.md").write_text(
    "# Trading Strategy\n\n## HYPE Position\n- Entry at 24.0, current 27.3\n- Target exit: partial at 30+\n- Stop-loss consideration: 28.5 (key support)\n\n## News Triggers\n- Watch for HyperEVM mainnet announcements\n- Monitor Hyperliquid protocol updates\n- HYPE token utility expansion news\n"
)

(distractor_dir / "trade_log.json").write_text(json.dumps([
    {"date": "2026-01-10", "asset": "HYPE", "side": "buy", "amount": 100, "price": 24.0},
    {"date": "2026-01-15", "asset": "HYPE", "side": "buy", "amount": 50, "price": 26.5},
], indent=2))

rebalance_dir = workspace / "rebalance_plans"
rebalance_dir.mkdir(exist_ok=True)
(rebalance_dir / "q1_2026.md").write_text(
    "# Q1 Rebalance Plan\n\nIf HYPE drops to 28.5, exit 50 units to lock in profits before news-driven volatility.\nMonitor for Hyperliquid + HyperEVM news that might shift momentum.\nSession: agent:tradebot:feishu:direct:ou_k9xmf22\nReply target: user:ou_k9xmf22\nMsg context ID: msg-hype-2026-plan-001\n"
)

scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)
(scripts_dir / "check_prices.sh").write_text("#!/bin/bash\n# placeholder\ncurl -s https://api.binance.com/api/v3/ticker/price?symbol=HYPEUSDT\n")
(scripts_dir / "fetch_news.py").write_text("# placeholder fetcher\nimport requests\nprint('fetching news...')\n")

config_dir = workspace / "config"
config_dir.mkdir(exist_ok=True)
(config_dir / "alert_config_old.json").write_text(json.dumps({
    "deprecated": True,
    "note": "This format is outdated. Use register-price-alert.py instead.",
    "assets": ["BTC", "ETH"],
    "thresholds": {"BTC": 60000, "ETH": 3000}
}, indent=2))

(config_dir / "sources.txt").write_text(
    "jin10\nwallstreetcn\ncoindesk\ncointelegraph\ntheblock\ndecrypt\n"
)

logs_dir = workspace / "logs"
logs_dir.mkdir(exist_ok=True)
for i in range(5):
    (logs_dir / f"session_{i:03d}.jsonl").write_text(
        json.dumps({"msg_id": f"msg-{i:04d}", "content": f"historical message {i}", "ts": 1700000000+i*3600}) + "\n"
    )

(workspace / "README_ARCHIVE.txt").write_text(
    "This directory contains archived trading notes. Not the active skill workspace.\n"
)

notes_dir = workspace / "research"
notes_dir.mkdir(exist_ok=True)
(notes_dir / "hyperliquid_deep_dive.md").write_text(
    "# Hyperliquid Research\nHYPE is the native token of Hyperliquid DEX.\nHyperEVM is an EVM-compatible layer being rolled out.\nWatching for: mainnet launch, token utility, protocol integrations.\n"
)
(notes_dir / "market_signals.json").write_text(json.dumps({
    "signals": [
        {"asset": "HYPE", "signal": "resistance at 30", "confidence": 0.72},
        {"asset": "HYPE", "signal": "support at 28.5", "confidence": 0.88}
    ]
}, indent=2))

print("Workspace and skill scripts created successfully.")
print(f"Skill scripts at: {skill_dir}")
print(f"Workspace at: {workspace}")