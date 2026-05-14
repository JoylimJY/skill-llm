#!/usr/bin/env python3
"""
Generate a realistic OpenClaw workspace for the token-counter skill evaluation.
This creates:
- Realistic session transcripts (.jsonl) with usage fields
- sessions.json index
- cron/jobs.json
- The token-counter script itself (since SKILL.md says scripts already exist)
- Many distractor files
"""

import json
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

BASE = Path("/workspace")
DATA_DIR = BASE / "openclaw_data"
SKILLS_DIR = BASE / "openclaw_skills"
WORKSPACE = BASE / "openclaw_workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    DATA_DIR / "agents" / "main" / "sessions",
    DATA_DIR / "cron",
    DATA_DIR / "agents" / "main" / "memory",
    DATA_DIR / "agents" / "sub" / "sessions",
    DATA_DIR / "logs",
    DATA_DIR / "config",
    SKILLS_DIR / "token-counter" / "scripts",
    SKILLS_DIR / "token-counter" / "references",
    SKILLS_DIR / "skill-creator" / "scripts",
    SKILLS_DIR / "token-counter" / "tests",
    WORKSPACE / "token-usage" / "daily",
    WORKSPACE / "reports" / "archived",
    WORKSPACE / "tmp",
    WORKSPACE / "exports",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ── helper: generate a realistic assistant usage block ───────────────────────
def make_usage(input_tokens, output_tokens, cache_read=0, cache_write=0):
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_write,
    }

def make_tool_use(tool_name, tool_id=None):
    return {
        "type": "tool_use",
        "id": tool_id or f"toolu_{uuid.uuid4().hex[:16]}",
        "name": tool_name,
        "input": {"query": "example input"},
    }

def make_tool_result(tool_id, content="ok"):
    return {
        "type": "tool_result",
        "tool_use_id": tool_id,
        "content": content,
    }

# ── session metadata ─────────────────────────────────────────────────────────
NOW = datetime(2025, 6, 10, 14, 0, 0)

MODELS = ["claude-opus-4-5", "claude-sonnet-3-7", "claude-haiku-3-5"]
TOOLS_POOL = [
    "bash", "read_file", "write_file", "web_search",
    "grep_search", "list_directory", "python_repl", "git_commit"
]
CLIENTS = ["personal", "bonsai", "unknown"]

sessions_index = []
session_files = []

def make_session(idx, delta_hours, client, category, model, tools_used, is_cron=False):
    sid = str(uuid.UUID(int=random.getrandbits(128), version=4))
    if is_cron:
        session_id = f"agent:main:cron:{sid}"
    else:
        session_id = f"agent:main:interactive:{sid}"

    ts = NOW - timedelta(hours=delta_hours)
    ts_str = ts.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # Build transcript lines
    lines = []

    # System message
    lines.append({
        "type": "system",
        "content": f"You are a helpful assistant. Client: {client}. Task category: {category}.",
        "timestamp": ts_str,
    })

    total_input = 0
    total_output = 0

    for turn in range(random.randint(3, 8)):
        # Human turn
        lines.append({
            "type": "human",
            "content": f"Turn {turn}: Please perform task {random.randint(100,999)}.",
            "timestamp": ts_str,
        })

        # Assistant turn with tool calls and usage
        inp = random.randint(800, 8000)
        out = random.randint(200, 2000)
        cache_r = random.randint(0, 2000)
        cache_w = random.randint(0, 500)
        total_input += inp
        total_output += out

        tool_calls = []
        tool_ids = []
        for t in random.sample(tools_used, k=min(len(tools_used), random.randint(1, 3))):
            tid = f"toolu_{uuid.uuid4().hex[:16]}"
            tool_calls.append(make_tool_use(t, tid))
            tool_ids.append(tid)

        assistant_msg = {
            "type": "assistant",
            "content": tool_calls if tool_calls else "I have completed the task.",
            "usage": make_usage(inp, out, cache_r, cache_w),
            "model": model,
            "timestamp": ts_str,
        }
        lines.append(assistant_msg)

        # Tool results
        for tid in tool_ids:
            lines.append({
                "type": "human",
                "content": [make_tool_result(tid, f"result of tool {tid}")],
                "timestamp": ts_str,
            })

    total_tokens = total_input + total_output

    # Write .jsonl file
    jsonl_path = DATA_DIR / "agents" / "main" / "sessions" / f"{sid}.jsonl"
    with open(jsonl_path, "w") as f:
        for line in lines:
            f.write(json.dumps(line) + "\n")

    # Session index entry
    entry = {
        "sessionId": session_id,
        "startTime": ts_str,
        "endTime": (ts + timedelta(minutes=random.randint(5, 90))).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "totalTokens": total_tokens,
        "model": model,
        "category": category,
        "client": client,
        "transcriptFile": str(jsonl_path),
        "isCron": is_cron,
    }
    return entry

