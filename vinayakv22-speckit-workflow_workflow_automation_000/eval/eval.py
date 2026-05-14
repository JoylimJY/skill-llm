import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ─── Locate the implementation session plan file ───────────────────────────
    # The agent should produce a file named "implementation_session_plan.md"
    # somewhere in the project. We search broadly.
    project_root = Path(workspace) / "projects" / "drone-fw" / "collision-avoidance"
    
    plan_files = list(Path(workspace).rglob("implementation_session_plan.md"))
    
    if not plan_files:
        add_check("file_exists", False, "implementation_session_plan.md not found anywhere in workspace")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    plan_file = plan_files[0]
    add_check("file_exists", True, f"Found at: {plan_file}")
    
    try:
        content = plan_file.read_text(encoding="utf-8")
    except Exception as e:
        add_check("file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("file_readable", True, f"File has {len(content)} characters")

    # ─── CHECK 1: Phase Detection ──────────────────────────────────────────────
    # Agent must correctly identify "Implementation" as the current phase.
    # The project has: .specify/ + constitution.md + spec.md + plan.md + tasks.md with NO [X] yet on feature tasks
    # → Tasks phase complete, Implementation in progress (T008 is [X])
    phase_detected = bool(
        re.search(r'\bimplement', content, re.IGNORECASE)
    )
    add_check(
        "phase_detection_implementation",
        phase_detected,
        "Document must identify current phase as 'Implementation' (tasks.md exists and is partially marked)" if not phase_detected else "Correctly identified Implementation phase"
    )

    # ─── CHECK 2: Correct feature identified ──────────────────────────────────
    # Must identify 'lidar-obstacle-detection' as the active feature (has tasks.md with incomplete tasks)
    # NOT 'gps-denied-navigation' (no tasks.md) NOT 'battery-monitor' (all done)
    feature_correct = bool(
        re.search(r'lidar.obstacle.detection|lidar_obstacle_detection|LiDAR Obstacle Detection|lidar obstacle detection', content, re.IGNORECASE)
    )
    add_check(
        "correct_active_feature",
        feature_correct,
        "Must identify 'lidar-obstacle-detection' as the active feature" if not feature_correct else "Correct feature identified"
    )

    # ─── CHECK 3: T008 skipped / already done ─────────────────────────────────
    # T008 is marked [X] in tasks.md — agent must NOT re-include it in any chunk
    t008_skipped = not bool(re.search(r'\bT008\b', content))
    # Allow mention if explicitly labeling it as already complete/skipped
    if not t008_skipped:
        # Check if T008 is mentioned but explicitly noted as done/skip
        t008_context = re.findall(r'.{0,50}T008.{0,80}', content, re.IGNORECASE)
        t008_skip_noted = any(re.search(r'already|done|complet|skip|\[X\]', ctx, re.IGNORECASE) for ctx in t008_context)
        t008_skipped = t008_skip_noted
    add_check(
        "t008_already_complete_handled",
        t008_skipped,
        "T008 is already marked [X] and must not appear as a pending task in any chunk" if not t008_skipped else "T008 correctly excluded from pending chunks"
    )

    # ─── CHECK 4: Chunking Rule — Simple tasks grouped 3-5 ────────────────────
    # Simple pending tasks: T001, T002, T003, T004, T005, T011, T013, T015
    # They should be grouped in batches of 3-5, not 1-2 and not all together.
    # We'll check that at least one chunk contains 3+ simple tasks together.
    
    # Find chunk sections - look for patterns like "Chunk 1", "Session 1", "Batch 1", "Group 1"
    chunk_pattern = re.findall(
        r'(?:chunk|session|batch|group|block)\s*\d+.*?(?=(?:chunk|session|batch|group|block)\s*\d+|\Z)',
        content,
        re.IGNORECASE | re.DOTALL
    )
    
    simple_tasks = ['T001', 'T002', 'T003', 'T004', 'T005', 'T011', 'T013', 'T015']
    complex_tasks = ['T006', 'T007', 'T009', 'T010', 'T012', 'T014']
    
    simple_chunking_ok = False
    complex_chunking_ok = False
    
    if chunk_pattern:
        for chunk in chunk_pattern:
            simple_in_chunk = sum(1 for t in simple_tasks if t in chunk)
            complex_in_chunk = sum(1 for t in complex_tasks if t in chunk)
            
            # A chunk with 3-5 simple tasks and no complex tasks → good simple grouping
            if 3 <= simple_in_chunk <= 5 and complex_in_chunk == 0:
                simple_chunking_ok = True
            
            # A chunk with 1-2 complex tasks → good complex grouping
            if 1 <= complex_in_chunk <= 2:
                complex_chunking_ok = True
    else:
        # Try alternative: look for task groupings in the text even without explicit chunk headers
        # Check that no single group has more than 5 tasks or mixes 6+ tasks together naively
        # We do a looser check: simple tasks appear in groups of 3-5
        task_groups = re.findall(r'((?:T\d{3}[,\s]+){2,}T\d{3})', content)
        for group in task_groups:
            tasks_in_group = re.findall(r'T\d{3}', group)
            simple_count = sum(1 for t in tasks_in_group if t in simple_tasks)
            complex_count = sum(1 for t in tasks_in_group if t in complex_tasks)
            if 3 <= simple_count <= 5 and complex_count == 0:
                simple_chunking_ok = True
            if 1 <= complex_count <= 2:
                complex_chunking_ok = True

    add_check(
        "simple_tasks_grouped_3_to_5",
        simple_chunking_ok,
        "Simple tasks must be grouped 3-5 per chunk (not 1-2, not all together)" if not simple_chunking_ok else "Simple tasks correctly grouped in batches of 3-5"
    )
    add_check(
        "complex_tasks_grouped_1_to_2",
        complex_chunking_ok,
        "Complex tasks must be grouped 1-2 per chunk (not more)" if not complex_chunking_ok else "Complex tasks correctly grouped in batches of 1-2"
    )

    # ─── CHECK 5: No over-grouping — complex tasks not lumped together ─────────
    # No single chunk should contain 3+ complex tasks
    no_overgroup = True
    if chunk_pattern:
        for chunk in chunk_pattern:
            complex_in_chunk = sum(1 for t in complex_tasks if t in chunk)
            if complex_in_chunk >= 3:
                no_overgroup = False
                break
    
    add_check(
        "no_over_grouping_complex",
        no_overgroup,
        "No single chunk should contain 3 or more complex tasks" if not no_overgroup else "No over-grouping detected"
    )

    # ─── CHECK 6: All pending tasks accounted for ──────────────────────────────
    # All 14 pending tasks (T001-T015 minus T008) should appear somewhere in the plan
    pending_tasks = ['T001', 'T002', 'T003', 'T004', 'T005', 'T006', 'T007',
                     'T009', 'T010', 'T011', 'T012', 'T013', 'T014', 'T015']
    missing_tasks = [t for t in pending_tasks if t not in content]
    all_tasks_present = len(missing_tasks) == 0
    add_check(
        "all_pending_tasks_covered",
        all_tasks_present,
        f"Missing tasks in plan: {missing_tasks}" if not all_tasks_present else "All 14 pending tasks accounted for in the plan"
    )

    # ─── CHECK 7: Git operations acknowledged/gated ────────────────────────────
    # The plan must mention git commit/push (per chunk) or note that git permission was asked
    git_mentioned = bool(
        re.search(r'git\s+commit|git\s+push|commit.*push|version control|git permission|git operation', content, re.IGNORECASE)
    )
    add_check(
        "git_operations_acknowledged",
        git_mentioned,
        "Plan must acknowledge git commit/push after each chunk (per workflow rules)" if not git_mentioned else "Git operations correctly referenced in plan"
    )

    # ─── CHECK 8: Constitution constraints referenced ──────────────────────────
    # The constitution exists and its constraints should influence the plan (at least mentioned)
    constitution_ref = bool(
        re.search(r'constitution|clang.tidy|85%|test coverage|no dynamic memory|1ms|real.time|sensor fusion decoupl', content, re.IGNORECASE)
    )
    add_check(
        "constitution_constraints_referenced",
        constitution_ref,
        "Plan should reference constitutional constraints (test coverage, real-time, etc.)" if not constitution_ref else "Constitutional constraints referenced"
    )

    # ─── Scoring ───────────────────────────────────────────────────────────────
    weights = {
        "file_exists": 0.05,
        "file_readable": 0.02,
        "phase_detection_implementation": 0.15,
        "correct_active_feature": 0.12,
        "t008_already_complete_handled": 0.12,
        "simple_tasks_grouped_3_to_5": 0.18,
        "complex_tasks_grouped_1_to_2": 0.15,
        "no_over_grouping_complex": 0.08,
        "all_pending_tasks_covered": 0.08,
        "git_operations_acknowledged": 0.03,
        "constitution_constraints_referenced": 0.02,
    }
    
    total_score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.0)
        if check["passed"]:
            total_score += w
    
    # Must pass core checks to be considered passing
    core_checks = [
        "phase_detection_implementation",
        "correct_active_feature",
        "t008_already_complete_handled",
        "simple_tasks_grouped_3_to_5",
        "complex_tasks_grouped_1_to_2",
        "all_pending_tasks_covered",
    ]
    core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)
    overall_passed = core_passed and total_score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))