import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # Find the briefing file
    briefing_file = None
    candidates = list(workspace.rglob("briefing*.md")) + list(workspace.rglob("news_briefing*.md")) + list(workspace.rglob("简报*.md")) + list(workspace.rglob("daily_briefing*.md"))
    
    if not candidates:
        # Also try txt
        candidates = list(workspace.rglob("briefing*.txt")) + list(workspace.rglob("news_briefing*.txt"))
    
    if candidates:
        # Prefer files in news-scout or workspace root
        for c in candidates:
            if "archive" not in str(c) and "template" not in str(c):
                briefing_file = c
                break
        if not briefing_file:
            briefing_file = candidates[0]
    
    if not briefing_file or not briefing_file.exists():
        add_check("briefing_file_exists", False, f"No briefing file found. Searched for briefing*.md, news_briefing*.md, etc. in {workspace}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("briefing_file_exists", True, f"Found briefing file: {briefing_file}")
    
    try:
        content = briefing_file.read_text(encoding='utf-8')
    except Exception as e:
        add_check("file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("file_readable", True, f"File read successfully, {len(content)} chars")
    
    # Check 1: Title header with date
    title_pattern = re.search(r'##\s*🔥\s*新闻斥候简报\s*\(\d{4}-\d{2}-\d{2}\)', content)
    add_check(
        "title_header_with_date",
        bool(title_pattern),
        f"Found title: '{title_pattern.group(0).strip()}'" if title_pattern else "Missing '## 🔥 新闻斥候简报 (YYYY-MM-DD)' header"
    )
    
    # Check 2: Three required section headers
    investing_section = re.search(r'###\s*📈\s*投资与美股市场', content)
    global_ai_section = re.search(r'###\s*🌍\s*全球\s*AI\s*前沿', content)
    china_ai_section = re.search(r'###\s*🇨🇳\s*中国国内\s*AI\s*动态', content)
    
    all_sections = bool(investing_section and global_ai_section and china_ai_section)
    add_check(
        "all_three_sections_present",
        all_sections,
        f"Investing: {bool(investing_section)}, Global AI: {bool(global_ai_section)}, China AI: {bool(china_ai_section)}"
    )
    
    # Check 3: Count news items with star ratings
    # Match lines like: 1. **[⭐⭐⭐⭐] ...** or numbered items with star ratings
    star_items = re.findall(r'^\d+\.\s*\*\*\[⭐+\]', content, re.MULTILINE)
    total_items = len(star_items)
    add_check(
        "total_10_items",
        total_items == 10,
        f"Found {total_items} news items with star ratings (expected 10)"
    )
    
    # Check 4: 3:4:3 distribution
    # Find items in each section by splitting content
    section_counts = {"investing": 0, "global_ai": 0, "china_ai": 0}
    
    if investing_section and global_ai_section and china_ai_section:
        inv_start = investing_section.start()
        gai_start = global_ai_section.start()
        cai_start = china_ai_section.start()
        
        # Sort sections by position
        sections_ordered = sorted([
            ("investing", inv_start),
            ("global_ai", gai_start),
            ("china_ai", cai_start)
        ], key=lambda x: x[1])
        
        for i, (sec_name, sec_start) in enumerate(sections_ordered):
            if i + 1 < len(sections_ordered):
                sec_end = sections_ordered[i+1][1]
                sec_text = content[sec_start:sec_end]
            else:
                sec_text = content[sec_start:]
            
            # Count star items in this section
            count = len(re.findall(r'^\d+\.\s*\*\*\[⭐+\]', sec_text, re.MULTILINE))
            section_counts[sec_name] = count
    
    distribution_ok = (
        section_counts["investing"] == 3 and
        section_counts["global_ai"] == 4 and
        section_counts["china_ai"] == 3
    )
    add_check(
        "3_4_3_distribution",
        distribution_ok,
        f"Investing: {section_counts['investing']} (expected 3), Global AI: {section_counts['global_ai']} (expected 4), China AI: {section_counts['china_ai']} (expected 3)"
    )
    
    # Check 5: Multi-source annotation (多家媒体报道) - must appear for deduplicated events
    # The mock data has duplicates: inv001 (Yahoo/CNBC/WSJ), ai001 (OpenAI/TC/Verge), cn001 (Baidu/机器之心)
    multi_source_annotation = re.search(r'多家媒体报道', content)
    add_check(
        "multi_source_annotation_present",
        bool(multi_source_annotation),
        "Found '多家媒体报道' annotation" if multi_source_annotation else "Missing '多家媒体报道' annotation for deduplicated events"
    )
    
    # Check 6: Paywall annotation for WSJ (WSJ URL is in mock data, but after dedup with P0 Yahoo Finance, WSJ should be dropped)
    # However, if agent keeps WSJ source, it must annotate. 
    # More importantly, the HTTP URL from WSJ must be either fixed to HTTPS or the P0 Yahoo Finance source must be preferred.
    wsj_in_content = bool(re.search(r'wsj\.com', content, re.IGNORECASE))
    http_non_https = re.findall(r'http://[^\s\)]+', content)
    # Filter out any markdown-escaped or code block http
    real_http_urls = [u for u in http_non_https if not u.startswith('https://')]
    
    add_check(
        "no_http_only_urls",
        len(real_http_urls) == 0,
        f"Found {len(real_http_urls)} non-HTTPS URLs: {real_http_urls[:3]}" if real_http_urls else "All URLs use HTTPS"
    )
    
    # Check 7: Paywall annotation if WSJ appears
    if wsj_in_content:
        wsj_paywall = bool(re.search(r'wsj.*订阅|订阅.*wsj|可能需订阅|付费', content, re.IGNORECASE))
        add_check(
            "wsj_paywall_annotation",
            wsj_paywall,
            "WSJ source present with paywall annotation" if wsj_paywall else "WSJ source present BUT missing paywall annotation '（可能需订阅）'"
        )
    else:
        add_check(
            "wsj_paywall_annotation",
            True,
            "WSJ source correctly excluded via P0 deduplication (Yahoo Finance preferred)"
        )
    
    # Check 8: Star ratings present in correct format [⭐] patterns
    star_patterns = re.findall(r'\[⭐+\]', content)
    valid_stars = all(1 <= len(re.findall('⭐', s)) <= 5 for s in star_patterns)
    add_check(
        "star_ratings_format",
        len(star_patterns) >= 10 and valid_stars,
        f"Found {len(star_patterns)} star rating blocks, all valid: {valid_stars}"
    )
    
    # Check 9: Footer with count and time
    footer_pattern = re.search(r'本次共检索\s*(\d+)\s*条新闻\s*[|｜]\s*更新时间[：:]\s*\d{2}:\d{2}', content)
    add_check(
        "footer_format",
        bool(footer_pattern),
        f"Found footer: '{footer_pattern.group(0).strip()}'" if footer_pattern else "Missing footer '📊 本次共检索 {N} 条新闻 | 更新时间：HH:MM'"
    )
    
    # Check 10: Check hotness ordering within each section (higher stars should come before lower)
    def get_section_star_counts(sec_name):
        if not (investing_section and global_ai_section and china_ai_section):
            return []
        
        inv_start = investing_section.start()
        gai_start = global_ai_section.start()
        cai_start = china_ai_section.start()
        
        sections_ordered = sorted([
            ("investing", inv_start),
            ("global_ai", gai_start),
            ("china_ai", cai_start)
        ], key=lambda x: x[1])
        
        for i, (sn, ss) in enumerate(sections_ordered):
            if sn == sec_name:
                if i + 1 < len(sections_ordered):
                    se = sections_ordered[i+1][1]
                    sec_text = content[ss:se]
                else:
                    sec_text = content[ss:]
                
                star_counts = []
                for item in re.findall(r'\[⭐+\]', sec_text):
                    star_counts.append(len(re.findall('⭐', item)))
                return star_counts
        return []
    
    ordering_ok = True
    ordering_details = []
    for sec_name in ["investing", "global_ai", "china_ai"]:
        counts = get_section_star_counts(sec_name)
        if counts:
            is_sorted = all(counts[i] >= counts[i+1] for i in range(len(counts)-1))
            ordering_ok = ordering_ok and is_sorted
            ordering_details.append(f"{sec_name}: {counts} sorted={is_sorted}")
    
    add_check(
        "hotness_descending_order",
        ordering_ok,
        "; ".join(ordering_details) if ordering_details else "Could not verify ordering (sections not found)"
    )
    
    # Check 11: Summary format (each item has 摘要 and 影响 fields)
    summary_fields = re.findall(r'-\s*\*摘要\*:', content)
    impact_fields = re.findall(r'-\s*\*影响\*:', content)
    add_check(
        "summary_and_impact_fields",
        len(summary_fields) >= 10 and len(impact_fields) >= 10,
        f"Found {len(summary_fields)} 摘要 fields and {len(impact_fields)} 影响 fields (expected ≥10 each)"
    )
    
    # Check 12: Source links in markdown format
    source_links = re.findall(r'🔗\s*\[.+?\]\(https://', content)
    add_check(
        "source_links_with_https",
        len(source_links) >= 8,
        f"Found {len(source_links)} source links with HTTPS (expected ≥8)"
    )
    
    # Calculate score
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    # Must pass critical checks to pass overall
    critical_check_names = [
        "briefing_file_exists",
        "total_10_items",
        "3_4_3_distribution",
        "no_http_only_urls",
        "footer_format"
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_check_names
    )
    
    overall_passed = critical_passed and score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))