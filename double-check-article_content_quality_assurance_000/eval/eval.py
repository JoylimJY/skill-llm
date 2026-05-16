import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    score = 0.0

    # Find the output report file
    report_path = None
    candidates = list(Path(workspace).rglob("article_review_report.md"))
    if candidates:
        report_path = candidates[0]

    if not report_path or not report_path.exists():
        checks.append({
            "name": "report_file_exists",
            "passed": False,
            "detail": "未找到 article_review_report.md 文件"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "report_file_exists",
        "passed": True,
        "detail": f"找到报告文件: {report_path}"
    })
    score += 0.1

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "report_readable",
            "passed": False,
            "detail": f"无法读取文件: {e}"
        })
        return {"passed": False, "score": score, "checks": checks}

    # CHECK 1: Top-level template header
    has_main_header = "## 文章检查报告" in content
    checks.append({
        "name": "main_header_present",
        "passed": has_main_header,
        "detail": "检查顶级标题 '## 文章检查报告'" if has_main_header else "缺少顶级标题 '## 文章检查报告'"
    })
    if has_main_header:
        score += 0.05

    # CHECK 2: All three section headers present
    sec1 = "### 第一步：错别字检查" in content
    sec2 = "### 第二步：表达检查" in content
    sec3 = "### 第三步：改进建议" in content

    checks.append({
        "name": "section1_header",
        "passed": sec1,
        "detail": "'### 第一步：错别字检查' 标题" + ("存在" if sec1 else "缺失")
    })
    checks.append({
        "name": "section2_header",
        "passed": sec2,
        "detail": "'### 第二步：表达检查' 标题" + ("存在" if sec2 else "缺失")
    })
    checks.append({
        "name": "section3_header",
        "passed": sec3,
        "detail": "'### 第三步：改进建议' 标题" + ("存在" if sec3 else "缺失")
    })
    if sec1: score += 0.05
    if sec2: score += 0.05
    if sec3: score += 0.05

    # CHECK 3: Bracket-label sub-headers inside sections
    has_typo_label = "【错别字修正】" in content
    has_expr_label = "【表达修正】" in content
    has_suggest_label = "【改进建议】" in content

    checks.append({
        "name": "bracket_label_typo",
        "passed": has_typo_label,
        "detail": "'【错别字修正】' 标签" + ("存在" if has_typo_label else "缺失")
    })
    checks.append({
        "name": "bracket_label_expression",
        "passed": has_expr_label,
        "detail": "'【表达修正】' 标签" + ("存在" if has_expr_label else "缺失")
    })
    checks.append({
        "name": "bracket_label_suggestion",
        "passed": has_suggest_label,
        "detail": "'【改进建议】' 标签" + ("存在" if has_suggest_label else "缺失")
    })
    if has_typo_label: score += 0.05
    if has_expr_label: score += 0.05
    if has_suggest_label: score += 0.05

    # CHECK 4: Typo corrections - must identify known planted errors
    # "以经" → "已经"
    typo1_found = "以经" in content and "已经" in content
    # "我们们" → "我们"
    typo2_found = "我们们" in content and "我们" in content
    # "在见" → "再见"
    typo3_found = "在见" in content and "再见" in content

    checks.append({
        "name": "typo_yijing_identified",
        "passed": typo1_found,
        "detail": "识别到错别字 '以经'→'已经'" if typo1_found else "未识别到错别字 '以经'→'已经'"
    })
    checks.append({
        "name": "typo_women_identified",
        "passed": typo2_found,
        "detail": "识别到多字错误 '我们们'→'我们'" if typo2_found else "未识别到多字错误 '我们们'→'我们'"
    })
    checks.append({
        "name": "typo_zaijian_identified",
        "passed": typo3_found,
        "detail": "识别到错别字 '在见'→'再见'" if typo3_found else "未识别到错别字 '在见'→'再见'"
    })
    if typo1_found: score += 0.1
    if typo2_found: score += 0.1
    if typo3_found: score += 0.1

    # CHECK 5: Expression issues - must catch broken sentence or logical non-sequitur
    # The paragraph about quantum computing is a logical non-sequitur
    # The missing punctuation (sentence without 。) should also be noted
    quantum_flagged = "量子" in content
    missing_punct_flagged = any(kw in content for kw in ["标点", "句号", "缺失", "结尾", "无句号", "没有句号", "punctuation"])

    checks.append({
        "name": "expression_quantum_nonsequitur",
        "passed": quantum_flagged,
        "detail": "识别到量子计算段落的逻辑偏题问题" if quantum_flagged else "未识别到量子计算段落的逻辑偏题问题"
    })
    checks.append({
        "name": "expression_missing_punctuation",
        "passed": missing_punct_flagged,
        "detail": "识别到缺少标点符号的问题" if missing_punct_flagged else "未识别到缺少标点符号的问题"
    })
    if quantum_flagged: score += 0.1
    if missing_punct_flagged: score += 0.05

    # CHECK 6: Improvement suggestions must be non-empty list
    suggest_section_match = re.search(r'【改进建议】(.*?)(?=###|\Z)', content, re.DOTALL)
    has_suggest_content = False
    if suggest_section_match:
        suggest_text = suggest_section_match.group(1).strip()
        has_numbered = bool(re.search(r'\d+[\.\、]', suggest_text))
        has_suggest_content = len(suggest_text) > 20 and has_numbered
    checks.append({
        "name": "suggestions_nonempty_numbered",
        "passed": has_suggest_content,
        "detail": "改进建议部分包含编号建议列表" if has_suggest_content else "改进建议部分为空或无编号列表"
    })
    if has_suggest_content: score += 0.1

    # CHECK 7: Paragraph location annotation in typo section (位置：第X段)
    has_location = bool(re.search(r'位置[：:]\s*第[一二三四五六七八九十\d]+段', content))
    checks.append({
        "name": "typo_location_annotation",
        "passed": has_location,
        "detail": "错别字修正包含段落位置标注（位置：第X段）" if has_location else "错别字修正缺少段落位置标注格式"
    })
    if has_location: score += 0.05

    score = min(score, 1.0)
    passed = (
        has_main_header and sec1 and sec2 and sec3 and
        has_typo_label and has_expr_label and has_suggest_label and
        typo1_found and typo2_found and typo3_found
    )

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))