#!/usr/bin/env python3
"""
Evaluation script for the claw-guard overnight monitoring task.
Usage: python3 eval_script.py /workspace
"""

import sys
import json
import subprocess
import re
from pathlib import Path

def run_cmd(cmd):
    """Run a shell command and return (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30,
            env={"PATH": "/home/quant/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                 "HOME": "/home/quant"}
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -1

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    
    # ── Get claw-guard status output ─────────────────────────────────────────
    status_stdout, status_stderr, status_rc = run_cmd("claw-guard status")
    status_text = status_stdout + status_stderr

    # ── CHECK 1: gguf-model-export is registered with correct flags ──────────
    check_name = "gguf_export_registered"
    try:
        # Must appear in status with correct ID
        has_gguf = "gguf-model-export" in status_text
        
        # Also verify via direct registry check — look for the watch-dir flag effect
        # The ID must be present and associated with the gguf exports directory
        passed_1 = has_gguf
        detail = f"gguf-model-export found in status: {has_gguf}. Status excerpt: {status_text[:500]}"
    except Exception as e:
        passed_1 = False
        detail = f"Exception: {e}"
    checks.append({"name": check_name, "passed": passed_1, "detail": detail})

    # ── CHECK 2: parquet-factor-dump is registered with correct flags ─────────
    check_name = "parquet_dump_registered"
    try:
        has_parquet = "parquet-factor-dump" in status_text
        passed_2 = has_parquet
        detail = f"parquet-factor-dump found in status: {has_parquet}"
    except Exception as e:
        passed_2 = False
        detail = f"Exception: {e}"
    checks.append({"name": check_name, "passed": passed_2, "detail": detail})

    # ── CHECK 3: risk-matrix-gen was registered AND then removed ─────────────
    check_name = "risk_matrix_removed"
    try:
        # risk-matrix-gen must NOT appear in status (it was cancelled)
        has_risk = "risk-matrix-gen" in status_text
        passed_3 = not has_risk
        detail = f"risk-matrix-gen in status (should be False): {has_risk}"
    except Exception as e:
        passed_3 = False
        detail = f"Exception: {e}"
    checks.append({"name": check_name, "passed": passed_3, "detail": detail})

    # ── CHECK 4: Gateway restart is registered ────────────────────────────────
    check_name = "gateway_restart_registered"
    try:
        # claw-guard status should show a restart watch entry
        restart_keywords = ["restart", "gateway", "register-restart", "Restart"]
        has_restart = any(kw.lower() in status_text.lower() for kw in restart_keywords)
        # More specifically, look for the restart watch being active
        # The status typically shows "Gateway restart: watching" or similar
        restart_active = (
            "restart" in status_text.lower() and
            ("watch" in status_text.lower() or "registered" in status_text.lower() or "active" in status_text.lower())
        )
        passed_4 = has_restart  # At minimum the restart section must show something
        detail = f"Restart-related content in status: {has_restart}, restart_active pattern: {restart_active}"
    except Exception as e:
        passed_4 = False
        detail = f"Exception: {e}"
    checks.append({"name": check_name, "passed": passed_4, "detail": detail})

    # ── CHECK 5: Correct notification target used ─────────────────────────────
    check_name = "correct_notification_target"
    try:
        # The target must be telegram:-1001827364518 (from runbook), NOT -1001234567890 (from config)
        correct_target = "telegram:-1001827364518"
        wrong_target = "telegram:-1001234567890"
        has_correct = correct_target in status_text
        has_wrong = wrong_target in status_text
        # Both correct registrations AND wrong (default config) could appear — 
        # we require correct target to be present
        passed_5 = has_correct
        detail = f"Correct target '{correct_target}' in status: {has_correct}. Wrong target present: {has_wrong}"
    except Exception as e:
        passed_5 = False
        detail = f"Exception: {e}"
    checks.append({"name": check_name, "passed": passed_5, "detail": detail})

    # ── CHECK 6: monitoring_report.json exists and has correct structure ───────
    check_name = "monitoring_report_exists_and_valid"
    try:
        report_path = workspace / "ops/monitoring/monitoring_report.json"
        if not report_path.exists():
            # Also search the workspace
            candidates = list(workspace.rglob("monitoring_report.json"))
            if candidates:
                report_path = candidates[0]
        
        if not report_path.exists():
            passed_6 = False
            detail = "monitoring_report.json not found anywhere in workspace"
        else:
            content = json.loads(report_path.read_text())
            
            required_keys = ["active_registrations", "gateway_restart_registered", "notification_target", "removed_jobs"]
            missing_keys = [k for k in required_keys if k not in content]
            
            if missing_keys:
                passed_6 = False
                detail = f"Missing keys in monitoring_report.json: {missing_keys}. Found: {list(content.keys())}"
            else:
                # Check types
                active_regs = content["active_registrations"]
                gw_registered = content["gateway_restart_registered"]
                notif_target = content["notification_target"]
                removed = content["removed_jobs"]
                
                type_ok = (
                    isinstance(active_regs, list) and
                    isinstance(gw_registered, bool) and
                    isinstance(notif_target, str) and
                    isinstance(removed, list)
                )
                passed_6 = type_ok
                detail = f"Keys present, types ok: {type_ok}. active_registrations={active_regs}, gateway_restart_registered={gw_registered}, notification_target={notif_target}, removed_jobs={removed}"
    except json.JSONDecodeError as e:
        passed_6 = False
        detail = f"JSON parse error: {e}"
    except Exception as e:
        passed_6 = False
        detail = f"Exception: {e}"
    checks.append({"name": check_name, "passed": passed_6, "detail": detail})

    # ── CHECK 7: report content correctness ───────────────────────────────────
    check_name = "monitoring_report_content_correct"
    try:
        report_path = workspace / "ops/monitoring/monitoring_report.json"
        if not report_path.exists():
            candidates = list(workspace.rglob("monitoring_report.json"))
            report_path = candidates[0] if candidates else None
        
        if report_path is None or not report_path.exists():
            passed_7 = False
            detail = "monitoring_report.json not found"
        else:
            content = json.loads(report_path.read_text())
            active = content.get("active_registrations", [])
            removed = content.get("removed_jobs", [])
            target = content.get("notification_target", "")
            gw = content.get("gateway_restart_registered", False)
            
            # Active must contain gguf-model-export and parquet-factor-dump
            active_str = " ".join(str(x) for x in active)
            has_gguf_in_report = "gguf-model-export" in active_str or "gguf_model_export" in active_str or "gguf" in active_str.lower()
            has_parquet_in_report = "parquet-factor-dump" in active_str or "parquet_factor_dump" in active_str or "parquet" in active_str.lower()
            
            # risk-matrix-gen must be in removed
            removed_str = " ".join(str(x) for x in removed)
            has_risk_removed = "risk-matrix-gen" in removed_str or "risk_matrix" in removed_str or "risk" in removed_str.lower()
            
            # target must reference the correct telegram group
            target_correct = "1001827364518" in target
            
            # gateway restart must be true
            gw_correct = gw is True
            
            all_correct = has_gguf_in_report and has_parquet_in_report and has_risk_removed and target_correct and gw_correct
            passed_7 = all_correct
            detail = (
                f"gguf in active: {has_gguf_in_report}, parquet in active: {has_parquet_in_report}, "
                f"risk removed: {has_risk_removed}, target correct: {target_correct} ('{target}'), "
                f"gateway_restart_registered: {gw_correct} (value={gw})"
            )
    except Exception as e:
        passed_7 = False
        detail = f"Exception: {e}"
    checks.append({"name": check_name, "passed": passed_7, "detail": detail})

    # ── CHECK 8: gguf registration used --watch-dir (not --log) ───────────────
    check_name = "gguf_uses_watch_dir_not_log"
    try:
        # Look for evidence that watch-dir was used for gguf — this shows in status
        # The runbook specifies "Watch dir" for gguf and "Log file" for parquet/risk
        # Status output typically distinguishes between log-watch and dir-watch
        gguf_watch_dir = (
            "gguf_exports" in status_text or
            "watch-dir" in status_text.lower() or
            "watch_dir" in status_text.lower() or
            "dir" in status_text.lower()
        )
        # This is a soft check — if status doesn't explicitly show it, we pass on benefit of the doubt
        # but penalize score
        passed_8 = gguf_watch_dir
        detail = f"Evidence of watch-dir usage for gguf in status: {gguf_watch_dir}. Status (first 800 chars): {status_text[:800]}"
    except Exception as e:
        passed_8 = False
        detail = f"Exception: {e}"
    checks.append({"name": check_name, "passed": passed_8, "detail": detail})

    # ── CHECK 9: parquet timeout is 120s (not default 180s) ───────────────────
    check_name = "parquet_custom_timeout"
    try:
        # Runbook specifies 120s for parquet, 360s for gguf, 90s for risk
        # Status output should show timeout values if claw-guard displays them
        has_120 = "120" in status_text
        has_360 = "360" in status_text
        # These are strong positive signals
        passed_9 = has_120 and has_360
        detail = f"Timeout 120s in status: {has_120}, timeout 360s in status: {has_360}"
    except Exception as e:
        passed_9 = False
        detail = f"Exception: {e}"
    checks.append({"name": check_name, "passed": passed_9, "detail": detail})

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weight the checks by importance
    weights = {
        "gguf_export_registered": 2.0,
        "parquet_dump_registered": 2.0,
        "risk_matrix_removed": 1.5,
        "gateway_restart_registered": 1.5,
        "correct_notification_target": 2.0,
        "monitoring_report_exists_and_valid": 1.0,
        "monitoring_report_content_correct": 2.0,
        "gguf_uses_watch_dir_not_log": 1.0,
        "parquet_custom_timeout": 1.0,
    }
    total_weight = sum(weights.values())
    earned_weight = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned_weight / total_weight, 4)
    
    # Overall pass requires core checks
    core_checks = ["gguf_export_registered", "parquet_dump_registered", "risk_matrix_removed",
                   "gateway_restart_registered", "correct_notification_target",
                   "monitoring_report_content_correct"]
    passed_overall = all(c["passed"] for c in checks if c["name"] in core_checks)

    result = {
        "passed": passed_overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return 0 if passed_overall else 1

if __name__ == "__main__":
    sys.exit(main())