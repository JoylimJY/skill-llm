import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = sys.argv[1]
    checks = []

    # Find the output file
    candidates = list(Path(workspace).rglob("content_package.md"))
    if not candidates:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [check("file_exists", False, "content_package.md not found anywhere in workspace")]
        }))
        return

    target = candidates[0]
    try:
        content = target.read_text(encoding="utf-8")
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [check("file_readable", False, f"Could not read file: {e}")]
        }))
        return

    # ---- CHECK 1: File is non-trivially long (not a stub) ----
    word_count = len(content.split())
    c1 = check("content_length_sufficient", word_count >= 200,
               f"Word count: {word_count} (need >= 200 to be a real deliverable, not a stub)")
    checks.append(c1)

    # ---- CHECK 2: Role switch declaration for Xiaohongshu Specialist ----
    # Must contain: [切换为：小红书专家 📕] or close variant with bracket syntax
    xhs_role_pattern = re.search(r'\[切换为[：:]\s*小红书专家\s*📕\]', content)
    c2 = check("xiaohongshu_role_declaration", bool(xhs_role_pattern),
               f"Must contain '[切换为：小红书专家 📕]' role switch declaration. Found: {bool(xhs_role_pattern)}")
    checks.append(c2)

    # ---- CHECK 3: Xiaohongshu post has required structural elements ----
    # Must have: 标题, 正文, 标签/hashtags with #, 封面图建议, 发布时间建议
    has_title = bool(re.search(r'标题', content))
    has_body = bool(re.search(r'正文', content))
    has_tags = bool(re.search(r'#[\w\u4e00-\u9fff]+', content))
    has_cover = bool(re.search(r'封面图', content))
    has_time = bool(re.search(r'发布时间', content))

    xhs_structure_pass = has_title and has_body and has_tags and has_cover and has_time
    c3 = check("xiaohongshu_structure_complete",
               xhs_structure_pass,
               f"XHS structure check — 标题:{has_title}, 正文:{has_body}, 标签(#):{has_tags}, 封面图:{has_cover}, 发布时间:{has_time}")
    checks.append(c3)

    # ---- CHECK 4: Hashtags are proper Xiaohongshu format (at least 3 hashtags) ----
    hashtags = re.findall(r'#[\w\u4e00-\u9fff]+', content)
    c4 = check("xiaohongshu_hashtag_count", len(hashtags) >= 3,
               f"Found {len(hashtags)} hashtags (need >= 3 for XHS format): {hashtags[:8]}")
    checks.append(c4)

    # ---- CHECK 5: Role switch declaration for Whimsy Injector ----
    whimsy_role_pattern = re.search(r'\[切换为[：:]\s*趣味注入师\s*✨\]', content)
    c5 = check("whimsy_injector_role_declaration", bool(whimsy_role_pattern),
               f"Must contain '[切换为：趣味注入师 ✨]' role switch declaration. Found: {bool(whimsy_role_pattern)}")
    checks.append(c5)

    # ---- CHECK 6: Whimsy Injector section exists and is meaningfully distinct ----
    # Find position of whimsy section
    whimsy_idx = content.find("趣味注入师")
    xhs_idx = content.find("小红书专家")
    growth_idx_search = re.search(r'增长黑客', content)

    whimsy_has_content = False
    if whimsy_idx > -1:
        # Check there's substantial text in the whimsy section (at least 50 chars after role declaration)
        whimsy_section = content[whimsy_idx:]
        whimsy_has_content = len(whimsy_section.strip()) > 100
    c6 = check("whimsy_injector_content_present", whimsy_has_content,
               f"Whimsy Injector section found at index {whimsy_idx} with substantial content: {whimsy_has_content}")
    checks.append(c6)

    # ---- CHECK 7: Growth Hacker role declaration ----
    growth_role_pattern = re.search(r'\[切换为[：:]\s*增长黑客\s*🚀\]', content)
    c7 = check("growth_hacker_role_declaration", bool(growth_role_pattern),
               f"Must contain '[切换为：增长黑客 🚀]' role switch declaration. Found: {bool(growth_role_pattern)}")
    checks.append(c7)

    # ---- CHECK 8: Growth Hacker deliverables present ----
    # Must include: 增长实验方案 OR 实验方案, 渠道策略, 关键指标 OR KPI
    has_experiment = bool(re.search(r'增长实验|实验方案|增长实验方案', content))
    has_channel_strategy = bool(re.search(r'渠道策略|渠道', content))
    has_kpi = bool(re.search(r'关键指标|KPI|指标追踪', content))

    growth_deliverables_pass = has_experiment and has_channel_strategy and has_kpi
    c8 = check("growth_hacker_deliverables_complete",
               growth_deliverables_pass,
               f"Growth Hacker deliverables — 增长实验方案:{has_experiment}, 渠道策略:{has_channel_strategy}, 关键指标:{has_kpi}")
    checks.append(c8)

    # ---- CHECK 9: Content is EcoThread specific (not generic) ----
    has_ecothread = bool(re.search(r'EcoThread|eco.*thread|可持续时尚|环保', content, re.IGNORECASE))
    c9 = check("content_is_brand_specific", has_ecothread,
               f"Content references EcoThread or sustainable fashion brand context: {has_ecothread}")
    checks.append(c9)

    # ---- CHECK 10: Three distinct sections exist (order: XHS -> Whimsy -> Growth) ----
    # Verify ordering: XHS section comes before Whimsy, which comes before Growth
    xhs_pos = content.find("小红书专家")
    whimsy_pos = content.find("趣味注入师")
    growth_pos = content.find("增长黑客")
    
    order_correct = (xhs_pos > -1 and whimsy_pos > -1 and growth_pos > -1 and
                     xhs_pos < whimsy_pos < growth_pos)
    c10 = check("three_sections_correct_order", order_correct,
                f"Section order XHS({xhs_pos}) < Whimsy({whimsy_pos}) < Growth({growth_pos}): {order_correct}")
    checks.append(c10)

    # ---- CHECK 11: Whimsy section references the fun/personality improvements (具体建议) ----
    # The Whimsy Injector deliverable spec says "带具体的趣味元素建议"
    has_whimsy_specifics = False
    if whimsy_pos > -1:
        whimsy_content = content[whimsy_pos:whimsy_pos+1500]
        # Should have emojis, creative language, or explicit "趣味" annotations
        emoji_count_in_whimsy = len(re.findall(r'[\U0001F300-\U0001F9FF]|[\u2600-\u27FF]', whimsy_content))
        has_whimsy_specifics = emoji_count_in_whimsy >= 2 or bool(re.search(r'趣味|创意|有趣|生动|个性', whimsy_content))
    c11 = check("whimsy_section_has_fun_elements", has_whimsy_specifics,
                f"Whimsy section has emoji/fun annotations: {has_whimsy_specifics}")
    checks.append(c11)

    # ---- SCORING ----
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)

    # Must pass critical checks to be considered passing overall
    critical_checks = ["file_exists" if False else None,
                       "xiaohongshu_role_declaration",
                       "growth_hacker_role_declaration",
                       "three_sections_correct_order",
                       "xiaohongshu_structure_complete"]
    critical_results = {c["name"]: c["passed"] for c in checks}
    critical_pass = all(critical_results.get(name, False) for name in critical_checks if name)

    overall_passed = critical_pass and score >= 0.72

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()