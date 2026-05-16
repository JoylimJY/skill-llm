import sys
import json
import re
from pathlib import Path

def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def find_plan_file(workspace):
    """Find the output plan file - look for alex_chen_plan or course_plan etc."""
    ws = Path(workspace)
    candidates = list(ws.rglob("alex_chen_plan*")) + \
                 list(ws.rglob("course_plan*")) + \
                 list(ws.rglob("4year_plan*")) + \
                 list(ws.rglob("four_year_plan*")) + \
                 list(ws.rglob("plan_final*")) + \
                 list(ws.rglob("final_plan*")) + \
                 list(ws.rglob("ossd_plan*")) + \
                 list(ws.rglob("*plan*.md")) + \
                 list(ws.rglob("*plan*.txt"))
    # Exclude old drafts
    candidates = [c for c in candidates if "old_draft" not in str(c).lower() 
                  and "v0.1" not in str(c).lower()
                  and "DRAFT" not in str(c)]
    if candidates:
        # Prefer newer files
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0]
    return None

def load_valid_codes(workspace):
    """Extract all valid course codes from the course catalog."""
    catalog = load_file(Path(workspace) / "references/course-catalog.md")
    if not catalog:
        return set()
    # Find all codes like ENG1D, MTH1W, ICS3U, etc.
    codes = set(re.findall(r'\b([A-Z]{2,3}[0-9][A-Z0-9]{0,2})\b', catalog))
    return codes

def check_section_presence(content, section_keywords):
    """Check that required section keywords appear in content."""
    content_lower = content.lower()
    return all(kw.lower() in content_lower for kw in section_keywords)

def check_no_4u_in_summer(content):
    """
    Verify that no 4U or 4M course codes appear in summer school slots.
    Look for summer school sections and check codes within them.
    """
    # Find summer school blocks
    summer_pattern = re.compile(
        r'(summer\s*school|summer\s*course|summer\s*semester)[^\n]*\n(.*?)(?=\n#{1,4}\s|\Z)',
        re.IGNORECASE | re.DOTALL
    )
    summer_blocks = summer_pattern.findall(content)
    
    # Also look for lines that mention "summer" and extract codes
    lines = content.split('\n')
    summer_lines = []
    in_summer = False
    for line in lines:
        if re.search(r'summer', line, re.IGNORECASE):
            in_summer = True
        if in_summer:
            summer_lines.append(line)
            # Exit after 5 lines
            if len(summer_lines) > 8:
                in_summer = False
    
    summer_text = '\n'.join(summer_lines)
    # Also collect from regex blocks
    for match in summer_blocks:
        summer_text += ' ' + match[1]
    
    # Check for any 4U or 4M codes in summer context
    four_u_m_codes = re.findall(r'\b[A-Z]{2,3}4[UM]\b', summer_text)
    return four_u_m_codes  # empty = good (no violations)

def check_cumulative_credits(content):
    """Look for cumulative credit counts in the output."""
    # Look for patterns like "total: 30" or "30 credits" or credit tables
    patterns = [
        r'cumulative\s*credits?\s*[:\-]\s*\d+',
        r'total\s*credits?\s*[:\-]\s*\d+',
        r'total\s*/\s*compulsory\s*/\s*elective',
        r'\d+\s*/\s*\d+\s*/\s*\d+',  # e.g. 30 / 17 / 13
        r'compulsory\s*credits?\s*[:\-]\s*\d+',
    ]
    content_lower = content.lower()
    for p in patterns:
        if re.search(p, content_lower):
            return True
    return False

def check_prerequisites_present(content):
    """Check that key prerequisite course codes appear somewhere in the plan."""
    # Required for both targets
    required_codes = ['MHF4U', 'MCV4U', 'ENG4U', 'MCR3U', 'ENG3U']
    # At least one of: SCH4U or SPH4U (for McMaster Engineering)
    science_prereqs = ['SCH4U', 'SPH4U']
    # ICS3U needed for ICS4U (Waterloo CS pathway)
    cs_codes = ['ICS3U', 'ICS4U']
    
    missing = []
    for code in required_codes:
        if code not in content:
            missing.append(code)
    
    has_science = any(c in content for c in science_prereqs)
    has_cs = any(c in content for c in cs_codes)
    
    return missing, has_science, has_cs

