import sys
import json
import re
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ─── Helper ───────────────────────────────────────────────────────────────
    def add(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ─── CHECK 1: Output directory detection priority ─────────────────────────
    # Must be output/UrbanFarm-2025/03 - Deep Research/
    expected_research_dir = workspace / "output" / "UrbanFarm-2025" / "03 - Deep Research"
    dir_exists = expected_research_dir.is_dir()
    total_score += add(
        "output_directory_priority_detection",
        dir_exists,
        f"Expected directory '{expected_research_dir}' exists: {dir_exists}. "
        "Agent must prioritize output/ over CWD per skill spec."
    )

    if not dir_exists:
        # Try to find if agent placed it elsewhere (partial credit context)
        alt_dirs = list(workspace.rglob("03 - Deep Research"))
        alt_info = f"Found alternative locations: {[str(d) for d in alt_dirs]}" if alt_dirs else "No '03 - Deep Research' dir found anywhere."
        checks[-1]["detail"] += f" {alt_info}"

    # ─── CHECK 2: Overview file exists with correct name ─────────────────────
    overview_candidates = list(workspace.rglob("000.Research-Overview.md"))
    overview_correct_location = expected_research_dir / "000.Research-Overview.md"
    overview_exists_correct = overview_correct_location.is_file()
    overview_exists_anywhere = len(overview_candidates) > 0

    total_score += add(
        "overview_file_correct_name_and_location",
        overview_exists_correct,
        f"000.Research-Overview.md at correct path: {overview_exists_correct}. "
        f"Found anywhere: {[str(p) for p in overview_candidates]}"
    )

    # ─── CHECK 3: Three individual research topic files exist ─────────────────
    all_files = list(expected_research_dir.glob("*.md")) if dir_exists else []
    research_files = [f for f in all_files if not f.name.startswith("000.")]

    # Check YYMMDD prefix pattern
    date_prefix_pattern = re.compile(r'^\d{6}\s.+\.md$')
    dated_research_files = [f for f in research_files if date_prefix_pattern.match(f.name)]

    has_three_topics = len(dated_research_files) >= 3
    total_score += add(
        "three_topic_files_with_yymmdd_prefix",
        has_three_topics,
        f"Found {len(dated_research_files)} files matching YYMMDD pattern. "
        f"Files: {[f.name for f in dated_research_files]}. Need >= 3."
    )

    # ─── CHECK 4: YYMMDD date is valid and recent ─────────────────────────────
    valid_dates = 0
    today = datetime.now()
    for f in dated_research_files:
        date_str = f.name[:6]
        try:
            parsed = datetime.strptime(date_str, "%y%m%d")
            # Should be within 1 year of today
            delta = abs((today - parsed).days)
            if delta < 400:
                valid_dates += 1
        except ValueError:
            pass

    has_valid_dates = valid_dates >= 3 if has_three_topics else valid_dates == len(dated_research_files)
    total_score += add(
        "yymmdd_dates_are_valid_and_current",
        has_valid_dates,
        f"{valid_dates}/{len(dated_research_files)} files have valid YYMMDD dates within reasonable range."
    )

    # ─── CHECK 5: Overview document has required table ────────────────────────
    overview_has_table = False
    overview_has_generated_field = False
    overview_has_findings = False
    overview_has_action_list = False
    overview_content = ""

    try:
        if overview_exists_correct:
            overview_content = overview_correct_location.read_text(encoding="utf-8")
        elif overview_candidates:
            overview_content = overview_candidates[0].read_text(encoding="utf-8")

        if overview_content:
            # Must have a markdown table with | No. | Research Topic | ...
            table_pattern = re.compile(r'\|\s*No\.?\s*\|.*Research\s*Topic.*\|', re.IGNORECASE)
            overview_has_table = bool(table_pattern.search(overview_content))
            overview_has_generated_field = bool(re.search(r'\*\*Generated\*\*\s*:', overview_content))
            overview_has_findings = bool(re.search(r'##\s+Core\s+Findings', overview_content, re.IGNORECASE))
            overview_has_action_list = bool(re.search(r'-\s*\[[\sx]\]', overview_content))  # checklist items
    except Exception as e:
        checks.append({"name": "overview_parse_error", "passed": False, "detail": str(e)})

    total_score += add(
        "overview_has_research_deliverables_table",
        overview_has_table,
        f"Overview contains '| No. | Research Topic |...' table: {overview_has_table}"
    )
    total_score += add(
        "overview_has_generated_metadata",
        overview_has_generated_field,
        f"Overview has **Generated**: field: {overview_has_generated_field}"
    )
    total_score += add(
        "overview_has_core_findings_section",
        overview_has_findings,
        f"Overview has '## Core Findings' section: {overview_has_findings}"
    )
    total_score += add(
        "overview_has_action_checklist",
        overview_has_action_list,
        f"Overview has markdown checklist items (- [ ] ...): {overview_has_action_list}"
    )

    # ─── CHECK 6: Individual research docs have correct structure ─────────────
    docs_with_core_conclusions = 0
    docs_with_roman_numerals = 0
    docs_with_app_recommendations = 0
    docs_with_generated_field = 0
    docs_with_inline_links = 0
    docs_without_trailing_references = 0

    for f in dated_research_files[:4]:  # check up to 4 files
        try:
            content = f.read_text(encoding="utf-8")

            # Must have ## Core Conclusions
            if re.search(r'##\s+Core\s+Conclusions', content, re.IGNORECASE):
                docs_with_core_conclusions += 1

            # Must have Roman numeral sections (## I. or ## II.)
            if re.search(r'##\s+I{1,3}V?\.\s', content) or re.search(r'##\s+[IVX]+\.\s', content):
                docs_with_roman_numerals += 1

            # Must have Application Recommendations
            if re.search(r'##\s+(III\.|Application\s+Rec)', content, re.IGNORECASE):
                docs_with_app_recommendations += 1

            # Must have **Generated**: field
            if re.search(r'\*\*Generated\*\*\s*:', content):
                docs_with_generated_field += 1

            # Must have inline markdown links [text](url)
            inline_link_count = len(re.findall(r'\[.+?\]\(https?://.+?\)', content))
            if inline_link_count >= 1:
                docs_with_inline_links += 1

            # Must NOT have a trailing "References" or "Bibliography" section at the end
            # Check last 500 chars for separate references section
            tail = content[-600:]
            has_trailing_refs = bool(re.search(r'\n##\s+(References|Bibliography|Sources|Further\s+Reading)', tail, re.IGNORECASE))
            if not has_trailing_refs:
                docs_without_trailing_references += 1

        except Exception as e:
            checks.append({"name": f"parse_error_{f.name}", "passed": False, "detail": str(e)})

    n = max(len(dated_research_files), 1)
    n_checked = min(len(dated_research_files), 4)

    total_score += add(
        "research_docs_have_core_conclusions_section",
        docs_with_core_conclusions >= n_checked and n_checked > 0,
        f"{docs_with_core_conclusions}/{n_checked} research docs have '## Core Conclusions'"
    )
    total_score += add(
        "research_docs_use_roman_numeral_sections",
        docs_with_roman_numerals >= n_checked and n_checked > 0,
        f"{docs_with_roman_numerals}/{n_checked} research docs use Roman numeral (## I., ## II.) sections"
    )
    total_score += add(
        "research_docs_have_application_recommendations",
        docs_with_app_recommendations >= n_checked and n_checked > 0,
        f"{docs_with_app_recommendations}/{n_checked} docs have Application Recommendations section"
    )
    total_score += add(
        "research_docs_have_generated_metadata",
        docs_with_generated_field >= n_checked and n_checked > 0,
        f"{docs_with_generated_field}/{n_checked} docs have **Generated**: field"
    )
    total_score += add(
        "research_docs_have_inline_links_not_trailing_refs",
        docs_with_inline_links >= n_checked and docs_without_trailing_references >= n_checked and n_checked > 0,
        f"Inline links: {docs_with_inline_links}/{n_checked}; No trailing refs: {docs_without_trailing_references}/{n_checked}"
    )

    # ─── CHECK 7: No forbidden sub-subdirectories ─────────────────────────────
    forbidden_subdirs = []
    if dir_exists:
        for item in expected_research_dir.iterdir():
            if item.is_dir():
                forbidden_subdirs.append(item.name)

    no_subdirs = len(forbidden_subdirs) == 0
    total_score += add(
        "no_sub_subdirectories_in_research_dir",
        no_subdirs,
        f"Forbidden subdirectories found: {forbidden_subdirs}. Skill spec prohibits sub-subdirs."
    )

    # ─── CHECK 8: Overview links use URL-encoded filenames ────────────────────
    overview_links_encoded = False
    if overview_content:
        # Should have ./YYMMDD%20... style links in the table
        encoded_link_pattern = re.compile(r'\./\d{6}%20[^\)]+\.md')
        overview_links_encoded = bool(encoded_link_pattern.search(overview_content))

    total_score += add(
        "overview_table_uses_url_encoded_links",
        overview_links_encoded,
        f"Overview table links use URL-encoded format (./YYMMDD%20...): {overview_links_encoded}"
    )

    # ─── CHECK 9: No separate executive summary files ─────────────────────────
    all_output_files = list((workspace / "output").rglob("*.md")) if (workspace / "output").is_dir() else []
    exec_summary_files = [
        f for f in all_output_files
        if re.search(r'executive.?summary|exec.?summary', f.name, re.IGNORECASE)
    ]
    no_exec_summary = len(exec_summary_files) == 0
    total_score += add(
        "no_separate_executive_summary_file",
        no_exec_summary,
        f"Found {len(exec_summary_files)} executive summary files (should be 0): {[f.name for f in exec_summary_files]}"
    )

    # ─── CHECK 10: Topic coverage (economics, hydroponics, regulatory) ─────────
    all_filenames = " ".join(f.name.lower() for f in dated_research_files)
    all_contents = ""
    for f in dated_research_files:
        try:
            all_contents += f.read_text(encoding="utf-8").lower()
        except:
            pass

    covers_economics = bool(re.search(r'vertical.farm|econom|roi|capital|cost', all_filenames + all_contents))
    covers_hydro = bool(re.search(r'hydroponic|soil.based|yield|nutrient|water\s+usage', all_filenames + all_contents))
    covers_regulatory = bool(re.search(r'regulat|zoning|permit|certif|subsid|policy', all_filenames + all_contents))

    total_score += add(
        "topics_cover_economics_of_vertical_farming",
        covers_economics,
        f"Research covers vertical farming economics: {covers_economics}"
    )
    total_score += add(
        "topics_cover_hydroponics_vs_soil",
        covers_hydro,
        f"Research covers hydroponics vs soil-based: {covers_hydro}"
    )
    total_score += add(
        "topics_cover_regulatory_landscape",
        covers_regulatory,
        f"Research covers regulatory/zoning/permitting: {covers_regulatory}"
    )

    # ─── Final Score ──────────────────────────────────────────────────────────
    max_score = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    overall_passed = final_score >= 0.75 and dir_exists and has_three_topics

    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))