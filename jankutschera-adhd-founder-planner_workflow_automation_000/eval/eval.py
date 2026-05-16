import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []

    # ─── Locate today's daily log ───────────────────────────────────────────────
    expected_path = ws / ".openclaw" / "skills" / "adhd-daily-planner" / "daily" / "2025-06-10.md"
    
    # Also search by glob in case agent placed it elsewhere in the skill dir
    found_files = list((ws / ".openclaw" / "skills" / "adhd-daily-planner" / "daily").glob("2025-06-10.md")) if (ws / ".openclaw" / "skills" / "adhd-daily-planner" / "daily").exists() else []
    
    if expected_path.exists():
        daily_file = expected_path
    elif found_files:
        daily_file = found_files[0]
    else:
        # Search entire workspace
        all_candidates = list(ws.rglob("2025-06-10.md"))
        daily_file = all_candidates[0] if all_candidates else None

    # CHECK 1: File exists at correct path
    file_at_correct_path = expected_path.exists()
    checks.append({
        "name": "daily_log_exists_at_correct_path",
        "passed": file_at_correct_path,
        "detail": f"Expected: {expected_path} | Found: {file_at_correct_path}"
    })

    if daily_file is None or not daily_file.exists():
        checks.append({"name": "file_readable", "passed": False, "detail": "No 2025-06-10.md found anywhere in workspace"})
        score = sum(1 for c in checks if c["passed"]) / 10.0
        return {"passed": False, "score": score, "checks": checks}

    try:
        content = daily_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": f"Read {len(content)} chars from {daily_file}"})

    # ─── CHECK 2: Correct swim lane headers (exact emoji + label) ────────────────
    required_lanes = [
        "🎯 MUST HAPPEN",
        "🔥 HIGH ENERGY",
        "💧 MEDIUM ENERGY",
        "❄️ LOW ENERGY",
        "🚫 NOT TODAY",
    ]
    lanes_found = {lane: (lane in content) for lane in required_lanes}
    all_lanes = all(lanes_found.values())
    checks.append({
        "name": "all_five_swim_lanes_present",
        "passed": all_lanes,
        "detail": f"Lane presence: {lanes_found}"
    })

    # ─── CHECK 3: Exactly ONE task in MUST HAPPEN lane ──────────────────────────
    try:
        must_happen_section = re.search(
            r"🎯 MUST HAPPEN(.*?)(?=🔥|💧|❄️|🚫|##|---|\Z)",
            content, re.DOTALL
        )
        if must_happen_section:
            must_happen_text = must_happen_section.group(1)
            # Count task lines (lines with bullet symbols: •, ★, ×, >, <)
            task_lines = [l.strip() for l in must_happen_text.split('\n')
                         if re.search(r'^[★•×><]', l.strip())]
            exactly_one = len(task_lines) == 1
            checks.append({
                "name": "exactly_one_task_in_must_happen",
                "passed": exactly_one,
                "detail": f"Tasks in MUST HAPPEN: {task_lines}"
            })
        else:
            checks.append({"name": "exactly_one_task_in_must_happen", "passed": False, "detail": "MUST HAPPEN section not found"})
    except Exception as e:
        checks.append({"name": "exactly_one_task_in_must_happen", "passed": False, "detail": str(e)})

    # ─── CHECK 4: The ONE thing is marked with ★ symbol ────────────────────────
    star_present = "★" in content
    # The ONE thing should be the investor update email (from brain dump: "MUST send investor update email")
    # We check that ★ appears in MUST HAPPEN section
    try:
        must_happen_section2 = re.search(
            r"🎯 MUST HAPPEN(.*?)(?=🔥|💧|❄️|🚫|##|---|\Z)",
            content, re.DOTALL
        )
        star_in_must_happen = "★" in must_happen_section2.group(1) if must_happen_section2 else False
    except:
        star_in_must_happen = False
    checks.append({
        "name": "star_symbol_marks_one_thing_in_must_happen",
        "passed": star_in_must_happen,
        "detail": f"★ in MUST HAPPEN section: {star_in_must_happen}"
    })

    # ─── CHECK 5: Dread task marked with 💀 ─────────────────────────────────────
    # The payment webhook bug is flagged as a dread task in brain dump
    skull_present = "💀" in content
    checks.append({
        "name": "dread_task_marked_with_skull",
        "passed": skull_present,
        "detail": f"💀 symbol present in today's log: {skull_present}"
    })

    # ─── CHECK 6: Migration symbols applied to prior day's tasks ────────────────
    # The prior day log (2025-06-09.md) must be UPDATED with migration symbols.
    # OR today's log must contain migrated tasks marked with > (migrated from yesterday)
    # Per SKILL.md: incomplete tasks get > (migrate) or strikethrough (drop) or < (future date)
    
    prior_log = ws / ".openclaw" / "skills" / "adhd-daily-planner" / "daily" / "2025-06-09.md"
    migration_applied = False
    migration_detail = ""
    try:
        if prior_log.exists():
            prior_content = prior_log.read_text(encoding="utf-8")
            # Look for migration symbols in prior log OR in today's log for tasks from yesterday
            has_migration_arrow = ">" in prior_content or ">" in content
            has_strikethrough = "~~" in prior_content or "~~" in content
            # Check if prior log was updated OR today's log shows migrated tasks
            migration_applied = has_migration_arrow or has_strikethrough
            migration_detail = f"'>' in prior_log: {'>' in prior_content}, '~~' in prior_log: {'~~' in prior_content}, '>' in today: {'>' in content}"
        else:
            migration_detail = "Prior day log not found"
    except Exception as e:
        migration_detail = str(e)
    checks.append({
        "name": "migration_symbols_applied",
        "passed": migration_applied,
        "detail": migration_detail
    })

    # ─── CHECK 7: Tax documents dropped (~~strikethrough~~) not migrated ────────
    # Brain dump says: "file quarterly tax documents" should be dropped (not migrated)
    # This should appear with strikethrough in prior log or be absent from today's active lanes
    try:
        prior_content2 = prior_log.read_text(encoding="utf-8") if prior_log.exists() else ""
        # Tax docs should be struck through in prior log
        tax_dropped = ("~~" in prior_content2 and "tax" in prior_content2.lower()) or \
                      ("~~" in content and "tax" in content.lower())
        # Also acceptable: tax docs should NOT appear as active • task in today's swim lanes
        # Check it's not an active task in HIGH/MEDIUM/LOW lanes
        active_lanes_match = re.search(
            r"🔥 HIGH ENERGY(.*?)(?=🚫|\Z)",
            content, re.DOTALL
        )
        tax_as_active_task = False
        if active_lanes_match:
            active_text = active_lanes_match.group(1)
            # If "tax" appears as a plain • bullet (not struck through), it's wrong
            for line in active_text.split('\n'):
                if re.search(r'^•.*tax', line.strip(), re.IGNORECASE):
                    tax_as_active_task = True
        tax_handled_correctly = tax_dropped or not tax_as_active_task
        checks.append({
            "name": "dread_tax_task_dropped_not_migrated",
            "passed": tax_handled_correctly,
            "detail": f"Tax struck in prior: {tax_dropped}, Tax as active bullet in today: {tax_as_active_task}"
        })
    except Exception as e:
        checks.append({"name": "dread_tax_task_dropped_not_migrated", "passed": False, "detail": str(e)})

    # ─── CHECK 8: Dopamine reward captured ──────────────────────────────────────
    # Brain dump says reward = "go for a 20 minute walk outside"
    # Should appear in dopamine menu or reward section
    dopamine_section = re.search(
        r"(dopamine|reward|🏃|walk|movement)",
        content, re.IGNORECASE
    )
    dopamine_present = dopamine_section is not None
    checks.append({
        "name": "dopamine_reward_captured",
        "passed": dopamine_present,
        "detail": f"Dopamine/reward reference found: {dopamine_present}"
    })

    # ─── CHECK 9: Duration markers used (proprietary format) ────────────────────
    # Must use ⚡5 min, ⏱️15 min, 🕐30 min, or ⏳60+ min — not plain "30 minutes"
    duration_markers = ["⚡", "⏱️", "🕐", "⏳"]
    has_duration_markers = any(m in content for m in duration_markers)
    checks.append({
        "name": "proprietary_duration_markers_used",
        "passed": has_duration_markers,
        "detail": f"Duration emoji markers found: {[m for m in duration_markers if m in content]}"
    })

    # ─── CHECK 10: NOT TODAY lane contains deferred items ───────────────────────
    # "plan team offsite for August" should remain in NOT TODAY
    try:
        not_today_section = re.search(
            r"🚫 NOT TODAY(.*?)(?=##|---|\Z)",
            content, re.DOTALL
        )
        not_today_has_tasks = False
        if not_today_section:
            not_today_text = not_today_section.group(1)
            not_today_lines = [l.strip() for l in not_today_text.split('\n')
                              if re.search(r'[★•×><]', l.strip())]
            not_today_has_tasks = len(not_today_lines) >= 1
        checks.append({
            "name": "not_today_lane_has_deferred_tasks",
            "passed": not_today_has_tasks,
            "detail": f"Tasks in NOT TODAY section found: {not_today_has_tasks}"
        })
    except Exception as e:
        checks.append({"name": "not_today_lane_has_deferred_tasks", "passed": False, "detail": str(e)})

    # ─── Final Scoring ───────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total

    # Must pass at minimum: file at correct path, all swim lanes, exactly one task in MUST HAPPEN, ★ symbol
    critical = ["daily_log_exists_at_correct_path", "all_five_swim_lanes_present",
                "exactly_one_task_in_must_happen", "star_symbol_marks_one_thing_in_must_happen"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)

    return {
        "passed": critical_passed and score >= 0.7,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))