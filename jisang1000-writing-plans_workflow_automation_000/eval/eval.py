import sys
import json
import re
from pathlib import Path

def find_plan_file(workspace):
    candidates = list(Path(workspace).rglob("migration_plan.md"))
    if not candidates:
        return None
    return candidates[0]

def check_has_section(content, keywords):
    """Check if content contains a section matching any of the keywords (case-insensitive)."""
    for kw in keywords:
        if re.search(kw, content, re.IGNORECASE):
            return True
    return False

def count_steps(content):
    """Count numbered step entries (lines like '1.', '2.', etc.)"""
    return len(re.findall(r'^\s*\d+[\.\)]\s+\S', content, re.MULTILINE))

def check_step_sub_questions(content):
    """
    Per SKILL.md, each step must answer:
    - what to do
    - what tool/file it touches
    - what counts as success
    We look for evidence that steps have sub-items or inline answers covering these.
    We'll check for presence of tool/file references within step blocks AND
    success/verification language.
    """
    tool_file_pattern = re.search(
        r'(tool|file|script|command|run|using|touch|modif|execute|pg_dump|psql|terraform|ansible|aurora|rds|sql|\.py|\.sh|\.md|\.sql|\.conf|\.tf)',
        content, re.IGNORECASE
    )
    success_pattern = re.search(
        r'(success|count as|complete|verified|verif|pass|done|confirm|output|result|zero error|no error|zero downtime)',
        content, re.IGNORECASE
    )
    return bool(tool_file_pattern), bool(success_pattern)

def check_heavyweight_indicator(content):
    """
    Per SKILL.md, heavyweight plans are for: many files/tools, external systems,
    long-running tasks, sub-agents. The scenario has all four.
    The plan should explicitly indicate heavyweight or list multiple sub-sections/agents.
    """
    hw_pattern = re.search(
        r'(heavyweight|heavy.?weight|sub.?agent|sub agent|DBA|external system|BigQuery|analytics pipeline|multiple.*database|across.*team)',
        content, re.IGNORECASE
    )
    return bool(hw_pattern)

def check_reporting_section(content):
    """
    Per SKILL.md, reporting must summarize:
    1. planned scope
    2. what completed
    3. what changed during execution
    4. what remains
    """
    has_scope = bool(re.search(r'(planned scope|scope)', content, re.IGNORECASE))
    has_completed = bool(re.search(r'(complet|what.*complet|done|finished)', content, re.IGNORECASE))
    has_changed = bool(re.search(r'(change|changed|assumption|deviat|actual|update|revised)', content, re.IGNORECASE))
    has_remains = bool(re.search(r'(remain|remaining|next step|outstanding|todo|to do|not.*done|incomplete)', content, re.IGNORECASE))
    return has_scope, has_completed, has_changed, has_remains

