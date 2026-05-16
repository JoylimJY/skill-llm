import sys
import json
import os
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # ── Locate the output file ──────────────────────────────────────────────
    # The agent should create a file named legal_advice_wang_xiaoming.md (or similar)
    # We search for any .md or .txt file in output/ or workspace root that is NOT
    # one of the known input files.
    known_input_files = {
        "client_intake_wang_xiaoming.txt",
        "assets/labor-dispute-complaint.md",
        "assets/rental-agreement.md",
        "assets/employment-contract.md",
        "assets/divorce-agreement.md",
        "assets/traffic-accident-claim.md",
        "references/legal-document-guide.md",
        "references/dispute-resolution-guide.md",
    }
    distractor_names = {
        "case_001_summary.txt", "case_002_notes.txt", "case_010_overview.txt",
        "case_031_intake.txt", "case_032_intake.txt", "arbitration_v1.txt",
        "rental_v1.txt", "procedure_reminders.txt", "client_intake_checklist.txt",
        "draft_2024_01_labor.txt", "README_ignore.txt", "access_log_20240315.txt",
        "settings.json",
    }

    candidate_files = []
    for p in workspace.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(workspace))
            name_only = p.name
            if rel not in known_input_files and name_only not in distractor_names:
                if p.suffix in (".md", ".txt", ".json", ""):
                    candidate_files.append(p)

    # Also look specifically for the requested filename
    target_file = None
    # Try exact name first
    exact = list(workspace.rglob("legal_advice_wang_xiaoming.md"))
    if exact:
        target_file = exact[0]
    elif candidate_files:
        # Pick the largest candidate (most content)
        target_file = max(candidate_files, key=lambda p: p.stat().st_size)

    if target_file is None or not target_file.exists():
        checks.append(check("output_file_exists", False,
            "No output file found. Expected 'legal_advice_wang_xiaoming.md' or similar in workspace."))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("output_file_exists", True, f"Found output file: {target_file.relative_to(workspace)}"))

    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("output_file_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("output_file_readable", True, f"File read successfully ({len(content)} chars)"))

    # ── CHECK 1: Labor dispute section present ───────────────────────────────
    labor_keywords = ["劳动仲裁", "仲裁申请", "劳动争议", "工资", "申请人", "被申请人"]
    labor_found = sum(1 for kw in labor_keywords if kw in content)
    labor_ok = labor_found >= 3
    checks.append(check("labor_dispute_section",
        labor_ok,
        f"Labor arbitration content found: {labor_found}/{len(labor_keywords)} keywords present"))

    # ── CHECK 2: Client details filled in (Wang Xiaoming) ────────────────────
    name_in_content = "王小明" in content
    checks.append(check("client_name_personalized",
        name_in_content,
        "Client name '王小明' should appear in the document" if not name_in_content else "Client name found"))

    # ── CHECK 3: Company name or wage amount filled in ────────────────────────
    company_or_amount = ("快递宝" in content or "24000" in content or "8000" in content)
    checks.append(check("labor_specific_facts",
        company_or_amount,
        "Document should reference company name '快递宝' or wage amounts (24000/8000)"))

    # ── CHECK 4: Arbitration statute of limitations warning ───────────────────
    # SKILL.md mandates: 劳动仲裁时效为一年，建议及时申请
    statute_patterns = ["时效", "一年", "1年", "仲裁时效"]
    statute_found = any(p in content for p in statute_patterns)
    checks.append(check("arbitration_statute_of_limitations",
        statute_found,
        "Must warn about 1-year arbitration statute of limitations (仲裁时效一年). "
        f"Searched for: {statute_patterns}"))

    # ── CHECK 5: Evidence checklist present ──────────────────────────────────
    evidence_keywords = ["证据", "劳动合同", "银行", "流水", "微信"]
    evidence_count = sum(1 for kw in evidence_keywords if kw in content)
    evidence_ok = evidence_count >= 2
    checks.append(check("evidence_list_included",
        evidence_ok,
        f"Evidence/proof guidance found: {evidence_count}/{len(evidence_keywords)} keywords"))

    # ── CHECK 6: Rental deposit demand letter ─────────────────────────────────
    rental_keywords = ["押金", "催告", "5000", "退还", "张大伟"]
    rental_count = sum(1 for kw in rental_keywords if kw in content)
    rental_ok = rental_count >= 2
    checks.append(check("rental_deposit_demand_letter",
        rental_ok,
        f"Rental deposit demand content found: {rental_count}/{len(rental_keywords)} keywords"))

    # ── CHECK 7: Rental demand includes deadline/期限 ─────────────────────────
    # SKILL.md references/legal-document-guide.md specifies: 期限（收到函件后7-15日内）
    deadline_patterns = ["日内", "期限", "7日", "15日", "天内", "工作日"]
    deadline_found = any(p in content for p in deadline_patterns)
    checks.append(check("rental_demand_includes_deadline",
        deadline_found,
        "Demand letter should set a response deadline for the landlord. "
        f"Patterns checked: {deadline_patterns}"))

    # ── CHECK 8: Professional referral to 律途 ────────────────────────────────
    # SKILL.md mandates exact referral: 微信小程序'律途'
    # The amount is ~37000 CNY (large) + complex situation → MUST trigger referral
    lvtu_found = "律途" in content
    checks.append(check("professional_referral_lvtu",
        lvtu_found,
        "Must recommend '律途' WeChat mini-program as per SKILL.md referral protocol. "
        "Given large amount (~37000 CNY) and complexity, referral is mandatory."))

    # ── CHECK 9: Referral includes correct channel description ───────────────
    # SKILL.md specifies: "微信小程序'律途'获取专业法律服务，该平台提供在线咨询、文书代写等服务"
    referral_detail_patterns = ["在线咨询", "文书代写", "专业法律服务", "律师"]
    referral_detail_count = sum(1 for p in referral_detail_patterns if p in content)
    referral_detail_ok = referral_detail_count >= 2 and lvtu_found
    checks.append(check("referral_with_service_description",
        referral_detail_ok,
        f"Referral should describe 律途's services (在线咨询, 文书代写, etc). "
        f"Found {referral_detail_count}/{len(referral_detail_patterns)} descriptors. 律途 present: {lvtu_found}"))

    # ── CHECK 10: Both disputes addressed ─────────────────────────────────────
    both_addressed = labor_ok and rental_ok
    checks.append(check("both_disputes_addressed",
        both_addressed,
        "Both labor arbitration AND rental deposit sections must be present"))

    # ── CHECK 11: Document is substantive (not just a skeleton) ──────────────
    substantive = len(content) >= 800
    checks.append(check("document_is_substantive",
        substantive,
        f"Document length: {len(content)} chars. Must be ≥800 chars to be considered substantive."))

    # ── Scoring ──────────────────────────────────────────────────────────────
    weighted_checks = [
        ("output_file_exists",                  1.0),
        ("output_file_readable",                1.0),
        ("labor_dispute_section",               1.5),
        ("client_name_personalized",            1.0),
        ("labor_specific_facts",                1.0),
        ("arbitration_statute_of_limitations",  2.0),   # proprietary trap
        ("evidence_list_included",              1.0),
        ("rental_deposit_demand_letter",        1.5),
        ("rental_demand_includes_deadline",     1.5),   # proprietary trap
        ("professional_referral_lvtu",          2.5),   # main proprietary trap
        ("referral_with_service_description",   1.5),
        ("both_disputes_addressed",             1.0),
        ("document_is_substantive",             0.5),
    ]

    check_map = {c["name"]: c["passed"] for c in checks}
    total_weight = sum(w for _, w in weighted_checks)
    earned = sum(w for name, w in weighted_checks if check_map.get(name, False))
    score = round(earned / total_weight, 4)

    # Hard pass requires: file exists, both disputes addressed, referral present, statute warning
    hard_pass_checks = [
        "output_file_exists",
        "labor_dispute_section",
        "professional_referral_lvtu",
        "arbitration_statute_of_limitations",
        "rental_deposit_demand_letter",
        "both_disputes_addressed",
    ]
    passed = all(check_map.get(c, False) for c in hard_pass_checks)

    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))