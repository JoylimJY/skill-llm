import sys
import os
import json
from pathlib import Path

def load_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return None

def check_bullet_lines(content, keywords):
    """Return True if at least one bullet line contains any of the keywords (case-insensitive)."""
    if not content:
        return False
    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("-"):
            lower = stripped.lower()
            if any(kw.lower() in lower for kw in keywords):
                return True
    return False

def count_bullet_lines(content):
    if not content:
        return 0
    return sum(1 for l in content.splitlines() if l.strip().startswith("-"))

def any_line_contains(content, keywords):
    if not content:
        return False
    lower_content = content.lower()
    return any(kw.lower() in lower_content for kw in keywords)

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── Locate the memory directory ──────────────────────────────────────────
    # Accept memory/ inside selective-memory/ or directly at workspace root
    candidate_paths = [
        Path(workspace) / "selective-memory" / "memory",
        Path(workspace) / "memory",
    ]
    memory_dir = None
    for p in candidate_paths:
        if p.is_dir():
            memory_dir = p
            break

    # Also search recursively for any directory named "memory" containing the four files
    if memory_dir is None:
        for d in Path(workspace).rglob("memory"):
            if d.is_dir():
                files_present = {f.name for f in d.iterdir() if f.is_file()}
                if {"wisdom.md", "goals.md", "mistakes.md", "preferences.md"} & files_present:
                    memory_dir = d
                    break

    # ── CHECK 1: Memory directory and all four files exist ───────────────────
    files_ok = False
    if memory_dir is not None:
        required = ["wisdom.md", "goals.md", "mistakes.md", "preferences.md"]
        missing = [f for f in required if not (memory_dir / f).exists()]
        files_ok = len(missing) == 0
        checks.append({
            "name": "memory_structure_exists",
            "passed": files_ok,
            "detail": f"memory_dir={memory_dir}, missing={missing}" if not files_ok else f"All four files found in {memory_dir}"
        })
    else:
        checks.append({
            "name": "memory_structure_exists",
            "passed": False,
            "detail": "Could not locate a 'memory/' directory with the required files anywhere in workspace."
        })

    if not files_ok:
        # Can't proceed meaningfully without files
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    # Load all four files
    wisdom   = load_file(memory_dir / "wisdom.md")
    goals    = load_file(memory_dir / "goals.md")
    mistakes = load_file(memory_dir / "mistakes.md")
    prefs    = load_file(memory_dir / "preferences.md")

    # ── CHECK 2: High-engagement events (>10) → preferences.md ──────────────
    # EVENT-001: 23 upvotes (long-form essay on MoltBook)
    # EVENT-006: 14 upvotes (long-form tutorial on MoltBook)
    # Both should produce preference entries about long-form content on MoltBook performing well
    high_eng_prefs = check_bullet_lines(prefs, [
        "long-form", "long form", "MoltBook", "23 upvotes", "14 upvotes", "essay", "tutorial", "high engagement"
    ])
    checks.append({
        "name": "high_engagement_saved_to_preferences",
        "passed": high_eng_prefs,
        "detail": f"preferences.md should contain entries about high-engagement (>10) posts (long-form MoltBook). Found: {high_eng_prefs}. Content snippet: {(prefs or '')[:300]}"
    })

    # ── CHECK 3: Zero engagement → mistakes.md ───────────────────────────────
    # EVENT-002: short one-liner on MicroChirp, 0 engagement
    zero_eng_mistake = check_bullet_lines(mistakes, [
        "short", "one-liner", "MicroChirp", "0 engagement", "0 upvotes", "no engagement", "short posts", "ignored"
    ])
    checks.append({
        "name": "zero_engagement_saved_to_mistakes",
        "passed": zero_eng_mistake,
        "detail": f"mistakes.md should contain an entry about zero-engagement post (short/MicroChirp). Content snippet: {(mistakes or '')[:300]}"
    })

    # ── CHECK 4: Constructive feedback → wisdom.md ───────────────────────────
    # EVENT-003: @data_wizard_99 constructive feedback about case studies
    constructive_wisdom = check_bullet_lines(wisdom, [
        "case stud", "feedback", "insightful", "impact", "data_wizard", "real-world"
    ])
    checks.append({
        "name": "constructive_feedback_saved_to_wisdom",
        "passed": constructive_wisdom,
        "detail": f"wisdom.md should contain lesson from constructive feedback (EVENT-003, add case studies). Content snippet: {(wisdom or '')[:300]}"
    })

    # ── CHECK 5: Rate-limit hit → mistakes.md ────────────────────────────────
    # EVENT-005: RATE_LIMIT_HIT on MoltBook
    rate_limit_mistake = check_bullet_lines(mistakes, [
        "rate limit", "rate-limit", "throttl", "too frequent", "space posts", "12 times", "posting frequency", "don't post too frequently"
    ])
    checks.append({
        "name": "rate_limit_saved_to_mistakes",
        "passed": rate_limit_mistake,
        "detail": f"mistakes.md should contain entry about rate limiting / spacing posts (EVENT-005). Content snippet: {(mistakes or '')[:300]}"
    })

    # ── CHECK 6: Cross-platform observation → preferences.md ─────────────────
    # EVENT-011: adapting content per platform outperforms copy-paste
    cross_platform_pref = check_bullet_lines(prefs, [
        "adapt", "cross-platform", "cross platform", "platform", "copy-past", "tone", "format", "length"
    ])
    checks.append({
        "name": "cross_platform_success_saved_to_preferences",
        "passed": cross_platform_pref,
        "detail": f"preferences.md should contain entry about adapting content per platform (EVENT-011). Content snippet: {(prefs or '')[:300]}"
    })

    # ── CHECK 7: Community insight → preferences or wisdom ───────────────────
    # EVENT-008: call-to-action posts outperform passive posts (multi-week observation → either preferences or wisdom acceptable)
    cta_saved = check_bullet_lines(wisdom, ["call-to-action", "call to action", "CTA", "outperform"]) or \
                check_bullet_lines(prefs, ["call-to-action", "call to action", "CTA", "outperform"])
    checks.append({
        "name": "community_insight_saved",
        "passed": cta_saved,
        "detail": f"EVENT-008 community insight (call-to-action) should appear in wisdom.md or preferences.md."
    })

    # ── CHECK 8: New goal → goals.md ─────────────────────────────────────────
    # EVENT-009: goal to become trusted AI assistant for ethical technology decisions
    goal_saved = check_bullet_lines(goals, [
        "trusted", "ethical", "enterprise", "technology decision", "AI assistant", "most trusted"
    ])
    checks.append({
        "name": "new_goal_saved_to_goals",
        "passed": goal_saved,
        "detail": f"goals.md should contain the new goal from EVENT-009. Content snippet: {(goals or '')[:300]}"
    })

    # ── CHECK 9: Valid criticism → mistakes.md ────────────────────────────────
    # EVENT-012: failed to verify sources before citing statistics (valid criticism)
    valid_criticism_mistake = check_bullet_lines(mistakes, [
        "verify source", "verif", "statistic", "citing", "source", "senior_reviewer", "repeated mistake"
    ])
    checks.append({
        "name": "valid_criticism_saved_to_mistakes",
        "passed": valid_criticism_mistake,
        "detail": f"mistakes.md should contain entry about failing to verify sources (EVENT-012). Content snippet: {(mistakes or '')[:300]}"
    })

    # ── CHECK 10: Principle observed → wisdom.md ─────────────────────────────
    # EVENT-015: clarifying question beats assuming the answer
    principle_wisdom = check_bullet_lines(wisdom, [
        "clarif", "ambiguous", "assum", "clarifying question", "misunderstand", "better than assuming"
    ])
    checks.append({
        "name": "principle_observation_saved_to_wisdom",
        "passed": principle_wisdom,
        "detail": f"wisdom.md should contain the principle from EVENT-015 (clarifying questions). Content snippet: {(wisdom or '')[:300]}"
    })

    # ── CHECK 11: NOISE / TOXIC items must NOT appear in memory ──────────────
    # EVENT-004: temporary mood - should NOT be saved
    # EVENT-007: unverified rumor - should NOT be saved
    # EVENT-010: toxic comment - should NOT be saved
    # EVENT-013: trivial interaction (what time is it) - should NOT be saved
    all_memory = (wisdom or "") + (goals or "") + (mistakes or "") + (prefs or "")

    toxic_saved = any_line_contains(all_memory, [
        "frustrated", "mood", "emotional state",  # EVENT-004 temporary emotion
    ])
    unverified_saved = any_line_contains(all_memory, [
        "shutting down", "anonymous source", "rumor",  # EVENT-007
    ])
    toxic_comment_saved = any_line_contains(all_memory, [
        "useless garbage", "should be deleted",  # EVENT-010
    ])
    trivial_saved = any_line_contains(all_memory, [
        "what time is it", "time is it",  # EVENT-013
    ])

    noise_correctly_excluded = not (toxic_saved or unverified_saved or toxic_comment_saved or trivial_saved)
    checks.append({
        "name": "noise_and_toxic_correctly_excluded",
        "passed": noise_correctly_excluded,
        "detail": f"Noise/toxic items should NOT appear in memory. "
                  f"toxic_emotion_saved={toxic_saved}, unverified_rumor_saved={unverified_saved}, "
                  f"toxic_comment_saved={toxic_comment_saved}, trivial_saved={trivial_saved}"
    })

    # ── CHECK 12: Bullet-point format throughout ──────────────────────────────
    # All non-empty, non-header lines that add content should use "- " format
    format_ok = True
    format_detail = []
    for fname, content in [("wisdom.md", wisdom), ("goals.md", goals), ("mistakes.md", mistakes), ("preferences.md", prefs)]:
        if not content:
            continue
        bullet_count = count_bullet_lines(content)
        if bullet_count == 0:
            # File might only have headers or be empty - acceptable only if truly empty
            non_empty_non_header = [
                l for l in content.splitlines()
                if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("-")
            ]
            if non_empty_non_header:
                format_ok = False
                format_detail.append(f"{fname} has non-bullet content lines: {non_empty_non_header[:3]}")
    checks.append({
        "name": "bullet_point_format_used",
        "passed": format_ok,
        "detail": "; ".join(format_detail) if format_detail else "All memory files use bullet-point format correctly."
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)

    # Overall pass: must pass structure + at least 8 out of remaining 11 content checks
    structure_passed = checks[0]["passed"]
    content_checks_passed = sum(1 for c in checks[1:] if c["passed"])
    overall_passed = structure_passed and content_checks_passed >= 8

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()