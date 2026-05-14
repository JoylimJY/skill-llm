import sys
import os
import re
import json

def evaluate(workspace: str):
    checks = []

    # ── Locate the review report ──────────────────────────────────────────────
    from pathlib import Path
    candidates = list(Path(workspace).rglob("pr_review_report.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False,
                         "detail": "pr_review_report.md not found anywhere in workspace."}]
        }

    report_path = candidates[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": str(e)}]
        }

    # ── Check 1: File exists ──────────────────────────────────────────────────
    checks.append({"name": "file_exists", "passed": True,
                   "detail": f"Found at {report_path}"})

    # ── Check 2: Header — exact format ───────────────────────────────────────
    has_header = bool(re.search(r'##\s+📋\s+Resumen de Revisión del PR', content))
    checks.append({"name": "header_format",
                   "passed": has_header,
                   "detail": "Must contain '## 📋 Resumen de Revisión del PR'"})

    # ── Check 3: Veredicto line with emoji ────────────────────────────────────
    # Must contain one of the three exact verdict patterns
    verdict_pattern = re.search(
        r'\*\*Veredicto:\*\*\s*(✅|⚠️|❌)\s*(APROBAR CON CAMBIOS|APROBAR|RECHAZAR)',
        content
    )
    has_verdict = verdict_pattern is not None
    checks.append({"name": "verdict_line",
                   "passed": has_verdict,
                   "detail": "Must contain '**Veredicto:** [✅|⚠️|❌] [APROBAR|APROBAR CON CAMBIOS|RECHAZAR]'"})

    # ── Check 4: Verdict must be RECHAZAR or APROBAR CON CAMBIOS (not APROBAR) ──
    correct_verdict = False
    if has_verdict:
        verdict_emoji = verdict_pattern.group(1)
        verdict_text = verdict_pattern.group(2)
        # Given BLOCKER issues, must NOT be plain ✅ APROBAR
        correct_verdict = not (verdict_emoji == "✅" and verdict_text == "APROBAR")
    checks.append({"name": "verdict_not_approve",
                   "passed": correct_verdict,
                   "detail": "Given critical security issues, verdict must be ❌ RECHAZAR or ⚠️ APROBAR CON CAMBIOS"})

    # ── Check 5: Findings summary line with four severity counts ─────────────
    findings_line = bool(re.search(
        r'\*\*Hallazgos:\*\*.*🔴.*🟡.*🔵.*💡',
        content
    ))
    checks.append({"name": "findings_summary_line",
                   "passed": findings_line,
                   "detail": "Must contain '**Hallazgos:** X 🔴 | X 🟡 | X 🔵 | X 💡'"})

    # ── Check 6: Archivos revisados count ≥ 3 ────────────────────────────────
    archivos_match = re.search(r'\*\*Archivos revisados:\*\*\s*(\d+)', content)
    archivos_ok = False
    if archivos_match:
        count = int(archivos_match.group(1))
        archivos_ok = count >= 3
    checks.append({"name": "archivos_revisados_gte_3",
                   "passed": archivos_ok,
                   "detail": "Must report at least 3 reviewed files (charge.py, webhook.js, invoice.php)"})

    # ── Check 7: Per-file sections using 📁 prefix ───────────────────────────
    file_sections = re.findall(r'###\s+📁\s+\S+', content)
    has_file_sections = len(file_sections) >= 3
    checks.append({"name": "file_section_headers",
                   "passed": has_file_sections,
                   "detail": f"Must have ≥3 '### 📁 filename' sections. Found: {len(file_sections)}"})

    # ── Check 8: At least one BLOCKER (🔴) finding ───────────────────────────
    blocker_count = len(re.findall(r'🔴', content))
    has_blockers = blocker_count >= 3
    checks.append({"name": "blocker_findings_present",
                   "passed": has_blockers,
                   "detail": f"Must have ≥3 🔴 BLOCKER findings (hardcoded secrets, SQL injection, etc). Found: {blocker_count}"})

    # ── Check 9: ❌ Código actual: pattern present ────────────────────────────
    current_code_sections = len(re.findall(r'❌\s+Código actual:', content))
    has_current_code = current_code_sections >= 3
    checks.append({"name": "current_code_blocks",
                   "passed": has_current_code,
                   "detail": f"Must have ≥3 '❌ Código actual:' sections. Found: {current_code_sections}"})

    # ── Check 10: ✅ Corrección sugerida: pattern present ────────────────────
    fix_sections = len(re.findall(r'✅\s+Corrección sugerida:', content))
    has_fixes = fix_sections >= 3
    checks.append({"name": "fix_suggestion_blocks",
                   "passed": has_fixes,
                   "detail": f"Must have ≥3 '✅ Corrección sugerida:' sections. Found: {fix_sections}"})

    # ── Check 11: ¿Por qué? explanation blocks ───────────────────────────────
    why_blocks = len(re.findall(r'\*\*¿Por qué\?\*\*', content))
    has_why = why_blocks >= 3
    checks.append({"name": "por_que_explanations",
                   "passed": has_why,
                   "detail": f"Must have ≥3 '**¿Por qué?**' explanation blocks. Found: {why_blocks}"})

    # ── Check 12: Resumen Final section ──────────────────────────────────────
    has_resumen_final = bool(re.search(r'###\s+🏁\s+Resumen Final', content))
    checks.append({"name": "resumen_final_section",
                   "passed": has_resumen_final,
                   "detail": "Must contain '### 🏁 Resumen Final' section"})

    # ── Check 13: Hardcoded secret flagged (SECRET_KEY / WEBHOOK_SECRET / dbPass) ──
    secret_flagged = bool(re.search(
        r'(sk_live|WEBHOOK_SECRET|SECRET_KEY|DB_PASSWORD|wh_secret|rootpass|dbPass)',
        content, re.IGNORECASE
    ))
    checks.append({"name": "hardcoded_secret_flagged",
                   "passed": secret_flagged,
                   "detail": "Must flag hardcoded secrets (sk_live_*, wh_secret_*, DB_PASSWORD, dbPass)"})

    # ── Check 14: SQL injection flagged ──────────────────────────────────────
    sql_injection_flagged = bool(re.search(
        r'(SQL injection|inyección SQL|concatenac|parameteriz|prepared statement|PDO)',
        content, re.IGNORECASE
    ))
    checks.append({"name": "sql_injection_flagged",
                   "passed": sql_injection_flagged,
                   "detail": "Must flag SQL injection vulnerabilities in charge.py, webhook.js, invoice.php"})

    # ── Check 15: Python-specific issues flagged (type hints, bare except, pickle) ──
    python_issues_flagged = (
        bool(re.search(r'(type hint|pickle|bare except|except:)', content, re.IGNORECASE))
    )
    checks.append({"name": "python_specific_issues",
                   "passed": python_issues_flagged,
                   "detail": "Must flag Python-specific issues: missing type hints, bare except, unsafe pickle"})

    # ── Check 16: JS-specific issues flagged (var, ==, console.log) ─────────
    js_issues_flagged = (
        bool(re.search(r'(usar var|use var|\bvar\b.*forbidden|console\.log|===|strict equality)', content, re.IGNORECASE))
        or bool(re.search(r'(var\s+|console\.log|==\s)', content))
    )
    # More lenient: just check that var or console.log is mentioned as an issue
    js_issues_flagged = bool(re.search(r'(console\.log|`var`|\bvar\b|==\b)', content, re.IGNORECASE))
    checks.append({"name": "js_specific_issues",
                   "passed": js_issues_flagged,
                   "detail": "Must flag JS issues: var usage, console.log, loose equality (==)"})

    # ── Check 17: PHP-specific issues flagged (md5, SQL concat, htmlspecialchars) ──
    php_issues_flagged = bool(re.search(
        r'(md5|htmlspecialchars|PDO|prepared|password_hash|XSS|\$_GET|\$_POST)',
        content, re.IGNORECASE
    ))
    checks.append({"name": "php_specific_issues",
                   "passed": php_issues_flagged,
                   "detail": "Must flag PHP issues: md5 password, SQL injection, missing htmlspecialchars/XSS"})

    # ── Check 18: TODO/FIXME flagged as convention violation ─────────────────
    todo_flagged = bool(re.search(r'(TODO|FIXME)', content, re.IGNORECASE))
    checks.append({"name": "todo_fixme_flagged",
                   "passed": todo_flagged,
                   "detail": "Must flag TODO/FIXME comments per team-conventions.md"})

    # ── Check 19: Resumen Final has the three sub-items ──────────────────────
    has_lo_bueno = bool(re.search(r'- Lo bueno:', content))
    has_must_fix = bool(re.search(r'- Lo que debe corregirse', content))
    has_sugerencias = bool(re.search(r'- Sugerencias para el futuro:', content))
    resumen_complete = has_lo_bueno and has_must_fix and has_sugerencias
    checks.append({"name": "resumen_final_complete",
                   "passed": resumen_complete,
                   "detail": f"Resumen Final needs 'Lo bueno', 'Lo que debe corregirse', 'Sugerencias para el futuro'. Found: bueno={has_lo_bueno}, fix={has_must_fix}, sug={has_sugerencias}"})

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Checks are weighted — critical structural checks count more
    weights = {
        "file_exists": 1,
        "header_format": 2,
        "verdict_line": 2,
        "verdict_not_approve": 2,
        "findings_summary_line": 2,
        "archivos_revisados_gte_3": 1,
        "file_section_headers": 2,
        "blocker_findings_present": 3,
        "current_code_blocks": 2,
        "fix_suggestion_blocks": 2,
        "por_que_explanations": 2,
        "resumen_final_section": 2,
        "hardcoded_secret_flagged": 3,
        "sql_injection_flagged": 3,
        "python_specific_issues": 2,
        "js_specific_issues": 2,
        "php_specific_issues": 2,
        "todo_fixme_flagged": 1,
        "resumen_final_complete": 2,
    }
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)

    # Must pass all structural + all critical security checks to pass overall
    critical = ["header_format", "verdict_line", "verdict_not_approve",
                "findings_summary_line", "file_section_headers", "blocker_findings_present",
                "current_code_blocks", "fix_suggestion_blocks", "resumen_final_section",
                "hardcoded_secret_flagged", "sql_injection_flagged"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)

    return {
        "passed": critical_passed and score >= 0.75,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))