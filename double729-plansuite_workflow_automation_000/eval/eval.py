import sys
import json
import re
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── Helper: read file safely ──────────────────────────────────────────────
    def read_file(path):
        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # FILE 1: task_plan.md
    # ═══════════════════════════════════════════════════════════════════════════
    task_plan_path = workspace / "task_plan.md"
    task_plan_content = read_file(task_plan_path)

    # CHECK 1: task_plan.md exists
    if task_plan_content is None:
        add_check("task_plan.md exists", False, "File not found at workspace/task_plan.md")
    else:
        add_check("task_plan.md exists", True, f"File found, {len(task_plan_content)} chars")

        # CHECK 2: STATUS: FINALIZED at the TOP of the file
        # Must appear within the first 10 non-empty lines
        lines = task_plan_content.splitlines()
        non_empty_lines = [l for l in lines if l.strip()]
        top_section = "\n".join(non_empty_lines[:10])
        finalized_at_top = bool(re.search(r'STATUS\s*:\s*FINALIZED', top_section, re.IGNORECASE))
        add_check(
            "STATUS: FINALIZED at top of task_plan.md",
            finalized_at_top,
            f"Top 10 non-empty lines: {repr(top_section[:300])}"
        )

        # CHECK 3: Timestamp present near the STATUS line
        # Find the STATUS line index and look within ±3 lines
        status_line_idx = None
        for i, line in enumerate(lines):
            if re.search(r'STATUS\s*:\s*FINALIZED', line, re.IGNORECASE):
                status_line_idx = i
                break
        
        timestamp_found = False
        if status_line_idx is not None:
            window_start = max(0, status_line_idx - 2)
            window_end = min(len(lines), status_line_idx + 5)
            window_text = "\n".join(lines[window_start:window_end])
            # Look for a timestamp pattern: date or time digits
            timestamp_found = bool(re.search(
                r'\d{4}[-/]\d{2}[-/]\d{2}|\d{2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}',
                window_text
            ))
        add_check(
            "Timestamp present near STATUS: FINALIZED",
            timestamp_found,
            f"Status line index: {status_line_idx}; timestamp pattern found: {timestamp_found}"
        )

        # CHECK 4: Plan has Background/Objective section
        has_background = bool(re.search(r'(background|objective|目标|背景)', task_plan_content, re.IGNORECASE))
        add_check("task_plan.md has Background/Objective section", has_background,
                  "Searched for 'background', 'objective', '背景', '目标'")

        # CHECK 5: Plan has Scope section
        has_scope = bool(re.search(r'(scope|范围)', task_plan_content, re.IGNORECASE))
        add_check("task_plan.md has Scope section", has_scope,
                  "Searched for 'scope', '范围'")

        # CHECK 6: Plan has Risks & Rollback section
        has_risks = bool(re.search(r'(risk|rollback|风险|回滚)', task_plan_content, re.IGNORECASE))
        add_check("task_plan.md has Risks & Rollback section", has_risks,
                  "Searched for 'risk', 'rollback', '风险', '回滚'")

        # CHECK 7: At least 2 milestones/sub-plans defined
        milestone_matches = re.findall(
            r'(milestone|sub.?plan|子计划|阶段|phase|step)\s*\d+',
            task_plan_content, re.IGNORECASE
        )
        # Also count markdown headers that look like numbered sub-plans
        header_matches = re.findall(r'^#+\s*(?:milestone|phase|step|m\d|sub.?plan|\d+[\).])', 
                                     task_plan_content, re.IGNORECASE | re.MULTILINE)
        total_milestone_refs = len(set(milestone_matches)) + len(header_matches)
        has_multiple_milestones = total_milestone_refs >= 2 or len(milestone_matches) >= 2 or len(header_matches) >= 2
        add_check(
            "task_plan.md has at least 2 milestones/sub-plans",
            has_multiple_milestones,
            f"Milestone keyword matches: {len(milestone_matches)}, Header matches: {len(header_matches)}"
        )

        # CHECK 8: Each milestone has acceptance criteria
        acceptance_criteria_count = len(re.findall(
            r'(acceptance.criteria|验收标准|acceptance criteria|dod|definition.of.done)',
            task_plan_content, re.IGNORECASE
        ))
        has_acceptance_criteria = acceptance_criteria_count >= 1
        add_check(
            "task_plan.md milestones include acceptance criteria",
            has_acceptance_criteria,
            f"Found {acceptance_criteria_count} acceptance criteria references"
        )

        # CHECK 9: Milestones reference inputs/outputs
        has_inputs = bool(re.search(r'\b(input|output|输入|输出)\b', task_plan_content, re.IGNORECASE))
        add_check(
            "task_plan.md milestones include input/output specifications",
            has_inputs,
            "Searched for 'input', 'output', '输入', '输出'"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # FILE 2: progress.md
    # ═══════════════════════════════════════════════════════════════════════════
    progress_path = workspace / "progress.md"
    progress_content = read_file(progress_path)

    if progress_content is None:
        add_check("progress.md exists", False, "File not found at workspace/progress.md")
    else:
        add_check("progress.md exists", True, f"File found, {len(progress_content)} chars")

        # CHECK 10: progress.md has a 'Next' field populated (freeze phase requirement)
        next_section = re.search(r'##\s*next\b(.+?)(?=##|\Z)', progress_content, re.IGNORECASE | re.DOTALL)
        next_populated = False
        if next_section:
            next_body = next_section.group(1).strip()
            # Must have actual content (not just whitespace or template placeholder)
            next_populated = len(next_body) > 5 and not re.fullmatch(r'[\s\-_]*', next_body)
        add_check(
            "progress.md 'Next' section is populated with sub-plan to execute",
            next_populated,
            f"Next section body: {repr(next_section.group(1).strip()[:200]) if next_section else 'section not found'}"
        )

        # CHECK 11: progress.md has a 'Done' section with at least one completed item
        done_section = re.search(r'##\s*done\b(.+?)(?=##|\Z)', progress_content, re.IGNORECASE | re.DOTALL)
        done_populated = False
        if done_section:
            done_body = done_section.group(1).strip()
            done_populated = len(done_body) > 5 and not re.fullmatch(r'[\s\-_]*', done_body)
        add_check(
            "progress.md 'Done' section records at least one completed milestone",
            done_populated,
            f"Done section body: {repr(done_section.group(1).strip()[:200]) if done_section else 'section not found'}"
        )

        # CHECK 12: progress.md has a 'Blockers' section
        has_blockers_section = bool(re.search(r'##\s*blocker', progress_content, re.IGNORECASE))
        add_check(
            "progress.md has 'Blockers' section",
            has_blockers_section,
            "Searched for '## Blockers' or similar"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # FILE 3: findings.md
    # ═══════════════════════════════════════════════════════════════════════════
    findings_path = workspace / "findings.md"
    findings_content = read_file(findings_path)

    if findings_content is None:
        add_check("findings.md exists", False, "File not found at workspace/findings.md")
    else:
        add_check("findings.md exists", True, f"File found, {len(findings_content)} chars")

        # CHECK 13: findings.md contains verification commands (shell/SQL commands)
        has_verification_commands = bool(re.search(
            r'(verification.command|verify|验证|check|SELECT|psql|python|bash|sh\b|\.py\b|\.sh\b|`[^`]+`)',
            findings_content, re.IGNORECASE
        ))
        add_check(
            "findings.md contains verification commands",
            has_verification_commands,
            "Searched for verification commands, SQL, shell commands, or code blocks"
        )

        # CHECK 14: findings.md contains rollback steps
        has_rollback = bool(re.search(
            r'(rollback|roll.back|回滚|undo|revert|restore)',
            findings_content, re.IGNORECASE
        ))
        add_check(
            "findings.md contains rollback steps",
            has_rollback,
            "Searched for 'rollback', 'roll back', '回滚', 'undo', 'revert', 'restore'"
        )

        # CHECK 15: findings.md contains key decisions or pitfalls
        has_decisions = bool(re.search(
            r'(decision|decided|pitfall|issue|finding|坑|决策|discovery|discovered|key)',
            findings_content, re.IGNORECASE
        ))
        add_check(
            "findings.md contains key decisions or pitfalls",
            has_decisions,
            "Searched for 'decision', 'pitfall', 'issue', 'finding', '坑', '决策'"
        )

        # CHECK 16: findings.md references the specific migration domain (database/schema/migration)
        has_domain_relevance = bool(re.search(
            r'(migration|schema|database|transaction|account|ledger|postgres|pg|sql|uuid|cents|amount)',
            findings_content, re.IGNORECASE
        ))
        add_check(
            "findings.md is relevant to the migration project domain",
            has_domain_relevance,
            "Searched for migration/database domain-specific terms"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # CROSS-FILE CHECK: task_plan.md was NOT in DRAFT state at end
    # ═══════════════════════════════════════════════════════════════════════════
    if task_plan_content is not None:
        is_draft = bool(re.search(r'STATUS\s*:\s*DRAFT', task_plan_content, re.IGNORECASE))
        # FINALIZED is required; DRAFT means it was reverted (acceptable only if a blocking issue was found AND properly documented in findings)
        if is_draft and findings_content is not None:
            # If DRAFT, findings must have a change proposal explaining why
            has_change_proposal = bool(re.search(
                r'(change.proposal|change proposal|变更|plan.change|revised|revision|revert.plan)',
                findings_content, re.IGNORECASE
            ))
            add_check(
                "If STATUS is DRAFT, change proposal documented in findings.md",
                has_change_proposal,
                "Plan reverted to DRAFT — change proposal must exist in findings.md per workflow rule §4"
            )
        elif not is_draft and task_plan_content is not None:
            add_check(
                "STATUS remains FINALIZED (no unilateral plan change without documentation)",
                finalized_at_top if 'finalized_at_top' in dir() else False,
                "Plan was FINALIZED and not rolled back to DRAFT without justification"
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # SCORING
    # ═══════════════════════════════════════════════════════════════════════════
    passed_checks = [c for c in checks if c["passed"]]
    total_checks = len(checks)
    score = len(passed_checks) / total_checks if total_checks > 0 else 0.0

    # Overall pass: must pass at least 80% of checks, and the two most critical checks must pass
    critical_checks = [
        "task_plan.md exists",
        "STATUS: FINALIZED at top of task_plan.md",
        "progress.md exists",
        "progress.md 'Next' section is populated with sub-plan to execute",
        "findings.md exists",
        "findings.md contains rollback steps",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    overall_passed = (score >= 0.75) and critical_passed

    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)