import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    overall_passed = True

    def add_check(name, passed, detail):
        nonlocal overall_passed
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            overall_passed = False

    # ── 1. Find daily_report.json ─────────────────────────────────────────
    try:
        candidates = list(Path(workspace_dir).rglob("daily_report.json"))
        if not candidates:
            add_check("file_exists", False, "daily_report.json not found anywhere in workspace")
            return {"passed": False, "score": 0.0, "checks": checks}
        report_path = candidates[0]
        add_check("file_exists", True, f"Found daily_report.json at {report_path}")
    except Exception as e:
        add_check("file_exists", False, f"Error searching for file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── 2. Parse JSON ─────────────────────────────────────────────────────
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        add_check("valid_json", True, "File is valid JSON")
    except Exception as e:
        add_check("valid_json", False, f"Failed to parse JSON: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── 3. Top-level structure: must be a list or dict with items list ────
    try:
        if isinstance(report, list):
            articles = report
        elif isinstance(report, dict):
            # Accept various key names
            for key in ("articles", "items", "data", "results"):
                if key in report and isinstance(report[key], list):
                    articles = report[key]
                    break
            else:
                # Try to find any list value
                list_vals = [v for v in report.values() if isinstance(v, list)]
                if list_vals:
                    articles = max(list_vals, key=len)
                else:
                    articles = []
        else:
            articles = []
        add_check("structure_parseable", len(articles) > 0,
                  f"Extracted {len(articles)} article entries from report")
    except Exception as e:
        add_check("structure_parseable", False, f"Error parsing structure: {e}")
        articles = []

    # ── 4. Exactly 3 articles (top 3 from RSS with max_items=3) ──────────
    try:
        count_ok = len(articles) == 3
        add_check("exactly_3_articles", count_ok,
                  f"Report contains {len(articles)} articles (expected 3)")
    except Exception as e:
        add_check("exactly_3_articles", False, f"Error counting articles: {e}")

    if len(articles) == 0:
        return {"passed": False, "score": round(sum(c["passed"] for c in checks) / len(checks), 3), "checks": checks}

    # ── 5. Required fields present in each article ────────────────────────
    REQUIRED_FIELDS = {"title", "link", "published", "content", "length"}
    # Also accept common aliases
    FIELD_ALIASES = {
        "link": ["link", "url", "article_url", "href"],
        "published": ["published", "pub_date", "pubdate", "date", "publish_time"],
        "content": ["content", "body", "text", "full_content", "article_content"],
        "length": ["length", "content_length", "char_count", "size"],
        "title": ["title", "headline", "article_title"],
    }

    def find_field(article, field):
        for alias in FIELD_ALIASES.get(field, [field]):
            if alias in article:
                return article[alias]
        return None

    fields_ok = True
    missing_info = []
    for i, art in enumerate(articles):
        for field in REQUIRED_FIELDS:
            val = find_field(art, field)
            if val is None:
                fields_ok = False
                missing_info.append(f"Article {i+1} missing field '{field}'")

    add_check("required_fields_present", fields_ok,
              "All required fields (title, link, published, content, length) present" if fields_ok
              else "; ".join(missing_info))

    # ── 6. Content is CRAWLED (not just RSS description) ─────────────────
    # The mock RSS descriptions are short (~5 words), crawled content is much longer
    try:
        RSS_DESCRIPTIONS = [
            "Researchers claim a new milestone.",
            "OpenAI releases its most powerful model yet.",
            "TSMC announces new fab in Arizona.",
        ]
        content_crawled = True
        crawl_details = []
        for i, art in enumerate(articles):
            content_val = find_field(art, "content")
            if content_val is None:
                content_crawled = False
                crawl_details.append(f"Article {i+1}: no content field")
                continue
            content_str = str(content_val)
            # Crawled content should be significantly longer than RSS description
            if len(content_str) < 200:
                content_crawled = False
                crawl_details.append(
                    f"Article {i+1}: content only {len(content_str)} chars — looks like RSS description, not crawled"
                )
            else:
                crawl_details.append(f"Article {i+1}: content {len(content_str)} chars — OK")

        add_check("content_is_crawled", content_crawled,
                  "; ".join(crawl_details))
    except Exception as e:
        add_check("content_is_crawled", False, f"Error checking content: {e}")

    # ── 7. Length field matches actual content length ─────────────────────
    try:
        length_ok = True
        length_details = []
        for i, art in enumerate(articles):
            content_val = find_field(art, "content")
            length_val = find_field(art, "length")
            if content_val is None or length_val is None:
                length_details.append(f"Article {i+1}: missing content or length field")
                continue
            actual_len = len(str(content_val))
            reported_len = int(length_val)
            if actual_len != reported_len:
                length_ok = False
                length_details.append(
                    f"Article {i+1}: reported length={reported_len} but actual content length={actual_len}"
                )
            else:
                length_details.append(f"Article {i+1}: length={reported_len} matches content ✓")

        add_check("length_matches_content", length_ok,
                  "; ".join(length_details) if length_details else "No articles to check")
    except Exception as e:
        add_check("length_matches_content", False, f"Error checking length: {e}")

    # ── 8. Links point to the local mock server (correct source used) ─────
    try:
        link_ok = True
        link_details = []
        for i, art in enumerate(articles):
            link_val = find_field(art, "link")
            if link_val is None:
                link_ok = False
                link_details.append(f"Article {i+1}: no link field")
                continue
            link_str = str(link_val)
            if "localhost:8765" in link_str or "127.0.0.1:8765" in link_str:
                link_details.append(f"Article {i+1}: link points to local mock server ✓")
            else:
                link_ok = False
                link_details.append(
                    f"Article {i+1}: link '{link_str}' does not reference local mock server"
                )
        add_check("links_from_correct_source", link_ok,
                  "; ".join(link_details))
    except Exception as e:
        add_check("links_from_correct_source", False, f"Error checking links: {e}")

    # ── 9. Correct articles (first 3 from RSS feed) ───────────────────────
    try:
        EXPECTED_TITLES = [
            "Quantum Computing Breakthrough Achieved at MIT",
            "OpenAI Unveils GPT-5 with Multimodal Reasoning",
            "Global Chip Shortage Eases as TSMC Expands Capacity",
        ]
        title_ok = True
        title_details = []
        found_titles = [find_field(a, "title") or "" for a in articles]
        for i, (found, expected) in enumerate(zip(found_titles, EXPECTED_TITLES)):
            if expected.lower() in str(found).lower() or str(found).lower() in expected.lower():
                title_details.append(f"Article {i+1}: title matches ✓")
            else:
                title_ok = False
                title_details.append(
                    f"Article {i+1}: expected title containing '{expected}', got '{found}'"
                )
        add_check("correct_top_3_articles", title_ok,
                  "; ".join(title_details))
    except Exception as e:
        add_check("correct_top_3_articles", False, f"Error checking titles: {e}")

    # ── 10. max_length applied (content ≤ 2000 chars as specified in prompt) ─
    # The prompt asks for max_length=2000; article content in mock server is ~3000+ chars
    try:
        max_length_ok = True
        max_len_details = []
        for i, art in enumerate(articles):
            content_val = find_field(art, "content")
            if content_val is None:
                max_len_details.append(f"Article {i+1}: no content to check")
                continue
            clen = len(str(content_val))
            if clen > 2000:
                max_length_ok = False
                max_len_details.append(
                    f"Article {i+1}: content is {clen} chars, exceeds 2000 char limit"
                )
            else:
                max_len_details.append(
                    f"Article {i+1}: content is {clen} chars ≤ 2000 ✓"
                )
        add_check("max_length_2000_applied", max_length_ok,
                  "; ".join(max_len_details))
    except Exception as e:
        add_check("max_length_2000_applied", False, f"Error checking max_length: {e}")

    # ── Final score ───────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)
    overall_passed = all(c["passed"] for c in checks)

    return {"passed": overall_passed, "score": score, "checks": checks}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))