import sys
import json
import csv
from pathlib import Path

def load_expected_calendar():
    """
    Ground truth derived directly from the SKILL.md 2026 calendar tables.
    Returns a dict: date_str -> {sprint, tone, tone_name, essence, action, reflection_phase, ideal_for_meeting}
    """
    # Tone definitions from SKILL.md
    tone_defs = {
        1:  ("Magnetic",      "Goal",       "Define the goal for the entire sprint. Choose carefully, you'll need to stick with it."),
        2:  ("Lunar",         "Challenge",  "Write down the doubt or challenge you faced today."),
        3:  ("Electric",      "Activation", "Take the first action on the project. Feel the energy to make great first steps."),
        4:  ("Self-Existing", "Plan",       "Lock in the final plan and tasks. Write it down. Feel free to adjust."),
        5:  ("Overtone",      "Traction",   "The work is progressing, show the first results to others."),
        6:  ("Rhythmic",      "Balance",    "Balance between sprint tasks and others. Take time for family and other commitments."),
        7:  ("Resonant",      "Sync",       "Align with partners and the team. Collaborate. Great time for calls and meetings."),
        8:  ("Galactic",      "Focus",      "Stay true to your original intent while acting. Maintain progress."),
        9:  ("Solar",         "Intention",  "Set the intention to act. Finalize preparation. Remember why you chose your goal."),
        10: ("Planetary",     "Action",     "Act, make sprint results available to everyone. Release publicly. Make it visible."),
        11: ("Spectral",      "Cleanup",    "Clear space and mind. Remove what's unnecessary."),
        12: ("Crystal",       "Results",    "Write down the results achieved in this sprint. What are you proud of?"),
        13: ("Cosmic",        "Reflection", "Write down what you learned. No new tasks today. Take final rest before new cycle."),
    }
    # Reflection phase: Tones 11, 12, 13
    reflection_tones = {11, 12, 13}

    # Ground truth from SKILL.md calendar tables (exact lookup):
    # date -> (sprint, tone)
    calendar_lookup = {
        "2026-04-01": (7,  9),
        "2026-04-02": (8,  10),
        "2026-04-06": (8,  1),
        "2026-04-12": (8,  7),
        "2026-04-15": (9,  10),
        "2026-04-19": (9,  1),
        "2026-04-28": (10, 10),
        "2026-05-01": (10, 13),
        "2026-05-11": (11, 10),
        "2026-05-15": (11, 1),
        "2026-06-06": (13, 10),
        "2026-06-16": (13, 7),
    }

    expected = {}
    for date_str, (sprint, tone) in calendar_lookup.items():
        name, essence, action = tone_defs[tone]
        expected[date_str] = {
            "sprint": sprint,
            "tone": tone,
            "tone_name": name,
            "essence": essence,
            "action": action,
            "reflection_phase": tone in reflection_tones,
            "ideal_for_meeting": tone == 7,
        }
    return expected

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # Find sprint_report.json anywhere in workspace
    candidates = list(workspace.rglob("sprint_report.json"))

    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{
                "name": "file_exists",
                "passed": False,
                "detail": "sprint_report.json not found anywhere in workspace."
            }]
        }

    report_path = candidates[0]
    checks.append({
        "name": "file_exists",
        "passed": True,
        "detail": f"Found sprint_report.json at {report_path}"
    })

    try:
        with open(report_path, "r") as f:
            report = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{
                "name": "json_parseable",
                "passed": False,
                "detail": f"Failed to parse JSON: {e}"
            }]
        }

    checks.append({
        "name": "json_parseable",
        "passed": True,
        "detail": "JSON parsed successfully."
    })

    expected = load_expected_calendar()

    # Build a flat lookup of the agent's output by date
    # Agent output may be a list of records or a dict keyed by date
    agent_by_date = {}
    try:
        if isinstance(report, list):
            for record in report:
                d = str(record.get("date", "")).strip()
                if d:
                    agent_by_date[d] = record
        elif isinstance(report, dict):
            # Could be {"records": [...]} or {"2026-04-01": {...}}
            if "records" in report:
                for record in report["records"]:
                    d = str(record.get("date", "")).strip()
                    if d:
                        agent_by_date[d] = record
            else:
                for key, val in report.items():
                    if key.startswith("2026-"):
                        agent_by_date[key] = val
                    elif isinstance(val, dict) and "date" in val:
                        agent_by_date[str(val["date"]).strip()] = val
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{
                "name": "structure_parseable",
                "passed": False,
                "detail": f"Could not extract records from JSON structure: {e}"
            }]
        }

    checks.append({
        "name": "structure_parseable",
        "passed": len(agent_by_date) > 0,
        "detail": f"Extracted {len(agent_by_date)} date-keyed records from report."
    })

    if len(agent_by_date) == 0:
        return {"passed": False, "score": 0.0, "checks": checks}

    # Check coverage
    missing_dates = [d for d in expected if d not in agent_by_date]
    coverage_ok = len(missing_dates) == 0
    checks.append({
        "name": "all_12_dates_covered",
        "passed": coverage_ok,
        "detail": f"Missing dates: {missing_dates}" if missing_dates else "All 12 dates present."
    })

    # Per-date field checks
    field_scores = []

    # --- Critical adversarial dates to check individually ---
    adversarial_checks = [
        ("2026-04-01", "sprint", 7,  "Sprint boundary: Apr 1 must be Sprint 7 (last day), not Sprint 8"),
        ("2026-04-02", "sprint", 8,  "Sprint boundary: Apr 2 must be Sprint 8 (first day), not Sprint 7"),
        ("2026-04-01", "tone",   9,  "Apr 1 tone must be 9 (Solar), not 10 — year starts on Tone 10 not Tone 1"),
        ("2026-04-02", "tone",   10, "Apr 2 is Sprint 8 Tone 10 (Planetary) — new sprint starts here"),
        ("2026-04-06", "tone",   1,  "Apr 6 must be Tone 1 (Magnetic) — sprint 8 goal-setting day"),
        ("2026-04-12", "tone",   7,  "Apr 12 must be Tone 7 (Resonant) — ideal meeting day"),
        ("2026-05-01", "tone",   13, "May 1 must be Tone 13 (Cosmic) — reflection/end of sprint 10"),
        ("2026-05-01", "reflection_phase", True, "May 1 Tone 13 must be marked reflection_phase=true"),
        ("2026-04-12", "ideal_for_meeting", True, "Apr 12 Tone 7 must be marked ideal_for_meeting=true"),
        ("2026-04-06", "ideal_for_meeting", False, "Apr 6 Tone 1 must NOT be marked ideal_for_meeting"),
        ("2026-06-06", "sprint", 13, "Jun 6 must be Sprint 13"),
        ("2026-06-06", "tone",   10, "Jun 6 must be Tone 10 (Planetary)"),
        ("2026-06-16", "tone",   7,  "Jun 16 must be Tone 7 (Resonant)"),
        ("2026-06-16", "ideal_for_meeting", True, "Jun 16 Tone 7 must be ideal_for_meeting=true"),
    ]

    for date_str, field, expected_val, description in adversarial_checks:
        try:
            if date_str not in agent_by_date:
                checks.append({
                    "name": f"adversarial_{date_str}_{field}",
                    "passed": False,
                    "detail": f"{description} — date not found in output."
                })
                field_scores.append(0)
                continue

            record = agent_by_date[date_str]
            # Normalize field lookup: try direct key and some common aliases
            aliases = {
                "sprint": ["sprint", "sprint_number", "sprint_num"],
                "tone": ["tone", "tone_number", "tone_num", "tone_id"],
                "tone_name": ["tone_name", "name", "tone_title"],
                "essence": ["essence", "focus", "essence_keyword"],
                "action": ["action", "recommended_action", "daily_action"],
                "reflection_phase": ["reflection_phase", "is_reflection", "reflection"],
                "ideal_for_meeting": ["ideal_for_meeting", "meeting_day", "is_meeting_day"],
            }
            actual_val = None
            for alias in aliases.get(field, [field]):
                if alias in record:
                    actual_val = record[alias]
                    break

            if actual_val is None:
                checks.append({
                    "name": f"adversarial_{date_str}_{field}",
                    "passed": False,
                    "detail": f"{description} — field '{field}' not found in record."
                })
                field_scores.append(0)
                continue

            # Normalize booleans
            if isinstance(expected_val, bool):
                if isinstance(actual_val, str):
                    actual_val = actual_val.lower() in ("true", "1", "yes")
                else:
                    actual_val = bool(actual_val)

            # Normalize ints
            if isinstance(expected_val, int):
                try:
                    actual_val = int(actual_val)
                except (ValueError, TypeError):
                    pass

            passed = actual_val == expected_val
            field_scores.append(1 if passed else 0)
            checks.append({
                "name": f"adversarial_{date_str}_{field}",
                "passed": passed,
                "detail": f"{description} — got: {actual_val}, expected: {expected_val}"
            })
        except Exception as e:
            checks.append({
                "name": f"adversarial_{date_str}_{field}",
                "passed": False,
                "detail": f"Error checking {date_str} {field}: {e}"
            })
            field_scores.append(0)

    # Check tone names for all 12 dates
    tone_name_correct = 0
    for date_str, exp in expected.items():
        if date_str not in agent_by_date:
            continue
        record = agent_by_date[date_str]
        agent_name = None
        for key in ["tone_name", "name", "tone_title"]:
            if key in record:
                agent_name = str(record[key]).strip()
                break
        if agent_name and agent_name.lower() == exp["tone_name"].lower():
            tone_name_correct += 1

    tone_name_pass = tone_name_correct >= 10
    checks.append({
        "name": "tone_names_correct",
        "passed": tone_name_pass,
        "detail": f"{tone_name_correct}/12 tone names correctly match SKILL.md definitions."
    })

    # Check reflection_phase classification for all dates
    reflection_correct = 0
    for date_str, exp in expected.items():
        if date_str not in agent_by_date:
            continue
        record = agent_by_date[date_str]
        agent_rp = None
        for key in ["reflection_phase", "is_reflection", "reflection"]:
            if key in record:
                agent_rp = record[key]
                break
        if agent_rp is not None:
            if isinstance(agent_rp, str):
                agent_rp = agent_rp.lower() in ("true", "1", "yes")
            else:
                agent_rp = bool(agent_rp)
            if agent_rp == exp["reflection_phase"]:
                reflection_correct += 1

    reflection_pass = reflection_correct >= 10
    checks.append({
        "name": "reflection_phase_correct",
        "passed": reflection_pass,
        "detail": f"{reflection_correct}/12 reflection_phase flags correctly set."
    })

    # Check ideal_for_meeting for all dates
    meeting_correct = 0
    for date_str, exp in expected.items():
        if date_str not in agent_by_date:
            continue
        record = agent_by_date[date_str]
        agent_im = None
        for key in ["ideal_for_meeting", "meeting_day", "is_meeting_day"]:
            if key in record:
                agent_im = record[key]
                break
        if agent_im is not None:
            if isinstance(agent_im, str):
                agent_im = agent_im.lower() in ("true", "1", "yes")
            else:
                agent_im = bool(agent_im)
            if agent_im == exp["ideal_for_meeting"]:
                meeting_correct += 1

    meeting_pass = meeting_correct >= 10
    checks.append({
        "name": "ideal_for_meeting_correct",
        "passed": meeting_pass,
        "detail": f"{meeting_correct}/12 ideal_for_meeting flags correctly set."
    })

    # Scoring
    all_check_results = [c["passed"] for c in checks]
    score = sum(all_check_results) / len(all_check_results) if all_check_results else 0.0

    # Must pass: file exists, json parseable, adversarial critical checks, tone names, reflection, meeting flags
    critical_names = {
        "file_exists", "json_parseable", "all_12_dates_covered",
        "tone_names_correct", "reflection_phase_correct", "ideal_for_meeting_correct",
    }
    # Also all adversarial checks involving sprint boundaries and tone 7 meeting flags
    critical_adversarial = [
        "adversarial_2026-04-01_sprint",
        "adversarial_2026-04-02_sprint",
        "adversarial_2026-04-01_tone",
        "adversarial_2026-04-02_tone",
        "adversarial_2026-05-01_reflection_phase",
        "adversarial_2026-04-12_ideal_for_meeting",
        "adversarial_2026-06-16_ideal_for_meeting",
        "adversarial_2026-04-06_ideal_for_meeting",
    ]

    checks_by_name = {c["name"]: c["passed"] for c in checks}
    critical_passed = all(
        checks_by_name.get(n, False)
        for n in list(critical_names) + critical_adversarial
    )

    passed = critical_passed and score >= 0.72

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))