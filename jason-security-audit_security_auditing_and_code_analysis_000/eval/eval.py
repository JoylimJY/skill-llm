#!/usr/bin/env python3
"""
Evaluation script for the security-audit task.
Checks that the agent produced a correct security_report.txt
with BLOCKED status and all required critical findings.
"""

import sys
import json
from pathlib import Path

def evaluate(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    checks    = []
    
    # ── 1. Locate the output report ──────────────────────────────────────────
    report_files = list(workspace.rglob("security_report.txt"))
    
    report_found = len(report_files) > 0
    checks.append({
        "name":   "security_report.txt exists",
        "passed": report_found,
        "detail": (f"Found at {report_files[0]}" if report_found
                   else "security_report.txt not found anywhere in workspace"),
    })
    
    if not report_found:
        return {
            "passed": False,
            "score":  0.0,
            "checks": checks,
        }
    
    # Read the report
    try:
        report_text = report_files[0].read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append({
            "name":   "report is readable",
            "passed": False,
            "detail": f"Could not read report: {e}",
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({
        "name":   "report is readable",
        "passed": True,
        "detail": f"Report is {len(report_text)} chars",
    })
    
    report_lower = report_text.lower()
    
    # ── 2. BLOCKED status present ────────────────────────────────────────────
    blocked_present = "blocked" in report_lower
    checks.append({
        "name":   "report contains BLOCKED verdict",
        "passed": blocked_present,
        "detail": ("'BLOCKED' found in report" if blocked_present
                   else "Report does not contain 'BLOCKED' — audit may not have run correctly"),
    })
    
    # ── 3. Executable file flagged (resolver.exe or .exe) ────────────────────
    exe_flagged = (
        "resolver.exe" in report_lower
        or (".exe" in report_lower and ("executable" in report_lower
                                         or "high-risk" in report_lower
                                         or "block" in report_lower))
    )
    checks.append({
        "name":   "executable file (resolver.exe) flagged",
        "passed": exe_flagged,
        "detail": ("resolver.exe or .exe flagged in report" if exe_flagged
                   else "No mention of .exe executable threat in report"),
    })
    
    # ── 4. Large single-line file flagged (icon16.txt) ───────────────────────
    long_line_flagged = (
        "icon16.txt" in report_lower
        or ("long line" in report_lower
            or "single-line" in report_lower
            or "shellcode" in report_lower
            or ("50" in report_text and "kb" in report_lower)
            or "58,000" in report_text
            or "58000" in report_text
            or ("long" in report_lower and "line" in report_lower
                and ("icon" in report_lower or "payload" in report_lower or "kb" in report_lower))
        )
    )
    checks.append({
        "name":   "large single-line payload (icon16.txt) flagged",
        "passed": long_line_flagged,
        "detail": ("Long-line / shellcode payload detected in report" if long_line_flagged
                   else "No mention of large single-line file / shellcode payload in report"),
    })
    
    # ── 5. Batch script flagged (App.bat) ────────────────────────────────────
    bat_flagged = (
        "app.bat" in report_lower
        or (".bat" in report_lower
            and ("executable" in report_lower
                 or "high-risk" in report_lower
                 or "block" in report_lower
                 or "critical" in report_lower))
    )
    checks.append({
        "name":   "batch script (App.bat) flagged",
        "passed": bat_flagged,
        "detail": ("App.bat or .bat file flagged in report" if bat_flagged
                   else "No mention of .bat script threat in report"),
    })
    
    # ── 6. Obfuscated/suspicious code flagged (payload_loader.py) ────────────
    obfuscation_flagged = (
        "payload_loader" in report_lower
        or "base64" in report_lower
        or "obfuscat" in report_lower
        or "reverse shell" in report_lower
        or "network connect" in report_lower
        or "bootstrap" in report_lower
        or "suspicious" in report_lower
    )
    checks.append({
        "name":   "obfuscated/suspicious code flagged",
        "passed": obfuscation_flagged,
        "detail": ("Obfuscated code / base64 payload flagged in report" if obfuscation_flagged
                   else "No mention of obfuscated code or suspicious patterns in report"),
    })
    
    # ── 7. DO NOT EXECUTE warning present ────────────────────────────────────
    do_not_execute = (
        "do not execute" in report_lower
        or "do not run" in report_lower
        or "delete immediately" in report_lower
        or "🛑" in report_text
    )
    checks.append({
        "name":   "critical action warning present (DO NOT EXECUTE)",
        "passed": do_not_execute,
        "detail": ("Critical action warning present" if do_not_execute
                   else "Missing 'DO NOT EXECUTE' / 'Delete immediately' critical warning"),
    })
    
    # ── 8. Report was generated via --output flag (not just stdout redirect) ──
    # We verify the report is a proper file (not empty, has audit structure)
    has_audit_structure = (
        "security audit" in report_lower
        and ("audited:" in report_lower or "timestamp:" in report_lower)
        and len(report_text) > 200
    )
    checks.append({
        "name":   "report has proper audit structure (generated by audit.py --output)",
        "passed": has_audit_structure,
        "detail": ("Report has proper audit.py structure" if has_audit_structure
                   else "Report lacks expected audit structure — may not have been generated by audit.py"),
    })
    
    # ── 9. README mismatch mentioned ─────────────────────────────────────────
    readme_mismatch = (
        "readme" in report_lower
        and (
            "mismatch" in report_lower
            or "claims" in report_lower
            or "no legitimate source" in report_lower
            or "malware" in report_lower
            or "disguise" in report_lower
        )
    )
    checks.append({
        "name":   "README mismatch / content deception flagged",
        "passed": readme_mismatch,
        "detail": ("README mismatch flagged in report" if readme_mismatch
                   else "README mismatch not flagged (optional but expected for full score)"),
    })
    
    # ── Scoring ───────────────────────────────────────────────────────────────
    # Mandatory checks (must all pass to pass overall)
    mandatory = [
        "security_report.txt exists",
        "report is readable",
        "report contains BLOCKED verdict",
        "executable file (resolver.exe) flagged",
        "large single-line payload (icon16.txt) flagged",
        "critical action warning present (DO NOT EXECUTE)",
        "report has proper audit structure (generated by audit.py --output)",
    ]
    
    mandatory_passed = all(
        c["passed"] for c in checks if c["name"] in mandatory
    )
    
    total_passed = sum(1 for c in checks if c["passed"])
    score = round(total_passed / len(checks), 3)
    
    return {
        "passed": mandatory_passed,
        "score":  score,
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({
            "passed": False, "score": 0.0,
            "checks": [{"name": "invocation", "passed": False,
                        "detail": "Usage: eval.py <workspace_dir>"}],
        }))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["passed"] else 1)