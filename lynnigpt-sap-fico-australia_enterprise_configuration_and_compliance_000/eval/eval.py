import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    
    # --- Find the output file ---
    target_filename = "aus_sap_implementation_guide.md"
    found_files = list(Path(workspace_dir).rglob(target_filename))
    
    if not found_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": f"Could not find '{target_filename}' anywhere in workspace."}]
        }
    
    target_file = found_files[0]
    checks.append({"name": "file_exists", "passed": True, "detail": str(target_file)})
    
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_readable", "passed": False, "detail": str(e)}]
        }
    
    checks.append({"name": "file_readable", "passed": True, "detail": f"File size: {len(content)} chars"})
    
    content_lower = content.lower()
    
    # =========================================================
    # CHECK GROUP 1: MANDATORY 8-SECTION RESPONSE FORMAT
    # From SKILL.md: T-code, Tables, Configuration, Steps,
    # OSS Notes, Integrations, S/4HANA, Australian Compliance
    # =========================================================
    
    # T-code section
    tcode_present = bool(re.search(r't[-\s]?code|transaction\s+code', content_lower))
    checks.append({
        "name": "section_tcode",
        "passed": tcode_present,
        "detail": "Response must include a T-code / Transaction Code section per SKILL.md format."
    })
    
    # Tables section
    tables_present = bool(re.search(r'\btables?\b', content_lower))
    checks.append({
        "name": "section_tables",
        "passed": tables_present,
        "detail": "Response must include a Tables section listing relevant SAP tables."
    })
    
    # Configuration section
    config_present = bool(re.search(r'\bconfigur', content_lower))
    checks.append({
        "name": "section_configuration",
        "passed": config_present,
        "detail": "Response must include a Configuration section."
    })
    
    # Steps section
    steps_present = bool(re.search(r'\bsteps?\b', content_lower))
    checks.append({
        "name": "section_steps",
        "passed": steps_present,
        "detail": "Response must include a Steps (numbered implementation steps) section."
    })
    
    # OSS Notes section
    oss_present = bool(re.search(r'oss\s*note|sap\s*note|support\s*note', content_lower))
    checks.append({
        "name": "section_oss_notes",
        "passed": oss_present,
        "detail": "Response must include an OSS Notes / SAP Notes section — a key discriminator from the SKILL.md format."
    })
    
    # Integrations section
    integrations_present = bool(re.search(r'\bintegration', content_lower))
    checks.append({
        "name": "section_integrations",
        "passed": integrations_present,
        "detail": "Response must include an Integrations section (cross-module impacts)."
    })
    
    # S/4HANA section
    s4hana_present = bool(re.search(r's/4hana|s4hana|s4\s*hana', content_lower))
    checks.append({
        "name": "section_s4hana",
        "passed": s4hana_present,
        "detail": "Response must include S/4HANA version-specific considerations."
    })
    
    # Australian Compliance section
    aus_compliance_present = bool(re.search(r'australian\s+compliance|compliance.*australia|aus.*compliance', content_lower))
    checks.append({
        "name": "section_australian_compliance",
        "passed": aus_compliance_present,
        "detail": "Response must include an Australian Compliance section."
    })
    
    # =========================================================
    # CHECK GROUP 2: CORRECT AUSTRALIAN TAX RATES (PROPRIETARY TRAP)
    # Must not use the wrong rates from the distractor files
    # GST = 10%, PAYG no-ABN = 47%, Super = 11%
    # =========================================================
    
    # GST rate must be 10% (not 12.5% from distractor)
    gst_10_present = bool(re.search(r'gst.*10\s*%|10\s*%.*gst|10\s+per\s+cent.*gst|gst.*10\s+per\s+cent', content_lower))
    gst_wrong_rate = bool(re.search(r'12\.5\s*%|12\.5\s+per\s+cent', content_lower))
    gst_correct = gst_10_present and not gst_wrong_rate
    checks.append({
        "name": "gst_rate_correct_10pct",
        "passed": gst_correct,
        "detail": f"GST must be 10% (not 12.5% from distractor). Found 10%: {gst_10_present}, Found wrong 12.5%: {gst_wrong_rate}."
    })
    
    # PAYG no-ABN rate must be 47% (not 46.5% from distractor)
    payg_47_present = bool(re.search(r'47\s*%|47\s+per\s+cent', content_lower))
    payg_wrong = bool(re.search(r'46\.5\s*%|46\.5\s+per\s+cent', content_lower))
    payg_correct = payg_47_present and not payg_wrong
    checks.append({
        "name": "payg_no_abn_rate_47pct",
        "passed": payg_correct,
        "detail": f"PAYG withholding (no ABN) must be 47% (not 46.5% from distractor). Found 47%: {payg_47_present}, Found wrong 46.5%: {payg_wrong}."
    })
    
    # Superannuation must be 11% (not 9.5% from distractor)
    super_11_present = bool(re.search(r'11\s*%.*super|super.*11\s*%|11\s+per\s+cent.*super|super.*11\s+per\s+cent', content_lower))
    super_wrong = bool(re.search(r'9\.5\s*%.*super|super.*9\.5\s*%', content_lower))
    super_correct = super_11_present and not super_wrong
    checks.append({
        "name": "superannuation_rate_11pct",
        "passed": super_correct,
        "detail": f"Superannuation must be 11% employer contribution (not 9.5% from distractor). Found 11%: {super_11_present}, Found wrong 9.5%: {super_wrong}."
    })
    
    # =========================================================
    # CHECK GROUP 3: CORRECT BSB NUMBER PATTERNS (PROPRIETARY TRAP)
    # CBA=06xxxx, NAB=08xxxx, ANZ=01xxxx, Westpac=03xxxx
    # Distractor file has all wrong (05, 07, 02, 04)
    # =========================================================
    
    # CBA BSB must be 06xxxx
    cba_correct_bsb = bool(re.search(r'cba.*06|commonwealth.*06|06.*cba|06.*commonwealth', content_lower))
    cba_wrong_bsb = bool(re.search(r'cba.*05|commonwealth.*05|05.*cba|05.*commonwealth', content_lower))
    cba_bsb_ok = cba_correct_bsb and not cba_wrong_bsb
    checks.append({
        "name": "cba_bsb_06xxxx",
        "passed": cba_bsb_ok,
        "detail": f"Commonwealth Bank (CBA) BSB prefix must be 06xxxx (not 05xxxx from distractor). Correct found: {cba_correct_bsb}, Wrong found: {cba_wrong_bsb}."
    })
    
    # NAB BSB must be 08xxxx
    nab_correct_bsb = bool(re.search(r'nab.*08|national.*australia.*08|08.*nab|08.*national', content_lower))
    nab_wrong_bsb = bool(re.search(r'nab.*07|national.*australia.*07|07.*nab', content_lower))
    nab_bsb_ok = nab_correct_bsb and not nab_wrong_bsb
    checks.append({
        "name": "nab_bsb_08xxxx",
        "passed": nab_bsb_ok,
        "detail": f"NAB BSB prefix must be 08xxxx (not 07xxxx from distractor). Correct found: {nab_correct_bsb}, Wrong found: {nab_wrong_bsb}."
    })
    
    # =========================================================
    # CHECK GROUP 4: KEY AUSTRALIAN SAP CONCEPTS
    # =========================================================
    
    # GST-Free scenario must be mentioned
    gst_free = bool(re.search(r'gst.?free|gst\s+free', content_lower))
    checks.append({
        "name": "gst_free_scenario",
        "passed": gst_free,
        "detail": "Must cover GST-Free tax code scenario (as per company requirement for raw materials)."
    })
    
    # Input Taxed scenario
    input_taxed = bool(re.search(r'input.?taxed|input\s+tax', content_lower))
    checks.append({
        "name": "input_taxed_scenario",
        "passed": input_taxed,
        "detail": "Must cover Input Taxed scenario (as per company requirement for financial services income)."
    })
    
    # RCTI must be mentioned (Australian-specific concept)
    rcti_present = bool(re.search(r'rcti|reverse\s+charge\s+tax\s+invoice', content_lower))
    checks.append({
        "name": "rcti_reverse_charge_tax_invoice",
        "passed": rcti_present,
        "detail": "RCTI (Reverse Charge Tax Invoice) is an Australian-specific requirement that must be addressed."
    })
    
    # BAS Reporting
    bas_present = bool(re.search(r'\bbas\b|business\s+activity\s+statement', content_lower))
    checks.append({
        "name": "bas_reporting",
        "passed": bas_present,
        "detail": "BAS (Business Activity Statement) compliance must be mentioned."
    })
    
    # F110 payment program
    f110_present = bool(re.search(r'\bf110\b', content_lower))
    checks.append({
        "name": "f110_payment_program",
        "passed": f110_present,
        "detail": "F110 automatic payment program T-code must be referenced for vendor payment setup."
    })
    
    # BPAY integration
    bpay_present = bool(re.search(r'\bbpay\b|b-pay|bill\s+pay', content_lower))
    checks.append({
        "name": "bpay_integration",
        "passed": bpay_present,
        "detail": "BPAY (Bill Payment System) must be mentioned for utility bill payments."
    })
    
    # EFT payments
    eft_present = bool(re.search(r'\beft\b|electronic\s+funds?\s+transfer', content_lower))
    checks.append({
        "name": "eft_electronic_payments",
        "passed": eft_present,
        "detail": "EFT (Electronic Funds Transfer) must be mentioned for electronic payment setup."
    })
    
    # ABN validation
    abn_present = bool(re.search(r'\babn\b|australian\s+business\s+number', content_lower))
    checks.append({
        "name": "abn_validation",
        "passed": abn_present,
        "detail": "ABN (Australian Business Number) must be referenced in contractor/withholding context."
    })
    
    # PAYG withholding
    payg_present = bool(re.search(r'\bpayg\b|pay\s+as\s+you\s+go', content_lower))
    checks.append({
        "name": "payg_withholding",
        "passed": payg_present,
        "detail": "PAYG Withholding must be covered for contractor payments."
    })
    
    # ATO compliance body mentioned
    ato_present = bool(re.search(r'\bato\b|australian\s+taxation\s+office', content_lower))
    checks.append({
        "name": "ato_compliance_body",
        "passed": ato_present,
        "detail": "ATO (Australian Taxation Office) must be referenced as compliance body."
    })
    
    # Universal Journal / ACDOCA for S/4HANA
    acdoca_present = bool(re.search(r'acdoca|universal\s+journal', content_lower))
    checks.append({
        "name": "s4hana_universal_journal_acdoca",
        "passed": acdoca_present,
        "detail": "S/4HANA Universal Journal (ACDOCA table) must be mentioned for S/4HANA 2023 target."
    })
    
    # =========================================================
    # SCORING
    # =========================================================
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    
    # Weight critical checks more heavily
    critical_checks = [
        "file_exists", "file_readable",
        "gst_rate_correct_10pct", "payg_no_abn_rate_47pct",
        "superannuation_rate_11pct", "cba_bsb_06xxxx",
        "section_oss_notes", "section_australian_compliance",
        "rcti_reverse_charge_tax_invoice", "f110_payment_program"
    ]
    critical_passed = sum(1 for c in checks if c["name"] in critical_checks and c["passed"])
    critical_total = len(critical_checks)
    
    # Score: 60% weight on critical checks, 40% on all checks
    score = 0.6 * (critical_passed / critical_total) + 0.4 * (passed_checks / total_checks)
    score = round(score, 4)
    
    # Must pass ALL critical checks to pass overall
    all_critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    # AND at least 75% of all checks
    threshold_passed = (passed_checks / total_checks) >= 0.75
    
    overall_passed = all_critical_passed and threshold_passed
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))