import sys
import os
import json
import re
from pathlib import Path

def find_file(workspace, filename):
    """Search recursively for a file by name."""
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""

def check_eng_review(workspace):
    checks = []

    # Find ENG_REVIEW.md
    f = find_file(workspace, "ENG_REVIEW.md")
    if f is None:
        return [{"name": "eng_review_file_exists", "passed": False, "detail": "ENG_REVIEW.md not found anywhere in workspace"}]
    
    content = read_file(f)
    content_lower = content.lower()

    checks.append({"name": "eng_review_file_exists", "passed": True, "detail": f"Found at {f}"})

    # Must contain the 5 review areas (Chinese or English acceptable)
    review_areas = [
        (["架构", "architecture", "模块"], "架构/Architecture section"),
        (["数据流", "data flow", "dataflow"], "数据流/Data Flow section"),
        (["状态机", "state machine", "状态"], "状态机/State Machine section"),
        (["错误边界", "error boundary", "异常处理", "error handling"], "错误边界/Error Boundary section"),
        (["测试矩阵", "test matrix", "测试覆盖", "test coverage"], "测试矩阵/Test Matrix section"),
    ]
    for keywords, label in review_areas:
        found = any(kw in content_lower for kw in keywords)
        checks.append({
            "name": f"eng_review_covers_{label.split('/')[0].lower().replace(' ', '_')}",
            "passed": found,
            "detail": f"Section '{label}' {'found' if found else 'MISSING'} in ENG_REVIEW.md"
        })

    # Must contain P0/P1/P2 priority classification
    has_p0 = bool(re.search(r'\bP0\b', content))
    has_p1 = bool(re.search(r'\bP1\b', content))
    has_p2 = bool(re.search(r'\bP2\b', content))
    checks.append({
        "name": "eng_review_priority_classification",
        "passed": has_p0 and has_p1 and has_p2,
        "detail": f"P0={has_p0}, P1={has_p1}, P2={has_p2} — all three priority levels must be present"
    })

    # Must contain hidden assumptions section (implicit assumptions / 隐含假设)
    has_assumptions = any(kw in content_lower for kw in [
        "隐含假设", "implicit assumption", "hidden assumption", "假设", "assumption"
    ])
    checks.append({
        "name": "eng_review_implicit_assumptions",
        "passed": has_assumptions,
        "detail": f"Implicit/hidden assumptions section {'found' if has_assumptions else 'MISSING'} — this is a required proprietary deliverable"
    })

    return checks

def check_code_review(workspace):
    checks = []

    # Find CODE_REVIEW.md
    f = find_file(workspace, "CODE_REVIEW.md")
    if f is None:
        return [{"name": "code_review_file_exists", "passed": False, "detail": "CODE_REVIEW.md not found anywhere in workspace"}]
    
    content = read_file(f)
    content_lower = content.lower()

    checks.append({"name": "code_review_file_exists", "passed": True, "detail": f"Found at {f}"})

    # Must contain P0/P1/P2 classification
    has_p0 = bool(re.search(r'\bP0\b', content))
    has_p1 = bool(re.search(r'\bP1\b', content))
    has_p2 = bool(re.search(r'\bP2\b', content))
    checks.append({
        "name": "code_review_priority_labels",
        "passed": has_p0 and has_p1 and has_p2,
        "detail": f"P0={has_p0}, P1={has_p1}, P2={has_p2} — code review must classify defects by priority"
    })

    # Must have a numeric quality score (1-10)
    score_pattern = re.search(r'(?:quality\s*score|评分|得分|score)[^\d]*(\d+)\s*/\s*10', content_lower)
    score_pattern2 = re.search(r'(?:quality\s*score|评分|得分|score)[^\d]*(\d+)\s*(?:out of|\/)\s*10', content_lower)
    score_pattern3 = re.search(r'\b([1-9]|10)\s*/\s*10\b', content)
    has_score = bool(score_pattern or score_pattern2 or score_pattern3)
    checks.append({
        "name": "code_review_quality_score",
        "passed": has_score,
        "detail": f"Numeric quality score (X/10) {'found' if has_score else 'MISSING'} — required by /review workflow"
    })

    # Must mention auto-fix or manual fix of P0 issues
    has_autofix_mention = any(kw in content_lower for kw in [
        "auto-fix", "autofix", "auto fix", "自动修复", "fixed", "已修复", "applied fix", "修复"
    ])
    checks.append({
        "name": "code_review_autofix_mention",
        "passed": has_autofix_mention,
        "detail": f"Auto-fix/fix action {'mentioned' if has_autofix_mention else 'MISSING'} — P0 issues must be auto-fixed"
    })

    # Must mention human decision points
    has_human_decision = any(kw in content_lower for kw in [
        "human decision", "human review", "需要人工", "manual decision", "architecture decision",
        "业务逻辑", "业务决策", "人工决策", "requires human", "needs human", "mark"
    ])
    checks.append({
        "name": "code_review_human_decision_points",
        "passed": has_human_decision,
        "detail": f"Human decision/architecture decision points {'marked' if has_human_decision else 'MISSING'} — required by /review workflow"
    })

    # Check that actual bugs from the code are identified:
    # P0: no qty validation, cache not invalidated in cancel
    has_cache_bug = any(kw in content_lower for kw in [
        "cache", "缓存", "invalidat", "cancel", "取消"
    ])
    has_validation_bug = any(kw in content_lower for kw in [
        "validat", "验证", "negative", "负数", "qty", "quantity", "零"
    ])
    checks.append({
        "name": "code_review_identifies_cache_bug",
        "passed": has_cache_bug,
        "detail": f"Cache invalidation bug in handle_order_cancelled {'identified' if has_cache_bug else 'MISSED'}"
    })
    checks.append({
        "name": "code_review_identifies_validation_bug",
        "passed": has_validation_bug,
        "detail": f"Input validation bug (negative/zero qty) {'identified' if has_validation_bug else 'MISSED'}"
    })

    return checks

