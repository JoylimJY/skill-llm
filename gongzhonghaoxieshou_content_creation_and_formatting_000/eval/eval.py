import sys
import os
import re
import json
from pathlib import Path

def find_article_draft(workspace):
    """Search for article_draft.md anywhere in workspace."""
    matches = list(Path(workspace).rglob("article_draft.md"))
    return matches[0] if matches else None

def load_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return None

def run_checks(workspace):
    checks = []
    score_total = 0.0

    # ── 1. File existence ────────────────────────────────────────────────────
    article_path = find_article_draft(workspace)
    file_exists = article_path is not None
    checks.append({
        "name": "article_draft.md exists",
        "passed": file_exists,
        "detail": f"Found at: {article_path}" if file_exists else "article_draft.md not found anywhere in workspace"
    })
    if not file_exists:
        # All remaining checks fail
        for name in [
            "Contains '# 标题：' heading",
            "Contains exactly 5 title options (covering all 5 types)",
            "Has 悬念型 title",
            "Has 痛点型 title",
            "Has 反差型 title",
            "Has 数字型 title",
            "Has 身份型 title",
            "Contains '## 封面建议' section",
            "Cover size is 900x500",
            "Contains '## 正文' section",
            "Opening matches one of the 5 爆款开头法",
            "Contains '## 配图建议' section",
            "Contains '## 排版建议' section",
            "排版建议 mentions 每段不超过5行",
            "排版建议 mentions 粗体使用/仅强调关键词",
            "排版建议 mentions 行间距/1.5",
            "No banned AI word '此外'",
            "No banned AI word '综上所述'",
            "No banned AI word '总的来说'",
            "No '不仅仅……而且……' pattern",
            "No three-part enumeration (第一/第二/第三)",
            "Article covers digital detox topic",
        ]:
            checks.append({"name": name, "passed": False, "detail": "File not found"})
        return checks

    content = load_file(article_path)
    if content is None:
        checks.append({"name": "File readable", "passed": False, "detail": "Could not read file"})
        return checks

    # ── 2. Main title heading ────────────────────────────────────────────────
    has_title_heading = bool(re.search(r'#\s*标题[：:]', content))
    checks.append({
        "name": "Contains '# 标题：' heading",
        "passed": has_title_heading,
        "detail": "Found '# 标题：' heading" if has_title_heading else "Missing '# 标题：' heading as per output format"
    })

    # ── 3. Five title options ────────────────────────────────────────────────
    # Look for explicit title type labels in the content
    title_type_patterns = {
        "悬念型": r'悬念型',
        "痛点型": r'痛点型',
        "反差型": r'反差型',
        "数字型": r'数字型',
        "身份型": r'身份型',
    }

    found_types = {}
    for type_name, pattern in title_type_patterns.items():
        found_types[type_name] = bool(re.search(pattern, content))

    num_types_found = sum(found_types.values())
    has_five_types = num_types_found == 5

    checks.append({
        "name": "Contains exactly 5 title options (covering all 5 types)",
        "passed": has_five_types,
        "detail": f"Found {num_types_found}/5 title types labeled. Types found: {[k for k,v in found_types.items() if v]}"
    })

    for type_name in ["悬念型", "痛点型", "反差型", "数字型", "身份型"]:
        checks.append({
            "name": f"Has {type_name} title",
            "passed": found_types[type_name],
            "detail": f"{'Found' if found_types[type_name] else 'Missing'} {type_name} title label in content"
        })

    # ── 4. Cover section ─────────────────────────────────────────────────────
    has_cover_section = bool(re.search(r'##\s*封面建议', content))
    checks.append({
        "name": "Contains '## 封面建议' section",
        "passed": has_cover_section,
        "detail": "Found '## 封面建议'" if has_cover_section else "Missing '## 封面建议' section"
    })

    # Cover size must be 900x500 (NOT 900x383 from distractor)
    has_correct_size = bool(re.search(r'900\s*[xX×]\s*500', content))
    checks.append({
        "name": "Cover size is 900x500",
        "passed": has_correct_size,
        "detail": "Found 900x500 cover size (correct per SKILL.md)" if has_correct_size else "Missing or incorrect cover size. Expected 900x500 (not 900x383 from outdated distractor)"
    })

    # ── 5. 正文 section ──────────────────────────────────────────────────────
    has_body = bool(re.search(r'##\s*正文', content))
    checks.append({
        "name": "Contains '## 正文' section",
        "passed": has_body,
        "detail": "Found '## 正文' section" if has_body else "Missing '## 正文' section"
    })

    # ── 6. Opening method check ──────────────────────────────────────────────
    opening_patterns = [
        r'你是不是也',          # 痛点开头
        r'那天[，,]',           # 故事开头
        r'根据[^，,。\n]{0,10}[调查研究数据]',  # 数据开头
        r'很多人以为[，,].*?但其实',  # 反差开头
        r'答案可能和你想的不一样',  # 悬念开头
        r'你有没有过',           # 痛点变体
        r'说实话[，,]',          # 口语化开头变体
    ]
    body_section = content
    # Try to isolate body section
    body_match = re.search(r'##\s*正文(.*?)(?:##\s*配图建议|##\s*排版建议|$)', content, re.DOTALL)
    if body_match:
        body_section = body_match.group(1)

    # Check for opening type - look in first ~300 chars of body or entire content
    first_part = body_section[:400] if len(body_section) > 400 else body_section
    has_valid_opening = any(re.search(p, first_part) for p in opening_patterns)

    # Also check by label
    has_opening_label = bool(re.search(r'(痛点开头|故事开头|数据开头|反差开头|悬念开头|开篇)', content))

    opening_ok = has_valid_opening or has_opening_label
    checks.append({
        "name": "Opening matches one of the 5 爆款开头法",
        "passed": opening_ok,
        "detail": "Found valid opening pattern or label" if opening_ok else "Opening does not match any of the 5 爆款开头法 from 写作技巧.md"
    })

    # ── 7. 配图建议 section ──────────────────────────────────────────────────
    has_image = bool(re.search(r'##\s*配图建议', content))
    checks.append({
        "name": "Contains '## 配图建议' section",
        "passed": has_image,
        "detail": "Found '## 配图建议'" if has_image else "Missing '## 配图建议' section"
    })

    # ── 8. 排版建议 section ──────────────────────────────────────────────────
    has_layout = bool(re.search(r'##\s*排版建议', content))
    checks.append({
        "name": "Contains '## 排版建议' section",
        "passed": has_layout,
        "detail": "Found '## 排版建议'" if has_layout else "Missing '## 排版建议' section"
    })

    # Layout rule: 每段不超过5行
    layout_section = ""
    layout_match = re.search(r'##\s*排版建议(.*?)(?:##|$)', content, re.DOTALL)
    if layout_match:
        layout_section = layout_match.group(1)

    has_5lines = bool(re.search(r'(每段不超过5行|每段.*?5行|段落.*?5行)', layout_section or content))
    checks.append({
        "name": "排版建议 mentions 每段不超过5行",
        "passed": has_5lines,
        "detail": "Found paragraph length rule" if has_5lines else "Missing '每段不超过5行' in 排版建议"
    })

    has_bold = bool(re.search(r'(粗体|仅强调关键词|强调关键词)', layout_section or content))
    checks.append({
        "name": "排版建议 mentions 粗体使用/仅强调关键词",
        "passed": has_bold,
        "detail": "Found bold usage rule" if has_bold else "Missing bold usage rule in 排版建议"
    })

    has_spacing = bool(re.search(r'(行间距|1\.5倍|1\.5\s*倍)', layout_section or content))
    checks.append({
        "name": "排版建议 mentions 行间距/1.5",
        "passed": has_spacing,
        "detail": "Found line spacing rule (1.5x)" if has_spacing else "Missing '行间距：建议1.5倍' in 排版建议"
    })

    # ── 9. Anti-AI checks ────────────────────────────────────────────────────
    banned_words = {
        "此外": r'此外',
        "综上所述": r'综上所述',
        "总的来说": r'总的来说',
    }
    for word, pattern in banned_words.items():
        found = bool(re.search(pattern, content))
        checks.append({
            "name": f"No banned AI word '{word}'",
            "passed": not found,
            "detail": f"PASS: '{word}' not found in article" if not found else f"FAIL: Banned AI word '{word}' found in article (violates 去AI味指南.md)"
        })

    # Check for "不仅仅……而且……" pattern
    has_bujinjin = bool(re.search(r'不仅仅.{0,20}而且', content))
    checks.append({
        "name": "No '不仅仅……而且……' pattern",
        "passed": not has_bujinjin,
        "detail": "PASS: Forbidden pattern not found" if not has_bujinjin else "FAIL: '不仅仅……而且……' pattern found (violates 去AI味指南.md)"
    })

    # Check for three-part enumeration (第一/第二/第三 used as structure)
    has_three_part = bool(re.search(r'第一[，,、].{0,50}第二[，,、].{0,50}第三[，,、]', content, re.DOTALL))
    checks.append({
        "name": "No three-part enumeration (第一/第二/第三)",
        "passed": not has_three_part,
        "detail": "PASS: Three-part enumeration pattern not found" if not has_three_part else "FAIL: 三段式列举 (第一/第二/第三) found (violates 去AI味指南.md)"
    })

    # ── 10. Topic relevance ─────────────────────────────────────────────────
    digital_detox_keywords = [
        r'手机', r'数字', r'屏幕', r'刷手机', r'排毒', r'戒手机', r'注意力',
        r'digital', r'detox', r'健康', r'依赖'
    ]
    topic_matches = sum(1 for kw in digital_detox_keywords if re.search(kw, content, re.IGNORECASE))
    on_topic = topic_matches >= 3
    checks.append({
        "name": "Article covers digital detox topic",
        "passed": on_topic,
        "detail": f"Found {topic_matches}/3 required topic keywords" + (", on topic" if on_topic else ", article may be off-topic")
    })

    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

    try:
        checks = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_script_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # Scoring: weighted
    weights = {
        "article_draft.md exists": 5,
        "Contains '# 标题：' heading": 4,
        "Contains exactly 5 title options (covering all 5 types)": 6,
        "Has 悬念型 title": 3,
        "Has 痛点型 title": 3,
        "Has 反差型 title": 3,
        "Has 数字型 title": 3,
        "Has 身份型 title": 3,
        "Contains '## 封面建议' section": 4,
        "Cover size is 900x500": 8,  # Tricky - distractor has 900x383
        "Contains '## 正文' section": 3,
        "Opening matches one of the 5 爆款开头法": 6,
        "Contains '## 配图建议' section": 4,
        "Contains '## 排版建议' section": 4,
        "排版建议 mentions 每段不超过5行": 5,
        "排版建议 mentions 粗体使用/仅强调关键词": 4,
        "排版建议 mentions 行间距/1.5": 4,
        "No banned AI word '此外'": 6,
        "No banned AI word '综上所述'": 5,
        "No banned AI word '总的来说'": 5,
        "No '不仅仅……而且……' pattern": 5,
        "No three-part enumeration (第一/第二/第三)": 5,
        "Article covers digital detox topic": 4,
    }
    total_weight = sum(weights.values())
    earned = sum(weights.get(c["name"], 1) for c in checks if c["passed"])
    score = round(earned / total_weight, 4)

    # Must pass critical checks to overall pass
    critical_checks = [
        "article_draft.md exists",
        "Contains exactly 5 title options (covering all 5 types)",
        "Cover size is 900x500",
        "No banned AI word '此外'",
        "No banned AI word '综上所述'",
        "Contains '## 封面建议' section",
        "Contains '## 排版建议' section",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )

    passed = critical_passed and score >= 0.72

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()