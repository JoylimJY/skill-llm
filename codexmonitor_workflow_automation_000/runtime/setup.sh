#!/bin/bash
set -e

# ── Create the mock codexmonitor binary ───────────────────────────────────
# This mock correctly implements the CLI interface described in SKILL.md
# and records invocation logs for evaluation.

cat > /usr/local/bin/codexmonitor << 'PYEOF'
#!/usr/bin/env python3
"""
Mock codexmonitor binary implementing the SKILL.md interface.
Reads session data from /workspace/.mock_codexmonitor_data.json
"""
import sys
import os
import json
import re
from pathlib import Path

DATA_FILE = Path("/workspace/.mock_codexmonitor_data.json")
LOG_FILE = Path("/workspace/.mock_codexmonitor_invocations.jsonl")

def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)

def log_invocation(args, env_vars):
    entry = {"args": args, "env": env_vars}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def get_sessions_dir(data, env):
    """Resolve sessions dir per SKILL.md: CODEX_SESSIONS_DIR > CODEX_HOME/sessions > default"""
    if "CODEX_SESSIONS_DIR" in env:
        return env["CODEX_SESSIONS_DIR"]
    elif "CODEX_HOME" in env:
        return os.path.join(env["CODEX_HOME"], "sessions")
    else:
        return os.path.expanduser("~/.codex/sessions")

def main():
    args = sys.argv[1:]
    env = {k: v for k, v in os.environ.items() if k.startswith("CODEX")}
    log_invocation(args, env)

    data = load_data()
    configured_sessions_dir = get_sessions_dir(data, env)
    expected_sessions_dir = data["sessions_root"]

    if not args:
        print("Usage: codexmonitor <command> [options]")
        print("Commands: list, show, watch")
        sys.exit(0)

    cmd = args[0]

    # ── version ──────────────────────────────────────────────────────────
    if cmd == "--version":
        print("codexmonitor 0.2.2")
        sys.exit(0)

    # ── list ─────────────────────────────────────────────────────────────
    elif cmd == "list":
        use_json = "--json" in args
        # Find date arg (not a flag)
        date_arg = None
        for a in args[1:]:
            if not a.startswith("--"):
                date_arg = a
                break

        if not date_arg:
            print("Error: date required for list command (format: YYYY/MM/DD)", file=sys.stderr)
            sys.exit(1)

        # Validate the configured sessions dir matches expected
        correct_dir = (configured_sessions_dir == expected_sessions_dir or
                       configured_sessions_dir.rstrip("/") == expected_sessions_dir.rstrip("/"))

        if date_arg == data["target_date"] and correct_dir:
            sessions_list = [
                {
                    "id": data["session_a"]["id"],
                    "date": "2025-03-15",
                    "turns": data["session_a"]["turns"],
                    "first_message": data["session_a"]["turns_data"][0]["content"][:60]
                },
                {
                    "id": data["session_b"]["id"],
                    "date": "2025-03-15",
                    "turns": data["session_b"]["turns"],
                    "first_message": data["session_b"]["turns_data"][0]["content"][:60]
                }
            ]
            if use_json:
                print(json.dumps({"date": date_arg, "sessions": sessions_list}, indent=2))
            else:
                print(f"Sessions for {date_arg}:")
                for s in sessions_list:
                    print(f"  {s['id']}  ({s['turns']} turns)  {s['first_message']}")
        else:
            if use_json:
                print(json.dumps({"date": date_arg, "sessions": [], "error": "no sessions found or wrong directory"}))
            else:
                print(f"No sessions found for {date_arg}")

    # ── show ─────────────────────────────────────────────────────────────
    elif cmd == "show":
        use_json = "--json" in args
        ranges_arg = None
        session_id = None

        i = 1
        while i < len(args):
            if args[i] == "--ranges" and i + 1 < len(args):
                ranges_arg = args[i + 1]
                i += 2
            elif args[i] == "--json":
                i += 1
            elif not args[i].startswith("--"):
                session_id = args[i]
                i += 1
            else:
                i += 1

        if not session_id:
            print("Error: session-id required", file=sys.stderr)
            sys.exit(1)

        # Identify which session
        if session_id == data["session_a"]["id"]:
            session = data["session_a"]
        elif session_id == data["session_b"]["id"]:
            session = data["session_b"]
        else:
            print(f"Error: session {session_id} not found", file=sys.stderr)
            sys.exit(1)

        turns_data = session["turns_data"]

        # Parse ranges: format is N...M,N...M (triple dots per SKILL.md)
        if ranges_arg:
            # Must use triple dots: N...M
            selected_turns = []
            range_pattern = re.compile(r'^(\d+)\.\.\.(\d+)$')
            range_specs = ranges_arg.split(",")
            valid_ranges = True
            for spec in range_specs:
                m = range_pattern.match(spec.strip())
                if not m:
                    # Wrong format (e.g., double dots or dash) — return error
                    print(f"Error: invalid range format '{spec}'. Use N...M (triple dots).", file=sys.stderr)
                    sys.exit(1)
                start, end = int(m.group(1)), int(m.group(2))
                for t in turns_data:
                    if start <= t["turn"] <= end:
                        selected_turns.append(t)
            # Deduplicate preserving order
            seen = set()
            deduped = []
            for t in selected_turns:
                if t["turn"] not in seen:
                    seen.add(t["turn"])
                    deduped.append(t)
            output_turns = deduped
        else:
            output_turns = turns_data

        if use_json:
            print(json.dumps({
                "session_id": session_id,
                "turns": output_turns
            }, indent=2))
        else:
            print(f"Session: {session_id}")
            for t in output_turns:
                print(f"  [{t['turn']}] {t['role'].upper()}: {t['content']}")

    # ── watch ─────────────────────────────────────────────────────────────
    elif cmd == "watch":
        print("Watching sessions... (mock: no live sessions)")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
PYEOF

chmod +x /usr/local/bin/codexmonitor

# Initialize invocation log
echo "" > /workspace/.mock_codexmonitor_invocations.jsonl

echo "Mock codexmonitor installed at /usr/local/bin/codexmonitor"
codexmonitor --version