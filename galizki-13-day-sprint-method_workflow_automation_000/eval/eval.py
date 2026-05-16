import sys
import json
import os
from pathlib import Path

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

# Ground truth from SKILL.md calendar - manually verified
# Each entry: date -> (sprint, tone, tone_name, essence, phase)
GROUND_TRUTH = {
    "2026-07-15": {
        "sprint": 16,
        "tone": 10,
        "tone_name": "Planetary",
        "essence": "Action",
        "phase": "Achievement"
    },
    "2026-09-05": {
        "sprint": 20,
        "tone": 10,
        "tone_name": "Planetary",
        "essence": "Action",
        "phase": "Achievement"
    },
    "2026-08-07": {
        "sprint": 17,
        "tone": 7,
        "tone_name": "Resonant",
        "essence": "Sync",
        "phase": "Achievement"
    },
    "2026-10-28": {
        "sprint": 24,
        "tone": 11,
        "tone_name": "Spectral",
        "essence": "Cleanup",
        "phase": "Reflection"
    },
    "2026-12-21": {
        "sprint": 28,
        "tone": 13,
        "tone_name": "Cosmic",
        "essence": "Reflection",
        "phase": "Reflection"
    },
    "2026-11-13": {
        "sprint": 25,
        "tone": 1,
        "tone_name": "Magnetic",
        "essence": "Goal",
        "phase": "Achievement"
    }
}

# Milestone IDs to dates
MILESTONE_DATE_MAP = {
    "M1": "2026-07-15",
    "M2": "2026-09-05",
    "M3": "2026-08-07",
    "M4": "2026-10-28",
    "M5": "2026-12-21",
    "M6": "2026-11-13"
}

def find_output_file(workspace):
    """Search for the sprint_analysis.json output file."""
    candidates = list(Path(workspace).rglob("sprint_analysis.json"))
    if candidates:
        return candidates[0]
    return None

def normalize_str(s):
    if s is None:
        return ""
    return str(s).strip().lower()

def check_field_fuzzy(value, expected_str):
    """Case-insensitive substring or equality check."""
    v = normalize_str(value)
    e = normalize_str(expected_str)
    return e in v or v == e

