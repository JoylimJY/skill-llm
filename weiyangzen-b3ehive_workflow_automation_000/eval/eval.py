import sys
import os
import re
import json
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
checks = []
total_score = 0.0
max_score = 100.0


def check(name, condition, detail, weight=0):
    global total_score
    passed = bool(condition)
    if passed:
        total_score += weight
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed


def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return None


# ─────────────────────────────────────────────
# PHASE 1 CHECKS: run_a, run_b, run_c structure
# ─────────────────────────────────────────────

for agent in ["a", "b", "c"]:
    agent_dir = Path(workspace) / f"run_{agent}"

    # Check implementation/main.* exists
    impl_files = list((agent_dir / "implementation").glob("main.*")) if (agent_dir / "implementation").exists() else []
    has_impl = len(impl_files) > 0
    check(
        f"run_{agent}: implementation/main.* exists",
        has_impl,
        f"Found: {[str(f.name) for f in impl_files]}" if has_impl else "No main.* found in implementation/",
        weight=4
    )

    # Check Checklist.md has NO unchecked items
    checklist_path = agent_dir / "Checklist.md"
    checklist_content = read_file(checklist_path)
    if checklist_content is None:
        check(f"run_{agent}: Checklist.md exists", False, "Checklist.md missing", weight=3)
        check(f"run_{agent}: Checklist.md fully checked", False, "Checklist.md missing", weight=3)
    else:
        check(f"run_{agent}: Checklist.md exists", True, "File found", weight=1)
        has_unchecked = bool(re.search(r'-\s*\[\s*\]', checklist_content))
        has_checked = bool(re.search(r'-\s*\[x\]', checklist_content, re.IGNORECASE))
        check(
            f"run_{agent}: Checklist.md fully checked (no '- [ ]' items)",
            not has_unchecked and has_checked,
            f"unchecked_items={'yes' if has_unchecked else 'no'}, has_checked_items={'yes' if has_checked else 'no'}",
            weight=3
        )

    # Check SUMMARY.md is non-trivial (not just placeholder)
    summary_path = agent_dir / "SUMMARY.md"
    summary_content = read_file(summary_path)
    if summary_content is None:
        check(f"run_{agent}: SUMMARY.md exists and non-trivial", False, "SUMMARY.md missing", weight=2)
    else:
        is_placeholder = "TODO" in summary_content or len(summary_content.strip()) < 100
        check(
            f"run_{agent}: SUMMARY.md is non-trivial",
            not is_placeholder,
            f"Length={len(summary_content.strip())}, contains_TODO={'yes' if 'TODO' in summary_content else 'no'}",
            weight=2
        )

# ─────────────────────────────────────────────
# PHASE 2 CHECKS: 6 cross-evaluation reports
# ─────────────────────────────────────────────

total_eval_files = 0
numeric_scores_present = 0
for agent_from in ["a", "b", "c"]:
    eval_dir = Path(workspace) / f"run_{agent_from}" / "evaluation"
    if not eval_dir.exists():
        continue
    eval_files = list(eval_dir.glob("EVALUATION_*.md")) + list(eval_dir.glob("evaluation_*.md"))
    for ef in eval_files:
        total_eval_files += 1
        content = read_file(ef)
        if content:
            # Check for numeric scores (digits in context of score/points)
            if re.search(r'\b(\d{1,2})\s*/\s*\d{1,2}\b|\bscore[:\s]+\d+|\b\d+\s*pts\b|\|\s*\d+\s*\|', content, re.IGNORECASE):
                numeric_scores_present += 1

check(
    "Phase 2: Exactly 6 cross-evaluation reports exist",
    total_eval_files == 6,
    f"Found {total_eval_files} evaluation files (expected 6)",
    weight=8
)
check(
    "Phase 2: Evaluation reports contain numeric scores",
    numeric_scores_present >= 4,
    f"{numeric_scores_present}/{total_eval_files} evaluation files have detectable numeric scores",
    weight=5
)

# ─────────────────────────────────────────────
# PHASE 3 CHECKS: 3 SCORECARD.md files
# ─────────────────────────────────────────────

