import sys
import os
import json
import re
import subprocess
from pathlib import Path

workspace = sys.argv[1]
project_dir = Path(workspace) / "iot-monitor"

checks = []
total_score = 0.0
max_score = 10.0

def make_check(name, passed, detail, weight=1.0):
    return {"name": name, "passed": passed, "detail": detail, "_weight": weight}

# ─── Helper ────────────────────────────────────────────────────────────────
def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

# ═══════════════════════════════════════════════════════════════════════════
# CHECK GROUP 1: Phase 1 — specs/ directory and topic files
# ═══════════════════════════════════════════════════════════════════════════

# 1.1 specs/ directory exists
specs_dir = project_dir / "specs"
specs_exists = specs_dir.is_dir()
checks.append(make_check(
    "specs_directory_exists",
    specs_exists,
    f"specs/ directory found at {specs_dir}" if specs_exists else f"specs/ directory missing at {specs_dir}",
    weight=0.5
))

# 1.2 At least 3 topic spec files exist (raw req has >= 4 distinct concerns)
spec_files = list(specs_dir.glob("*.md")) if specs_exists else []
# Filter out any README or non-topic files
topic_files = [f for f in spec_files if f.name.lower() not in ("readme.md",)]
enough_topics = len(topic_files) >= 3
checks.append(make_check(
    "at_least_3_topic_specs",
    enough_topics,
    f"Found {len(topic_files)} topic spec files: {[f.name for f in topic_files]}",
    weight=1.0
))

# 1.3 Each spec contains the three required sections
required_sections = ["需求描述", "验收标准", "边界情况"]
# Also accept English equivalents
required_sections_en = ["requirement", "acceptance criteria", "edge case"]

specs_well_formed = 0
specs_details = []
for tf in topic_files:
    content = read_file(tf)
    if content is None:
        specs_details.append(f"{tf.name}: unreadable")
        continue
    content_lower = content.lower()
    has_all = all(
        (sec in content) or (sec_en in content_lower)
        for sec, sec_en in zip(required_sections, required_sections_en)
    )
    if has_all:
        specs_well_formed += 1
    else:
        missing = [sec for sec, sec_en in zip(required_sections, required_sections_en)
                   if sec not in content and sec_en not in content_lower]
        specs_details.append(f"{tf.name}: missing sections {missing}")

all_specs_well_formed = (specs_well_formed == len(topic_files)) and len(topic_files) >= 3
checks.append(make_check(
    "all_specs_have_required_sections",
    all_specs_well_formed,
    f"{specs_well_formed}/{len(topic_files)} specs contain 需求描述+验收标准+边界情况. Issues: {specs_details}",
    weight=1.5
))

# 1.4 Topics are atomic — "one sentence, no and" test
# Heuristic: spec file names should not suggest compound topics
# More importantly, we check the content is focused (no "and" connecting disparate concerns in the title/first heading)
compound_violations = []
for tf in topic_files:
    content = read_file(tf) or ""
    lines = content.strip().split("\n")
    first_heading = next((l for l in lines if l.startswith("#")), "")
    # A compound topic often has "and" or "&" or "+" in the heading
    if re.search(r'\band\b|＆|&|\+and\+', first_heading, re.IGNORECASE):
        compound_violations.append(tf.name)

topics_are_atomic = len(compound_violations) == 0
checks.append(make_check(
    "topics_are_atomic_no_compound_headings",
    topics_are_atomic,
    f"Compound topic headings (violate 'one sentence no and' rule): {compound_violations}" if compound_violations else "All topic headings appear atomic.",
    weight=0.5
))

# ═══════════════════════════════════════════════════════════════════════════
# CHECK GROUP 2: Phase 2 — IMPLEMENTATION_PLAN.md
# ═══════════════════════════════════════════════════════════════════════════

plan_path = project_dir / "IMPLEMENTATION_PLAN.md"
plan_content = read_file(plan_path)
plan_exists = plan_content is not None

checks.append(make_check(
    "implementation_plan_exists",
    plan_exists,
    f"IMPLEMENTATION_PLAN.md found" if plan_exists else "IMPLEMENTATION_PLAN.md missing",
    weight=0.5
))

