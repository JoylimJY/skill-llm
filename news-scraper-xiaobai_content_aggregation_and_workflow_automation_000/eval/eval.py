#!/usr/bin/env python3
"""
Evaluation script for the AI news digest task.
Checks that ai_news_digest.md was created with correct format and content.
"""
import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    # ── Locate the output file ────────────────────────────────────────────────
    candidates = list(Path(workspace).rglob("ai_news_digest.md"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named ai_news_digest.md" if file_found
                  else "No file named ai_news_digest.md found anywhere in workspace"
    })
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    digest_path = candidates[0]
    try:
        content = digest_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check 1: Date header with emoji ──────────────────────────────────────
    date_header = bool(re.search(r'📅\s+\d{4}-\d{2}-\d{2}\s+AI资讯', content))
    checks.append({
        "name": "date_header_format",
        "passed": date_header,
        "detail": "Found '📅 YYYY-MM-DD AI资讯' header" if date_header
                  else "Missing '📅 YYYY-MM-DD AI资讯' header line"
    })

    # ── Check 2: Has category section headers (bold, with emoji + Chinese) ───
    # Categories from SKILL.md: 大模型, AI应用, 企业商业, 安全合规, 开源社区, 硬件芯片, 学术研究, 智能体
    valid_categories = {"大模型", "AI应用", "企业商业", "安全合规", "开源社区", "硬件芯片", "学术研究", "智能体"}
    # Match lines like: 🧠 **智能体** or 🔒 **安全合规** (any leading emoji + bold category)
    section_header_pattern = re.findall(r'\*\*(.+?)\*\*', content)
    found_categories = {h.strip() for h in section_header_pattern if h.strip() in valid_categories}
    has_categories = len(found_categories) >= 2
    checks.append({
        "name": "category_section_headers",
        "passed": has_categories,
        "detail": f"Found {len(found_categories)} valid category section headers: {found_categories}"
    })

    # ── Check 3: Articles use blockquote format with 📌 ─────────────────────
    title_lines = re.findall(r'^>\s*📌\s*标题[：:].+', content, re.MULTILINE)
    has_title_blocks = len(title_lines) >= 5
    checks.append({
        "name": "blockquote_title_format",
        "passed": has_title_blocks,
        "detail": f"Found {len(title_lines)} '> 📌 标题：...' lines (need ≥5)"
    })

    # ── Check 4: Classification lines use 🏷️ with valid category + valid tags ─
    tag_lines = re.findall(r'^>\s*🏷️\s*分类[：:].+标签[：:].+', content, re.MULTILINE)
    has_tag_lines = len(tag_lines) >= 5
    checks.append({
        "name": "classification_tag_format",
        "passed": has_tag_lines,
        "detail": f"Found {len(tag_lines)} '> 🏷️ 分类：... | 标签：...' lines (need ≥5)"
    })

    # ── Check 5: Tags come from allowed taxonomy ──────────────────────────────
    valid_tags = {"OpenAI", "Google", "NVIDIA", "Meta", "Microsoft",
                  "阿里巴巴", "中国", "国际", "Agent", "多模态", "安全"}
    # Extract all tags from tag lines
    tag_values_found = set()
    for line in tag_lines:
        m = re.search(r'标签[：:](.+)', line)
        if m:
            raw = m.group(1).strip()
            parts = re.split(r'[、，,\s]+', raw)
            for p in parts:
                p = p.strip().rstrip('*').strip()
                if p:
                    tag_values_found.add(p)

    illegal_tags = tag_values_found - valid_tags
    tags_valid = len(illegal_tags) == 0 and len(tag_values_found) > 0
    checks.append({
        "name": "tags_from_valid_taxonomy",
        "passed": tags_valid,
        "detail": f"Tags found: {tag_values_found}. Illegal tags: {illegal_tags}"
    })

    # ── Check 6: Categories in tag lines come from valid taxonomy ─────────────
    cat_values_found = set()
    for line in tag_lines:
        m = re.search(r'分类[：:](.+?)\s*\|', line)
        if m:
            cat = m.group(1).strip()
            cat_values_found.add(cat)
    illegal_cats = cat_values_found - valid_categories
    cats_valid = len(illegal_cats) == 0 and len(cat_values_found) > 0
    checks.append({
        "name": "categories_from_valid_taxonomy",
        "passed": cats_valid,
        "detail": f"Categories in tag lines: {cat_values_found}. Illegal: {illegal_cats}"
    })

    # ── Check 7: Summary lines use 📝 ────────────────────────────────────────
    summary_lines = re.findall(r'^>\s*📝\s*概要[：:].+', content, re.MULTILINE)
    has_summary = len(summary_lines) >= 5
    checks.append({
        "name": "summary_emoji_format",
        "passed": has_summary,
        "detail": f"Found {len(summary_lines)} '> 📝 概要：...' lines (need ≥5)"
    })

    # ── Check 8: Links use 🔗 and correct zh path ────────────────────────────
    link_lines = re.findall(r'^>\s*🔗\s*链接[：:]\s*(https?://\S+)', content, re.MULTILINE)
    has_links = len(link_lines) >= 5
    checks.append({
        "name": "link_emoji_format",
        "passed": has_links,
        "detail": f"Found {len(link_lines)} '> 🔗 链接：...' lines (need ≥5)"
    })

    # ── Check 9: Links use /zh/news/ path (not /en/ or bare /news/) ──────────
    zh_links = [u for u in link_lines if "/zh/news/" in u]
    non_zh_links = [u for u in link_lines if "/zh/news/" not in u]
    links_use_zh = len(zh_links) >= 5 and len(non_zh_links) == 0
    checks.append({
        "name": "links_use_zh_chinese_path",
        "passed": links_use_zh,
        "detail": f"{len(zh_links)} links use /zh/news/. Non-zh links: {non_zh_links}"
    })

    # ── Check 10: At least 2 distinct categories represented ─────────────────
    multi_category = len(found_categories) >= 2
    checks.append({
        "name": "multiple_categories_present",
        "passed": multi_category,
        "detail": f"Distinct categories in output: {found_categories}"
    })

    # ── Check 11: Horizontal rule separators between sections ────────────────
    hr_count = len(re.findall(r'^---\s*$', content, re.MULTILINE))
    has_separators = hr_count >= 2
    checks.append({
        "name": "section_separators_present",
        "passed": has_separators,
        "detail": f"Found {hr_count} '---' horizontal rule separators (need ≥2)"
    })

    # ── Check 12: Articles grouped under their category (ordering check) ──────
    # Each section header should be followed by blockquoted articles before next header
    # Simple heuristic: a 📌 line should appear after a category header before the next header
    sections = re.split(r'\*\*.+?\*\*', content)
    articles_inside_sections = False
    if len(sections) >= 2:
        for sec in sections[1:]:  # skip preamble
            if re.search(r'^>\s*📌', sec, re.MULTILINE):
                articles_inside_sections = True
                break
    checks.append({
        "name": "articles_grouped_under_categories",
        "passed": articles_inside_sections,
        "detail": "Articles appear under category section headers" if articles_inside_sections
                  else "Articles do not appear under bold category section headers"
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    weights = {
        "output_file_exists": 0.05,
        "date_header_format": 0.08,
        "category_section_headers": 0.08,
        "blockquote_title_format": 0.10,
        "classification_tag_format": 0.10,
        "tags_from_valid_taxonomy": 0.10,
        "categories_from_valid_taxonomy": 0.10,
        "summary_emoji_format": 0.08,
        "link_emoji_format": 0.08,
        "links_use_zh_chinese_path": 0.10,
        "multiple_categories_present": 0.05,
        "section_separators_present": 0.05,
        "articles_grouped_under_categories": 0.03,
    }
    score = sum(weights.get(c["name"], 0) for c in checks if c["passed"])
    passed = all(c["passed"] for c in checks)

    return {
        "passed": passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))