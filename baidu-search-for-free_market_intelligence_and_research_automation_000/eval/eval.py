import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
total_score = 0.0

def make_check(name, passed, detail, weight=1.0):
    return {"name": name, "passed": passed, "detail": detail, "_weight": weight}

# ── Locate the report file ────────────────────────────────────────────────────
report_files = list(Path(workspace).rglob("nev_competitive_report.json"))

check_file_exists = make_check(
    "report_file_exists",
    len(report_files) > 0,
    f"Found {len(report_files)} file(s) named 'nev_competitive_report.json'" if report_files else "File 'nev_competitive_report.json' not found anywhere in workspace.",
    weight=1.0
)
checks.append(check_file_exists)

if not report_files:
    result = {
        "passed": False,
        "score": 0.0,
        "checks": [{"name": c["name"], "passed": c["passed"], "detail": c["detail"]} for c in checks]
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)

report_path = report_files[0]

# ── Load and parse the JSON ───────────────────────────────────────────────────
try:
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    checks.append(make_check("report_valid_json", True, f"Loaded valid JSON from {report_path}", weight=0.5))
except Exception as e:
    checks.append(make_check("report_valid_json", False, f"JSON parse error: {e}", weight=0.5))
    result = {
        "passed": False,
        "score": 0.0,
        "checks": [{"name": c["name"], "passed": c["passed"], "detail": c["detail"]} for c in checks]
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)

# ── Check 1: Top-level structure has expected sections ───────────────────────
try:
    has_query = "query" in report or "search_query" in report or "keyword" in report
    has_results = "results" in report or "search_results" in report
    has_content = "page_contents" in report or "fetched_pages" in report or "content_analysis" in report or "pages" in report

    # Also accept flat list of items each containing search + page data
    is_flat_combined = isinstance(report, list) and len(report) > 0 and all(
        ("url" in item or "link" in item) for item in report
    )

    structure_ok = (has_results or is_flat_combined) and (has_content or is_flat_combined)
    checks.append(make_check(
        "report_has_combined_structure",
        structure_ok,
        f"Report contains both search results and fetched page content: {structure_ok}. Keys found: {list(report.keys()) if isinstance(report, dict) else 'list'}",
        weight=1.0
    ))
except Exception as e:
    checks.append(make_check("report_has_combined_structure", False, f"Error checking structure: {e}", weight=1.0))

# ── Check 2: Search was performed for 新能源汽车市场份额 ──────────────────────
try:
    report_str = json.dumps(report, ensure_ascii=False)
    keyword_present = "新能源汽车市场份额" in report_str
    checks.append(make_check(
        "search_query_nev_market_share",
        keyword_present,
        f"Report contains evidence of searching '新能源汽车市场份额': {keyword_present}",
        weight=1.0
    ))
except Exception as e:
    checks.append(make_check("search_query_nev_market_share", False, f"Error: {e}", weight=1.0))

# ── Check 3: num_results=8 was respected (exactly 8 search results) ──────────
try:
    # Find the search results list
    result_items = None
    if isinstance(report, list):
        result_items = report
    elif isinstance(report, dict):
        for key in ["results", "search_results", "items", "data"]:
            if key in report and isinstance(report[key], list):
                result_items = report[key]
                break

    if result_items is not None:
        count = len(result_items)
        exactly_8 = count == 8
        checks.append(make_check(
            "num_results_equals_8",
            exactly_8,
            f"Expected exactly 8 search results (num_results=8), found {count}",
            weight=2.0
        ))
    else:
        checks.append(make_check(
            "num_results_equals_8",
            False,
            "Could not locate the search results list in the report",
            weight=2.0
        ))
except Exception as e:
    checks.append(make_check("num_results_equals_8", False, f"Error: {e}", weight=2.0))

