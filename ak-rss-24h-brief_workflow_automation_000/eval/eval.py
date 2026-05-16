#!/usr/bin/env python3
"""
Evaluation script for ak-rss-24h-brief task.
Checks that the agent correctly invoked generate_brief.py with the right parameters
and that the output file matches the proprietary format defined in SKILL.md.
"""

import sys
import re
import json
from pathlib import Path


def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Find the output file ──────────────────────────────────────────────────
    candidates = list(workspace.rglob("daily_brief.md"))
    if not candidates:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "Could not find 'daily_brief.md' anywhere in the workspace."
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    # Use the most recently modified one if multiple exist
    output_file = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    total_score += add_check(
        "output_file_exists",
        True,
        f"Found output file at: {output_file}",
        weight=0.5
    )

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Could not read output file: {e}"
        })
        return {"passed": False, "score": total_score / 10.0, "checks": checks}

    lines = content.splitlines()

    # ── CHECK 1: Title header ─────────────────────────────────────────────────
    has_title = any(
        re.match(r"^# 技术资讯简报（最近\s*\d+\s*小时）", line)
        for line in lines
    )
    total_score += add_check(
        "title_header_format",
        has_title,
        "Title line '# 技术资讯简报（最近 N 小时）' present" if has_title
        else f"Missing or malformed title header. First line was: '{lines[0] if lines else '(empty)'}'",
        weight=1.0
    )

    # ── CHECK 2: RSS Source header line ──────────────────────────────────────
    # Must be: - [RSS Source](<path-to-opml>)
    # The path must reference the local OPML file (not a fabricated URL)
    rss_source_lines = [l for l in lines if re.match(r"^- \[RSS Source\]\(.+\)", l)]
    has_rss_source = len(rss_source_lines) > 0
    total_score += add_check(
        "rss_source_header_line",
        has_rss_source,
        f"RSS Source line found: '{rss_source_lines[0]}'" if has_rss_source
        else "Missing '- [RSS Source](...)' header line. This is a required proprietary format element.",
        weight=1.5
    )

    if has_rss_source:
        # The RSS source link must point to the actual OPML used (local file or path)
        opml_ref = re.search(r"^- \[RSS Source\]\((.+)\)", rss_source_lines[0])
        opml_in_link = opml_ref.group(1) if opml_ref else ""
        # Accept: absolute path containing tech_feeds.opml, or relative path
        valid_opml_ref = "tech_feeds.opml" in opml_in_link or "opml" in opml_in_link.lower()
        total_score += add_check(
            "rss_source_link_valid",
            valid_opml_ref,
            f"RSS Source link references OPML: '{opml_in_link}'" if valid_opml_ref
            else f"RSS Source link does not reference the actual OPML file: '{opml_in_link}'",
            weight=0.5
        )

    # ── CHECK 3: Category headings must be ## **Name** format ────────────────
    category_headings = [l for l in lines if re.match(r"^## \*\*[^*]+\*\*\s*$", l)]
    has_bold_categories = len(category_headings) >= 1
    total_score += add_check(
        "category_headings_bold_format",
        has_bold_categories,
        f"Found {len(category_headings)} bold category heading(s): {category_headings}" if has_bold_categories
        else "No '## **Category Name**' headings found. Category headings must be bold-wrapped inside ##.",
        weight=2.0
    )

    # Reject plain ## headings (not bold-wrapped) that look like categories
    plain_headings = [l for l in lines if re.match(r"^## [^*\s]", l)]
    has_plain_bad_headings = len(plain_headings) > 0
    total_score += add_check(
        "no_plain_category_headings",
        not has_plain_bad_headings,
        "No plain (non-bold) ## category headings found (good)" if not has_plain_bad_headings
        else f"Found {len(plain_headings)} non-bold ## headings (should be ## **Name**): {plain_headings[:3]}",
        weight=0.5
    )

    # ── CHECK 4: Article items with title+link ────────────────────────────────
    article_item_lines = [l for l in lines if re.match(r"^- \[.+\]\(https?://", l)]
    # Exclude the RSS Source line itself
    article_items = [l for l in article_item_lines if not re.match(r"^- \[RSS Source\]", l)]
    enough_articles = len(article_items) >= 5
    total_score += add_check(
        "minimum_article_items",
        enough_articles,
        f"Found {len(article_items)} article items (need ≥5)" if enough_articles
        else f"Only {len(article_items)} article items found (need ≥5 per --min-items constraint).",
        weight=1.0
    )

    not_too_many = len(article_items) <= 10
    total_score += add_check(
        "maximum_article_items",
        not_too_many,
        f"{len(article_items)} articles ≤ 10 (within --max-items limit)" if not_too_many
        else f"{len(article_items)} articles exceeds --max-items=10 limit.",
        weight=0.5
    )

    # ── CHECK 5: Chinese summary on the line immediately after each article ───
    # Pattern: article line followed by a line starting with spaces and Chinese chars
    chinese_char_pattern = re.compile(r'[\u4e00-\u9fff]')
    summary_checks_passed = 0
    summary_checks_total = 0

    for i, line in enumerate(lines):
        if re.match(r"^- \[.+\]\(https?://", line) and not re.match(r"^- \[RSS Source\]", line):
            summary_checks_total += 1
            # Next line should be the Chinese summary
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # Must start with whitespace or be indented, contain Chinese
                has_chinese = bool(chinese_char_pattern.search(next_line))
                is_indented_or_nonempty = next_line.strip() != ""
                # Must NOT contain bare English sentences (check for mostly non-Chinese long words)
                has_embedded_english_sentence = bool(
                    re.search(r'\b[A-Z][a-z]+ [a-z]+ [a-z]+ [a-z]+\b', next_line)
                )
                if has_chinese and is_indented_or_nonempty and not has_embedded_english_sentence:
                    summary_checks_passed += 1

    if summary_checks_total > 0:
        summary_ratio = summary_checks_passed / summary_checks_total
        summaries_ok = summary_ratio >= 0.8
        total_score += add_check(
            "chinese_summaries_present",
            summaries_ok,
            f"{summary_checks_passed}/{summary_checks_total} articles have valid Chinese summaries on next line",
            weight=2.0
        )
    else:
        total_score += add_check(
            "chinese_summaries_present",
            False,
            "No article items found to check summaries against.",
            weight=2.0
        )

    # ── CHECK 6: No source domain or timestamps in output ─────────────────────
    # Should not contain lines like "Source: ...", "Published:", date strings, fetch stats
    forbidden_patterns = [
        (r'Published:', "Published timestamp found"),
        (r'Source Domain:', "Source domain line found"),
        (r'Fetched \d+ feeds', "Fetch stats found"),
        (r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}', "ISO timestamp found in output"),
        (r'UTC\b', "UTC timezone string found"),
    ]
    no_forbidden = True
    forbidden_found = []
    for pat, msg in forbidden_patterns:
        matches = [l for l in lines if re.search(pat, l)]
        if matches:
            no_forbidden = False
            forbidden_found.append(f"{msg}: '{matches[0]}'")

    total_score += add_check(
        "no_forbidden_fields",
        no_forbidden,
        "No forbidden fields (source domain, timestamps, fetch stats) found" if no_forbidden
        else f"Forbidden fields found: {'; '.join(forbidden_found)}",
        weight=0.5
    )

    # ── CHECK 7: Overall Summary footer ──────────────────────────────────────
    overall_lines = [l for l in lines if l.startswith("Overall Summary:")]
    has_overall = len(overall_lines) >= 1
    total_score += add_check(
        "overall_summary_footer",
        has_overall,
        f"Footer found: '{overall_lines[0][:80]}...'" if has_overall
        else "Missing 'Overall Summary: ...' footer line.",
        weight=1.0
    )

    # ── CHECK 8: Overall summary contains Chinese ─────────────────────────────
    if has_overall:
        summary_has_chinese = bool(chinese_char_pattern.search(overall_lines[0]))
        total_score += add_check(
            "overall_summary_chinese",
            summary_has_chinese,
            "Overall Summary contains Chinese text (good)" if summary_has_chinese
            else "Overall Summary line does not contain Chinese text.",
            weight=0.5
        )

    # ── CHECK 9: Used 24-hour window (title reflects correct hours) ───────────
    hours_match = re.search(r"最近\s*(\d+)\s*小时", content)
    correct_hours = False
    if hours_match:
        hours_val = int(hours_match.group(1))
        correct_hours = hours_val == 24
    total_score += add_check(
        "correct_24h_window",
        correct_hours,
        f"Title shows 24-hour window" if correct_hours
        else f"Title shows wrong time window: '{hours_match.group(0) if hours_match else 'not found'}'",
        weight=0.5
    )

    # ── Compute final score ───────────────────────────────────────────────────
    max_possible = 0.5 + 1.0 + 1.5 + 0.5 + 2.0 + 0.5 + 1.0 + 0.5 + 2.0 + 0.5 + 1.0 + 0.5 + 0.5
    score = round(total_score / max_possible, 3)

    # Must pass core structural checks to be considered passing
    core_checks = [
        "output_file_exists",
        "title_header_format",
        "rss_source_header_line",
        "category_headings_bold_format",
        "minimum_article_items",
        "chinese_summaries_present",
        "overall_summary_footer",
    ]
    core_passed = all(
        c["passed"] for c in checks if c["name"] in core_checks
    )

    passed = core_passed and score >= 0.7

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [],
                          "error": "No workspace directory provided"}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))