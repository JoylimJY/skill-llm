#!/usr/bin/env python3
"""
Evaluation script for the token-saver v3 task.

Checks:
1. openclaw.json exists at ~/.openclaw/openclaw.json with correct Gemini 2.5 Pro model
2. Compaction state is set to conservative preset (800K threshold for 1M context)
3. Workspace compression was run (backups exist for appropriate files)
4. PROJECTS.md was NOT modified (no compression applied)
5. optimization_report.json exists and contains correct model detection and savings data
6. Model detection source in report is "openclaw.json" (config file, not env/fallback)
"""

import sys
import json
import re
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    home = Path.home()
    
    checks = []
    
    # ── Check 1: openclaw.json exists and references Gemini 2.5 Pro ──────────
    config_path = home / ".openclaw" / "openclaw.json"
    check1_passed = False
    check1_detail = ""
    
    try:
        if not config_path.exists():
            check1_detail = f"~/.openclaw/openclaw.json does not exist. Agent must create this file to configure the model."
        else:
            config_data = json.loads(config_path.read_text())
            model_value = config_data.get("model", "")
            # Accept any valid identifier for Gemini 2.5 Pro
            # Valid: "gemini-2-5-pro", "gemini2.5-pro", "gemini-2.5pro", "gemini2.5pro", "gemini-2.5-pro"
            gemini_25_identifiers = [
                "gemini-2-5-pro",
                "gemini2.5-pro", 
                "gemini-2.5pro",
                "gemini2.5pro",
                "gemini-2.5-pro",
            ]
            if model_value in gemini_25_identifiers:
                check1_passed = True
                check1_detail = f"openclaw.json found with model='{model_value}' (Gemini 2.5 Pro). ✓"
            else:
                check1_detail = f"openclaw.json exists but model='{model_value}' is not a recognized Gemini 2.5 Pro identifier. Expected one of: {gemini_25_identifiers}"
    except json.JSONDecodeError as e:
        check1_detail = f"openclaw.json exists but is invalid JSON: {e}"
    except Exception as e:
        check1_detail = f"Unexpected error reading openclaw.json: {e}"
    
    checks.append({
        "name": "openclaw.json configured with Gemini 2.5 Pro",
        "passed": check1_passed,
        "detail": check1_detail
    })
    
    # ── Check 2: Compaction set to conservative preset (800K for 1M context) ──
    compaction_path = workspace / ".openclaw" / "compaction.json"
    check2_passed = False
    check2_detail = ""
    
    try:
        if not compaction_path.exists():
            check2_detail = "Compaction state file not found at workspace/.openclaw/compaction.json. Agent must run compaction conservative command."
        else:
            compaction_data = json.loads(compaction_path.read_text())
            threshold = compaction_data.get("threshold")
            preset = compaction_data.get("preset", "").lower()
            context_window = compaction_data.get("context_window")
            
            # Gemini 2.5 Pro: 1M context, conservative = 80% = 800,000
            expected_threshold = 800000
            expected_preset = "conservative"
            
            if preset != expected_preset:
                check2_detail = f"Compaction preset is '{preset}', expected 'conservative'."
            elif threshold != expected_threshold:
                check2_detail = (
                    f"Compaction threshold is {threshold}, expected {expected_threshold} "
                    f"(80% of Gemini 2.5 Pro's 1,000,000 context window). "
                    f"This is the key dynamic preset: conservative=80%×1M=800K."
                )
            elif context_window != 1000000:
                check2_detail = (
                    f"Context window stored as {context_window}, expected 1000000 for Gemini 2.5 Pro."
                )
            else:
                check2_passed = True
                check2_detail = f"Conservative compaction preset correctly set to {threshold} tokens (80% of 1M context). ✓"
    except json.JSONDecodeError as e:
        check2_detail = f"compaction.json is invalid JSON: {e}"
    except Exception as e:
        check2_detail = f"Unexpected error reading compaction state: {e}"
    
    checks.append({
        "name": "Conservative compaction preset = 800K (80% of Gemini 2.5 Pro 1M context)",
        "passed": check2_passed,
        "detail": check2_detail
    })
    
    # ── Check 3: Workspace files were compressed (backups exist) ──────────────
    check3_passed = False
    check3_detail = ""
    
    try:
        # Files that SHOULD have been compressed and backed up
        expected_backups = ["SOUL.md.backup", "AGENTS.md.backup", "USER.md.backup", "MEMORY.md.backup"]
        found_backups = []
        missing_backups = []
        
        for backup_name in expected_backups:
            backup_path = workspace / backup_name
            if backup_path.exists():
                found_backups.append(backup_name)
            else:
                missing_backups.append(backup_name)
        
        if len(found_backups) >= 2:
            # At least 2 files compressed (some may be smart-bypassed if already optimized)
            check3_passed = True
            check3_detail = f"Backup files found: {found_backups}. Compression was applied. ✓"
            if missing_backups:
                check3_detail += f" (Not backed up / smart-bypassed: {missing_backups})"
        else:
            check3_detail = f"Too few backup files found: {found_backups}. Missing: {missing_backups}. Compression may not have been run."
    except Exception as e:
        check3_detail = f"Error checking backup files: {e}"
    
    checks.append({
        "name": "Workspace compression run (backup files created for SOUL/AGENTS/USER/MEMORY)",
        "passed": check3_passed,
        "detail": check3_detail
    })
    
    # ── Check 4: PROJECTS.md was NOT modified (no compression = no backup) ────
    check4_passed = False
    check4_detail = ""
    
    try:
        projects_backup = workspace / "PROJECTS.md.backup"
        projects_md = workspace / "PROJECTS.md"
        
        if projects_backup.exists():
            check4_detail = (
                "PROJECTS.md.backup exists, meaning compression was applied to PROJECTS.md. "
                "Per SKILL.md, PROJECTS.md must NOT be compressed (user structure preserved). "
                "This is the 'no compression' rule the agent must follow."
            )
        elif not projects_md.exists():
            check4_detail = "PROJECTS.md does not exist in workspace."
        else:
            check4_passed = True
            check4_detail = "PROJECTS.md correctly left unmodified (no backup created, no compression applied). ✓"
    except Exception as e:
        check4_detail = f"Error checking PROJECTS.md: {e}"
    
    checks.append({
        "name": "PROJECTS.md not compressed (file-aware rule: no compression for PROJECTS.md)",
        "passed": check4_passed,
        "detail": check4_detail
    })
    
    # ── Check 5: optimization_report.json exists and is valid ─────────────────
    check5_passed = False
    check5_detail = ""
    report_data = None
    
    try:
        # Search for optimization_report.json anywhere in workspace
        report_files = list(workspace.rglob("optimization_report.json"))
        
        if not report_files:
            check5_detail = "optimization_report.json not found anywhere in workspace."
        else:
            report_path = report_files[0]
            report_data = json.loads(report_path.read_text())
            
            # Must have file entries showing compression results
            files_section = report_data.get("files", [])
            
            if not files_section:
                check5_detail = f"optimization_report.json found at {report_path} but has no 'files' section."
            else:
                compressed_files = [f for f in files_section if f.get("status") == "compressed"]
                skipped_projects = [f for f in files_section 
                                    if f.get("file") == "PROJECTS.md" 
                                    and f.get("status") in ("skipped_no_compression", "not_found")]
                
                if len(compressed_files) == 0:
                    check5_detail = f"Report found but no files show status='compressed'. Files: {[f.get('file') for f in files_section]}"
                else:
                    check5_passed = True
                    check5_detail = (
                        f"optimization_report.json found at {report_path}. "
                        f"Compressed files: {[f['file'] for f in compressed_files]}. "
                        f"Total savings: {report_data.get('total_savings', 'N/A')} tokens. ✓"
                    )
    except json.JSONDecodeError as e:
        check5_detail = f"optimization_report.json is invalid JSON: {e}"
    except Exception as e:
        check5_detail = f"Error reading optimization_report.json: {e}"
    
    checks.append({
        "name": "optimization_report.json exists with valid compression results",
        "passed": check5_passed,
        "detail": check5_detail
    })
    
    # ── Check 6: Report shows model detected via openclaw.json (not fallback) ──
    check6_passed = False
    check6_detail = ""
    
    try:
        if report_data is None:
            check6_detail = "Cannot check model detection: optimization_report.json not found or invalid."
        else:
            detection_source = report_data.get("detection_source", "")
            model_detected = report_data.get("model_detected", "")
            context_window = report_data.get("context_window", 0)
            
            # Detection source must be "openclaw.json" (config file)
            if "openclaw.json" not in detection_source:
                check6_detail = (
                    f"Report shows detection_source='{detection_source}', expected 'openclaw.json'. "
                    f"Model detection priority: config file takes precedence over env/fallback. "
                    f"The agent must create ~/.openclaw/openclaw.json for config-based detection."
                )
            elif context_window != 1000000:
                check6_detail = (
                    f"Report shows context_window={context_window} for model '{model_detected}', "
                    f"expected 1000000 for Gemini 2.5 Pro."
                )
            elif "Gemini 2.5 Pro" not in model_detected and "gemini" not in model_detected.lower():
                check6_detail = (
                    f"Report shows model_detected='{model_detected}', expected Gemini 2.5 Pro."
                )
            else:
                check6_passed = True
                check6_detail = (
                    f"Report correctly shows model '{model_detected}' detected via '{detection_source}' "
                    f"with {context_window} context window. ✓"
                )
    except Exception as e:
        check6_detail = f"Error validating model detection in report: {e}"
    
    checks.append({
        "name": "Report confirms model detected via openclaw.json (not env/fallback)",
        "passed": check6_passed,
        "detail": check6_detail
    })
    
    # ── Compute final score ────────────────────────────────────────────────────
    # Weighted scoring:
    # Check 1 (config): 20%  - foundational
    # Check 2 (compaction): 25% - proprietary dynamic preset trap
    # Check 3 (compression ran): 20%
    # Check 4 (PROJECTS.md untouched): 15% - file-aware compression trap
    # Check 5 (report valid): 10%
    # Check 6 (detection source): 10%
    
    weights = [0.20, 0.25, 0.20, 0.15, 0.10, 0.10]
    score = sum(w for w, c in zip(weights, checks) if c["passed"])
    score = round(score, 4)
    
    all_passed = all(c["passed"] for c in checks)
    
    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    
    return result


def main():
    if len(sys.argv) != 2:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_invocation", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}]
        }))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    
    try:
        result = run_checks(workspace_dir)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": f"Evaluation crashed: {e}"}]
        }
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()