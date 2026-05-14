#!/usr/bin/env python3
"""
Evaluation script for the token-counter task.
Checks:
1. The explicit JSON export file exists at the path the agent specified.
2. The daily snapshot file exists under token-usage/daily/YYYY-MM-DD.json.
3. Both files are valid JSON.
4. The export file contains breakdowns for tools, category, and client (all three required).
5. The export file covers 7d period (i.e., has > 0 sessions and > 0 tokens).
6. The daily snapshot matches the structural schema (has totalTokens, breakdowns, etc.).
7. The breakdowns in the export contain at least one entry each for tools, category, client.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

def main(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    overall_passed = True

    def add_check(name, passed, detail):
        nonlocal overall_passed
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            overall_passed = False

    # ── 1. Find the explicit JSON export (not the daily snapshot) ────────────
    # The agent was asked to export to a file named token-usage-7d.json
    openclaw_workspace = Path("/workspace/openclaw_workspace")

    export_file = None
    candidates = list(openclaw_workspace.rglob("token-usage-7d.json"))
    # Also accept any file named *7d*.json outside of daily/ folder
    if not candidates:
        candidates = [
            p for p in openclaw_workspace.rglob("*.json")
            if "daily" not in str(p) and "7d" in p.name
        ]

    if candidates:
        export_file = candidates[0]
        add_check(
            "export_file_exists",
            True,
            f"Found export file at: {export_file}"
        )
    else:
        add_check(
            "export_file_exists",
            False,
            "No token-usage-7d.json file found in openclaw_workspace (excluding daily/)"
        )

    # ── 2. Export file is valid JSON ─────────────────────────────────────────
    export_data = None
    if export_file:
        try:
            with open(export_file) as f:
                export_data = json.load(f)
            add_check("export_file_valid_json", True, "Export file is valid JSON")
        except Exception as e:
            add_check("export_file_valid_json", False, f"JSON parse error: {e}")
    else:
        add_check("export_file_valid_json", False, "Export file not found, cannot parse")

    # ── 3. Export covers 7d period with real data ────────────────────────────
    if export_data:
        total_sessions = export_data.get("totalSessions", 0)
        total_tokens   = export_data.get("totalTokens", 0)
        ok = total_sessions > 0 and total_tokens > 0
        add_check(
            "export_has_real_data",
            ok,
            f"totalSessions={total_sessions}, totalTokens={total_tokens}"
        )
    else:
        add_check("export_has_real_data", False, "No export data to check")

    # ── 4. Export has breakdowns for tools, category, AND client ─────────────
    if export_data:
        breakdowns = export_data.get("breakdowns", {})
        required_bks = {"tools", "category", "client"}
        present_bks  = set(breakdowns.keys())
        missing_bks  = required_bks - present_bks
        ok = len(missing_bks) == 0
        add_check(
            "export_has_required_breakdowns",
            ok,
            f"Present breakdowns: {sorted(present_bks)}. "
            f"Missing: {sorted(missing_bks) if missing_bks else 'none'}"
        )
    else:
        add_check("export_has_required_breakdowns", False, "No export data")

    # ── 5. Each required breakdown has at least one entry ────────────────────
    if export_data:
        breakdowns = export_data.get("breakdowns", {})
        non_empty = {k: len(v) > 0 for k, v in breakdowns.items() if k in {"tools","category","client"}}
        all_non_empty = all(non_empty.values()) and len(non_empty) == 3
        add_check(
            "breakdowns_are_populated",
            all_non_empty,
            f"Non-empty check per breakdown: {non_empty}"
        )
    else:
        add_check("breakdowns_are_populated", False, "No export data")

    # ── 6. Daily snapshot exists ─────────────────────────────────────────────
    daily_dir = openclaw_workspace / "token-usage" / "daily"
    daily_files = list(daily_dir.glob("*.json")) if daily_dir.exists() else []
    # Accept any file matching YYYY-MM-DD.json pattern
    import re
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}\.json$')
    valid_daily = [f for f in daily_files if date_pattern.match(f.name)]

    if valid_daily:
        add_check(
            "daily_snapshot_exists",
            True,
            f"Daily snapshot found: {[f.name for f in valid_daily]}"
        )
    else:
        add_check(
            "daily_snapshot_exists",
            False,
            f"No YYYY-MM-DD.json file found in {daily_dir}"
        )

    # ── 7. Daily snapshot is valid JSON with correct structure ───────────────
    daily_data = None
    if valid_daily:
        try:
            with open(valid_daily[0]) as f:
                daily_data = json.load(f)
            required_keys = {"generatedAt", "totalSessions", "totalTokens",
                             "totalInputTokens", "totalOutputTokens", "breakdowns"}
            present_keys = set(daily_data.keys())
            missing_keys = required_keys - present_keys
            ok = len(missing_keys) == 0
            add_check(
                "daily_snapshot_valid_structure",
                ok,
                f"Present keys: {sorted(present_keys)}. Missing: {sorted(missing_keys) if missing_keys else 'none'}"
            )
        except Exception as e:
            add_check("daily_snapshot_valid_structure", False, f"Error reading daily snapshot: {e}")
    else:
        add_check("daily_snapshot_valid_structure", False, "No daily snapshot to validate")

    # ── 8. Daily snapshot covers a 1-day period (subset of 7d) ──────────────
    if daily_data:
        total_t = daily_data.get("totalTokens", 0)
        export_t = export_data.get("totalTokens", 0) if export_data else 0
        # Daily should have fewer or equal tokens than 7d report
        ok = total_t > 0 and (export_t == 0 or total_t <= export_t)
        add_check(
            "daily_snapshot_plausible_token_count",
            ok,
            f"Daily totalTokens={total_t}, 7d totalTokens={export_t}. "
            f"Daily should be ≤ 7d and > 0."
        )
    else:
        add_check("daily_snapshot_plausible_token_count", False, "No daily snapshot data")

    # ── score ─────────────────────────────────────────────────────────────────
    n_passed = sum(1 for c in checks if c["passed"])
    score = round(n_passed / len(checks), 3)

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "workspace dir argument missing"}]}))
        sys.exit(1)
    main(sys.argv[1])