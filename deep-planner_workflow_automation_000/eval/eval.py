import sys
import json
import re
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── Locate any new .todolist file created by the agent ───────────────────────
    todolist_dir = workspace / ".todolist"

    # Find all .md files in .todolist/ except the pre-existing ones
    PREEXISTING = {
        "20250108-competitive-pricing-research.md",
        "20241203-onboarding-content-audit.md",
    }

    try:
        all_todolist_files = [
            f for f in todolist_dir.glob("*.md")
            if f.name not in PREEXISTING
        ]
    except Exception as e:
        all_todolist_files = []

    # ── CHECK 1: Agent created a new .todolist file ───────────────────────────────
    if not all_todolist_files:
        check("new_todolist_file_created", False,
              "No new .todolist file found. Agent must create a new plan file in .todolist/")
        # Return early since all subsequent checks depend on this
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    # Use the first (or only) new file
    new_file = all_todolist_files[0]
    try:
        content = new_file.read_text(encoding="utf-8")
    except Exception as e:
        check("new_todolist_file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    check("new_todolist_file_created", True, f"Found new todolist file: {new_file.name}")

    # ── CHECK 2: Filename follows YYYYMMDD-{task-name}.md convention ─────────────
    filename = new_file.name
    filename_pattern = re.match(r'^\d{8}-.+\.md$', filename)
    date_part = filename[:8] if len(filename) >= 8 else ""
    date_valid = False
    try:
        datetime.strptime(date_part, "%Y%m%d")
        date_valid = True
    except ValueError:
        pass

    fname_ok = bool(filename_pattern) and date_valid
    check("filename_convention_YYYYMMDD", fname_ok,
          f"Filename '{filename}' {'matches' if fname_ok else 'does NOT match'} YYYYMMDD-{{task-name}}.md convention")

    # ── CHECK 3: File contains required top-level sections ────────────────────────
    required_sections = ["## Goal", "## TodoList", "## Assumptions & Confirmations", "## Progress"]
    missing_sections = [s for s in required_sections if s not in content]
    sections_ok = len(missing_sections) == 0
    check("required_sections_present", sections_ok,
          f"Missing sections: {missing_sections}" if missing_sections else "All required sections present")

    # ── CHECK 4: Status field is present and set to 'completed' ──────────────────
    status_match = re.search(r'Status:\s*(in-progress|completed)', content)
    status_ok = False
    status_detail = "No 'Status:' field found"
    if status_match:
        status_val = status_match.group(1)
        status_ok = (status_val == "completed")
        status_detail = f"Status is '{status_val}' (expected 'completed')"
    check("status_is_completed", status_ok, status_detail)

    # ── CHECK 5: Created timestamp line present ───────────────────────────────────
    created_match = re.search(r'Created:\s*\d{4}-\d{2}-\d{2}', content)
    check("created_timestamp_present", bool(created_match),
          "Created: YYYY-MM-DD timestamp found" if created_match else "No 'Created:' timestamp line found")

    # ── CHECK 6: TodoList has at least 3 steps with [x] checked off ───────────────
    checked_steps = re.findall(r'-\s*\[x\]', content, re.IGNORECASE)
    all_steps = re.findall(r'-\s*\[[x ]\]', content, re.IGNORECASE)
    enough_steps = len(all_steps) >= 3
    all_checked = len(checked_steps) == len(all_steps) and len(all_steps) > 0
    check("todolist_has_3plus_steps", enough_steps,
          f"Found {len(all_steps)} steps (need >= 3)")
    check("all_steps_checked_off", all_checked,
          f"{len(checked_steps)}/{len(all_steps)} steps checked [x]")

    # ── CHECK 7: Steps include tool/skill annotations in backticks ────────────────
    # e.g.  `web search`  or  `internal reasoning`
    backtick_annotations = re.findall(r'`[^`]+`', content)
    # Filter to those appearing on step lines
    step_lines = [l for l in content.splitlines() if re.match(r'\s*-\s*\[[x ]\]', l, re.IGNORECASE)]
    annotated_steps = [l for l in step_lines if '`' in l]
    annotation_ok = len(annotated_steps) >= 2
    check("steps_have_tool_annotations", annotation_ok,
          f"{len(annotated_steps)}/{len(step_lines)} steps have backtick tool annotations (need >= 2)")

    # ── CHECK 8: Assumptions & Confirmations block has "Assumed:" prefix ─────────
    assumed_present = bool(re.search(r'[-*]?\s*Assumed:', content))
    check("assumptions_block_has_assumed_prefix", assumed_present,
          "'Assumed:' prefix found in Assumptions block" if assumed_present else "No 'Assumed:' prefix found")

    # ── CHECK 9: Progress section has X/Y format ──────────────────────────────────
    progress_match = re.search(r'##\s*Progress\s*\n.*?(\d+)/(\d+)\s*steps?\s*completed', content, re.DOTALL | re.IGNORECASE)
    if progress_match:
        done = int(progress_match.group(1))
        total = int(progress_match.group(2))
        progress_consistent = (done == total and done > 0)
        check("progress_section_format", True,
              f"Progress section found: {done}/{total} steps completed")
        check("progress_reflects_completion", progress_consistent,
              f"{done}/{total} — {'consistent with completion' if progress_consistent else 'done != total, inconsistent with completed status'}")
    else:
        check("progress_section_format", False,
              "No 'X/Y steps completed' pattern found in ## Progress section")
        check("progress_reflects_completion", False,
              "Cannot check progress consistency — pattern missing")

    # ── CHECK 10: The interrupted in-progress file was acknowledged ───────────────
    # Agent should NOT have modified the in-progress file to completed (that task
    # wasn't finished by the agent). It should have left it or mentioned it.
    # But more importantly: the agent should have created a NEW separate plan.
    # We verify the old interrupted file is still in-progress (not tampered).
    interrupted_path = todolist_dir / "20250108-competitive-pricing-research.md"
    try:
        interrupted_content = interrupted_path.read_text(encoding="utf-8")
        interrupted_status = re.search(r'Status:\s*(in-progress|completed)', interrupted_content)
        if interrupted_status:
            old_status = interrupted_status.group(1)
            # The old file should still exist. Whether it was resumed or left alone,
            # the key signal is the agent created a NEW file for the NEW task.
            check("interrupted_file_preserved", True,
                  f"Interrupted file still exists with status: {old_status}")
        else:
            check("interrupted_file_preserved", False,
                  "Interrupted file exists but Status field was removed")
    except Exception as e:
        check("interrupted_file_preserved", False,
              f"Interrupted file missing or unreadable: {e}")

    # ── CHECK 11: New file is different task from interrupted one ────────────────
    # The new plan must NOT be the same task name as competitive-pricing-research
    new_name_lower = new_file.stem.lower()
    is_new_task = "competitive-pricing-research" not in new_name_lower
    check("new_file_is_distinct_task", is_new_task,
          f"New file '{new_file.name}' is for a distinct task" if is_new_task
          else "New file appears to be the same as the interrupted task — agent may have duplicated it")

    # ── Scoring ───────────────────────────────────────────────────────────────────
    weights = {
        "new_todolist_file_created": 0.10,
        "filename_convention_YYYYMMDD": 0.10,
        "required_sections_present": 0.10,
        "status_is_completed": 0.10,
        "created_timestamp_present": 0.05,
        "todolist_has_3plus_steps": 0.10,
        "all_steps_checked_off": 0.10,
        "steps_have_tool_annotations": 0.10,
        "assumptions_block_has_assumed_prefix": 0.08,
        "progress_section_format": 0.07,
        "progress_reflects_completion": 0.05,
        "interrupted_file_preserved": 0.03,
        "new_file_is_distinct_task": 0.02,
    }

    score = 0.0
    for c in checks:
        w = weights.get(c["name"], 0.0)
        if c["passed"]:
            score += w

    passed = score >= 0.75

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks,
    }


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(ws)
    print(json.dumps(result, indent=2))