# ── Check 4: rank field present and starts at 1, not 0 ───────────────────────
try:
    report_str = json.dumps(report, ensure_ascii=False)
    # Look for rank field in the data
    has_rank_field = '"rank"' in report_str or "'rank'" in report_str

    rank_starts_at_1 = False
    if isinstance(report, list):
        items = report
    elif isinstance(report, dict):
        items = report.get("results", report.get("search_results", []))
    else:
        items = []

    if items:
        first_item = items[0]
        if isinstance(first_item, dict) and "rank" in first_item:
            rank_starts_at_1 = first_item["rank"] == 1
        else:
            # rank may be embedded - check if report mentions rank:1
            rank_starts_at_1 = ('"rank": 1' in report_str or '"rank":1' in report_str)

    checks.append(make_check(
        "rank_field_present_starts_at_1",
        has_rank_field and rank_starts_at_1,
        f"rank field present: {has_rank_field}, first rank == 1: {rank_starts_at_1}",
        weight=1.5
    ))
except Exception as e:
    checks.append(make_check("rank_field_present_starts_at_1", False, f"Error: {e}", weight=1.5))

# ── Check 5: fetch_url was used - page title and text present ─────────────────
try:
    report_str = json.dumps(report, ensure_ascii=False)
    # The mock fetch_url returns specific content; check for known text snippets
    known_page_titles = [
        "2024年中国新能源汽车市场份额分析报告",
        "新能源汽车销量排行榜TOP10",
        "比亚迪vs特斯拉：中国市场争夺战"
    ]
    known_text_snippets = [
        "中国汽车工业协会",
        "比亚迪",
        "494.4万辆"
    ]

    title_found = any(t in report_str for t in known_page_titles)
    text_found = any(s in report_str for s in known_text_snippets)

    checks.append(make_check(
        "fetch_url_used_page_content_present",
        title_found and text_found,
        f"Page title from fetch_url found: {title_found}, Page text content found: {text_found}",
        weight=2.0
    ))
except Exception as e:
    checks.append(make_check("fetch_url_used_page_content_present", False, f"Error: {e}", weight=2.0))

# ── Check 6: abstract field from search results is preserved ─────────────────
try:
    report_str = json.dumps(report, ensure_ascii=False)
    abstract_key_present = '"abstract"' in report_str
    known_abstract = "比亚迪领跑全球" in report_str or "新能源汽车渗透率已突破40%" in report_str

    checks.append(make_check(
        "search_abstract_field_preserved",
        abstract_key_present and known_abstract,
        f"'abstract' key in output: {abstract_key_present}, known abstract text found: {known_abstract}",
        weight=1.5
    ))
except Exception as e:
    checks.append(make_check("search_abstract_field_preserved", False, f"Error: {e}", weight=1.5))

# ── Check 7: fetch_url result uses 'title' and 'text' keys (not 'body'/'content') ──
try:
    report_str = json.dumps(report, ensure_ascii=False)
    # Check that the agent used the correct key names from fetch_url API
    uses_text_key = '"text"' in report_str or "'text'" in report_str
    uses_page_title = ('"page_title"' in report_str or '"title"' in report_str)
    # Should NOT be using wrong keys like 'body', 'content', 'description' for page text
    uses_wrong_key = ('"body"' in report_str and '"text"' not in report_str)

    checks.append(make_check(
        "fetch_url_correct_keys_used",
        uses_text_key and uses_page_title and not uses_wrong_key,
        f"'text' key present: {uses_text_key}, title key present: {uses_page_title}, wrong 'body' key used without 'text': {uses_wrong_key}",
        weight=1.0
    ))
except Exception as e:
    checks.append(make_check("fetch_url_correct_keys_used", False, f"Error: {e}", weight=1.0))

# ── Compute final score ───────────────────────────────────────────────────────
total_weight = sum(c["_weight"] for c in checks)
earned_weight = sum(c["_weight"] for c in checks if c["passed"])
score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0

passed = score >= 0.75 and checks[0]["passed"]  # file must exist + 75% score

result = {
    "passed": passed,
    "score": score,
    "checks": [{"name": c["name"], "passed": c["passed"], "detail": c["detail"]} for c in checks]
}

print(json.dumps(result, ensure_ascii=False, indent=2))