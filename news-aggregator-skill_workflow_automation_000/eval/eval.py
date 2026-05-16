#!/usr/bin/env python3
"""
Evaluation script for the news aggregator multi-source briefing task.

Checks:
1. A report file exists in reports/ with a timestamped .md filename
2. Report is in Simplified Chinese (contains CJK characters substantially)
3. GitHub section exists with per-item deep analysis (核心价值, 启发思考, 场景标签)
4. Finance section exists covering Finance/Economy/Crypto/Stock/Gold/Market topics
5. Title items are formatted as Markdown links [text](url) — not plain text
6. fetch_news.py was called with --deep flag (evidence via content depth OR command log)
7. Keywords were expanded: finance-related queries used multi-term keywords
8. Report has required structural sections (Global Headlines / Tech & AI / Finance)
"""

import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    total_score = 0.0
    weights = {}

    # ── Check 1: Report file exists in reports/ with timestamped .md name ──
    try:
        report_files = list((workspace / "reports").glob("*.md"))
        # Must have at least one .md file with timestamp-like name
        timestamp_pattern = re.compile(r'\d{8}[_\-]\d{4}|\d{8}[_\-]\d{6}|\d{4}[_\-]\d{2}[_\-]\d{2}')
        valid_reports = [f for f in report_files if timestamp_pattern.search(f.name)]
        if not valid_reports:
            # Relax: any .md report file is acceptable (agent might use slightly diff naming)
            valid_reports = report_files
        passed_1 = len(valid_reports) > 0
        report_path = valid_reports[0] if valid_reports else None
        detail_1 = f"Found {len(valid_reports)} report(s): {[f.name for f in valid_reports]}" if valid_reports else "No .md report found in reports/"
    except Exception as e:
        passed_1 = False
        report_path = None
        detail_1 = f"Exception: {e}"
    checks.append(check("report_file_exists_in_reports_dir", passed_1, detail_1))
    weights["report_file_exists_in_reports_dir"] = 0.10

    # ── Load report content ──
    report_content = ""
    if report_path:
        try:
            report_content = report_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            report_content = ""
            checks.append(check("report_readable", False, f"Cannot read report: {e}"))

    # ── Check 2: Report contains substantial Simplified Chinese ──
    try:
        cjk_chars = len(re.findall(r'[\u4e00-\u9fff]', report_content))
        passed_2 = cjk_chars >= 50
        detail_2 = f"Found {cjk_chars} CJK characters (need ≥50)"
    except Exception as e:
        passed_2 = False
        detail_2 = f"Exception: {e}"
    checks.append(check("report_in_simplified_chinese", passed_2, detail_2))
    weights["report_in_simplified_chinese"] = 0.10

    # ── Check 3: GitHub Trending section with deep per-item analysis ──
    try:
        content_lower = report_content.lower()
        has_github_section = (
            'github' in content_lower or
            'trending' in content_lower or
            '趋势' in report_content or
            'github trending' in content_lower
        )
        # Must contain core value / inspiration / scenario tags markers
        has_core_value = (
            '核心价值' in report_content or
            'core value' in content_lower or
            '核心' in report_content
        )
        has_inspiration = (
            '启发' in report_content or
            '启发思考' in report_content or
            'inspiration' in content_lower or
            '洞察' in report_content
        )
        has_scenario_tags = (
            '场景' in report_content or
            '#' in report_content or  # hashtag scenario labels
            'scenario' in content_lower
        )
        passed_3 = has_github_section and has_core_value and has_inspiration and has_scenario_tags
        detail_3 = (
            f"github_section={has_github_section}, core_value={has_core_value}, "
            f"inspiration={has_inspiration}, scenario_tags={has_scenario_tags}"
        )
    except Exception as e:
        passed_3 = False
        detail_3 = f"Exception: {e}"
    checks.append(check("github_trending_deep_analysis_present", passed_3, detail_3))
    weights["github_trending_deep_analysis_present"] = 0.20

    # ── Check 4: Finance section covering expanded keyword topics ──
    try:
        finance_keywords_cn = ['金融', '股市', '市场', '经济', '加密', '黄金', '比特币', '美元', '降息', '融资', '财经']
        finance_keywords_en = ['finance', 'stock', 'market', 'economy', 'crypto', 'gold', 'bitcoin', 'rate']
        hits_cn = [kw for kw in finance_keywords_cn if kw in report_content]
        hits_en = [kw for kw in finance_keywords_en if kw in content_lower]
        passed_4 = len(hits_cn) >= 2 or len(hits_en) >= 2 or (len(hits_cn) + len(hits_en) >= 3)
        detail_4 = f"CN finance keywords found: {hits_cn}, EN: {hits_en}"
    except Exception as e:
        passed_4 = False
        detail_4 = f"Exception: {e}"
    checks.append(check("finance_section_with_expanded_topics", passed_4, detail_4))
    weights["finance_section_with_expanded_topics"] = 0.15

    # ── Check 5: Titles formatted as Markdown links [text](url) ──
    try:
        # Find markdown links: [...](...) pattern
        md_links = re.findall(r'\[.+?\]\(https?://[^\)]+\)', report_content)
        # Must have at least 3 markdown links (for multiple items)
        passed_5 = len(md_links) >= 3
        detail_5 = f"Found {len(md_links)} Markdown link(s): {md_links[:3]}..."
    except Exception as e:
        passed_5 = False
        detail_5 = f"Exception: {e}"
    checks.append(check("titles_are_markdown_links", passed_5, detail_5))
    weights["titles_are_markdown_links"] = 0.15

    # ── Check 6: --deep flag used (report contains content-derived insights) ──
    # Evidence: items should show detailed content summaries beyond just title+score
    try:
        # Look for bullet points (indicating deep interpretation)
        bullet_points = re.findall(r'^[\s]*[-*•]\s+.{20,}', report_content, re.MULTILINE)
        # Or numbered deep interpretation sections
        has_deep_bullets = len(bullet_points) >= 5
        # Also check for content-rich descriptions (long paragraphs per item)
        long_paragraphs = [p for p in report_content.split('\n') if len(p.strip()) > 80]
        has_content_depth = len(long_paragraphs) >= 5
        passed_6 = has_deep_bullets or has_content_depth
        detail_6 = f"Bullet points (≥20 chars): {len(bullet_points)}, Long paragraphs: {len(long_paragraphs)}"
    except Exception as e:
        passed_6 = False
        detail_6 = f"Exception: {e}"
    checks.append(check("deep_flag_evidence_content_richness", passed_6, detail_6))
    weights["deep_flag_evidence_content_richness"] = 0.10

    # ── Check 7: Keyword expansion evidence ──
    # The agent should have used expanded keywords for Finance queries.
    # We detect this by checking if the report covers MULTIPLE finance sub-topics
    # (crypto/gold/stock/economy) — only possible if expanded keywords were used.
    try:
        sub_topics_cn = {
            'crypto_or_bitcoin': any(t in report_content for t in ['加密', '比特币', 'Crypto', 'crypto', 'Bitcoin']),
            'gold_or_commodity': any(t in report_content for t in ['黄金', 'Gold', 'gold', '大宗商品']),
            'stock_market': any(t in report_content for t in ['股市', '股票', 'Stock', 'stock', 'A股', '市场']),
            'economy_macro': any(t in report_content for t in ['经济', '宏观', '降息', 'Economy', 'economy', 'GDP']),
        }
        covered = sum(1 for v in sub_topics_cn.values() if v)
        passed_7 = covered >= 2
        detail_7 = f"Finance sub-topics covered: {sub_topics_cn} ({covered}/4 required ≥2)"
    except Exception as e:
        passed_7 = False
        detail_7 = f"Exception: {e}"
    checks.append(check("keyword_expansion_multi_finance_subtopics", passed_7, detail_7))
    weights["keyword_expansion_multi_finance_subtopics"] = 0.10

    # ── Check 8: Report has required structural sections ──
    try:
        has_headline_section = bool(re.search(
            r'(全球头条|全球要闻|头条|Global Headlines|Headlines|重要新闻|今日要闻)',
            report_content
        ))
        has_tech_section = bool(re.search(
            r'(科技|Tech|AI|人工智能|Technology|技术)',
            report_content
        ))
        has_finance_section = bool(re.search(
            r'(财经|Finance|金融|市场|Market|Social)',
            report_content
        ))
        passed_8 = has_headline_section and has_tech_section and has_finance_section
        detail_8 = (
            f"headline={has_headline_section}, tech={has_tech_section}, finance={has_finance_section}"
        )
    except Exception as e:
        passed_8 = False
        detail_8 = f"Exception: {e}"
    checks.append(check("report_structure_three_sections", passed_8, detail_8))
    weights["report_structure_three_sections"] = 0.10

    # ── Compute Score ──
    total_weight = sum(weights.values())
    score = 0.0
    for c in checks:
        w = weights.get(c["name"], 0.0)
        if c["passed"]:
            score += w

    # Normalize
    score = round(score / total_weight, 4)
    all_passed = all(c["passed"] for c in checks)

    output = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()