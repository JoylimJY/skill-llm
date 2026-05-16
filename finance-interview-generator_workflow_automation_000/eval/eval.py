import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    
    # ── 1. Find the output file ──────────────────────────────────────────────
    workspace = Path(workspace_dir)
    candidates = list(workspace.rglob("interview_questions.md"))
    
    file_found = len(candidates) > 0
    checks.append({
        "name": "Output file 'interview_questions.md' exists",
        "passed": file_found,
        "detail": f"Found at {candidates[0]}" if file_found else "File not found anywhere in workspace"
    })
    
    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    
    try:
        content = candidates[0].read_text(encoding='utf-8')
    except Exception as e:
        checks.append({"name": "File is readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "File is readable", "passed": True, "detail": f"Content length: {len(content)} chars"})
    
    # ── 2. Check for 5-column table structure ───────────────────────────────
    required_headers = ["考察能力", "问题类型", "面试问题", "预期回答要点", "追问建议"]
    header_check = all(h in content for h in required_headers)
    checks.append({
        "name": "Table has all 5 required Chinese column headers",
        "passed": header_check,
        "detail": f"Required: {required_headers}\nFound headers present: {[h for h in required_headers if h in content]}\nMissing: {[h for h in required_headers if h not in content]}"
    })
    
    # ── 3. Check markdown table format (pipe characters) ────────────────────
    table_rows = [line.strip() for line in content.split('\n') if line.strip().startswith('|')]
    has_table_format = len(table_rows) >= 3  # at least header, separator, one data row
    checks.append({
        "name": "Content uses markdown table format (pipe-delimited rows)",
        "passed": has_table_format,
        "detail": f"Found {len(table_rows)} table rows (need >= 3)"
    })
    
    # ── 4. Check correct level: 中层管理者 ──────────────────────────────────
    # The task specifies mid-level (finance manager, 5-8 years), NOT 高级管理层 or 骨干员工
    # The questions should reflect 中层管理者 context
    level_keywords = ["中层管理者", "财务经理", "Finance Manager"]
    # We check indirectly: the content should NOT only have 高级管理层 framing
    # More importantly, the questions should be appropriate in tone
    # Direct check: does it mention the position
    position_check = "财务经理" in content or "Finance Manager" in content
    checks.append({
        "name": "Position/role context reflects Finance Manager (中层管理者 level)",
        "passed": position_check,
        "detail": f"'财务经理' or 'Finance Manager' found in content: {position_check}"
    })
    
    # ── 5. Check capabilities: 预算管理 AND 融资筹划 ────────────────────────
    capability_budget = "预算管理" in content or "预算" in content
    capability_financing = "融资筹划" in content or "融资" in content
    both_capabilities = capability_budget and capability_financing
    checks.append({
        "name": "Both required capabilities covered: 预算管理 and 融资筹划",
        "passed": both_capabilities,
        "detail": f"预算管理 present: {capability_budget}, 融资筹划 present: {capability_financing}"
    })
    
    # ── 6. Check industry context: 房地产 ───────────────────────────────────
    industry_check = "房地产" in content
    checks.append({
        "name": "Industry context 房地产 (real estate) is reflected",
        "passed": industry_check,
        "detail": f"'房地产' found in content: {industry_check}"
    })
    
    # ── 7. Check all 4 question types are present ───────────────────────────
    required_qtypes = ["行为事件法", "情景模拟", "专业技能", "压力测试"]
    found_qtypes = [qt for qt in required_qtypes if qt in content]
    all_qtypes = len(found_qtypes) == 4
    checks.append({
        "name": "All 4 question types present (行为事件法/情景模拟/专业技能/压力测试)",
        "passed": all_qtypes,
        "detail": f"Found: {found_qtypes}\nMissing: {[qt for qt in required_qtypes if qt not in content]}"
    })
    
    # ── 8. Check 追问建议 column has actual content (not empty) ─────────────
    # Parse table rows to find non-empty 追问建议 cells
    data_rows_with_followup = 0
    for row in table_rows:
        if row.startswith('|') and '---' not in row:
            cells = [c.strip() for c in row.split('|') if c.strip()]
            if len(cells) >= 5:
                followup_cell = cells[4]
                if len(followup_cell) > 5 and followup_cell not in ["追问建议", "---"]:
                    data_rows_with_followup += 1
    
    followup_has_content = data_rows_with_followup >= 2
    checks.append({
        "name": "追问建议 column has substantive content in at least 2 rows",
        "passed": followup_has_content,
        "detail": f"Rows with non-trivial 追问建议 content: {data_rows_with_followup} (need >= 2)"
    })
    
    # ── 9. Check 预期回答要点 column has actual content ─────────────────────
    data_rows_with_expected = 0
    for row in table_rows:
        if row.startswith('|') and '---' not in row:
            cells = [c.strip() for c in row.split('|') if c.strip()]
            if len(cells) >= 4:
                expected_cell = cells[3]
                if len(expected_cell) > 5 and expected_cell not in ["预期回答要点", "---"]:
                    data_rows_with_expected += 1
    
    expected_has_content = data_rows_with_expected >= 2
    checks.append({
        "name": "预期回答要点 column has substantive content in at least 2 rows",
        "passed": expected_has_content,
        "detail": f"Rows with non-trivial 预期回答要点 content: {data_rows_with_expected} (need >= 2)"
    })
    
    # ── 10. Minimum number of question rows (at least 4 data rows) ──────────
    # Count actual data rows (not header, not separator)
    data_rows = []
    for row in table_rows:
        if '---' not in row and '考察能力' not in row and row.startswith('|'):
            cells = [c.strip() for c in row.split('|') if c.strip()]
            if len(cells) >= 3:
                data_rows.append(row)
    
    sufficient_rows = len(data_rows) >= 4
    checks.append({
        "name": "Table has at least 4 question data rows",
        "passed": sufficient_rows,
        "detail": f"Data rows found: {len(data_rows)} (need >= 4)"
    })
    
    # ── 11. BEI question type includes "(BEI)" notation ─────────────────────
    bei_notation = "行为事件法(BEI)" in content or "行为事件法（BEI）" in content or ("BEI" in content and "行为事件法" in content)
    checks.append({
        "name": "BEI question type includes BEI notation",
        "passed": bei_notation,
        "detail": f"'行为事件法(BEI)' or equivalent found: {bei_notation}"
    })
    
    # ── Final scoring ───────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    
    # Must pass critical checks to be considered overall passing
    critical_checks = [
        "Output file 'interview_questions.md' exists",
        "Table has all 5 required Chinese column headers",
        "Both required capabilities covered: 预算管理 and 融资筹划",
        "All 4 question types present (行为事件法/情景模拟/专业技能/压力测试)",
        "追问建议 column has substantive content in at least 2 rows",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))