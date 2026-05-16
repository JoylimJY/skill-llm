import sys
import re
import json
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── Helper ──────────────────────────────────────────────────────────────
    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── 1. Find the output file ──────────────────────────────────────────────
    candidates = list(workspace.rglob("python_concurrency_cards.md"))
    if not candidates:
        # broaden search for any .md file that looks like anki output
        candidates = [
            f for f in workspace.rglob("*.md")
            if "anki" in f.read_text(errors="ignore").lower()
            and "#anki/" in f.read_text(errors="ignore")
        ]

    if not candidates:
        check("file_found", False, "No output .md file with #anki/ tag found anywhere in workspace")
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    # Use the first (or most plausible) candidate
    out_file = candidates[0]
    try:
        content = out_file.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        check("file_readable", False, f"Could not read file: {e}")
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    check("file_found", True, f"Found output file: {out_file.relative_to(workspace)}")

    # ── 2. Tag format: #anki/[domain]/[topic] with English-only tags ─────────
    tag_pattern = re.compile(r"#anki/([a-zA-Z_]+)/([a-zA-Z_]+)")
    tags_found = tag_pattern.findall(content)
    has_valid_tag = len(tags_found) > 0

    # Check no Chinese characters in tags
    tag_lines = [line for line in content.splitlines() if line.strip().startswith("#anki/")]
    chinese_in_tags = any(re.search(r'[\u4e00-\u9fff]', line) for line in tag_lines)

    tag_ok = has_valid_tag and not chinese_in_tags
    check(
        "tag_format_correct",
        tag_ok,
        f"Tags found: {tags_found[:3]}. Chinese in tags: {chinese_in_tags}. "
        f"Expected #anki/[english_domain]/[english_topic]"
    )

    # ── 3. Table row structure: | Question | / | Answer | ───────────────────
    # simple-anki-sync format: two-row markdown table per card
    table_block_pattern = re.compile(
        r"\|\s*(.+?)\s*\|\s*\n\|\s*-+\s*\|\s*\n\|\s*(.+?)\s*\|",
        re.MULTILINE
    )
    cards = table_block_pattern.findall(content)
    num_cards = len(cards)

    has_enough_cards = num_cards >= 5
    check(
        "minimum_cards",
        has_enough_cards,
        f"Found {num_cards} cards in proper simple-anki-sync table format (need ≥5)"
    )

    # ── 4. Question design: standardized templates (no "What is X?" patterns) ─
    bad_question_patterns = [
        re.compile(r"What is\s+\w", re.IGNORECASE),
        re.compile(r"What are\s+\w", re.IGNORECASE),
        re.compile(r"How does\s+\w", re.IGNORECASE),
        re.compile(r"Why does\s+\w", re.IGNORECASE),
        re.compile(r"Explain\s+\w", re.IGNORECASE),
        re.compile(r"Describe\s+\w", re.IGNORECASE),
    ]
    questions = [c[0] for c in cards]
    bad_questions = []
    for q in questions:
        for pat in bad_question_patterns:
            if pat.search(q):
                bad_questions.append(q)
                break

    no_bad_questions = len(bad_questions) == 0
    check(
        "standardized_question_format",
        no_bad_questions,
        f"Bad question forms found: {bad_questions[:3]}. "
        "Expected templates like 'X definition', 'GIL pros/cons', 'who X'"
    )

    # ── 5. Word limits in English answers (max 18 absolute) ──────────────────
    answers = [c[1] for c in cards]
    word_limit_violations = []
    for i, ans in enumerate(answers):
        # Strip HTML tags for word counting
        clean = re.sub(r"<[^>]+>", " ", ans)
        # Remove supplementary section (after <br><br><small>)
        core = re.split(r"<br>", clean)[0].strip()
        # Remove handle references
        core_no_handles = re.sub(r">[\w\s]+", "", core).strip()
        word_count = len(core_no_handles.split())
        if word_count > 18:
            word_limit_violations.append(
                f"Card {i+1}: '{core_no_handles[:60]}' = {word_count} words"
            )

    word_limits_ok = len(word_limit_violations) == 0
    check(
        "english_word_limit_18_max",
        word_limits_ok,
        f"Violations: {word_limit_violations[:3]}"
        if not word_limits_ok
        else "All answers within 18-word absolute limit"
    )

    # ── 6. Supplementary info format: <br><br><small>emoji content</small> ───
    supp_pattern = re.compile(r"<br><br><small>(.*?)</small>", re.IGNORECASE)
    all_supps = supp_pattern.findall(content)

    valid_emojis = {"💡", "📝", "🔗", "⚡", "📊", "📅"}
    supp_format_errors = []
    supp_length_errors = []

    for s in all_supps:
        # Check starts with valid emoji
        first_char = s.strip()
        has_valid_emoji = any(first_char.startswith(e) for e in valid_emojis)
        if not has_valid_emoji:
            supp_format_errors.append(f"Missing/invalid emoji: '{s[:30]}'")

        # Check 10-20 character limit (excluding emoji itself)
        # emoji is typically 1-2 chars; strip it and surrounding space
        stripped = re.sub(r"^[^\w\u4e00-\u9fff]*", "", s).strip()
        # rough: remove leading emoji chars
        text_only = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27BF]\s*", "", s).strip()
        if len(text_only) > 20:
            supp_length_errors.append(f"Supplementary too long ({len(text_only)} chars): '{text_only[:30]}'")

    has_supplementary = len(all_supps) > 0
    supp_format_ok = has_supplementary and len(supp_format_errors) == 0

    check(
        "supplementary_info_present",
        has_supplementary,
        f"Found {len(all_supps)} supplementary info blocks"
    )
    check(
        "supplementary_emoji_valid",
        supp_format_ok,
        f"Emoji errors: {supp_format_errors[:3]}"
        if supp_format_errors
        else "All supplementary blocks use valid skill-defined emojis"
    )
    check(
        "supplementary_length_limit",
        len(supp_length_errors) == 0,
        f"Length errors: {supp_length_errors[:3]}"
        if supp_length_errors
        else f"All {len(all_supps)} supplementary blocks within 20-char limit"
    )

    # ── 7. Handle system (>) used for at least one cross-reference ──────────
    handle_pattern = re.compile(r">\s*\w+")
    handles_in_answers = [a for a in answers if handle_pattern.search(a)]
    has_handles = len(handles_in_answers) >= 1
    check(
        "handle_cross_references_used",
        has_handles,
        f"Found {len(handles_in_answers)} answer(s) using >handle cross-references"
    )

    # ── 8. Atomization: no more than 3 bullet points per answer ─────────────
    bullet_violations = []
    for i, ans in enumerate(answers):
        bullets = re.findall(r"(?:^|\n)\s*[-•]\s+", ans)
        if len(bullets) > 3:
            bullet_violations.append(f"Card {i+1}: {len(bullets)} bullet points")

    atomization_ok = len(bullet_violations) == 0
    check(
        "max_3_bullets_per_card",
        atomization_ok,
        f"Violations: {bullet_violations[:3]}"
        if not atomization_ok
        else "All cards have ≤3 bullet points"
    )

    # ── 9. Content coverage: key concurrency concepts present ────────────────
    required_concepts = ["GIL", "asyncio", "threading", "concurrent", "deadlock"]
    content_lower = content.lower()
    missing = [c for c in required_concepts if c.lower() not in content_lower]
    coverage_ok = len(missing) == 0
    check(
        "content_covers_concurrency_topics",
        coverage_ok,
        f"Missing topics: {missing}" if not coverage_ok else "All required concurrency topics covered"
    )

    # ── Scoring ─────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = round(len(passed_checks) / total, 3)

    # Must-pass gates: file found, cards exist, tag format, word limits
    gates = [
        "file_found",
        "minimum_cards",
        "tag_format_correct",
        "english_word_limit_18_max",
    ]
    gate_results = {c["name"]: c["passed"] for c in checks}
    all_gates_passed = all(gate_results.get(g, False) for g in gates)

    overall = all_gates_passed and score >= 0.70

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    evaluate(sys.argv[1] if len(sys.argv) > 1 else "/workspace")