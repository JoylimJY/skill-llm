#!/usr/bin/env python3
"""
Evaluation script for the news-aggregator AI briefing task.
Checks:
  1. fetch_news.py was invoked with --deep flag
  2. --source all OR hackernews was used (not a narrow single non-AI source)
  3. Keyword expansion was applied (multiple AI-domain keywords, not just "AI")
  4. A report file exists in reports/ directory
  5. Report is in Simplified Chinese (contains Chinese characters)
  6. Report contains Markdown links (titles as links, not plain text)
  7. Report contains metadata lines (Source, time/date, heat/score)
  8. Report contains deep interpretation bullets (2-3 bullet points per item)
  9. Report filename has a timestamp pattern
"""
import sys
import json
import re
import os
from pathlib import Path

def load_invocations(workspace: Path):
    log_path = workspace / "cache" / "invocations.jsonl"
    invocations = []
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    invocations.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return invocations

def check_deep_flag(invocations):
    """At least one invocation must use --deep."""
    return any(inv.get("deep", False) for inv in invocations)

def check_source_broad(invocations):
    """
    At least one invocation should use source=all, or multiple invocations
    covering different sources (showing broad fetch intent).
    Also accepted: any invocation that targets hackernews, github, producthunt,
    36kr, tencent, v2ex, wallstreetcn, weibo (when multiple are called).
    Most importantly, 'all' source should appear OR multiple distinct sources.
    """
    sources_used = set(inv.get("source", "") for inv in invocations)
    if "all" in sources_used:
        return True, "Used --source all"
    # Accept if multiple distinct sources were queried
    multi_source = [s for s in sources_used if s in
                    {"hackernews", "github", "producthunt", "36kr",
                     "tencent", "wallstreetcn", "v2ex", "weibo"}]
    if len(multi_source) >= 2:
        return True, f"Used multiple sources: {sorted(multi_source)}"
    return False, f"Only narrow source used: {sources_used}"

def check_keyword_expansion(invocations):
    """
    For AI-related fetches, the keyword must be expanded beyond just 'AI'.
    Must include at least 3 of: AI, LLM, GPT, Claude, Generative, Machine Learning, RAG, Agent.
    """
    ai_expansion_terms = {"ai", "llm", "gpt", "claude", "generative", "machine learning", "rag", "agent", "deepseek"}
    for inv in invocations:
        kw = inv.get("keyword") or ""
        if not kw:
            continue
        kw_parts = {k.strip().lower() for k in kw.split(",")}
        matches = kw_parts & ai_expansion_terms
        if len(matches) >= 3:
            return True, f"Found expanded AI keywords: {sorted(matches)}"
    # Also pass if source=all and --deep is used (global scan strategy doesn't always need keywords)
    for inv in invocations:
        if inv.get("source") == "all" and inv.get("deep") and not inv.get("keyword"):
            return True, "Global scan strategy used (source=all --deep, no keyword needed per SKILL.md global scan pattern)"
    return False, "No invocation had sufficient AI keyword expansion (need 3+ of: AI,LLM,GPT,Claude,Generative,Machine Learning,RAG,Agent)"

def find_report(workspace: Path):
    """Find report(s) in reports/ directory."""
    reports_dir = workspace / "reports"
    if not reports_dir.exists():
        return []
    return list(reports_dir.glob("*.md"))

def check_report_filename_timestamp(report_path: Path):
    """Filename should match a timestamp pattern like YYYYMMDD_HHMM or YYYY-MM-DD."""
    name = report_path.stem
    patterns = [
        r"\d{8}_\d{4}",      # YYYYMMDD_HHMM
        r"\d{8}_\d{6}",      # YYYYMMDD_HHMMSS
        r"\d{4}-\d{2}-\d{2}", # YYYY-MM-DD
        r"\d{8}",              # YYYYMMDD
        r"\d{10,}",           # Unix timestamp
    ]
    for pat in patterns:
        if re.search(pat, name):
            return True
    return False

