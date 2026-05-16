import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── 1. Find news_report.md ──────────────────────────────────────────────
    candidates = list(workspace.rglob("news_report.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "news_report.md not found anywhere in workspace"}]
        }
    
    report_path = candidates[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    # ── 2. Check: Chinese section headers present ───────────────────────────
    # SKILL.md mandates: ## 科技新闻  and  ## 军事新闻
    has_tech_header = bool(re.search(r"##\s*科技新闻", content))
    has_mil_header = bool(re.search(r"##\s*军事新闻", content))
    checks.append({
        "name": "chinese_tech_header",
        "passed": has_tech_header,
        "detail": "Found '## 科技新闻'" if has_tech_header else "Missing required Chinese header '## 科技新闻'"
    })
    checks.append({
        "name": "chinese_military_header",
        "passed": has_mil_header,
        "detail": "Found '## 军事新闻'" if has_mil_header else "Missing required Chinese header '## 军事新闻'"
    })

    # ── 3. Check: Items use [标题](链接) markdown link format ───────────────
    md_links = re.findall(r'\[.+?\]\(http[^\)]+\)', content)
    has_md_links = len(md_links) >= 3
    checks.append({
        "name": "markdown_link_format",
        "passed": has_md_links,
        "detail": f"Found {len(md_links)} markdown [title](url) links (need ≥3)"
    })

    # ── 4. Check: 来源 field present ────────────────────────────────────────
    source_lines = re.findall(r'来源[：:]\s*\S+', content)
    has_source_field = len(source_lines) >= 3
    checks.append({
        "name": "source_field_present",
        "passed": has_source_field,
        "detail": f"Found {len(source_lines)} '来源：' fields (need ≥3)"
    })

    # ── 5. Check: 要点 field present ────────────────────────────────────────
    summary_lines = re.findall(r'要点[：:]\s*\S+', content)
    has_summary_field = len(summary_lines) >= 3
    checks.append({
        "name": "summary_field_present",
        "passed": has_summary_field,
        "detail": f"Found {len(summary_lines)} '要点：' fields (need ≥3)"
    })

    # ── 6. Check: 时间 field present ────────────────────────────────────────
    time_lines = re.findall(r'时间[：:]\s*\S+', content)
    has_time_field = len(time_lines) >= 3
    checks.append({
        "name": "time_field_present",
        "passed": has_time_field,
        "detail": f"Found {len(time_lines)} '时间：' fields (need ≥3)"
    })

    # ── 7. Check: Credibility filtering — forum/anonymous excluded ──────────
    # Items that should NOT appear (from mock data marked as forum_anonymous or second_hand):
    forbidden_titles = [
        "论坛爆料",           # 36kr forum post
        "网传",               # thepaper forum post  
        "Anonymous source claims Apple to buy Netflix",  # theverge rumor
        "Forum Post: Alleged leaked",  # militarytimes forum
        "转载：某博主",       # ithome second-hand
    ]
    credibility_violations = []
    for ft in forbidden_titles:
        if ft in content:
            credibility_violations.append(ft)
    
    credibility_ok = len(credibility_violations) == 0
    checks.append({
        "name": "credibility_filtering",
        "passed": credibility_ok,
        "detail": "No forum/anonymous/second-hand content found" if credibility_ok
                  else f"Included unreliable content: {credibility_violations}"
    })

    # ── 8. Check: Official content IS included ──────────────────────────────
    # At least some of the verified official articles must appear
    expected_official = [
        "阿里巴巴",        # 36kr official
        "华为鸿蒙",        # ithome official
        "OpenAI",          # techcrunch official
        "TSMC",            # arstechnica official
        "Defense News",    # defensenews official (in source field)
    ]
    found_official = [t for t in expected_official if t in content]
    has_sufficient_official = len(found_official) >= 3
    checks.append({
        "name": "official_content_included",
        "passed": has_sufficient_official,
        "detail": f"Found {len(found_official)}/5 expected official articles: {found_official}"
    })

    # ── 9. Check: Both domestic AND international sources covered ───────────
    # Domestic tech markers
    domestic_tech_sources = ["36氪", "机器之心", "IT之家", "量子位"]
    has_domestic_tech = any(s in content for s in domestic_tech_sources)
    
    # International tech markers
    intl_tech_sources = ["TechCrunch", "The Verge", "Ars Technica", "Wired"]
    has_intl_tech = any(s in content for s in intl_tech_sources)
    
    # Domestic military markers
    domestic_mil_sources = ["观察者网", "澎湃新闻", "腾讯军事"]
    has_domestic_mil = any(s in content for s in domestic_mil_sources)
    
    # International military markers
    intl_mil_sources = ["Defense News", "Jane's Defence", "Military Times"]
    has_intl_mil = any(s in content for s in intl_mil_sources)
    
    coverage_count = sum([has_domestic_tech, has_intl_tech, has_domestic_mil, has_intl_mil])
    has_broad_coverage = coverage_count >= 3
    checks.append({
        "name": "multi_category_coverage",
        "passed": has_broad_coverage,
        "detail": (f"Coverage: domestic_tech={has_domestic_tech}, intl_tech={has_intl_tech}, "
                   f"domestic_mil={has_domestic_mil}, intl_mil={has_intl_mil} ({coverage_count}/4 categories)")
    })

    # ── 10. Check: Numbered list items ──────────────────────────────────────
    numbered_items = re.findall(r'^\s*\d+\.\s+\[', content, re.MULTILINE)
    has_numbered = len(numbered_items) >= 3
    checks.append({
        "name": "numbered_list_format",
        "passed": has_numbered,
        "detail": f"Found {len(numbered_items)} numbered list items starting with [title](url)"
    })

    # ── 11. Check: 来源 | 时间 combined format (pipe separator) ─────────────
    # SKILL.md format: 来源：xxx | 时间：xxx
    pipe_lines = re.findall(r'来源[：:].+?\|.+?时间[：:]', content)
    has_pipe_format = len(pipe_lines) >= 2
    checks.append({
        "name": "source_time_pipe_format",
        "passed": has_pipe_format,
        "detail": f"Found {len(pipe_lines)} '来源：xxx | 时间：xxx' formatted lines (need ≥2)"
    })

    # ── Score calculation ────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    
    # Must pass critical checks to pass overall
    critical_checks = ["chinese_tech_header", "chinese_military_header", 
                       "credibility_filtering", "official_content_included",
                       "multi_category_coverage"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    
    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))