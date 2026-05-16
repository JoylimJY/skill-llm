import sys
import os
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # ─────────────────────────────────────────────
    # Helper
    # ─────────────────────────────────────────────
    def read_file(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # ══════════════════════════════════════════════
    # FILE 1: references/exercises.md
    # Must cover all 6 subsections of Chapter 1 (除法)
    # with correct Chinese titles and knowledge-point
    # terminology from SKILL.md
    # ══════════════════════════════════════════════
    exercises_path = workspace / "references" / "exercises.md"

    # Check 1: File exists
    check_exists = {"name": "exercises.md exists at references/exercises.md", "passed": False, "detail": ""}
    try:
        if exercises_path.exists():
            check_exists["passed"] = True
            check_exists["detail"] = "File found."
        else:
            check_exists["detail"] = "File not found at references/exercises.md"
    except Exception as e:
        check_exists["detail"] = f"Error: {e}"
    checks.append(check_exists)

    ex_content = ""
    if exercises_path.exists():
        try:
            ex_content = read_file(exercises_path)
        except Exception as e:
            ex_content = ""

    # Check 2: All 6 subsections of Chapter 1 present
    ch1_sections = [
        ("分苹果", "1.1"),
        ("搭一搭", "1.2"),   # 搭一搭（一） and/or 搭一搭（二）
        ("分草莓", "1.4"),
        ("分橘子", "1.5"),
        ("分一分", "1.6"),
    ]
    check_ch1_sections = {"name": "exercises.md covers Chapter 1 subsection titles (分苹果,搭一搭,分草莓,分橘子,分一分)", "passed": False, "detail": ""}
    try:
        missing = []
        for title, _ in ch1_sections:
            if title not in ex_content:
                missing.append(title)
        if not missing:
            check_ch1_sections["passed"] = True
            check_ch1_sections["detail"] = "All required Chapter 1 subsection titles found."
        else:
            check_ch1_sections["detail"] = f"Missing subsection titles: {missing}"
    except Exception as e:
        check_ch1_sections["detail"] = f"Error: {e}"
    checks.append(check_ch1_sections)

    # Check 3: Section 1.5 分橘子 uses correct terminology (被除数、除数、商)
    check_terminology = {"name": "exercises.md contains 被除数/除数/商 terminology for 分橘子 (1.5)", "passed": False, "detail": ""}
    try:
        terms = ["被除数", "除数", "商"]
        missing_terms = [t for t in terms if t not in ex_content]
        if not missing_terms:
            check_terminology["passed"] = True
            check_terminology["detail"] = "All required terms (被除数, 除数, 商) found."
        else:
            check_terminology["detail"] = f"Missing terminology: {missing_terms}"
    except Exception as e:
        check_terminology["detail"] = f"Error: {e}"
    checks.append(check_terminology)

    # Check 4: Contains actual exercise questions (at least some numeric content / question marks)
    check_has_exercises = {"name": "exercises.md contains actual exercise questions (not just headers)", "passed": False, "detail": ""}
    try:
        # Look for question marks or arithmetic expressions or numbered items
        has_questions = (
            ex_content.count("？") + ex_content.count("?") >= 3
            or bool(re.search(r'\d+\s*[÷×+\-]\s*\d+', ex_content))
            or bool(re.search(r'[1-9]\．|[1-9]\. |[1-9]、', ex_content))
        )
        if has_questions:
            check_has_exercises["passed"] = True
            check_has_exercises["detail"] = "Exercise questions found."
        else:
            check_has_exercises["detail"] = "No actual exercise questions detected (need question marks or arithmetic expressions)."
    except Exception as e:
        check_has_exercises["detail"] = f"Error: {e}"
    checks.append(check_has_exercises)

    # Check 5: Mentions 平均分 (core concept of Chapter 1)
    check_pingjunfen = {"name": "exercises.md mentions 平均分 (core concept, Chapter 1.1 and 1.6)", "passed": False, "detail": ""}
    try:
        if "平均分" in ex_content:
            check_pingjunfen["passed"] = True
            check_pingjunfen["detail"] = "平均分 found."
        else:
            check_pingjunfen["detail"] = "平均分 not found in exercises.md"
    except Exception as e:
        check_pingjunfen["detail"] = f"Error: {e}"
    checks.append(check_pingjunfen)

    # ══════════════════════════════════════════════
    # FILE 2: references/common_errors.md
    # Must cover Chapter 4 (测量) with both subsections:
    # 4.1 铅笔有多长 (厘米、分米) and 4.2 1千米有多长
    # ══════════════════════════════════════════════
    errors_path = workspace / "references" / "common_errors.md"

    check_errors_exists = {"name": "common_errors.md exists at references/common_errors.md", "passed": False, "detail": ""}
    try:
        if errors_path.exists():
            check_errors_exists["passed"] = True
            check_errors_exists["detail"] = "File found."
        else:
            check_errors_exists["detail"] = "File not found at references/common_errors.md"
    except Exception as e:
        check_errors_exists["detail"] = f"Error: {e}"
    checks.append(check_errors_exists)

    err_content = ""
    if errors_path.exists():
        try:
            err_content = read_file(errors_path)
        except Exception as e:
            err_content = ""

    # Check 6: 测量 chapter heading present
    check_measurement_chapter = {"name": "common_errors.md covers 测量 (Chapter 4)", "passed": False, "detail": ""}
    try:
        if "测量" in err_content:
            check_measurement_chapter["passed"] = True
            check_measurement_chapter["detail"] = "测量 chapter found."
        else:
            check_measurement_chapter["detail"] = "测量 not found in common_errors.md"
    except Exception as e:
        check_measurement_chapter["detail"] = f"Error: {e}"
    checks.append(check_measurement_chapter)

    # Check 7: Both subsections of Chapter 4 mentioned
    check_ch4_subsections = {"name": "common_errors.md includes 铅笔有多长 and 1千米有多长 sections", "passed": False, "detail": ""}
    try:
        has_41 = "铅笔有多长" in err_content
        has_42 = "千米有多长" in err_content or "1千米" in err_content
        if has_41 and has_42:
            check_ch4_subsections["passed"] = True
            check_ch4_subsections["detail"] = "Both subsections found."
        else:
            missing = []
            if not has_41:
                missing.append("铅笔有多长 (4.1)")
            if not has_42:
                missing.append("1千米有多长 (4.2)")
            check_ch4_subsections["detail"] = f"Missing: {missing}"
    except Exception as e:
        check_ch4_subsections["detail"] = f"Error: {e}"
    checks.append(check_ch4_subsections)

    # Check 8: Correct length unit terms (厘米, 分米, 千米)
    check_units = {"name": "common_errors.md contains correct length units: 厘米, 分米, 千米", "passed": False, "detail": ""}
    try:
        units = ["厘米", "分米", "千米"]
        missing_units = [u for u in units if u not in err_content]
        if not missing_units:
            check_units["passed"] = True
            check_units["detail"] = "All length units (厘米, 分米, 千米) found."
        else:
            check_units["detail"] = f"Missing units: {missing_units}"
    except Exception as e:
        check_units["detail"] = f"Error: {e}"
    checks.append(check_units)

    # Check 9: Contains actual error descriptions (not just headers)
    check_errors_content = {"name": "common_errors.md has substantive error descriptions", "passed": False, "detail": ""}
    try:
        # Must have more than just section headers - look for explanation text
        lines = [l.strip() for l in err_content.split("\n") if l.strip() and not l.strip().startswith("#")]
        substantive = [l for l in lines if len(l) > 10]
        if len(substantive) >= 3:
            check_errors_content["passed"] = True
            check_errors_content["detail"] = f"Found {len(substantive)} substantive lines."
        else:
            check_errors_content["detail"] = f"Only {len(substantive)} substantive lines (need >= 3)."
    except Exception as e:
        check_errors_content["detail"] = f"Error: {e}"
    checks.append(check_errors_content)

    # ══════════════════════════════════════════════
    # FILE 3: assets/templates/week_plan.md
    # Must be a 5-day plan for Chapter 3 (生活中的大数)
    # with correct 4 subsections and 30-40 min daily time
    # ══════════════════════════════════════════════
    plan_path = workspace / "assets" / "templates" / "week_plan.md"

    check_plan_exists = {"name": "week_plan.md exists at assets/templates/week_plan.md", "passed": False, "detail": ""}
    try:
        if plan_path.exists():
            check_plan_exists["passed"] = True
            check_plan_exists["detail"] = "File found."
        else:
            check_plan_exists["detail"] = "File not found at assets/templates/week_plan.md"
    except Exception as e:
        check_plan_exists["detail"] = f"Error: {e}"
    checks.append(check_plan_exists)

    plan_content = ""
    if plan_path.exists():
        try:
            plan_content = read_file(plan_path)
        except Exception as e:
            plan_content = ""

    # Check 10: Chapter 3 生活中的大数 is the target chapter
    check_plan_chapter3 = {"name": "week_plan.md targets Chapter 3 (生活中的大数)", "passed": False, "detail": ""}
    try:
        if "生活中的大数" in plan_content:
            check_plan_chapter3["passed"] = True
            check_plan_chapter3["detail"] = "生活中的大数 found in week plan."
        else:
            check_plan_chapter3["detail"] = "生活中的大数 not found in week_plan.md"
    except Exception as e:
        check_plan_chapter3["detail"] = f"Error: {e}"
    checks.append(check_plan_chapter3)

    # Check 11: All 4 subsections of Chapter 3 are present
    ch3_sections = ["数一数", "拨一拨", "比一比", "有多少个字"]
    check_ch3_subsections = {"name": "week_plan.md includes all 4 subsections of Chapter 3 (数一数,拨一拨,比一比,有多少个字)", "passed": False, "detail": ""}
    try:
        missing_ch3 = [s for s in ch3_sections if s not in plan_content]
        if not missing_ch3:
            check_ch3_subsections["passed"] = True
            check_ch3_subsections["detail"] = "All 4 Chapter 3 subsections found."
        else:
            check_ch3_subsections["detail"] = f"Missing subsections: {missing_ch3}"
    except Exception as e:
        check_ch3_subsections["detail"] = f"Error: {e}"
    checks.append(check_ch3_subsections)

    # Check 12: Daily study time recommendation 30-40 minutes
    check_study_time = {"name": "week_plan.md specifies 30-40 minutes daily study time", "passed": False, "detail": ""}
    try:
        # Match patterns like "30-40分钟", "30～40分钟", "30~40分钟", "30到40分钟"
        time_pattern = re.search(r'30\s*[-～~到]\s*40\s*分钟', plan_content)
        # Also accept "每天.*30.*40" type patterns
        alt_pattern = re.search(r'30.*40.*分钟|40.*分钟.*30', plan_content)
        if time_pattern or alt_pattern:
            check_study_time["passed"] = True
            check_study_time["detail"] = "30-40 minutes study time found."
        else:
            check_study_time["detail"] = "30-40 minutes daily study time not found. Need pattern like '30-40分钟'."
    except Exception as e:
        check_study_time["detail"] = f"Error: {e}"
    checks.append(check_study_time)

    # Check 13: Plan covers 5 days (weekday structure)
    check_five_days = {"name": "week_plan.md covers a 5-day weekly structure", "passed": False, "detail": ""}
    try:
        # Look for weekday mentions in Chinese or numbered days
        day_patterns = [
            r'周[一二三四五]|星期[一二三四五]',
            r'[第]?[一二三四五]天',
            r'Day\s*[1-5]',
            r'第[1-5]天',
        ]
        day_count = 0
        for pattern in day_patterns:
            matches = re.findall(pattern, plan_content)
            day_count = max(day_count, len(matches))

        # Also check for explicit "5天" or "一周" mentions
        has_week_ref = "一周" in plan_content or "本周" in plan_content or "5天" in plan_content

        if day_count >= 5 or (day_count >= 4 and has_week_ref):
            check_five_days["passed"] = True
            check_five_days["detail"] = f"5-day structure found (matched {day_count} day references)."
        elif day_count >= 3:
            # Partial credit check - still pass if there's clear weekly structure
            if has_week_ref:
                check_five_days["passed"] = True
                check_five_days["detail"] = f"Weekly structure found with {day_count} day references + week reference."
            else:
                check_five_days["detail"] = f"Only {day_count} day references found (need 5)."
        else:
            check_five_days["detail"] = f"Only {day_count} day references found (need 5 for weekly plan)."
    except Exception as e:
        check_five_days["detail"] = f"Error: {e}"
    checks.append(check_five_days)

    # Check 14: Practice lesson (练习课) mentioned in the plan
    check_practice = {"name": "week_plan.md includes 练习课 (practice lesson) in the weekly plan", "passed": False, "detail": ""}
    try:
        if "练习课" in plan_content or "练习" in plan_content:
            check_practice["passed"] = True
            check_practice["detail"] = "练习课 or 练习 found in plan."
        else:
            check_practice["detail"] = "练习课 not found in week_plan.md"
    except Exception as e:
        check_practice["detail"] = f"Error: {e}"
    checks.append(check_practice)

    # ══════════════════════════════════════════════
    # SCORING
    # ══════════════════════════════════════════════
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0
    overall_passed = score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "argument check", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace_dir = sys.argv[1]
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))