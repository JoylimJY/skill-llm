import sys
import os
import re
import json
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    score = 0.0

    # --- Find the offer letter file ---
    offer_file = None
    candidates = list(Path(workspace).rglob("offer_letter_marcus_webb.txt"))
    if not candidates:
        # Try alternate reasonable names
        candidates = list(Path(workspace).rglob("*webb*offer*.txt")) + \
                     list(Path(workspace).rglob("*offer*webb*.txt")) + \
                     list(Path(workspace).rglob("*marcus*webb*.txt"))

    if candidates:
        offer_file = candidates[0]
        checks.append({"name": "offer_letter_file_exists", "passed": True, "detail": f"Found at {offer_file}"})
        score += 0.05
    else:
        checks.append({"name": "offer_letter_file_exists", "passed": False, "detail": "No offer letter file matching 'offer_letter_marcus_webb.txt' or similar found in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        content = offer_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    content_lower = content.lower()

    # ---- CHECK 1: Company Letterhead ----
    has_letterhead = "novabio therapeutics" in content_lower and (
        "400 oyster point" in content_lower or "south san francisco" in content_lower
    )
    checks.append({
        "name": "company_letterhead_present",
        "passed": has_letterhead,
        "detail": "Must include 'NovaBio Therapeutics' and the company address in the header." if not has_letterhead else "Letterhead found."
    })
    if has_letterhead:
        score += 0.05

    # ---- CHECK 2: Candidate name in letter ----
    has_candidate = "marcus webb" in content_lower or "dr. marcus webb" in content_lower
    checks.append({
        "name": "candidate_name_present",
        "passed": has_candidate,
        "detail": "Candidate name 'Marcus Webb' (or 'Dr. Marcus Webb') must appear in the letter."
    })
    if has_candidate:
        score += 0.05

    # ---- CHECK 3: Salutation uses first name only (Dear Marcus) ----
    dear_first = bool(re.search(r'dear\s+marcus\b', content_lower))
    checks.append({
        "name": "salutation_first_name_only",
        "passed": dear_first,
        "detail": "SKILL.md requires 'Dear [First Name]' format. Should be 'Dear Marcus,'."
    })
    if dear_first:
        score += 0.05

    # ---- CHECK 4: RE: line with job title ----
    re_line = bool(re.search(r're\s*:\s*employment offer\s*[-–]\s*director of clinical operations', content_lower))
    checks.append({
        "name": "re_subject_line",
        "passed": re_line,
        "detail": "Must include 'RE: Employment Offer - Director of Clinical Operations' per SKILL.md output structure."
    })
    if re_line:
        score += 0.05

    # ---- CHECK 5: POSITION DETAILS section header ----
    has_position_section = bool(re.search(r'position\s+details', content_lower))
    checks.append({
        "name": "position_details_section",
        "passed": has_position_section,
        "detail": "Must include 'POSITION DETAILS' section header per SKILL.md template."
    })
    if has_position_section:
        score += 0.05

    # ---- CHECK 6: Reports To Dr. Priya Nair with correct title ----
    has_manager = bool(re.search(r'priya\s+nair', content_lower)) and (
        "svp" in content_lower or "clinical development" in content_lower
    )
    checks.append({
        "name": "manager_name_and_title",
        "passed": has_manager,
        "detail": "Must include reporting manager Dr. Priya Nair, SVP Clinical Development."
    })
    if has_manager:
        score += 0.05

    # ---- CHECK 7: Start date August 4, 2025 ----
    has_start_date = bool(re.search(r'august\s+4[,.]?\s*2025', content_lower)) or \
                     bool(re.search(r'aug\.?\s+4[,.]?\s*2025', content_lower)) or \
                     "08/04/2025" in content or "2025-08-04" in content
    checks.append({
        "name": "start_date_correct",
        "passed": has_start_date,
        "detail": "Start date must be August 4, 2025."
    })
    if has_start_date:
        score += 0.05

    # ---- CHECK 8: COMPENSATION section header ----
    has_comp_section = bool(re.search(r'\bcompensation\b', content_lower))
    checks.append({
        "name": "compensation_section",
        "passed": has_comp_section,
        "detail": "Must include a COMPENSATION section per SKILL.md template."
    })
    if has_comp_section:
        score += 0.05

    # ---- CHECK 9: Base salary $205,000 ----
    has_base_salary = bool(re.search(r'\$\s*205[,\s]*000', content)) or "205,000" in content
    checks.append({
        "name": "base_salary_205000",
        "passed": has_base_salary,
        "detail": "Base salary of $205,000 must be explicitly stated."
    })
    if has_base_salary:
        score += 0.06

    # ---- CHECK 10: Bi-weekly payment schedule ----
    has_biweekly = bool(re.search(r'bi[\s-]?weekly', content_lower))
    checks.append({
        "name": "payment_schedule_biweekly",
        "passed": has_biweekly,
        "detail": "Payment schedule must be stated as bi-weekly per intake notes."
    })
    if has_biweekly:
        score += 0.04

    # ---- CHECK 11: Signing bonus $15,000 ----
    has_signing = bool(re.search(r'\$\s*15[,\s]*000', content)) or "15,000" in content
    checks.append({
        "name": "signing_bonus_15000",
        "passed": has_signing,
        "detail": "Signing bonus of $15,000 must appear in compensation section."
    })
    if has_signing:
        score += 0.05

    # ---- CHECK 12: Annual bonus 20% ----
    has_bonus_pct = bool(re.search(r'20\s*%', content)) and "bonus" in content_lower
    checks.append({
        "name": "annual_bonus_20pct",
        "passed": has_bonus_pct,
        "detail": "Annual bonus target of 20% must be stated."
    })
    if has_bonus_pct:
        score += 0.04

    # ---- CHECK 13: Equity - 18,000 options ----
    has_equity_count = bool(re.search(r'18[,\s]*000\s*(stock\s+)?options?', content_lower)) or \
                       ("18,000" in content and "option" in content_lower)
    checks.append({
        "name": "equity_18000_options",
        "passed": has_equity_count,
        "detail": "Equity grant of 18,000 stock options must be stated."
    })
    if has_equity_count:
        score += 0.04

    # ---- CHECK 14: Equity - 4-year vesting + 1-year cliff (PROPRIETARY TRAP) ----
    has_vest = bool(re.search(r'4[\s-]year\s+vest', content_lower)) or \
               bool(re.search(r'vest(?:ing)?\s+over\s+4\s+years?', content_lower))
    has_cliff = bool(re.search(r'1[\s-]year\s+cliff', content_lower))
    has_equity_terms = has_vest and has_cliff
    checks.append({
        "name": "equity_vesting_and_cliff_specified",
        "passed": has_equity_terms,
        "detail": "SKILL.md requires equity section to specify vesting schedule AND cliff. Must state '4-year vest' and '1-year cliff'."
    })
    if has_equity_terms:
        score += 0.07

    # ---- CHECK 15: Equity references full Option Agreement (from finance email + SKILL.md legal note) ----
    has_option_agreement_ref = bool(re.search(r'option\s+agreement', content_lower)) or \
                                bool(re.search(r'separate\s+(written\s+)?agreement', content_lower))
    checks.append({
        "name": "equity_references_option_agreement",
        "passed": has_option_agreement_ref,
        "detail": "SKILL.md states equity terms should reference full agreement. Finance email confirms this is required."
    })
    if has_option_agreement_ref:
        score += 0.04

    # ---- CHECK 16: BENEFITS section ----
    has_benefits_section = bool(re.search(r'\bbenefits?\b', content_lower))
    checks.append({
        "name": "benefits_section_present",
        "passed": has_benefits_section,
        "detail": "Must include a BENEFITS section per SKILL.md template."
    })
    if has_benefits_section:
        score += 0.03

    # ---- CHECK 17: Benefits content from 2025 plan ----
    has_401k = "401(k)" in content or "401k" in content_lower
    has_pto = bool(re.search(r'25\s+days', content_lower)) or "paid time off" in content_lower or "pto" in content_lower
    benefits_ok = has_401k and has_pto
    checks.append({
        "name": "benefits_2025_plan_details",
        "passed": benefits_ok,
        "detail": "Benefits should reflect 2025 plan: 401(k) with 5% match and 25 days PTO."
    })
    if benefits_ok:
        score += 0.03

    # ---- CHECK 18: CONTINGENCIES section (SKILL.md proprietary) ----
    has_contingencies = bool(re.search(r'contingent|contingencies', content_lower))
    has_bg_check = bool(re.search(r'background\s+check', content_lower))
    has_work_auth = bool(re.search(r'eligib\w+\s+to\s+work|work\s+eligib|i[\s-]?9|employment\s+verif', content_lower))
    contingencies_ok = has_contingencies and has_bg_check and has_work_auth
    checks.append({
        "name": "contingencies_section_with_details",
        "passed": contingencies_ok,
        "detail": "Must include contingencies: background check and work eligibility/I-9 verification."
    })
    if contingencies_ok:
        score += 0.05

    # ---- CHECK 19: Response deadline June 2, 2025 ----
    has_deadline = bool(re.search(r'june\s+2[,.]?\s*2025', content_lower)) or \
                   bool(re.search(r'jun\.?\s+2[,.]?\s*2025', content_lower)) or \
                   "06/02/2025" in content
    checks.append({
        "name": "response_deadline_june_2",
        "passed": has_deadline,
        "detail": "Offer expiry / response deadline must be June 2, 2025."
    })
    if has_deadline:
        score += 0.05

    # ---- CHECK 20: Signing manager - Dr. Priya Nair + title at bottom ----
    closing_section = content[-800:]  # Last 800 chars
    closing_lower = closing_section.lower()
    has_closing_manager = "priya nair" in closing_lower and (
        "svp" in closing_lower or "clinical development" in closing_lower
    )
    checks.append({
        "name": "closing_signature_manager",
        "passed": has_closing_manager,
        "detail": "Closing must be signed by Dr. Priya Nair, SVP Clinical Development (name + title at bottom)."
    })
    if has_closing_manager:
        score += 0.04

    # ---- CHECK 21: ACCEPTANCE block with separator (SKILL.md proprietary structure) ----
    has_acceptance_separator = "---" in content and "acceptance" in content_lower
    checks.append({
        "name": "acceptance_block_with_separator",
        "passed": has_acceptance_separator,
        "detail": "SKILL.md output structure requires '---' separator followed by ACCEPTANCE section."
    })
    if has_acceptance_separator:
        score += 0.04

    # ---- CHECK 22: Signature lines in acceptance block (exact format per SKILL.md) ----
    has_sig_line = bool(re.search(r'signature\s*:\s*_{5,}', content_lower))
    has_print_line = bool(re.search(r'print\s+name\s*:\s*_{5,}', content_lower))
    has_date_line = bool(re.search(r'date\s*:\s*_{5,}', content_lower))
    acceptance_lines_ok = has_sig_line and has_print_line and has_date_line
    checks.append({
        "name": "acceptance_signature_lines_exact_format",
        "passed": acceptance_lines_ok,
        "detail": "SKILL.md mandates exact signature lines: 'Signature: _______', 'Print Name: _______', 'Date: _______'."
    })
    if acceptance_lines_ok:
        score += 0.05

    # ---- CHECK 23: At-will employment statement ----
    has_at_will = bool(re.search(r'at[\s-]will', content_lower))
    checks.append({
        "name": "at_will_statement",
        "passed": has_at_will,
        "detail": "SKILL.md legal considerations require at-will employment to be stated clearly (US)."
    })
    if has_at_will:
        score += 0.04

    # ---- CHECK 24: Hybrid work location (South San Francisco, Mon+Wed) ----
    has_location = "south san francisco" in content_lower or "ssf" in content_lower
    has_hybrid = "hybrid" in content_lower
    location_ok = has_location and has_hybrid
    checks.append({
        "name": "work_location_hybrid_ssf",
        "passed": location_ok,
        "detail": "Work location should reflect hybrid arrangement at South San Francisco office."
    })
    if location_ok:
        score += 0.03

    # ---- CHECK 25: Full-time exempt employment type ----
    has_ft_exempt = bool(re.search(r'full[\s-]time', content_lower)) and "exempt" in content_lower
    checks.append({
        "name": "employment_type_fulltime_exempt",
        "passed": has_ft_exempt,
        "detail": "Employment type must state 'Full-time' and 'Exempt' per SKILL.md and intake notes."
    })
    if has_ft_exempt:
        score += 0.03

    # ---- Final pass/fail determination ----
    critical_checks = [
        "offer_letter_file_exists",
        "candidate_name_present",
        "base_salary_205000",
        "equity_vesting_and_cliff_specified",
        "acceptance_block_with_separator",
        "acceptance_signature_lines_exact_format",
        "contingencies_section_with_details",
        "response_deadline_june_2",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    # Normalize score to [0, 1]
    score = min(round(score, 3), 1.0)
    overall_passed = critical_passed and score >= 0.55

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))