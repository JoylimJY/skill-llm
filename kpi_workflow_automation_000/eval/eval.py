import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    
    # --- Locate the KPI file ---
    kpi_path = Path("/root/.openclaw/workspace/memory/kpi.md")
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # CHECK 0: File existence
    if not kpi_path.exists():
        add_check("kpi_file_exists", False, f"File not found at {kpi_path}")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    try:
        content = kpi_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("kpi_file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("kpi_file_exists", True, f"File found at {kpi_path}")
    
    # CHECK 1: File has proper top-level heading
    has_heading = bool(re.search(r'#\s+KPI', content))
    add_check("has_kpi_heading", has_heading, 
              "File contains a top-level KPI heading" if has_heading else "Missing top-level KPI heading")
    
    # CHECK 2: Contains at least 3 KPI blocks (should have 4 from the brief)
    kpi_sections = re.findall(r'###\s+KPI\s*\d+[:：]', content)
    has_min_kpis = len(kpi_sections) >= 3
    add_check("has_minimum_kpis", has_min_kpis,
              f"Found {len(kpi_sections)} KPI sections (need >= 3)" )
    
    # CHECK 3: Each KPI has all required fields
    required_fields = [
        (r'周期[:：]', '周期'),
        (r'(指标定义|指标说明)[:：]', '指标定义'),
        (r'统计口径[:：]', '统计口径'),
        (r'目标值[:：]', '目标值'),
        (r'实际值[:：]', '实际值'),
        (r'达成率[:：]', '达成率'),
        (r'负责人[:：]', '负责人'),
    ]
    
    all_fields_present = True
    missing_details = []
    for pattern, field_name in required_fields:
        count = len(re.findall(pattern, content))
        if count < 3:  # at least 3 KPIs should have each field
            all_fields_present = False
            missing_details.append(f"{field_name}: found {count} occurrences (need >=3)")
    
    add_check("all_kpi_required_fields_present", all_fields_present,
              "All KPIs have required fields" if all_fields_present else f"Missing fields: {'; '.join(missing_details)}")
    
    # CHECK 4: Actual values and achievement rates are present and non-trivial
    achievement_rates = re.findall(r'达成率[:：]\s*([0-9]+(?:\.[0-9]+)?)\s*%', content)
    has_achievement_rates = len(achievement_rates) >= 3
    add_check("has_achievement_rates", has_achievement_rates,
              f"Found {len(achievement_rates)} achievement rate entries (need >=3)")
    
    # CHECK 5: Achievement rates are calculated correctly for at least 2 KPIs
    # KPI1: 22/18 * 100% = 122.2%
    # KPI2: 41/30 * 100% = 136.7% (or similar)  
    # KPI3: 214/260 * 100% = 82.3%
    # KPI4: 2.1/2.5 * 100% = 84%
    expected_rates = {
        "content_volume": (22/18*100, 5.0),      # ~122.2%, tolerance 5%
        "mql": (214/260*100, 5.0),               # ~82.3%, tolerance 5%
        "conversion": (2.1/2.5*100, 5.0),        # ~84%, tolerance 5%
    }
    
    all_rates = [float(r) for r in achievement_rates]
    correct_calcs = 0
    for name, (expected, tol) in expected_rates.items():
        for rate in all_rates:
            if abs(rate - expected) <= tol:
                correct_calcs += 1
                break
    
    has_correct_calcs = correct_calcs >= 2
    add_check("achievement_rates_correctly_calculated", has_correct_calcs,
              f"Found {correct_calcs}/3 correctly calculated achievement rates" +
              f" (expected ~122.2%, ~82.3%, ~84%)")
    
    # CHECK 6: Tasks are present with proper checkbox format
    task_checkboxes = re.findall(r'- \[[ x]\]', content)
    has_tasks = len(task_checkboxes) >= 8  # At least 8 tasks across all KPIs (min 2 per KPI)
    add_check("has_task_checkboxes", has_tasks,
              f"Found {len(task_checkboxes)} task checkbox entries (need >= 8)")
    
    # CHECK 7: Completed tasks are marked with [x]
    completed_tasks = re.findall(r'- \[x\]', content, re.IGNORECASE)
    has_completed_tasks = len(completed_tasks) >= 6  # Most tasks in brief are completed
    add_check("has_completed_task_markers", has_completed_tasks,
              f"Found {len(completed_tasks)} completed [x] tasks (need >= 6)")
    
    # CHECK 8: Has retrospective/复盘 section
    has_retrospective = bool(re.search(r'复盘', content))
    add_check("has_retrospective_section", has_retrospective,
              "File contains retrospective (复盘) section" if has_retrospective else "Missing 复盘 section")
    
    # CHECK 9: Retrospective has all 5 required sub-sections
    retro_required = [
        (r'结果概述', '结果概述'),
        (r'高杠杆动作', '高杠杆动作'),
        (r'偏差原因', '偏差原因'),
        (r'可复用经验', '可复用经验'),
        (r'下周期优化项', '下周期优化项'),
    ]
    
    retro_present = []
    retro_missing = []
    for pattern, field in retro_required:
        if re.search(pattern, content):
            retro_present.append(field)
        else:
            retro_missing.append(field)
    
    all_retro_fields = len(retro_missing) == 0
    add_check("retrospective_has_all_5_fields", all_retro_fields,
              f"Present: {retro_present}" + (f" | Missing: {retro_missing}" if retro_missing else ""))
    
    # CHECK 10 (CRITICAL PROPRIETARY TRAP): Score must be EXACTLY from {5, 4, 3.75, 3.5, 3.25}
    # Find all score mentions in retrospective area
    valid_scores = {5.0, 4.0, 3.75, 3.5, 3.25}
    
    # Look for score patterns
    score_patterns = re.findall(
        r'(?:最终评分|评分|得分|score)[:：\s]*([0-9]+(?:\.[0-9]+)?)',
        content, re.IGNORECASE
    )
    
    score_found = False
    score_valid = False
    score_value = None
    
    if score_patterns:
        score_found = True
        for sp in score_patterns:
            try:
                sv = float(sp)
                if sv in valid_scores:
                    score_valid = True
                    score_value = sv
                    break
            except ValueError:
                pass
    
    add_check("retrospective_has_score", score_found,
              f"Score field found: {score_patterns}" if score_found else "No score found in retrospective")
    
    add_check("score_uses_valid_ladder_value", score_valid,
              f"Score {score_value} is from valid ladder {{5, 4, 3.75, 3.5, 3.25}}" if score_valid 
              else f"Score(s) found: {score_patterns} — NONE match valid ladder {{5, 4, 3.75, 3.5, 3.25}}")
    
    # CHECK 11: Retrospective content is non-trivial (each field has actual content, not just the label)
    retro_content_checks = []
    for pattern, field in retro_required:
        # Look for the field followed by actual content (not just an empty line)
        match = re.search(pattern + r'[:：]?\s*(.{10,})', content)
        if match:
            retro_content_checks.append(field)
    
    retro_has_content = len(retro_content_checks) >= 4
    add_check("retrospective_fields_have_content", retro_has_content,
              f"{len(retro_content_checks)}/5 retrospective fields have non-trivial content")
    
    # CHECK 12: File is in "归档" or "复盘归档" section (proper structural separation)
    has_archive_section = bool(re.search(r'(复盘归档|归档)', content))
    add_check("has_archive_section", has_archive_section,
              "File has 复盘归档 archive section" if has_archive_section else "Missing 复盘归档 section")
    
    # CHECK 13: KPI cycle period matches Q2 2024
    has_q2_period = bool(re.search(r'2024[-–]Q2|2024-0[456]|Q2\s*2024', content))
    add_check("kpi_period_is_q2_2024", has_q2_period,
              "KPI period correctly references 2024-Q2" if has_q2_period else "KPI period 2024-Q2 not found")
    
    # CHECK 14: Alex Wong is listed as responsible person
    has_responsible_person = bool(re.search(r'Alex\s*Wong|Alex wong', content, re.IGNORECASE))
    add_check("has_correct_responsible_person", has_responsible_person,
              "Alex Wong listed as responsible person" if has_responsible_person else "Responsible person Alex Wong not found")
    
    # --- Calculate final score ---
    critical_checks = [
        "kpi_file_exists",
        "has_minimum_kpis",
        "all_kpi_required_fields_present",
        "has_achievement_rates",
        "has_tasks_checkboxes" if False else "has_task_checkboxes",
        "has_retrospective_section",
        "retrospective_has_all_5_fields",
        "retrospective_has_score",
        "score_uses_valid_ladder_value",
    ]
    
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    
    # Must pass all critical checks to overall pass
    critical_passed = all(
        c["passed"] for c in checks 
        if c["name"] in critical_checks
    )
    
    score = passed_count / total_count
    overall_passed = critical_passed and score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))