#!/usr/bin/env python3
"""
Evaluation script for aria2-json-rpc skill task.
Checks that the agent:
1. Connected to the correct mock server (port 7600)
2. Added exactly 3 downloads using aria2.addUri (each with proper array format)
3. Applied a 512 KB/s (524288 bytes) throttle to episode01_4k.mp4 via aria2.changeOption
4. Queried stopped downloads (tellStopped) with pagination args
5. Ran purgeDownloadResult to clean up completed downloads
6. Produced a valid audit_report.json with required fields
"""
import sys
import json
import urllib.request
from pathlib import Path

def main(workspace):
    workspace = Path(workspace)
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # ── Helper: query mock server state ──────────────────────────────────────
    def rpc(method, params=None):
        req = {"jsonrpc": "2.0", "id": "eval", "method": method, "params": params or []}
        data = json.dumps(req).encode()
        r = urllib.request.urlopen(
            urllib.request.Request(
                "http://localhost:7600",
                data=data,
                headers={"Content-Type": "application/json"}
            ),
            timeout=5
        )
        return json.loads(r.read())

    # ── Check 1: Mock server is reachable ────────────────────────────────────
    try:
        resp = rpc("aria2.getVersion")
        server_alive = "result" in resp
        add_check("mock_server_reachable", server_alive,
                  f"Server response: {resp.get('result', resp.get('error'))}")
    except Exception as e:
        add_check("mock_server_reachable", False, f"Server not reachable: {e}")
        # Can't continue without server
        total = len(checks)
        passed = sum(1 for c in checks if c["passed"])
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── Check 2: Exactly 3 downloads were added ──────────────────────────────
    try:
        resp = rpc("aria2.tellStopped", [0, 100])
        stopped = resp.get("result", [])
        
        resp2 = rpc("aria2.tellActive", [])
        active = resp2.get("result", [])
        
        # Also check purged - need to inspect server state differently
        # We'll check total unique GIDs by looking at what was ever added
        # by querying the global stat history
        all_downloads = stopped + active
        
        # Count downloads that match our expected URLs
        expected_filenames = {
            "episode01_4k.mp4",
            "episode02_4k.mp4", 
            "episode03_4k.mp4"
        }
        
        found_filenames = set()
        gid_of_ep01 = None
        all_gids = []
        
        for dl in all_downloads:
            files = dl.get("files", [])
            filename = ""
            if files:
                import os
                filename = os.path.basename(files[0].get("path", ""))
            if filename in expected_filenames:
                found_filenames.add(filename)
                if filename == "episode01_4k.mp4":
                    gid_of_ep01 = dl.get("gid")
            all_gids.append(dl.get("gid"))

        # The downloads might be purged - check via a different approach
        # Try to get stopped with offset 0 before purge count via global stat
        resp_stat = rpc("aria2.getGlobalStat", [])
        stat = resp_stat.get("result", {})
        
        # After purge, numStopped should be 0 (or fewer)
        num_stopped_after = int(stat.get("numStopped", "0"))
        
        # Check if at least 3 downloads were created by examining if report exists
        # and has 3 GIDs
        three_downloads_added = len(found_filenames) >= 3 or num_stopped_after == 0
        
        # Try querying the server's internal state for all downloads ever added
        # by temporarily using tellStopped with large range including purged
        # (purged items won't show up in tellStopped after purge)
        add_check("three_downloads_added", 
                  len(found_filenames) == 3 or (len(found_filenames) < 3 and num_stopped_after == 0),
                  f"Found filenames in server: {found_filenames}, numStopped={num_stopped_after}")
    except Exception as e:
        add_check("three_downloads_added", False, f"Error checking downloads: {e}")
        gid_of_ep01 = None
        all_gids = []

    # ── Check 3: audit_report.json exists and is valid JSON ──────────────────
    report_files = list(workspace.rglob("audit_report.json"))
    if not report_files:
        add_check("audit_report_exists", False, "audit_report.json not found anywhere in workspace")
        add_check("audit_report_has_gids", False, "Cannot check - file missing")
        add_check("audit_report_has_throttle_info", False, "Cannot check - file missing")
        add_check("purge_confirmed_in_report", False, "Cannot check - file missing")
    else:
        report_path = report_files[0]
        try:
            with open(report_path) as f:
                report = json.load(f)
            add_check("audit_report_exists", True, f"Found at {report_path}")
        except Exception as e:
            report = {}
            add_check("audit_report_exists", False, f"File found but invalid JSON: {e}")

        # ── Check 4: Report contains GIDs (at least 3) ──────────────────────
        try:
            # Look for GIDs in the report - they can be in any structure
            report_str = json.dumps(report)
            
            # GIDs are 16-char hex strings
            import re
            found_gids_in_report = re.findall(r'[0-9a-f]{16}', report_str)
            found_gids_in_report = list(set(found_gids_in_report))
            
            has_gids = len(found_gids_in_report) >= 3
            add_check("audit_report_has_gids", has_gids,
                      f"GIDs found in report: {found_gids_in_report}")
        except Exception as e:
            add_check("audit_report_has_gids", False, f"Error checking GIDs: {e}")

        # ── Check 5: Report mentions throttle / speed limit ──────────────────
        try:
            report_str_lower = json.dumps(report).lower()
            # Check for 524288 (512*1024) or "512" near "kb" or "max-download-limit"
            has_throttle = (
                "524288" in report_str_lower or
                "max-download-limit" in report_str_lower or
                ("512" in report_str_lower and ("kb" in report_str_lower or "limit" in report_str_lower)) or
                "throttl" in report_str_lower
            )
            add_check("audit_report_has_throttle_info", has_throttle,
                      f"Report throttle info present: {has_throttle}. Keys found: {list(report.keys()) if isinstance(report, dict) else 'non-dict'}")
        except Exception as e:
            add_check("audit_report_has_throttle_info", False, f"Error: {e}")

        # ── Check 6: Report confirms purge was performed ─────────────────────
        try:
            report_str_lower = json.dumps(report).lower()
            has_purge = (
                "purge" in report_str_lower or
                "purgedownloadresult" in report_str_lower or
                "cleaned" in report_str_lower or
                "removed" in report_str_lower
            )
            add_check("purge_confirmed_in_report", has_purge,
                      f"Purge keyword in report: {has_purge}")
        except Exception as e:
            add_check("purge_confirmed_in_report", False, f"Error: {e}")

    # ── Check 7: changeOption was actually called with 524288 bytes ──────────
    try:
        # Query server: check if any download has max-download-limit=524288
        resp_stopped = rpc("aria2.tellStopped", [0, 100])
        stopped_dls = resp_stopped.get("result", [])
        resp_active = rpc("aria2.tellActive", [])
        active_dls = resp_active.get("result", [])
        all_dls = stopped_dls + active_dls
        
        throttle_applied = False
        throttle_target_gid = None
        
        for dl in all_dls:
            import os
            files = dl.get("files", [])
            filename = os.path.basename(files[0].get("path", "")) if files else ""
            if "episode01" in filename:
                throttle_target_gid = dl.get("gid")
                opts_resp = rpc("aria2.getOption", [throttle_target_gid])
                opts = opts_resp.get("result", {})
                limit = opts.get("max-download-limit", "")
                if str(limit) == "524288":
                    throttle_applied = True
                    break
        
        # If not found in current lists (might be purged), check via the report
        if not throttle_applied and report_files:
            try:
                with open(report_files[0]) as f:
                    report_data = json.load(f)
                report_str = json.dumps(report_data)
                if "524288" in report_str:
                    throttle_applied = True
            except:
                pass
        
        add_check("throttle_524288_applied_to_ep01", throttle_applied,
                  f"throttle_target_gid={throttle_target_gid}, throttle_applied={throttle_applied}")
    except Exception as e:
        add_check("throttle_524288_applied_to_ep01", False, f"Error: {e}")

    # ── Check 8: purgeDownloadResult was called (numStopped drops to 0) ──────
    try:
        resp_stat = rpc("aria2.getGlobalStat", [])
        stat = resp_stat.get("result", {})
        num_stopped = int(stat.get("numStopped", "999"))
        purge_called = num_stopped == 0
        add_check("purge_download_result_called", purge_called,
                  f"numStopped after operations: {num_stopped} (should be 0 after purge)")
    except Exception as e:
        add_check("purge_download_result_called", False, f"Error: {e}")

    # ── Check 9: Correct script workflow (config test first) ─────────────────
    # We verify the agent used python3 scripts/config_loader.py test by checking
    # that the server received requests on port 7600 (if it had wrong port it would fail)
    try:
        resp = rpc("aria2.getVersion", [])
        version_ok = resp.get("result", {}).get("version") == "1.36.0"
        add_check("correct_port_used", version_ok,
                  f"Server on port 7600 responded correctly: {version_ok}")
    except Exception as e:
        add_check("correct_port_used", False, f"Could not verify port: {e}")

    # ── Check 10: Three distinct URLs were submitted (correct addUri format) ──
    try:
        if report_files:
            with open(report_files[0]) as f:
                report_data = json.load(f)
            import re
            report_str = json.dumps(report_data)
            # Check for all 3 episode filenames or GIDs
            ep01 = "episode01" in report_str
            ep02 = "episode02" in report_str
            ep03 = "episode03" in report_str
            all_episodes = ep01 and ep02 and ep03
            add_check("all_three_episodes_in_report", all_episodes,
                      f"ep01={ep01}, ep02={ep02}, ep03={ep03}")
        else:
            add_check("all_three_episodes_in_report", False, "No report to check")
    except Exception as e:
        add_check("all_three_episodes_in_report", False, f"Error: {e}")

    # ── Final scoring ─────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total if total > 0 else 0.0
    overall = score >= 0.7

    result = {
        "passed": overall,
        "score": round(score, 3),
        "checks": checks,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace_dir)