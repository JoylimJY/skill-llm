#!/usr/bin/env python3
"""
Evaluation script for the LP Quarterly Briefing PPTX task.
Checks:
1. Output file exists and is a valid PPTX
2. No leftover XXXX_ placeholder text remains
3. Key content from brief is present (fund metrics, company names, etc.)
4. Proper XML conventions: b="1" for headers, no unicode bullets
5. pack.py was used properly (file is valid PPTX, not corrupted)
"""

import sys
import json
import zipfile
import subprocess
from pathlib import Path

def run_checks(workspace: str) -> dict:
    workspace = Path(workspace)
    checks = []
    
    def add_check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── Check 1: Output file exists ──────────────────────────────────────────
    output_candidates = list(workspace.rglob("lp_quarterly_briefing.pptx"))
    if not output_candidates:
        # Also accept any non-template pptx in workspace root
        output_candidates = [
            p for p in workspace.glob("*.pptx")
            if p.name != "lp_briefing_template.pptx"
        ]
    
    if not output_candidates:
        add_check("output_file_exists", False, "No output PPTX file found (expected lp_quarterly_briefing.pptx)")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    output_path = output_candidates[0]
    add_check("output_file_exists", True, f"Found output file: {output_path.name}")

    # ── Check 2: Valid PPTX (zip structure) ───────────────────────────────────
    try:
        with zipfile.ZipFile(output_path, 'r') as zf:
            names = zf.namelist()
            has_presentation = any("ppt/presentation.xml" in n for n in names)
            has_slides = any("ppt/slides/slide" in n for n in names)
        add_check("valid_pptx_structure", has_presentation and has_slides,
                  f"ZIP entries: presentation.xml={has_presentation}, slides={has_slides}")
    except Exception as e:
        add_check("valid_pptx_structure", False, f"PPTX is not a valid ZIP/PPTX: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check 3: Extract text via markitdown ──────────────────────────────────
    extracted_text = ""
    try:
        result = subprocess.run(
            ["python3", "-m", "markitdown", str(output_path)],
            capture_output=True, text=True, timeout=60
        )
        extracted_text = result.stdout.lower()
        add_check("markitdown_extraction", len(extracted_text) > 100,
                  f"Extracted {len(extracted_text)} chars from output")
    except Exception as e:
        add_check("markitdown_extraction", False, f"markitdown failed: {e}")

    # ── Check 4: No leftover XXXX_ placeholders ───────────────────────────────
    import re
    placeholder_pattern = re.compile(r'xxxx_|lorem|ipsum', re.IGNORECASE)
    # Also check slide XML directly
    placeholder_found = False
    placeholder_detail = "No placeholders found"
    try:
        with zipfile.ZipFile(output_path, 'r') as zf:
            slide_files = [n for n in zf.namelist() if re.match(r'ppt/slides/slide\d+\.xml', n)]
            for sf in slide_files:
                content = zf.read(sf).decode('utf-8', errors='replace')
                matches = re.findall(r'XXXX_\w+', content)
                if matches:
                    placeholder_found = True
                    placeholder_detail = f"Found placeholders in {sf}: {matches[:5]}"
                    break
        if not placeholder_found and extracted_text:
            if placeholder_pattern.search(extracted_text):
                placeholder_found = True
                placeholder_detail = "Placeholder text found in markitdown output"
    except Exception as e:
        placeholder_detail = f"Error checking placeholders: {e}"
    
    add_check("no_placeholder_text", not placeholder_found, placeholder_detail)

    # ── Check 5: Fund name present ────────────────────────────────────────────
    fund_name_present = "arcturus ventures" in extracted_text or "arcturus" in extracted_text
    add_check("fund_name_present", fund_name_present,
              "Expected 'Arcturus Ventures' in extracted text")

    # ── Check 6: Fund IRR metric present ──────────────────────────────────────
    irr_present = "27.4" in extracted_text or "27.4%" in extracted_text
    add_check("fund_irr_present", irr_present,
              "Expected fund IRR '27.4%' in extracted text")

    # ── Check 7: TVPI metric present ──────────────────────────────────────────
    tvpi_present = "1.8x" in extracted_text or "1.8" in extracted_text
    add_check("tvpi_present", tvpi_present,
              "Expected TVPI '1.8x' in extracted text")

    # ── Check 8: Portfolio companies present ──────────────────────────────────
    companies = ["novatech", "greenfleet", "medpulse"]
    companies_found = [c for c in companies if c in extracted_text]
    add_check("portfolio_companies_present", len(companies_found) >= 2,
              f"Found companies: {companies_found} (need ≥2 of 3)")

    # ── Check 9: Reporting period present ────────────────────────────────────
    period_present = "q2 2024" in extracted_text or "q2" in extracted_text
    add_check("reporting_period_present", period_present,
              "Expected 'Q2 2024' in extracted text")

    # ── Check 10: Key risk content present ───────────────────────────────────
    risk_present = (
        "interest rate" in extracted_text or
        "greenfleet" in extracted_text or
        "supply chain" in extracted_text or
        "regulatory" in extracted_text
    )
    add_check("key_risks_present", risk_present,
              "Expected at least one key risk in extracted text")

    # ── Check 11: Capital deployment data present ─────────────────────────────
    capital_present = (
        "280" in extracted_text or
        "231" in extracted_text or
        "committed" in extracted_text or
        "deployed" in extracted_text
    )
    add_check("capital_data_present", capital_present,
              "Expected capital deployment data (committed/deployed) in extracted text")

    # ── Check 12: No unicode bullets in XML ──────────────────────────────────
    unicode_bullet_found = False
    unicode_detail = "No unicode bullet characters (•) found in slide XML"
    try:
        with zipfile.ZipFile(output_path, 'r') as zf:
            slide_files = [n for n in zf.namelist() if re.match(r'ppt/slides/slide\d+\.xml', n)]
            for sf in slide_files:
                content = zf.read(sf).decode('utf-8', errors='replace')
                if '&#x2022;' in content or '\u2022' in content or '•' in content:
                    unicode_bullet_found = True
                    unicode_detail = f"Unicode bullet found in {sf}"
                    break
    except Exception as e:
        unicode_detail = f"Error checking bullets: {e}"
    
    add_check("no_unicode_bullets", not unicode_bullet_found, unicode_detail)

    # ── Check 13: Bold headers present (b="1" in XML) ─────────────────────────
    bold_found = False
    try:
        with zipfile.ZipFile(output_path, 'r') as zf:
            slide_files = [n for n in zf.namelist() if re.match(r'ppt/slides/slide\d+\.xml', n)]
            for sf in slide_files:
                content = zf.read(sf).decode('utf-8', errors='replace')
                if 'b="1"' in content or "b='1'" in content:
                    bold_found = True
                    break
    except Exception as e:
        pass
    add_check("bold_headers_present", bold_found,
              "Expected bold headers using b=\"1\" in XML (per editing.md rules)")

    # ── Check 14: No accent lines under titles (forbidden per SKILL.md) ───────
    # Check for thin horizontal lines immediately below title area (y ~ 0.5-0.9")
    # We look for LINE shapes in the first slide's XML near title positions
    # This is a heuristic: check if presentation.xml has slide ordering
    try:
        with zipfile.ZipFile(output_path, 'r') as zf:
            pres_xml = zf.read("ppt/presentation.xml").decode('utf-8', errors='replace')
        sldId_count = len(re.findall(r'<p:sldId\b', pres_xml))
        add_check("slide_count_valid", sldId_count >= 4,
                  f"Presentation has {sldId_count} slides (expected ≥4 to replace all content slides)")
    except Exception as e:
        add_check("slide_count_valid", False, f"Could not read presentation.xml: {e}")

    # ── Check 15: Milestones present ─────────────────────────────────────────
    milestone_present = (
        "novatech" in extracted_text and (
            "series c" in extracted_text or
            "q3" in extracted_text or
            "clearroute" in extracted_text or
            "milestone" in extracted_text or
            "q4 2024" in extracted_text
        )
    )
    add_check("milestones_present", milestone_present,
              "Expected upcoming milestones content (NovaTech Series C, GreenFleet, etc.)")

    # ── Scoring ───────────────────────────────────────────────────────────────
    mandatory_checks = [
        "output_file_exists",
        "valid_pptx_structure", 
        "no_placeholder_text",
        "fund_name_present",
        "fund_irr_present",
        "portfolio_companies_present",
    ]
    
    mandatory_passed = all(
        c["passed"] for c in checks if c["name"] in mandatory_checks
    )
    
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total if total > 0 else 0.0

    overall_passed = mandatory_passed and score >= 0.70

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)