if plan_content:
    # 2.2 Each task has a priority label (P1/P2/P3 or 高/中/低 or high/medium/low)
    priority_pattern = re.compile(
        r'(P[123]|高优|中优|低优|high|medium|low|priority\s*[123])',
        re.IGNORECASE
    )
    priority_matches = priority_pattern.findall(plan_content)
    has_priorities = len(priority_matches) >= 2  # at least 2 tasks with priority
    checks.append(make_check(
        "plan_has_priority_labels",
        has_priorities,
        f"Found {len(priority_matches)} priority labels in plan: {priority_matches[:10]}",
        weight=1.0
    ))

    # 2.3 Plan covers all specs (each spec filename or topic name referenced in plan)
    coverage_ok = True
    uncovered = []
    for tf in topic_files:
        topic_name = tf.stem  # e.g., "topic-alert-thresholds"
        # Accept topic stem or any reasonable abbreviation
        # Check if the topic stem words appear in the plan
        words = re.split(r'[-_]', topic_name)
        meaningful_words = [w for w in words if w.lower() not in ("topic", "spec", "feature")]
        if meaningful_words:
            found = any(w.lower() in plan_content.lower() for w in meaningful_words)
            if not found:
                coverage_ok = False
                uncovered.append(tf.name)

    checks.append(make_check(
        "plan_covers_all_specs",
        coverage_ok,
        f"Uncovered specs in plan: {uncovered}" if not coverage_ok else "All spec topics referenced in plan.",
        weight=1.0
    ))

    # 2.4 Plan has status fields (todo/done markers)
    status_pattern = re.compile(r'(todo|done|✅|☑|❌|\[ \]|\[x\])', re.IGNORECASE)
    status_matches = status_pattern.findall(plan_content)
    has_status = len(status_matches) >= 2
    checks.append(make_check(
        "plan_has_status_fields",
        has_status,
        f"Found {len(status_matches)} status markers: {status_matches[:10]}",
        weight=0.5
    ))

    # 2.5 Gap analysis evidence: plan should reference existing codebase items
    gap_indicators = ["collector", "storage", "api", "notifier", "stub", "in-memory", "gap", "missing", "exists"]
    gap_evidence = [g for g in gap_indicators if g.lower() in plan_content.lower()]
    has_gap_analysis = len(gap_evidence) >= 2
    checks.append(make_check(
        "plan_shows_gap_analysis",
        has_gap_analysis,
        f"Gap analysis indicators found: {gap_evidence}",
        weight=1.0
    ))
else:
    for name in ["plan_has_priority_labels", "plan_covers_all_specs", "plan_has_status_fields", "plan_shows_gap_analysis"]:
        checks.append(make_check(name, False, "IMPLEMENTATION_PLAN.md missing — skipped", weight=1.0 if name != "plan_has_status_fields" else 0.5))

# ═══════════════════════════════════════════════════════════════════════════
# CHECK GROUP 3: Phase 3 — Execution evidence
# ═══════════════════════════════════════════════════════════════════════════

# 3.1 At least one task marked done in the plan
plan_has_done = False
done_count = 0
if plan_content:
    done_pattern = re.compile(r'(done|✅|\[x\])', re.IGNORECASE)
    done_matches = done_pattern.findall(plan_content)
    done_count = len(done_matches)
    plan_has_done = done_count >= 1

checks.append(make_check(
    "plan_has_at_least_one_done_task",
    plan_has_done,
    f"Found {done_count} done markers in plan.",
    weight=1.0
))

# 3.2 Git commits exist beyond the initial snapshot
git_log = None
try:
    result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=str(project_dir),
        capture_output=True, text=True, timeout=10
    )
    git_log = result.stdout.strip()
except Exception as e:
    git_log = None

commit_lines = git_log.split("\n") if git_log else []
commit_lines = [l for l in commit_lines if l.strip()]
# Initial commit was "chore: initial codebase snapshot"
agent_commits = [l for l in commit_lines if "initial codebase snapshot" not in l]
has_agent_commits = len(agent_commits) >= 1

checks.append(make_check(
    "git_commits_from_execution",
    has_agent_commits,
    f"Agent commits found: {agent_commits[:5]}" if agent_commits else "No agent commits found beyond initial snapshot.",
    weight=1.0
))

# 3.3 Some implementation artifact was created/modified (new file in src/ or tests/)
new_files = []
try:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1", "HEAD"] if len(commit_lines) >= 2 else ["git", "diff", "--name-only", "HEAD"],
        cwd=str(project_dir),
        capture_output=True, text=True, timeout=10
    )
    new_files = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
except Exception:
    pass

# Also check if any new source files exist that weren't in original setup
# Original src/ files: collector.py, storage.py, api.py, __init__.py
original_src = {"collector.py", "storage.py", "api.py", "__init__.py"}
current_src = set(f.name for f in (project_dir / "src").glob("*.py")) if (project_dir / "src").is_dir() else set()
new_src_files = current_src - original_src

implementation_exists = len(new_src_files) > 0 or len(new_files) > 0
checks.append(make_check(
    "implementation_artifact_created",
    implementation_exists,
    f"New src files: {new_src_files}. Git changed files: {new_files[:5]}",
    weight=1.0
))

# ═══════════════════════════════════════════════════════════════════════════
# SCORING
# ═══════════════════════════════════════════════════════════════════════════

total_weight = sum(c["_weight"] for c in checks)
earned_weight = sum(c["_weight"] for c in checks if c["passed"])
score = round((earned_weight / total_weight) * 10.0, 2) if total_weight > 0 else 0.0

# Clean output (remove internal _weight key)
output_checks = [{"name": c["name"], "passed": c["passed"], "detail": c["detail"]} for c in checks]
overall_passed = score >= 7.0

result = {
    "passed": overall_passed,
    "score": score,
    "checks": output_checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))