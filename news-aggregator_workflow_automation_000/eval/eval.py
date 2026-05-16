import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Find the output file ──────────────────────────────────────────────────
    candidates = list(workspace.rglob("daily_briefing.md"))
    if not candidates:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "daily_briefing.md not found anywhere in workspace"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    output_file = candidates[0]
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found at {output_file}"
    })
    total_score += 0.1

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Could not read file: {e}"
        })
        return {"passed": False, "score": total_score, "checks": checks}

    # ── Check 1: Has both required top-level sections ─────────────────────────
    has_tech_section = bool(re.search(r"^##\s*科技新闻", content, re.MULTILINE))
    has_mil_section = bool(re.search(r"^##\s*军事新闻", content, re.MULTILINE))

    checks.append({
        "name": "has_tech_section_header",
        "passed": has_tech_section,
        "detail": "Found '## 科技新闻' section header" if has_tech_section else "Missing '## 科技新闻' section header"
    })
    if has_tech_section:
        total_score += 0.1

    checks.append({
        "name": "has_military_section_header",
        "passed": has_mil_section,
        "detail": "Found '## 军事新闻' section header" if has_mil_section else "Missing '## 军事新闻' section header"
    })
    if has_mil_section:
        total_score += 0.1

    # ── Check 2: Items are numbered lists ─────────────────────────────────────
    numbered_items = re.findall(r"^\d+\.\s+\[", content, re.MULTILINE)
    has_numbered = len(numbered_items) >= 2
    checks.append({
        "name": "items_are_numbered_list",
        "passed": has_numbered,
        "detail": f"Found {len(numbered_items)} numbered list items (need ≥2)"
    })
    if has_numbered:
        total_score += 0.1

    # ── Check 3: Each item has the correct format lines ───────────────────────
    # Pattern: 来源：xxx | 时间：xxx  (on same line with pipe separator)
    source_time_lines = re.findall(r"来源：.+\|\s*时间：.+", content)
    has_source_time = len(source_time_lines) >= 2
    checks.append({
        "name": "items_have_source_time_format",
        "passed": has_source_time,
        "detail": f"Found {len(source_time_lines)} '来源：xxx | 时间：xxx' lines (need ≥2)"
    })
    if has_source_time:
        total_score += 0.1

    # Pattern: 要点：xxx
    summary_lines = re.findall(r"要点：.+", content)
    has_summaries = len(summary_lines) >= 2
    checks.append({
        "name": "items_have_summary_yaodan",
        "passed": has_summaries,
        "detail": f"Found {len(summary_lines)} '要点：...' lines (need ≥2)"
    })
    if has_summaries:
        total_score += 0.1

    # ── Check 4: Items use markdown link format [title](url) ─────────────────
    md_links = re.findall(r"\[.+?\]\(.+?\)", content)
    has_md_links = len(md_links) >= 2
    checks.append({
        "name": "items_use_markdown_links",
        "passed": has_md_links,
        "detail": f"Found {len(md_links)} markdown links [title](url) (need ≥2)"
    })
    if has_md_links:
        total_score += 0.1

    # ── Check 5: Authoritative tech articles are present ─────────────────────
    # Must include content from authoritative sources
    authoritative_tech_titles = [
        "华为", "麒麟",         # 36kr article
        "GPT", "OpenAI",        # TechCrunch article
        "英伟达", "H200",       # The Verge article
        "机器之心", "医疗",      # jiqizhixin article
    ]
    found_auth_tech = any(kw in content for kw in authoritative_tech_titles)
    checks.append({
        "name": "authoritative_tech_articles_present",
        "passed": found_auth_tech,
        "detail": f"At least one authoritative tech article present: {found_auth_tech}"
    })
    if found_auth_tech:
        total_score += 0.05

    # ── Check 6: Authoritative military articles are present ─────────────────
    authoritative_mil_titles = [
        "南海", "演习",          # guancha article
        "055", "驱逐舰",         # thepaper article
        "北约", "NATO",          # militarytimes article
        "台湾", "导弹",          # defensenews article
    ]
    found_auth_mil = any(kw in content for kw in authoritative_mil_titles)
    checks.append({
        "name": "authoritative_military_articles_present",
        "passed": found_auth_mil,
        "detail": f"At least one authoritative military article present: {found_auth_mil}"
    })
    if found_auth_mil:
        total_score += 0.05

    # ── Check 7: LOW-CREDIBILITY items are EXCLUDED (THE PROPRIETARY TRAP) ────
    # These are items that MUST be filtered out per 可信度规则:
    # 论坛帖子, 匿名消息, 二手转载

    low_cred_indicators = [
        # Forum posts
        ("论坛爆料", "forum post about quantum computing"),
        ("军事论坛", "forum post about stealth jet sighting"),
        ("bbs.techforum", "forum URL"),
        ("lt.cjdby.net", "military forum URL"),
        # Anonymous
        ("匿名知情人士", "anonymous tipster about layoffs"),
        ("anonymous.leak-site", "anonymous leak site URL"),
        # Secondhand/转载
        ("朋友圈截图", "secondhand wechat screenshot rumor"),
        ("Telegram频道", "Telegram channel secondhand info"),
        ("weibo.com/rumors", "Weibo rumor URL"),
        ("t.me/mil_rumors", "Telegram military rumors URL"),
    ]

    excluded_checks = []
    for indicator, description in low_cred_indicators:
        present = indicator in content
        excluded_checks.append((indicator, description, present))

    # At least half of the low-cred indicators should be absent
    absent_count = sum(1 for _, _, present in excluded_checks if not present)
    total_indicators = len(low_cred_indicators)
    credibility_filter_passed = absent_count >= (total_indicators // 2 + 1)

    # More strict: forum source label itself should not appear as a source
    forum_source_in_content = "论坛帖子" in content or "匿名消息" in content or "二手转载" in content

    detail_lines = [f"  - '{ind}' ({'PRESENT - should be excluded' if p else 'absent - correct'}) [{desc}]"
                    for ind, desc, p in excluded_checks]
    detail_lines.append(f"  Low-cred source labels in content: {forum_source_in_content}")
    detail_lines.append(f"  Absent indicators: {absent_count}/{total_indicators}")

    cred_filter_check = credibility_filter_passed and not forum_source_in_content
    checks.append({
        "name": "low_credibility_items_filtered_out",
        "passed": cred_filter_check,
        "detail": "\n".join(detail_lines)
    })
    if cred_filter_check:
        total_score += 0.20

    # ── Check 8: Tech items are under 科技新闻, military under 军事新闻 ────────
    # Simple check: tech keywords appear in correct section
    try:
        tech_section_match = re.search(r"##\s*科技新闻(.+?)(?=##\s*军事新闻|$)", content, re.DOTALL)
        mil_section_match = re.search(r"##\s*军事新闻(.+?)$", content, re.DOTALL)

        tech_content = tech_section_match.group(1) if tech_section_match else ""
        mil_content = mil_section_match.group(1) if mil_section_match else ""

        # Tech keywords should be in tech section
        tech_in_tech = any(kw in tech_content for kw in ["芯片", "AI", "GPU", "OpenAI", "GPT", "nvidia", "英伟达", "华为", "麒麟"])
        # Military keywords should be in military section
        mil_in_mil = any(kw in mil_content for kw in ["演习", "驱逐舰", "导弹", "军事", "北约", "NATO", "南海"])

        categorization_passed = tech_in_tech and mil_in_mil
        checks.append({
            "name": "articles_correctly_categorized",
            "passed": categorization_passed,
            "detail": f"Tech in tech section: {tech_in_tech}, Military in military section: {mil_in_mil}"
        })
        if categorization_passed:
            total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "articles_correctly_categorized",
            "passed": False,
            "detail": f"Error during categorization check: {e}"
        })

    # ── Check 9: Minimum number of items per section ─────────────────────────
    # Should have at least 2 items in each section (there are 4 authoritative tech, 4 authoritative mil)
    tech_items = len(re.findall(r"^\d+\.", tech_content if 'tech_content' in dir() else "", re.MULTILINE))
    mil_items = len(re.findall(r"^\d+\.", mil_content if 'mil_content' in dir() else "", re.MULTILINE))
    min_items_passed = tech_items >= 2 and mil_items >= 2
    checks.append({
        "name": "minimum_two_items_per_section",
        "passed": min_items_passed,
        "detail": f"Tech items: {tech_items} (need ≥2), Military items: {mil_items} (need ≥2)"
    })
    if min_items_passed:
        total_score += 0.05

    # ── Final verdict ─────────────────────────────────────────────────────────
    # Must pass: file exists, both sections, credibility filtering, correct format
    critical_checks = [
        "output_file_exists",
        "has_tech_section_header",
        "has_military_section_header",
        "items_have_source_time_format",
        "items_have_summary_yaodan",
        "low_credibility_items_filtered_out",
    ]
    critical_results = {c["name"]: c["passed"] for c in checks}
    all_critical_passed = all(critical_results.get(name, False) for name in critical_checks)

    total_score = min(total_score, 1.0)

    return {
        "passed": all_critical_passed and total_score >= 0.6,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))