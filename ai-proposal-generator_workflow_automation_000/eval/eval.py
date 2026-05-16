import sys
import json
import re
from pathlib import Path
from datetime import date

workspace = Path(sys.argv[1])
checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ─── CHECK 1: Custom template file exists in proposals/templates/custom/ ──────
try:
    custom_dir = workspace / "proposals" / "templates" / "custom"
    custom_templates = list(custom_dir.glob("*.md"))
    if custom_templates:
        template_file = custom_templates[0]
        template_content = template_file.read_text()
        checks.append(make_check(
            "custom_template_file_exists",
            True,
            f"Found custom template: {template_file.name}"
        ))
    else:
        checks.append(make_check(
            "custom_template_file_exists",
            False,
            "No .md file found in proposals/templates/custom/"
        ))
        template_content = ""
        template_file = None
except Exception as e:
    checks.append(make_check("custom_template_file_exists", False, str(e)))
    template_content = ""
    template_file = None

# ─── CHECK 2: Wizard output format — ASCII border ━━━ present ─────────────────
try:
    has_border = "━" in template_content
    checks.append(make_check(
        "wizard_output_ascii_border",
        has_border,
        "Template contains ━━━ wizard output border" if has_border
        else "Missing ━━━ ASCII border from wizard output format"
    ))
except Exception as e:
    checks.append(make_check("wizard_output_ascii_border", False, str(e)))

# ─── CHECK 3: Wizard output has required fields (Name, Style, Theme, Sections, Saved) ──
try:
    required_fields = ["Name:", "Style:", "Theme:", "Sections:", "Saved:"]
    missing = [f for f in required_fields if f not in template_content]
    passed = len(missing) == 0
    checks.append(make_check(
        "wizard_output_required_fields",
        passed,
        f"All wizard fields present" if passed
        else f"Missing wizard fields: {missing}"
    ))
except Exception as e:
    checks.append(make_check("wizard_output_required_fields", False, str(e)))

# ─── CHECK 4: Wizard output specifies consultant style ─────────────────────────
try:
    has_consultant_style = bool(re.search(r'[Ss]tyle.*[Cc]onsultant|[Cc]onsultant.*[Ss]tyle', template_content))
    checks.append(make_check(
        "wizard_output_consultant_style",
        has_consultant_style,
        "Wizard output references 'consultant' style" if has_consultant_style
        else "Wizard output does not reference 'consultant' style"
    ))
except Exception as e:
    checks.append(make_check("wizard_output_consultant_style", False, str(e)))

# ─── CHECK 5: Wizard output specifies ocean-blue / Ocean Blue theme ─────────────
try:
    has_ocean = bool(re.search(r'[Oo]cean[\s-][Bb]lue|ocean.blue', template_content, re.IGNORECASE))
    checks.append(make_check(
        "wizard_output_ocean_blue_theme",
        has_ocean,
        "Wizard output references 'Ocean Blue' theme" if has_ocean
        else "Wizard output does not reference 'Ocean Blue' theme"
    ))
except Exception as e:
    checks.append(make_check("wizard_output_ocean_blue_theme", False, str(e)))

# ─── CHECK 6: Draft .md file for BrightWave exists in proposals/generated/ ────
try:
    gen_dir = workspace / "proposals" / "generated"
    draft_files = list(gen_dir.glob("*brightwave*.md")) + list(gen_dir.glob("*BrightWave*.md")) + list(gen_dir.glob("*bright*wave*.md"))
    # also try any md
    all_mds = list(gen_dir.glob("*.md"))
    # filter for brightwave
    bw_drafts = [f for f in all_mds if "bright" in f.name.lower()]
    if bw_drafts:
        draft_file = bw_drafts[0]
        draft_content = draft_file.read_text()
        checks.append(make_check(
            "draft_md_exists",
            True,
            f"Found draft: {draft_file.name}"
        ))
    else:
        checks.append(make_check(
            "draft_md_exists",
            False,
            f"No BrightWave draft .md found in proposals/generated/. Files there: {[f.name for f in all_mds]}"
        ))
        draft_content = ""
        draft_file = None
except Exception as e:
    checks.append(make_check("draft_md_exists", False, str(e)))
    draft_content = ""
    draft_file = None

# ─── CHECK 7: Draft file naming convention YYYY-MM-DD_brightwave-solutions.md ─
try:
    if draft_file:
        name = draft_file.name
        # Must match YYYY-MM-DD_<something>brightwave<something>.md
        pattern = r'^\d{4}-\d{2}-\d{2}_.*bright.*\.md$'
        naming_ok = bool(re.match(pattern, name, re.IGNORECASE))
        checks.append(make_check(
            "draft_file_naming_convention",
            naming_ok,
            f"Draft filename '{name}' matches YYYY-MM-DD_client-name.md convention" if naming_ok
            else f"Draft filename '{name}' does NOT match YYYY-MM-DD_client-name.md convention"
        ))
    else:
        checks.append(make_check("draft_file_naming_convention", False, "No draft file to check"))
except Exception as e:
    checks.append(make_check("draft_file_naming_convention", False, str(e)))

# ─── CHECK 8: Draft contains consultant-style sections ────────────────────────
try:
    consultant_sections = [
        "situation analysis",
        "key challenges",
        "recommendations",
        "engagement options",
        "expected outcomes",
        "credentials",
        "investment",
        "next steps",
    ]
    if draft_content:
        content_lower = draft_content.lower()
        found = [s for s in consultant_sections if s in content_lower]
        # Require at least 5 of 8 sections
        passed = len(found) >= 5
        checks.append(make_check(
            "draft_contains_consultant_sections",
            passed,
            f"Found {len(found)}/8 consultant sections: {found}"
        ))
    else:
        checks.append(make_check("draft_contains_consultant_sections", False, "No draft content to check"))