def run_evaluation(workspace):
    checks = []
    total_score = 0.0

    # --- Check 1: Output file exists ---
    output_path = find_output_file(workspace)
    file_exists = output_path is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found sprint_analysis.json at: {output_path}" if file_exists else "sprint_analysis.json not found anywhere in workspace"
    })
    if not file_exists:
        return {"passed": False, "score": 0.0, "checks": checks}

    # --- Check 2: Valid JSON structure ---
    try:
        data = load_json(output_path)
        is_valid_json = True
        checks.append({"name": "valid_json_structure", "passed": True, "detail": f"File parsed successfully from {output_path}"})
    except Exception as e:
        checks.append({"name": "valid_json_structure", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # --- Check 3: Contains milestone entries ---
    # Find the list of milestone analyses - could be top-level list or nested
    milestone_entries = None
    if isinstance(data, list):
        milestone_entries = data
    elif isinstance(data, dict):
        for key in ["milestones", "analysis", "results", "sprint_analysis", "milestone_analysis"]:
            if key in data and isinstance(data[key], list):
                milestone_entries = data[key]
                break
        if milestone_entries is None:
            # Try to find any list value
            for v in data.values():
                if isinstance(v, list) and len(v) >= 3:
                    milestone_entries = v
                    break

    has_entries = milestone_entries is not None and len(milestone_entries) >= 6
    checks.append({
        "name": "has_all_milestone_entries",
        "passed": has_entries,
        "detail": f"Found {len(milestone_entries) if milestone_entries else 0} entries, expected 6"
    })
    if not has_entries:
        return {"passed": False, "score": 0.1, "checks": checks}

    # Build a lookup by date or ID
    entry_by_date = {}
    entry_by_id = {}
    for entry in milestone_entries:
        if not isinstance(entry, dict):
            continue
        date_val = entry.get("date", entry.get("milestone_date", ""))
        id_val = entry.get("id", entry.get("milestone_id", ""))
        if date_val:
            entry_by_date[str(date_val).strip()] = entry
        if id_val:
            entry_by_id[str(id_val).strip()] = entry

    # Per-milestone checks (each worth ~1/6 of remaining score)
    milestone_checks_passed = 0
    per_milestone_weight = 1.0 / 6

    for mid, date in MILESTONE_DATE_MAP.items():
        gt = GROUND_TRUTH[date]
        entry = entry_by_date.get(date) or entry_by_id.get(mid)
        if entry is None:
            checks.append({
                "name": f"milestone_{mid}_found",
                "passed": False,
                "detail": f"No entry found for milestone {mid} (date {date})"
            })
            continue

        m_checks = []

        # Check sprint number
        sprint_val = entry.get("sprint", entry.get("sprint_number", entry.get("sprint_num", None)))
        sprint_ok = False
        try:
            sprint_ok = int(sprint_val) == gt["sprint"]
        except (TypeError, ValueError):
            sprint_ok = False
        m_checks.append(("sprint_number", sprint_ok, f"Expected sprint={gt['sprint']}, got {sprint_val}"))

        # Check tone number
        tone_val = entry.get("tone", entry.get("tone_number", entry.get("tone_num", None)))
        tone_ok = False
        try:
            tone_ok = int(tone_val) == gt["tone"]
        except (TypeError, ValueError):
            tone_ok = False
        m_checks.append(("tone_number", tone_ok, f"Expected tone={gt['tone']}, got {tone_val}"))

        # Check tone name
        tone_name_val = entry.get("tone_name", entry.get("name", entry.get("tone_label", "")))
        tone_name_ok = check_field_fuzzy(tone_name_val, gt["tone_name"])
        m_checks.append(("tone_name", tone_name_ok, f"Expected tone_name='{gt['tone_name']}', got '{tone_name_val}'"))

        # Check essence
        essence_val = entry.get("essence", entry.get("focus", entry.get("energy", "")))
        essence_ok = check_field_fuzzy(essence_val, gt["essence"])
        m_checks.append(("essence", essence_ok, f"Expected essence='{gt['essence']}', got '{essence_val}'"))

        # Check phase (Achievement vs Reflection)
        phase_val = entry.get("phase", entry.get("sprint_phase", entry.get("cycle_phase", "")))
        phase_ok = check_field_fuzzy(phase_val, gt["phase"])
        m_checks.append(("phase", phase_ok, f"Expected phase='{gt['phase']}', got '{phase_val}'"))

        milestone_passed_count = sum(1 for _, ok, _ in m_checks if ok)
        milestone_fully_passed = milestone_passed_count >= 4  # Allow 1 field to be in a different key

        for chk_name, chk_ok, chk_detail in m_checks:
            checks.append({
                "name": f"milestone_{mid}_{chk_name}",
                "passed": chk_ok,
                "detail": chk_detail
            })

        if milestone_fully_passed:
            milestone_checks_passed += 1

    # --- Critical proprietary trap checks ---
    # Verify the agent did NOT use naive arithmetic (offset trap)
    # M1: 2026-07-15 must be Sprint 16, Tone 10 (NOT what naive day-of-year % 13 would give)
    # 2026-07-15 is day 196 of 2026. (196-1) % 13 = 195 % 13 = 0 -> tone 13? or 1 depending on formula
    # Correct is tone 10, sprint 16. This catches naive calculators.
    m1_entry = entry_by_date.get("2026-07-15") or entry_by_id.get("M1")
    proprietary_trap_1_passed = False
    if m1_entry:
        try:
            t = int(m1_entry.get("tone", m1_entry.get("tone_number", 0)))
            s = int(m1_entry.get("sprint", m1_entry.get("sprint_number", 0)))
            proprietary_trap_1_passed = (t == 10 and s == 16)
        except:
            pass
    checks.append({
        "name": "proprietary_trap_calendar_offset_M1",
        "passed": proprietary_trap_1_passed,
        "detail": "2026-07-15 must be Sprint 16 Tone 10 (Planetary). Naive day-of-year arithmetic gives wrong result."
    })

    # Verify Reflection Phase correctly identified for M4 (Tone 11)
    m4_entry = entry_by_date.get("2026-10-28") or entry_by_id.get("M4")
    proprietary_trap_2_passed = False
    if m4_entry:
        phase_raw = m4_entry.get("phase", m4_entry.get("sprint_phase", ""))
        tone_raw = m4_entry.get("tone", m4_entry.get("tone_number", None))
        try:
            tone_int = int(tone_raw)
            phase_correct = check_field_fuzzy(phase_raw, "reflection")
            proprietary_trap_2_passed = (tone_int == 11 and phase_correct)
        except:
            pass
    checks.append({
        "name": "proprietary_trap_reflection_phase_M4",
        "passed": proprietary_trap_2_passed,
        "detail": "2026-10-28 must be Tone 11 (Spectral) in Reflection Phase (tones 11-13 = Reflection Phase)"
    })

    # Verify Tone 1 (Magnetic) identified as goal-setting moment for M6
    m6_entry = entry_by_date.get("2026-11-13") or entry_by_id.get("M6")
    proprietary_trap_3_passed = False
    if m6_entry:
        try:
            tone_int = int(m6_entry.get("tone", m6_entry.get("tone_number", 0)))
            # Either tone_name or essence/action should reference goal/magnetic
            tone_name = normalize_str(m6_entry.get("tone_name", ""))
            essence = normalize_str(m6_entry.get("essence", ""))
            action_text = normalize_str(m6_entry.get("action", m6_entry.get("recommended_action", m6_entry.get("guidance", ""))))
            proprietary_trap_3_passed = (
                tone_int == 1 and
                ("magnetic" in tone_name or "magnetic" in action_text or "goal" in essence or "goal" in action_text)
            )
        except:
            pass
    checks.append({
        "name": "proprietary_trap_tone1_magnetic_M6",
        "passed": proprietary_trap_3_passed,
        "detail": "2026-11-13 must be Tone 1 (Magnetic) with Goal/goal-setting essence recognized"
    })

    # --- Compute final score ---
    all_checks = checks
    trap_checks = [c for c in all_checks if c["name"].startswith("proprietary_trap")]
    milestone_detail_checks = [c for c in all_checks if c["name"].startswith("milestone_") and not c["name"].endswith("_found")]

    trap_passed = sum(1 for c in trap_checks if c["passed"])
    milestone_detail_passed = sum(1 for c in milestone_detail_checks if c["passed"])
    total_milestone_detail = len(milestone_detail_checks) if milestone_detail_checks else 1

    # Scoring:
    # 20% - file exists + valid JSON + has entries
    # 30% - per-milestone field accuracy (sprint, tone, name, essence, phase across 6 milestones)
    # 30% - proprietary trap checks (3 traps, 10% each)
    # 20% - overall milestone correctness (at least 4/6 fully correct)

    base_score = 0.2 if (file_exists and is_valid_json and has_entries) else 0.0
    detail_score = 0.30 * (milestone_detail_passed / max(total_milestone_detail, 1))
    trap_score = 0.30 * (trap_passed / 3)
    milestone_complete_score = 0.20 * (milestone_checks_passed / 6)

    final_score = base_score + detail_score + trap_score + milestone_complete_score

    # Overall pass: must get at least 2/3 proprietary traps AND 4/6 milestones substantially correct
    passed = (trap_passed >= 2) and (milestone_checks_passed >= 4)

    return {
        "passed": passed,
        "score": round(final_score, 3),
        "checks": all_checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_evaluation(workspace)
    print(json.dumps(result, indent=2))