def check_retro(workspace):
    checks = []

    # Find RETRO.md
    f = find_file(workspace, "RETRO.md")
    if f is None:
        return [{"name": "retro_file_exists", "passed": False, "detail": "RETRO.md not found anywhere in workspace"}]
    
    content = read_file(f)
    content_lower = content.lower()

    checks.append({"name": "retro_file_exists", "passed": True, "detail": f"Found at {f}"})

    # Must have 4 required sections
    required_sections = [
        (["交付统计", "delivery stats", "completed", "功能", "features delivered", "deliverable"], "交付统计/Delivery Stats"),
        (["质量趋势", "quality trend", "test coverage", "测试覆盖", "bug density", "bug 密度"], "质量趋势/Quality Trends"),
        (["学习总结", "learning", "lessons", "新问题", "解法", "what we learned"], "学习总结/Learnings"),
        (["下周重点", "next week", "next sprint", "下一周", "priorities", "优先级"], "下周重点/Next Week Priorities"),
    ]
    for keywords, label in required_sections:
        found = any(kw in content_lower for kw in keywords)
        checks.append({
            "name": f"retro_section_{label.split('/')[0].lower().replace(' ', '_')}",
            "passed": found,
            "detail": f"Section '{label}' {'found' if found else 'MISSING'} in RETRO.md"
        })

    # Must list exactly 3 next-week priorities (look for numbered list near "next week" section)
    # Strategy: find numbered items (1., 2., 3.) or bullet count near next week section
    next_week_section = ""
    lines = content.split("\n")
    in_section = False
    for i, line in enumerate(lines):
        ll = line.lower()
        if any(kw in ll for kw in ["下周重点", "next week", "next sprint", "下一周"]):
            in_section = True
            next_week_section = "\n".join(lines[i:i+20])
            break

    if not in_section:
        # try to find numbered items in whole doc
        next_week_section = content

    numbered_items = re.findall(r'(?:^|\n)\s*(?:\d+[\.\)]\s|\*\s|-\s).+', next_week_section)
    has_three_priorities = len(numbered_items) >= 3
    checks.append({
        "name": "retro_next_week_has_three_priorities",
        "passed": has_three_priorities,
        "detail": f"Found {len(numbered_items)} priority items in next-week section; need at least 3 (per /retro spec)"
    })

    # Must reference actual sprint data (coverage numbers, bug counts, etc.)
    has_coverage_ref = bool(re.search(r'\d+\s*%', content))
    checks.append({
        "name": "retro_references_actual_sprint_data",
        "passed": has_coverage_ref,
        "detail": f"Sprint metrics (e.g., coverage %) {'referenced' if has_coverage_ref else 'MISSING'} — retro must be grounded in actual data"
    })

    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

    all_checks = []
    all_checks.extend(check_eng_review(workspace))
    all_checks.extend(check_code_review(workspace))
    all_checks.extend(check_retro(workspace))

    passed_count = sum(1 for c in all_checks if c["passed"])
    total = len(all_checks)
    score = round(passed_count / total, 3) if total > 0 else 0.0
    overall_passed = passed_count >= int(total * 0.75)  # 75% threshold

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": all_checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()