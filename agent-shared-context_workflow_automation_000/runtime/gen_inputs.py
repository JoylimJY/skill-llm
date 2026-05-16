import os
import json
import random
import time
from pathlib import Path
from datetime import datetime, timezone

random.seed(42)

# Define the openclaw workspace structure (as per SKILL.md)
base = Path.home() / ".openclaw" / "workspace"
scripts_dir = base / "scripts"
shared_dir = base / "shared"
agents_dir = base / "agents"
logs_dir = base / "logs"
cron_dir = base / "cron"

for d in [scripts_dir, shared_dir, agents_dir, logs_dir, cron_dir,
          base / "agents" / "reddit",
          base / "agents" / "news",
          base / "agents" / "moltbook",
          base / "agents" / "clawstr",
          base / "logs" / "archive",
          base / "config"]:
    d.mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────

# 1. Agent config files (distractors)
(base / "agents" / "reddit" / "config.json").write_text(json.dumps({
    "agent": "reddit",
    "subreddits": ["selfhosted", "MachineLearning", "LocalLLaMA"],
    "poll_interval": 300
}, indent=2))

(base / "agents" / "news" / "config.json").write_text(json.dumps({
    "agent": "news",
    "sources": ["HN", "TechCrunch", "ArsTechnica"],
    "poll_interval": 600
}, indent=2))

(base / "agents" / "moltbook" / "config.json").write_text(json.dumps({
    "agent": "moltbook",
    "platform": "moltbook",
    "post_limit": 3
}, indent=2))

(base / "agents" / "clawstr" / "config.json").write_text(json.dumps({
    "agent": "clawstr",
    "platform": "clawstr",
    "hashtags": ["#AI", "#LocalLLM", "#OpenSource"]
}, indent=2))

# 2. Stale/wrong format trends.json (agent must overwrite or work with this)
# Intentionally malformed / empty to ensure agent initializes properly
(shared_dir / "trends.json").write_text("{}")

# 3. Stale highlights.json with very old entries (to be cleaned up)
now_ts = time.time()
stale_ts = now_ts - (72 * 3600)  # 72 hours old
recent_ts = now_ts - (10 * 3600)  # 10 hours old

(shared_dir / "highlights.json").write_text(json.dumps({
    "highlights": [
        {
            "source": "legacy-agent",
            "title": "Old story about blockchain",
            "summary": "Three-day-old content that should be pruned",
            "timestamp": stale_ts
        },
        {
            "source": "legacy-agent",
            "title": "Slightly less old story",
            "summary": "Also stale content",
            "timestamp": stale_ts + 3600
        }
    ]
}, indent=2))

# 4. Cron config distractors
(cron_dir / "reddit.cron").write_text(
    "0 * * * * python3 ~/.openclaw/workspace/agents/reddit/run.py\n"
)
(cron_dir / "news.cron").write_text(
    "*/30 * * * * python3 ~/.openclaw/workspace/agents/news/run.py\n"
)

# 5. Log distractors
for i in range(3):
    (logs_dir / f"run_{i}.log").write_text(
        f"[{datetime.now().isoformat()}] Agent run {i} completed. Found {random.randint(5,20)} items.\n"
    )

(logs_dir / "archive" / "run_old.log").write_text(
    "[2024-01-01T00:00:00] Legacy log entry\n"
)

# 6. Config distractors
(base / "config" / "global.json").write_text(json.dumps({
    "workspace": str(base),
    "version": "1.0.0",
    "log_level": "INFO"
}, indent=2))

(base / "config" / "relay.json").write_text(json.dumps({
    "shared_dir": str(shared_dir),
    "max_trends": 100,
    "max_highlights": 100
}, indent=2))

# 7. A decoy "context.py" script in the wrong place to confuse agents
decoy_script = base / "agents" / "context_helper.py"
decoy_script.write_text(
    "# Decoy: This is NOT the shared context script.\n"
    "# See scripts/shared-context.py for the correct tool.\n"
    "print('This is not the right script')\n"
)

