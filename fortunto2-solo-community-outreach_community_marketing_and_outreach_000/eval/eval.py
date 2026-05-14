import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    checks = []
    
    def add_check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # --- Find the output file ---
    # Must be at docs/outreach-plan.md
    target_path = workspace / "docs" / "outreach-plan.md"
    
    # Also search recursively in case agent put it elsewhere
    found_files = list(workspace.rglob("outreach-plan.md"))
    
    if not target_path.exists():
        if found_files:
            add_check("file_location", False, f"outreach-plan.md found at wrong location(s): {[str(f) for f in found_files]}. Must be at docs/outreach-plan.md")
        else:
            add_check("file_location", False, "docs/outreach-plan.md not found anywhere in workspace")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("file_location", True, "docs/outreach-plan.md exists at correct path")
    
    try:
        content = target_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("file_readable", True, f"File readable, {len(content)} chars")
    
    content_lower = content.lower()
    
    # --- CHECK 1: Header with project name ---
    has_project_header = bool(re.search(r'#\s+Community Outreach Plan.*SchemaDrift', content, re.IGNORECASE))
    add_check(
        "header_project_name",
        has_project_header,
        "Document must have '# Community Outreach Plan: SchemaDrift' header" if not has_project_header else "Header found"
    )
    
    # --- CHECK 2: Generated date in YYYY-MM-DD format ---
    date_match = re.search(r'\*\*Generated:\*\*\s*(\d{4}-\d{2}-\d{2})', content)
    if not date_match:
        date_match = re.search(r'Generated.*?(\d{4}-\d{2}-\d{2})', content)
    add_check(
        "generated_date_format",
        bool(date_match),
        "Must include **Generated:** YYYY-MM-DD date field" if not date_match else f"Date found: {date_match.group(0)}"
    )
    
    # --- CHECK 3: Product and ICP fields ---
    has_product_field = bool(re.search(r'\*\*Product:\*\*', content, re.IGNORECASE)) or 'product:' in content_lower
    has_icp_field = bool(re.search(r'\*\*ICP:\*\*', content, re.IGNORECASE)) or 'icp:' in content_lower
    add_check(
        "product_and_icp_fields",
        has_product_field and has_icp_field,
        f"Product field: {has_product_field}, ICP field: {has_icp_field}"
    )
    
    # --- CHECK 4: Target Communities table ---
    has_table_header = bool(re.search(r'##\s+Target Communities', content, re.IGNORECASE))
    has_table = bool(re.search(r'\|\s*Community\s*\|.*\|.*Priority\s*\|', content, re.IGNORECASE))
    # Table must have at least 3 rows (Reddit, HN, PH)
    table_rows = re.findall(r'\|\s*r?/?[\w\s/]+\s*\|[^|]+\|[^|]+\|', content)
    # Count data rows (not header or separator)
    data_rows = [r for r in table_rows if '---' not in r and 'Community' not in r]
    has_enough_rows = len(data_rows) >= 3
    
    add_check(
        "target_communities_table",
        has_table_header and has_table and has_enough_rows,
        f"Table header: {has_table_header}, Table found: {has_table}, Data rows >= 3: {has_enough_rows} (found {len(data_rows)})"
    )
    
    # --- CHECK 5: Table has Priority column with valid values ---
    priority_values = re.findall(r'\b(high|medium|low)\b', content_lower)
    has_priority_values = len(priority_values) >= 3
    add_check(
        "priority_column_values",
        has_priority_values,
        f"Priority column must have high/medium/low values. Found {len(priority_values)} instances."
    )
    
    # --- CHECK 6: Top Threads section with exactly 5 thread drafts ---
    has_top_threads_section = bool(re.search(r'##\s+Top Threads to Engage', content, re.IGNORECASE))
    thread_headers = re.findall(r'###\s+Thread:\s*.+', content, re.IGNORECASE)
    # Filter out PH checklist section headers
    thread_headers = [h for h in thread_headers if 'checklist' not in h.lower() and 'pre-launch' not in h.lower()]
    num_threads = len(thread_headers)
    
    add_check(
        "top_threads_section_exists",
        has_top_threads_section,
        "Must have '## Top Threads to Engage' section" if not has_top_threads_section else "Section found"
    )
    
    add_check(
        "exactly_five_thread_drafts",
        num_threads == 5,
        f"Must have exactly 5 thread drafts (### Thread: ...). Found {num_threads}."
    )
    
    # --- CHECK 7: Thread format - required fields ---
    url_fields = re.findall(r'\*\*URL:\*\*', content)
    community_fields = re.findall(r'\*\*Subreddit/Community:\*\*', content, re.IGNORECASE)
    why_relevant_fields = re.findall(r'\*\*Why relevant:\*\*', content, re.IGNORECASE)
    draft_response_fields = re.findall(r'\*\*Draft response:\*\*', content, re.IGNORECASE)
    
    thread_format_ok = (
        len(url_fields) >= 5 and
        len(community_fields) >= 5 and
        len(why_relevant_fields) >= 5 and
        len(draft_response_fields) >= 5
    )
    add_check(
        "thread_format_fields",
        thread_format_ok,
        f"Each thread must have **URL:**, **Subreddit/Community:**, **Why relevant:**, **Draft response:**. Found URL:{len(url_fields)}, Community:{len(community_fields)}, Why:{len(why_relevant_fields)}, Draft:{len(draft_response_fields)}"
    )
    
    # --- CHECK 8: Builder disclosure in thread responses ---
    # Must include "disclaimer: I'm the developer" or similar
    disclaimer_patterns = [
        r"disclaimer.*developer",
        r"disclaimer.*built this",
        r"i['']m the developer",
        r"i built this",
        r"full disclosure.*developer",
        r"disclosure.*i.*built",
        r"i.*maker",
        r"disclaimer.*maker",
    ]
    disclaimer_found = any(re.search(p, content_lower) for p in disclaimer_patterns)
    # Count how many thread responses have some form of disclosure
    disclosure_count = len(re.findall(r'disclaimer', content_lower))
    
    add_check(
        "builder_disclosure_present",
        disclaimer_found and disclosure_count >= 3,
        f"Must include builder disclosure (e.g., 'disclaimer: I'm the developer') in responses. Found pattern: {disclaimer_found}, count: {disclosure_count}"
    )
    
    # --- CHECK 9: Filtering - old/inactive threads should NOT be primary choices ---
    # The old threads (r006 from 2022, hn003 from 2019) should not be in the top 5
    # Check by URL fragments
    banned_urls = [
        "pqr678",  # r006 - 2022 Flyway/Liquibase comparison - too old
        "12398234",  # hn003 - 2019 Flyway - too old
    ]
    # Also check for the low-comment thread
    low_comment_url = "stu901"  # r007 - 3 comments, should be filtered
    
    content_has_old_thread = any(u in content for u in banned_urls)
    content_has_low_comment = low_comment_url in content
    
    filtering_passed = not content_has_old_thread and not content_has_low_comment
    add_check(
        "thread_filtering_applied",
        filtering_passed,
        f"Old threads (2019, 2022) and low-comment threads (<5 comments) must be filtered out. Old thread in content: {content_has_old_thread}, Low-comment thread in content: {content_has_low_comment}"
    )
    
    # --- CHECK 10: ProductHunt Launch Checklist section ---
    has_ph_section = bool(re.search(r'##\s+ProductHunt Launch Checklist', content, re.IGNORECASE)) or \
                     bool(re.search(r'##\s+Product\s*Hunt Launch Checklist', content, re.IGNORECASE))
    
    has_pre_launch = bool(re.search(r'###\s+Pre-Launch', content, re.IGNORECASE)) or \
                     bool(re.search(r'pre.launch', content_lower))
    has_launch_day = bool(re.search(r'###\s+Launch Day', content, re.IGNORECASE)) or \
                     'launch day' in content_lower
    has_post_launch = bool(re.search(r'###\s+Post-Launch', content, re.IGNORECASE)) or \
                      'post-launch' in content_lower or 'post launch' in content_lower
    
    ph_checklist_complete = has_ph_section and has_pre_launch and has_launch_day and has_post_launch
    add_check(
        "ph_launch_checklist_complete",
        ph_checklist_complete,
        f"PH checklist needs: section header:{has_ph_section}, Pre-Launch:{has_pre_launch}, Launch Day:{has_launch_day}, Post-Launch:{has_post_launch}"
    )
    
    # --- CHECK 11: Checklist items are checkboxes ---
    checkboxes = re.findall(r'- \[ \]', content)
    has_enough_checkboxes = len(checkboxes) >= 10
    add_check(
        "checklist_uses_checkboxes",
        has_enough_checkboxes,
        f"Checklist must use '- [ ]' markdown checkboxes. Found {len(checkboxes)} (need >= 10)"
    )
    
    # --- CHECK 12: Tagline constraint mentioned (<60 chars) ---
    tagline_constraint = bool(re.search(r'<\s*60\s*chars?', content, re.IGNORECASE)) or \
                         bool(re.search(r'60\s*char', content, re.IGNORECASE))
    add_check(
        "tagline_char_limit_mentioned",
        tagline_constraint,
        "PH checklist must note tagline < 60 chars constraint" if not tagline_constraint else "Tagline constraint found"
    )
    
    # --- CHECK 13: Tuesday-Thursday PST launch timing ---
    launch_timing = bool(re.search(r'tuesday.{0,20}thursday', content_lower)) or \
                    bool(re.search(r'tue.{0,10}thu', content_lower)) or \
                    bool(re.search(r'00:01\s*PST', content, re.IGNORECASE))
    add_check(
        "launch_day_timing",
        launch_timing,
        "Must mention Tuesday-Thursday timing and/or 00:01 PST for PH launch" if not launch_timing else "Launch timing found"
    )
    
    # --- CHECK 14: Search Keywords Used section ---
    has_keywords_section = bool(re.search(r'##\s+Search Keywords Used', content, re.IGNORECASE)) or \
                           bool(re.search(r'keywords used', content_lower)) or \
                           bool(re.search(r'keywords?.*results?', content_lower))
    
    # Must have at least some keywords with result counts
    keyword_with_counts = re.findall(r'[\w\s]+:\s*\d+\s*results?', content, re.IGNORECASE)
    has_keyword_counts = len(keyword_with_counts) >= 2
    
    add_check(
        "search_keywords_section",
        has_keywords_section,
        f"Must include 'Search Keywords Used' section. Found: {has_keywords_section}"
    )
    
    add_check(
        "keyword_result_counts",
        has_keyword_counts,
        f"Keywords section must show result counts (e.g., 'keyword: N results'). Found {len(keyword_with_counts)} entries."
    )
    
    # --- CHECK 15: Footer line ---
    footer_pattern = r'Generated by /community-outreach'
    has_footer = bool(re.search(footer_pattern, content, re.IGNORECASE))
    add_check(
        "footer_attribution",
        has_footer,
        "Must end with footer: '*Generated by /community-outreach. Review all drafts before posting.*'" if not has_footer else "Footer found"
    )
    
    # --- CHECK 16: Real URLs from the search results are referenced ---
    known_urls = [
        "reddit.com/r/devops/comments/abc123",
        "reddit.com/r/postgresql/comments/def456",
        "reddit.com/r/devops",
        "reddit.com/r/postgresql",
        "news.ycombinator.com",
        "producthunt.com",
    ]
    urls_found = sum(1 for u in known_urls if u in content)
    add_check(
        "real_urls_referenced",
        urls_found >= 3,
        f"Must reference actual URLs from search results. Found {urls_found}/6 known URL fragments."
    )
    
    # --- CHECK 17: Value-first content in responses (not purely promotional) ---
    # Responses should have substantial content before mentioning the product
    # Check that "schemedrift" doesn't appear only in first paragraph of each response block
    response_blocks = re.split(r'\*\*Draft response:\*\*', content, flags=re.IGNORECASE)
    value_first_count = 0
    for block in response_blocks[1:]:  # Skip first split (before any draft response)
        # Take just the first 300 chars of each response block
        first_portion = block[:300].lower()
        # SchemaDrift should NOT be in the very first sentence of the response
        product_in_first_para = 'schemedrift' in first_portion[:100]
        if not product_in_first_para:
            value_first_count += 1
    
    add_check(
        "value_first_approach",
        value_first_count >= 3,
        f"Responses must provide value BEFORE mentioning product. {value_first_count}/5 responses appear to lead with value (not product name)"
    )
    
    # --- CHECK 18: Postgres/SchemaDrift mentioned in ICP and product description ---
    has_postgres_context = 'postgresql' in content_lower or 'postgres' in content_lower
    has_schemedrift_described = 'schemedrift' in content_lower
    add_check(
        "product_context_accurate",
        has_postgres_context and has_schemedrift_described,
        f"Product description must reference PostgreSQL and SchemaDrift. Postgres: {has_postgres_context}, SchemaDrift named: {has_schemedrift_described}"
    )
    
    # --- Compute score ---
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Must pass critical checks to overall pass
    critical_checks = [
        "file_location",
        "exactly_five_thread_drafts",
        "thread_format_fields",
        "builder_disclosure_present",
        "ph_launch_checklist_complete",
        "thread_filtering_applied",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == cn), False)
        for cn in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))