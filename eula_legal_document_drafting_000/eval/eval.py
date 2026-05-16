import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str):
    checks = []
    ws = Path(workspace)

    # --- 1. Find eula_draft.md ---
    candidates = list(ws.rglob("eula_draft.md"))
    if not candidates:
        checks.append(check("file_exists", False, "eula_draft.md not found anywhere in workspace"))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    # Take the most recently modified one if multiple
    draft_path = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    checks.append(check("file_exists", True, f"Found at {draft_path.relative_to(ws)}"))

    try:
        content = draft_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("file_readable", True, f"File read successfully ({len(content)} chars)"))
    content_lower = content.lower()

    # --- 2. Parties & Product Identity ---
    has_vendor = "vectorcraft technologies" in content_lower or "vectorcraft technologies, inc" in content_lower
    checks.append(check(
        "identity_licensor",
        has_vendor,
        "Must name 'VectorCraft Technologies, Inc.' as Licensor" if not has_vendor else "Licensor identified"
    ))

    has_product = "vectorcraft pro" in content_lower
    checks.append(check(
        "identity_product",
        has_product,
        "Product name 'VectorCraft Pro' must appear" if not has_product else "Product named"
    ))

    has_copyright = "2025" in content and ("copyright" in content_lower or "©" in content)
    checks.append(check(
        "copyright_notice",
        has_copyright,
        "Must include copyright notice with year 2025" if not has_copyright else "Copyright notice present"
    ))

    # --- 3. License Grant specifics ---
    has_nonexclusive = "non-exclusive" in content_lower or "nonexclusive" in content_lower
    checks.append(check(
        "grant_nonexclusive",
        has_nonexclusive,
        "License grant must be explicitly non-exclusive" if not has_nonexclusive else "Non-exclusive stated"
    ))

    has_nontransferable = "non-transferable" in content_lower or "nontransferable" in content_lower
    checks.append(check(
        "grant_nontransferable",
        has_nontransferable,
        "License must be non-transferable" if not has_nontransferable else "Non-transferable stated"
    ))

    has_perpetual = "perpetual" in content_lower
    checks.append(check(
        "grant_perpetual",
        has_perpetual,
        "Must specify perpetual license duration" if not has_perpetual else "Perpetual duration specified"
    ))

    # Two-device limit from product brief
    two_device = bool(re.search(r'\btwo\b.*\bdevice|\b2\b.*\bdevice|two.*install|2.*install', content_lower))
    checks.append(check(
        "grant_two_devices",
        two_device,
        "Must specify 2-device installation limit from product brief" if not two_device else "2-device limit stated"
    ))

    has_backup = "backup" in content_lower or "archival" in content_lower
    checks.append(check(
        "grant_backup_copy",
        has_backup,
        "Must address backup/archival copy allowance" if not has_backup else "Backup copy addressed"
    ))

    # --- 4. Restrictions ---
    has_reverse = "reverse engineer" in content_lower or "reverse-engineer" in content_lower or "decompil" in content_lower
    checks.append(check(
        "restriction_reverse_engineering",
        has_reverse,
        "Must prohibit reverse engineering/decompilation" if not has_reverse else "Reverse engineering restricted"
    ))

    has_redistrib = "redistribut" in content_lower or "sublicens" in content_lower
    checks.append(check(
        "restriction_redistribution",
        has_redistrib,
        "Must prohibit redistribution/sublicensing" if not has_redistrib else "Redistribution prohibited"
    ))

    has_export = "export" in content_lower
    checks.append(check(
        "restriction_export_control",
        has_export,
        "Must include export control clause" if not has_export else "Export control present"
    ))

    has_notices = "proprietary notice" in content_lower or "copyright notice" in content_lower or "remove" in content_lower
    checks.append(check(
        "restriction_no_remove_notices",
        has_notices,
        "Must prohibit removal of proprietary/copyright notices" if not has_notices else "Notice removal prohibited"
    ))

    # --- 5. Intellectual Property ---
    has_ip_ownership = ("sole and exclusive" in content_lower or "all right" in content_lower) and ("own" in content_lower or "title" in content_lower)
    checks.append(check(
        "ip_licensor_ownership",
        has_ip_ownership,
        "Must state Licensor retains all ownership (sole and exclusive property)" if not has_ip_ownership else "IP ownership stated"
    ))

    # User owns output - this is specific to product brief + skill ip section
    has_user_output = ("output" in content_lower or "export" in content_lower or "user-generated" in content_lower or "files generated" in content_lower or "files created" in content_lower) and ("licensee" in content_lower or "user" in content_lower) and ("own" in content_lower)
    checks.append(check(
        "ip_user_output_ownership",
        has_user_output,
        "Must state Licensee owns their output files (SVG/PNG/PDF exports)" if not has_user_output else "User output ownership addressed"
    ))

    # Open source disclosure
    has_oss = "open source" in content_lower or "open-source" in content_lower or "libpng" in content_lower or "appendix" in content_lower
    checks.append(check(
        "ip_open_source_disclosure",
        has_oss,
        "Must disclose open-source components (libpng, zlib, FreeType)" if not has_oss else "Open source disclosure present"
    ))

    has_feedback = "feedback" in content_lower
    checks.append(check(
        "ip_feedback_clause",
        has_feedback,
        "Must include feedback clause (licensor may use feedback without restriction)" if not has_feedback else "Feedback clause present"
    ))

    has_trademark = "trademark" in content_lower or "trade name" in content_lower or "service mark" in content_lower
    checks.append(check(
        "ip_trademark",
        has_trademark,
        "Must include trademark non-use clause" if not has_trademark else "Trademark clause present"
    ))

    # --- 6. Liability ---
    # AS IS must be conspicuous
    has_as_is = '"as is"' in content_lower or '"as-is"' in content_lower or 'AS IS' in content or 'AS-IS' in content
    checks.append(check(
        "liability_as_is_disclaimer",
        has_as_is,
        'Must include "AS IS" warranty disclaimer (conspicuous)' if not has_as_is else "AS IS disclaimer present"
    ))

    has_consequential = "consequential" in content_lower and ("damage" in content_lower or "liab" in content_lower)
    checks.append(check(
        "liability_consequential_exclusion",
        has_consequential,
        "Must exclude consequential/indirect damages" if not has_consequential else "Consequential damages excluded"
    ))

    # Liability cap: 12 months fees paid — from skill output
    has_cap = ("twelve" in content_lower or "12" in content) and ("month" in content_lower) and ("paid" in content_lower or "fees" in content_lower or "purchas" in content_lower)
    checks.append(check(
        "liability_cap_12_months",
        has_cap,
        "Must include liability cap of 12-month fees paid (from skill's liability section)" if not has_cap else "12-month liability cap present"
    ))

    has_indemnification = "indemnif" in content_lower
    checks.append(check(
        "liability_indemnification",
        has_indemnification,
        "Must include indemnification clause" if not has_indemnification else "Indemnification present"
    ))

    has_savings = ("to the extent permitted" in content_lower or "applicable law" in content_lower)
    checks.append(check(
        "liability_savings_clause",
        has_savings,
        "Must include savings clause for jurisdictions restricting disclaimers" if not has_savings else "Savings clause present"
    ))

    # --- 7. Termination ---
    has_auto_term = "terminates automatically" in content_lower or "automatic" in content_lower and "terminat" in content_lower
    checks.append(check(
        "termination_automatic_on_breach",
        has_auto_term,
        "Must state Agreement terminates automatically on breach" if not has_auto_term else "Automatic termination on breach present"
    ))

    has_term_convenience = "convenience" in content_lower or ("terminate" in content_lower and "destroy" in content_lower and "copies" in content_lower)
    checks.append(check(
        "termination_for_convenience",
        has_term_convenience,
        "Must include termination for convenience by Licensee" if not has_term_convenience else "Termination for convenience present"
    ))

    has_effects = ("cease" in content_lower or "destroy" in content_lower) and ("terminat" in content_lower)
    checks.append(check(
        "termination_effects",
        has_effects,
        "Must describe effects of termination (cease use, destroy copies)" if not has_effects else "Termination effects described"
    ))

    # Survival clause with explicit list — key proprietary trap from skill
    has_survival = "surviv" in content_lower
    checks.append(check(
        "termination_survival_clause",
        has_survival,
        "Must include survival clause listing sections that survive termination" if not has_survival else "Survival clause present"
    ))

    # Check that survival clause mentions specific items from the skill
    survival_items = ["intellectual property", "liability", "indemnif", "governing law"]
    survival_section = ""
    if has_survival:
        # Find the paragraph containing survival
        for para in content.split("\n"):
            if "surviv" in para.lower():
                survival_section += para.lower() + " "
    survival_detail_count = sum(1 for item in survival_items if item in survival_section)
    has_survival_detail = survival_detail_count >= 2
    checks.append(check(
        "termination_survival_explicit_list",
        has_survival_detail,
        f"Survival clause must explicitly list surviving sections (found {survival_detail_count}/4 expected: IP, Liability, Indemnification, Governing Law)" if not has_survival_detail else f"Survival clause lists surviving sections ({survival_detail_count}/4)"
    ))

    # --- 8. Enforceability ---
    has_clickwrap = "click" in content_lower and ("wrap" in content_lower or "agree" in content_lower)
    checks.append(check(
        "enforcement_clickwrap",
        has_clickwrap,
        "Must specify click-wrap as acceptance mechanism" if not has_clickwrap else "Click-wrap specified"
    ))

    # Governing law: Delaware
    has_delaware = "delaware" in content_lower
    checks.append(check(
        "enforcement_governing_law_delaware",
        has_delaware,
        "Must specify Delaware as governing law jurisdiction" if not has_delaware else "Delaware governing law specified"
    ))

    # Arbitration with AAA
    has_arbitration = "arbitrat" in content_lower
    checks.append(check(
        "enforcement_arbitration",
        has_arbitration,
        "Must include binding arbitration clause" if not has_arbitration else "Arbitration clause present"
    ))

    has_aaa = "aaa" in content_lower or "american arbitration" in content_lower
    checks.append(check(
        "enforcement_aaa_rules",
        has_aaa,
        "Must specify AAA arbitration rules (from product brief)" if not has_aaa else "AAA rules specified"
    ))

    has_severability = "severab" in content_lower
    checks.append(check(
        "enforcement_severability",
        has_severability,
        "Must include severability clause" if not has_severability else "Severability clause present"
    ))

    has_entire_agreement = "entire agreement" in content_lower or "integration" in content_lower
    checks.append(check(
        "enforcement_entire_agreement",
        has_entire_agreement,
        "Must include entire agreement/integration clause" if not has_entire_agreement else "Entire agreement clause present"
    ))

    # --- 9. Checklist completeness signal (checklist command used) ---
    # Check that the document has sufficient section coverage (checklist-driven)
    section_headers = [m.group(0) for m in re.finditer(r'^#{1,3}\s+\w', content, re.MULTILINE)]
    has_sections = len(section_headers) >= 5
    checks.append(check(
        "structure_sections",
        has_sections,
        f"Document must have at least 5 clearly named sections (found {len(section_headers)})" if not has_sections else f"Document well-structured ({len(section_headers)} sections)"
    ))

    # --- Compute score ---
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)

    # Must pass at least 80% to be considered passing
    overall_passed = score >= 0.80

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))