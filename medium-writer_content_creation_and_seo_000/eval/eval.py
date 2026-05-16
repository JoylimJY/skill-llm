import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # --- Find the output article file ---
    # Agent is told to create: final_article.md
    article_files = list(workspace.rglob("final_article.md"))
    
    if not article_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "final_article.md not found anywhere in workspace."}]
        }
    
    article_path = article_files[0]
    try:
        content = article_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read final_article.md: {e}"}]
        }

    # ---- CHECK 1: File exists ----
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {article_path}"})

    # ---- CHECK 2: Headline uses Number + Benefit formula ----
    # Must have a number (digit) in the title AND a benefit/outcome word
    # The 📌 emoji marker must precede the title
    title_line = None
    for line in content.splitlines():
        if "📌" in line:
            title_line = line
            break
    
    has_pinpoint_emoji_title = title_line is not None
    checks.append({
        "name": "title_has_pinpoint_emoji",
        "passed": has_pinpoint_emoji_title,
        "detail": f"Title line with 📌 found: '{title_line}'" if has_pinpoint_emoji_title else "No line with 📌 emoji found. Required for title per SKILL.md article structure."
    })

    has_number_in_title = False
    if title_line:
        has_number_in_title = bool(re.search(r'\b\d+\b', title_line))
    checks.append({
        "name": "headline_number_benefit_formula",
        "passed": has_number_in_title,
        "detail": f"Numeric digit found in 📌 title line: '{title_line}'" if has_number_in_title else "No digit found in 📌 title — violates Number+Benefit headline formula."
    })

    # ---- CHECK 3: Subtitle (📝) exists and expresses a benefit ----
    subtitle_line = None
    for line in content.splitlines():
        if "📝" in line:
            subtitle_line = line
            break
    
    has_subtitle_emoji = subtitle_line is not None
    checks.append({
        "name": "subtitle_has_notepad_emoji",
        "passed": has_subtitle_emoji,
        "detail": f"Subtitle line with 📝 found: '{subtitle_line}'" if has_subtitle_emoji else "No 📝 subtitle marker found. Required by SKILL.md article format."
    })

    # ---- CHECK 4: Hero image placeholder (🖼️) marker present ----
    has_image_marker = "🖼️" in content or "🖼" in content
    checks.append({
        "name": "hero_image_marker_present",
        "passed": has_image_marker,
        "detail": "🖼️ hero image placeholder found." if has_image_marker else "No 🖼️ image marker found. Required by SKILL.md article structure."
    })

    # ---- CHECK 5: Horizontal rule separators (---) used ----
    # Must have at least 2 occurrences of --- as a separator line
    separator_lines = [line.strip() for line in content.splitlines() if line.strip() == "---"]
    has_separators = len(separator_lines) >= 2
    checks.append({
        "name": "horizontal_rule_separators",
        "passed": has_separators,
        "detail": f"Found {len(separator_lines)} '---' separator line(s). Need at least 2." 
    })

    # ---- CHECK 6: Introduction section contains primary keyword in first 100 words ----
    # Primary keyword from brief: "machine learning for developers"
    keyword = "machine learning for developers"
    
    # Find the introduction section (after 🖼️ and first ---, before next H2)
    # Simpler: check the first 100 words of the body (after intro markers)
    lines = content.splitlines()
    body_start = 0
    for i, line in enumerate(lines):
        if "🖼" in line or ("---" in line and i > 3):
            body_start = i + 1
            break
    
    body_text = " ".join(lines[body_start:])
    first_100_words = " ".join(body_text.split()[:100]).lower()
    keyword_in_first_100 = keyword.lower() in first_100_words
    
    # Also check broader: maybe just in early content
    early_content = " ".join(content.split()[:150]).lower()
    keyword_in_early = keyword.lower() in early_content
    
    checks.append({
        "name": "primary_keyword_in_first_100_words",
        "passed": keyword_in_first_100 or keyword_in_early,
        "detail": f"Keyword '{keyword}' found in first 100-150 words: {keyword_in_first_100 or keyword_in_early}. (SEO rule: keyword must appear in first 100 words)"
    })

    # ---- CHECK 7: Primary keyword in title ----
    title_has_keyword = keyword.lower() in (title_line or "").lower()
    # Also accept partial match (e.g., "machine learning" + "developer")
    title_has_ml = "machine learning" in (title_line or "").lower()
    title_has_dev = "developer" in (title_line or "").lower() or "developers" in (title_line or "").lower()
    title_keyword_ok = title_has_keyword or (title_has_ml and title_has_dev)
    checks.append({
        "name": "primary_keyword_in_title",
        "passed": title_keyword_ok,
        "detail": f"Title keyword check — '{title_line}'. ML present: {title_has_ml}, Dev present: {title_has_dev}."
    })

    # ---- CHECK 8: At least one H2 heading contains keyword-related term ----
    h2_lines = [line for line in content.splitlines() if line.strip().startswith("## ")]
    h2_with_keyword = any(
        "machine learning" in h.lower() or "developer" in h.lower() or "ml" in h.lower()
        for h in h2_lines
    )
    checks.append({
        "name": "keyword_in_h2_heading",
        "passed": h2_with_keyword,
        "detail": f"H2 headings found: {h2_lines}. At least one must contain ML/developer keyword per SEO rules."
    })

    # ---- CHECK 9: CTA in conclusion (clap/follow request) ----
    conclusion_area = content.lower()[-1500:]  # last 1500 chars
    has_cta_clap = "clap" in conclusion_area
    has_cta_follow = "follow" in conclusion_area
    has_cta = has_cta_clap or has_cta_follow
    checks.append({
        "name": "cta_in_conclusion",
        "passed": has_cta,
        "detail": f"CTA check — 'clap' found: {has_cta_clap}, 'follow' found: {has_cta_follow}. SKILL.md mandates CTA (clap/follow request) in conclusion."
    })

    # ---- CHECK 10: Related articles footer with 📚 emoji ----
    has_related_footer = "📚" in content
    checks.append({
        "name": "related_articles_footer_emoji",
        "passed": has_related_footer,
        "detail": "📚 related articles footer marker found." if has_related_footer else "No 📚 footer marker. SKILL.md requires '📚 関連記事リンク' section at end."
    })

    # ---- CHECK 11: Article has meaningful length (min 600 words = ~4 min read) ----
    word_count = len(content.split())
    is_long_enough = word_count >= 600
    checks.append({
        "name": "minimum_word_count",
        "passed": is_long_enough,
        "detail": f"Word count: {word_count}. Minimum 600 words required for a 5-minute read as per brief."
    })

    # ---- CHECK 12: Has multiple H2 sections (at least 3 body sections) ----
    has_enough_h2 = len(h2_lines) >= 3
    checks.append({
        "name": "minimum_h2_sections",
        "passed": has_enough_h2,
        "detail": f"Found {len(h2_lines)} H2 sections. Need at least 3 for a properly structured article per SKILL.md format."
    })

    # ---- CHECK 13: Towards Data Science publication mentioned/targeted ----
    tds_mentioned = "towards data science" in content.lower() or "TDS" in content
    checks.append({
        "name": "publication_targeting",
        "passed": tds_mentioned,
        "detail": "Towards Data Science publication targeting found in article." if tds_mentioned else "No reference to Towards Data Science publication. Brief specifies TDS as target publication."
    })

    # ---- CHECK 14: Does NOT preserve the broken draft's bad headline (regression check) ----
    bad_headline_preserved = "How Developers Can Get Into Machine Learning" in content and "📌" not in content
    checks.append({
        "name": "broken_draft_not_reused_verbatim",
        "passed": not bad_headline_preserved,
        "detail": "Agent did not blindly reuse the broken draft's unformatted headline without proper 📌 marker."
    })

    # --- Compute score ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    # Determine overall pass: must pass critical checks
    critical_checks = [
        "file_exists",
        "title_has_pinpoint_emoji",
        "headline_number_benefit_formula",
        "subtitle_has_notepad_emoji",
        "cta_in_conclusion",
        "related_articles_footer_emoji",
        "primary_keyword_in_first_100_words",
        "minimum_word_count",
        "minimum_h2_sections",
    ]
    critical_results = {c["name"]: c["passed"] for c in checks}
    all_critical_pass = all(critical_results.get(name, False) for name in critical_checks)

    overall_passed = all_critical_pass and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))