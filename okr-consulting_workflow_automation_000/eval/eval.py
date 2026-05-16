import sys
import json
import math
from pathlib import Path

def find_report(workspace):
    """Find q3_2024_retrospective.json anywhere in workspace."""
    results = list(Path(workspace).rglob("q3_2024_retrospective.json"))
    return results[0] if results else None

def score_check(passed, name, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    checks = []

    # ── Locate the report ────────────────────────────────────────────────────
    report_path = find_report(workspace)
    if report_path is None:
        checks.append(score_check(False, "file_exists", "q3_2024_retrospective.json not found anywhere in workspace."))
        return {"passed": False, "score": 0.0, "checks": checks}
    checks.append(score_check(True, "file_exists", f"Found at {report_path}"))

    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        checks.append(score_check(False, "file_parseable", f"JSON parse error: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}
    checks.append(score_check(True, "file_parseable", "Valid JSON."))

    # ── Check top-level structure ────────────────────────────────────────────
    required_top = ["quarter", "division", "teams"]
    missing = [k for k in required_top if k not in report]
    if missing:
        checks.append(score_check(False, "top_level_structure", f"Missing top-level keys: {missing}"))
    else:
        checks.append(score_check(True, "top_level_structure", "All required top-level keys present."))

    if "teams" not in report or not isinstance(report.get("teams"), list):
        checks.append(score_check(False, "teams_list", "No 'teams' list found in report."))
        return {"passed": False, "score": 0.0, "checks": checks}

    teams_by_name = {t.get("team_name", t.get("name", "")): t for t in report["teams"]}

    # ────────────────────────────────────────────────────────────────────────
    # SCORING CHECKS
    # ────────────────────────────────────────────────────────────────────────

    # ── Helper: find a team loosely ─────────────────────────────────────────
    def find_team(keyword):
        for name, t in teams_by_name.items():
            if keyword.lower() in name.lower():
                return t
        return None

    # ── 1. Platform Engineering — KR scores on 0.0–1.0 scale ───────────────
    pe_team = find_team("Platform")
    pe_scores_correct = False
    pe_detail = "Platform Engineering team not found."
    if pe_team:
        # Flatten all KR scores
        all_kr_scores = []
        for obj in pe_team.get("objectives", []):
            for kr in obj.get("key_results", []):
                s = kr.get("score")
                if s is not None:
                    all_kr_scores.append(s)
        if all_kr_scores:
            all_in_range = all(0.0 <= s <= 1.0 for s in all_kr_scores)
            # PE-O1-KR1: target=3, final=2, score should be >= 0.7 (exceeded)
            # PE-O2-KR1: target=8, final=7.5 (met), score should be high
            if all_in_range:
                pe_scores_correct = True
                pe_detail = f"All {len(all_kr_scores)} KR scores in 0.0–1.0 range."
            else:
                pe_detail = f"Some KR scores outside 0.0–1.0 range: {all_kr_scores}"
        else:
            pe_detail = "No KR scores found on Platform Engineering team."
    checks.append(score_check(pe_scores_correct, "kr_scores_0_to_1_scale", pe_detail))

    # ── 2. Color coding thresholds ───────────────────────────────────────────
    # Check that color/status labels match SKILL.md thresholds:
    # Green: 0.7-1.0, Yellow: 0.4-0.6, Red: 0.0-0.3
    color_threshold_correct = True
    color_detail_parts = []

    def check_color_for_score(score, color_field):
        """Returns True if the color is correctly assigned per SKILL.md thresholds."""
        if score is None or color_field is None:
            return None
        color_str = str(color_field).lower()
        if score >= 0.7:
            return any(c in color_str for c in ["green", "🟢", "nailed"])
        elif score >= 0.4:
            return any(c in color_str for c in ["yellow", "🟡", "progress", "amber"])
        else:
            return any(c in color_str for c in ["red", "🔴", "miss"])

    # Spot-check: Data & ML had severe misses — check they appear as red
    dml_team = find_team("Data")
    dml_avg_is_red = False
    if dml_team:
        avg_score = dml_team.get("average_score", dml_team.get("avg_score", dml_team.get("score")))
        color = dml_team.get("color", dml_team.get("status", dml_team.get("rating", "")))
        if avg_score is not None:
            if avg_score <= 0.3:
                # Should be Red
                if color and any(c in str(color).lower() for c in ["red", "🔴", "miss"]):
                    dml_avg_is_red = True
                    color_detail_parts.append(f"Data & ML avg={avg_score:.2f} correctly labeled red/missed.")
                else:
                    color_threshold_correct = False
                    color_detail_parts.append(f"Data & ML avg={avg_score:.2f} should be RED but got color='{color}'.")
            elif avg_score <= 0.39:
                # borderline, give benefit of doubt
                dml_avg_is_red = True
                color_detail_parts.append(f"Data & ML avg={avg_score:.2f} borderline red range.")
        else:
            # Try to infer from objectives
            obj_scores = []
            for obj in dml_team.get("objectives", []):
                os_ = obj.get("score", obj.get("average_score", obj.get("avg_score")))
                if os_ is not None:
                    obj_scores.append(os_)
            if obj_scores:
                team_avg = sum(obj_scores) / len(obj_scores)
                if team_avg <= 0.35:
                    dml_avg_is_red = True
                    color_detail_parts.append(f"Data & ML inferred avg={team_avg:.2f}, acceptable.")

    # Product Management — all scores near 1.0, should be flagged as sandbagging
    pm_team = find_team("Product")
    pm_color_ok = False
    if pm_team:
        pm_color = pm_team.get("color", pm_team.get("status", pm_team.get("rating", "")))
        pm_avg = pm_team.get("average_score", pm_team.get("avg_score", pm_team.get("score")))
        if pm_avg is not None and pm_avg >= 0.85:
            # Should be green but ALSO flagged as sandbagging
            if any(c in str(pm_color).lower() for c in ["green", "🟢"]):
                pm_color_ok = True
                color_detail_parts.append(f"PM avg={pm_avg:.2f} labeled green (correct for score).")
        else:
            pm_color_ok = True  # Will be caught by sandbagging check

    checks.append(score_check(
        color_threshold_correct,
        "color_thresholds_correct",
        "; ".join(color_detail_parts) if color_detail_parts else "Could not verify color thresholds."
    ))

    # ── 3. Sandbagging Detection (PM team, all scores >= 0.9) ───────────────
    sandbagging_flagged = False
    sandbagging_detail = "Sandbagging antipattern not detected in report."
    
    report_str = json.dumps(report).lower()
    
    if pm_team:
        pm_antipatterns = pm_team.get("antipatterns", pm_team.get("flags", pm_team.get("issues", pm_team.get("warnings", []))))
        if isinstance(pm_antipatterns, list):
            for ap in pm_antipatterns:
                ap_str = str(ap).lower()
                if any(w in ap_str for w in ["sandbag", "too easy", "not ambitious", "stretch", "100%", "above 0.7", "sweet spot", "gaming"]):
                    sandbagging_flagged = True
                    sandbagging_detail = f"PM team sandbagging flagged: '{ap}'"
                    break
        
        # Also check team-level notes/recommendations
        if not sandbagging_flagged:
            for field in ["notes", "recommendations", "coaching_notes", "retrospective_notes", "lessons", "observations"]:
                val = pm_team.get(field, "")
                if isinstance(val, list):
                    val = " ".join(str(x) for x in val)
                if any(w in str(val).lower() for w in ["sandbag", "too easy", "not ambitious", "stretch", "gaming", "sweet spot"]):
                    sandbagging_flagged = True
                    sandbagging_detail = f"PM sandbagging noted in '{field}'."
                    break
    
    # Broader check: report mentions sandbagging somewhere
    if not sandbagging_flagged:
        if any(w in report_str for w in ["sandbag", "not ambitious enough", "goals were too easy", "sweet spot", "100% completion is a warning"]):
            sandbagging_flagged = True
            sandbagging_detail = "Sandbagging concern mentioned in report body."
    
    checks.append(score_check(sandbagging_flagged, "sandbagging_antipattern_detected",
                               sandbagging_detail))

    # ── 4. Structural Violations: PM team has 6 objectives (> max 5) ────────
    structural_violation_flagged = False
    structural_detail = "Objective count violation (PM has 6 > max 5) not flagged."
    
    if pm_team:
        pm_antipatterns = pm_team.get("antipatterns", pm_team.get("flags", pm_team.get("issues", pm_team.get("warnings", []))))
        if isinstance(pm_antipatterns, list):
            for ap in pm_antipatterns:
                ap_str = str(ap).lower()
                if any(w in ap_str for w in ["too many objective", "6 objective", "exceed", "max", "3-5", "limit"]):
                    structural_violation_flagged = True
                    structural_detail = f"Objective count violation flagged: '{ap}'"
                    break
        
        if not structural_violation_flagged:
            for field in ["notes", "recommendations", "coaching_notes", "retrospective_notes", "lessons", "structural_issues", "observations"]:
                val = pm_team.get(field, "")
                if isinstance(val, list):
                    val = " ".join(str(x) for x in val)
                if any(w in str(val).lower() for w in ["too many objective", "6 objective", "exceeds", "3-5 objective", "objective limit", "more than 5"]):
                    structural_violation_flagged = True
                    structural_detail = f"Objective count violation noted in '{field}'."
                    break
    
    if not structural_violation_flagged:
        if any(w in report_str for w in ["too many objective", "6 objective", "exceeds the recommended", "3-5 objective", "more than 5 objective"]):
            structural_violation_flagged = True
            structural_detail = "Objective count violation found in report body."
    
    checks.append(score_check(structural_violation_flagged, "too_many_objectives_flagged",
                               structural_detail))

    # ── 5. KR count violation: DML-O1 has 7 KRs (> max 5) ──────────────────
    kr_violation_flagged = False
    kr_violation_detail = "KR count violation (DML-O1 has 7 KRs > max 5) not flagged."
    
    if dml_team:
        for field in ["antipatterns", "flags", "issues", "warnings", "notes",
                      "recommendations", "coaching_notes", "retrospective_notes", "structural_issues", "observations"]:
            val = dml_team.get(field, "")
            if isinstance(val, list):
                val = " ".join(str(x) for x in val)
            if any(w in str(val).lower() for w in ["too many key result", "7 key result", "kr count", "3-5 key", "more than 5 key", "key result limit", "exceeds"]):
                kr_violation_flagged = True
                kr_violation_detail = f"KR count violation noted in DML team '{field}'."
                break
        
        # Also check per-objective
        if not kr_violation_flagged:
            for obj in dml_team.get("objectives", []):
                if "DML-O1" in str(obj.get("id", "")) or "diagnostic" in str(obj.get("title", "")).lower():
                    for field in ["antipatterns", "flags", "issues", "warnings", "notes", "observations"]:
                        val = obj.get(field, "")
                        if isinstance(val, list):
                            val = " ".join(str(x) for x in val)
                        if any(w in str(val).lower() for w in ["too many", "7 key", "3-5", "exceeds", "key result limit"]):
                            kr_violation_flagged = True
                            kr_violation_detail = f"KR count violation noted on DML-O1 in '{field}'."
                            break
    
    if not kr_violation_flagged:
        if any(w in report_str for w in ["too many key result", "7 key result", "key result limit", "dml-o1"]):
            kr_violation_flagged = True
            kr_violation_detail = "KR count violation mentioned in report body."
    
    checks.append(score_check(kr_violation_flagged, "too_many_key_results_flagged",
                               kr_violation_detail))

    # ── 6. Qualitative KR antipattern flagged ───────────────────────────────
    qualitative_flagged = False
    qualitative_detail = "Qualitative/unmeasurable KR antipattern not flagged."
    
    qualitative_keywords = ["qualitative", "no measurable", "no target", "unmeasurable", 
                            "not measurable", "vague", "needs a number", "missing target",
                            "improve pipeline documentation", "document all model", "implement okr tracking"]
    
    for keyword in qualitative_keywords:
        if keyword in report_str:
            qualitative_flagged = True
            qualitative_detail = f"Qualitative KR antipattern detected via keyword '{keyword}'."
            break
    
    checks.append(score_check(qualitative_flagged, "qualitative_kr_antipattern_flagged",
                               qualitative_detail))

    # ── 7. Average score computation correctness ────────────────────────────
    # Check that DML team average is below 0.4 (they had catastrophic misses)
    # DML-O1: KR scores should be very low (0.78 vs 0.91 sens = ~0.3; 210 vs 80ms = 0; 0/2 partners = 0; 0/1 papers = 0; 5.5/4 hr = ~0.5; 88/95% = ~0.5; qualitative = 0)
    # DML-O2: All very low (18/4 breaches = ~0.1; 41/90% = ~0.1; 12/3 days = 0.1)
    dml_score_correct = False
    dml_score_detail = "Could not verify DML average score."
    
    if dml_team:
        dml_avg = dml_team.get("average_score", dml_team.get("avg_score", dml_team.get("score")))
        if dml_avg is not None:
            if dml_avg <= 0.35:
                dml_score_correct = True
                dml_score_detail = f"DML avg score={dml_avg:.3f} correctly low (catastrophic misses)."
            else:
                dml_score_detail = f"DML avg score={dml_avg:.3f} seems too high — team had severe misses."
    
    checks.append(score_check(dml_score_correct, "dml_team_low_average_score", dml_score_detail))

    # ── 8. Retrospective coaching prompts / lessons learned present ──────────
    retro_present = False
    retro_detail = "No retrospective/lessons-learned section found."
    
    retro_keywords = ["lesson", "learned", "what worked", "what didn't", "next quarter",
                      "do differently", "action item", "recommend", "coaching", 
                      "if you had to do", "goal right", "execution", "retrospective"]
    
    for keyword in retro_keywords:
        if keyword in report_str:
            retro_present = True
            retro_detail = f"Retrospective content detected via keyword '{keyword}'."
            break
    
    # Also check for a top-level retro key
    for field in ["retrospective", "lessons_learned", "lessons", "retro", "next_steps", "action_items"]:
        if field in report:
            retro_present = True
            retro_detail = f"Retrospective data present in top-level field '{field}'."
            break
    
    checks.append(score_check(retro_present, "retrospective_lessons_present", retro_detail))

    # ── 9. Division-level average in sweet spot check ────────────────────────
    # The division average should reflect that PM's near-100% is a concern (sandbagging),
    # and overall division is likely not in the "sweet spot" (60-70%)
    # We just check that the report includes a division-level summary
    div_summary_present = False
    div_summary_detail = "No division-level aggregate summary found."
    
    for field in ["division_summary", "summary", "overall", "division_average",
                  "aggregate", "division_score", "division_avg"]:
        if field in report:
            div_summary_present = True
            div_summary_detail = f"Division summary found in field '{field}'."
            break
    
    # Broader check
    if not div_summary_present:
        for keyword in ["division average", "overall average", "division score", "aggregate score",
                        "novabio", "engineering & product"]:
            if keyword in report_str:
                div_summary_present = True
                div_summary_detail = f"Division-level summary detected via keyword '{keyword}'."
                break
    
    checks.append(score_check(div_summary_present, "division_level_summary_present", div_summary_detail))

    # ── 10. PE-O2-KR4 and DML-O1-KR7 and PM-O5-KR1 scored 0.0 ─────────────
    # Qualitative KRs with no target should score 0.0 (cannot measure = no score)
    qualitative_zero_score = False
    qualitative_zero_detail = "Qualitative KRs with no target not scored as 0.0."
    
    def find_kr_score(team, kr_id):
        for obj in team.get("objectives", []):
            for kr in obj.get("key_results", []):
                if kr.get("id") == kr_id:
                    return kr.get("score")
        return None
    
    scores_to_check = []
    if pe_team:
        s = find_kr_score(pe_team, "PE-O2-KR4")
        if s is not None:
            scores_to_check.append(("PE-O2-KR4", s))
    if dml_team:
        s = find_kr_score(dml_team, "DML-O1-KR7")
        if s is not None:
            scores_to_check.append(("DML-O1-KR7", s))
    if pm_team:
        s = find_kr_score(pm_team, "PM-O5-KR1")
        if s is not None:
            scores_to_check.append(("PM-O5-KR1", s))
    
    if scores_to_check:
        all_zero_or_low = all(s <= 0.1 for _, s in scores_to_check)
        if all_zero_or_low:
            qualitative_zero_score = True
            qualitative_zero_detail = f"Qualitative KRs scored low/zero: {scores_to_check}"
        else:
            qualitative_zero_detail = f"Some qualitative KRs scored too high: {scores_to_check}"
    else:
        # If KR scores aren't broken out but antipattern was flagged, partial credit
        if qualitative_flagged:
            qualitative_zero_score = True
            qualitative_zero_detail = "Qualitative KRs not individually scored but antipattern was flagged."
    
    checks.append(score_check(qualitative_zero_score, "qualitative_krs_scored_zero_or_flagged",
                               qualitative_zero_detail))

    # ── Final scoring ────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)
    
    # Must pass at minimum: file exists, parseable, scoring scale, sandbagging, 
    # structural violation, and retrospective to be considered passing
    critical_checks = ["file_exists", "file_parseable", "kr_scores_0_to_1_scale",
                       "sandbagging_antipattern_detected", "too_many_objectives_flagged",
                       "retrospective_lessons_present"]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.7

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))