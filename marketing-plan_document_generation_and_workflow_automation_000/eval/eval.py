import sys
import json
import traceback
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── 1. Find the output file ──────────────────────────────────────────────
    target_filename = "沃特巢_营销方案.docx"
    found_files = list(workspace.rglob(target_filename))

    if not found_files:
        # Also accept any .docx that looks like the right one
        all_docx = list(workspace.rglob("*.docx"))
        detail = f"File '{target_filename}' not found. Found .docx files: {[str(f.relative_to(workspace)) for f in all_docx]}"
        checks.append({"name": "file_exists", "passed": False, "detail": detail})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    docx_path = found_files[0]
    total_score += add_check(
        "file_exists",
        True,
        f"Found target file at: {docx_path.relative_to(workspace)}"
    )

    # ── 2. Parse the docx ────────────────────────────────────────────────────
    try:
        from docx import Document
        doc = Document(str(docx_path))
    except Exception as e:
        checks.append({"name": "docx_parseable", "passed": False, "detail": f"Failed to parse docx: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    total_score += add_check("docx_parseable", True, "python-docx parsed the file successfully.")

    # Collect all text
    full_text = "\n".join([p.text for p in doc.paragraphs])
    # Also collect table cell text
    table_text = ""
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                table_text += cell.text + " "

    all_text = full_text + "\n" + table_text

    # ── 3. Chinese language mode check (lang='zh') ───────────────────────────
    # Must use Chinese section headings, not English ones
    zh_headings = ["一、项目概述", "二、预算分配", "三、执行计划", "四、目标指标"]
    en_headings = ["1. Executive Summary", "2. Budget Allocation", "3. Timeline", "4. Goals"]

    zh_heading_hits = sum(1 for h in zh_headings if h in all_text)
    en_heading_hits = sum(1 for h in en_headings if h in all_text)

    zh_mode_passed = zh_heading_hits >= 3 and en_heading_hits == 0
    total_score += add_check(
        "chinese_language_mode",
        zh_mode_passed,
        f"Chinese headings found: {zh_heading_hits}/4, English headings found: {en_heading_hits}. "
        f"Must use lang='zh' in generate_docx().",
        weight=2.0
    )

    # ── 4. Correct product & company in document ─────────────────────────────
    product_ok = "VoltNest 家用智能充电桩" in all_text or "家用智能充电桩" in all_text
    company_ok = "沃特巢科技" in all_text or "VoltNest" in all_text
    total_score += add_check(
        "product_company_present",
        product_ok and company_ok,
        f"Product found: {product_ok}, Company found: {company_ok}"
    )

    # ── 5. Budget correctness (¥200,000 and ¥ symbol in table) ───────────────
    # Budget total must appear; ¥ symbol required (zh mode)
    yuan_symbol_in_table = "¥" in table_text
    budget_value_present = "200,000" in all_text or "200000" in all_text
    total_score += add_check(
        "budget_yuan_symbol",
        yuan_symbol_in_table,
        f"'¥' symbol in budget table: {yuan_symbol_in_table}. Required by lang='zh' mode.",
        weight=1.5
    )
    total_score += add_check(
        "budget_total_present",
        budget_value_present,
        f"Budget value (200,000) found in document: {budget_value_present}"
    )

    # ── 6. All 4 channels present ─────────────────────────────────────────────
    expected_channels = ["抖音", "KOL", "展会", "SEM"]
    channel_hits = [c for c in expected_channels if c in all_text]
    channels_ok = len(channel_hits) >= 3
    total_score += add_check(
        "channels_present",
        channels_ok,
        f"Channels found: {channel_hits} ({len(channel_hits)}/4 required, need ≥3)",
        weight=1.5
    )

    # ── 7. Channel budget percentages → correct ¥ amounts ────────────────────
    # 40% of 200000 = 80000, 30% = 60000, 20% = 40000, 10% = 20000
    expected_amounts = ["80,000", "60,000", "40,000", "20,000"]
    amount_hits = [a for a in expected_amounts if a in table_text or a in all_text]
    amounts_ok = len(amount_hits) >= 3
    total_score += add_check(
        "channel_budget_amounts_correct",
        amounts_ok,
        f"Channel budget amounts found: {amount_hits}. "
        f"Expected: {expected_amounts} (budget * pct/100). Need ≥3.",
        weight=2.0
    )

    # ── 8. Milestones / timeline present ─────────────────────────────────────
    milestone_keywords = ["Week 1", "Week 2", "Week 4", "Week 6", "Week 8"]
    milestone_hits = [m for m in milestone_keywords if m in all_text]
    milestones_ok = len(milestone_hits) >= 4
    total_score += add_check(
        "milestones_present",
        milestones_ok,
        f"Milestone weeks found: {milestone_hits} ({len(milestone_hits)}/5, need ≥4)",
        weight=1.0
    )

    # ── 9. Goals present ─────────────────────────────────────────────────────
    goal_keywords = ["5,000,000", "50,000", "2,000", "300%"]
    goal_hits = [g for g in goal_keywords if g in all_text]
    goals_ok = len(goal_hits) >= 3
    total_score += add_check(
        "goals_present",
        goals_ok,
        f"Goal targets found: {goal_hits} ({len(goal_hits)}/4, need ≥3)",
        weight=1.0
    )

    # ── 10. Competitors data added via add_competitor ─────────────────────────
    competitor_keywords = ["特斯拉", "小鹏", "蔚来"]
    competitor_hits = [c for c in competitor_keywords if c in all_text]
    # Note: the base generate_docx() template doesn't render competitors,
    # so the agent must either extend the template or add them to another section.
    competitors_ok = len(competitor_hits) >= 2
    total_score += add_check(
        "competitors_in_document",
        competitors_ok,
        f"Competitor names found in document: {competitor_hits} ({len(competitor_hits)}/3, need ≥2). "
        "Agent must extend template to render competitor data.",
        weight=1.5
    )

    # ── 11. Table Grid style used ─────────────────────────────────────────────
    table_grid_used = any(
        t.style.name == "Table Grid" for t in doc.tables if t.style
    )
    total_score += add_check(
        "table_grid_style",
        table_grid_used,
        f"Budget table uses 'Table Grid' style: {table_grid_used}",
        weight=1.0
    )

    # ── 12. Document has at least one table with correct structure ────────────
    has_table = len(doc.tables) >= 1
    if has_table:
        first_table = doc.tables[0]
        # Should have header row + 4 channel rows = 5 rows, 3 cols
        rows_ok = len(first_table.rows) >= 3
        cols_ok = len(first_table.columns) >= 3
        table_structure_ok = rows_ok and cols_ok
    else:
        table_structure_ok = False

    total_score += add_check(
        "budget_table_structure",
        table_structure_ok,
        f"Budget table exists: {has_table}, rows≥3: {rows_ok if has_table else False}, cols≥3: {cols_ok if has_table else False}",
        weight=1.0
    )

    # ── Final scoring ─────────────────────────────────────────────────────────
    max_score = 1.0 + 1.0 + 2.0 + 1.0 + 1.5 + 1.0 + 1.5 + 2.0 + 1.0 + 1.0 + 1.5 + 1.0 + 1.0
    normalized_score = round(min(total_score / max_score, 1.0), 4)
    passed = normalized_score >= 0.75

    result = {
        "passed": passed,
        "score": normalized_score,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    try:
        run_eval(sys.argv[1])
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": traceback.format_exc()}]
        }))