scorecard_count = 0
valid_dimension_scores = 0
DIMENSIONS = ["simplicity", "speed", "stability", "corner_cases", "corner cases", "maintainability"]
WEIGHTS = {"simplicity": 20, "speed": 25, "stability": 25, "maintainability": 10}

for agent in ["a", "b", "c"]:
    sc_path = Path(workspace) / f"run_{agent}" / "SCORECARD.md"
    content = read_file(sc_path)
    if content is None:
        check(f"run_{agent}: SCORECARD.md exists", False, "SCORECARD.md missing", weight=2)
        continue
    scorecard_count += 1
    check(f"run_{agent}: SCORECARD.md exists", True, "File found", weight=2)

    # Check all 5 dimensions mentioned
    found_dims = sum(1 for d in DIMENSIONS if d.lower() in content.lower())
    has_all_dims = found_dims >= 4  # at least 4 of the 5+ keywords
    check(
        f"run_{agent}: SCORECARD.md references all scoring dimensions",
        has_all_dims,
        f"Found {found_dims} dimension keywords in scorecard",
        weight=2
    )

    # Check numeric scores are present
    has_numbers = bool(re.search(r'\b\d{1,2}\b', content))
    check(
        f"run_{agent}: SCORECARD.md contains numeric scores",
        has_numbers,
        f"Numeric values found: {has_numbers}",
        weight=2
    )

check(
    "Phase 3: All 3 scorecards exist",
    scorecard_count == 3,
    f"Found {scorecard_count}/3 scorecards",
    weight=2
)

# ─────────────────────────────────────────────
# PHASE 4 CHECKS: final/ directory, COMPARISON_REPORT.md, DECISION_RATIONALE.md
# ─────────────────────────────────────────────

# final/ directory with runnable code
final_dir = Path(workspace) / "final"
final_has_code = False
if final_dir.exists():
    # any .py, .js, .ts, .go, .rb, .java file
    code_files = list(final_dir.rglob("*.py")) + list(final_dir.rglob("*.js")) + \
                 list(final_dir.rglob("*.ts")) + list(final_dir.rglob("*.go"))
    final_has_code = len(code_files) > 0

check(
    "Phase 4: final/ directory exists",
    final_dir.exists(),
    f"final/ dir exists: {final_dir.exists()}",
    weight=3
)
check(
    "Phase 4: final/ directory contains runnable code",
    final_has_code,
    f"Code files in final/: {[str(f.relative_to(workspace)) for f in (list(final_dir.rglob('*.py')) if final_dir.exists() else [])[:3]]}",
    weight=4
)

# COMPARISON_REPORT.md
cr_candidates = list(Path(workspace).rglob("COMPARISON_REPORT.md"))
cr_content = read_file(cr_candidates[0]) if cr_candidates else None
has_cr = cr_content is not None and len(cr_content.strip()) > 200

check(
    "Phase 4: COMPARISON_REPORT.md exists and is substantive",
    has_cr,
    f"Found at: {str(cr_candidates[0]) if cr_candidates else 'not found'}, length={len(cr_content) if cr_content else 0}",
    weight=5
)

# COMPARISON_REPORT.md mentions all three agents
if cr_content:
    agents_mentioned = sum(1 for ag in ["Agent A", "Agent B", "Agent C"] if ag in cr_content or f"run_{ag.split()[-1].lower()}" in cr_content.lower())
    check(
        "COMPARISON_REPORT.md references all three agents",
        agents_mentioned >= 3,
        f"Agent references found: {agents_mentioned}/3",
        weight=3
    )
else:
    check("COMPARISON_REPORT.md references all three agents", False, "Report missing", weight=3)

# DECISION_RATIONALE.md
dr_candidates = list(Path(workspace).rglob("DECISION_RATIONALE.md"))
dr_content = read_file(dr_candidates[0]) if dr_candidates else None
has_dr = dr_content is not None and len(dr_content.strip()) > 100

