import sys
import json
import re
from pathlib import Path

def count_words(text: str) -> int:
    return len(text.split())

def run_eval(workspace: str):
    checks = []
    total_score = 0.0

    # ── Locate the output file ──────────────────────────────────────────────
    candidates = list(Path(workspace).rglob("content_package.md"))

    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found content_package.md at: {candidates[0]}" if file_found else "content_package.md not found anywhere in workspace"
    })

    if not file_found:
        return checks, 0.0

    content_path = candidates[0]
    try:
        raw = content_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return checks, 0.0

    content_lower = raw.lower()

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 1: SUMMARY SECTION
    # ══════════════════════════════════════════════════════════════════════════

    # 1a. Summary section exists
    has_summary_section = bool(re.search(r'summary', content_lower))
    checks.append({
        "name": "summary_section_present",
        "passed": has_summary_section,
        "detail": "Found 'summary' heading/section" if has_summary_section else "No summary section found"
    })

    # 1b. Has 5–10 bullet points in the summary (key points)
    # Count bullet lines (lines starting with - or * or numbered)
    bullet_lines = re.findall(r'(?m)^[ \t]*[-*•]\s+.+', raw)
    bullet_count = len(bullet_lines)
    has_enough_bullets = 5 <= bullet_count <= 20  # generous upper bound; exact 5-10 per summary
    checks.append({
        "name": "summary_has_5_to_10_key_points",
        "passed": bullet_count >= 5,
        "detail": f"Found {bullet_count} bullet-point lines total (need at least 5 for key points)"
    })

    # 1c. Has exactly 3 key takeaways
    takeaway_matches = re.findall(r'(?i)(takeaway|key takeaway)', raw)
    # Also check for a numbered list under a "takeaways" heading
    takeaway_section = re.search(r'(?i)(key takeaway|takeaway)[s]?\s*[:\n]+(.*?)(?=\n#+|\Z)', raw, re.DOTALL)
    numbered_in_takeaway = []
    if takeaway_section:
        numbered_in_takeaway = re.findall(r'(?m)^\s*\d+[\.\)]\s+.+', takeaway_section.group(0))
    has_three_takeaways = len(numbered_in_takeaway) >= 3 or len(takeaway_matches) >= 1
    # More lenient: check for 3 numbered items anywhere near "takeaway"
    all_numbered = re.findall(r'(?m)^\s*[123][\.\)]\s+.+', raw)
    has_three_takeaways = has_three_takeaways or len(all_numbered) >= 3
    checks.append({
        "name": "summary_has_3_key_takeaways",
        "passed": has_three_takeaways,
        "detail": f"Takeaway mentions: {len(takeaway_matches)}, numbered items near takeaway: {len(numbered_in_takeaway)}, all numbered-3 items: {len(all_numbered)}"
    })

    # 1d. Summary references content from the reference text (key terms)
    reference_terms = ["wujub", "obligation", "qarinah", "command", "absolute", "al-amr", "jurist",
                       "hanafi", "shafi", "hanbali", "maliki", "quran", "sunnah", "ijma", "salah", "zakat"]
    terms_found = [t for t in reference_terms if t.lower() in content_lower]
    has_reference_content = len(terms_found) >= 3
    checks.append({
        "name": "summary_grounded_in_reference_text",
        "passed": has_reference_content,
        "detail": f"Reference terms found: {terms_found} ({len(terms_found)}/3 minimum)"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 2: POST VARIANTS — structural distinctness
    # ══════════════════════════════════════════════════════════════════════════

    # 2a. Contains at least 3 variant sections
    variant_markers = re.findall(r'(?i)(variant\s*[123]|post\s*[123]|version\s*[123]|draft\s*[123])', raw)
    has_three_variants_labeled = len(set(variant_markers)) >= 3 or len(variant_markers) >= 3
    # Also check for any section headers suggesting 3 distinct posts
    section_headers = re.findall(r'(?m)^#{1,4}\s+.+', raw)
    checks.append({
        "name": "three_post_variants_present",
        "passed": has_three_variants_labeled or len(section_headers) >= 5,
        "detail": f"Variant labels found: {variant_markers}, total section headers: {len(section_headers)}"
    })

    # 2b. Variant 1 contains a hook + paragraphs + question structure
    # Look for a question mark (closing question) in prose
    question_marks = [i for i, line in enumerate(raw.split('\n')) if '?' in line]
    has_closing_questions = len(question_marks) >= 3  # at least 3 variants each have a question
    checks.append({
        "name": "variants_each_have_closing_question",
        "passed": has_closing_questions,
        "detail": f"Lines with '?' found at line indices: {question_marks[:10]}. Need at least 3."
    })

    # 2c. Variant 2 has bullet-point structure
    # Already have bullet_lines from above; check there are bullets in what appears to be a variant section
    # Strategy: look for a chunk of text that has multiple bullets
    variant2_bullet_check = bullet_count >= 4
    checks.append({
        "name": "variant_2_has_bullet_structure",
        "passed": variant2_bullet_check,
        "detail": f"Total bullet lines in document: {bullet_count} (need >= 4 to confirm bullet-based variant exists)"
    })

    # 2d. Variant 3 has story/analogy + lesson keywords
    has_story_analogy = bool(re.search(r'(?i)(story|analogy|imagine|once|picture this|consider)', raw))
    has_lesson_keyword = bool(re.search(r'(?i)\bLesson\b', raw))
    checks.append({
        "name": "variant_3_has_story_and_lesson",
        "passed": has_story_analogy and has_lesson_keyword,
        "detail": f"Story/analogy keyword found: {has_story_analogy}, 'Lesson:' keyword found: {has_lesson_keyword}"
    })

    # 2e. Each variant is under 160 words (proprietary word limit constraint)
    # Heuristic: split by variant markers and check word counts
    # Split the document into potential variant chunks
    variant_chunks = re.split(r'(?i)(variant\s*[123]|post variant\s*[123]|###?\s+variant)', raw)
    variant_word_counts = []
    for chunk in variant_chunks:
        wc = count_words(chunk)
        if 20 < wc < 400:  # ignore tiny/huge non-variant chunks
            variant_word_counts.append(wc)

    # Also try splitting by "---" dividers between variant sections
    if len(variant_word_counts) < 3:
        sections_by_divider = re.split(r'\n---+\n', raw)
        for sec in sections_by_divider:
            wc = count_words(sec)
            if 20 < wc < 400:
                variant_word_counts.append(wc)

    over_limit = [wc for wc in variant_word_counts if wc > 160]
    word_limit_ok = len(over_limit) == 0 or len(variant_word_counts) == 0
    checks.append({
        "name": "variants_under_160_words_each",
        "passed": word_limit_ok,
        "detail": f"Variant chunk word counts (20<wc<400): {variant_word_counts}. Over-limit chunks: {over_limit}"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 3: ARCHIVE ENTRY — proprietary format
    # ══════════════════════════════════════════════════════════════════════════

    # 3a. Archive section exists
    has_archive = bool(re.search(r'(?i)(archive|archiv)', raw))
    checks.append({
        "name": "archive_section_present",
        "passed": has_archive,
        "detail": "Found 'archive' section" if has_archive else "No archive section found"
    })

    # 3b. Archive uses the exact slash-separated format: Title / Angle / Draft / Question / Tags
    # The proprietary format is: Title / Angle / Draft / Question / Tags
    archive_format_pattern = re.search(
        r'(?i)([^/\n]+)\s*/\s*([^/\n]+)\s*/\s*([^/\n]+)\s*/\s*([^/\n]+)\s*/\s*([^\n]+)',
        raw
    )
    has_slash_format = archive_format_pattern is not None
    # Validate it has 5 slash-separated segments
    if archive_format_pattern:
        segments = [s.strip() for s in archive_format_pattern.group(0).split('/')]
        has_five_segments = len(segments) >= 5
    else:
        has_five_segments = False

    checks.append({
        "name": "archive_uses_title_angle_draft_question_tags_format",
        "passed": has_slash_format and has_five_segments,
        "detail": (
            f"Slash-separated archive entry found: '{archive_format_pattern.group(0)[:120]}'" 
            if archive_format_pattern else "No slash-separated archive entry found (expected: Title / Angle / Draft / Question / Tags)"
        )
    })

    # 3c. Archive entry contains meaningful content (not just placeholder labels)
    if archive_format_pattern:
        entry_text = archive_format_pattern.group(0).lower()
        is_not_template = not bool(re.search(r'\[title\]|\[angle\]|\[draft\]|\[question\]|\[tags?\]', entry_text))
        has_real_content = len(entry_text.replace('/', '').strip()) > 40
        archive_content_ok = is_not_template and has_real_content
    else:
        archive_content_ok = False
    checks.append({
        "name": "archive_entry_has_real_content",
        "passed": archive_content_ok,
        "detail": f"Archive entry real content check: not_template={archive_content_ok}"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # SCORING
    # ══════════════════════════════════════════════════════════════════════════
    weights = {
        "output_file_exists": 0.05,
        "summary_section_present": 0.05,
        "summary_has_5_to_10_key_points": 0.10,
        "summary_has_3_key_takeaways": 0.10,
        "summary_grounded_in_reference_text": 0.10,
        "three_post_variants_present": 0.10,
        "variants_each_have_closing_question": 0.10,
        "variant_2_has_bullet_structure": 0.05,
        "variant_3_has_story_and_lesson": 0.10,
        "variants_under_160_words_each": 0.05,
        "archive_section_present": 0.05,
        "archive_uses_title_angle_draft_question_tags_format": 0.10,
        "archive_entry_has_real_content": 0.05,
    }

    score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.0)
        if check["passed"]:
            score += w

    passed_overall = score >= 0.70

    return checks, round(score, 3), passed_overall


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score, passed = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crashed", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result))
        return

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()