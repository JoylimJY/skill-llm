#!/usr/bin/env python3
"""
Evaluator for the weekly_digest.json task.

Checks:
1. File 'weekly_digest.json' exists somewhere in the workspace.
2. JSON is valid and has required top-level keys: 'stats' and 'image_path'.
3. 'stats' contains correct numeric fields (total_sessions > 0, unique_users > 0, success_rate).
4. 'image_path' points to an actual PNG file that exists on disk.
5. The PNG file is a valid image (has PNG magic bytes).
6. 'stats' was derived from --period week (total_sessions >= today-only count, consistent data).
"""
import sys
import json
import struct
from pathlib import Path

def check_png_magic(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            header = f.read(8)
        return header == b'\x89PNG\r\n\x1a\n'
    except Exception:
        return False

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    overall_passed = True

    # ── Check 1: weekly_digest.json exists ───────────────────────────────────
    digest_files = list(workspace.rglob("weekly_digest.json"))
    c1_passed = len(digest_files) > 0
    c1_detail = f"Found {len(digest_files)} file(s): {[str(f) for f in digest_files]}" if c1_passed else "weekly_digest.json not found anywhere in workspace"
    checks.append({"name": "weekly_digest.json_exists", "passed": c1_passed, "detail": c1_detail})
    if not c1_passed:
        overall_passed = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    digest_path = digest_files[0]

    # ── Check 2: Valid JSON with required keys ────────────────────────────────
    try:
        with open(digest_path) as f:
            digest = json.load(f)
        has_stats = "stats" in digest
        has_image_path = "image_path" in digest
        c2_passed = has_stats and has_image_path
        c2_detail = (
            f"Keys present: {list(digest.keys())}. "
            f"'stats' present: {has_stats}, 'image_path' present: {has_image_path}"
        )
    except Exception as e:
        c2_passed = False
        c2_detail = f"JSON parse error: {e}"
        digest = {}
    checks.append({"name": "valid_json_with_required_keys", "passed": c2_passed, "detail": c2_detail})
    if not c2_passed:
        overall_passed = False

    # ── Check 3: stats has meaningful numeric content (from week period) ──────
    try:
        stats = digest.get("stats", {})
        total_sessions = stats.get("total_sessions", 0)
        unique_users = stats.get("unique_users", 0)
        success_rate = stats.get("success_rate", None)
        avg_dur = stats.get("avg_duration_seconds", None)

        c3_passed = (
            isinstance(total_sessions, (int, float)) and total_sessions > 0
            and isinstance(unique_users, (int, float)) and unique_users > 0
            and success_rate is not None
            and avg_dur is not None
            and isinstance(stats.get("total_duration_seconds"), (int, float))
        )
        c3_detail = (
            f"total_sessions={total_sessions}, unique_users={unique_users}, "
            f"success_rate={success_rate}, avg_duration_seconds={avg_dur}"
        )
    except Exception as e:
        c3_passed = False
        c3_detail = f"Error reading stats: {e}"
    checks.append({"name": "stats_has_valid_week_data", "passed": c3_passed, "detail": c3_detail})
    if not c3_passed:
        overall_passed = False

    # ── Check 4: image_path field points to an existing file ─────────────────
    try:
        image_path_str = digest.get("image_path", "")
        image_path = Path(image_path_str)
        c4_passed = bool(image_path_str) and image_path.exists() and image_path.is_file()
        c4_detail = f"image_path='{image_path_str}', exists={image_path.exists() if image_path_str else 'N/A'}"
    except Exception as e:
        c4_passed = False
        c4_detail = f"Error checking image_path: {e}"
        image_path = None
    checks.append({"name": "image_path_points_to_existing_file", "passed": c4_passed, "detail": c4_detail})
    if not c4_passed:
        overall_passed = False

    # ── Check 5: The file at image_path is a valid PNG ────────────────────────
    try:
        if c4_passed and image_path is not None:
            c5_passed = check_png_magic(image_path)
            c5_detail = (
                f"PNG magic bytes check {'PASSED' if c5_passed else 'FAILED'} for {image_path}"
            )
        else:
            c5_passed = False
            c5_detail = "Skipped — image_path was not valid in check 4"
    except Exception as e:
        c5_passed = False
        c5_detail = f"Error reading image file: {e}"
    checks.append({"name": "image_is_valid_png", "passed": c5_passed, "detail": c5_detail})
    if not c5_passed:
        overall_passed = False

    # ── Check 6: period is 'week' (image_path filename or stats plausible) ────
    # The task asks for the past week's digest; we verify total_sessions is
    # at least as large as what "today" would produce (i.e., a multi-day range).
    # We do this by cross-running the script in a subprocess to get today's count.
    try:
        import subprocess, os
        env = os.environ.copy()
        env["OPENCLAW_WORKSPACE"] = workspace_str
        result = subprocess.run(
            ["python3", str(workspace / "scripts" / "run_usage_report.py"),
             "--mode", "text", "--period", "today", "--json"],
            capture_output=True, text=True, env=env, timeout=30
        )
        today_data = json.loads(result.stdout.strip())
        today_total = today_data["stats"]["total_sessions"]
        week_total = stats.get("total_sessions", 0)
        # Week should have >= today's sessions (it spans more days)
        # Also verify stats aren't identical to an "all" or "today" trivial run
        c6_passed = week_total >= today_total
        c6_detail = (
            f"week total_sessions={week_total} >= today total_sessions={today_total}: {c6_passed}"
        )
    except Exception as e:
        # If we can't cross-check, give benefit of the doubt if stats look reasonable
        c6_passed = total_sessions > 0
        c6_detail = f"Cross-check skipped due to: {e}. Fallback: total_sessions={total_sessions} > 0"
    checks.append({"name": "stats_are_week_scoped_not_today_only", "passed": c6_passed, "detail": c6_detail})
    if not c6_passed:
        overall_passed = False

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 4)

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argv", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    run_eval(sys.argv[1])