import os
import random
from pathlib import Path

random.seed(42)

workspace = Path(os.environ.get("WORKSPACE", "/root"))
act_dir = workspace / "act"

# Create full directory structure
for d in ["sections", "practice", "vocab", "formulas"]:
    (act_dir / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────

# 1. Old, incomplete profile stub (wrong format, missing fields)
(act_dir / "profile.md").write_text(
    "# Student Profile\nName: Jordan Lee\nGoal: Get into college\n"
    "Test: sometime next year\n"
    "# NOTE: This file is incomplete and needs to be properly set up.\n"
)

# 2. Distractor vocab file
(act_dir / "vocab" / "word_list.md").write_text(
    "## Vocabulary\n- Ephemeral: lasting for a very short time\n"
    "- Recalcitrant: stubbornly uncooperative\n"
    "- Loquacious: tending to talk a great deal\n"
)

# 3. Distractor formulas file
(act_dir / "formulas" / "math_basics.md").write_text(
    "## Math Formulas\n- Area of circle: πr²\n- Quadratic: (-b ± √(b²-4ac)) / 2a\n"
    "- Distance formula: √((x2-x1)² + (y2-y1)²)\n"
)

# 4. Stale/empty section files to be replaced
for section in ["english", "math", "reading", "science"]:
    (act_dir / "sections" / f"{section}.md").write_text(
        f"# {section.title()} Section\n_No data recorded yet._\n"
    )

# 5. Practice test results — RAW messy data (agent must interpret and process)
# Three practice tests with per-section scores
practice_raw = {
    "practice_test_1.md": (
        "## Practice Test 1 — 2024-09-15\n"
        "English: 24\n"
        "Math: 21\n"
        "Reading: 23\n"
        "Science: 22\n"
        "Composite: 22\n\n"
        "### Errors (raw notes)\n"
        "- english: missed comma splice rules (3 wrong), pronoun agreement (2 wrong)\n"
        "- math: forgot distance/midpoint formulas (4 wrong), trig basics (3 wrong)\n"
        "- reading: ran out of time on passage 3, guessed last 4\n"
        "- science: confused contradicting viewpoints questions, skipped 2\n"
    ),
    "practice_test_2.md": (
        "## Practice Test 2 — 2024-10-12\n"
        "English: 26\n"
        "Math: 22\n"
        "Reading: 21\n"
        "Science: 25\n"
        "Composite: 24\n\n"
        "### Errors (raw notes)\n"
        "- english: still missing punctuation within clauses (2 wrong), transition words (1 wrong)\n"
        "- math: coordinate geometry errors (3 wrong), forgot SOHCAHTOA (2 wrong)\n"
        "- reading: poor pacing again — passage 4 rushed, inference questions wrong (5 wrong)\n"
        "- science: data representation fine, research summaries confused (3 wrong)\n"
    ),
    "practice_test_3.md": (
        "## Practice Test 3 — 2024-11-08\n"
        "English: 25\n"
        "Math: 24\n"
        "Reading: 22\n"
        "Science: 23\n"
        "Composite: 24\n\n"
        "### Errors (raw notes)\n"
        "- english: redundancy/wordiness (3 wrong)\n"
        "- math: systems of equations (2 wrong), logarithm rules (2 wrong)\n"
        "- reading: main idea questions ok, but detail/inference split wrong (4 wrong)\n"
        "- science: conflicting viewpoints passage still slow (3 wrong)\n"
    ),
}

for filename, content in practice_raw.items():
    (act_dir / "practice" / filename).write_text(content)

# 6. A feedback stub that is empty/placeholder
(act_dir / "feedback.md").write_text(
    "# Strategy Feedback\n_To be filled in after analysis._\n"
)

# 7. College targets raw notes (messy, unstructured)
(act_dir / "college_targets_raw.txt").write_text(
    "Colleges Jordan is interested in:\n"
    "1. University of Michigan — Ann Arbor: typical ACT range 32-35, no writing required\n"
    "2. Ohio State University: typical ACT range 27-33, writing NOT required\n"
    "3. University of Illinois Urbana-Champaign: ACT range 26-32, writing NOT required\n"
    "4. Indiana University Bloomington: ACT range 24-31, writing NOT required\n"
    "Jordan wants to be competitive at Ohio State and realistic at IU Bloomington.\n"
    "Test date: February 8, 2025\n"
    "Current date context: November 2024 (~13 weeks out)\n"
    "Jordan studies about 8 hours/week.\n"
    "Jordan is a high school junior, so user type = student.\n"
    "Jordan does NOT need the Writing section (none of the target colleges require it).\n"
    "Target composite: 30\n"
)

# 8. Additional distractor files
(act_dir / "sections" / "writing.md").write_text(
    "# Writing Section\n_Not applicable — check profile for Writing requirement._\n"
)

(act_dir / "vocab" / "science_terms.md").write_text(
    "## Science Vocab\n- Hypothesis: testable prediction\n"
    "- Variable: factor that can change in an experiment\n"
    "- Control group: baseline comparison group\n"
)

(act_dir / "formulas" / "science_concepts.md").write_text(
    "## Science Concepts\n- Conflicting viewpoints: read each scientist separately\n"
    "- Data representation: identify axes and units first\n"
)

# 9. A red-herring "study_plan.md" that is wrong/outdated
(act_dir / "study_plan_OLD.md").write_text(
    "# Old Study Plan (OUTDATED — DO NOT USE)\n"
    "Week 1: Review all sections equally\n"
    "Week 2: Take a practice test\n"
    "Week 3: Review everything again\n"
    "This plan ignores weak area targeting and superscore strategy.\n"
)

print("Workspace initialized successfully.")
print(f"ACT prep directory created at: {act_dir}")