def main():
    workspace = sys.argv[1]
    checks = []
    total_score = 0.0
    weights = {}

    # --- Find file ---
    plan_path = find_plan_file(workspace)
    file_found = plan_path is not None
    checks.append({
        "name": "migration_plan.md exists",
        "passed": file_found,
        "detail": f"Found at {plan_path}" if file_found else "migration_plan.md not found anywhere in workspace"
    })

    if not file_found:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result))
        return

    try:
        content = plan_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # --- Check 1: Goal section (weight: 0.10) ---
    has_goal = check_has_section(content, [r'\bgoal\b', r'\bobjective\b', r'\bpurpose\b'])
    checks.append({
        "name": "plan_has_goal_section",
        "passed": has_goal,
        "detail": "Plan contains a 'Goal' or 'Objective' section" if has_goal else "Missing Goal/Objective section (required by plan shape)"
    })
    if has_goal: total_score += 0.10

    # --- Check 2: Constraints section (weight: 0.10) ---
    has_constraints = check_has_section(content, [r'\bconstraint', r'\blimitation', r'\brequirement'])
    checks.append({
        "name": "plan_has_constraints_section",
        "passed": has_constraints,
        "detail": "Plan contains a 'Constraints' or 'Requirements' section" if has_constraints else "Missing Constraints section (required by plan shape)"
    })
    if has_constraints: total_score += 0.10

    # --- Check 3: Ordered Steps section (weight: 0.15) ---
    has_steps_section = check_has_section(content, [r'\bstep', r'\bordered step', r'\bexecution step', r'\bphase'])
    step_count = count_steps(content)
    has_enough_steps = step_count >= 4
    checks.append({
        "name": "plan_has_ordered_steps_section",
        "passed": has_steps_section and has_enough_steps,
        "detail": f"Found steps section: {has_steps_section}, numbered steps found: {step_count} (need >=4)"
    })
    if has_steps_section and has_enough_steps: total_score += 0.15

    # --- Check 4: Verification Points section (weight: 0.10) ---
    has_verification = check_has_section(content, [
        r'\bverif', r'\bcheck point', r'\bcheckpoint', r'\bvalidat', r'\bsmoke test', r'\btest.*point'
    ])
    checks.append({
        "name": "plan_has_verification_points",
        "passed": has_verification,
        "detail": "Plan contains verification/validation points" if has_verification else "Missing Verification Points section (required by plan shape)"
    })
    if has_verification: total_score += 0.10

    # --- Check 5: Possible Blockers section (weight: 0.10) ---
    has_blockers = check_has_section(content, [r'\bblocker', r'\brisk', r'\bobstacle', r'\bdependenc', r'\bblocking'])
    checks.append({
        "name": "plan_has_possible_blockers",
        "passed": has_blockers,
        "detail": "Plan contains a Blockers/Risks section" if has_blockers else "Missing Possible Blockers section (required by plan shape)"
    })
    if has_blockers: total_score += 0.10

    # --- Check 6: Step sub-questions (tool/file + success) (weight: 0.15) ---
    has_tool_ref, has_success_ref = check_step_sub_questions(content)
    step_detail_ok = has_tool_ref and has_success_ref
    checks.append({
        "name": "steps_answer_tool_and_success_subquestions",
        "passed": step_detail_ok,
        "detail": f"Steps reference tools/files: {has_tool_ref}, Steps define success criteria: {has_success_ref}"
    })
    if step_detail_ok: total_score += 0.15

    # --- Check 7: Heavyweight indicator (weight: 0.10) ---
    is_heavyweight = check_heavyweight_indicator(content)
    checks.append({
        "name": "plan_classified_as_heavyweight",
        "passed": is_heavyweight,
        "detail": "Plan acknowledges heavyweight scope (sub-agents, external systems, DBA, multi-db)" if is_heavyweight else "Plan does not acknowledge heavyweight classification despite scope (many files, external systems, sub-agents implied)"
    })
    if is_heavyweight: total_score += 0.10

    # --- Check 8: Reporting section with 4 required fields (weight: 0.10) ---
    has_scope_r, has_completed_r, has_changed_r, has_remains_r = check_reporting_section(content)
    reporting_fields = sum([has_scope_r, has_completed_r, has_changed_r, has_remains_r])
    reporting_ok = reporting_fields >= 3  # at least 3 of 4 fields
    checks.append({
        "name": "plan_has_reporting_section_with_required_fields",
        "passed": reporting_ok,
        "detail": f"Reporting fields present - scope:{has_scope_r}, completed:{has_completed_r}, changed:{has_changed_r}, remains:{has_remains_r} ({reporting_fields}/4 found, need >=3)"
    })
    if reporting_ok: total_score += 0.10

    # --- Check 9: Domain-specific content (migration context) (weight: 0.10) ---
    has_domain = bool(re.search(
        r'(Aurora|PostgreSQL|shipments_db|inventory_db|orders_db|BigQuery|microservice|FK|foreign key|DNS|cutover|zero.?downtime|maintenance window)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "plan_addresses_actual_migration_scenario",
        "passed": has_domain,
        "detail": "Plan references actual migration details (Aurora, db names, BigQuery, FK, etc.)" if has_domain else "Plan is too generic; doesn't address the specific migration scenario"
    })
    if has_domain: total_score += 0.10

    # --- Final ---
    total_score = round(min(total_score, 1.0), 4)
    passed = total_score >= 0.75

    result = {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()