import sys
import json
import re
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    ws = Path(workspace)

    # ── 1. Locate the report file ─────────────────────────────────────────────
    report_candidates = list(ws.rglob("vendor_risk_report.md"))
    report_found = len(report_candidates) > 0
    checks.append({
        "name": "report_file_exists",
        "passed": report_found,
        "detail": f"Found {len(report_candidates)} file(s) named vendor_risk_report.md" if report_found
                  else "No file named vendor_risk_report.md found anywhere in workspace."
    })
    if not report_found:
        return False, 0.0, checks

    report_path = report_candidates[0]

    try:
        content = report_path.read_text(errors="replace")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        return False, 0.0, checks

    checks.append({"name": "report_readable", "passed": True, "detail": f"Report read from {report_path}"})

    # ── 2. Report must be non-trivial markdown from audit.py ─────────────────
    has_header = bool(re.search(r"#\s+Security Audit Report", content, re.IGNORECASE))
    checks.append({
        "name": "markdown_audit_header_present",
        "passed": has_header,
        "detail": "Found '# Security Audit Report' header." if has_header
                  else "Missing '# Security Audit Report' header — audit.py output not detected."
    })

    # ── 3. Risk level must be HIGH (3+ findings in flagged file) ─────────────
    risk_match = re.search(r"##\s+Risk Level:\s*(HIGH|MEDIUM|LOW)", content)
    risk_correct = risk_match is not None and risk_match.group(1) == "HIGH"
    checks.append({
        "name": "risk_level_is_HIGH",
        "passed": risk_correct,
        "detail": f"Risk level found: {risk_match.group(1) if risk_match else 'NOT FOUND'} (expected HIGH)."
    })

    # ── 4. Findings section must include exfiltration patterns ────────────────
    exfil_patterns = [
        r"HTTP POST",
        r"reads.*\.env|\.env.*cat|credential keyword|unknown external domain|exfiltration",
    ]
    findings_hits = [p for p in exfil_patterns if re.search(p, content, re.IGNORECASE)]
    has_findings = len(findings_hits) >= 1
    checks.append({
        "name": "findings_section_contains_exfil_patterns",
        "passed": has_findings,
        "detail": f"Matched {len(findings_hits)}/{len(exfil_patterns)} expected exfiltration finding patterns."
    })

    # ── 5. Permission Manifest section must be present ────────────────────────
    has_manifest = bool(re.search(r"##\s+Permission Manifest", content, re.IGNORECASE))
    checks.append({
        "name": "permission_manifest_section_present",
        "passed": has_manifest,
        "detail": "Found '## Permission Manifest' section." if has_manifest
                  else "Missing '## Permission Manifest' section."
    })

    # ── 6. Report references the correct audited file ─────────────────────────
    references_target = bool(re.search(r"vendor-data-sync", content, re.IGNORECASE))
    checks.append({
        "name": "report_references_vendor_data_sync",
        "passed": references_target,
        "detail": "Report mentions 'vendor-data-sync' (correct target file)." if references_target
                  else "Report does not mention 'vendor-data-sync' — wrong file may have been audited."
    })

    # ── 7. Summary line present ───────────────────────────────────────────────
    has_summary = bool(re.search(r"##\s+Summary", content, re.IGNORECASE))
    checks.append({
        "name": "summary_section_present",
        "passed": has_summary,
        "detail": "Found '## Summary' section." if has_summary else "Missing '## Summary' section."
    })

    # ── 8. Summary reports multiple findings (>=3) ────────────────────────────
    summary_count_match = re.search(r"(\d+)\s+suspicious pattern", content, re.IGNORECASE)
    count_ok = False
    count_detail = "Could not parse suspicious pattern count from Summary."
    if summary_count_match:
        count = int(summary_count_match.group(1))
        count_ok = count >= 3
        count_detail = f"Summary reports {count} suspicious pattern(s) (need >= 3 for HIGH)."
    checks.append({
        "name": "summary_finding_count_gte_3",
        "passed": count_ok,
        "detail": count_detail
    })

    # ── Score ─────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = all(c["passed"] for c in checks)

    return all_passed, score, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        all_passed, score, checks = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crashed", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result))
        return

    print(json.dumps({"passed": all_passed, "score": score, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()