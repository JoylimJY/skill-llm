import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    # --- Find the output file ---
    candidates = list(Path(workspace).rglob("daily_briefing.md"))
    
    file_found = len(candidates) > 0
    checks.append({
        "name": "Output file daily_briefing.md exists",
        "passed": file_found,
        "detail": f"Found at {candidates[0]}" if file_found else "daily_briefing.md not found anywhere in workspace"
    })
    
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    try:
        content = candidates[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # -----------------------------------------------------------------------
    # CHECK 1: Has correct top-level section headers (## 科技新闻 and ## 军事新闻)
    # -----------------------------------------------------------------------
    has_tech_header = bool(re.search(r'^##\s+科技新闻', content, re.MULTILINE))
    has_military_header = bool(re.search(r'^##\s+军事新闻', content, re.MULTILINE))
    
    header_passed = has_tech_header and has_military_header
    checks.append({
        "name": "Correct section headers: ## 科技新闻 and ## 军事新闻",
        "passed": header_passed,
        "detail": f"科技新闻 header: {has_tech_header}, 军事新闻 header: {has_military_header}"
    })
    if header_passed:
        total_score += 1.0

    # -----------------------------------------------------------------------
    # CHECK 2: Items use proper markdown link format [标题](链接)
    # -----------------------------------------------------------------------
    link_pattern = re.findall(r'\[(.+?)\]\((https?://[^\)]+)\)', content)
    has_links = len(link_pattern) >= 4  # at least 4 valid linked items expected
    checks.append({
        "name": "Items use [title](url) markdown link format (at least 4)",
        "passed": has_links,
        "detail": f"Found {len(link_pattern)} markdown links: {link_pattern[:3]}..."
    })
    if has_links:
        total_score += 1.0

    # -----------------------------------------------------------------------
    # CHECK 3: Items contain 来源：xxx | 时间：xxx format
    # -----------------------------------------------------------------------
    source_time_pattern = re.findall(r'来源：.+?\|.+?时间：', content)
    has_source_time = len(source_time_pattern) >= 4
    checks.append({
        "name": "Items contain '来源：xxx | 时间：xxx' format (at least 4)",
        "passed": has_source_time,
        "detail": f"Found {len(source_time_pattern)} source|time entries"
    })
    if has_source_time:
        total_score += 1.0

    # -----------------------------------------------------------------------
    # CHECK 4: Items contain 要点：xxx
    # -----------------------------------------------------------------------
    keypoint_pattern = re.findall(r'要点：.+', content)
    has_keypoints = len(keypoint_pattern) >= 4
    checks.append({
        "name": "Items contain '要点：xxx' field (at least 4)",
        "passed": has_keypoints,
        "detail": f"Found {len(keypoint_pattern)} keypoint entries"
    })
    if has_keypoints:
        total_score += 1.0

    # -----------------------------------------------------------------------
    # CHECK 5: Low-credibility / forum / anonymous sources are EXCLUDED
    # -----------------------------------------------------------------------
    forbidden_urls = [
        "bbs.ithome.com",                              # IT之家论坛帖子
        "reddit.com",                                  # Reddit anonymous post
        "somerandomblog.net",                          # anonymous blog
        "newsDetail_forward_2024060302",               # 澎湃网匿名转载
    ]
    forbidden_titles_patterns = [
        r'论坛爆料',
        r'INSIDER CLAIMS',
        r'Secret.*Leaked',
        r'网帖转载',
        r'匿名.*称',
    ]
    
    excluded_low_cred = True
    violated = []
    for url in forbidden_urls:
        if url in content:
            excluded_low_cred = False
            violated.append(f"URL present: {url}")
    for pat in forbidden_titles_patterns:
        if re.search(pat, content, re.IGNORECASE):
            excluded_low_cred = False
            violated.append(f"Pattern found: {pat}")
    
    checks.append({
        "name": "Low-credibility/forum/anonymous sources are excluded",
        "passed": excluded_low_cred,
        "detail": "All forbidden sources correctly excluded" if excluded_low_cred else f"Violations: {violated}"
    })
    if excluded_low_cred:
        total_score += 2.0  # weighted higher - core filtering requirement

    # -----------------------------------------------------------------------
    # CHECK 6: Duplicate items are deduplicated
    # -----------------------------------------------------------------------
    # 豆包/GPT-5 should appear only once each despite being in multiple feeds
    douban_matches = len(re.findall(r'豆包', content))
    gpt5_matches = len(re.findall(r'GPT.?5', content, re.IGNORECASE))
    
    douban_deduped = douban_matches <= 1
    gpt5_deduped = gpt5_matches <= 1
    dedup_passed = douban_deduped and gpt5_deduped
    
    checks.append({
        "name": "Duplicate items are deduplicated (豆包 and GPT-5 appear at most once)",
        "passed": dedup_passed,
        "detail": f"豆包 occurrences: {douban_matches} (expect ≤1), GPT-5 occurrences: {gpt5_matches} (expect ≤1)"
    })
    if dedup_passed:
        total_score += 1.5

    # -----------------------------------------------------------------------
    # CHECK 7: Key high-credibility items ARE present
    # -----------------------------------------------------------------------
    expected_present = [
        ("华为", "昇腾"),       # 华为芯片 from 36kr
        ("山东舰", "航母"),     # 山东舰 from 澎湃
        ("OpenAI", "GPT"),      # OpenAI from TechCrunch/Verge (deduplicated)
        ("NATO", "TSMC|AlphaFold|F-16|US Navy|TSMC"),  # at least some intl military
    ]
    
    present_checks = []
    for primary, secondary_pattern in expected_present:
        found_primary = primary in content
        found_secondary = bool(re.search(secondary_pattern, content))
        present_checks.append(found_primary or found_secondary)
    
    all_key_items_present = sum(present_checks) >= 3
    checks.append({
        "name": "Key high-credibility items present (at least 3 of 4 expected topics)",
        "passed": all_key_items_present,
        "detail": f"Topic presence: 华为/昇腾={present_checks[0]}, 山东舰/航母={present_checks[1]}, OpenAI/GPT={present_checks[2]}, intl_military={present_checks[3]}"
    })
    if all_key_items_present:
        total_score += 1.5

    # -----------------------------------------------------------------------
    # CHECK 8: Numbered items within each section
    # -----------------------------------------------------------------------
    numbered_items = re.findall(r'^\d+\.\s+\[', content, re.MULTILINE)
    has_numbered = len(numbered_items) >= 4
    checks.append({
        "name": "Items are numbered within sections (at least 4 numbered entries)",
        "passed": has_numbered,
        "detail": f"Found {len(numbered_items)} numbered list items"
    })
    if has_numbered:
        total_score += 1.0

    # -----------------------------------------------------------------------
    # FINAL SCORE
    # -----------------------------------------------------------------------
    max_score = 10.0
    normalized_score = min(total_score / max_score, 1.0)
    
    # Must pass critical checks to overall pass
    critical_passed = (
        file_found and
        header_passed and
        has_links and
        excluded_low_cred and
        has_keypoints
    )
    
    result = {
        "passed": critical_passed and normalized_score >= 0.65,
        "score": round(normalized_score, 3),
        "checks": checks
    }
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))