# Generate 12 sessions across last 7 days
session_configs = [
    (2,   "personal",  "coding",       MODELS[0], ["bash", "write_file", "git_commit"],           False),
    (5,   "bonsai",    "data-analysis","claude-sonnet-3-7", ["python_repl", "read_file", "bash"], False),
    (10,  "personal",  "research",     MODELS[2], ["web_search", "read_file"],                    False),
    (20,  "bonsai",    "coding",       MODELS[0], ["bash", "grep_search", "write_file"],           True),
    (30,  "unknown",   "ops",          MODELS[1], ["bash", "list_directory"],                      True),
    (48,  "personal",  "writing",      MODELS[2], ["read_file", "write_file"],                     False),
    (60,  "bonsai",    "data-analysis",MODELS[0], ["python_repl", "bash"],                        True),
    (72,  "unknown",   "coding",       MODELS[1], ["bash", "grep_search"],                        False),
    (90,  "personal",  "research",     MODELS[2], ["web_search"],                                 False),
    (100, "bonsai",    "ops",          MODELS[0], ["bash", "list_directory", "git_commit"],       True),
    (130, "personal",  "coding",       MODELS[1], ["bash", "write_file"],                         False),
    (160, "bonsai",    "research",     MODELS[2], ["web_search", "read_file", "python_repl"],     False),
]

for i, (hrs, client, cat, model, tools, is_cron) in enumerate(session_configs):
    entry = make_session(i, hrs, client, cat, model, tools, is_cron)
    sessions_index.append(entry)

# Write sessions.json
with open(DATA_DIR / "agents" / "main" / "sessions" / "sessions.json", "w") as f:
    json.dump({"sessions": sessions_index}, f, indent=2)

# ── cron/jobs.json ───────────────────────────────────────────────────────────
cron_jobs = {
    "jobs": [
        {
            "id": f"cron-{uuid.UUID(int=random.getrandbits(128), version=4)}",
            "name": "daily-data-sync",
            "schedule": "0 2 * * *",
            "client": "bonsai",
            "category": "ops",
            "enabled": True,
        },
        {
            "id": f"cron-{uuid.UUID(int=random.getrandbits(128), version=4)}",
            "name": "weekly-report",
            "schedule": "0 9 * * 1",
            "client": "personal",
            "category": "reporting",
            "enabled": True,
        },
        {
            "id": f"cron-{uuid.UUID(int=random.getrandbits(128), version=4)}",
            "name": "hourly-monitor",
            "schedule": "0 * * * *",
            "client": "bonsai",
            "category": "monitoring",
            "enabled": False,
        },
    ]
}
with open(DATA_DIR / "cron" / "jobs.json", "w") as f:
    json.dump(cron_jobs, f, indent=2)

