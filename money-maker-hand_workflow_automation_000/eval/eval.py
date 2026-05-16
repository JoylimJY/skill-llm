import sys
import json
import re
import os
from pathlib import Path

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_checks(workspace):
    checks = []
    overall_passed = True

    # ── Locate the weekly report Markdown file ──────────────────────────────
    report_files = list(Path(workspace).rglob("weekly_report.md"))
    if not report_files:
        # Also accept common alternative names
        report_files = list(Path(workspace).rglob("*report*.md"))

    report_exists = len(report_files) > 0
    checks.append({
        "name": "weekly_report_md_exists",
        "passed": report_exists,
        "detail": f"Found: {[str(p) for p in report_files]}" if report_exists else "No .md report file found."
    })
    if not report_exists:
        overall_passed = False

    report_content = ""
    if report_exists:
        try:
            with open(report_files[0], "r", encoding="utf-8") as f:
                report_content = f.read()
        except Exception as e:
            checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
            overall_passed = False

    # ── Check 1: Report has required sections ───────────────────────────────
    required_sections = ["收入进度", "Top 5", "行动计划", "风险"]
    sections_found = [s for s in required_sections if s in report_content]
    section_check = len(sections_found) == len(required_sections)
    checks.append({
        "name": "report_has_required_sections",
        "passed": section_check,
        "detail": f"Found sections matching: {sections_found}. Required: {required_sections}"
    })
    if not section_check:
        overall_passed = False

    # ── Check 2: Opportunity scoring (30+30+20+20 rubric) ──────────────────
    # Load income_database.json and check that scored opportunities are present
    db_path = Path(workspace) / "income_database.json"
    db_data = {}
    try:
        db_data = load_json(db_path)
    except Exception as e:
        checks.append({"name": "income_database_readable", "passed": False, "detail": str(e)})
        overall_passed = False

    # Check scored opportunities exist in the database
    opps = db_data.get("opportunities_scored", db_data.get("opportunities_raw", []))
    
    # Try to find scored data - could be in various keys
    scored_opps = db_data.get("opportunities_scored", [])
    has_scores = False
    correct_scores = []
    
    # Expected scores from raw values (sum of the 4 dimension raw scores):
    # market_demand_raw + monetization_raw + entry_barrier_raw + time_investment_raw
    expected_scores = {
        "知乎盐选投稿": 28 + 27 + 18 + 19,   # = 92
        "小红书起号": 25 + 26 + 14 + 15,       # = 80
        "Skill 开发外包": 18 + 22 + 13 + 15,   # = 68
        "知乎问答带货": 20 + 14 + 16 + 15,     # = 65
        "技术文档翻译": 12 + 12 + 10 + 17,     # = 51  → BELOW min 60, excluded
        "数据标注兼职": 10 + 8 + 18 + 5,       # = 41  → BELOW min 60, excluded
        "视频号带货": 22 + 18 + 5 + 6,         # = 51  → BELOW min 60, excluded
    }
    # Opportunities with score >= 60: 知乎盐选投稿(92), 小红书起号(80), Skill开发外包(68), 知乎问答带货(65)
    # Only 4 qualify (>= 60), so report shows Top 4 (not 5, but that's max available above threshold)
    qualifying = {k: v for k, v in expected_scores.items() if v >= 60}
    # qualifying: 4 items

    if scored_opps:
        has_scores = True
        for opp in scored_opps:
            name = opp.get("name", "")
            score = opp.get("score", opp.get("total_score", None))
            if name in expected_scores and score is not None:
                correct_scores.append(abs(int(score) - expected_scores[name]) <= 2)

    checks.append({
        "name": "opportunities_scored_in_database",
        "passed": has_scores and len(correct_scores) > 0,
        "detail": f"Scored opportunities found: {has_scores}. Correct score checks: {correct_scores}"
    })
    if not (has_scores and len(correct_scores) > 0):
        overall_passed = False

    # ── Check 3: Report excludes below-threshold opportunities ──────────────
    excluded_in_report = True
    for name in ["技術文档翻译", "技术文档翻译", "数据标注兼职", "视频号带货"]:
        # These have scores < 60 and should NOT appear as ranked opportunities in report
        # (they could appear in risk section, but not in Top N list)
        pass  # We check in the ranked section specifically

    # Check that the TOP section in report contains high-scoring items
    top_section_match = re.search(r"Top\s*\d.*?(?=##|\Z)", report_content, re.DOTALL | re.IGNORECASE)
    top_section = top_section_match.group(0) if top_section_match else ""
    
    has_zhihu_top = "知乎盐选投稿" in top_section or "知乎盐选" in top_section
    checks.append({
        "name": "report_top_section_has_highest_scored_opportunity",
        "passed": has_zhihu_top,
        "detail": f"知乎盐选投稿 (score 92) should appear in Top section. Found: {has_zhihu_top}"
    })
    if not has_zhihu_top:
        overall_passed = False

    # ── Check 4: Excluded low-score opps not in top ranked list ────────────
    # 数据标注兼职 (score 41) must NOT be a ranked opportunity
    low_score_excluded = "数据标注兼职" not in top_section
    checks.append({
        "name": "low_score_opportunity_excluded_from_top_list",
        "passed": low_score_excluded,
        "detail": f"数据标注兼职 (score 41, below min 60) must not appear in ranked opportunity list. Excluded: {low_score_excluded}"
    })
    if not low_score_excluded:
        overall_passed = False

    # ── Check 5: Dashboard metrics updated ──────────────────────────────────
    dashboard_path = Path(workspace) / "dashboard_metrics.json"
    dashboard_data = {}
    try:
        dashboard_data = load_json(dashboard_path)
    except Exception as e:
        checks.append({"name": "dashboard_metrics_readable", "passed": False, "detail": str(e)})
        overall_passed = False

    # daily_target = (10000 - 0) / 28 = 357.14... → should be ~357
    daily_target = dashboard_data.get("money_maker_daily_target", 0)
    daily_target_correct = 350 <= float(daily_target) <= 365
    checks.append({
        "name": "dashboard_daily_target_correct",
        "passed": daily_target_correct,
        "detail": f"Expected ~357 (10000/28), got {daily_target}"
    })
    if not daily_target_correct:
        overall_passed = False

    # opportunities_found should reflect qualifying count (>= 4 since 4 qualify above threshold)
    opps_found = dashboard_data.get("money_maker_opportunities_found", 0)
    opps_found_correct = int(opps_found) >= 4
    checks.append({
        "name": "dashboard_opportunities_found_updated",
        "passed": opps_found_correct,
        "detail": f"Expected >= 4 qualifying opportunities found, got {opps_found}"
    })
    if not opps_found_correct:
        overall_passed = False

    # reports_generated should be >= 1
    reports_gen = dashboard_data.get("money_maker_reports_generated", 0)
    reports_gen_correct = int(reports_gen) >= 1
    checks.append({
        "name": "dashboard_reports_generated_incremented",
        "passed": reports_gen_correct,
        "detail": f"Expected >= 1, got {reports_gen}"
    })
    if not reports_gen_correct:
        overall_passed = False

    # last_report_date should not be null
    last_report_date = dashboard_data.get("money_maker_last_report_date", None)
    date_set = last_report_date is not None and last_report_date != "null" and str(last_report_date).strip() != ""
    checks.append({
        "name": "dashboard_last_report_date_set",
        "passed": date_set,
        "detail": f"last_report_date should not be null/empty, got: {last_report_date}"
    })
    if not date_set:
        overall_passed = False

    # ── Check 6: income_database.json schema updated ─────────────────────────
    # Should have correct income_sources structure
    sources = db_data.get("income_sources", [])
    source_names = [s.get("name", "") for s in sources]
    required_sources = ["知乎盐选", "小红书", "Skill 开发", "外包接单"]
    sources_ok = all(rs in source_names for rs in required_sources)
    checks.append({
        "name": "income_database_has_all_sources",
        "passed": sources_ok,
        "detail": f"Required sources: {required_sources}. Found: {source_names}"
    })
    if not sources_ok:
        overall_passed = False

    # ── Check 7: Report has income progress with correct figures ─────────────
    # Report must show goal=10000, current=0, progress=0%, days=28
    has_goal = "10,000" in report_content or "10000" in report_content
    has_days = "28" in report_content
    progress_correct = has_goal and has_days
    checks.append({
        "name": "report_income_progress_correct_figures",
        "passed": progress_correct,
        "detail": f"Report must include goal (10000) and days (28). has_goal={has_goal}, has_days={has_days}"
    })
    if not progress_correct:
        overall_passed = False

    # ── Check 8: State persistence file updated ──────────────────────────────
    state_path = Path(workspace) / "money_maker_state.json"
    state_data = {}
    try:
        state_data = load_json(state_path)
    except Exception as e:
        checks.append({"name": "state_file_readable", "passed": False, "detail": str(e)})
        overall_passed = False

    # last_phase_completed should be 7 (all 7 phases done)
    phase_completed = state_data.get("last_phase_completed", 0)
    phase_ok = int(phase_completed) >= 6
    checks.append({
        "name": "state_all_phases_completed",
        "passed": phase_ok,
        "detail": f"Expected last_phase_completed >= 6 (all phases), got {phase_completed}"
    })
    if not phase_ok:
        overall_passed = False

    # ── Score calculation ────────────────────────────────────────────────────
    n_checks = len(checks)
    n_passed = sum(1 for c in checks if c["passed"])
    score = round(n_passed / n_checks, 4) if n_checks > 0 else 0.0

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))