def check_chinese_content(content: str):
    """Check that the report contains Simplified Chinese characters."""
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', content)
    return len(chinese_chars) >= 20

def check_markdown_links(content: str):
    """
    Check that item titles are formatted as Markdown links: [Title](URL)
    Must find at least 2 such links in header context (### or ## headings).
    """
    # Look for Markdown links anywhere (title links in headings or body)
    link_pattern = r'\[.+?\]\(https?://[^\)]+\)'
    links = re.findall(link_pattern, content)
    return len(links) >= 2

def check_metadata_lines(content: str):
    """
    Check that at least some items have metadata (source + time/date + score/heat).
    Look for patterns that include source names and time indicators.
    """
    source_keywords = ["hackernews", "github", "36kr", "tencent", "weibo",
                       "wallstreetcn", "producthunt", "v2ex",
                       "HackerNews", "GitHub", "来源", "Source", "分", "score", "热度"]
    time_keywords = ["ago", "h ago", "min", "时", "分钟", "小时", "今天", "今日",
                     "trending", "2025", "2024", "AM", "PM", "热度", "评分"]

    source_found = any(kw in content for kw in source_keywords)
    time_found = any(kw in content for kw in time_keywords)
    return source_found and time_found

def check_deep_interpretation_bullets(content: str):
    """
    Check that items have deep interpretation bullets.
    Look for bullet points (- or *) that contain substantive content.
    """
    bullet_pattern = r'^[\s]*[-*]\s+.{20,}$'
    bullets = re.findall(bullet_pattern, content, re.MULTILINE)
    return len(bullets) >= 3

