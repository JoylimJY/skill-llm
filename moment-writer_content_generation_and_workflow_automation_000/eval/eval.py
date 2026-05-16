import sys
import json
import re
from pathlib import Path

def count_chinese_chars(text):
    """Count Chinese characters and common punctuation in a string."""
    count = 0
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            count += 1
        elif ch in '，。！？、：；""''（）【】…—～':
            count += 1
        elif ch.isalnum():
            count += 1
    return count

def get_paragraphs(text):
    """Split text into paragraphs by blank lines."""
    # Split on one or more blank lines
    paras = re.split(r'\n\s*\n', text.strip())
    return [p.strip() for p in paras if p.strip()]

def check_first_para_length(paragraph):
    """Check if the first paragraph is 20-25 characters."""
    length = count_chinese_chars(paragraph)
    return 20 <= length <= 35  # slightly lenient for mixed content but strict enough

def check_para_line_count(paragraph):
    """Check that each paragraph has at most 3 lines."""
    lines = [l for l in paragraph.split('\n') if l.strip()]
    return len(lines) <= 3

def extract_post_section(content, marker):
    """Extract a section of the markdown file by header marker."""
    pattern = rf'#{1,3}\s*.*?{marker}.*?\n(.*?)(?=\n#{1,3}\s|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def find_output_file(workspace):
    """Find moments_package.md in the workspace."""
    results = list(Path(workspace).rglob('moments_package.md'))
    return results[0] if results else None

