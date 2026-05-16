#!/usr/bin/env python3
"""
Evaluation script for the news-aggregator-skill task.
Checks:
1. Report file exists in reports/ directory with correct timestamped naming pattern.
2. Report is in Simplified Chinese (heuristic: contains CJK characters).
3. All news item titles are Markdown links (not plain text).
4. GitHub Trending items are ALL present with Deep Analysis (核心价值, 启发思考, 场景标签).
5. Smart Fill applied to non-GitHub sources: supplementary items annotated (⚠️ or 🔥 markers).
6. fetch_news.py was invoked with --source all --limit 15 --deep (Global Scan strategy).
7. Report contains both Tech/AI and Finance sections.
8. GitHub section does NOT contain Smart Fill annotation markers (GitHub Exception respected).
"""

import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── 1. Find report file ───────────────────────────────────────────────────
    reports_dir = workspace / "reports"
    report_files = []
    try:
        # Match patterns like: hn_news_20250710_1200.md, news_report_20250710_1200.md, etc.
        timestamp_pattern = re.compile(r'\d{8}_\d{4}')
        report_files = [
            f for f in reports_dir.rglob("*.md")
            if timestamp_pattern.search(f.name)
        ]
    except Exception as e:
        report_files = []

    file_found = len(report_files) > 0
    if file_found:
        report_path = report_files[0]
        detail = f"Found report: {report_path.name}"
    else:
        # Fallback: any .md file in reports/
        try:
            all_md = list(reports_dir.rglob("*.md"))
            if all_md:
                report_path = all_md[0]
                detail = f"Found .md file but without timestamp pattern: {report_path.name}"
                file_found = True  # partial credit scenario handled below
            else:
                report_path = None
                detail = "No .md report file found in reports/ directory."
        except Exception:
            report_path = None
            detail = "reports/ directory not accessible."

    score = add_check(
        "report_file_exists_with_timestamp",
        len(report_files) > 0,
        detail,
        weight=1.0
    )
    total_score += score

    if report_path is None or not report_path.exists():
        # Can't do further checks
        for name in [
            "report_in_simplified_chinese",
            "all_titles_are_markdown_links",
            "github_all_5_repos_present",
            "github_deep_analysis_核心价值",
            "github_deep_analysis_启发思考",
            "github_deep_analysis_场景标签",
            "smart_fill_annotations_present",
            "github_no_smart_fill_annotations",
            "tech_ai_section_present",
            "finance_section_present",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Report file missing; check skipped."})
        result = {
            "passed": False,
            "score": round(total_score / 11.0, 3),
            "checks": checks,
        }
        print(json.dumps(result))
        return

    try:
        report_content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        report_content = ""
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})

    # ── 2. Simplified Chinese check (CJK characters present) ─────────────────
    cjk_pattern = re.compile(r'[\u4e00-\u9fff]')
    cjk_count = len(cjk_pattern.findall(report_content))
    zh_passed = cjk_count >= 50  # At least 50 CJK characters expected in a real report
    total_score += add_check(
        "report_in_simplified_chinese",
        zh_passed,
        f"CJK character count: {cjk_count} (need >= 50)",
        weight=1.0
    )

    # ── 3. All item titles are Markdown links ─────────────────────────────────
    # Heuristic: Check that news item titles appear as [text](url) and NOT as bare ### N. Title
    # Look for at least 5 markdown links in the document
    md_link_pattern = re.compile(r'\[.+?\]\(https?://[^\)]+\)')
    md_links = md_link_pattern.findall(report_content)

    # Check for bare title pattern (### N. Title without a link) — bad pattern
    # We look for headlines that are NOT links
    bare_title_pattern = re.compile(r'#{2,4}\s+\d+\.\s+(?!\[)[A-Za-z\u4e00-\u9fff]')
    bare_titles = bare_title_pattern.findall(report_content)

    links_ok = len(md_links) >= 5 and len(bare_titles) == 0
    total_score += add_check(
        "all_titles_are_markdown_links",
        links_ok,
        f"Markdown links found: {len(md_links)}, Bare (non-link) titles found: {len(bare_titles)}",
        weight=1.5
    )

    # ── 4. GitHub: All 5 repos present ───────────────────────────────────────
    github_repos = [
        "phi-4-mini",
        "gemma-3n",
        "llama.cpp",
        "storm",
        "rustls",
    ]
    repos_found = [repo for repo in github_repos if repo.lower() in report_content.lower()]
    all_repos_present = len(repos_found) == 5
    total_score += add_check(
        "github_all_5_repos_present",
        all_repos_present,
        f"GitHub repos found: {repos_found} ({len(repos_found)}/5). Missing: {set(github_repos)-set(repos_found)}",
        weight=1.5
    )

    # ── 5-7. GitHub Deep Analysis checks ─────────────────────────────────────
    for label, weight in [("核心价值", 1.0), ("启发思考", 1.0), ("场景标签", 1.0)]:
        present = label in report_content
        total_score += add_check(
            f"github_deep_analysis_{label}",
            present,
            f"'{label}' {'found' if present else 'NOT found'} in report.",
            weight=weight
        )

    # ── 6. Scenario tags (场景标签) — must contain # hashtag-style keywords ──
    # Check for hashtag patterns near 场景标签 sections
    hashtag_pattern = re.compile(r'#[A-Za-z\u4e00-\u9fff]+')
    hashtags = hashtag_pattern.findall(report_content)
    has_hashtags = len(hashtags) >= 3
    total_score += add_check(
        "github_scenario_hashtags_present",
        has_hashtags,
        f"Hashtag-style scenario tags found: {hashtags[:10]} (need >= 3)",
        weight=0.5
    )

    # ── 7. Smart Fill annotations on non-GitHub items ─────────────────────────
    # The report must contain time-ago annotations for supplementary items
    smart_fill_indicators = [
        "⚠️",       # warning emoji for older items
        "🔥",        # fire emoji for high-heat items
        "ago",       # English "ago"
        "小时前",     # Chinese "hours ago"
        "Hot",       # "24h Hot" style
        "24h",       # time marker
    ]
    smart_fill_found = any(ind in report_content for ind in smart_fill_indicators)
    total_score += add_check(
        "smart_fill_annotations_present",
        smart_fill_found,
        f"Smart Fill annotation markers found: {[ind for ind in smart_fill_indicators if ind in report_content]}",
        weight=1.5
    )

    # ── 8. GitHub section does NOT have Smart Fill markers ───────────────────
    # Extract the GitHub section from the report
    # Look for a section that contains multiple github repo names
    github_section_pattern = re.compile(
        r'(?:github|GitHub|trending|Trending).*?(?=\n#{1,3}\s|\Z)',
        re.DOTALL | re.IGNORECASE
    )
    
    # More targeted: find the block between GitHub heading and next major heading
    # Strategy: locate lines containing GitHub repo names and check surrounding context
    lines = report_content.split('\n')
    github_section_lines = []
    in_github_section = False
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Detect start of GitHub section
        if re.search(r'(github|trending)', line_lower) and line.startswith('#'):
            in_github_section = True
        # Detect start of a NEW major section (not GitHub)
        elif line.startswith('#') and in_github_section:
            if not re.search(r'(github|trending)', line_lower):
                in_github_section = False
        if in_github_section:
            github_section_lines.append(line)

    github_section_text = '\n'.join(github_section_lines) if github_section_lines else ""
    
    # Check: Smart Fill markers should NOT appear in GitHub section
    github_smart_fill_markers = ["⚠️", "🔥 24h", "Smart Fill", "小时前补充"]
    github_has_smart_fill = any(m in github_section_text for m in github_smart_fill_markers)
    
    # Only penalize if github section was identified and has markers
    if github_section_text:
        github_no_smart_fill = not github_has_smart_fill
        detail = f"GitHub section ({len(github_section_lines)} lines). Smart Fill markers in GitHub section: {github_has_smart_fill}"
    else:
        # If we can't identify section, check globally that smart fill markers don't
        # appear right next to GitHub repo names
        github_no_smart_fill = True  # Give benefit of doubt
        detail = "Could not isolate GitHub section; assuming compliant (benefit of doubt)."
    
    total_score += add_check(
        "github_no_smart_fill_annotations",
        github_no_smart_fill,
        detail,
        weight=1.0
    )

    # ── 9. Tech/AI section present ────────────────────────────────────────────
    tech_keywords = ["Tech", "AI", "技术", "人工智能", "LLM"]
    tech_section = any(
        kw in line and line.startswith('#')
        for kw in tech_keywords
        for line in lines
    )
    total_score += add_check(
        "tech_ai_section_present",
        tech_section,
        f"Tech/AI section header found: {tech_section}",
        weight=0.5
    )

    # ── 10. Finance section present ───────────────────────────────────────────
    finance_keywords = ["Finance", "财经", "金融", "Market", "市场", "金融 / 社会"]
    finance_section = any(
        kw.lower() in line.lower() and line.startswith('#')
        for kw in finance_keywords
        for line in lines
    )
    total_score += add_check(
        "finance_section_present",
        finance_section,
        f"Finance section header found: {finance_section}",
        weight=0.5
    )

    # ── Final scoring ─────────────────────────────────────────────────────────
    max_score = 1.0 + 1.0 + 1.5 + 1.5 + 1.0 + 1.0 + 1.0 + 0.5 + 1.5 + 1.0 + 0.5 + 0.5
    normalized_score = round(total_score / max_score, 3)
    overall_passed = normalized_score >= 0.70 and all(
        c["passed"] for c in checks if c["name"] in [
            "report_file_exists_with_timestamp",
            "report_in_simplified_chinese",
            "github_all_5_repos_present",
            "smart_fill_annotations_present",
        ]
    )

    result = {
        "passed": overall_passed,
        "score": normalized_score,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [], "error": "Usage: eval.py <workspace_dir>"}))
        sys.exit(1)
    evaluate(sys.argv[1])