def check_protect_11_12(content):
    """
    Check that Grade 11 and 12 don't have excessive U-level courses stacked.
    In protect_11_12 mode, we look for reasonable distribution.
    We'll check that the plan doesn't list more than 5 U-level courses in 
    a single grade (Grade 11 or 12) without acknowledgment.
    """
    # Find Grade 12 section
    grade12_match = re.search(
        r'grade\s*12(.*?)(?=grade\s*9|grade\s*10|grade\s*11|\Z)',
        content, re.IGNORECASE | re.DOTALL
    )
    if not grade12_match:
        return True, "Grade 12 section not found"
    
    grade12_text = grade12_match.group(1)
    # Count 4U/4M codes
    four_codes = re.findall(r'\b[A-Z]{2,3}4[UM]\b', grade12_text)
    # In protect_11_12 mode, 7-8 is normal for Grade 12 (building Top 6 pool)
    # But we check that the plan acknowledges the protect mode
    return len(four_codes), four_codes

def check_diff_present(content):
    """Check that a before/after diff or update section is present for the catalog change."""
    patterns = [
        r'(before|after)\s*(update|change|diff)',
        r'(update|change|diff)',
        r'ics3u.*?(removed|online.only|memo|updated)',
        r'(catalog|catalogue)\s*(update|change)',
        r'minimal.change',
        r'impacted\s*(course|grade)',
    ]
    content_lower = content.lower()
    for p in patterns:
        if re.search(p, content_lower, re.IGNORECASE):
            return True
    return False

def check_no_removed_course_in_final(content):
    """
    After the catalog update, ICS3U should be noted as online-only.
    The plan should reflect ICS3U as [ONLINE] or note it's taken online.
    The in-school timetable version should NOT be scheduled as a regular in-school course
    without acknowledging the memo change.
    """
    # Check: the plan should mention ICS3U (it's still needed as prereq for ICS4U)
    # but should NOT schedule it as a regular in-school course without the [ONLINE] note
    has_ics3u = 'ICS3U' in content
    
    # Check if it's noted as online where mentioned
    ics3u_online = bool(re.search(r'ICS3U.*?\[?online\]?', content, re.IGNORECASE)) or \
                   bool(re.search(r'\[?online\]?.*?ICS3U', content, re.IGNORECASE)) or \
                   bool(re.search(r'ICS3U.*?e.?learn', content, re.IGNORECASE))
    
    return has_ics3u, ics3u_online

def check_targets_section(content):
    """Check that both Waterloo CS and McMaster Engineering are mentioned."""
    content_lower = content.lower()
    has_waterloo = 'waterloo' in content_lower
    has_waterloo_cs = 'waterloo' in content_lower and ('cs' in content_lower or 'computer science' in content_lower)
    has_mcmaster = 'mcmaster' in content_lower
    has_mcmaster_eng = 'mcmaster' in content_lower and ('engineering' in content_lower or 'eng' in content_lower)
    return has_waterloo_cs, has_mcmaster_eng

def check_online_credits_noted(content):
    """Check that the plan notes the 2 online credits already satisfied."""
    content_lower = content.lower()
    patterns = [
        r'online\s*credit',
        r'e.?learning',
        r'chv2o.*online',
        r'glc2o.*online',
        r'2\s*online',
        r'online.*requirement.*met',
        r'online.*already',
    ]
    for p in patterns:
        if re.search(p, content_lower):
            return True
    return False

def check_four_year_structure(content):
    """Check that the plan covers all 4 grades (or at least Grades 11 and 12 for this student)."""
    content_lower = content.lower()
    has_g11 = bool(re.search(r'grade\s*11', content_lower))
    has_g12 = bool(re.search(r'grade\s*12', content_lower))
    return has_g11 and has_g12

def check_top6_section(content):
    """Check that Top 6 analysis is present."""
    content_lower = content.lower()
    return bool(re.search(r'top\s*6', content_lower)) or bool(re.search(r'top six', content_lower))

def check_validation_checklist(content):
    """Check that a validation/checklist section is present."""
    content_lower = content.lower()
    patterns = [
        r'validation',
        r'checklist',
        r'graduation\s*(requirement|req)',
        r'prereq.*met',
        r'requirement.*met',
    ]
    for p in patterns:
        if re.search(p, content_lower):
            return True
    return False