# ── the token-counter script ─────────────────────────────────────────────────
TOKEN_COUNTER_SCRIPT = r'''#!/usr/bin/env python3
"""
token-counter: OpenClaw token usage reporter
Reads session transcripts and session metadata to produce token usage reports.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

DATA_DIR   = Path(os.environ.get("OPENCLAW_DATA_DIR",   "/workspace/openclaw_data"))
SKILLS_DIR = Path(os.environ.get("OPENCLAW_SKILLS_DIR", "/workspace/openclaw_skills"))
WS_DIR     = Path(os.environ.get("OPENCLAW_WORKSPACE",  "/workspace/openclaw_workspace"))

SESSIONS_INDEX = DATA_DIR / "agents" / "main" / "sessions" / "sessions.json"
SESSIONS_DIR   = DATA_DIR / "agents" / "main" / "sessions"
CRON_JOBS      = DATA_DIR / "cron" / "jobs.json"

VALID_BREAKDOWNS = {"tools", "category", "client", "model"}

def parse_period(period_str):
    m = re.match(r'^(\d+)([dhw])$', period_str)
    if not m:
        raise ValueError(f"Invalid period '{period_str}'. Use e.g. 1d, 7d, 1w, 30d.")
    val, unit = int(m.group(1)), m.group(2)
    if unit == 'd':
        return timedelta(days=val)
    elif unit == 'w':
        return timedelta(weeks=val)
    elif unit == 'h':
        return timedelta(hours=val)

def load_sessions_index():
    if not SESSIONS_INDEX.exists():
        return []
    with open(SESSIONS_INDEX) as f:
        data = json.load(f)
    return data.get("sessions", [])

def load_cron_jobs():
    if not CRON_JOBS.exists():
        return []
    with open(CRON_JOBS) as f:
        data = json.load(f)
    return data.get("jobs", [])

def parse_transcript(jsonl_path):
    """Parse a .jsonl transcript and return per-turn usage and tool usage."""
    entries = []
    tool_tokens = defaultdict(int)  # tool_name -> tokens attributed
    total_input = 0
    total_output = 0

    if not Path(jsonl_path).exists():
        return total_input, total_output, dict(tool_tokens)

    with open(jsonl_path) as f:
        lines = [json.loads(l) for l in f if l.strip()]

    for msg in lines:
        if msg.get("type") != "assistant":
            continue
        usage = msg.get("usage", {})
        inp = usage.get("input_tokens", 0)
        out = usage.get("output_tokens", 0)
        total_input += inp
        total_output += out

        # Tool attribution: split output tokens across tool calls in message
        content = msg.get("content", [])
        if isinstance(content, list):
            tool_calls = [c for c in content if isinstance(c, dict) and c.get("type") == "tool_use"]
            if tool_calls:
                tokens_per_tool = (inp + out) // len(tool_calls) if tool_calls else 0
                for tc in tool_calls:
                    tool_tokens[tc.get("name", "unknown")] += tokens_per_tool

    return total_input, total_output, dict(tool_tokens)

def build_report(sessions, breakdowns, now=None):
    if now is None:
        now = datetime.now(timezone.utc)

    report = {
        "generatedAt": now.isoformat(),
        "totalSessions": len(sessions),
        "totalTokens": 0,
        "totalInputTokens": 0,
        "totalOutputTokens": 0,
        "breakdowns": {},
    }

    by_category = defaultdict(int)
    by_client   = defaultdict(int)
    by_model    = defaultdict(int)
    by_tool     = defaultdict(int)

    for sess in sessions:
        # Try to parse transcript for accurate numbers
        transcript = sess.get("transcriptFile", "")
        inp, out, tool_tok = parse_transcript(transcript)
        # Use max of index totalTokens vs transcript sum
        index_total = sess.get("totalTokens", 0)
        transcript_total = inp + out
        total = max(index_total, transcript_total)

        report["totalTokens"]       += total
        report["totalInputTokens"]  += inp
        report["totalOutputTokens"] += out

        cat    = sess.get("category", "unknown")
        client = sess.get("client",   "unknown")
        model  = sess.get("model",    "unknown")

        by_category[cat]    += total
        by_client[client]   += total
        by_model[model]     += total
        for tool, tok in tool_tok.items():
            by_tool[tool]   += tok

    if "category" in breakdowns:
        report["breakdowns"]["category"] = dict(sorted(by_category.items(), key=lambda x: -x[1]))
    if "client" in breakdowns:
        report["breakdowns"]["client"]   = dict(sorted(by_client.items(),   key=lambda x: -x[1]))
    if "model" in breakdowns:
        report["breakdowns"]["model"]    = dict(sorted(by_model.items(),    key=lambda x: -x[1]))
    if "tools" in breakdowns:
        report["breakdowns"]["tools"]    = dict(sorted(by_tool.items(),     key=lambda x: -x[1]))

    return report

def filter_sessions_by_period(sessions, delta, now=None):
    if now is None:
        now = datetime.now(timezone.utc)
    cutoff = now - delta
    filtered = []
    for s in sessions:
        ts_str = s.get("startTime", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts >= cutoff:
                filtered.append(s)
        except Exception:
            pass
    return filtered

def filter_by_session_id(sessions, session_id):
    return [s for s in sessions if s.get("sessionId") == session_id]

def print_report_text(report, breakdowns):
    print(f"\n{'='*60}")
    print(f"  OpenClaw Token Usage Report")
    print(f"  Generated: {report['generatedAt']}")
    print(f"{'='*60}")
    print(f"  Total Sessions : {report['totalSessions']}")
    print(f"  Total Tokens   : {report['totalTokens']:,}")
    print(f"  Input Tokens   : {report['totalInputTokens']:,}")
    print(f"  Output Tokens  : {report['totalOutputTokens']:,}")

    for bk_name, bk_data in report.get("breakdowns", {}).items():
        print(f"\n  -- Breakdown: {bk_name} --")
        for k, v in bk_data.items():
            pct = (v / report["totalTokens"] * 100) if report["totalTokens"] else 0
            print(f"    {k:<30} {v:>10,}  ({pct:.1f}%)")
    print(f"{'='*60}\n")

def main():
    parser = argparse.ArgumentParser(description="OpenClaw Token Counter")
    parser.add_argument("--period",    help="Time period, e.g. 7d, 30d, 1w")
    parser.add_argument("--breakdown", help="Comma-separated: tools,category,client,model")
    parser.add_argument("--session",   help="Filter to single session ID")
    parser.add_argument("--format",    choices=["text", "json"], default="text")
    parser.add_argument("--output",    help="Write output to this file path")
    parser.add_argument("--save",      action="store_true", help="Save daily snapshot to token-usage/daily/YYYY-MM-DD.json")
    args = parser.parse_args()

    # Validate breakdowns
    breakdowns = set()
    if args.breakdown:
        parts = [b.strip() for b in args.breakdown.split(",")]
        invalid = set(parts) - VALID_BREAKDOWNS
        if invalid:
            print(f"ERROR: Invalid breakdown(s): {invalid}. Valid: {VALID_BREAKDOWNS}", file=sys.stderr)
            sys.exit(1)
        breakdowns = set(parts)
    else:
        breakdowns = {"category", "client", "model", "tools"}

    now = datetime.now(timezone.utc)
    sessions = load_sessions_index()

    if args.session:
        sessions = filter_by_session_id(sessions, args.session)
    elif args.period:
        delta = parse_period(args.period)
        sessions = filter_sessions_by_period(sessions, delta, now=now)

    report = build_report(sessions, breakdowns, now=now)

    if args.format == "json":
        output_str = json.dumps(report, indent=2)
    else:
        output_str = None

    if output_str is not None and args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            f.write(output_str)
        print(f"Report written to {args.output}")
    elif output_str is not None:
        print(output_str)
    else:
        print_report_text(report, breakdowns)
        if args.output:
            with open(args.output, "w") as f:
                f.write(f"OpenClaw Token Report\n")
                f.write(f"Total Tokens: {report['totalTokens']}\n")

    if args.save:
        today_str = now.strftime("%Y-%m-%d")
        save_path = WS_DIR / "token-usage" / "daily" / f"{today_str}.json"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Daily snapshot saved to {save_path}")

if __name__ == "__main__":
    main()
'''

