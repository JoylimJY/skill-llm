#!/usr/bin/env python3
"""Evaluation script for codex-quota task."""

import json
import sys
import os
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    workspace_path = Path(workspace)
    home = Path(os.path.expanduser("~"))
    sessions_root = home / ".codex" / "sessions"

    # ── CHECK 1: quota_report.json exists somewhere in the workspace ──
    report_files = list(workspace_path.rglob("quota_report.json"))
    if not report_files:
        checks.append({
            "name": "quota_report.json exists",
            "passed": False,
            "detail": "No quota_report.json found anywhere in the workspace."
        })
        return False, 0.0, checks

    report_file = report_files[0]
    checks.append({
        "name": "quota_report.json exists",
        "passed": True,
        "detail": f"Found at {report_file}"
    })

    # ── CHECK 2: File is valid JSON ──
    try:
        with open(report_file) as f:
            data = json.load(f)
        checks.append({
            "name": "quota_report.json is valid JSON",
            "passed": True,
            "detail": f"Parsed successfully."
        })
    except Exception as e:
        checks.append({
            "name": "quota_report.json is valid JSON",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        return False, 1.0/4.0, checks

    # ── CHECK 3: JSON has the correct top-level structure from --json output ──
    # The codex-quota.py --json flag outputs:
    # { "source_file": ..., "file_age_minutes": ..., "primary_window": {...}, "secondary_window": {...} }
    required_keys = {"source_file", "file_age_minutes", "primary_window", "secondary_window"}
    present_keys = set(data.keys()) if isinstance(data, dict) else set()
    missing_keys = required_keys - present_keys
    if missing_keys:
        checks.append({
            "name": "JSON output has correct codex-quota structure",
            "passed": False,
            "detail": f"Missing required keys: {missing_keys}. Got keys: {present_keys}. "
                      "The agent must use codex-quota.py --json, not hand-craft the output."
        })
        return False, 2.0/4.0, checks
    checks.append({
        "name": "JSON output has correct codex-quota structure",
        "passed": True,
        "detail": f"All required keys present: {required_keys}"
    })

    # ── CHECK 4: primary_window and secondary_window have sub-keys: used, limit, reset_at ──
    primary = data.get("primary_window", {})
    secondary = data.get("secondary_window", {})
    window_keys = {"used", "limit", "reset_at"}

    primary_ok = isinstance(primary, dict) and window_keys.issubset(primary.keys())
    secondary_ok = isinstance(secondary, dict) and window_keys.issubset(secondary.keys())

    if not primary_ok or not secondary_ok:
        checks.append({
            "name": "Window objects contain used/limit/reset_at",
            "passed": False,
            "detail": (
                f"primary_window keys: {list(primary.keys()) if isinstance(primary, dict) else 'not a dict'}, "
                f"secondary_window keys: {list(secondary.keys()) if isinstance(secondary, dict) else 'not a dict'}. "
                "Expected both to have: used, limit, reset_at."
            )
        })
        return False, 2.5/4.0, checks
    checks.append({
        "name": "Window objects contain used/limit/reset_at",
        "passed": True,
        "detail": "primary_window and secondary_window both contain used, limit, reset_at."
    })

    # ── CHECK 5: Values are NOT from the stale mid-age session (used=9999/49999) ──
    # The agent must create a NEWER session file with fresh/non-extreme values,
    # OR the report must NOT reflect the stale "almost maxed" values from mid session.
    # The trap: mid session has primary.used=9999, limit=10000 and secondary.used=49999, limit=50000
    # If agent simply reads an existing session and doesn't create a newer one,
    # they'd be stuck with those stale values (the old session has no rate_limits).
    # Either way the agent needs to create a valid recent session file.
    
    primary_used = primary.get("used")
    secondary_used = secondary.get("used")
    
    stale_trap = (primary_used == 9999 and secondary_used == 49999)
    if stale_trap:
        checks.append({
            "name": "Report does not use stale outdated session data",
            "passed": False,
            "detail": (
                "The report appears to use the outdated mid-age session file (primary.used=9999, secondary.used=49999). "
                "A newer session file with updated rate_limits should have been created."
            )
        })
        return False, 3.0/4.0, checks

    # ── CHECK 6: A newer session file exists in the correct YYYY/MM/DD structure ──
    from datetime import datetime, timedelta
    today = datetime.now()
    today_dir = sessions_root / today.strftime("%Y") / today.strftime("%m") / today.strftime("%d")
    today_sessions = list(today_dir.glob("*.jsonl")) if today_dir.exists() else []

    # Also check yesterday in case boundary
    yesterday = today - timedelta(days=1)
    yesterday_dir = sessions_root / yesterday.strftime("%Y") / yesterday.strftime("%m") / yesterday.strftime("%d")
    yesterday_sessions_new = [
        f for f in (yesterday_dir.glob("*.jsonl") if yesterday_dir.exists() else [])
    ]

    has_recent_session = len(today_sessions) > 0

    if not has_recent_session:
        # Check if source_file in report points to a file newer than the mid session
        source_file_path = Path(data.get("source_file", ""))
        if source_file_path.exists():
            import time
            mid_date_approx = (datetime.now() - timedelta(days=1)).timestamp()
            file_mtime = source_file_path.stat().st_mtime
            has_recent_session = file_mtime > mid_date_approx
            detail = f"source_file {source_file_path} mtime check: {'newer than mid session' if has_recent_session else 'not newer'}"
        else:
            detail = f"No session file found in today's directory ({today_dir}) and source_file path invalid."
        checks.append({
            "name": "New session file created in correct YYYY/MM/DD path",
            "passed": has_recent_session,
            "detail": detail
        })
    else:
        checks.append({
            "name": "New session file created in correct YYYY/MM/DD path",
            "passed": True,
            "detail": f"Found {len(today_sessions)} session file(s) in {today_dir}"
        })

    # ── CHECK 7: The session file contains a token_count event with rate_limits ──
    # Find all session files and look for valid token_count events
    all_sessions = sorted(sessions_root.rglob("*.jsonl"))
    found_valid_token_count = False
    newest_rate_limits = None
    newest_file = None
    
    for sf in all_sessions:
        try:
            with open(sf) as f:
                lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    if event.get("type") == "token_count" and "rate_limits" in event:
                        found_valid_token_count = True
                        newest_rate_limits = event["rate_limits"]
                        newest_file = sf
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

    if not found_valid_token_count:
        checks.append({
            "name": "Session JSONL contains valid token_count event with rate_limits",
            "passed": False,
            "detail": "No token_count event with rate_limits found in any session JSONL file."
        })
    else:
        checks.append({
            "name": "Session JSONL contains valid token_count event with rate_limits",
            "passed": True,
            "detail": f"Found valid token_count+rate_limits in {newest_file}"
        })

    # Calculate score
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total

    all_passed = all(c["passed"] for c in checks)
    return all_passed, score, checks


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace path provided."}
        ]}))
        sys.exit(1)

    workspace = sys.argv[1]
    try:
        all_passed, score, checks = run_checks(workspace)
        print(json.dumps({
            "passed": all_passed,
            "score": round(score, 3),
            "checks": checks
        }, indent=2))
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }))


if __name__ == "__main__":
    main()