# ── THE KEY SCRIPT: shared-context.py ────────────────────────────────────────
# This is the actual CLI tool described in SKILL.md
script_content = '''#!/usr/bin/env python3
"""
shared-context.py — Agent Relay CLI
Cross-agent context sharing via shared JSON files.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
SHARED_DIR = WORKSPACE / "shared"
TRENDS_FILE = SHARED_DIR / "trends.json"
HIGHLIGHTS_FILE = SHARED_DIR / "highlights.json"


def load_json(path, default_key):
    if path.exists():
        try:
            data = json.loads(path.read_text())
            if isinstance(data, dict) and default_key in data:
                return data
        except Exception:
            pass
    return {default_key: []}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def cmd_add_trend(args):
    data = load_json(TRENDS_FILE, "trends")
    if "trends" not in data or not isinstance(data["trends"], list):
        data = {"trends": []}
    entry = {
        "source": args.source,
        "topic": args.topic,
        "score": args.score,
        "timestamp": time.time()
    }
    data["trends"].append(entry)
    save_json(TRENDS_FILE, data)
    print(f"[relay] Trend logged: {args.topic} (score={args.score}, source={args.source})")


def cmd_add_highlight(args):
    data = load_json(HIGHLIGHTS_FILE, "highlights")
    if "highlights" not in data or not isinstance(data["highlights"], list):
        data = {"highlights": []}
    entry = {
        "source": args.source,
        "title": args.title,
        "summary": args.summary,
        "timestamp": time.time()
    }
    data["highlights"].append(entry)
    save_json(HIGHLIGHTS_FILE, data)
    print(f"[relay] Highlight logged: {args.title} (source={args.source})")


def cmd_get_trends(args):
    data = load_json(TRENDS_FILE, "trends")
    trends = data.get("trends", [])
    trends_sorted = sorted(trends, key=lambda x: x.get("score", 0), reverse=True)
    limited = trends_sorted[:args.limit]
    if not limited:
        print("[relay] No trends found.")
        return
    for t in limited:
        ts = t.get("timestamp", 0)
        print(f"[{t.get('source','?')}] {t.get('topic','?')} — score={t.get('score',0)} ts={ts:.0f}")


def cmd_get_highlights(args):
    data = load_json(HIGHLIGHTS_FILE, "highlights")
    highlights = data.get("highlights", [])
    highlights_sorted = sorted(highlights, key=lambda x: x.get("timestamp", 0), reverse=True)
    limited = highlights_sorted[:args.limit]
    if not limited:
        print("[relay] No highlights found.")
        return
    for h in limited:
        ts = h.get("timestamp", 0)
        print(f"[{h.get('source','?')}] {h.get('title','?')} — {h.get('summary','?')} ts={ts:.0f}")


def cmd_cleanup(args):
    cutoff = time.time() - (args.hours * 3600)

    # Clean trends
    data_t = load_json(TRENDS_FILE, "trends")
    before = len(data_t.get("trends", []))
    data_t["trends"] = [e for e in data_t.get("trends", []) if e.get("timestamp", 0) >= cutoff]
    after_t = len(data_t["trends"])
    save_json(TRENDS_FILE, data_t)

    # Clean highlights
    data_h = load_json(HIGHLIGHTS_FILE, "highlights")
    before_h = len(data_h.get("highlights", []))
    data_h["highlights"] = [e for e in data_h.get("highlights", []) if e.get("timestamp", 0) >= cutoff]
    after_h = len(data_h["highlights"])
    save_json(HIGHLIGHTS_FILE, data_h)

    removed_t = before - after_t
    removed_h = before_h - after_h
    print(f"[relay] Cleanup done (cutoff={args.hours}h): removed {removed_t} trends, {removed_h} highlights.")


def main():
    parser = argparse.ArgumentParser(description="Agent Relay — shared context CLI")
    subparsers = parser.add_subparsers(dest="command")

    # add-trend
    p_at = subparsers.add_parser("add-trend")
    p_at.add_argument("--source", required=True)
    p_at.add_argument("--topic", required=True)
    p_at.add_argument("--score", type=int, required=True)

    # add-highlight
    p_ah = subparsers.add_parser("add-highlight")
    p_ah.add_argument("--source", required=True)
    p_ah.add_argument("--title", required=True)
    p_ah.add_argument("--summary", required=True)

    # get-trends
    p_gt = subparsers.add_parser("get-trends")
    p_gt.add_argument("--limit", type=int, default=5)

    # get-highlights
    p_gh = subparsers.add_parser("get-highlights")
    p_gh.add_argument("--limit", type=int, default=5)

    # cleanup
    p_cl = subparsers.add_parser("cleanup")
    p_cl.add_argument("--hours", type=int, required=True)

    args = parser.parse_args()
    if args.command == "add-trend":
        cmd_add_trend(args)
    elif args.command == "add-highlight":
        cmd_add_highlight(args)
    elif args.command == "get-trends":
        cmd_get_trends(args)
    elif args.command == "get-highlights":
        cmd_get_highlights(args)
    elif args.command == "cleanup":
        cmd_cleanup(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

(scripts_dir / "shared-context.py").write_text(script_content)
print("Workspace initialized successfully.")
print(f"  Base: {base}")
print(f"  Scripts: {scripts_dir}")
print(f"  Shared: {shared_dir}")