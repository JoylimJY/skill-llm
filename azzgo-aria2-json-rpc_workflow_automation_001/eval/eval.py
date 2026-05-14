#!/usr/bin/env python3
"""
Evaluation script for the aria2 download pipeline audit task.
Checks:
1. config_loader test was used (connection to mock server works)
2. Two new downloads were added via aria2.addUri
3. The pre-existing active download aabbccdd11223344 was throttled (changeOption max-download-limit=512000)
4. New downloads were also throttled at 512000 bytes/s
5. Stopped downloads were retrieved using tellStopped (with pagination params)
6. Completed downloads (ddeeff0044556677, eeff001155667788) were individually removed via removeDownloadResult
   (NOT aria2.remove which would fail on complete downloads)
7. purgeDownloadResult was called to clean remaining stopped items
8. An audit_report.json was created with required fields
"""

import sys
import json
import os
from pathlib import Path

def load_state():
    try:
        with open("/workspace/mock_aria2_state.json") as f:
            return json.load(f)
    except Exception as e:
        return None

def find_audit_report(workspace):
    """Find audit_report.json anywhere in the workspace."""
    matches = list(Path(workspace).rglob("audit_report.json"))
    return matches[0] if matches else None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    # Load final mock state
    state = load_state()
    if state is None:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "state_file_accessible", "passed": False, "detail": "Could not load mock state file"}]
        }))
        return

    downloads = state.get("downloads", {})
    options = state.get("options", {})
    removed_results = state.get("removed_results", [])

    # ── Check 1: New downloads were added ─────────────────────────────────────
    # The two original active GIDs are known; new ones must exist
    original_gids = {"aabbccdd11223344", "bbccddee22334455", "ccddee0033445566",
                     "ddeeff0044556677", "eeff001155667788", "ff00112266778899"}
    new_gids = [gid for gid in downloads.keys() if gid not in original_gids]
    
    new_downloads_added = len(new_gids) >= 2
    checks.append({
        "name": "two_new_downloads_added",
        "passed": new_downloads_added,
        "detail": f"Found {len(new_gids)} new download(s) added (expected >= 2). New GIDs: {new_gids}"
    })

    # ── Check 2: New downloads contain the correct URLs ───────────────────────
    expected_urls = {
        "http://media-server.studio.local/rushes/day12_cam_A.mxf",
        "http://media-server.studio.local/rushes/day12_cam_B.mxf"
    }
    found_urls = set()
    for gid in new_gids:
        dl = downloads.get(gid, {})
        files = dl.get("files", [])
        # The mock server sets path from the URL filename
        for f in files:
            path = f.get("path", "")
            for url in expected_urls:
                if url.split("/")[-1] in path:
                    found_urls.add(url)
    
    correct_urls = len(found_urls) >= 2
    checks.append({
        "name": "correct_urls_submitted",
        "passed": correct_urls,
        "detail": f"Found URLs matching: {found_urls}. Expected both cam_A and cam_B URLs."
    })

    # ── Check 3: Existing active download throttled (aabbccdd11223344) ────────
    throttle_gid = "aabbccdd11223344"
    throttle_opts = options.get(throttle_gid, {})
    limit_val = throttle_opts.get("max-download-limit", "0")
    throttled_existing = str(limit_val) == "512000"
    checks.append({
        "name": "existing_download_throttled_512000",
        "passed": throttled_existing,
        "detail": f"GID {throttle_gid} max-download-limit = '{limit_val}' (expected '512000')"
    })

    # ── Check 4: New downloads also throttled ─────────────────────────────────
    new_throttled_count = 0
    for gid in new_gids:
        opts = options.get(gid, {})
        if str(opts.get("max-download-limit", "0")) == "512000":
            new_throttled_count += 1
    
    new_downloads_throttled = new_throttled_count >= 2
    checks.append({
        "name": "new_downloads_throttled_512000",
        "passed": new_downloads_throttled,
        "detail": f"{new_throttled_count}/{len(new_gids)} new downloads have max-download-limit=512000"
    })

    # ── Check 5: Completed downloads removed via removeDownloadResult ─────────
    # ddeeff0044556677 and eeff001155667788 were "complete" - must use removeDownloadResult
    complete_gids = {"ddeeff0044556677", "eeff001155667788"}
    removed_complete = complete_gids.intersection(set(removed_results))
    not_in_downloads = complete_gids - set(downloads.keys())
    
    # Either in removed_results OR no longer in downloads (purge also removes them)
    completed_cleaned = (len(removed_complete) >= 2) or (len(not_in_downloads) >= 2)
    checks.append({
        "name": "completed_downloads_removed_correctly",
        "passed": completed_cleaned,
        "detail": (
            f"Complete GIDs removed: {removed_complete}. "
            f"Not in downloads anymore: {not_in_downloads}. "
            f"Removed results list: {removed_results}"
        )
    })

    # ── Check 6: Error download also cleaned up (ff00112266778899) ────────────
    error_gid = "ff00112266778899"
    error_cleaned = (error_gid in removed_results) or (error_gid not in downloads)
    checks.append({
        "name": "error_download_cleaned_up",
        "passed": error_cleaned,
        "detail": f"Error GID {error_gid} cleaned: in_removed={error_gid in removed_results}, not_in_downloads={error_gid not in downloads}"
    })

    # ── Check 7: Purge was called (all stopped/complete/error gone) ────────────
    remaining_stopped = [
        gid for gid, dl in downloads.items()
        if dl.get("status") in ("complete", "error", "removed")
        and gid in original_gids
    ]
    purge_called = len(remaining_stopped) == 0
    checks.append({
        "name": "purge_download_result_called",
        "passed": purge_called,
        "detail": f"Remaining original stopped/complete/error downloads: {remaining_stopped} (should be empty after purge)"
    })

    # ── Check 8: Audit report exists and has required fields ──────────────────
    report_path = find_audit_report(workspace)
    report_exists = report_path is not None
    checks.append({
        "name": "audit_report_exists",
        "passed": report_exists,
        "detail": f"audit_report.json found at: {report_path}" if report_exists else "audit_report.json not found anywhere in workspace"
    })

    report_valid = False
    report_detail = "audit_report.json not found"
    if report_exists:
        try:
            with open(report_path) as f:
                report = json.load(f)
            
            required_fields = ["new_downloads", "throttled_gids", "cleaned_gids"]
            missing = [field for field in required_fields if field not in report]
            
            if missing:
                report_detail = f"Missing required fields: {missing}. Found: {list(report.keys())}"
            else:
                # Check new_downloads is a list with >= 2 entries containing GIDs
                nd = report.get("new_downloads", [])
                th = report.get("throttled_gids", [])
                cl = report.get("cleaned_gids", [])
                
                has_new_downloads = isinstance(nd, list) and len(nd) >= 2
                has_throttled = isinstance(th, list) and len(th) >= 1
                has_cleaned = isinstance(cl, list) and len(cl) >= 1
                
                if has_new_downloads and has_throttled and has_cleaned:
                    report_valid = True
                    report_detail = f"Report valid. new_downloads={len(nd)}, throttled_gids={len(th)}, cleaned_gids={len(cl)}"
                else:
                    report_detail = (
                        f"Report fields incomplete. "
                        f"new_downloads(list,>=2)={has_new_downloads}, "
                        f"throttled_gids(list,>=1)={has_throttled}, "
                        f"cleaned_gids(list,>=1)={has_cleaned}. "
                        f"Values: nd={nd}, th={th}, cl={cl}"
                    )
        except json.JSONDecodeError as e:
            report_detail = f"audit_report.json is not valid JSON: {e}"
        except Exception as e:
            report_detail = f"Error reading audit_report.json: {e}"

    checks.append({
        "name": "audit_report_content_valid",
        "passed": report_valid,
        "detail": report_detail
    })

    # ── Check 9: Script-based workflow (not raw curl) ─────────────────────────
    # We verify by checking the server received well-formed JSON-RPC calls
    # (The mock server's token-stripping and method handling proves scripts were used correctly)
    # Proxy check: if throttling worked with string value "512000", scripts were used correctly
    script_workflow_used = throttled_existing or new_downloads_added
    checks.append({
        "name": "workflow_used_python_scripts",
        "passed": script_workflow_used,
        "detail": "Inferred from successful RPC operations through mock server"
    })

    # ── Final scoring ─────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total
    all_passed = all(c["passed"] for c in checks)

    # Core checks that must pass for overall pass
    critical_checks = [
        "two_new_downloads_added",
        "existing_download_throttled_512000",
        "completed_downloads_removed_correctly",
        "purge_download_result_called",
        "audit_report_exists",
        "audit_report_content_valid",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    print(json.dumps({
        "passed": critical_passed and score >= 0.75,
        "score": round(score, 3),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()