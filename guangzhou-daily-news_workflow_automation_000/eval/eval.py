import sys
import json
import re
import os
from pathlib import Path
from datetime import date

def run_eval(workspace: str):
    checks = []
    total_score = 0.0
    
    today_str = date.today().strftime('%Y-%m-%d')
    expected_filename = f"广州日报_{today_str}.md"
    
    # ── Check 1: File exists at ~/News/广州日报_YYYY-MM-DD.md ─────────────────
    news_dir = Path(workspace) / "News"
    target_file = news_dir / expected_filename
    
    # Also check in case workspace is /home/agent
    if not target_file.exists():
        alt_locations = list(Path(workspace).rglob("广州日报_*.md"))
        # Filter out archive files
        alt_locations = [f for f in alt_locations if "archive" not in str(f)]
        if alt_locations:
            target_file = alt_locations[0]
    
    file_exists = target_file.exists()
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Expected file at {news_dir / expected_filename}. {'Found: ' + str(target_file) if file_exists else 'Not found.'}"
    })
    
    if not file_exists:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # ── Check 2: Correct top-level header ─────────────────────────────────────
    has_main_header = "# 📰 广州日报新闻简报" in content
    checks.append({
        "name": "main_header_correct",
        "passed": has_main_header,
        "detail": f"Must contain '# 📰 广州日报新闻简报'. {'Found.' if has_main_header else 'Not found.'}"
    })
    
    # ── Check 3: Metadata line with date, source, article count ───────────────
    meta_pattern = re.search(
        r'📅\s*(\d{4}-\d{2}-\d{2})\s*·\s*来源：新花城\s*·\s*共\s*(\d+)\s*条',
        content
    )
    meta_ok = meta_pattern is not None
    checks.append({
        "name": "metadata_line_present",
        "passed": meta_ok,
        "detail": f"Must have '📅 YYYY-MM-DD · 来源：新花城 · 共 N 条'. {'Found: ' + meta_pattern.group(0) if meta_ok else 'Not found.'}"
    })
    
    # ── Check 4: Article count 20-30 ──────────────────────────────────────────
    article_count_ok = False
    article_count = 0
    if meta_ok:
        try:
            article_count = int(meta_pattern.group(2))
            article_count_ok = 20 <= article_count <= 30
        except Exception:
            pass
    checks.append({
        "name": "article_count_20_to_30",
        "passed": article_count_ok,
        "detail": f"Article count must be 20-30. Found: {article_count}"
    })
    
    # ── Check 5: Blockquote format for articles (> ## N. Title) ───────────────
    blockquote_headers = re.findall(r'^> ## \d+\. .+', content, re.MULTILINE)
    blockquote_count = len(blockquote_headers)
    blockquote_ok = blockquote_count >= 20
    checks.append({
        "name": "blockquote_article_format",
        "passed": blockquote_ok,
        "detail": f"Articles must use '> ## N. Title' blockquote format. Found {blockquote_count} such headers (need ≥20)."
    })
    
    # ── Check 6: Attribution lines with reporter and editor fields ────────────
    attribution_lines = re.findall(
        r'> ✍️ 记者：\*\*.+?\*\* · 📝 编辑：\*\*.+?\*\* · 🔗 \[阅读原文\]\(.+?\)',
        content
    )
    attr_count = len(attribution_lines)
    attr_ok = attr_count >= 20
    checks.append({
        "name": "attribution_lines_present",
        "passed": attr_ok,
        "detail": f"Each article must have '✍️ 记者：**X** · 📝 编辑：**X** · 🔗 [阅读原文](url)'. Found {attr_count} (need ≥20)."
    })
    
    # ── Check 7: Em-dash placeholder for missing reporter/editor ──────────────
    # Some articles have no reporter or editor, should use '—' not 'N/A' or 'Unknown' etc
    dash_placeholders = re.findall(r'> ✍️ 记者：\*\*—\*\*', content)
    missing_reporter_articles = [
        a for a in ["009", "014", "020"]  # Articles with no reporter in mock data
    ]
    # Check that '—' appears at least once (for articles with no reporter)
    has_dash_placeholder = len(dash_placeholders) >= 1
    checks.append({
        "name": "em_dash_for_missing_fields",
        "passed": has_dash_placeholder,
        "detail": f"Missing reporter/editor must use '—' (em-dash) placeholder. Found {len(dash_placeholders)} em-dash reporter entries. {'OK.' if has_dash_placeholder else 'Using wrong placeholder or missing.'}"
    })
    
    # ── Check 8: HR separator present ─────────────────────────────────────────
    has_hr = re.search(r'^---\s*$', content, re.MULTILINE) is not None
    checks.append({
        "name": "horizontal_rule_separator",
        "passed": has_hr,
        "detail": f"Must have '---' horizontal rule separator after metadata. {'Found.' if has_hr else 'Not found.'}"
    })
    
    # ── Check 9: Article links point to the mock server or are valid URLs ─────
    url_pattern = re.findall(r'\[阅读原文\]\((http[^)]+)\)', content)
    urls_ok = len(url_pattern) >= 20
    checks.append({
        "name": "article_urls_present",
        "passed": urls_ok,
        "detail": f"Each article must have a '阅读原文' link. Found {len(url_pattern)} URLs (need ≥20)."
    })
    
    # ── Check 10: Category emoji labels in blockquotes ────────────────────────
    # Category lines must be inside blockquotes: "> emoji category · ⏰ time"
    cat_lines = re.findall(r'^> [🔴💻📚🌿💰🌍👥⚽🏥🎓♻️🌾📌].+?·\s*⏰', content, re.MULTILINE)
    cat_ok = len(cat_lines) >= 15
    checks.append({
        "name": "category_emoji_in_blockquote",
        "passed": cat_ok,
        "detail": f"Category lines with emoji must appear inside blockquotes. Found {len(cat_lines)} (need ≥15)."
    })
    
    # ── Check 11: Summary text present in blockquotes ─────────────────────────
    # At least half articles should have summary text (a non-empty > line after category)
    summary_lines = re.findall(r'^> [^\s#>✍📝🔗🔴💻📚🌿💰🌍👥⚽🏥🎓♻️🌾📌⏰].{30,}', content, re.MULTILINE)
    summary_ok = len(summary_lines) >= 15
    checks.append({
        "name": "summary_text_present",
        "passed": summary_ok,
        "detail": f"Articles should include summary text (≥30 chars) in blockquotes. Found {len(summary_lines)} summary lines (need ≥15)."
    })
    
    # ── Compute score ─────────────────────────────────────────────────────────
    weights = {
        "output_file_exists": 0.15,
        "main_header_correct": 0.10,
        "metadata_line_present": 0.10,
        "article_count_20_to_30": 0.10,
        "blockquote_article_format": 0.15,
        "attribution_lines_present": 0.10,
        "em_dash_for_missing_fields": 0.07,
        "horizontal_rule_separator": 0.05,
        "article_urls_present": 0.08,
        "category_emoji_in_blockquote": 0.05,
        "summary_text_present": 0.05,
    }
    
    score = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    all_passed = all(c["passed"] for c in checks)
    
    return {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/agent"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))