except Exception as e:
    checks.append(make_check("draft_contains_consultant_sections", False, str(e)))

# ─── CHECK 9: Draft references BrightWave and pricing from SERVICES.md ────────
try:
    if draft_content:
        has_client = bool(re.search(r'brightwave', draft_content, re.IGNORECASE))
        # Growth package pricing $6,500/month matches budget range from notes
        has_pricing = bool(re.search(r'\$6[,.]?500|\$6500|Growth', draft_content, re.IGNORECASE))
        passed = has_client and has_pricing
        checks.append(make_check(
            "draft_references_client_and_pricing",
            passed,
            f"Client ref: {has_client}, Pricing ref (Growth $6,500): {has_pricing}"
        ))
    else:
        checks.append(make_check("draft_references_client_and_pricing", False, "No draft content"))
except Exception as e:
    checks.append(make_check("draft_references_client_and_pricing", False, str(e)))

# ─── CHECK 10: Final HTML file exists for BrightWave ─────────────────────────
try:
    gen_dir = workspace / "proposals" / "generated"
    all_htmls = list(gen_dir.glob("*.html"))
    bw_htmls = [f for f in all_htmls if "bright" in f.name.lower()]
    if bw_htmls:
        html_file = bw_htmls[0]
        html_content = html_file.read_text()
        checks.append(make_check(
            "final_html_exists",
            True,
            f"Found HTML: {html_file.name}"
        ))
    else:
        checks.append(make_check(
            "final_html_exists",
            False,
            f"No BrightWave .html found in proposals/generated/. Files: {[f.name for f in all_htmls]}"
        ))
        html_content = ""
        html_file = None
except Exception as e:
    checks.append(make_check("final_html_exists", False, str(e)))
    html_content = ""
    html_file = None

# ─── CHECK 11: HTML file naming convention YYYY-MM-DD_brightwave*.html ────────
try:
    if html_file:
        name = html_file.name
        pattern = r'^\d{4}-\d{2}-\d{2}_.*bright.*\.html$'
        naming_ok = bool(re.match(pattern, name, re.IGNORECASE))
        checks.append(make_check(
            "html_file_naming_convention",
            naming_ok,
            f"HTML filename '{name}' matches convention" if naming_ok
            else f"HTML filename '{name}' does NOT match YYYY-MM-DD_client-name.html convention"
        ))
    else:
        checks.append(make_check("html_file_naming_convention", False, "No HTML file found"))
except Exception as e:
    checks.append(make_check("html_file_naming_convention", False, str(e)))

# ─── CHECK 12: HTML uses proposal-consultant style class ─────────────────────
try:
    if html_content:
        has_class = "proposal-consultant" in html_content
        checks.append(make_check(
            "html_proposal_consultant_class",
            has_class,
            "HTML contains 'proposal-consultant' style class" if has_class
            else "HTML missing 'proposal-consultant' style class"
        ))
    else:
        checks.append(make_check("html_proposal_consultant_class", False, "No HTML content"))
except Exception as e:
    checks.append(make_check("html_proposal_consultant_class", False, str(e)))

# ─── CHECK 13: HTML contains Ocean Blue primary color #0ea5e9 ─────────────────
try:
    if html_content:
        has_color = "#0ea5e9" in html_content or "0ea5e9" in html_content.lower()
        checks.append(make_check(
            "html_ocean_blue_theme_color",
            has_color,
            "HTML contains Ocean Blue primary color #0ea5e9" if has_color
            else "HTML missing Ocean Blue primary color #0ea5e9"
        ))
    else:
        checks.append(make_check("html_ocean_blue_theme_color", False, "No HTML content"))
except Exception as e:
    checks.append(make_check("html_ocean_blue_theme_color", False, str(e)))

# ─── CHECK 14: HTML is valid (has DOCTYPE, html, head, body tags) ─────────────
try:
    if html_content:
        has_doctype = "<!DOCTYPE" in html_content or "<!doctype" in html_content
        has_html = "<html" in html_content
        has_head = "<head" in html_content
        has_body = "<body" in html_content
        passed = all([has_doctype, has_html, has_head, has_body])
        checks.append(make_check(
            "html_valid_structure",
            passed,
            f"DOCTYPE:{has_doctype} html:{has_html} head:{has_head} body:{has_body}"
        ))
    else:
        checks.append(make_check("html_valid_structure", False, "No HTML content"))
except Exception as e:
    checks.append(make_check("html_valid_structure", False, str(e)))

# ─── CHECK 15: HTML contains BrightWave client name ─────────────────────────
try:
    if html_content:
        has_client = bool(re.search(r'brightwave', html_content, re.IGNORECASE))
        checks.append(make_check(
            "html_references_client",
            has_client,
            "HTML references BrightWave client" if has_client
            else "HTML does not reference BrightWave"
        ))
    else:
        checks.append(make_check("html_references_client", False, "No HTML content"))
except Exception as e:
    checks.append(make_check("html_references_client", False, str(e)))

# ─── CHECK 16: HTML has responsive viewport meta tag ─────────────────────────
try:
    if html_content:
        has_viewport = "viewport" in html_content and "width=device-width" in html_content
        checks.append(make_check(
            "html_mobile_responsive",
            has_viewport,
            "HTML has responsive viewport meta tag" if has_viewport
            else "HTML missing responsive viewport meta tag"
        ))
    else:
        checks.append(make_check("html_mobile_responsive", False, "No HTML content"))
except Exception as e:
    checks.append(make_check("html_mobile_responsive", False, str(e)))

# ─── Scoring ─────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall_passed = score >= 0.75  # Need at least 75% to pass

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))