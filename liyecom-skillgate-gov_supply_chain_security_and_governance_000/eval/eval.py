#!/usr/bin/env python3
"""
Evaluation script for the SkillGate governance task.
Checks:
1. A scan was run and produced evidence JSON files in .skillgate/ or security-evidence/
2. The shell-executor skill was quarantined (CRITICAL risk)
3. A gov_explain output (human-readable explanation) was saved for the shell-executor finding
4. The external-downloader skill was also flagged (HIGH risk)
"""

import sys
import json
import os
import re
from pathlib import Path

def find_json_files(root: Path):
    """Find all JSON files recursively."""
    return list(root.rglob("*.json"))

def find_evidence_dir(workspace: Path):
    """
    Look for the .skillgate directory or any directory containing evidence JSON files
    produced by gov_scan.
    """
    candidates = []
    # Common output locations
    for name in [".skillgate", "security-evidence", "skillgate-output", "governance-output"]:
        d = workspace / name
        if d.exists() and d.is_dir():
            candidates.append(d)
    # Also search recursively for any directory with gov_scan-style evidence
    for d in workspace.rglob("*"):
        if d.is_dir() and d not in candidates:
            candidates.append(d)
    return candidates

def load_json_safe(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None

def check_scan_evidence(workspace: Path):
    """
    Check that gov_scan was run and produced evidence files.
    Evidence files should contain scan results with risk levels.
    """
    detail = ""
    # Look for JSON files that look like scan evidence
    all_json = find_json_files(workspace)
    
    evidence_files = []
    for jf in all_json:
        # Skip the original workspace setup files
        if jf.name in ["package.json", "skill-registry.json", "contacts.json"]:
            continue
        data = load_json_safe(jf)
        if data is None:
            continue
        # SkillGate evidence files typically contain skill, risk, findings fields
        if isinstance(data, dict):
            content_str = jf.read_text().lower()
            if any(k in content_str for k in ["risk", "finding", "scan", "critical", "high", "skillkey", "skill_key", "skillgate"]):
                evidence_files.append(jf)
    
    # Also check for non-JSON evidence (text/markdown outputs)
    explain_files = []
    for pattern in ["*.txt", "*.md", "*.log"]:
        for f in workspace.rglob(pattern):
            if f.name in ["governance-policy.md", "compliance-checklist.md", "README.internal", "audit-log.txt", "ci-pipeline.yml"]:
                continue
            content = ""
            try:
                content = f.read_text().lower()
            except Exception:
                continue
            if any(k in content for k in ["shell-executor", "critical", "risk", "finding", "skillgate", "quarantine"]):
                explain_files.append(f)
    
    return evidence_files, explain_files

def check_quarantine(workspace: Path):
    """
    Check that shell-executor was quarantined.
    Quarantine may manifest as:
    - A .quarantine marker file
    - A quarantine subdirectory
    - The skill being moved/renamed
    - A quarantine record in .skillgate/
    """
    shell_exec_dir = workspace / "enterprise-skills" / "shell-executor"
    
    markers = []
    
    # Check for quarantine marker files
    for pattern in ["*.quarantine", ".quarantined", "QUARANTINE", "quarantine.json", ".disabled"]:
        matches = list(workspace.rglob(pattern))
        markers.extend(matches)
    
    # Check if the directory was moved to a quarantine area
    quarantine_dirs = []
    for name in [".skillgate", ".quarantine", "quarantined", "quarantine"]:
        d = workspace / name
        if d.exists():
            quarantine_dirs.append(d)
    
    # Check content of .skillgate directory structure
    skillgate_dir = workspace / ".skillgate"
    quarantine_evidence = []
    if skillgate_dir.exists():
        for f in skillgate_dir.rglob("*"):
            if f.is_file():
                try:
                    content = f.read_text().lower()
                    if "quarantine" in content and "shell-executor" in content:
                        quarantine_evidence.append(f)
                    elif f.suffix == ".json":
                        data = load_json_safe(f)
                        if isinstance(data, dict):
                            data_str = json.dumps(data).lower()
                            if "quarantine" in data_str:
                                quarantine_evidence.append(f)
                except Exception:
                    pass
    
    # Check if shell-executor directory contains quarantine markers
    skill_quarantined = False
    if shell_exec_dir.exists():
        for marker in [".quarantine", ".quarantined", "QUARANTINE", ".disabled"]:
            if (shell_exec_dir / marker).exists():
                skill_quarantined = True
                break
        # Check if files were modified to indicate quarantine
        for f in shell_exec_dir.iterdir():
            if "quarantine" in f.name.lower():
                skill_quarantined = True
                break
    
    # Also check if skill directory was renamed or moved
    quarantine_path_exists = any([
        (workspace / ".skillgate" / "quarantine").exists(),
        (workspace / ".skillgate" / "quarantined").exists(),
        (workspace / "quarantine").exists(),
    ])
    
    return {
        "markers": markers,
        "quarantine_dirs": quarantine_dirs,
        "quarantine_evidence": quarantine_evidence,
        "skill_quarantined": skill_quarantined,
        "quarantine_path_exists": quarantine_path_exists
    }

def check_explain_output(workspace: Path):
    """
    Check that gov_explain was run and its output was saved.
    The output should be human-readable text explaining why shell-executor was flagged.
    """
    explain_outputs = []
    
    # Search for files containing explanation content
    for f in workspace.rglob("*"):
        if not f.is_file():
            continue
        if f.name in ["governance-policy.md", "compliance-checklist.md", "README.internal", 
                       "audit-log.txt", "ci-pipeline.yml", "SKILL.md", "executor.js",
                       "downloader.py", "install.sh"]:
            continue
        try:
            content = f.read_text(errors='replace')
            content_lower = content.lower()
            # Look for explain output: should mention the skill and provide explanation
            if ("shell-executor" in content_lower or "shell_executor" in content_lower) and \
               len(content) > 50 and \
               any(k in content_lower for k in ["explain", "reason", "why", "risk", "finding", 
                                                  "critical", "dangerous", "injection", "flagged"]):
                explain_outputs.append(f)
        except Exception:
            continue
    
    return explain_outputs

def check_skillgate_output_structure(workspace: Path):
    """
    Check that .skillgate directory was created by the scan (canonical output location).
    """
    skillgate_dir = workspace / ".skillgate"
    if not skillgate_dir.exists():
        # Try alternative locations
        for alt in ["enterprise-skills/.skillgate", "security-evidence"]:
            d = workspace / alt
            if d.exists():
                files = list(d.rglob("*"))
                if len(files) > 1:  # more than just .gitkeep
                    return True, str(d), len(files)
        return False, "", 0
    
    files = [f for f in skillgate_dir.rglob("*") if f.is_file()]
    return len(files) > 0, str(skillgate_dir), len(files)

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument_check", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    
    workspace = Path(sys.argv[1])
    checks = []
    
    # -------------------------------------------------------------------
    # CHECK 1: Scan was run and produced evidence output
    # -------------------------------------------------------------------
    try:
        has_output, output_dir, file_count = check_skillgate_output_structure(workspace)
        evidence_files, explain_files = check_scan_evidence(workspace)
        
        scan_ran = has_output or len(evidence_files) > 0 or len(explain_files) > 0
        
        detail = f"Output directory: {output_dir}, files: {file_count}, " \
                 f"evidence JSON files found: {len(evidence_files)}, " \
                 f"explain-like files: {len(explain_files)}"
        
        checks.append({
            "name": "scan_evidence_produced",
            "passed": scan_ran,
            "detail": detail
        })
    except Exception as e:
        checks.append({
            "name": "scan_evidence_produced",
            "passed": False,
            "detail": f"Exception: {e}"
        })
    
    # -------------------------------------------------------------------
    # CHECK 2: shell-executor was identified as CRITICAL/HIGH risk
    # -------------------------------------------------------------------
    try:
        critical_found = False
        critical_detail = []
        
        # Search all files for mentions of shell-executor with critical/high risk
        for f in workspace.rglob("*"):
            if not f.is_file():
                continue
            try:
                content = f.read_text(errors='replace')
                content_lower = content.lower()
                if ("shell-executor" in content_lower or "shell_executor" in content_lower):
                    if any(k in content_lower for k in ["critical", "high", "risk", "finding", "quarantine"]):
                        critical_found = True
                        critical_detail.append(str(f.relative_to(workspace)))
            except Exception:
                continue
        
        checks.append({
            "name": "shell_executor_flagged",
            "passed": critical_found,
            "detail": f"Files mentioning shell-executor with risk context: {critical_detail[:5]}"
        })
    except Exception as e:
        checks.append({
            "name": "shell_executor_flagged",
            "passed": False,
            "detail": f"Exception: {e}"
        })
    
    # -------------------------------------------------------------------
    # CHECK 3: shell-executor was quarantined
    # -------------------------------------------------------------------
    try:
        q_result = check_quarantine(workspace)
        
        quarantine_confirmed = (
            len(q_result["quarantine_evidence"]) > 0 or
            q_result["skill_quarantined"] or
            q_result["quarantine_path_exists"] or
            len(q_result["markers"]) > 0
        )
        
        # Additional check: look for quarantine state in any file
        if not quarantine_confirmed:
            for f in workspace.rglob("*"):
                if not f.is_file():
                    continue
                try:
                    content = f.read_text(errors='replace').lower()
                    if "quarantine" in content and ("shell-executor" in content or "shell_executor" in content):
                        quarantine_confirmed = True
                        break
                except Exception:
                    continue
        
        detail = (
            f"Quarantine markers: {len(q_result['markers'])}, "
            f"Skill dir quarantine flag: {q_result['skill_quarantined']}, "
            f"Quarantine evidence files: {len(q_result['quarantine_evidence'])}, "
            f"Quarantine path exists: {q_result['quarantine_path_exists']}"
        )
        
        checks.append({
            "name": "shell_executor_quarantined",
            "passed": quarantine_confirmed,
            "detail": detail
        })
    except Exception as e:
        checks.append({
            "name": "shell_executor_quarantined",
            "passed": False,
            "detail": f"Exception: {e}"
        })
    
    # -------------------------------------------------------------------
    # CHECK 4: gov_explain output was saved for shell-executor
    # -------------------------------------------------------------------
    try:
        explain_outputs = check_explain_output(workspace)
        
        # Check if there's a dedicated explain output file
        explain_saved = len(explain_outputs) > 0
        
        # Also look specifically in security-evidence/ or .skillgate/
        dedicated_explain = False
        for candidate_dir in [workspace / "security-evidence", workspace / ".skillgate"]:
            if candidate_dir.exists():
                for f in candidate_dir.rglob("*"):
                    if f.is_file() and f.suffix in [".txt", ".json", ".md", ".log"]:
                        try:
                            content = f.read_text(errors='replace').lower()
                            if len(content) > 100 and any(k in content for k in 
                                                           ["explain", "reason", "shell", "risk", "finding"]):
                                dedicated_explain = True
                                break
                        except Exception:
                            continue
        
        explain_check_passed = explain_saved or dedicated_explain
        
        detail = (
            f"Explain-like output files found: {[str(f.relative_to(workspace)) for f in explain_outputs[:5]]}, "
            f"Dedicated explain file in output dir: {dedicated_explain}"
        )
        
        checks.append({
            "name": "explain_output_saved",
            "passed": explain_check_passed,
            "detail": detail
        })
    except Exception as e:
        checks.append({
            "name": "explain_output_saved",
            "passed": False,
            "detail": f"Exception: {e}"
        })
    
    # -------------------------------------------------------------------
    # CHECK 5: external-downloader was also flagged (HIGH risk)
    # -------------------------------------------------------------------
    try:
        ext_downloader_flagged = False
        
        for f in workspace.rglob("*"):
            if not f.is_file():
                continue
            try:
                content = f.read_text(errors='replace').lower()
                if ("external-downloader" in content or "external_downloader" in content):
                    if any(k in content for k in ["high", "critical", "risk", "finding", "flagged"]):
                        ext_downloader_flagged = True
                        break
            except Exception:
                continue
        
        checks.append({
            "name": "external_downloader_flagged",
            "passed": ext_downloader_flagged,
            "detail": f"external-downloader appears in scan findings: {ext_downloader_flagged}"
        })
    except Exception as e:
        checks.append({
            "name": "external_downloader_flagged",
            "passed": False,
            "detail": f"Exception: {e}"
        })
    
    # -------------------------------------------------------------------
    # Scoring
    # -------------------------------------------------------------------
    # Weight the checks
    weights = {
        "scan_evidence_produced": 0.25,
        "shell_executor_flagged": 0.20,
        "shell_executor_quarantined": 0.30,
        "explain_output_saved": 0.15,
        "external_downloader_flagged": 0.10,
    }
    
    score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.0)
        if check["passed"]:
            score += w
    
    passed = score >= 0.70  # Must pass at least scan + quarantine + flagging
    
    print(json.dumps({
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()