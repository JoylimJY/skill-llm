import sys
import json
import re
from pathlib import Path

def load_json_safe(path):
    try:
        return json.loads(Path(path).read_text()), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path}: {e}"

def run_eval(workspace):
    workspace = Path(workspace)
    checks = []
    total_score = 0.0

    # ── 1. nag-config.json exists at workspace root ────────────────────────
    config_path = workspace / "nag-config.json"
    config, err = load_json_safe(config_path)

    check_exists = {"name": "nag-config.json exists at workspace root", "passed": False, "detail": ""}
    if err:
        check_exists["detail"] = err
        checks.append(check_exists)
        # Cannot proceed with config checks
        config = None
    else:
        check_exists["passed"] = True
        check_exists["detail"] = "File found and parsed."
        checks.append(check_exists)

    # ── 2. Config has exactly 2 reminders ─────────────────────────────────
    check_count = {"name": "Config has exactly 2 reminders", "passed": False, "detail": ""}
    if config:
        reminders = config.get("reminders", [])
        if len(reminders) == 2:
            check_count["passed"] = True
            check_count["detail"] = "Found 2 reminders."
        else:
            check_count["detail"] = f"Expected 2 reminders, found {len(reminders)}."
    else:
        check_count["detail"] = "Config not loaded."
    checks.append(check_count)

    # Helper: find reminder by id
    def find_reminder(rems, rid):
        for r in rems:
            if r.get("id") == rid:
                return r
        return None

    reminders = config.get("reminders", []) if config else []

    # ── 3. Protein shake reminder: required fields ─────────────────────────
    protein_id_candidates = ["protein-shake", "protein_shake", "post-workout-protein", 
                              "protein", "post-workout", "protein-shake-reminder"]
    protein = None
    for pid in protein_id_candidates:
        protein = find_reminder(reminders, pid)
        if protein:
            break
    # Also try partial match
    if not protein:
        for r in reminders:
            rid = r.get("id", "").lower()
            if "protein" in rid or "shake" in rid or ("post" in rid and "workout" in rid):
                protein = r
                break

    check_protein_id = {"name": "Protein shake reminder exists (by id containing 'protein' or 'shake')", 
                        "passed": protein is not None, 
                        "detail": f"Found: {protein.get('id') if protein else 'None'}"}
    checks.append(check_protein_id)

    if protein:
        # cronFirst = "30 7 * * 1-5" or equivalent weekday-only expression
        cron_first = protein.get("cronFirst", "")
        # Accept various valid formats for 7:30 AM weekdays
        # "30 7 * * 1-5" or "30 7 * * mon-fri" or "30 7 * * MON-FRI"
        cron_ok = bool(re.match(r"30\s+7\s+\*\s+\*\s+(1-5|mon-fri|MON-FRI|Mon-Fri)", cron_first, re.IGNORECASE))
        check_protein_cron = {"name": "Protein shake cronFirst: 7:30 AM weekdays", 
                               "passed": cron_ok, 
                               "detail": f"cronFirst='{cron_first}'"}
        checks.append(check_protein_cron)

        # nagAfter = "08:15"
        nag_after = protein.get("nagAfter", "")
        nag_ok = nag_after.strip() == "08:15"
        check_protein_nag = {"name": "Protein shake nagAfter: 08:15", 
                              "passed": nag_ok, 
                              "detail": f"nagAfter='{nag_after}'"}
        checks.append(check_protein_nag)

        # confirmPatterns includes required phrases (case-insensitive check)
        patterns = [p.lower() for p in protein.get("confirmPatterns", [])]
        required_patterns = ["had it", "drank it", "done", "finished"]
        all_patterns_present = all(any(req in p for p in patterns) or req in patterns for req in required_patterns)
        check_protein_patterns = {"name": "Protein shake confirmPatterns include all required phrases", 
                                   "passed": all_patterns_present, 
                                   "detail": f"patterns={patterns}"}
        checks.append(check_protein_patterns)

        # days = ["monday","tuesday","wednesday","thursday","friday"] (case-insensitive)
        days = [d.lower() for d in protein.get("days", [])]
        expected_days = {"monday", "tuesday", "wednesday", "thursday", "friday"}
        days_ok = set(days) == expected_days
        check_protein_days = {"name": "Protein shake days: Mon-Fri only", 
                               "passed": days_ok, 
                               "detail": f"days={days}"}
        checks.append(check_protein_days)

        # messages.first must be present
        first_msg = protein.get("messages", {}).get("first", "")
        first_ok = len(first_msg.strip()) > 5
        check_protein_first = {"name": "Protein shake messages.first is set", 
                                "passed": first_ok, 
                                "detail": f"messages.first='{first_msg[:80]}'"}
        checks.append(check_protein_first)

        # tone must be present and mention escalation/caps
        tone = protein.get("tone", "").lower()
        tone_ok = len(tone) > 5 and ("caps" in tone or "escalat" in tone or "urgent" in tone or "all cap" in tone)
        check_protein_tone = {"name": "Protein shake tone mentions escalation/caps", 
                               "passed": tone_ok, 
                               "detail": f"tone='{protein.get('tone','')[:100]}'"}
        checks.append(check_protein_tone)

    # ── 4. Mobility reminder: required fields ──────────────────────────────
    mobility = None
    mobility_id_candidates = ["evening-mobility", "mobility", "evening-stretch", 
                               "mobility-routine", "stretch", "evening_mobility"]
    for mid in mobility_id_candidates:
        mobility = find_reminder(reminders, mid)
        if mobility:
            break
    if not mobility:
        for r in reminders:
            rid = r.get("id", "").lower()
            if "mobil" in rid or "stretch" in rid or "evening" in rid:
                mobility = r
                break

    check_mobility_id = {"name": "Mobility reminder exists (by id containing 'mobil', 'stretch', or 'evening')", 
                         "passed": mobility is not None, 
                         "detail": f"Found: {mobility.get('id') if mobility else 'None'}"}
    checks.append(check_mobility_id)

    if mobility:
        # cronFirst = "0 20 * * *" (8 PM every day)
        cron_first_m = mobility.get("cronFirst", "")
        cron_m_ok = bool(re.match(r"0\s+20\s+\*\s+\*\s+\*", cron_first_m))
        check_mobility_cron = {"name": "Mobility cronFirst: 8:00 PM every day", 
                                "passed": cron_m_ok, 
                                "detail": f"cronFirst='{cron_first_m}'"}
        checks.append(check_mobility_cron)

        # nagAfter = "20:45"
        nag_after_m = mobility.get("nagAfter", "")
        nag_m_ok = nag_after_m.strip() == "20:45"
        check_mobility_nag = {"name": "Mobility nagAfter: 20:45", 
                               "passed": nag_m_ok, 
                               "detail": f"nagAfter='{nag_after_m}'"}
        checks.append(check_mobility_nag)

        # confirmPatterns
        m_patterns = [p.lower() for p in mobility.get("confirmPatterns", [])]
        required_m = ["stretched", "done", "completed", "finished it", "all done"]
        all_m_present = all(
            any(req in p for p in m_patterns) or req in m_patterns 
            for req in required_m
        )
        check_mobility_patterns = {"name": "Mobility confirmPatterns include all required phrases", 
                                    "passed": all_m_present, 
                                    "detail": f"patterns={m_patterns}"}
        checks.append(check_mobility_patterns)

        # days should NOT be specified (fires every day)
        days_m = mobility.get("days")
        no_days_ok = days_m is None or days_m == []
        check_mobility_nodays = {"name": "Mobility reminder has no days restriction (fires every day)", 
                                  "passed": no_days_ok, 
                                  "detail": f"days={days_m}"}
        checks.append(check_mobility_nodays)

        # messages.first should NOT be set (generate from label/tone)
        first_m = mobility.get("messages", {}).get("first", None)
        no_first_ok = first_m is None or first_m == ""
        check_mobility_nofirst = {"name": "Mobility messages.first absent (should be generated)", 
                                   "passed": no_first_ok, 
                                   "detail": f"messages.first={first_m}"}
        checks.append(check_mobility_nofirst)

        # tone must be present
        tone_m = mobility.get("tone", "")
        tone_m_ok = len(tone_m.strip()) > 5
        check_mobility_tone = {"name": "Mobility tone field is set", 
                                "passed": tone_m_ok, 
                                "detail": f"tone='{tone_m[:100]}'"}
        checks.append(check_mobility_tone)

    # ── 5. memory/nag-state.json: correct schema and state ────────────────
    state_path = workspace / "memory" / "nag-state.json"
    state, state_err = load_json_safe(state_path)

    check_state_exists = {"name": "memory/nag-state.json exists and is valid JSON", 
                          "passed": state is not None, 
                          "detail": state_err or "OK"}
    checks.append(check_state_exists)

    if state:
        # date must be 2026-02-15
        state_date = state.get("date", "")
        check_state_date = {"name": "State date is 2026-02-15", 
                            "passed": state_date == "2026-02-15", 
                            "detail": f"date='{state_date}'"}
        checks.append(check_state_date)

        state_reminders = state.get("reminders", {})

        # Protein shake: confirmed=true, confirmedAt="08:22", nagCount=1
        protein_id_actual = protein.get("id") if protein else None
        protein_state = state_reminders.get(protein_id_actual, {}) if protein_id_actual else {}
        
        # Also try common ids if protein not found
        if not protein_state:
            for pid in protein_id_candidates:
                if pid in state_reminders:
                    protein_state = state_reminders[pid]
                    break

        check_protein_confirmed = {"name": "Protein shake: confirmed=true in state", 
                                    "passed": protein_state.get("confirmed") is True, 
                                    "detail": f"confirmed={protein_state.get('confirmed')}"}
        checks.append(check_protein_confirmed)

        check_protein_confirmed_at = {"name": "Protein shake: confirmedAt='08:22' in state", 
                                       "passed": protein_state.get("confirmedAt", "").strip() == "08:22", 
                                       "detail": f"confirmedAt='{protein_state.get('confirmedAt')}'"}
        checks.append(check_protein_confirmed_at)

        check_protein_nag_count = {"name": "Protein shake: nagCount=1 in state", 
                                    "passed": protein_state.get("nagCount") == 1, 
                                    "detail": f"nagCount={protein_state.get('nagCount')}"}
        checks.append(check_protein_nag_count)

        # Mobility: confirmed=false, nagCount=0
        mobility_id_actual = mobility.get("id") if mobility else None
        mobility_state = state_reminders.get(mobility_id_actual, {}) if mobility_id_actual else {}
        if not mobility_state:
            for mid in mobility_id_candidates:
                if mid in state_reminders:
                    mobility_state = state_reminders[mid]
                    break

        check_mobility_unconfirmed = {"name": "Mobility: confirmed=false in state", 
                                       "passed": mobility_state.get("confirmed") is False, 
                                       "detail": f"confirmed={mobility_state.get('confirmed')}"}
        checks.append(check_mobility_unconfirmed)

        check_mobility_nag_zero = {"name": "Mobility: nagCount=0 in state", 
                                    "passed": mobility_state.get("nagCount") == 0, 
                                    "detail": f"nagCount={mobility_state.get('nagCount')}"}
        checks.append(check_mobility_nag_zero)

    # ── 6. HEARTBEAT.md: Nag Check block ─────────────────────────────────
    heartbeat_path = workspace / "HEARTBEAT.md"
    try:
        hb_text = heartbeat_path.read_text()
    except Exception as e:
        hb_text = ""
        checks.append({"name": "HEARTBEAT.md readable", "passed": False, "detail": str(e)})

    hb_lower = hb_text.lower()

    check_hb_section = {"name": "HEARTBEAT.md contains a Nag Check section", 
                         "passed": "nag check" in hb_lower, 
                         "detail": "'nag check' found: " + str("nag check" in hb_lower)}
    checks.append(check_hb_section)

    # Must reference nag-config.json and nag-state.json
    check_hb_config_ref = {"name": "HEARTBEAT.md references nag-config.json", 
                            "passed": "nag-config.json" in hb_text, 
                            "detail": f"Found: {'nag-config.json' in hb_text}"}
    checks.append(check_hb_config_ref)

    check_hb_state_ref = {"name": "HEARTBEAT.md references nag-state.json", 
                           "passed": "nag-state.json" in hb_text, 
                           "detail": f"Found: {'nag-state.json' in hb_text}"}
    checks.append(check_hb_state_ref)

    # Must mention date reset logic
    check_hb_date_reset = {"name": "HEARTBEAT.md describes date-based reset logic", 
                            "passed": ("date" in hb_lower and ("reset" in hb_lower or "differ" in hb_lower or "differs" in hb_lower)), 
                            "detail": f"date+reset mentioned: {('date' in hb_lower and ('reset' in hb_lower or 'differ' in hb_lower))}"}
    checks.append(check_hb_date_reset)

    # Must mention nagAfter time gate
    check_hb_nagafter = {"name": "HEARTBEAT.md mentions nagAfter time gate", 
                          "passed": "nagafter" in hb_lower or "nag_after" in hb_lower or "nagAfter" in hb_text, 
                          "detail": f"nagAfter in heartbeat: {'nagafter' in hb_lower}"}
    checks.append(check_hb_nagafter)

    # Must mention nagCount >= 3 for escalation
    check_hb_escalate = {"name": "HEARTBEAT.md mentions nagCount >= 3 escalation", 
                          "passed": ("nagcount" in hb_lower or "nag_count" in hb_lower or "nagCount" in hb_text) 
                                     and ("3" in hb_text) 
                                     and ("escalat" in hb_lower or "urgenc" in hb_lower or "intense" in hb_lower), 
                          "detail": f"nagCount+3+escalate: {('nagcount' in hb_lower)} and {'3' in hb_text} and {'escalat' in hb_lower}"}
    checks.append(check_hb_escalate)

    # Must mention days/weekday restriction skip
    check_hb_days = {"name": "HEARTBEAT.md mentions days/weekday restriction skip", 
                      "passed": ("days" in hb_lower or "weekday" in hb_lower) and ("skip" in hb_lower or "omit" in hb_lower or "not" in hb_lower), 
                      "detail": f"days+skip mentioned: {('days' in hb_lower and 'skip' in hb_lower)}"}
    checks.append(check_hb_days)

    # Must mention confirmed field / confirmation
    check_hb_confirmed = {"name": "HEARTBEAT.md mentions confirmed state check", 
                           "passed": "confirmed" in hb_lower or "confirm" in hb_lower, 
                           "detail": f"confirm in heartbeat: {'confirm' in hb_lower}"}
    checks.append(check_hb_confirmed)

    # ── Compute score ──────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 3)
    overall_passed = score >= 0.80

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))