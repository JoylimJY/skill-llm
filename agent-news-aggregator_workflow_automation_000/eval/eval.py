import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime

def evaluate(workspace: str):
    checks = []
    
    # ─── Helper ───────────────────────────────────────────────
    def add_check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # ─── Find output file ──────────────────────────────────────
    briefing_path = None
    # Primary location: workspace root briefing.md
    candidate = Path(workspace) / "briefing.md"
    if candidate.exists():
        briefing_path = candidate
    else:
        # Search recursively
        matches = list(Path(workspace).rglob("briefing.md"))
        if matches:
            briefing_path = matches[0]
    
    if briefing_path is None:
        add_check("output_file_exists", False, "briefing.md not found anywhere in workspace")
        return checks, 0.0
    
    try:
        content = briefing_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("output_file_readable", False, f"Could not read briefing.md: {e}")
        return checks, 0.0
    
    add_check("output_file_exists", True, f"Found briefing.md at {briefing_path}")
    
    # ─── Check 1: Lobster emoji header present ─────────────────
    # Must contain: ## 🦞 [target] 新闻简报 · [date]
    lobster_pattern = r'##\s*🦞'
    has_lobster = bool(re.search(lobster_pattern, content))
    add_check(
        "header_lobster_emoji",
        has_lobster,
        "Found '## 🦞' header" if has_lobster else "Missing '## 🦞' in header — required by SKILL.md format"
    )
    
    # ─── Check 2: Target name "NovaMind" in header ─────────────
    # Agent must read config to find target.name = "NovaMind"
    novamind_in_header = bool(re.search(r'##\s*🦞\s*NovaMind', content))
    add_check(
        "header_target_novamind",
        novamind_in_header,
        "Header correctly identifies target as NovaMind" if novamind_in_header else
        "Header does not contain 'NovaMind' — agent likely did not read config/openclaw.yaml"
    )
    
    # ─── Check 3: Date in header format YYYY-MM-DD ─────────────
    date_pattern = r'##\s*🦞.*新闻简报\s*·\s*(\d{4}-\d{2}-\d{2})'
    date_match = re.search(date_pattern, content)
    if date_match:
        date_str = date_match.group(1)
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            add_check("header_date_format", True, f"Date '{date_str}' is correctly formatted as YYYY-MM-DD")
        except ValueError:
            add_check("header_date_format", False, f"Date '{date_str}' could not be parsed as YYYY-MM-DD")
    else:
        add_check("header_date_format", False, "No YYYY-MM-DD date found in header line with 🦞")
    
    # ─── Check 4: All 5 required sections present ──────────────
    required_sections = [
        ("section_1_direct_news",    r'###\s*一[、.．:：]?\s*直接提到'),
        ("section_2_community",      r'###\s*二[、.．:：]?\s*(用户案例|社区)'),
        ("section_3_industry",       r'###\s*三[、.．:：]?\s*行业新闻'),
        ("section_4_competitors",    r'###\s*四[、.．:：]?\s*竞品动态'),
        ("section_5_signal",         r'###\s*五[、.．:：]?\s*今日核心信号'),
    ]
    
    for check_name, pattern in required_sections:
        found = bool(re.search(pattern, content))
        add_check(
            check_name,
            found,
            f"Section found" if found else f"Missing required section matching: {pattern}"
        )
    
    # ─── Check 5: Section 五 uses blockquote (>) syntax ────────
    # According to SKILL.md format: > [对今日信息的最重要判断，1-2句]
    sig_section_match = re.search(
        r'###\s*五[、.．:：]?\s*今日核心信号.*?(\n|$)(.*?)(?=###|\Z)',
        content, re.DOTALL
    )
    if sig_section_match:
        sig_content = sig_section_match.group(2)
        has_blockquote = bool(re.search(r'^\s*>', sig_content, re.MULTILINE))
        add_check(
            "section_5_blockquote_format",
            has_blockquote,
            "Section 五 uses '>' blockquote as required" if has_blockquote
            else "Section 五 missing '>' blockquote format — required by SKILL.md"
        )
    else:
        add_check("section_5_blockquote_format", False, "Could not find Section 五 content to check blockquote")
    
    # ─── Check 6: Empty sections use prescribed placeholder ────
    # "若某类别无内容，写：「暂无相关内容」"
    # At least one section should either have content or use the placeholder
    placeholder_text = "暂无相关内容"
    # Check that if any section appears empty, it uses the placeholder
    # We just verify the placeholder string exists somewhere (likely used for some section)
    has_placeholder_or_content = (
        placeholder_text in content or
        # Has substantive list items under sections
        bool(re.search(r'###.*\n+\s*[-*]', content))
    )
    add_check(
        "empty_section_placeholder",
        has_placeholder_or_content,
        f"Placeholder '暂无相关内容' found or sections have content" if has_placeholder_or_content
        else "No content and no '暂无相关内容' placeholder found in any section"
    )
    
    # ─── Check 7: Content from official_urls (Route A) ─────────
    # The config has official_urls pointing to localhost:8080
    # Agent should have fetched /blog, /releases, /news
    # Evidence: content from mock server should appear
    mock_content_markers = [
        "NovaMind v2.5",
        "Series B",
        "CloudBase",
        "v2.5.0",
        "multi-modal",
        "Multi-Modal",
        "50M",
        "$50",
        "Horizon",
    ]
    route_a_hits = sum(1 for marker in mock_content_markers if marker in content)
    route_a_passed = route_a_hits >= 2
    add_check(
        "route_a_official_content",
        route_a_passed,
        f"Found {route_a_hits}/{len(mock_content_markers)} mock server content markers in briefing "
        f"(need ≥2). Agent {'correctly fetched' if route_a_passed else 'likely did NOT fetch'} official_urls from config."
    )
    
    # ─── Check 8: Keywords from config appear in briefing ──────
    # config keywords: "NovaMind AI", "nova-mind", "NovaMind"
    # These should appear as evidence the agent used the config keywords
    config_keywords_found = sum(1 for kw in ["NovaMind AI", "nova-mind", "NovaMind"] if kw.lower() in content.lower())
    add_check(
        "config_keywords_used",
        config_keywords_found >= 2,
        f"Found {config_keywords_found}/3 config keywords in briefing content"
    )
    
    # ─── Check 9: Route B media sites attempted ────────────────
    # Agent should have attempted to fetch from 36kr, huxiu, sspai, ifanr
    # Since those sites may fail, the agent should at least mention them or
    # show evidence of attempting. Check for media source references.
    media_sites = ["36kr", "huxiu", "虎嗅", "sspai", "少数派", "ifanr", "爱范儿"]
    media_hits = [site for site in media_sites if site.lower() in content.lower()]
    route_b_passed = len(media_hits) >= 2
    add_check(
        "route_b_media_attempted",
        route_b_passed,
        f"Found references to media sites: {media_hits} ({len(media_hits)}/7 sites). "
        f"{'Route B attempted correctly.' if route_b_passed else 'Agent likely skipped Route B media fetching.'}"
    )
    
    # ─── Check 10: NovaMind appears in section titles (not just header) ──
    # Section 一 should say "直接提到 NovaMind 的新闻" or similar
    novamind_in_section = bool(re.search(r'###.*一.*NovaMind|NovaMind.*###.*一', content))
    # Also accept if it appears anywhere in section 1 heading
    section1_with_target = bool(re.search(r'###\s*一[、.．:：]?\s*直接提到\s*NovaMind', content))
    add_check(
        "target_name_in_section_headers",
        section1_with_target,
        "Section 一 heading correctly includes 'NovaMind'" if section1_with_target
        else "Section 一 heading does not reference 'NovaMind' — should be '直接提到 NovaMind 的新闻'"
    )
    
    # ─── Scoring ───────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    
    return checks, score


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks, score = evaluate(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_script_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    
    passed_count = sum(1 for c in checks if c["passed"])
    overall_passed = passed_count >= int(len(checks) * 0.75)
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))