check(
    "Phase 4: DECISION_RATIONALE.md exists and is substantive",
    has_dr,
    f"Found at: {str(dr_candidates[0]) if dr_candidates else 'not found'}, length={len(dr_content) if dr_content else 0}",
    weight=5
)

# ─────────────────────────────────────────────
# PROPRIETARY TRAP: Decision threshold logic check
# ─────────────────────────────────────────────
# The DECISION_RATIONALE.md must indicate which decision strategy was used
# and it must be consistent with the score margins (>15, 5-15, <=5)

decision_strategy_mentioned = False
threshold_terms = ["single winner", "hybrid", "simplest", "clear winner", "margin", "threshold",
                   "15 point", "15-point", "15pts", "> 15", ">15", "5 point", "SingleWinner",
                   "HybridSolution", "SimplestImplementation"]
if dr_content:
    content_lower = dr_content.lower()
    decision_strategy_mentioned = any(term.lower() in content_lower for term in threshold_terms)

check(
    "DECISION_RATIONALE.md applies threshold-based winner selection logic",
    decision_strategy_mentioned,
    f"Threshold/strategy terms found: {[t for t in threshold_terms if dr_content and t.lower() in dr_content.lower()][:3]}",
    weight=8
)

# ─────────────────────────────────────────────
# EVALUATION WEIGHTS CHECK
# The scorecards/reports should reflect correct dimension weights
# simplicity=20, speed=25, stability=25, corner_cases=20, maintainability=10
# ─────────────────────────────────────────────

weight_evidence = []
all_content = ""
for agent in ["a", "b", "c"]:
    sc = read_file(Path(workspace) / f"run_{agent}" / "SCORECARD.md") or ""
    all_content += sc

if cr_content:
    all_content += cr_content
if dr_content:
    all_content += dr_content

# Check that the weights 20, 25, 25, 20, 10 appear in context of scoring
weight_patterns = [
    (r'\b20\b.*simpl|\bsimpl.*\b20\b', "simplicity weight=20"),
    (r'\b25\b.*speed|\bspeed.*\b25\b', "speed weight=25"),
    (r'\b25\b.*stabil|\bstabil.*\b25\b', "stability weight=25"),
    (r'\b10\b.*maintain|\bmaintain.*\b10\b', "maintainability weight=10"),
]

weights_found = 0
for pattern, desc in weight_patterns:
    if re.search(pattern, all_content, re.IGNORECASE | re.DOTALL):
        weights_found += 1
        weight_evidence.append(desc)

check(
    "Scoring uses correct dimension weights (20/25/25/20/10)",
    weights_found >= 2,
    f"Weight patterns found: {weight_evidence}",
    weight=6
)

# ─────────────────────────────────────────────
# BONUS: winning agent is attributed in final deliverable
# ─────────────────────────────────────────────
attribution_found = False
if dr_content:
    attribution_found = bool(re.search(r'(Agent\s+[ABC]|run_[abc])\s+(wins|selected|winner|chosen|best)', dr_content, re.IGNORECASE))
    if not attribution_found:
        # looser check: any mention of a specific agent being the winner
        attribution_found = bool(re.search(r'winner[:\s]+(Agent\s+[ABC]|run_[abc])|best[:\s]+(Agent\s+[ABC]|run_[abc])', dr_content, re.IGNORECASE))

check(
    "DECISION_RATIONALE.md attributes winning agent",
    attribution_found,
    f"Attribution pattern found: {attribution_found}",
    weight=4
)

# ─────────────────────────────────────────────
# Final scoring
# ─────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total_checks = len(checks)
final_score = round((total_score / max_score) * 100, 2)
overall_passed = final_score >= 60.0 and \
    all(c["passed"] for c in checks if c["name"] in [
        "Phase 4: COMPARISON_REPORT.md exists and is substantive",
        "Phase 4: DECISION_RATIONALE.md exists and is substantive",
        "Phase 4: final/ directory contains runnable code",
        "Phase 2: Exactly 6 cross-evaluation reports exist",
    ])

result = {
    "passed": overall_passed,
    "score": final_score,
    "checks": checks
}
print(json.dumps(result, indent=2))