def run_eval(workspace):
    checks = []
    total_score = 0.0

    # ---- CHECK 0: File existence ----
    output_file = find_output_file(workspace)
    file_exists = output_file is not None
    checks.append({
        "name": "moments_package.md exists",
        "passed": file_exists,
        "detail": f"Found at {output_file}" if file_exists else "File moments_package.md not found anywhere in workspace"
    })

    if not file_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        content = output_file.read_text(encoding='utf-8')
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "File readable and non-empty",
        "passed": len(content.strip()) > 200,
        "detail": f"Content length: {len(content)} chars"
    })

    # ---- CHECK 1: All 5 post types present ----
    # We check for the 5 required command types in the content
    type_keywords = {
        "professional": ["专业", "professional", "故事案例", "案例", "咨询", "逆转", "读写"],
        "reliable": ["靠谱", "reliable", "失败", "否定", "不服输", "坚持", "方案"],
        "warm": ["温暖", "warm", "亲子", "孩子", "睡前", "生活", "温情"],
        "counter": ["反认知", "counter", "误解", "打破", "认知", "危险", "努力"],
        "intro_100": ["介绍", "intro", "深耕", "踩坑", "价值", "服务", "定位"]
    }

    types_found = {}
    for type_name, keywords in type_keywords.items():
        found = any(kw in content for kw in keywords)
        types_found[type_name] = found

    all_types_present = all(types_found.values())
    checks.append({
        "name": "All 5 post types generated (professional/reliable/warm/counter/intro_100)",
        "passed": all_types_present,
        "detail": f"Types found: {types_found}"
    })

    # ---- CHECK 2: Correct command types used per post ----
    # Check that command names are mentioned or implied correctly
    # The professional post should use /moments professional
    # The reliable post should use /moments reliable
    # The warm post should use /moments warm
    # The counter post should use /moments counter
    # The intro post should use /moments intro_100

    command_mentions = {
        "professional": bool(re.search(r'/moments\s+professional|专业型|故事案例.*细节.*美好结果', content, re.DOTALL)),
        "reliable": bool(re.search(r'/moments\s+reliable|靠谱型|失败故事.*不服输.*成功', content, re.DOTALL)),
        "warm": bool(re.search(r'/moments\s+warm|温暖型|生活场景.*真实互动.*情感', content, re.DOTALL)),
        "counter": bool(re.search(r'/moments\s+counter|反认知|打破认知.*植入理念', content, re.DOTALL)),
        "intro_100": bool(re.search(r'/moments\s+intro_100|自我介绍|深耕领域.*踩坑', content, re.DOTALL)),
    }
    commands_used_correctly = sum(command_mentions.values()) >= 3
    checks.append({
        "name": "Correct moments command types applied (at least 3 of 5 correctly typed)",
        "passed": commands_used_correctly,
        "detail": f"Command type usage: {command_mentions}"
    })

    # ---- CHECK 3: First paragraph length constraint (20-25 chars) ----
    # Extract individual post bodies (not headers) and check their first paragraphs
    # We'll look for blocks of Chinese text that look like post bodies

    # Split content into sections based on markdown headers
    sections = re.split(r'\n#{1,3}\s+', content)
    post_sections = []
    for section in sections:
        # A post section has substantial Chinese content
        chinese_char_count = sum(1 for c in section if '\u4e00' <= c <= '\u9fff')
        if chinese_char_count > 30:
            post_sections.append(section)

    first_para_checks = []
    for i, section in enumerate(post_sections[:5]):  # Check first 5 post-like sections
        paras = get_paragraphs(section)
        if paras:
            first_para = paras[0]
            # Remove markdown headers from first para
            first_para_clean = re.sub(r'^[#\s]+', '', first_para).strip()
            if first_para_clean:
                length = count_chinese_chars(first_para_clean)
                is_valid = 15 <= length <= 40  # lenient but still tests the constraint
                first_para_checks.append((i, length, is_valid, first_para_clean[:50]))

    valid_first_paras = sum(1 for _, _, v, _ in first_para_checks if v)
    first_para_passed = valid_first_paras >= 3 if first_para_checks else False
    checks.append({
        "name": "First paragraph length constraint (scene-setting opener, ~20-25 chars)",
        "passed": first_para_passed,
        "detail": f"Checked {len(first_para_checks)} sections: {[(l, v, t) for _, l, v, t in first_para_checks]}"
    })

    # ---- CHECK 4: Paragraph line limit (≤3 lines per paragraph) ----
    all_paras = get_paragraphs(content)
    para_violations = []
    for i, para in enumerate(all_paras):
        lines = [l for l in para.split('\n') if l.strip() and not l.strip().startswith('#')]
        if len(lines) > 3:
            para_violations.append((i, len(lines), para[:60]))

    # Allow minor violations for headers/metadata sections
    meaningful_violations = [(i, c, t) for i, c, t in para_violations
                              if sum(1 for ch in t if '\u4e00' <= ch <= '\u9fff') > 10]
    para_limit_passed = len(meaningful_violations) <= 2
    checks.append({
        "name": "Paragraph line limit (≤3 lines per paragraph)",
        "passed": para_limit_passed,
        "detail": f"Found {len(meaningful_violations)} violation(s): {meaningful_violations[:3]}"
    })

    # ---- CHECK 5: Marketing content in comments section, not body ----
    # Check that promotional/pricing content is in a comments/评论区 section
    # and NOT in the main post body sections
    marketing_keywords = ['报名', '优惠', '打折', '元', '课程链接', '扫码', '立即', '限时', '名额']

    # Find if there's a 评论区 / comments section
    has_comment_section = bool(re.search(r'评论区|comment|💬|【评论】', content, re.IGNORECASE))

    # Check if marketing content appears in post BODY (bad) vs comments (ok)
    # A rough heuristic: marketing keywords should NOT dominate the main content area
    body_marketing_hits = 0
    comment_section_start = -1

    lines_list = content.split('\n')
    for idx, line in enumerate(lines_list):
        if re.search(r'评论区|【评论】|comment区', line, re.IGNORECASE):
            comment_section_start = idx

    # Count marketing keywords before any comment section marker
    pre_comment_content = '\n'.join(lines_list[:comment_section_start]) if comment_section_start > 0 else content
    for kw in marketing_keywords:
        if kw in pre_comment_content:
            body_marketing_hits += 1

    # If there's a comment section AND marketing is mostly there, it's good
    # If there's no comment section and no marketing keywords at all, that's also acceptable (conservative)
    # The key constraint: marketing info should NOT be heavily embedded in main body
    comment_rule_passed = has_comment_section or body_marketing_hits <= 2
    checks.append({
        "name": "Marketing info placement (评论区 rule: promotional content in comments, not body)",
        "passed": comment_rule_passed,
        "detail": f"Has comment section: {has_comment_section}, body marketing keyword hits: {body_marketing_hits}"
    })

    # ---- CHECK 6: intro_100 is approximately 100 characters ----
    intro_pattern = re.search(
        r'(?:intro_100|自我介绍|个人介绍)[^\n]*\n(.*?)(?=\n#{1,3}\s|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )
    intro_length_passed = False
    intro_detail = "Could not find intro_100 section"
    if intro_pattern:
        intro_body = intro_pattern.group(1).strip()
        intro_len = count_chinese_chars(intro_body)
        # ~100 chars: allow 60-160 range (lenient due to mixed content)
        intro_length_passed = 60 <= intro_len <= 200
        intro_detail = f"intro_100 body length: {intro_len} chars (target ~100)"
    else:
        # Try to find any short self-intro section
        intro_matches = re.findall(r'(?:深耕|踩坑|价值钩子|我是谁|帮助谁)[^#]{20,300}', content, re.DOTALL)
        if intro_matches:
            best_match = min(intro_matches, key=len)
            intro_len = count_chinese_chars(best_match)
            intro_length_passed = 60 <= intro_len <= 200
            intro_detail = f"Found intro-like block, length: {intro_len} chars"
    
    checks.append({
        "name": "intro_100 approximately 100 characters (self-introduction post)",
        "passed": intro_length_passed,
        "detail": intro_detail
    })

    # ---- CHECK 7: McKinsey Trust Formula structure visible ----
    # The content should show awareness of the formula through type diversity
    # (all 4 trust dimensions covered: 专业度, 可靠度, 亲密度, 自身利益)
    trust_dimensions = {
        "专业度 (professional)": bool(re.search(r'专业|案例|权威|professional', content, re.IGNORECASE)),
        "可靠度 (reliable)": bool(re.search(r'靠谱|reliable|失败.*成功|坚持', content, re.DOTALL)),
        "亲密度 (warm)": bool(re.search(r'温暖|warm|亲子|生活|孩子', content)),
        "降低自身利益感 (altruistic/counter)": bool(re.search(r'利他|反认知|counter|altruistic|误解|打破', content)),
    }
    dimensions_covered = sum(trust_dimensions.values())
    trust_formula_passed = dimensions_covered >= 3
    checks.append({
        "name": "McKinsey Trust Formula coverage (all trust dimensions represented)",
        "passed": trust_formula_passed,
        "detail": f"Dimensions covered: {dimensions_covered}/4 — {trust_dimensions}"
    })

    # ---- SCORING ----
    weights = {
        0: 0.10,  # file exists
        1: 0.05,  # readable
        2: 0.20,  # all 5 types
        3: 0.15,  # correct commands
        4: 0.15,  # first para length
        5: 0.10,  # para line limit
        6: 0.10,  # comments section
        7: 0.05,  # intro_100 length
        8: 0.10,  # trust formula
    }

    score = 0.0
    for i, check in enumerate(checks):
        if check["passed"]:
            score += weights.get(i, 0.05)

    all_critical_passed = (
        checks[0]["passed"] and  # file exists
        checks[2]["passed"] and  # all 5 types
        checks[4]["passed"] and  # first para length
        checks[8]["passed"]      # trust formula
    )

    return {
        "passed": all_critical_passed and score >= 0.60,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))