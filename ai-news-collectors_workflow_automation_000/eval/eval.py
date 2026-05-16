import sys
import re
import json
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # --- Find the output file ---
    candidates = list(workspace.rglob("ai_news_report.md"))
    file_found = len(candidates) > 0

    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found ai_news_report.md at: {candidates[0]}" if file_found else "ai_news_report.md not found anywhere in workspace"
    })

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        content = candidates[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": f"File size: {len(content)} chars"})

    # -----------------------------------------------------------------------
    # CHECK 1: Header format — must contain 🔥 AI 新闻速递 with a date in parens
    # -----------------------------------------------------------------------
    header_match = bool(re.search(r'##\s+🔥\s*AI\s+新闻速递[（(]\d{4}-\d{2}-\d{2}[)）]', content))
    checks.append({
        "name": "header_format_correct",
        "passed": header_match,
        "detail": "Must have '## 🔥 AI 新闻速递（YYYY-MM-DD）' header" if not header_match else "Header format OK"
    })

    # -----------------------------------------------------------------------
    # CHECK 2: Star rating sections — must have at least ⭐⭐⭐⭐⭐, ⭐⭐⭐⭐, ⭐⭐⭐ headings
    # -----------------------------------------------------------------------
    has_5star = bool(re.search(r'###\s+⭐⭐⭐⭐⭐', content))
    has_4star = bool(re.search(r'###\s+⭐⭐⭐⭐(?!⭐)', content))
    has_3star = bool(re.search(r'###\s+⭐⭐⭐(?!⭐)', content))
    star_sections_ok = has_5star and has_4star and has_3star

    checks.append({
        "name": "star_rating_sections_present",
        "passed": star_sections_ok,
        "detail": f"5-star: {has_5star}, 4-star: {has_4star}, 3-star: {has_3star}. All three tiers required."
    })

    # -----------------------------------------------------------------------
    # CHECK 3: News item count — must be between 15 and 25
    # -----------------------------------------------------------------------
    # Count numbered items like "1. **..." or "15. **..."
    numbered_items = re.findall(r'^\s*\d+\.\s+\*\*', content, re.MULTILINE)
    item_count = len(numbered_items)
    count_ok = 15 <= item_count <= 25

    checks.append({
        "name": "news_item_count_15_to_25",
        "passed": count_ok,
        "detail": f"Found {item_count} numbered news items. Required: 15-25."
    })

    # -----------------------------------------------------------------------
    # CHECK 4: Each news item has a summary line and a link
    # -----------------------------------------------------------------------
    # Look for > 摘要 pattern and > 🔗 link pattern
    summary_lines = re.findall(r'^\s*>\s+.+', content, re.MULTILINE)
    link_lines = re.findall(r'🔗\s*\[.+?\]\(https?://.+?\)', content)
    items_have_summaries = len(summary_lines) >= max(1, item_count - 2)  # allow small tolerance
    items_have_links = len(link_lines) >= max(1, item_count // 2)  # at least half have links

    checks.append({
        "name": "news_items_have_summaries",
        "passed": items_have_summaries,
        "detail": f"Found {len(summary_lines)} '>' summary lines for {item_count} items."
    })
    checks.append({
        "name": "news_items_have_https_links",
        "passed": items_have_links,
        "detail": f"Found {len(link_lines)} 🔗 HTTPS links. Expected at least {item_count // 2}."
    })

    # -----------------------------------------------------------------------
    # CHECK 5: Footer stats line — exact proprietary format
    # 📊 本次共收集 XX 条新闻 | 搜索 XX 次 | 覆盖维度：A/B/C/D/E/F | 更新时间：HH:MM
    # -----------------------------------------------------------------------
    footer_pattern = re.search(
        r'📊\s*本次共收集\s*\d+\s*条新闻\s*[|｜]\s*搜索\s*\d+\s*次\s*[|｜]\s*覆盖维度[：:]\s*[A-F][/／][A-F][/／][A-F][/／][A-F][/／][A-F][/／][A-F]\s*[|｜]\s*更新时间[：:]\s*\d{1,2}:\d{2}',
        content
    )
    footer_ok = footer_pattern is not None

    checks.append({
        "name": "footer_stats_line_correct",
        "passed": footer_ok,
        "detail": "Must end with: 📊 本次共收集 XX 条新闻 | 搜索 XX 次 | 覆盖维度：A/B/C/D/E/F | 更新时间：HH:MM" if not footer_ok else "Footer format OK: " + (footer_pattern.group(0)[:80] if footer_pattern else "")
    })

    # -----------------------------------------------------------------------
    # CHECK 6: Search count in footer must be >= 8
    # -----------------------------------------------------------------------
    search_count = 0
    if footer_ok:
        search_count_match = re.search(
            r'搜索\s*(\d+)\s*次',
            content
        )
        if search_count_match:
            search_count = int(search_count_match.group(1))
    search_count_ok = search_count >= 8

    checks.append({
        "name": "search_count_at_least_8",
        "passed": search_count_ok,
        "detail": f"Footer claims {search_count} searches. Must be >= 8 per SKILL.md requirement."
    })

    # -----------------------------------------------------------------------
    # CHECK 7: All 6 dimensions covered (A/B/C/D/E/F) in footer
    # -----------------------------------------------------------------------
    dimension_ok = False
    if footer_ok:
        dim_match = re.search(
            r'覆盖维度[：:]\s*([A-F][/／][A-F][/／][A-F][/／][A-F][/／][A-F][/／][A-F])',
            content
        )
        if dim_match:
            dim_str = re.sub(r'[/／]', '/', dim_match.group(1))
            dimensions = set(dim_str.split('/'))
            dimension_ok = dimensions == {'A', 'B', 'C', 'D', 'E', 'F'}

    checks.append({
        "name": "all_6_dimensions_covered",
        "passed": dimension_ok,
        "detail": "Footer must show exactly A/B/C/D/E/F dimensions all covered." if not dimension_ok else "All 6 dimensions A-F covered."
    })

    # -----------------------------------------------------------------------
    # CHECK 8: Deduplication — at least one item mentions "多家媒体报道"
    # -----------------------------------------------------------------------
    has_dedup_marker = bool(re.search(r'多家媒体报道', content))
    checks.append({
        "name": "deduplication_merge_applied",
        "passed": has_dedup_marker,
        "detail": "At least one merged item must mention '多家媒体报道' per deduplication rule." if not has_dedup_marker else "Found '多家媒体报道' merge marker."
    })

    # -----------------------------------------------------------------------
    # CHECK 9: Output is in Chinese (majority Chinese characters)
    # -----------------------------------------------------------------------
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    total_alpha = len(re.findall(r'[a-zA-Z\u4e00-\u9fff]', content))
    chinese_ratio = chinese_chars / total_alpha if total_alpha > 0 else 0
    is_chinese = chinese_ratio >= 0.3  # at least 30% of alpha chars are Chinese

    checks.append({
        "name": "output_primarily_chinese",
        "passed": is_chinese,
        "detail": f"Chinese character ratio: {chinese_ratio:.2%} ({chinese_chars} Chinese / {total_alpha} total alpha). Must be >= 30%."
    })

    # -----------------------------------------------------------------------
    # CHECK 10: No content from wrong_template.md or strategy notes contamination
    #           (agent should not have just copied distractor content)
    # -----------------------------------------------------------------------
    distractor_phrases = [
        "Only 3 items, incomplete",
        "max_results: 5",
        "we typically do 3-4 searches max",
        "Old report for",
    ]
    distractor_contamination = any(phrase in content for phrase in distractor_phrases)
    checks.append({
        "name": "no_distractor_contamination",
        "passed": not distractor_contamination,
        "detail": "Output should not contain content from distractor/config files." if distractor_contamination else "No distractor contamination found."
    })

    # -----------------------------------------------------------------------
    # SCORING
    # -----------------------------------------------------------------------
    weights = {
        "output_file_exists": 0.05,
        "file_readable": 0.02,
        "header_format_correct": 0.10,
        "star_rating_sections_present": 0.12,
        "news_item_count_15_to_25": 0.12,
        "news_items_have_summaries": 0.08,
        "news_items_have_https_links": 0.08,
        "footer_stats_line_correct": 0.15,
        "search_count_at_least_8": 0.10,
        "all_6_dimensions_covered": 0.08,
        "deduplication_merge_applied": 0.05,
        "output_primarily_chinese": 0.03,
        "no_distractor_contamination": 0.02,
    }

    score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.0)
        if check["passed"]:
            score += w

    # Must pass critical checks to pass overall
    critical_checks = [
        "output_file_exists",
        "header_format_correct",
        "star_rating_sections_present",
        "news_item_count_15_to_25",
        "footer_stats_line_correct",
        "search_count_at_least_8",
        "all_6_dimensions_covered",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    passed = critical_passed and score >= 0.70

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))