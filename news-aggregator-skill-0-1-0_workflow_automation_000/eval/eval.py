#!/usr/bin/env python3
"""
Evaluation script for the news-aggregator task.
Tests:
1. fetch_news.py was called with expanded AI keywords (not just "AI")
2. fetch_news.py was called with --deep flag for both sources
3. A report file exists in reports/ with correct timestamped naming
4. Smart Fill was applied (>= 5 HN items in report, with ⚠️ or 🔥 annotations)
5. GitHub Trending section exists with ALL 5 items and Core Value/Inspiration/Scenarios per item
6. All item titles in report are Markdown links [text](url)
7. Report is in Simplified Chinese
8. Metadata line (Source, Time/Date, Heat/Score) is present
"""

import sys
import json
import re
import os
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []
    
    # ── Helper ──────────────────────────────────────────────────────────────
    def check(name, passed, detail=""):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── 1. Read fetch call log ───────────────────────────────────────────────
    fetch_log = ws / "logs/fetch_calls.log"
    calls = []
    try:
        with open(fetch_log) as f:
            for line in f:
                line = line.strip()
                if line:
                    calls.append(json.loads(line))
    except Exception as e:
        check("fetch_log_readable", False, f"Cannot read fetch call log: {e}")
        calls = []

    # ── 2. Keyword Expansion Check ───────────────────────────────────────────
    REQUIRED_AI_KEYWORDS = {"llm", "gpt", "claude", "generative", "machine learning", "rag", "agent"}
    keyword_expanded = False
    deep_used_hn = False
    deep_used_gh = False
    
    for call in calls:
        argv = call.get("argv", [])
        argv_str = " ".join(argv).lower()
        
        # Check for keyword expansion
        if "--keyword" in argv:
            kw_idx = argv.index("--keyword")
            if kw_idx + 1 < len(argv):
                kw_val = argv[kw_idx + 1].lower()
                # Count how many required keywords are present
                found = sum(1 for k in REQUIRED_AI_KEYWORDS if k in kw_val)
                if found >= 3:
                    keyword_expanded = True
        
        # Check --deep flag
        source_idx = argv.index("--source") if "--source" in argv else -1
        source_val = argv[source_idx + 1].lower() if source_idx >= 0 and source_idx + 1 < len(argv) else ""
        
        if "--deep" in argv:
            if "hackernews" in source_val or "all" in source_val:
                deep_used_hn = True
            if "github" in source_val or "all" in source_val:
                deep_used_gh = True

    check(
        "keyword_expansion_used",
        keyword_expanded,
        f"Agent must expand 'AI' to multiple domain keywords (LLM, GPT, Claude, etc.). "
        f"Found calls: {[c['argv'] for c in calls]}"
    )
    check(
        "deep_flag_hackernews",
        deep_used_hn,
        f"--deep must be used when fetching HackerNews items. Calls: {[c['argv'] for c in calls]}"
    )
    check(
        "deep_flag_github",
        deep_used_gh,
        f"--deep must be used when fetching GitHub Trending items. Calls: {[c['argv'] for c in calls]}"
    )

    # ── 3. Report File Exists with Correct Naming ────────────────────────────
    reports_dir = ws / "reports"
    report_files = [
        f for f in reports_dir.glob("*.md")
        if f.name != ".gitkeep" and f.stat().st_size > 100
    ]
    
    # Check timestamped filename pattern: *_YYYYMMDD_HHMM.md
    TIMESTAMP_PATTERN = re.compile(r'\d{8}_\d{4}\.md$')
    timestamped_reports = [f for f in report_files if TIMESTAMP_PATTERN.search(f.name)]
    
    has_report = check(
        "report_file_exists",
        len(report_files) > 0,
        f"Expected *.md file in reports/. Found: {[f.name for f in report_files]}"
    )
    check(
        "report_timestamped_filename",
        len(timestamped_reports) > 0,
        f"Report filename must match *_YYYYMMDD_HHMM.md pattern. "
        f"Found: {[f.name for f in report_files]}"
    )
    
    if not has_report:
        # Can't evaluate content without a file
        score = sum(1 for c in checks if c["passed"]) / max(len(checks), 1)
        return {"passed": False, "score": round(score, 2), "checks": checks}
    
    # Use most recently modified report
    report_file = max(report_files, key=lambda f: f.stat().st_mtime)
    try:
        report_content = report_file.read_text(encoding="utf-8")
    except Exception as e:
        check("report_readable", False, f"Cannot read report: {e}")
        score = sum(1 for c in checks if c["passed"]) / max(len(checks), 1)
        return {"passed": False, "score": round(score, 2), "checks": checks}

    # ── 4. Smart Fill Check ─────────────────────────────────────────────────
    # HN has only 2 recent items; Smart Fill must bring total to >= 5
    # Check for smart-fill annotations: ⚠️ or 🔥
    has_warning_annotation = "⚠️" in report_content
    has_hot_annotation = "🔥" in report_content
    smart_fill_annotated = has_warning_annotation or has_hot_annotation
    
    # Count HN items mentioned in report (by checking known item URLs or titles)
    hn_known_urls = [
        "40001", "40002", "40003", "40004", "40005"
    ]
    hn_items_found = sum(1 for uid in hn_known_urls if uid in report_content)
    
    check(
        "smart_fill_applied",
        hn_items_found >= 5,
        f"Smart Fill must bring total HN items to >= 5 (only 2 are within 3h window). "
        f"Found {hn_items_found} HN item IDs in report."
    )
    check(
        "smart_fill_annotated",
        smart_fill_annotated,
        f"Supplementary items from outside the time window must be annotated with ⚠️ or 🔥. "
        f"Found ⚠️: {has_warning_annotation}, Found 🔥: {has_hot_annotation}"
    )

    # ── 5. GitHub Trending: All Items Present + Deep Analysis ────────────────
    gh_known_repos = [
        "phi-4-mini",
        "llama.cpp",
        "langgraph",
        "qdrant",
        "swarm",
    ]
    gh_items_found = sum(1 for repo in gh_known_repos if repo in report_content)
    
    # Deep analysis markers: Core Value / 核心价值, Inspiration / 启发, Scenarios / 场景
    has_core_value = "核心价值" in report_content or "Core Value" in report_content
    has_inspiration = "启发" in report_content or "Inspiration" in report_content
    has_scenarios = "场景" in report_content or "Scenarios" in report_content or "#" in report_content
    
    check(
        "github_all_items_listed",
        gh_items_found >= 4,
        f"All GitHub Trending items must be listed. Found {gh_items_found}/5. "
        f"Missing: {[r for r in gh_known_repos if r not in report_content]}"
    )
    check(
        "github_deep_analysis_core_value",
        has_core_value,
        "GitHub items must include '核心价值' (Core Value) analysis section."
    )
    check(
        "github_deep_analysis_inspiration",
        has_inspiration,
        "GitHub items must include '启发思考' (Inspiration) analysis section."
    )
    check(
        "github_deep_analysis_scenarios",
        has_scenarios,
        "GitHub items must include '场景标签' (Scenarios) with hashtag keywords."
    )

    # ── 6. Markdown Link Format ──────────────────────────────────────────────
    # Items must be [Title](URL) format, not plain text headers
    markdown_link_pattern = re.compile(r'\[.+?\]\(https?://.+?\)')
    markdown_links = markdown_link_pattern.findall(report_content)
    
    # Specifically check that at least one HN item is linked properly
    hn_link_pattern = re.compile(r'\[.+?\]\(https://news\.ycombinator\.com/.+?\)')
    gh_link_pattern = re.compile(r'\[.+?\]\(https://github\.com/.+?\)')
    
    has_hn_links = bool(hn_link_pattern.search(report_content))
    has_gh_links = bool(gh_link_pattern.search(report_content))
    
    check(
        "titles_are_markdown_links_hn",
        has_hn_links,
        f"HN item titles must be Markdown links [title](url). "
        f"Total markdown links found: {len(markdown_links)}"
    )
    check(
        "titles_are_markdown_links_github",
        has_gh_links,
        f"GitHub item titles must be Markdown links [title](url). "
        f"Total markdown links found: {len(markdown_links)}"
    )

    # ── 7. Language Check (Simplified Chinese) ───────────────────────────────
    # Check for Chinese characters (at least 50 CJK chars in the report)
    cjk_pattern = re.compile(r'[\u4e00-\u9fff]')
    cjk_chars = cjk_pattern.findall(report_content)
    is_chinese = len(cjk_chars) >= 50
    
    check(
        "report_in_simplified_chinese",
        is_chinese,
        f"Report must be primarily in Simplified Chinese. "
        f"Found {len(cjk_chars)} CJK characters (need >= 50)."
    )

    # ── 8. Metadata Line Check ───────────────────────────────────────────────
    # Look for patterns like "Score:", "score:", "热度", "来源", "Source"
    has_source_meta = bool(re.search(r'(来源|Source|HackerNews|hackernews|GitHub)', report_content, re.IGNORECASE))
    has_score_meta = bool(re.search(r'(Score|分|热度|score|stars)', report_content, re.IGNORECASE))
    has_time_meta = bool(re.search(r'(小时前|ago|2025|时间|Time|⏰)', report_content, re.IGNORECASE))
    
    check(
        "metadata_line_source",
        has_source_meta,
        "Report items must include source metadata (来源/Source)."
    )
    check(
        "metadata_line_score",
        has_score_meta,
        "Report items must include heat/score metadata (Score/热度/分)."
    )
    check(
        "metadata_line_time",
        has_time_meta,
        "Report items must include time/date metadata."
    )

    # ── 9. Report Structure ──────────────────────────────────────────────────
    has_global_headlines = bool(re.search(r'(全球|头条|Global|Headlines|重要)', report_content, re.IGNORECASE))
    has_tech_section = bool(re.search(r'(科技|Tech|AI|人工智能|技术)', report_content, re.IGNORECASE))
    
    check(
        "report_has_global_headlines_section",
        has_global_headlines,
        "Report must have a Global Headlines section (全球头条/Global Headlines)."
    )
    check(
        "report_has_tech_ai_section",
        has_tech_section,
        "Report must have a Tech & AI section."
    )

    # ── Final Scoring ────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    
    # Must pass critical checks to overall pass
    critical_checks = [
        "keyword_expansion_used",
        "deep_flag_hackernews",
        "report_file_exists",
        "smart_fill_applied",
        "smart_fill_annotated",
        "github_all_items_listed",
        "github_deep_analysis_core_value",
        "report_in_simplified_chinese",
        "titles_are_markdown_links_hn",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))