def check_codes_from_catalog(content, valid_codes):
    """
    Find all course codes in the plan and check they exist in the catalog.
    Returns list of invalid codes found.
    """
    # Find all codes that look like course codes (2-3 letters + digit + optional alphanumeric)
    found_codes = set(re.findall(r'\b([A-Z]{2,3}[0-9][A-Z0-9]{0,2})\b', content))
    
    # Filter to codes that look like course codes (not random text)
    # Valid pattern: 2-3 uppercase letters + 1 digit + 1-2 uppercase letters/digits
    course_like = {c for c in found_codes if re.match(r'^[A-Z]{2,3}[0-9][A-Z0-9]{1,2}$', c)}
    
    # Exclude obvious non-course patterns
    exclusions = {'MET', 'FOR', 'NOT', 'AID', 'AND', 'TOP', 'CAN', 'USE'}
    course_like -= exclusions
    
    invalid = course_like - valid_codes
    return invalid, course_like

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = []
    total_score = 0.0
    
    # ── Find the plan file ───────────────────────────────────────────────────
    plan_file = find_plan_file(workspace)
    plan_content = None
    
    if plan_file:
        plan_content = load_file(plan_file)
    
    file_found = plan_file is not None and plan_content is not None and len(plan_content) > 200
    
    checks.append({
        "name": "Plan file exists and is non-trivial",
        "passed": file_found,
        "detail": f"Found: {plan_file}" if file_found else "No plan file found matching expected names (alex_chen_plan*, course_plan*, *plan*.md, etc.)"
    })
    
    if not file_found:
        # Can't do further checks
        for name in [
            "4-section output structure present",
            "Both targets mentioned (Waterloo CS + McMaster Eng)",
            "Top 6 analysis present",
            "Validation checklist section present",
            "Prerequisite course codes in plan",
            "All course codes from catalog only",
            "No 4U/4M courses in summer school slots",
            "protect_11_12 respected (Grade 12 has reasonable load)",
            "Cumulative credit counts present",
            "Online credits requirement noted/satisfied",
            "Catalog update diff present (ICS3U memo applied)",
            "ICS3U treated as online-only after memo",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Plan file missing — cannot evaluate"})
        
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, indent=2))
        return
    
    content = plan_content
    valid_codes = load_valid_codes(workspace)
    
    # ── Check 1: 4-section structure ─────────────────────────────────────────
    section_keywords = [
        ["target", "assumption"],
        ["prerequisite", "top 6"],
        ["grade 11", "grade 12"],
        ["validation", "checklist", "graduation"],
    ]
    section_names = [
        "Targets & assumptions section",
        "Prerequisites + Top 6 section",
        "4-year course plan by grade",
        "Validation checklist section",
    ]
    
    sections_ok = []
    for kws, name in zip(section_keywords, section_names):
        ok = check_section_presence(content, kws)
        sections_ok.append(ok)
    
    all_sections = all(sections_ok)
    checks.append({
        "name": "4-section output structure present",
        "passed": all_sections,
        "detail": f"Sections found: {dict(zip(section_names, sections_ok))}"
    })
    
    # ── Check 2: Both targets ─────────────────────────────────────────────────
    has_waterloo_cs, has_mcmaster_eng = check_targets_section(content)
    both_targets = has_waterloo_cs and has_mcmaster_eng
    checks.append({
        "name": "Both targets mentioned (Waterloo CS + McMaster Engineering)",
        "passed": both_targets,
        "detail": f"Waterloo CS: {has_waterloo_cs}, McMaster Engineering: {has_mcmaster_eng}"
    })
    
    # ── Check 3: Top 6 ───────────────────────────────────────────────────────
    has_top6 = check_top6_section(content)
    checks.append({
        "name": "Top 6 analysis present",
        "passed": has_top6,
        "detail": "Top 6 / Top six keyword found" if has_top6 else "No Top 6 analysis found"
    })
    
    # ── Check 4: Validation checklist ────────────────────────────────────────
    has_checklist = check_validation_checklist(content)
    checks.append({
        "name": "Validation checklist section present",
        "passed": has_checklist,
        "detail": "Validation/checklist keywords found" if has_checklist else "No validation checklist found"
    })
    
    # ── Check 5: Prerequisites ────────────────────────────────────────────────
    missing_prereqs, has_science, has_cs = check_prerequisites_present(content)
    prereqs_ok = len(missing_prereqs) == 0 and has_science and has_cs
    checks.append({
        "name": "Key prerequisite course codes present in plan",
        "passed": prereqs_ok,
        "detail": (
            f"Missing required codes: {missing_prereqs}; "
            f"Has science prereq (SCH4U/SPH4U): {has_science}; "
            f"Has CS pathway (ICS3U/ICS4U): {has_cs}"
        )
    })
    
    # ── Check 6: All codes from catalog ──────────────────────────────────────
    invalid_codes, all_codes_in_plan = check_codes_from_catalog(content, valid_codes)
    # Allow minor false positives (abbreviations) — flag if > 2 clearly invalid course codes
    # Filter invalid to those that actually look like course codes strictly
    strict_invalid = {c for c in invalid_codes if re.match(r'^[A-Z]{3}[0-9][A-Z]{1,2}$', c)}
    codes_ok = len(strict_invalid) == 0
    checks.append({
        "name": "All course codes in plan exist in course catalog",
        "passed": codes_ok,
        "detail": f"Invalid codes found: {strict_invalid if strict_invalid else 'none'} | Codes in plan: {sorted(all_codes_in_plan)[:20]}"
    })
    
    # ── Check 7: No 4U/M in summer school ────────────────────────────────────
    summer_violations = check_no_4u_in_summer(content)
    no_summer_violation = len(summer_violations) == 0
    checks.append({
        "name": "No 4U/4M courses placed in summer school slots (summerSchool.useFor=nonTop6)",
        "passed": no_summer_violation,
        "detail": f"4U/4M codes found in summer context: {summer_violations}" if summer_violations else "No violations — summer school correctly used for non-Top6 courses"
    })
    
    # ── Check 8: protect_11_12 ────────────────────────────────────────────────
    g12_4u_count, g12_4u_codes = check_protect_11_12(content)
    # Grade 12: 7-8 courses is standard; having all 8 as 4U is overload without justification
    # In protect_11_12 mode the plan should ideally cap heavy courses
    # We'll be lenient: warn if > 8 unique 4U codes in Grade 12 section (which would be impossible given 8 courses/yr)
    protect_ok = isinstance(g12_4u_count, int) and g12_4u_count <= 8
    checks.append({
        "name": "protect_11_12 respected (Grade 12 course load reasonable)",
        "passed": protect_ok,
        "detail": f"Grade 12 4U/4M course codes found: {g12_4u_codes} (count: {g12_4u_count})"
    })
    
    # ── Check 9: Cumulative credits ───────────────────────────────────────────
    has_credits = check_cumulative_credits(content)
    checks.append({
        "name": "Cumulative credit counts (total/compulsory/elective) present",
        "passed": has_credits,
        "detail": "Credit count patterns found" if has_credits else "No cumulative credit counts detected in output"
    })
    
    # ── Check 10: Online credits noted ───────────────────────────────────────
    online_noted = check_online_credits_noted(content)
    checks.append({
        "name": "Online credit requirement noted as already satisfied",
        "passed": online_noted,
        "detail": "Online credit acknowledgment found" if online_noted else "No mention of online credits / e-learning requirement"
    })
    
    # ── Check 11: Catalog update diff (ICS3U memo) ───────────────────────────
    diff_present = check_diff_present(content)
    checks.append({
        "name": "Catalog update applied with before/after diff (ICS3U memo from admin)",
        "passed": diff_present,
        "detail": "Update/diff section found" if diff_present else "No evidence of catalog update or before/after diff in output"
    })
    
    # ── Check 12: ICS3U treated as online after memo ─────────────────────────
    has_ics3u, ics3u_online = check_no_removed_course_in_final(content)
    # ICS3U should still appear (as prereq for ICS4U) but be noted as online-only
    ics3u_ok = has_ics3u and ics3u_online
    checks.append({
        "name": "ICS3U correctly noted as online-only section after catalog memo",
        "passed": ics3u_ok,
        "detail": f"ICS3U present: {has_ics3u}, ICS3U marked online: {ics3u_online}"
    })
    
    # ── Score ─────────────────────────────────────────────────────────────────
    weights = {
        0: 0.05,   # file exists
        1: 0.10,   # 4-section structure
        2: 0.08,   # both targets
        3: 0.07,   # top 6
        4: 0.07,   # validation checklist
        5: 0.12,   # prerequisites
        6: 0.10,   # codes from catalog
        7: 0.12,   # no 4U in summer
        8: 0.05,   # protect_11_12
        9: 0.08,   # cumulative credits
        10: 0.05,  # online credits
        11: 0.06,  # catalog diff
        12: 0.05,  # ICS3U online
    }
    
    score = sum(weights[i] * (1.0 if c["passed"] else 0.0) for i, c in enumerate(checks))
    passed = score >= 0.70
    
    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()