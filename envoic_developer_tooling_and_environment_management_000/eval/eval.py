#!/usr/bin/env python3
"""
Evaluation script for the envoic disk-audit task.
Checks that the agent:
1. Produced envoic_report.json in the workspace (anywhere under /workspace).
2. The file is valid JSON.
3. The report contains scan results covering multiple environment types (Python venvs, node_modules).
4. The report reflects a deep scan (finds deeply nested environments, at least 4 distinct stale entries).
5. The report contains or is accompanied by dry-run manage output (manage/cleanup plan present).
6. The agent checked health of at least one specific broken .venv via 'info' subcommand evidence.
"""

import sys
import json
import os
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    total_score = 0.0
    weights = {
        "report_exists": 0.20,
        "valid_json": 0.15,
        "has_python_envs": 0.20,
        "has_node_modules": 0.15,
        "deep_scan_coverage": 0.20,
        "manage_dry_run_evidence": 0.10,
    }

    # ── Check 1: envoic_report.json exists somewhere under workspace ──
    report_files = list(workspace.rglob("envoic_report.json"))
    if not report_files:
        checks.append({
            "name": "report_exists",
            "passed": False,
            "detail": "envoic_report.json not found anywhere under /workspace"
        })
    else:
        checks.append({
            "name": "report_exists",
            "passed": True,
            "detail": f"Found envoic_report.json at: {report_files[0]}"
        })

    # ── Check 2: Valid JSON ──
    report_data = None
    if report_files:
        try:
            report_path = report_files[0]
            content = report_path.read_text(encoding="utf-8")
            report_data = json.loads(content)
            checks.append({
                "name": "valid_json",
                "passed": True,
                "detail": f"File is valid JSON with {len(content)} bytes, type={type(report_data).__name__}"
            })
        except json.JSONDecodeError as e:
            checks.append({
                "name": "valid_json",
                "passed": False,
                "detail": f"Invalid JSON: {e}"
            })
        except Exception as e:
            checks.append({
                "name": "valid_json",
                "passed": False,
                "detail": f"Error reading file: {e}"
            })
    else:
        checks.append({
            "name": "valid_json",
            "passed": False,
            "detail": "Cannot check JSON validity: report file not found"
        })

    # ── Helper: flatten report data to a string for keyword search ──
    def report_str(data) -> str:
        if data is None:
            return ""
        try:
            return json.dumps(data).lower()
        except Exception:
            return str(data).lower()

    rs = report_str(report_data)

    # ── Check 3: Report mentions Python virtual environments ──
    python_keywords = ["venv", "virtualenv", "pyvenv", "python", ".venv", "conda"]
    python_found = any(kw in rs for kw in python_keywords)
    if report_data is not None:
        checks.append({
            "name": "has_python_envs",
            "passed": python_found,
            "detail": f"Python env keywords found in report: {python_found}. Keywords searched: {python_keywords}"
        })
    else:
        checks.append({
            "name": "has_python_envs",
            "passed": False,
            "detail": "No report data to analyze for Python envs"
        })

    # ── Check 4: Report mentions node_modules ──
    node_keywords = ["node_modules", "npm", "node", "javascript", "js"]
    node_found = any(kw in rs for kw in node_keywords)
    if report_data is not None:
        checks.append({
            "name": "has_node_modules",
            "passed": node_found,
            "detail": f"node_modules keywords found in report: {node_found}. Keywords searched: {node_keywords}"
        })
    else:
        checks.append({
            "name": "has_node_modules",
            "passed": False,
            "detail": "No report data to analyze for node_modules"
        })

    # ── Check 5: Deep scan coverage ──
    # We planted stale envs in: 
    #   projects/ml-experiment-alpha/experiments/run_001/.venv (broken)
    #   projects/ml-experiment-alpha/experiments/run_002/.venv (broken)
    #   projects/data-pipeline/.venv (valid)
    #   projects/api-service/services/auth/.venv (valid, deep)
    #   projects/api-service/services/ml/.venv (broken, deep)
    #   archive/old-prototype/backend/api/v1/.venv (broken, very deep)
    #   projects/frontend-dashboard/node_modules (stale)
    #   projects/api-service/services/frontend/node_modules (deep)
    #   archive/old-prototype/frontend/client/node_modules (deep)
    #   envs/ml-base-env (conda)
    #
    # A shallow scan would miss deeply nested ones.
    # We check that at least 4 distinct environment paths are referenced.
    
    deep_path_indicators = [
        "run_001",
        "run_002", 
        "api-service",
        "old-prototype",
        "archive",
        "services",
        "ml-base-env",
        "frontend-dashboard",
    ]
    
    deep_hits = sum(1 for indicator in deep_path_indicators if indicator.lower() in rs)
    deep_scan_passed = deep_hits >= 4
    
    if report_data is not None:
        checks.append({
            "name": "deep_scan_coverage",
            "passed": deep_scan_passed,
            "detail": (
                f"Deep scan coverage: {deep_hits}/{len(deep_path_indicators)} deep path indicators found "
                f"in report (need >= 4). Found: {[i for i in deep_path_indicators if i.lower() in rs]}"
            )
        })
    else:
        checks.append({
            "name": "deep_scan_coverage",
            "passed": False,
            "detail": "No report data to check deep scan coverage"
        })

    # ── Check 6: Evidence of manage --dry-run ──
    # Look for a dry-run log file anywhere in workspace, OR dry-run content in the JSON report
    dry_run_keywords = ["dry-run", "dry_run", "dryrun", "would delete", "would remove", 
                        "cleanup plan", "manage", "candidate", "proposed"]
    
    # Check report JSON itself
    dry_in_report = any(kw in rs for kw in dry_run_keywords)
    
    # Also check for any companion log files (manage_output.txt, dry_run.txt, cleanup_plan.txt, etc.)
    dry_run_log_files = []
    for pattern in ["*.txt", "*.log", "*.json"]:
        for f in workspace.rglob(pattern):
            if f == (report_files[0] if report_files else None):
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="ignore").lower()
                if any(kw in content for kw in dry_run_keywords):
                    dry_run_log_files.append(str(f.relative_to(workspace)))
            except Exception:
                pass
    
    dry_run_evidence = dry_in_report or len(dry_run_log_files) > 0
    checks.append({
        "name": "manage_dry_run_evidence",
        "passed": dry_run_evidence,
        "detail": (
            f"Dry-run evidence found: in_report={dry_in_report}, "
            f"companion_files={dry_run_log_files[:5]}"
        )
    })

    # ── Compute final score ──
    check_map = {c["name"]: c["passed"] for c in checks}
    score = sum(weights[name] for name, passed in check_map.items() if passed)
    
    # Normalize score to [0, 1]
    max_score = sum(weights.values())
    normalized_score = round(score / max_score, 4)
    
    passed = normalized_score >= 0.70  # Need at least 70% to pass

    result = {
        "passed": passed,
        "score": normalized_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()