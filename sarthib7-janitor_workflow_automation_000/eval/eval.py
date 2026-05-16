import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Check 1: janitor_report.json exists somewhere in workspace ──────────
    report_files = list(workspace.rglob("janitor_report.json"))
    if not report_files:
        checks.append({"name": "report_file_exists", "passed": False, "detail": "janitor_report.json not found anywhere in workspace"})
        return finalize(checks)
    
    report_path = report_files[0]
    checks.append({"name": "report_file_exists", "passed": True, "detail": f"Found at {report_path}"})
    
    # ── Check 2: Report is valid JSON with required structure ────────────────
    try:
        with open(report_path) as f:
            report = json.load(f)
        checks.append({"name": "report_valid_json", "passed": True, "detail": "Report is valid JSON"})
    except Exception as e:
        checks.append({"name": "report_valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return finalize(checks)
    
    # ── Check 3: Report has expected top-level fields ────────────────────────
    required_fields = ["timestamp", "status", "stats", "recommendations"]
    missing = [f for f in required_fields if f not in report]
    if missing:
        checks.append({"name": "report_has_required_fields", "passed": False, "detail": f"Missing fields: {missing}"})
    else:
        checks.append({"name": "report_has_required_fields", "passed": True, "detail": f"All required fields present: {required_fields}"})
    
    # ── Check 4: Status is 'healthy' ─────────────────────────────────────────
    status_val = report.get("status", "")
    status_ok = status_val == "healthy"
    checks.append({"name": "report_status_healthy", "passed": status_ok, "detail": f"status={status_val!r} (expected 'healthy')"})
    
    # ── Check 5: stats.totalCleanups >= 2 (proves single instance reuse) ────
    stats = report.get("stats", {})
    total_cleanups = stats.get("totalCleanups", 0)
    cleanups_ok = total_cleanups >= 2
    checks.append({
        "name": "stats_total_cleanups_gte_2",
        "passed": cleanups_ok,
        "detail": f"totalCleanups={total_cleanups} (must be >= 2, proves same Janitor instance used for both passes)"
    })
    
    # ── Check 6: stats has required sub-fields ───────────────────────────────
    stats_fields = ["totalCleanups", "totalFilesDeleted", "totalSpaceSaved", "memoryUsage"]
    missing_stats = [f for f in stats_fields if f not in stats]
    if missing_stats:
        checks.append({"name": "stats_has_required_fields", "passed": False, "detail": f"Missing stats fields: {missing_stats}"})
    else:
        checks.append({"name": "stats_has_required_fields", "passed": True, "detail": "All stats sub-fields present"})
    
    # ── Check 7: recommendations is non-empty list ───────────────────────────
    recs = report.get("recommendations", [])
    recs_ok = isinstance(recs, list) and len(recs) > 0
    checks.append({
        "name": "recommendations_non_empty",
        "passed": recs_ok,
        "detail": f"recommendations has {len(recs) if isinstance(recs, list) else 'N/A'} entries (must be >= 1)"
    })
    
    # ── Check 8: audit_trail.json is still intact (custom isImportant) ──────
    audit_path = workspace / "fintech_project" / "audit_trail.json"
    if not audit_path.exists():
        checks.append({"name": "audit_trail_protected", "passed": False, "detail": "audit_trail.json was deleted — isImportant override was not applied correctly"})
    else:
        try:
            with open(audit_path) as f:
                audit_data = json.load(f)
            has_entries = "entries" in audit_data and len(audit_data["entries"]) == 3
            checks.append({
                "name": "audit_trail_protected",
                "passed": has_entries,
                "detail": f"audit_trail.json exists and has {len(audit_data.get('entries', []))} entries (expected 3)"
            })
        except Exception as e:
            checks.append({"name": "audit_trail_protected", "passed": False, "detail": f"audit_trail.json corrupted: {e}"})
    
    # ── Check 9: Cache/tmp/coverage files were actually cleaned up ───────────
    project = workspace / "fintech_project"
    
    # Files that should have been deleted
    should_be_gone = [
        project / "babel.cache",
        project / "webpack.cache",
        project / "eslint.cache",
        project / ".DS_Store",
        project / "tmp" / "session_abc123.tmp",
        project / "tmp" / "upload_xyz.tmp",
        project / "dist" / "bundle.js.map",
        project / "dist" / "vendor.js.map",
    ]
    
    still_present = [str(p) for p in should_be_gone if p.exists()]
    
    # We expect at least 5 of these to be gone (some may vary based on config)
    cleaned_count = len(should_be_gone) - len(still_present)
    cleanup_ok = cleaned_count >= 5
    checks.append({
        "name": "cache_files_cleaned",
        "passed": cleanup_ok,
        "detail": f"{cleaned_count}/{len(should_be_gone)} cache/tmp/map files deleted. Still present: {still_present[:3] if still_present else 'none'}"
    })
    
    # ── Check 10: Protected src/ files are still present ────────────────────
    protected = [
        workspace / "fintech_project" / "src" / "index.js",
        workspace / "fintech_project" / "src" / "payments.js",
        workspace / "fintech_project" / "package.json",
    ]
    missing_protected = [str(p) for p in protected if not p.exists()]
    src_ok = len(missing_protected) == 0
    checks.append({
        "name": "protected_src_files_intact",
        "passed": src_ok,
        "detail": f"Missing protected files: {missing_protected if missing_protected else 'none — all intact'}"
    })
    
    return finalize(checks)


def finalize(checks):
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3) if total > 0 else 0.0
    overall = passed_count == total
    return {
        "passed": overall,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))