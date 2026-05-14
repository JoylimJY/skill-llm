import sys
import json
import re
from pathlib import Path

def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def count_lines(content):
    return len([l for l in content.strip().split('\n') if l.strip()])

def run_checks(workspace):
    ws = Path(workspace)
    checks = []

    # --- Find the root CLAUDE.md ---
    root_claude_path = ws / "CLAUDE.md"
    root_content = load_file(root_claude_path)

    # CHECK 1: Root CLAUDE.md exists
    checks.append({
        "name": "root_CLAUDE.md_exists",
        "passed": root_content is not None,
        "detail": "Root CLAUDE.md must exist at project root." if root_content is None else "Root CLAUDE.md found."
    })
    if root_content is None:
        root_content = ""

    # CHECK 2: Root CLAUDE.md is under 50 lines (non-empty lines)
    root_line_count = count_lines(root_content)
    passed_line_count = root_line_count <= 50
    checks.append({
        "name": "root_CLAUDE.md_under_50_lines",
        "passed": passed_line_count,
        "detail": f"Root CLAUDE.md has {root_line_count} non-empty lines. Must be <= 50."
    })

    # CHECK 3: Root CLAUDE.md must NOT contain generic coding advice
    generic_patterns = [
        r"write clean code",
        r"meaningful variable names",
        r"DRY principle",
        r"SOLID principle",
        r"handle errors appropriately",
        r"keep functions small",
        r"use async.await",
        r"magic numbers",
        r"use destructuring",
        r"prefer const over let",
        r"avoid var",
        r"arrow functions",
        r"functional components over class",
    ]
    found_generic = []
    for pat in generic_patterns:
        if re.search(pat, root_content, re.IGNORECASE):
            found_generic.append(pat)
    checks.append({
        "name": "root_CLAUDE.md_no_generic_coding_advice",
        "passed": len(found_generic) == 0,
        "detail": f"Root CLAUDE.md contains generic advice Claude already knows: {found_generic}" if found_generic else "No generic coding advice found."
    })

    # CHECK 4: Root CLAUDE.md must NOT contain duplicate rules (e.g., .env rule appears twice)
    env_mentions = len(re.findall(r"NEVER commit .env", root_content, re.IGNORECASE))
    auth_mentions = len(re.findall(r"NEVER modify.*auth\.ts", root_content, re.IGNORECASE))
    no_duplicates = (env_mentions <= 1) and (auth_mentions <= 1)
    checks.append({
        "name": "root_CLAUDE.md_no_duplicate_rules",
        "passed": no_duplicates,
        "detail": f".env rule appears {env_mentions}x, auth.ts rule appears {auth_mentions}x. Each must appear at most once." if not no_duplicates else "No duplicate critical rules found."
    })

    # CHECK 5: Root CLAUDE.md must contain critical non-obvious rules
    # - auth.ts warning
    has_auth_rule = bool(re.search(r"auth\.ts", root_content, re.IGNORECASE))
    # - PO = Purchase Order domain terminology
    has_po_term = bool(re.search(r"PO\s*=\s*Purchase Order", root_content, re.IGNORECASE))
    # - Zustand preference (non-obvious)
    has_zustand = bool(re.search(r"zustand", root_content, re.IGNORECASE))
    # - clsx preference (non-obvious)
    has_clsx = bool(re.search(r"clsx", root_content, re.IGNORECASE))
    # - .env warning
    has_env_rule = bool(re.search(r"\.env", root_content, re.IGNORECASE))

    critical_rules_passed = has_auth_rule and has_po_term and has_zustand and has_clsx and has_env_rule
    checks.append({
        "name": "root_CLAUDE.md_retains_critical_nontrivial_rules",
        "passed": critical_rules_passed,
        "detail": (
            f"auth.ts rule: {has_auth_rule}, PO=Purchase Order: {has_po_term}, "
            f"Zustand: {has_zustand}, clsx: {has_clsx}, .env: {has_env_rule}. All must be present."
        )
    })

    # CHECK 6: Root CLAUDE.md must use shortened/consolidated build commands (not full paths)
    # Must have test command (jest or pnpm test), build command
    has_test_cmd = bool(re.search(r"`(jest|pnpm test|npm test)[^`]*`", root_content))
    has_build_cmd = bool(re.search(r"`(pnpm build|npm run build|tsc.*next build)[^`]*`", root_content))
    checks.append({
        "name": "root_CLAUDE.md_has_build_and_test_commands",
        "passed": has_test_cmd and has_build_cmd,
        "detail": f"Test command present: {has_test_cmd}, Build command present: {has_build_cmd}."
    })

    # CHECK 7: Root CLAUDE.md must NOT contain aspirational/process rules Claude can't enforce
    # (git workflow, team contact info, testing coverage %, OWASP, agile methodology)
    aspirational_patterns = [
        r"agile",
        r"two.week sprint",
        r"contact.*team",
        r"get at least one approval",
        r"squash commits",
        r"OWASP",
        r"code coverage",
        r">80%",
        r"for questions",
        r"contact the",
    ]
    found_aspirational = []
    for pat in aspirational_patterns:
        if re.search(pat, root_content, re.IGNORECASE):
            found_aspirational.append(pat)
    checks.append({
        "name": "root_CLAUDE.md_no_aspirational_team_process_rules",
        "passed": len(found_aspirational) == 0,
        "detail": f"Found aspirational/process content: {found_aspirational}" if found_aspirational else "No aspirational/team process content found."
    })

    # CHECK 8: Root CLAUDE.md must NOT have overused IMPORTANT (should be used sparingly)
    important_count = len(re.findall(r"\bIMPORTANT\b", root_content, re.IGNORECASE))
    # Sparingly = at most 1-2 uses (the SKILL.md says "use sparingly or loses effect")
    important_ok = important_count <= 2
    checks.append({
        "name": "root_CLAUDE.md_IMPORTANT_used_sparingly",
        "passed": important_ok,
        "detail": f"IMPORTANT appears {important_count} times. Should be <= 2 for impact. Found {important_count}."
    })

    # CHECK 9: Payments subdir CLAUDE.md must be fixed - no duplicated cross-module rules
    payments_claude_path = ws / "src" / "payments" / "CLAUDE.md"
    payments_content = load_file(payments_claude_path)
    if payments_content is None:
        checks.append({
            "name": "payments_CLAUDE.md_cleaned_of_cross_module_duplicates",
            "passed": False,
            "detail": "src/payments/CLAUDE.md not found or not readable."
        })
    else:
        # Should NOT contain cross-module rules: auth.ts, global .env warning (already in root), global state rule
        has_auth_in_payments = bool(re.search(r"auth\.ts", payments_content, re.IGNORECASE))
        has_global_env_in_payments = bool(re.search(r"NEVER commit .env", payments_content, re.IGNORECASE))
        has_global_state_in_payments = bool(re.search(r"zustand.*not.*useState|useState.*not.*zustand", payments_content, re.IGNORECASE))
        has_generic_in_payments = bool(re.search(r"write clean code|meaningful variable", payments_content, re.IGNORECASE))

        no_cross_module_dupes = not has_auth_in_payments and not has_global_env_in_payments and not has_global_state_in_payments and not has_generic_in_payments
        checks.append({
            "name": "payments_CLAUDE.md_cleaned_of_cross_module_duplicates",
            "passed": no_cross_module_dupes,
            "detail": (
                f"auth.ts in payments: {has_auth_in_payments}, "
                f"global .env in payments: {has_global_env_in_payments}, "
                f"global state rule in payments: {has_global_state_in_payments}, "
                f"generic advice in payments: {has_generic_in_payments}. "
                "All should be False (removed as cross-module duplicates)."
            )
        })

    # CHECK 10: payments CLAUDE.md is also concise (under 20 lines for a module file)
    if payments_content:
        payments_line_count = count_lines(payments_content)
        payments_concise = payments_line_count <= 20
        checks.append({
            "name": "payments_CLAUDE.md_is_concise",
            "passed": payments_concise,
            "detail": f"src/payments/CLAUDE.md has {payments_line_count} non-empty lines. Should be <= 20 for a submodule file."
        })
    else:
        checks.append({
            "name": "payments_CLAUDE.md_is_concise",
            "passed": False,
            "detail": "src/payments/CLAUDE.md not found, cannot check conciseness."
        })

    # CHECK 11: Root CLAUDE.md uses bullet points (not paragraphs) and has markdown headings
    has_headings = bool(re.search(r"^##\s+\w+", root_content, re.MULTILINE))
    has_bullets = bool(re.search(r"^\s*[-*]\s+", root_content, re.MULTILINE))
    checks.append({
        "name": "root_CLAUDE.md_uses_headings_and_bullets",
        "passed": has_headings and has_bullets,
        "detail": f"Has markdown headings: {has_headings}, Has bullet points: {has_bullets}."
    })

    # CHECK 12: Root CLAUDE.md must NOT contain long prose/welcome paragraphs
    # The bloated original had paragraphs like "Welcome to the PayStream Core project!"
    has_welcome_prose = bool(re.search(r"welcome to|please read all sections|this document contains comprehensive", root_content, re.IGNORECASE))
    has_about_prose = bool(re.search(r"the team uses|for questions about|contact the.*team", root_content, re.IGNORECASE))
    no_prose = not has_welcome_prose and not has_about_prose
    checks.append({
        "name": "root_CLAUDE.md_no_long_prose_or_welcome_text",
        "passed": no_prose,
        "detail": f"Welcome prose: {has_welcome_prose}, About/contact prose: {has_about_prose}. Both must be False."
    })

    # Calculate score
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))