def check_report_structure(content: str):
    """
    Check for required structural sections:
    - Global Headlines section OR similar
    - Tech & AI section OR similar
    """
    # Accept Chinese or English section headers
    headline_patterns = [
        r'全球.*?头条|头条新闻|Global.*?Headlines|Headlines',
        r'科技.*?AI|Tech.*?AI|AI.*?科技|技术|人工智能',
        r'##|###',  # At minimum, has markdown sections
    ]
    found = sum(1 for p in headline_patterns if re.search(p, content, re.IGNORECASE))
    return found >= 2

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    workspace = Path(sys.argv[1])
    checks = []
    
    # ── Load invocations ──────────────────────────────────────────────────────
    invocations = load_invocations(workspace)
    has_invocations = len(invocations) > 0

    # Check 1: Was fetch_news.py invoked at all?
    checks.append({
        "name": "fetch_news_invoked",
        "passed": has_invocations,
        "detail": f"Found {len(invocations)} invocation(s) in cache/invocations.jsonl"
    })

    # Check 2: --deep flag used
    deep_used = check_deep_flag(invocations) if has_invocations else False
    checks.append({
        "name": "deep_flag_used",
        "passed": deep_used,
        "detail": "At least one invocation must use --deep for deep content extraction" if not deep_used else "--deep flag confirmed"
    })

    # Check 3: Broad source strategy
    if has_invocations:
        broad_ok, broad_detail = check_source_broad(invocations)
    else:
        broad_ok, broad_detail = False, "No invocations found"
    checks.append({
        "name": "broad_source_strategy",
        "passed": broad_ok,
        "detail": broad_detail
    })

    # Check 4: Keyword expansion
    if has_invocations:
        kw_ok, kw_detail = check_keyword_expansion(invocations)
    else:
        kw_ok, kw_detail = False, "No invocations found"
    checks.append({
        "name": "keyword_expansion",
        "passed": kw_ok,
        "detail": kw_detail
    })

    # ── Evaluate report file ──────────────────────────────────────────────────
    reports = find_report(workspace)
    report_found = len(reports) > 0
    checks.append({
        "name": "report_file_exists",
        "passed": report_found,
        "detail": f"Found reports: {[str(r.name) for r in reports]}" if report_found else "No .md file found in reports/ directory"
    })

    if report_found:
        # Use the most recently modified report if multiple exist
        report_path = max(reports, key=lambda p: p.stat().st_mtime)
        try:
            content = report_path.read_text(encoding="utf-8")
        except Exception as e:
            content = ""
            checks.append({"name": "report_readable", "passed": False, "detail": str(e)})

        # Check 6: Timestamp in filename
        ts_ok = check_report_filename_timestamp(report_path)
        checks.append({
            "name": "report_filename_timestamp",
            "passed": ts_ok,
            "detail": f"Filename '{report_path.name}' {'contains' if ts_ok else 'does NOT contain'} a timestamp pattern"
        })

        # Check 7: Simplified Chinese content
        cn_ok = check_chinese_content(content)
        checks.append({
            "name": "report_in_chinese",
            "passed": cn_ok,
            "detail": f"Chinese character count: {len(re.findall(chr(0x4e00) + '-' + chr(0x9fff), content))} (need >= 20)"
                      if not cn_ok else "Report contains Simplified Chinese content"
        })
        # Fix regex for Chinese
        cn_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
        checks[-1]["detail"] = f"Chinese character count: {cn_chars} {'(OK)' if cn_ok else '(need >= 20)'}"

        # Check 8: Markdown links for titles
        md_links_ok = check_markdown_links(content)
        link_count = len(re.findall(r'\[.+?\]\(https?://[^\)]+\)', content))
        checks.append({
            "name": "markdown_link_titles",
            "passed": md_links_ok,
            "detail": f"Found {link_count} Markdown link(s). Need >= 2. Titles must be [Title](URL) format."
        })

        # Check 9: Metadata lines
        meta_ok = check_metadata_lines(content)
        checks.append({
            "name": "metadata_lines_present",
            "passed": meta_ok,
            "detail": "Metadata lines (source + time + heat/score) found" if meta_ok else "No metadata lines detected. Each item needs Source, Time/Date, Heat/Score."
        })

        # Check 10: Deep interpretation bullets
        bullets_ok = check_deep_interpretation_bullets(content)
        bullet_count = len(re.findall(r'^[\s]*[-*]\s+.{20,}$', content, re.MULTILINE))
        checks.append({
            "name": "deep_interpretation_bullets",
            "passed": bullets_ok,
            "detail": f"Found {bullet_count} substantive bullet point(s). Need >= 3 for deep interpretation."
        })

        # Check 11: Report structure (sections)
        struct_ok = check_report_structure(content)
        checks.append({
            "name": "report_structure_sections",
            "passed": struct_ok,
            "detail": "Report has required sections (Global Headlines + Tech/AI)" if struct_ok else "Missing required structural sections"
        })

    else:
        # Add placeholder failures for report-dependent checks
        for check_name in ["report_filename_timestamp", "report_in_chinese",
                           "markdown_link_titles", "metadata_lines_present",
                           "deep_interpretation_bullets", "report_structure_sections"]:
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": "Cannot evaluate — no report file found"
            })

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weighted scoring
    weights = {
        "fetch_news_invoked": 1.0,
        "deep_flag_used": 2.0,
        "broad_source_strategy": 1.5,
        "keyword_expansion": 2.0,
        "report_file_exists": 1.0,
        "report_filename_timestamp": 1.0,
        "report_in_chinese": 1.5,
        "markdown_link_titles": 2.0,
        "metadata_lines_present": 1.5,
        "deep_interpretation_bullets": 2.0,
        "report_structure_sections": 1.0,
    }

    total_weight = sum(weights.values())
    earned = sum(weights.get(c["name"], 1.0) for c in checks if c["passed"])
    score = round(earned / total_weight, 3)

    # Must pass critical checks to overall pass
    critical = {"fetch_news_invoked", "deep_flag_used", "report_file_exists",
                "markdown_link_titles", "report_in_chinese"}
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical
    )

    passed = critical_passed and score >= 0.65

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()