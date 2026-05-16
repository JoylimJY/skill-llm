import sys
import json
import re
from pathlib import Path
from datetime import date, timedelta

def load_plan(workspace: Path):
    """Find and load the preparation_plan.json anywhere in workspace."""
    candidates = list(workspace.rglob("preparation_plan.json"))
    if not candidates:
        return None, "File preparation_plan.json not found anywhere in workspace"
    return candidates[0], None

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []

    # ── Load file ────────────────────────────────────────────────────────────
    plan_path, err = load_plan(workspace)
    if err:
        checks.append({"name": "file_exists", "passed": False, "detail": err})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "file_exists", "passed": True,
                   "detail": f"Found at {plan_path.relative_to(workspace)}"})

    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception as ex:
        checks.append({"name": "json_valid", "passed": False, "detail": str(ex)})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "json_valid", "passed": True, "detail": "Valid JSON"})

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION A – ORAL ARGUMENT STRUCTURE
    # ═══════════════════════════════════════════════════════════════════════

    # A1: Total oral time ≤ 21 minutes
    try:
        total_minutes = float(plan.get("total_oral_minutes", plan.get("total_time_minutes", 0)))
        a1_pass = 18 <= total_minutes <= 21
        checks.append({"name": "A1_total_time_18_to_21_min",
                        "passed": a1_pass,
                        "detail": f"total_oral_minutes={total_minutes} (must be 18–21)"})
    except Exception as ex:
        checks.append({"name": "A1_total_time_18_to_21_min", "passed": False, "detail": str(ex)})

    # A2: Two claims each ~10 min (8–12 min acceptable)
    try:
        claims = plan.get("claims", [])
        a2_pass = True
        detail_parts = []
        if len(claims) != 2:
            a2_pass = False
            detail_parts.append(f"Expected 2 claims, found {len(claims)}")
        else:
            for c in claims:
                t = float(c.get("allocated_minutes", c.get("time_minutes", 0)))
                if not (8 <= t <= 12):
                    a2_pass = False
                detail_parts.append(f"Claim '{c.get('name','?')}' = {t} min")
        checks.append({"name": "A2_each_claim_approx_10_min",
                        "passed": a2_pass,
                        "detail": "; ".join(detail_parts) if detail_parts else "OK"})
    except Exception as ex:
        checks.append({"name": "A2_each_claim_approx_10_min", "passed": False, "detail": str(ex)})

    # A3: Claim One argument ordering
    # CORRECT order per SKILL.md logic applied to this case:
    # C1-B (ARBITRARY DETENTION – strongest, substantive) FIRST
    # C1-D (FAIR TRIAL elements – broader doctrinal bridge, and explicitly "before reason of arrest" per Kafker-style rule)
    # C1-C (REASONS FOR ARREST – narrower substantive)
    # C1-A (LAWFULNESS – procedural, less important)
    # C1-E (DURATION – factual support, can be woven in or last)
    # Key check: C1-B before C1-A, and C1-D before C1-C (per the explicit Kafker example in SKILL.md)
    try:
        claim1 = next((c for c in claims if "one" in c.get("name","").lower() or "liberty" in c.get("name","").lower() or "1" in str(c.get("name",""))), None)
        if claim1 is None and claims:
            claim1 = claims[0]
        
        if claim1 is None:
            checks.append({"name": "A3_claim1_argument_ordering", "passed": False,
                            "detail": "Claim 1 not found in plan"})
        else:
            sub_args = claim1.get("sub_arguments", claim1.get("arguments", []))
            # Normalize argument identifiers
            labels = []
            for sa in sub_args:
                raw = str(sa.get("id", sa.get("label", sa.get("name", "")))).upper()
                labels.append(raw)
            
            detail = f"Claim 1 argument order: {labels}"
            
            # Check 1: C1-B (arbitrary/ARBITRARY) must appear before C1-A (lawfulness/LAWFUL)
            def find_idx(labels, keywords):
                for i, lbl in enumerate(labels):
                    if any(k.upper() in lbl for k in keywords):
                        return i
                return -1
            
            idx_arbitrary = find_idx(labels, ["C1-B","ARBITRARY","ARBITRAR"])
            idx_lawful    = find_idx(labels, ["C1-A","LAWFUL","LAWFULNESS"])
            idx_fairtrial = find_idx(labels, ["C1-D","FAIR","FAIR_TRIAL","FAIRTRIAL"])
            idx_reasons   = find_idx(labels, ["C1-C","REASON","INFORMED","ARREST_REASON"])

            order_ok = True
            order_details = []

            if idx_arbitrary == -1 or idx_lawful == -1:
                order_ok = False
                order_details.append("Could not find both ARBITRARY and LAWFULNESS arguments")
            elif idx_arbitrary > idx_lawful:
                order_ok = False
                order_details.append("ARBITRARY must come BEFORE LAWFULNESS (strongest before procedural)")
            else:
                order_details.append(f"ARBITRARY(pos {idx_arbitrary}) before LAWFULNESS(pos {idx_lawful}) ✓")

            if idx_fairtrial != -1 and idx_reasons != -1:
                if idx_fairtrial > idx_reasons:
                    order_ok = False
                    order_details.append("FAIR_TRIAL must come BEFORE REASONS_FOR_ARREST (per Kafker-style rule in SKILL.md)")
                else:
                    order_details.append(f"FAIR_TRIAL(pos {idx_fairtrial}) before REASONS(pos {idx_reasons}) ✓")

            checks.append({"name": "A3_claim1_argument_ordering",
                            "passed": order_ok,
                            "detail": detail + " | " + "; ".join(order_details)})
    except Exception as ex:
        checks.append({"name": "A3_claim1_argument_ordering", "passed": False, "detail": str(ex)})

    # A4: Claim Two ordering – C2-B (risk of torture, VERY STRONG) must be first;
    # C2-D (burden of proof) must come directly after C2-B (before C2-C procedural effective remedy);
    # C2-A (diplomatic assurances, WEAK) should either be absent or last
    try:
        claim2 = next((c for c in claims if "two" in c.get("name","").lower() or "refoul" in c.get("name","").lower() or "2" in str(c.get("name",""))), None)
        if claim2 is None and len(claims) > 1:
            claim2 = claims[1]
        
        if claim2 is None:
            checks.append({"name": "A4_claim2_argument_ordering", "passed": False,
                            "detail": "Claim 2 not found in plan"})
        else:
            sub_args2 = claim2.get("sub_arguments", claim2.get("arguments", []))
            labels2 = []
            for sa in sub_args2:
                raw = str(sa.get("id", sa.get("label", sa.get("name","")))).upper()
                labels2.append(raw)
            
            detail2 = f"Claim 2 argument order: {labels2}"
            
            def find_idx2(labels, keywords):
                for i, lbl in enumerate(labels):
                    if any(k.upper() in lbl for k in keywords):
                        return i
                return -1
            
            idx_torture   = find_idx2(labels2, ["C2-B","RISK","TORTURE","WELL-ESTABLISHED","FACTUAL"])
            idx_burden    = find_idx2(labels2, ["C2-D","BURDEN","PROOF","STANDARD","EVIDENTIARY"])
            idx_remedy    = find_idx2(labels2, ["C2-C","REMEDY","EFFECTIVE_REMEDY","REMEDIES"])
            idx_diplom    = find_idx2(labels2, ["C2-A","DIPLOMATIC","ASSURANCE"])

            order2_ok = True
            order2_details = []

            # Torture (C2-B) must be first (or among the first)
            if idx_torture == -1:
                order2_ok = False
                order2_details.append("RISK_OF_TORTURE argument not found")
            elif idx_torture > 0:
                order2_ok = False
                order2_details.append(f"RISK_OF_TORTURE must be FIRST (currently pos {idx_torture})")
            else:
                order2_details.append("RISK_OF_TORTURE is first ✓")

            # Burden (C2-D) must come before remedy (C2-C)
            if idx_burden != -1 and idx_remedy != -1:
                if idx_burden > idx_remedy:
                    order2_ok = False
                    order2_details.append("BURDEN_OF_PROOF must come before EFFECTIVE_REMEDY (bridge before procedural)")
                else:
                    order2_details.append(f"BURDEN(pos {idx_burden}) before REMEDY(pos {idx_remedy}) ✓")

            # Diplomatic assurances – if included, must be LAST (weakest)
            if idx_diplom != -1 and len(labels2) > 0:
                if idx_diplom != len(labels2) - 1:
                    order2_ok = False
                    order2_details.append(f"DIPLOMATIC_ASSURANCES is weak and must appear LAST if included (currently pos {idx_diplom}/{len(labels2)-1})")
                else:
                    order2_details.append("DIPLOMATIC_ASSURANCES placed last (weakest) ✓")

            checks.append({"name": "A4_claim2_argument_ordering",
                            "passed": order2_ok,
                            "detail": detail2 + " | " + "; ".join(order2_details)})
    except Exception as ex:
        checks.append({"name": "A4_claim2_argument_ordering", "passed": False, "detail": str(ex)})

    # A5: Weaknesses – plan should NOT proactively address every weakness
    # The plan should explicitly note that W1 (national security) and W3 (jurisdiction) 
    # are only addressed if asked, and C2-A is deprioritized
    try:
        weaknesses_section = plan.get("weakness_strategy", plan.get("weaknesses", {}))
        plan_str = json.dumps(plan).lower()
        
        # Check if plan explicitly says NOT to proactively cover all weaknesses
        covers_everything = False
        proactive_phrases = ["address all weaknesses", "cover every weakness", 
                             "mention all weak points", "proactively cover all"]
        for phrase in proactive_phrases:
            if phrase in plan_str:
                covers_everything = True
        
        selective_phrases = ["only if asked", "only when asked", "not proactively", 
                             "skip if not asked", "do not volunteer", "avoid unless",
                             "if judge asks", "not necessary to mention",
                             "不需要主动", "选择性"]
        has_selective = any(phrase in plan_str for phrase in selective_phrases)
        
        a5_pass = has_selective and not covers_everything
        checks.append({"name": "A5_selective_weakness_coverage",
                        "passed": a5_pass,
                        "detail": (f"Plan {'contains' if has_selective else 'lacks'} selective weakness strategy; "
                                   f"covers_everything={covers_everything}")})
    except Exception as ex:
        checks.append({"name": "A5_selective_weakness_coverage", "passed": False, "detail": str(ex)})

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION B – MOCK SESSION SCHEDULE
    # ═══════════════════════════════════════════════════════════════════════

    try:
        moot_schedule = plan.get("mock_schedule", plan.get("moot_schedule", plan.get("practice_schedule", [])))
        
        if not moot_schedule:
            checks.append({"name": "B1_mock_schedule_exists", "passed": False,
                            "detail": "No mock_schedule / moot_schedule / practice_schedule found in plan"})
        else:
            checks.append({"name": "B1_mock_schedule_exists", "passed": True,
                            "detail": f"Found {len(moot_schedule)} mock sessions scheduled"})
    except Exception as ex:
        moot_schedule = []
        checks.append({"name": "B1_mock_schedule_exists", "passed": False, "detail": str(ex)})

    # B2: One session immediately before each competition round
    try:
        competition_dates_str = ["2025-04-05", "2025-04-06", "2025-04-07",
                                 "2025-04-25"]  # day before I1 (last available before intl rounds)
        
        session_dates = []
        for s in moot_schedule:
            d_raw = s.get("date", s.get("session_date", ""))
            if d_raw:
                try:
                    session_dates.append(date.fromisoformat(str(d_raw)[:10]))
                except:
                    pass

        pre_round_checks = []
        b2_pass = True
        for comp_date_str in competition_dates_str[:4]:  # Check regional rounds + pre-intl
            comp_date = date.fromisoformat(comp_date_str)
            # Session within 2 days before competition day counts as "before"
            covered = any(0 <= (comp_date - sd).days <= 2 for sd in session_dates)
            if comp_date_str in ["2025-04-05", "2025-04-06", "2025-04-07"]:
                # For regional rounds, at minimum a session 1-2 days before first round
                if comp_date_str == "2025-04-05":
                    if not covered:
                        b2_pass = False
                    pre_round_checks.append(f"Pre-regional({comp_date_str}): {'✓' if covered else '✗'}")
            else:
                if not covered:
                    b2_pass = False
                pre_round_checks.append(f"Pre-intl({comp_date_str}): {'✓' if covered else '✗'}")
        
        checks.append({"name": "B2_session_before_each_round",
                        "passed": b2_pass,
                        "detail": "; ".join(pre_round_checks)})
    except Exception as ex:
        checks.append({"name": "B2_session_before_each_round", "passed": False, "detail": str(ex)})

    # B3: Early phase frequency (every 2 days); Late phase frequency (every 1 day)
    # First available: 2025-03-10; Regional starts: 2025-04-05
    # "Late phase" = within ~2 weeks of first competition = from ~2025-03-22 onward
    # Early phase: 2025-03-10 to 2025-03-21 (should have sessions ~every 2 days)
    # Late phase: 2025-03-22 to 2025-04-04 (should have sessions ~every 1 day, or close)
    try:
        session_dates_sorted = sorted(set(session_dates))
        
        early_start = date(2025, 3, 10)
        early_end   = date(2025, 3, 21)
        late_start  = date(2025, 3, 22)
        late_end    = date(2025, 4, 4)

        early_sessions = [d for d in session_dates_sorted if early_start <= d <= early_end]
        late_sessions  = [d for d in session_dates_sorted if late_start  <= d <= late_end]

        # Early phase: should span the early window with ~2-day gaps
        early_ok = len(early_sessions) >= 3  # at minimum a few sessions
        
        # Late phase: should have more density
        late_ok = len(late_sessions) >= 5  # should be daily-ish for 14-day window
        
        # Also check: early sessions aren't daily (that would be wrong)
        if len(early_sessions) >= 2:
            early_gaps = [(early_sessions[i+1] - early_sessions[i]).days 
                          for i in range(len(early_sessions)-1)]
            avg_early_gap = sum(early_gaps) / len(early_gaps) if early_gaps else 0
            # Early gap should be ~2 days (allow 1-3)
            early_gap_ok = all(1 <= g <= 3 for g in early_gaps)
        else:
            early_gap_ok = False
            avg_early_gap = 0

        b3_pass = early_ok and late_ok and early_gap_ok
        checks.append({"name": "B3_frequency_early_vs_late_phase",
                        "passed": b3_pass,
                        "detail": (f"Early sessions(Mar10-21): {[str(d) for d in early_sessions]}, "
                                   f"avg gap={avg_early_gap:.1f}d, gap_ok={early_gap_ok}; "
                                   f"Late sessions(Mar22-Apr4): {len(late_sessions)} sessions, late_ok={late_ok}")})
    except Exception as ex:
        checks.append({"name": "B3_frequency_early_vs_late_phase", "passed": False, "detail": str(ex)})

    # B4: No mandated high-frequency schedule when gap > 30 days
    # First available 2025-03-10; first competition 2025-04-05 = 26 days, < 30 days
    # So high-frequency IS appropriate here. This check verifies agent understood the rule
    # by NOT applying the "skip high frequency" exception (since 26 days < 30 days threshold).
    try:
        first_practice = date(2025, 3, 10)
        first_competition = date(2025, 4, 5)
        gap_days = (first_competition - first_practice).days  # = 26 days

        # The plan should show a frequency schedule starting from ~Mar 10 (not skipping early phase)
        # because 26 days < 30 days threshold
        has_early_phase = len([d for d in session_dates_sorted 
                                if date(2025,3,10) <= d <= date(2025,3,21)]) >= 2
        
        b4_pass = has_early_phase
        checks.append({"name": "B4_30day_rule_correctly_not_triggered",
                        "passed": b4_pass,
                        "detail": (f"Gap first_practice to first_competition = {gap_days} days (<30), "
                                   f"so high-frequency schedule SHOULD start immediately. "
                                   f"Has early sessions: {has_early_phase}")})
    except Exception as ex:
        checks.append({"name": "B4_30day_rule_correctly_not_triggered", "passed": False, "detail": str(ex)})

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION C – MOCK SESSION PERSONNEL CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════

    # C1: Each session must have exactly 1 oralist
    # C2: Each session must have 1-3 judges (who record improvable points)
    # C3: Each session must have a timekeeper
    # C4: Each session must have a question recorder (separate role)
    try:
        if not moot_schedule:
            checks.append({"name": "C1_C2_C3_C4_session_personnel", "passed": False,
                            "detail": "No sessions to evaluate"})
        else:
            personnel_issues = []
            sessions_checked = 0
            
            for i, session in enumerate(moot_schedule[:5]):  # check first 5 sessions
                roles = session.get("roles", session.get("personnel", session.get("staff", {})))
                
                if isinstance(roles, dict):
                    oralists   = roles.get("oralist", roles.get("oralists", roles.get("speaker", [])))
                    judges     = roles.get("judges", roles.get("judge", []))
                    timekeeper = roles.get("timekeeper", roles.get("timer", None))
                    qrecorder  = roles.get("question_recorder", roles.get("recorder", 
                                           roles.get("questions_recorder", None)))
                    
                    # Normalize to lists
                    if isinstance(oralists, str): oralists = [oralists]
                    if isinstance(judges, str):   judges   = [judges]
                    
                    n_oralists = len(oralists) if isinstance(oralists, list) else (1 if oralists else 0)
                    n_judges   = len(judges)   if isinstance(judges, list)   else (1 if judges   else 0)
                    
                    if n_oralists != 1:
                        personnel_issues.append(f"Session {i+1}: oralists={n_oralists} (must be 1)")
                    if not (1 <= n_judges <= 3):
                        personnel_issues.append(f"Session {i+1}: judges={n_judges} (must be 1-3)")
                    if not timekeeper:
                        personnel_issues.append(f"Session {i+1}: missing timekeeper")
                    if not qrecorder:
                        personnel_issues.append(f"Session {i+1}: missing question_recorder")
                    sessions_checked += 1
                elif isinstance(roles, list):
                    # roles as list of {role: ..., person: ...}
                    role_names = [str(r.get("role","")).lower() for r in roles]
                    n_oralists = sum(1 for r in role_names if "oralist" in r or "speaker" in r)
                    n_judges   = sum(1 for r in role_names if "judge" in r)
                    has_timer  = any("time" in r for r in role_names)
                    has_qrec   = any("recorder" in r or "question" in r for r in role_names)
                    
                    if n_oralists != 1:
                        personnel_issues.append(f"Session {i+1}: oralists={n_oralists} (must be 1)")
                    if not (1 <= n_judges <= 3):
                        personnel_issues.append(f"Session {i+1}: judges={n_judges} (must be 1-3)")
                    if not has_timer:
                        personnel_issues.append(f"Session {i+1}: missing timekeeper")
                    if not has_qrec:
                        personnel_issues.append(f"Session {i+1}: missing question_recorder")
                    sessions_checked += 1
                else:
                    personnel_issues.append(f"Session {i+1}: unrecognized roles format ({type(roles).__name__})")
            
            c_pass = len(personnel_issues) == 0 and sessions_checked > 0
            checks.append({"name": "C1_C2_C3_C4_session_personnel",
                            "passed": c_pass,
                            "detail": (f"Checked {sessions_checked} sessions. "
                                       + ("; ".join(personnel_issues) if personnel_issues else "All personnel configs valid ✓"))})
    except Exception as ex:
        checks.append({"name": "C1_C2_C3_C4_session_personnel", "passed": False, "detail": str(ex)})

    # C5: Judges must record improvable points (check that plan mentions this requirement)
    try:
        plan_str_lower = json.dumps(plan).lower()
        judge_record_phrases = [
            "record", "note down", "write down", "記录", "记录",
            "improvable", "improvement", "feedback", "毛病", "问题点",
            "can_improve", "points_to_improve", "judge_notes", "judge_feedback"
        ]
        has_judge_recording = any(p in plan_str_lower for p in judge_record_phrases)
        checks.append({"name": "C5_judges_record_feedback",
                        "passed": has_judge_recording,
                        "detail": "Judges must document improvable points per SKILL.md. "
                                  + ("Found evidence of this requirement ✓" if has_judge_recording
                                     else "No mention of judges recording feedback ✗")})
    except Exception as ex:
        checks.append({"name": "C5_judges_record_feedback", "passed": False, "detail": str(ex)})

    # ── Final score ──────────────────────────────────────────────────────────
    total   = len(checks)
    passed  = sum(1 for c in checks if c["passed"])
    score   = round(passed / total, 3) if total > 0 else 0.0
    overall = score >= 0.75 and checks[0]["passed"] and checks[1]["passed"]

    return {
        "passed": overall,
        "score":  score,
        "checks": checks,
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))