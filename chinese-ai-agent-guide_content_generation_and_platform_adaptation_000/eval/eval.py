import sys
import json
import re
from pathlib import Path

def find_output_file(workspace, filename):
    results = list(Path(workspace).rglob(filename))
    return results[0] if results else None

def count_emoji_in_paragraph(paragraph):
    # Unicode emoji ranges (broad)
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001F9FF"
        "\U00002600-\U000027BF"
        "\U0000FE00-\U0000FE0F"
        "\U00002702-\U000027B0"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "]+",
        re.UNICODE
    )
    return len(emoji_pattern.findall(paragraph))

def check_xiaohongshu(content):
    checks = []
    
    # Title must contain clickbait words
    clickbait_words = ["绝了", "家人们", "谁懂啊", "绝绝子", "真的会"]
    first_line = content.strip().split('\n')[0]
    has_clickbait = any(w in first_line for w in clickbait_words)
    checks.append({
        "name": "xhs_clickbait_title",
        "passed": has_clickbait,
        "detail": f"Title clickbait check. First line: '{first_line[:80]}'. Found clickbait: {has_clickbait}"
    })
    
    # Must have numbered structure (1. 2. 3.)
    has_numbered = bool(re.search(r'[123]\s*[\.、]', content))
    checks.append({
        "name": "xhs_numbered_structure",
        "passed": has_numbered,
        "detail": f"Numbered list structure (1. 2. 3.) found: {has_numbered}"
    })
    
    # Must have trailing hashtags
    has_tags = bool(re.search(r'#[\u4e00-\u9fffA-Za-z0-9]+', content))
    checks.append({
        "name": "xhs_hashtags",
        "passed": has_tags,
        "detail": f"Trailing hashtag tags found: {has_tags}"
    })
    
    # Paragraphs must have 2-3 emoji each
    # Split into non-empty paragraphs
    paragraphs = [p.strip() for p in content.strip().split('\n\n') if p.strip() and len(p.strip()) > 10]
    # Filter out single-line tag footers
    body_paragraphs = [p for p in paragraphs if not re.match(r'^#', p.strip())]
    
    emoji_per_para_ok = 0
    emoji_details = []
    for i, para in enumerate(body_paragraphs[:5]):  # check first 5 body paragraphs
        count = count_emoji_in_paragraph(para)
        ok = 2 <= count <= 3
        if ok:
            emoji_per_para_ok += 1
        emoji_details.append(f"para{i+1}: {count} emoji")
    
    # Pass if majority of checked paragraphs have 2-3 emoji
    emoji_ok = emoji_per_para_ok >= max(1, len(body_paragraphs[:5]) // 2)
    checks.append({
        "name": "xhs_emoji_per_paragraph",
        "passed": emoji_ok,
        "detail": f"2-3 emoji per paragraph check: {', '.join(emoji_details)}. Passed paragraphs: {emoji_per_para_ok}/{len(body_paragraphs[:5])}"
    })
    
    # Check for product content relevance (错题本 or 答疑 or 报告)
    has_product_content = any(kw in content for kw in ["错题", "答疑", "报告", "学习", "复习"])
    checks.append({
        "name": "xhs_product_relevance",
        "passed": has_product_content,
        "detail": f"Product content mentioned (错题/答疑/报告/学习/复习): {has_product_content}"
    })
    
    return checks

def check_jike(content):
    checks = []
    
    # Short sentences, one sentence per paragraph (no long unbroken paragraphs)
    # Each paragraph should be short (< 50 chars ideally, definitely < 100)
    lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
    
    # First line must be eye-catching (short, punchy)
    first_line = lines[0] if lines else ""
    has_punchy_opener = len(first_line) <= 30 or any(w in first_line for w in ["！", "？", "。", "…", "真的", "终于", "居然", "原来"])
    checks.append({
        "name": "jike_punchy_opener",
        "passed": has_punchy_opener,
        "detail": f"First line is punchy/short: '{first_line[:60]}'"
    })
    
    # No long unbroken paragraphs (no paragraph > 80 chars without line break)
    long_paragraphs = [p for p in content.split('\n\n') if len(p.strip()) > 100]
    no_long_blocks = len(long_paragraphs) == 0
    checks.append({
        "name": "jike_no_long_paragraphs",
        "passed": no_long_blocks,
        "detail": f"No long unbroken paragraph blocks (>100 chars): {no_long_blocks}. Long blocks found: {len(long_paragraphs)}"
    })
    
    # Must end with a question to encourage interaction
    last_meaningful = content.strip()
    has_question_end = last_meaningful.endswith("？") or last_meaningful.endswith("?") or "？" in last_meaningful[-50:]
    checks.append({
        "name": "jike_ends_with_question",
        "passed": has_question_end,
        "detail": f"Ends with question: {has_question_end}. Last 50 chars: '{last_meaningful[-50:]}'"
    })
    
    # Has product relevance
    has_product_content = any(kw in content for kw in ["错题", "答疑", "报告", "学习", "AI", "功能"])
    checks.append({
        "name": "jike_product_relevance",
        "passed": has_product_content,
        "detail": f"Product content mentioned: {has_product_content}"
    })
    
    return checks

def check_wechat(content):
    checks = []
    
    # Must be split into 2-3 separate message blocks
    # Look for clear separators: --- or 【消息x】 or blank lines creating 2-3 sections
    # Count distinct message blocks
    
    # Try common separators
    block_patterns = [
        r'---+',
        r'【消息\s*\d+】',
        r'=====+',
        r'\[消息\s*\d+\]',
        r'第[一二三]\s*条',
        r'▌|▎|■',
    ]
    
    block_count_by_separator = 0
    for pattern in block_patterns:
        separators = re.findall(pattern, content)
        if separators:
            block_count_by_separator = len(separators) + 1
            break
    
    # Also check double newline blocks
    double_newline_blocks = [b.strip() for b in re.split(r'\n{2,}', content.strip()) if b.strip() and len(b.strip()) > 20]
    
    blocks_found = block_count_by_separator if block_count_by_separator >= 2 else len(double_newline_blocks)
    is_split = 2 <= blocks_found <= 3
    checks.append({
        "name": "wechat_message_split",
        "passed": is_split,
        "detail": f"Split into 2-3 message blocks. Detected blocks: {blocks_found} (separator method: {block_count_by_separator}, newline method: {len(double_newline_blocks)})"
    })
    
    # Professional but warm tone — no excessive flattery
    sycophantic_phrases = ["您真是太棒了", "您太厉害了", "哇您好厉害", "您真厉害", "感谢您的光临"]
    has_sycophancy = any(p in content for p in sycophantic_phrases)
    checks.append({
        "name": "wechat_no_excessive_flattery",
        "passed": not has_sycophancy,
        "detail": f"No excessive sycophantic language: {not has_sycophancy}"
    })
    
    # Has product relevance
    has_product_content = any(kw in content for kw in ["错题", "答疑", "报告", "学习", "功能", "更新"])
    checks.append({
        "name": "wechat_product_relevance",
        "passed": has_product_content,
        "detail": f"Product content mentioned: {has_product_content}"
    })
    
    return checks

def check_feedback_replies(content):
    checks = []
    
    # F-2024-089: User said "格式还行吧" (= "行吧" pattern = grudging acceptance)
    # Agent should acknowledge imperfection, offer improvement
    # Must NOT just say "好的，有问题随时联系我们"
    
    # Check reply for F-2024-089 exists
    has_f089 = "F-2024-089" in content or "备考小刘" in content or "089" in content
    checks.append({
        "name": "feedback_089_addressed",
        "passed": has_f089,
        "detail": f"Reply for F-2024-089 (备考小刘) found: {has_f089}"
    })
    
    # F-2024-089 reply should address potential improvement (不够完美/优化/改进/还有什么不足)
    # Find the section around 089
    f089_section = ""
    if has_f089:
        idx = max(content.find("F-2024-089"), content.find("备考小刘"), content.find("089"))
        f089_section = content[idx:idx+400]
    
    improvement_words = ["优化", "改进", "不足", "完善", "还有什么", "做得不够", "不够好", "哪里", "建议", "反馈"]
    f089_acknowledges_imperfection = any(w in f089_section for w in improvement_words)
    checks.append({
        "name": "feedback_089_checks_imperfection",
        "passed": f089_acknowledges_imperfection,
        "detail": f"Reply for 089 acknowledges potential imperfection/asks for improvement: {f089_acknowledges_imperfection}. Section: '{f089_section[:150]}'"
    })
    
    # F-2024-091: User said "先这样" (= busy/dissatisfied, should NOT add follow-up pleasantries)
    has_f091 = "F-2024-091" in content or "王阿姨" in content or "091" in content
    checks.append({
        "name": "feedback_091_addressed",
        "passed": has_f091,
        "detail": f"Reply for F-2024-091 (高三家长王阿姨) found: {has_f091}"
    })
    
    # F-2024-091 reply should be brief, NOT add "好的，随时为您服务" style filler
    f091_section = ""
    if has_f091:
        idx = max(content.find("F-2024-091"), content.find("王阿姨"), content.find("091"))
        f091_section = content[idx:idx+400]
    
    filler_phrases = ["随时为您服务", "有问题随时联系", "期待您的好消息", "随时待命", "好的好的"]
    f091_no_filler = not any(p in f091_section for p in filler_phrases)
    # Also check that it's brief (less than 120 chars)
    f091_is_brief = len(f091_section.strip()) < 300  # the whole section including heading should be short
    
    checks.append({
        "name": "feedback_091_no_filler_pleasantries",
        "passed": f091_no_filler,
        "detail": f"Reply for 091 avoids filler pleasantries: {f091_no_filler}. Section: '{f091_section[:150]}'"
    })
    checks.append({
        "name": "feedback_091_brief_response",
        "passed": f091_is_brief,
        "detail": f"Reply for 091 is brief (not over-elaborate): {f091_is_brief}. Section length: {len(f091_section)}"
    })
    
    return checks

def check_no_ai_flavor(content):
    checks = []
    
    forbidden_phrases = [
        "作为一个AI语言模型",
        "作为一个 AI 语言模型",
        "首先…其次…最后…综上所述",
        "首先...其次...最后...综上所述",
    ]
    
    # Also check structural "首先...其次...最后...综上所述" pattern
    has_structure_cliche = bool(re.search(r'首先.{0,50}其次.{0,50}最后.{0,100}综上所述', content, re.DOTALL))
    
    found_forbidden = [p for p in forbidden_phrases if p in content]
    
    no_ai_flavor = len(found_forbidden) == 0 and not has_structure_cliche
    checks.append({
        "name": "no_ai_flavor_phrases",
        "passed": no_ai_flavor,
        "detail": f"No forbidden AI-flavor phrases. Found: {found_forbidden}, structural cliché: {has_structure_cliche}"
    })
    
    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    all_checks = []
    
    # Find the output file
    target_file = find_output_file(workspace, "social_content_output.json")
    
    if target_file is None:
        # Try fallback: social_content_output.txt or similar
        for ext in [".txt", ".md"]:
            target_file = find_output_file(workspace, f"social_content_output{ext}")
            if target_file:
                break
    
    if target_file is None:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{
                "name": "output_file_exists",
                "passed": False,
                "detail": "Could not find social_content_output.json (or .txt/.md) anywhere in the workspace."
            }]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    all_checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found output file at: {target_file}"
    })
    
    # Read the file
    try:
        raw = target_file.read_text(encoding="utf-8")
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{
                "name": "output_file_readable",
                "passed": False,
                "detail": f"Could not read file: {e}"
            }]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # If JSON, parse it and extract sections
    xhs_content = ""
    jike_content = ""
    wechat_content = ""
    feedback_content = ""
    
    if target_file.suffix == ".json":
        try:
            data = json.loads(raw)
            # Expected keys: xiaohongshu, jike, wechat, feedback_replies
            xhs_content = data.get("xiaohongshu", data.get("小红书", ""))
            jike_content = data.get("jike", data.get("即刻", ""))
            wechat_content = data.get("wechat", data.get("微信", ""))
            feedback_content_raw = data.get("feedback_replies", data.get("用户回复", data.get("replies", {})))
            if isinstance(feedback_content_raw, dict):
                feedback_content = " ".join(str(v) for v in feedback_content_raw.values())
                # Also try to get F-2024-089 and F-2024-091 sections
                for k, v in feedback_content_raw.items():
                    if "089" in str(k):
                        feedback_content = "F-2024-089 " + str(v) + "\n" + feedback_content
                    if "091" in str(k):
                        feedback_content = feedback_content + "\nF-2024-091 " + str(v)
            else:
                feedback_content = str(feedback_content_raw)
            
            all_checks.append({
                "name": "json_structure_valid",
                "passed": bool(xhs_content or jike_content or wechat_content),
                "detail": f"JSON parsed. Keys found: {list(data.keys())}"
            })
        except json.JSONDecodeError as e:
            all_checks.append({
                "name": "json_structure_valid",
                "passed": False,
                "detail": f"JSON parse error: {e}"
            })
            # Fall back to treating whole file as text
            xhs_content = raw
            jike_content = raw
            wechat_content = raw
            feedback_content = raw
    else:
        # Plain text — try to extract sections by headers
        xhs_match = re.search(r'(?:小红书|xiaohongshu)[^\n]*\n(.*?)(?=\n(?:即刻|jike|微信|wechat|用户|feedback|F-2024)|$)', raw, re.IGNORECASE | re.DOTALL)
        jike_match = re.search(r'(?:即刻|jike)[^\n]*\n(.*?)(?=\n(?:微信|wechat|用户|feedback|F-2024)|$)', raw, re.IGNORECASE | re.DOTALL)
        wechat_match = re.search(r'(?:微信|wechat)[^\n]*\n(.*?)(?=\n(?:用户|feedback|F-2024|回复)|$)', raw, re.IGNORECASE | re.DOTALL)
        feedback_match = re.search(r'(?:用户|feedback|回复|F-2024)[^\n]*\n(.*?)$', raw, re.IGNORECASE | re.DOTALL)
        
        xhs_content = xhs_match.group(1) if xhs_match else raw
        jike_content = jike_match.group(1) if jike_match else raw
        wechat_content = wechat_match.group(1) if wechat_match else raw
        feedback_content = feedback_match.group(1) if feedback_match else raw
        
        all_checks.append({
            "name": "text_sections_parseable",
            "passed": bool(xhs_match or jike_match or wechat_match),
            "detail": f"Text sections: xhs={bool(xhs_match)}, jike={bool(jike_match)}, wechat={bool(wechat_match)}, feedback={bool(feedback_match)}"
        })
    
    # If sections are empty, use full raw content for all (graceful degradation for scoring)
    if not xhs_content.strip():
        xhs_content = raw
    if not jike_content.strip():
        jike_content = raw
    if not wechat_content.strip():
        wechat_content = raw
    if not feedback_content.strip():
        feedback_content = raw
    
    # Run all checks
    all_checks.extend(check_xiaohongshu(xhs_content))
    all_checks.extend(check_jike(jike_content))
    all_checks.extend(check_wechat(wechat_content))
    all_checks.extend(check_feedback_replies(feedback_content))
    all_checks.extend(check_no_ai_flavor(raw))
    
    # Score
    passed_checks = sum(1 for c in all_checks if c["passed"])
    total_checks = len(all_checks)
    score = round(passed_checks / total_checks, 4) if total_checks > 0 else 0.0
    
    # Overall pass: need 75% of checks to pass
    overall_passed = score >= 0.75
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": all_checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()