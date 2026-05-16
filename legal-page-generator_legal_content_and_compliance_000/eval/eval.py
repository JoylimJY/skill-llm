import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # --- FIND THE OUTPUT FILE ---
    # The agent should create cookie_policy.md (or similar) somewhere in the workspace
    candidate_files = list(workspace.rglob("cookie_policy.md"))
    
    if not candidate_files:
        # Also accept .txt variants with cookie_policy in the name
        candidate_files = list(workspace.rglob("cookie_policy*.md")) + list(workspace.rglob("cookie_policy*.txt"))

    file_found = len(candidate_files) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found cookie_policy output file at: {candidate_files[0]}" if file_found else "No cookie_policy.md file found anywhere in workspace."
    })

    if not file_found:
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    target_file = candidate_files[0]
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    content_lower = content.lower()

    # --- CHECK 1: Cookie Policy page type identified and titled ---
    has_cookie_policy_title = bool(re.search(r'cookie\s+policy', content_lower))
    checks.append({
        "name": "cookie_policy_title_present",
        "passed": has_cookie_policy_title,
        "detail": "Document must reference 'Cookie Policy' as the page type." if not has_cookie_policy_title else "Cookie Policy title/heading found."
    })

    # --- CHECK 2: GDPR / jurisdiction mentioned ---
    has_gdpr = bool(re.search(r'gdpr|general data protection|eu\b|european union', content_lower))
    checks.append({
        "name": "jurisdiction_gdpr_mentioned",
        "passed": has_gdpr,
        "detail": "GDPR or EU jurisdiction must be identified in the document." if not has_gdpr else "GDPR/EU jurisdiction reference found."
    })

    # --- CHECK 3: Cookie types section (must distinguish types) ---
    has_cookie_types = bool(re.search(
        r'(type[s]?\s+of\s+cookie|cookie\s+type|essential|functional|analytic|performance|marketing|third.party)',
        content_lower
    ))
    checks.append({
        "name": "cookie_types_section",
        "passed": has_cookie_types,
        "detail": "Must include a section on cookie types (essential, analytics, marketing, etc.)." if not has_cookie_types else "Cookie types section found."
    })

    # --- CHECK 4: Purposes explained ---
    has_purposes = bool(re.search(
        r'(purpose[s]?|why\s+we\s+use|used\s+for|we\s+use\s+(these\s+)?cookie|session|tracking|analytics|preference)',
        content_lower
    ))
    checks.append({
        "name": "cookie_purposes_section",
        "passed": has_purposes,
        "detail": "Must explain the purposes for which cookies are used." if not has_purposes else "Cookie purposes/usage section found."
    })

    # --- CHECK 5: How to manage cookies ---
    has_manage = bool(re.search(
        r'(manag|opt.out|disable|browser\s+setting|withdraw|consent|control\s+(your\s+)?cookie)',
        content_lower
    ))
    checks.append({
        "name": "cookie_management_section",
        "passed": has_manage,
        "detail": "Must include guidance on how users can manage/opt-out of cookies." if not has_manage else "Cookie management section found."
    })

    # --- CHECK 6: SEO recommendation is NOINDEX (critical proprietary trap) ---
    has_noindex = bool(re.search(r'noindex', content_lower))
    has_index_only = bool(re.search(r'\bindex\b', content_lower)) and not has_noindex
    
    seo_noindex_correct = has_noindex
    checks.append({
        "name": "seo_recommendation_noindex",
        "passed": seo_noindex_correct,
        "detail": (
            "SEO recommendation MUST specify 'noindex' for legal pages. "
            "Naive agents may recommend indexing — the skill requires noindex for legal pages."
            if not seo_noindex_correct
            else "Correct noindex SEO recommendation found."
        )
    })

    # --- CHECK 7: Footer placement mentioned ---
    has_footer = bool(re.search(r'footer', content_lower))
    checks.append({
        "name": "footer_placement_mentioned",
        "passed": has_footer,
        "detail": "Must include footer link placement recommendation." if not has_footer else "Footer placement recommendation found."
    })

    # --- CHECK 8: Disclaimer / legal review recommendation (proprietary trap) ---
    has_disclaimer = bool(re.search(
        r'(disclaimer|legal\s+review|consult\s+(a\s+)?lawyer|attorney|legal\s+counsel|recommend.*review|not\s+legal\s+advice)',
        content_lower
    ))
    checks.append({
        "name": "disclaimer_legal_review",
        "passed": has_disclaimer,
        "detail": (
            "Must include a disclaimer recommending legal review. "
            "This is a required output component per the skill specification."
            if not has_disclaimer
            else "Legal review disclaimer found."
        )
    })

    # --- CHECK 9: Structured outline (headings/sections present) ---
    has_structure = bool(re.search(r'^#{1,3}\s+\w+', content, re.MULTILINE)) or \
                    bool(re.search(r'\*\*[A-Z][\w\s]+\*\*', content)) or \
                    bool(re.search(r'^\d+\.\s+\w+', content, re.MULTILINE)) or \
                    bool(re.search(r'^[A-Z][A-Z\s]{3,}$', content, re.MULTILINE))
    checks.append({
        "name": "structured_outline_present",
        "passed": has_structure,
        "detail": "Document must have a structured outline with headings/sections." if not has_structure else "Structured outline with headings found."
    })

    # --- CHECK 10: Last updated / date field present ---
    has_date = bool(re.search(r'(last\s+updated|effective\s+date|date\s+of|version\s*:?\s*\d|updated\s*:)', content_lower))
    checks.append({
        "name": "last_updated_date_present",
        "passed": has_date,
        "detail": "Must include a 'Last Updated' date field as per legal page best practices." if not has_date else "Last updated date field found."
    })

    # --- SCORING ---
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = round(len(passed_checks) / total, 4)

    # Must pass all critical checks to be considered overall passed
    critical = ["output_file_exists", "seo_recommendation_noindex", "disclaimer_legal_review", 
                "cookie_types_section", "cookie_management_section"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))