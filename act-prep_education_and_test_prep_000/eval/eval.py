import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    act_dir = Path(workspace) / "act"

    def check(name, condition, detail):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})
        return bool(condition)

    # ── 1. profile.md exists and has required Decision Checklist fields ──────
    profile_path = act_dir / "profile.md"
    profile_text = ""
    try:
        profile_text = profile_path.read_text().lower()
        profile_exists = True
    except Exception as e:
        profile_exists = False
        check("profile.md exists", False, f"Missing profile.md: {e}")

    if profile_exists:
        check("profile.md exists", True, "File found.")

        # Test date present
        has_test_date = bool(re.search(r"(test date|february|feb|2025)", profile_text))
        check("profile: test date recorded", has_test_date,
              "Expected test date (February 2025) in profile.md" if not has_test_date else "Test date found.")

        # Target composite score = 30
        has_target_30 = bool(re.search(r"(target.*30|composite.*30|goal.*30|30.*target|30.*composite)", profile_text))
        check("profile: target composite score = 30", has_target_30,
              "Expected target composite score of 30 in profile.md" if not has_target_30 else "Target score 30 found.")

        # Baseline/current scores present (should reference current ~22-24 range)
        has_baseline = bool(re.search(r"(baseline|current score|composite.*2[234]|2[234].*composite)", profile_text))
        check("profile: baseline score recorded", has_baseline,
              "Expected baseline composite score (~22-24) in profile.md" if not has_baseline else "Baseline found.")

        # Colleges listed
        has_colleges = bool(re.search(r"(ohio state|michigan|illinois|indiana)", profile_text))
        check("profile: target colleges listed", has_colleges,
              "Expected target colleges in profile.md" if not has_colleges else "Colleges found.")

        # User type = student
        has_user_type = bool(re.search(r"(user type|student)", profile_text))
        check("profile: user type = student", has_user_type,
              "Expected user type 'student' in profile.md" if not has_user_type else "User type found.")

        # Writing NOT required
        writing_not_required = bool(re.search(
            r"(writing.*(not required|no|false|n/a|optional|skip|not needed|exempt)|"
            r"(not required|no|false|n/a|skip|not needed).*writing)",
            profile_text
        ))
        check("profile: Writing section marked as NOT required", writing_not_required,
              "Profile must indicate Writing is not required for Jordan's target colleges."
              if not writing_not_required else "Writing not-required flag found.")

        # Study hours/week recorded
        has_study_hours = bool(re.search(r"(8 hour|8hr|hours.*week|week.*hours)", profile_text))
        check("profile: study hours per week recorded", has_study_hours,
              "Expected '8 hours/week' study availability in profile.md"
              if not has_study_hours else "Study hours found.")

    # ── 2. Section files have error analysis (WHY, not just scores) ──────────
    sections = ["english", "math", "reading", "science"]
    error_analysis_keywords = [
        "comma", "pronoun", "trig", "formula", "pacing", "time", "inference",
        "viewpoint", "coordinate", "redundan", "logarithm", "wordiness",
        "punctuation", "transition", "midpoint", "sohcahtoa", "equation"
    ]

    sections_with_why_analysis = 0
    for section in sections:
        section_path = act_dir / "sections" / f"{section}.md"
        try:
            section_text = section_path.read_text().lower()
            # Must have at least one "why" keyword (not just scores)
            has_why = any(kw in section_text for kw in error_analysis_keywords)
            # Must NOT be the original stub
            not_stub = "_no data recorded yet_" not in section_text and len(section_text) > 80
            if has_why and not_stub:
                sections_with_why_analysis += 1
        except Exception:
            pass

    check("sections: ≥3 sections have WHY-based error analysis",
          sections_with_why_analysis >= 3,
          f"Only {sections_with_why_analysis}/4 section files have error analysis explaining WHY questions were missed."
          if sections_with_why_analysis < 3
          else f"{sections_with_why_analysis}/4 sections have proper error analysis.")

    # ── 3. Superscore calculation — per-section max across all 3 tests ───────
    # Expected per-section bests:
    #   English: max(24,26,25) = 26
    #   Math:    max(21,22,24) = 24
    #   Reading: max(23,21,22) = 23
    #   Science: max(22,25,23) = 25
    #   Superscore composite: (26+24+23+25)/4 = 24.5 → rounded = 25
    #
    # The agent must compute superscore = 25 (NOT just pick best composite = 24)

    EXPECTED_SUPERSCORE = 25
    EXPECTED_ENG = 26
    EXPECTED_MATH = 24
    EXPECTED_READ = 23
    EXPECTED_SCI = 25

    superscore_locations = []
    for candidate_path in [
        act_dir / "profile.md",
        act_dir / "feedback.md",
    ] + list((act_dir / "practice").glob("*.md")):
        try:
            superscore_locations.append(candidate_path.read_text().lower())
        except Exception:
            pass

    combined_text = "\n".join(superscore_locations)

    # Check superscore value of 25 is mentioned
    has_superscore_25 = bool(re.search(
        r"(superscore.*25|25.*superscore|super\s*score.*25|25.*super\s*score|"
        r"super score.*25|projected.*25|best.*composite.*25|composite.*best.*25)",
        combined_text
    ))
    check("superscore: composite superscore = 25 computed",
          has_superscore_25,
          f"Expected superscore composite of {EXPECTED_SUPERSCORE} (best section scores summed/averaged). "
          "Superscore ≠ best single-test composite (which was 24)."
          if not has_superscore_25
          else "Superscore of 25 found.")

    # Check that section bests are mentioned (at least 2 of 4)
    section_best_hits = 0
    # English best = 26
    if re.search(r"(english.*26|26.*english)", combined_text):
        section_best_hits += 1
    # Math best = 24
    if re.search(r"(math.*24|24.*math)", combined_text):
        section_best_hits += 1
    # Science best = 25
    if re.search(r"(science.*25|25.*science)", combined_text):
        section_best_hits += 1
    # Reading best = 23
    if re.search(r"(reading.*23|23.*reading)", combined_text):
        section_best_hits += 1

    check("superscore: per-section best scores identified (≥2 of 4)",
          section_best_hits >= 2,
          f"Only {section_best_hits}/4 per-section best scores explicitly identified. "
          "Expected English=26, Math=24, Reading=23, Science=25."
          if section_best_hits < 2
          else f"{section_best_hits}/4 section best scores found.")

    # ── 4. feedback.md — non-stub, documents what works/doesn't ─────────────
    feedback_path = act_dir / "feedback.md"
    feedback_text = ""
    try:
        feedback_text = feedback_path.read_text().lower()
    except Exception as e:
        check("feedback.md updated with strategy notes", False, f"Cannot read feedback.md: {e}")

    feedback_meaningful = (
        len(feedback_text) > 150 and
        "_to be filled in after analysis_" not in feedback_text and
        bool(re.search(r"(strateg|work|improv|focus|pacing|error|weak|strong|section)", feedback_text))
    )
    check("feedback.md: updated with meaningful strategy feedback",
          feedback_meaningful,
          "feedback.md still contains placeholder text or is too short/generic."
          if not feedback_meaningful else "feedback.md has meaningful content.")

    # ── 5. College targeting — realistic gap analysis ─────────────────────────
    # Jordan's superscore = 25. Target colleges require 27-33 (Ohio State) and 24-31 (IU).
    # Profile or a targeting section should note that Jordan is currently competitive
    # for IU Bloomington but needs significant improvement for Ohio State.

    targeting_text = ""
    for p in [profile_path, feedback_path]:
        try:
            targeting_text += p.read_text().lower()
        except Exception:
            pass

    has_gap_analysis = bool(re.search(
        r"(indiana|iu|bloomington|gap|below|reach|target|need.*point|point.*need|"
        r"competitive|ohio.*state|improve|short|not yet|27|30)",
        targeting_text
    ))
    check("college targeting: gap analysis references score requirements",
          has_gap_analysis,
          "Expected college targeting analysis noting Jordan's score gap vs. Ohio State / IU requirements."
          if not has_gap_analysis else "College targeting gap analysis found.")

    # ── 6. Writing section — sections/writing.md should note NOT required ────
    writing_path = act_dir / "sections" / "writing.md"
    try:
        writing_text = writing_path.read_text().lower()
        writing_correctly_flagged = bool(re.search(
            r"(not required|no|skip|n/a|exempt|not needed|optional.*skip|do not prep|"
            r"none.*target|target.*none|not prepping)",
            writing_text
        ))
        check("sections/writing.md: correctly marked not required",
              writing_correctly_flagged,
              "sections/writing.md should clearly indicate Writing is not required for Jordan's colleges."
              if not writing_correctly_flagged else "Writing section correctly flagged.")
    except Exception as e:
        check("sections/writing.md: correctly marked not required", False,
              f"Cannot read writing.md: {e}")

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)

    return {
        "passed": passed_count >= 10,  # Must pass at least 10/12 checks
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/root"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))