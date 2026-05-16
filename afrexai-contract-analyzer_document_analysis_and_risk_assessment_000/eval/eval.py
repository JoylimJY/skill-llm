import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []

    # 1. Find the output analysis file
    output_file = None
    for candidate in Path(workspace_dir).rglob("contract_analysis.md"):
        output_file = candidate
        break

    if output_file is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "No file named 'contract_analysis.md' found anywhere in the workspace."}]
        }

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    content_lower = content.lower()

    # CHECK 1: Correct top-level header format
    header_match = bool(re.search(r"##\s+Contract Analysis:\s*.+", content))
    checks.append({
        "name": "correct_header_format",
        "passed": header_match,
        "detail": "Must contain '## Contract Analysis: [Title/Type]' header." if not header_match else "Header format correct."
    })

    # CHECK 2: Overall Risk Level declaration using exact format
    risk_level_match = bool(re.search(r"\*\*Risk Level:\s*(Low|Medium|High|Critical)\*\*", content, re.IGNORECASE))
    checks.append({
        "name": "risk_level_declaration",
        "passed": risk_level_match,
        "detail": "Must contain '**Risk Level: [Low/Medium/High/Critical]**'." if not risk_level_match else "Risk level declaration found."
    })

    # CHECK 3: Risk level is Critical or High (contract is severely one-sided)
    risk_level_value_match = bool(re.search(r"\*\*Risk Level:\s*(High|Critical)\*\*", content, re.IGNORECASE))
    checks.append({
        "name": "risk_level_is_high_or_critical",
        "passed": risk_level_value_match,
        "detail": "Given the extremely one-sided terms, Risk Level must be 'High' or 'Critical'." if not risk_level_value_match else "Risk level correctly assessed as High/Critical."
    })

    # CHECK 4: All five required section headers present
    required_sections = ["### Summary", "### Risk Flags", "### Missing Clauses", "### Plain English", "### Top Negotiation Points"]
    missing_sections = []
    for section in required_sections:
        if section.lower() not in content_lower:
            missing_sections.append(section)
    sections_present = len(missing_sections) == 0
    checks.append({
        "name": "all_five_sections_present",
        "passed": sections_present,
        "detail": f"Missing sections: {missing_sections}" if not sections_present else "All five required sections present."
    })

    # CHECK 5: Risk Flags table has the correct column headers
    table_header_match = bool(re.search(r"\|\s*#\s*\|\s*Clause\s*\|\s*Risk\s*\|\s*Issue\s*\|\s*Suggestion\s*\|", content, re.IGNORECASE))
    checks.append({
        "name": "risk_table_correct_columns",
        "passed": table_header_match,
        "detail": "Risk Flags table must have columns: # | Clause | Risk | Issue | Suggestion" if not table_header_match else "Risk table column format correct."
    })

    # CHECK 6: Emoji risk indicators used (🔴 or 🟡 or 🟢)
    has_red = "🔴" in content
    has_yellow = "🟡" in content
    has_green = "🟢" in content
    emoji_used = has_red or has_yellow
    checks.append({
        "name": "emoji_risk_indicators_used",
        "passed": emoji_used,
        "detail": "Must use 🔴 and/or 🟡 emoji risk indicators in the Risk Flags table." if not emoji_used else f"Emoji indicators found: 🔴={has_red}, 🟡={has_yellow}, 🟢={has_green}."
    })

    # CHECK 7: Mandatory legal disclaimer present
    disclaimer_match = bool(re.search(r"(AI analysis|not legal advice|consult an attorney)", content, re.IGNORECASE))
    checks.append({
        "name": "mandatory_disclaimer_present",
        "passed": disclaimer_match,
        "detail": "Must include disclaimer: 'This is AI analysis, not legal advice. Consult an attorney...'." if not disclaimer_match else "Legal disclaimer found."
    })

    # CHECK 8: Key risks identified - unlimited client liability (Section 6.3)
    liability_risk = bool(re.search(r"(unlimited.*liabilit|liabilit.*unlimited|6\.3|client.*liabilit.*unlimited)", content_lower))
    checks.append({
        "name": "identifies_unlimited_client_liability",
        "passed": liability_risk,
        "detail": "Must flag Section 6.3 (unlimited client liability) as a risk." if not liability_risk else "Unlimited client liability risk identified."
    })

    # CHECK 9: Key risks identified - one-sided indemnification (Section 5)
    indemnity_risk = bool(re.search(r"(indemnif|section 5|one.sided|no.*vendor.*indemn)", content_lower))
    checks.append({
        "name": "identifies_onesided_indemnification",
        "passed": indemnity_risk,
        "detail": "Must flag one-sided indemnification (Section 5) as a risk." if not indemnity_risk else "One-sided indemnification risk identified."
    })

    # CHECK 10: Key risks identified - aggressive auto-renewal (Section 3.1 - 180 days notice)
    autorenewal_risk = bool(re.search(r"(auto.renew|180.day|six.month|automatic.*renew|renew.*180)", content_lower))
    checks.append({
        "name": "identifies_aggressive_autorenewal",
        "passed": autorenewal_risk,
        "detail": "Must flag 180-day notice window for auto-renewal (Section 3.1) as a risk." if not autorenewal_risk else "Auto-renewal risk identified."
    })

    # CHECK 11: Key risks identified - IP ownership (Section 4)
    ip_risk = bool(re.search(r"(intellectual property|ip ownership|work product|section 4|assigns.*vendor|vendor.*owns)", content_lower))
    checks.append({
        "name": "identifies_ip_ownership_risk",
        "passed": ip_risk,
        "detail": "Must flag IP/work product ownership clause (Section 4) as a risk." if not ip_risk else "IP ownership risk identified."
    })

    # CHECK 12: Missing clauses section identifies force majeure
    force_majeure_missing = bool(re.search(r"force majeure", content_lower))
    checks.append({
        "name": "missing_force_majeure_identified",
        "passed": force_majeure_missing,
        "detail": "Must identify missing force majeure clause." if not force_majeure_missing else "Missing force majeure clause correctly identified."
    })

    # CHECK 13: Missing clauses or risk flags identify missing data/privacy clause
    data_privacy_missing = bool(re.search(r"(data privacy|privacy|hipaa|data protection|gdpr)", content_lower))
    checks.append({
        "name": "missing_data_privacy_identified",
        "passed": data_privacy_missing,
        "detail": "Must identify missing data/privacy clause (critical for healthcare context)." if not data_privacy_missing else "Missing data/privacy clause identified."
    })

    # CHECK 14: Negotiation points section has 3-5 items with suggested alternative language
    negotiation_section_match = re.search(r"###\s*Top Negotiation Points(.*?)(?=###|\Z)", content, re.DOTALL | re.IGNORECASE)
    has_alternative_language = False
    negotiation_count = 0
    if negotiation_section_match:
        neg_text = negotiation_section_match.group(1)
        # Count numbered items or bullet points
        numbered = re.findall(r"^\s*(\d+[\.\)]|\*|-)\s+", neg_text, re.MULTILINE)
        negotiation_count = len(numbered)
        # Check for suggested alternative language keywords
        has_alternative_language = bool(re.search(r"(suggest|alternative|replace.*with|instead|propose|recommend.*language|changed to|revised)", neg_text, re.IGNORECASE))

    negotiation_valid = (3 <= negotiation_count <= 5) and has_alternative_language
    checks.append({
        "name": "negotiation_points_3_to_5_with_alternatives",
        "passed": negotiation_valid,
        "detail": f"Must have 3-5 negotiation points with suggested alternative language. Found {negotiation_count} items, has_alternative_language={has_alternative_language}." if not negotiation_valid else f"Negotiation section valid: {negotiation_count} items with alternative language."
    })

    # CHECK 15: Identifies Vendor's $100 liability cap
    vendor_cap_risk = bool(re.search(r"(\$100|one hundred dollar|100\.00|vendor.*cap|liability.*cap.*100)", content_lower))
    checks.append({
        "name": "identifies_vendor_100_dollar_cap",
        "passed": vendor_cap_risk,
        "detail": "Must flag the absurdly low $100 liability cap for Vendor (Section 6.2)." if not vendor_cap_risk else "Vendor's $100 liability cap risk identified."
    })

    # Scoring
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    passed = score >= 0.75 and checks[0]["passed"]  # File must exist AND majority of checks pass

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))