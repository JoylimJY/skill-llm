import sys
import json
import re
from pathlib import Path

def find_files_by_name(workspace, filename):
    return list(Path(workspace).rglob(filename))

def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def run_eval(workspace):
    checks = []
    workspace = Path(workspace)

    # -----------------------------------------------------------------------
    # CHECK 1: ongoing-tasks.md exists at the EXACT required path
    # -----------------------------------------------------------------------
    ongoing_path = workspace / "memory" / "tasks" / "ongoing-tasks.md"
    ongoing_exists = ongoing_path.exists()
    checks.append({
        "name": "ongoing-tasks.md exists at memory/tasks/ongoing-tasks.md",
        "passed": ongoing_exists,
        "detail": f"File found at {ongoing_path}" if ongoing_exists else f"File NOT found at {ongoing_path}. Also checked rglob: {find_files_by_name(workspace, 'ongoing-tasks.md')}"
    })

    ongoing_text = ""
    if ongoing_exists:
        try:
            ongoing_text = load_text(ongoing_path)
        except Exception as e:
            checks.append({"name": "ongoing-tasks.md readable", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 2: ongoing-tasks.md contains a health status emoji (🟢, 🟡, or 🔴)
    # -----------------------------------------------------------------------
    health_emojis = ["🟢", "🟡", "🔴"]
    has_health_emoji = any(emoji in ongoing_text for emoji in health_emojis)
    checks.append({
        "name": "ongoing-tasks.md contains a health status emoji (🟢/🟡/🔴)",
        "passed": has_health_emoji,
        "detail": f"Health emoji found in ongoing-tasks.md" if has_health_emoji else "No health status emoji (🟢/🟡/🔴) found in ongoing-tasks.md"
    })

    # -----------------------------------------------------------------------
    # CHECK 3: ongoing-tasks.md mentions task type 'infinite' or 'Infinite'
    # -----------------------------------------------------------------------
    has_infinite_type = bool(re.search(r'\binfinite\b', ongoing_text, re.IGNORECASE))
    checks.append({
        "name": "ongoing-tasks.md identifies task as 'infinite' type",
        "passed": has_infinite_type,
        "detail": "Found 'infinite' type designation" if has_infinite_type else "No 'infinite' type designation found — task type not correctly classified"
    })

    # -----------------------------------------------------------------------
    # CHECK 4: ongoing-tasks.md contains a schedule (interval/frequency)
    # -----------------------------------------------------------------------
    has_schedule = bool(re.search(
        r'(schedule|every\s+\d+|interval|frequency|hour|minute|daily|weekly)',
        ongoing_text, re.IGNORECASE
    ))
    checks.append({
        "name": "ongoing-tasks.md contains scheduling information",
        "passed": has_schedule,
        "detail": "Schedule/interval info found" if has_schedule else "No schedule or interval information found in ongoing-tasks.md"
    })

    # -----------------------------------------------------------------------
    # CHECK 5: ongoing-tasks.md references log monitoring / e-commerce context
    # -----------------------------------------------------------------------
    has_monitoring_context = bool(re.search(
        r'(log|monitor|anomal|error|payment|ecommerce|e-commerce|traffic|alert)',
        ongoing_text, re.IGNORECASE
    ))
    checks.append({
        "name": "ongoing-tasks.md references log monitoring / e-commerce domain",
        "passed": has_monitoring_context,
        "detail": "Domain context found" if has_monitoring_context else "No log monitoring or e-commerce domain context found in ongoing-tasks.md"
    })

    # -----------------------------------------------------------------------
    # CHECK 6: ongoing-tasks.md contains checkpoint(s)
    # -----------------------------------------------------------------------
    has_checkpoints = bool(re.search(r'checkpoint', ongoing_text, re.IGNORECASE))
    checks.append({
        "name": "ongoing-tasks.md contains at least one 'checkpoint'",
        "passed": has_checkpoints,
        "detail": "Checkpoint(s) found in ongoing-tasks.md" if has_checkpoints else "No 'checkpoint' keyword found — checkpoints are required per the clawlist workflow"
    })

    # -----------------------------------------------------------------------
    # CHECK 7: A brainstorming phase artifact exists (any file with 'brainstorm' in name or containing brainstorm content)
    # -----------------------------------------------------------------------
    brainstorm_files = list(workspace.rglob('*brainstorm*'))
    brainstorm_files += list(workspace.rglob('*brainstorming*'))
    # Also check for a file with brainstorming-phase content
    brainstorm_content_found = False
    brainstorm_detail = ""
    if brainstorm_files:
        brainstorm_content_found = True
        brainstorm_detail = f"Found brainstorming artifact(s): {[str(f) for f in brainstorm_files[:3]]}"
    else:
        # Search all .md files for brainstorming phase markers
        for mdfile in workspace.rglob("*.md"):
            try:
                content = load_text(mdfile)
                if re.search(r'brainstorm', content, re.IGNORECASE) and str(mdfile) != str(ongoing_path):
                    brainstorm_content_found = True
                    brainstorm_detail = f"Brainstorming content found in: {mdfile}"
                    break
            except:
                pass
        if not brainstorm_content_found:
            brainstorm_detail = "No brainstorming artifact or content found anywhere in workspace"

    checks.append({
        "name": "Brainstorming phase artifact exists",
        "passed": brainstorm_content_found,
        "detail": brainstorm_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 8: A write-plan / plan artifact exists with checkpoints
    # -----------------------------------------------------------------------
    plan_files = list(workspace.rglob('*plan*'))
    plan_with_checkpoints = False
    plan_detail = ""
    for pf in plan_files:
        if pf.is_file() and pf.suffix in ['.md', '.txt', '.json', '.yaml']:
            try:
                content = load_text(pf)
                if re.search(r'checkpoint', content, re.IGNORECASE):
                    plan_with_checkpoints = True
                    plan_detail = f"Plan artifact with checkpoints found: {pf}"
                    break
            except:
                pass
    if not plan_with_checkpoints:
        # Also check ongoing-tasks itself (it may embed the plan)
        if has_checkpoints and has_schedule:
            plan_with_checkpoints = True
            plan_detail = "Plan-level detail (checkpoints + schedule) found within ongoing-tasks.md itself"
        else:
            plan_detail = f"No write-plan artifact with checkpoints found. Scanned: {[str(f) for f in plan_files[:5]]}"

    checks.append({
        "name": "Write-plan artifact with checkpoints exists",
        "passed": plan_with_checkpoints,
        "detail": plan_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 9: ongoing-tasks.md is NOT the old deprecated wrong-location file
    #          (i.e., it was genuinely created new, not just renamed)
    # -----------------------------------------------------------------------
    wrong_location = workspace / "memory" / "ongoing_tasks_old.txt"
    wrong_still_exists = wrong_location.exists()
    # The correct file must have substantive content (>100 chars)
    is_substantive = len(ongoing_text.strip()) > 100 if ongoing_exists else False
    checks.append({
        "name": "ongoing-tasks.md is substantive (not a stub, >100 chars)",
        "passed": is_substantive,
        "detail": f"Content length: {len(ongoing_text.strip())} chars" if ongoing_exists else "File missing"
    })

    # -----------------------------------------------------------------------
    # SCORE
    # -----------------------------------------------------------------------
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))