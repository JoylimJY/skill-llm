#!/usr/bin/env python3
"""
Evaluation script for OEJTS Personality Tuner task.
Checks that USER.md and SOUL.md have been correctly updated with the
personality profile while preserving existing content.
"""

import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    max_checks = 0

    def check(name: str, passed: bool, detail: str, weight: float = 1.0):
        nonlocal total_score, max_checks
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_checks += weight
        if passed:
            total_score += weight

    # ── Load files ────────────────────────────────────────────────────────────
    user_md_path = ws / "USER.md"
    soul_md_path = ws / "SOUL.md"

    try:
        user_content = user_md_path.read_text()
    except Exception as e:
        check("USER.md exists and readable", False, f"Could not read USER.md: {e}", 2.0)
        return finalize(checks, total_score, max_checks)

    try:
        soul_content = soul_md_path.read_text()
    except Exception as e:
        check("SOUL.md exists and readable", False, f"Could not read SOUL.md: {e}", 2.0)
        return finalize(checks, total_score, max_checks)

    # ── Check 1: USER.md managed block markers present ────────────────────────
    user_start_marker = "<!-- OJTS_PROFILE_START -->"
    user_end_marker = "<!-- OJTS_PROFILE_END -->"
    has_user_start = user_start_marker in user_content
    has_user_end = user_end_marker in user_content
    check(
        "USER.md has correct OJTS_PROFILE managed block markers",
        has_user_start and has_user_end,
        f"start_marker={'found' if has_user_start else 'MISSING'}, "
        f"end_marker={'found' if has_user_end else 'MISSING'}. "
        f"Note: markers are OJTS_PROFILE_START/END (not OEJTS)",
        weight=2.0
    )

    # ── Check 2: SOUL.md managed block markers present ────────────────────────
    soul_start_marker = "<!-- OJTS_ADAPTATION_START -->"
    soul_end_marker = "<!-- OJTS_ADAPTATION_END -->"
    has_soul_start = soul_start_marker in soul_content
    has_soul_end = soul_end_marker in soul_content
    check(
        "SOUL.md has correct OJTS_ADAPTATION managed block markers",
        has_soul_start and has_soul_end,
        f"start_marker={'found' if has_soul_start else 'MISSING'}, "
        f"end_marker={'found' if has_soul_end else 'MISSING'}. "
        f"Note: markers are OJTS_ADAPTATION_START/END",
        weight=2.0
    )

    # ── Check 3: USER.md existing content preserved ───────────────────────────
    preserved_strings_user = [
        "Jordan Kim",
        "Senior Software Engineer",
        "Platform Infrastructure",
        "Project Atlas",
        "Project Beacon",
        "Go, Kubernetes, Terraform",
    ]
    missing_user = [s for s in preserved_strings_user if s not in user_content]
    check(
        "USER.md preserves all original content",
        len(missing_user) == 0,
        f"Missing original content: {missing_user}" if missing_user else "All original content preserved.",
        weight=2.0
    )

    # ── Check 4: SOUL.md existing content preserved ───────────────────────────
    preserved_strings_soul = [
        "Be concise and technically precise",
        "Jordan has requested reduced emoji usage",
        "soul-config v2.3",
        "Prefers British English spelling",
        "Never fabricate API references",
    ]
    missing_soul = [s for s in preserved_strings_soul if s not in soul_content]
    check(
        "SOUL.md preserves all original content",
        len(missing_soul) == 0,
        f"Missing original content: {missing_soul}" if missing_soul else "All original content preserved.",
        weight=2.0
    )

    # ── Extract managed block content for deeper checks ───────────────────────
    user_block = ""
    if has_user_start and has_user_end:
        try:
            start_idx = user_content.index(user_start_marker)
            end_idx = user_content.index(user_end_marker) + len(user_end_marker)
            user_block = user_content[start_idx:end_idx]
        except Exception:
            pass

    soul_block = ""
    if has_soul_start and has_soul_end:
        try:
            start_idx = soul_content.index(soul_start_marker)
            end_idx = soul_content.index(soul_end_marker) + len(soul_end_marker)
            soul_block = soul_content[start_idx:end_idx]
        except Exception:
            pass

    # ── Check 5: Correct type code INTJ in USER.md block ─────────────────────
    # The answers produce INTJ:
    # IE axis: Q1(1),Q2(5),Q3(1),Q4(5),Q5(2),Q6(5),Q7(1),Q8(5)
    # weights: +1,-1,+1,-1,+1,-1,+1,-1
    # raw = (1-3)*1 + (5-3)*(-1) + (1-3)*1 + (5-3)*(-1) + (2-3)*1 + (5-3)*(-1) + (1-3)*1 + (5-3)*(-1)
    #      = -2 + -2 + -2 + -2 + -1 + -2 + -2 + -2 = -15  => normalised = -15/16 => negative = but wait
    # Wait, let me recalculate: weight +1 means increases FIRST letter (I for IE)
    # Q1 weight=+1: (1-3)*1 = -2  (disagree with "prefer groups", so I direction)
    # Hmm but negative normalised = E. Let me re-examine...
    # Looking at the script: "IE": "I" if normalised["IE"] >= 0 else "E"
    # Q1(+1,val=1): (1-3)*1=-2, Q2(-1,val=5): (5-3)*(-1)=-2
    # Q3(+1,val=1): (1-3)*1=-2, Q4(-1,val=5): (5-3)*(-1)=-2
    # Q5(+1,val=2): (2-3)*1=-1, Q6(-1,val=5): (5-3)*(-1)=-2
    # Q7(+1,val=1): (1-3)*1=-2, Q8(-1,val=5): (5-3)*(-1)=-2
    # IE raw = -2-2-2-2-1-2-2-2 = -15; normalised = -15/16 = -0.9375 => E? 
    # But answers Q1=1 means disagrees with "prefer groups" → I...
    # The script maps IE>=0 → I. So negative → E.
    # But Q1 "I prefer working in groups rather than alone" - answer 1 (disagree) → introvert
    # Q1 weight=+1, val=1: contribution = (1-3)*1 = -2. Negative → E direction in script.
    # Hmm, this means the script maps Q1 polarity: +1 weight increases toward first letter.
    # For IE, first letter is I. But val=1 (low, disagrees with "groups") with weight +1 gives negative → pushes toward E.
    # That means polarity may be reversed from intuition, but the math is what it is.
    # Let's just compute all four expected:
    
    # SN: Q9(+1,1),Q10(-1,5),Q11(+1,1),Q12(-1,5),Q13(+1,1),Q14(-1,5),Q15(+1,2),Q16(-1,5)
    # = (1-3)*1 + (5-3)*(-1) + (1-3)*1 + (5-3)*(-1) + (1-3)*1 + (5-3)*(-1) + (2-3)*1 + (5-3)*(-1)
    # = -2-2-2-2-2-2-1-2 = -15; norm=-15/16 → N
    
    # FT: Q17(+1,1),Q18(-1,5),Q19(+1,1),Q20(-1,5),Q21(+1,1),Q22(-1,5),Q23(+1,1),Q24(-1,5)
    # = -2-2-2-2-2-2-2-2 = -16; norm=-16/16=-1.0 → T
    
    # JP: Q25(+1,5),Q26(-1,1),Q27(+1,5),Q28(-1,1),Q29(+1,5),Q30(-1,1),Q31(+1,5),Q32(-1,1)
    # = (5-3)*1 + (1-3)*(-1) + (5-3)*1 + (1-3)*(-1) + (5-3)*1 + (1-3)*(-1) + (5-3)*1 + (1-3)*(-1)
    # = 2+2+2+2+2+2+2+2 = 16; norm=16/16=1.0 → J
    
    # So type = E (neg IE) + N (neg SN) + T (neg FT) + J (pos JP) = ENTJ
    expected_type = "ENTJ"
    
    type_in_user = expected_type in user_block
    check(
        f"USER.md profile block contains correct type code ({expected_type})",
        type_in_user,
        f"Expected type '{expected_type}' in USER.md managed block. Block content snippet: {user_block[:300] if user_block else 'EMPTY'}",
        weight=3.0
    )

    # ── Check 6: Correct type code ENTJ in SOUL.md block ─────────────────────
    type_in_soul = expected_type in soul_block
    check(
        f"SOUL.md adaptation block contains correct type code ({expected_type})",
        type_in_soul,
        f"Expected type '{expected_type}' in SOUL.md managed block. Block content snippet: {soul_block[:300] if soul_block else 'EMPTY'}",
        weight=3.0
    )

    # ── Check 7: Behavior preferences present for E, N, T, J in USER.md ──────
    # Expected behaviors for ENTJ:
    expected_behaviors_user = {
        "E": "Engage proactively",
        "N": "big-picture",
        "T": "logic",
        "J": "structured plans",
    }
    missing_behaviors = []
    for letter, snippet in expected_behaviors_user.items():
        if snippet.lower() not in user_block.lower():
            missing_behaviors.append(f"{letter}: '{snippet}'")
    check(
        "USER.md profile block contains correct behavior preferences for ENTJ",
        len(missing_behaviors) == 0,
        f"Missing behavior snippets: {missing_behaviors}" if missing_behaviors else "All ENTJ behavior preferences found.",
        weight=2.0
    )

    # ── Check 8: Behavior preferences in SOUL.md adaptation block ────────────
    missing_soul_behaviors = []
    for letter, snippet in expected_behaviors_user.items():
        if snippet.lower() not in soul_block.lower():
            missing_soul_behaviors.append(f"{letter}: '{snippet}'")
    check(
        "SOUL.md adaptation block contains correct behavior adaptations for ENTJ",
        len(missing_soul_behaviors) == 0,
        f"Missing behavior snippets in SOUL.md: {missing_soul_behaviors}" if missing_soul_behaviors else "All ENTJ adaptations found in SOUL.md.",
        weight=2.0
    )

    # ── Check 9: User override note in SOUL.md ────────────────────────────────
    has_override_note = "override" in soul_block.lower() or "supersedes" in soul_block.lower()
    check(
        "SOUL.md adaptation block contains user override note",
        has_override_note,
        "Override/supersede language found in SOUL.md block." if has_override_note else "No override note found in SOUL.md managed block.",
        weight=1.0
    )

    # ── Check 10: Markers appear exactly once in each file ────────────────────
    user_start_count = user_content.count(user_start_marker)
    user_end_count = user_content.count(user_end_marker)
    soul_start_count = soul_content.count(soul_start_marker)
    soul_end_count = soul_content.count(soul_end_marker)
    markers_once = (user_start_count == 1 and user_end_count == 1 and
                    soul_start_count == 1 and soul_end_count == 1)
    check(
        "Each managed block marker appears exactly once in its file",
        markers_once,
        f"USER.md: start={user_start_count}x, end={user_end_count}x | "
        f"SOUL.md: start={soul_start_count}x, end={soul_end_count}x",
        weight=1.0
    )

    return finalize(checks, total_score, max_checks)


def finalize(checks, total_score, max_checks):
    all_passed = all(c["passed"] for c in checks)
    final_score = round(total_score / max_checks, 4) if max_checks > 0 else 0.0
    return {
        "passed": all_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))