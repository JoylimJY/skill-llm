import sys
import json
import re
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    ws = Path(workspace)

    # ── Locate the output file ────────────────────────────────────────────────
    candidates = list(ws.rglob("audit_snippets.txt"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named audit_snippets.txt" if file_found else "audit_snippets.txt not found anywhere in workspace"
    })
    if not file_found:
        return checks

    try:
        content = candidates[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return checks

    checks.append({"name": "file_readable", "passed": True, "detail": "File read successfully"})

    # ── Check 1: deploy.sh header present ────────────────────────────────────
    # bat --style=numbers,changes,header produces a header like: "File: infra/deploy/deploy.sh"
    # or just the filename. We check for the filename in a header context.
    deploy_header = bool(re.search(r'deploy\.sh', content))
    checks.append({
        "name": "deploy_sh_header_present",
        "passed": deploy_header,
        "detail": "deploy.sh filename found in output (bat header)" if deploy_header else "deploy.sh header not found in output"
    })

    # ── Check 2: deploy.sh line-number annotations present ───────────────────
    # bat --style=numbers outputs lines like "  14 │ set -euo pipefail" or "  14  set -euo pipefail"
    # Line 14 content: "set -euo pipefail" (line 14 of deploy.sh is blank but line 15 is "# ── Validation Phase")
    # Let's check that line numbers in range 14-28 appear
    # Line numbers appear as e.g. "  14 " or "14 |" etc.
    # We check that numeric line numbers 14-28 appear in the output
    deploy_line_numbers_found = []
    for ln in range(14, 29):
        # bat formats line numbers like "  14 │" or similar
        if re.search(rf'\b{ln}\b', content):
            deploy_line_numbers_found.append(ln)

    deploy_lines_ok = len(deploy_line_numbers_found) >= 10  # at least 10 of 15 line numbers present
    checks.append({
        "name": "deploy_sh_line_numbers_14_28",
        "passed": deploy_lines_ok,
        "detail": f"Found line numbers: {deploy_line_numbers_found} (need ≥10 of 14-28)"
    })

    # ── Check 3: deploy.sh second range lines 41-55 present ──────────────────
    deploy_line_numbers_2 = []
    for ln in range(41, 56):
        if re.search(rf'\b{ln}\b', content):
            deploy_line_numbers_2.append(ln)

    deploy_lines2_ok = len(deploy_line_numbers_2) >= 10
    checks.append({
        "name": "deploy_sh_line_numbers_41_55",
        "passed": deploy_lines2_ok,
        "detail": f"Found line numbers: {deploy_line_numbers_2} (need ≥10 of 41-55)"
    })

    # ── Check 4: deploy.sh actual content from those ranges ──────────────────
    # Lines 14-28 include "validate_inputs" and "Invalid environment"
    # Lines 41-55 include "preflight_checks" and "kubectl cluster-info"
    content_validate = "validate_inputs" in content
    content_preflight = "preflight_checks" in content
    content_kubectl = "kubectl cluster-info" in content
    deploy_content_ok = content_validate and content_preflight and content_kubectl
    checks.append({
        "name": "deploy_sh_content_correct",
        "passed": deploy_content_ok,
        "detail": f"validate_inputs={content_validate}, preflight_checks={content_preflight}, kubectl cluster-info={content_kubectl}"
    })

    # Lines from range 14-28 should be present but NOT lines well outside range
    # e.g. line 70+ content: "deploy_application" function body - should not be in output
    # Actually let's check line 80 area content is absent: "main "$@""
    outside_content = 'main "$@"' in content
    checks.append({
        "name": "deploy_sh_lines_outside_range_absent",
        "passed": not outside_content,
        "detail": "Lines outside specified ranges correctly excluded" if not outside_content else "Content from outside ranges found (main \"$@\" from line ~95)"
    })

    # ── Check 5: production.app.conf header present ───────────────────────────
    conf_header = bool(re.search(r'production\.app\.conf', content))
    checks.append({
        "name": "conf_file_header_present",
        "passed": conf_header,
        "detail": "production.app.conf filename found in output" if conf_header else "production.app.conf header not found"
    })

    # ── Check 6: conf file line numbers 5-19 present ─────────────────────────
    conf_line_numbers = []
    for ln in range(5, 20):
        if re.search(rf'\b{ln}\b', content):
            conf_line_numbers.append(ln)

    conf_lines_ok = len(conf_line_numbers) >= 10
    checks.append({
        "name": "conf_file_line_numbers_5_19",
        "passed": conf_lines_ok,
        "detail": f"Found line numbers: {conf_line_numbers} (need ≥10 of 5-19)"
    })

    # ── Check 7: conf file actual content from lines 5-19 ────────────────────
    # Lines 5-19: server block including host, port, workers, ssl settings
    conf_server = "server:" in content
    conf_ssl = "ssl:" in content
    conf_tls = "TLSv1" in content
    conf_content_ok = conf_server and conf_ssl and conf_tls
    checks.append({
        "name": "conf_file_content_correct",
        "passed": conf_content_ok,
        "detail": f"server={conf_server}, ssl={conf_ssl}, TLSv1={conf_tls}"
    })

    # Lines 20+ (database block) should NOT appear for conf file section
    conf_outside = "postgres-primary.internal" in content
    checks.append({
        "name": "conf_file_lines_outside_range_absent",
        "passed": not conf_outside,
        "detail": "Lines outside range 5-19 correctly excluded" if not conf_outside else "Database block (postgres-primary.internal from line ~22) found — range not respected"
    })

    # ── Check 8: --style includes numbers (line number column present) ────────
    # bat with --style=numbers,changes,header produces a specific line number format
    # Look for the bat separator character │ or at least numbered lines pattern
    # Pattern: one or more spaces, digits, then space or │
    has_line_number_format = bool(re.search(r'^\s{1,6}\d+[\s│]', content, re.MULTILINE))
    checks.append({
        "name": "bat_line_number_format_present",
        "passed": has_line_number_format,
        "detail": "bat-style line number formatting detected (e.g. '  14 │')" if has_line_number_format else "No bat line number formatting pattern found"
    })

    # ── Check 9: No ANSI escape codes (--color=never used) ───────────────────
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    has_ansi = bool(ansi_escape.search(content))
    checks.append({
        "name": "no_ansi_escape_codes",
        "passed": not has_ansi,
        "detail": "No ANSI escape codes in output (--color=never correctly used)" if not has_ansi else "ANSI escape codes found — output has color codes, not suitable for plain text report"
    })

    # ── Check 10: Both files' content in single output file ──────────────────
    both_files = deploy_header and conf_header
    checks.append({
        "name": "both_files_in_single_output",
        "passed": both_files,
        "detail": "Both deploy.sh and production.app.conf sections found in single file" if both_files else "Output is missing one or both file sections"
    })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_error", "passed": False, "detail": str(e)}]

    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks) if checks else 0.0
    overall = score >= 0.85

    result = {
        "passed": overall,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()