#!/usr/bin/env python3
"""
Evaluation script for the news-aggregator-skill task.
Checks that the agent correctly:
  1. Saved a report file to the reports/ directory with a timestamped name (.md)
  2. Used Markdown link format for titles: ### N. [Title](URL)
  3. Applied Smart Fill with annotations (⚠️ or 🔥) for HN/V2EX items outside the 3h window
  4. Correctly identified in-window items (≤ 3h) separately from annotated fill items
  5. Applied GitHub Trending Exception: ALL 5 repos listed, NO smart-fill annotation, each with 核心价值/Core Value, 启发思考/Inspiration, and 场景标签/Scenarios
  6. Report is written in Simplified Chinese (contains Chinese characters)
  7. Report has substantial content (not just a stub)
"""

import sys
import json
import re
from pathlib import Path

def check(name, passed, detail=""):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []
    score = 0.0

    # ── CHECK 1: Report file exists in reports/ with .md extension ────────────
    try:
        reports_dir = ws / "reports"
        report_files = list(reports_dir.glob("*.md"))
        # Filter out old distractor
        report_files = [f for f in report_files if f.name != "old_report.md"]
        
        if not report_files:
            checks.append(check("report_file_exists", False, 
                "No .md file found in reports/ directory. Agent must save to reports/ with timestamped filename."))
            # Cannot continue without file
            return {"passed": False, "score": 0.0, "checks": checks}
        
        # Use the most recently created report file
        report_file = max(report_files, key=lambda f: f.stat().st_mtime)
        content = report_file.read_text(encoding="utf-8")
        
        # Check filename has date-like pattern
        has_timestamp = bool(re.search(r'20\d{6}', report_file.name) or 
                            re.search(r'\d{4}[-_]\d{2}[-_]\d{2}', report_file.name) or
                            re.search(r'\d{8}', report_file.name))
        checks.append(check("report_timestamped_filename", has_timestamp,
            f"File: {report_file.name}. Expected timestamp pattern like YYYYMMDD in filename."))
        if has_timestamp:
            score += 0.1
            
    except Exception as e:
        checks.append(check("report_file_exists", False, f"Exception: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── CHECK 2: Report has substantial content ────────────────────────────────
    try:
        content_len = len(content.strip())
        is_substantial = content_len > 800
        checks.append(check("report_has_substantial_content", is_substantial,
            f"Report length: {content_len} chars. Expected > 800 chars for a meaningful briefing."))
        if is_substantial:
            score += 0.05
    except Exception as e:
        checks.append(check("report_has_substantial_content", False, f"Exception: {e}"))

    # ── CHECK 3: Contains Chinese characters (Simplified Chinese output) ───────
    try:
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', content))
        checks.append(check("report_in_simplified_chinese", has_chinese,
            "Report must be written in Simplified Chinese (简体中文)."))
        if has_chinese:
            score += 0.05
    except Exception as e:
        checks.append(check("report_in_simplified_chinese", False, f"Exception: {e}"))

    # ── CHECK 4: Markdown link format for titles ───────────────────────────────
    try:
        # Look for properly formatted markdown links in headings
        # Pattern: ### N. [Any Title](URL)  OR  ## [Title](URL)  OR  **[Title](URL)**
        md_links_in_headings = re.findall(
            r'(?:#{1,4}\s+\d*\.?\s*\[.+?\]\(https?://[^\)]+\)|^\*{1,2}\[.+?\]\(https?://[^\)]+\))',
            content, re.MULTILINE
        )
        # Also check for any markdown links at all (more lenient)
        any_md_links = re.findall(r'\[.+?\]\(https?://[^\)]+\)', content)
        
        has_md_links = len(any_md_links) >= 3  # At least 3 properly linked items
        has_heading_md_links = len(md_links_in_headings) >= 2
        
        passed_links = has_md_links and has_heading_md_links
        checks.append(check("titles_use_markdown_link_format", passed_links,
            f"Found {len(md_links_in_headings)} heading-style markdown links and {len(any_md_links)} total markdown links. "
            f"Titles MUST be formatted as ### N. [Title](URL), not plain text."))
        if passed_links:
            score += 0.15
    except Exception as e:
        checks.append(check("titles_use_markdown_link_format", False, f"Exception: {e}"))

    # ── CHECK 5: Smart Fill annotations present (for non-GitHub items) ─────────
    try:
        # Look for annotation markers as specified in SKILL.md
        annotation_patterns = [
            r'⚠️',          # Warning emoji annotation
            r'🔥',           # Fire emoji for hot items
            r'24h\s*Hot',    # Text annotation
            r'24h\s*热',     # Chinese annotation
            r'Smart\s*Fill',
            r'补充',          # Chinese for "supplement"
            r'超出时间窗',    # "outside time window" in Chinese
            r'时间范围外',
        ]
        
        annotation_found = any(
            re.search(pattern, content, re.IGNORECASE) 
            for pattern in annotation_patterns
        )
        
        checks.append(check("smart_fill_annotations_present", annotation_found,
            "Report must annotate Smart Fill items (items outside the 3h window) with markers like ⚠️, 🔥, or similar. "
            "HN/V2EX have items from 8h, 12h, 18h, 22h ago that should trigger Smart Fill."))
        if annotation_found:
            score += 0.15
    except Exception as e:
        checks.append(check("smart_fill_annotations_present", False, f"Exception: {e}"))

    # ── CHECK 6: In-window items included (the 2 HN items within 3h) ──────────
    try:
        # The 2 HN items within 3h window
        in_window_signals = [
            "LLM Agents Are Eating the World",
            "RAG vs Fine-Tuning",
        ]
        in_window_found = sum(1 for sig in in_window_signals if sig.lower() in content.lower())
        
        passed_inwindow = in_window_found >= 1  # At least 1 of the 2 in-window items
        checks.append(check("in_window_items_included", passed_inwindow,
            f"Found {in_window_found}/2 in-window HN items (within 3h). "
            "Items: 'LLM Agents Are Eating the World' (1h20m ago), 'RAG vs Fine-Tuning' (2h45m ago)."))
        if passed_inwindow:
            score += 0.05
    except Exception as e:
        checks.append(check("in_window_items_included", False, f"Exception: {e}"))

    # ── CHECK 7: GitHub repos ALL present (GitHub Exception — all 5 repos) ─────
    try:
        github_repos = [
            "graphrag",
            "ollama",
            "unsloth", 
            "pydantic-ai",
            "litellm",
        ]
        repos_found = [repo for repo in github_repos if repo.lower() in content.lower()]
        all_repos_present = len(repos_found) == 5
        
        checks.append(check("github_all_repos_listed", all_repos_present,
            f"Found {len(repos_found)}/5 GitHub repos: {repos_found}. "
            "SKILL.md GitHub Exception: ALL fetched items must be listed, no exceptions."))
        if all_repos_present:
            score += 0.15
    except Exception as e:
        checks.append(check("github_all_repos_listed", False, f"Exception: {e}"))

    # ── CHECK 8: GitHub items have Deep Analysis (核心价值 / Core Value) ────────
    try:
        deep_analysis_patterns = [
            r'核心价值',
            r'Core\s*Value',
            r'启发思考',
            r'Inspiration',
            r'场景标签',
            r'Scenarios',
        ]
        
        # Count how many deep analysis sections appear
        found_patterns = [p for p in deep_analysis_patterns 
                         if re.search(p, content, re.IGNORECASE)]
        
        # Require at least 2 of the 3 types (in Chinese or English)
        has_core_value = any(re.search(p, content, re.IGNORECASE) 
                            for p in [r'核心价值', r'Core\s*Value'])
        has_inspiration = any(re.search(p, content, re.IGNORECASE) 
                             for p in [r'启发思考', r'Inspiration'])
        has_scenarios = any(re.search(p, content, re.IGNORECASE) 
                           for p in [r'场景标签', r'Scenarios', r'#\w+\s+#\w+'])
        
        deep_analysis_present = sum([has_core_value, has_inspiration, has_scenarios]) >= 2
        
        checks.append(check("github_deep_analysis_present", deep_analysis_present,
            f"GitHub Exception requires EACH repo to have 核心价值, 启发思考, and 场景标签. "
            f"Found: core_value={has_core_value}, inspiration={has_inspiration}, scenarios={has_scenarios}. "
            f"Matched patterns: {found_patterns}"))
        if deep_analysis_present:
            score += 0.15
    except Exception as e:
        checks.append(check("github_deep_analysis_present", False, f"Exception: {e}"))

    # ── CHECK 9: Scenario tags present (# hashtag format) ─────────────────────
    try:
        # Scenario tags: #RAG #LocalFirst #Rust style
        hashtag_pattern = re.findall(r'#[A-Za-z\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff]+', content)
        has_hashtags = len(hashtag_pattern) >= 3  # At least 3 scenario tags across repos
        
        checks.append(check("scenario_hashtags_present", has_hashtags,
            f"Found {len(hashtag_pattern)} hashtag-style scenario tags: {hashtag_pattern[:10]}. "
            "Expected 3-5 per GitHub repo, e.g. #RAG #LocalFirst #Python."))
        if has_hashtags:
            score += 0.10
    except Exception as e:
        checks.append(check("scenario_hashtags_present", False, f"Exception: {e}"))

    # ── CHECK 10: GitHub items NOT annotated with Smart Fill markers ───────────
    try:
        # GitHub items should NOT have smart fill markers near them
        github_section_match = re.search(
            r'(github|GitHub|trending|Trending).{0,2000}',
            content, re.IGNORECASE | re.DOTALL
        )
        
        if github_section_match:
            github_section = github_section_match.group(0)
            # Check that annotation markers don't appear near github items
            smart_fill_in_github = bool(re.search(r'⚠️|Smart\s*Fill|补充.*github|github.*补充', 
                                                    github_section, re.IGNORECASE))
            no_smart_fill_in_github = not smart_fill_in_github
        else:
            no_smart_fill_in_github = True  # Can't assess, give benefit of doubt
            
        checks.append(check("github_no_smart_fill_contamination", no_smart_fill_in_github,
            "GitHub Trending section must NOT contain Smart Fill annotations. "
            "SKILL.md explicitly prohibits Smart Fill for GitHub Trending."))
        if no_smart_fill_in_github:
            score += 0.05
    except Exception as e:
        checks.append(check("github_no_smart_fill_contamination", False, f"Exception: {e}"))

    # ── FINAL SCORE ────────────────────────────────────────────────────────────
    # Critical checks that determine overall pass/fail
    critical_passed = (
        checks[0]["passed"] and  # report file exists
        checks[3]["passed"] and  # markdown links
        checks[6]["passed"] and  # all github repos
        checks[7]["passed"]      # github deep analysis
    )
    
    final_passed = critical_passed and score >= 0.55
    
    return {
        "passed": final_passed,
        "score": round(min(score, 1.0), 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, 
                          "checks": [{"name": "args", "passed": False, 
                                      "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = run_eval(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))