script_path = SKILLS_DIR / "token-counter" / "scripts" / "token-counter"
with open(script_path, "w") as f:
    f.write(TOKEN_COUNTER_SCRIPT)

# ── quick_validate.py stub ───────────────────────────────────────────────────
validate_script = SKILLS_DIR / "skill-creator" / "scripts" / "quick_validate.py"
with open(validate_script, "w") as f:
    f.write('''#!/usr/bin/env python3
import sys, json
from pathlib import Path
skill_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
required = ["scripts/token-counter", "references/classification-rules.md"]
missing = [r for r in required if not (skill_dir / r).exists()]
if missing:
    print(f"WARN: missing: {missing}")
else:
    print("OK: skill structure valid")
''')

# ── references/classification-rules.md ──────────────────────────────────────
rules_md = SKILLS_DIR / "token-counter" / "references" / "classification-rules.md"
with open(rules_md, "w") as f:
    f.write("""# Classification Rules

## Client Detection
- `personal`: path contains `/personal/`, `/home/user/`, email ends in `@personal.com`
- `bonsai`: path contains `/bonsai/`, `/clients/bonsai/`, domain `bonsai.io`
- `mixed`: session touches both personal and bonsai resources
- `unknown`: none of the above markers matched

## Category Keywords
- `coding`: commit, diff, patch, refactor, implement, debug
- `research`: search, summarize, literature, paper, arxiv
- `data-analysis`: pandas, dataframe, csv, chart, plot, query
- `ops`: deploy, cron, monitor, alert, sync, pipeline
- `writing`: draft, edit, proofread, blog, document
""")

# ── distractor files ─────────────────────────────────────────────────────────
distractors = [
    (DATA_DIR / "agents" / "main" / "memory" / "memory.json",
     json.dumps({"facts": ["user prefers dark mode", "timezone: UTC+9"], "version": 3})),
    (DATA_DIR / "logs" / "agent-errors-2025-06-09.log",
     "2025-06-09T03:12:44Z ERROR: tool timeout bash after 30s\n2025-06-09T07:55:01Z WARN: rate limit approaching\n"),
    (DATA_DIR / "logs" / "agent-debug-2025-06-10.log",
     "DEBUG session started\nDEBUG transcript flushed\nDEBUG session closed\n"),
    (DATA_DIR / "config" / "agent.yaml",
     "model: claude-opus-4-5\nmax_tokens: 16000\ntimeout: 120\nretry: 3\n"),
    (DATA_DIR / "config" / "tools.json",
     json.dumps({"enabled_tools": ["bash","read_file","write_file","web_search","python_repl"]})),
    (DATA_DIR / "agents" / "sub" / "sessions" / "README.txt",
     "Sub-agent sessions are not yet indexed. Manual parsing required.\n"),
    (WORKSPACE / "reports" / "archived" / "old-report-2025-05.txt",
     "Monthly report May 2025\nTotal tokens: 4,201,337\n(archived, do not modify)\n"),
    (WORKSPACE / "tmp" / "scratch.json",
     json.dumps({"note": "temporary scratch space", "delete_after": "2025-07-01"})),
    (WORKSPACE / "exports" / "placeholder.txt",
     "This directory is for exported reports.\n"),
    (SKILLS_DIR / "token-counter" / "tests" / "test_parser.py",
     "# placeholder test file\nimport unittest\nclass TestParser(unittest.TestCase): pass\n"),
    (SKILLS_DIR / "token-counter" / "references" / "model-pricing.json",
     json.dumps({
         "claude-opus-4-5":    {"input": 15.0, "output": 75.0},
         "claude-sonnet-3-7":  {"input": 3.0,  "output": 15.0},
         "claude-haiku-3-5":   {"input": 0.8,  "output": 4.0},
     })),
]

for path, content in distractors:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"  DATA_DIR   : {DATA_DIR}")
print(f"  SKILLS_DIR : {SKILLS_DIR}")
print(f"  WORKSPACE  : {WORKSPACE}")
print(f"  Sessions   : {len(sessions_index)} sessions generated")