import json
import sys
import math
from pathlib import Path

def epley_1rm(weight, reps):
    return weight * (1 + reps / 30)

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    fitness_path = workspace / "data" / "fitness.json"
    checks = []
    total_score = 0.0

    # ── Load fitness.json ──────────────────────────────────────────────────
    try:
        data = json.loads(fitness_path.read_text())
    except Exception as e:
        checks.append({"name": "fitness.json readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    workouts = data.get("workouts", [])
    meals = data.get("meals", [])
    prs = data.get("prs", {})
    current_week = data.get("current_week", {})
    weekly_summary = data.get("weekly_summary", [])

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 1: Monday June 2 workout logged (Upper Body A)
    # ─────────────────────────────────────────────────────────────────────
    june2_workouts = [w for w in workouts if w.get("date") == "2026-06-02"]
    has_june2 = len(june2_workouts) > 0
    checks.append({
        "name": "June 2 upper body workout logged",
        "passed": has_june2,
        "detail": f"Found {len(june2_workouts)} workout(s) dated 2026-06-02"
    })
    if has_june2:
        total_score += 0.08

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 2: Bench Press sets parsed correctly (3 sets, not 2)
    # bench 185x5 185x5 185x4 → sets: [{185,5},{185,5},{185,4}]
    # ─────────────────────────────────────────────────────────────────────
    bench_sets_ok = False
    bench_detail = "Bench Press not found in June 2 workout"
    if has_june2:
        for w in june2_workouts:
            for ex in w.get("exercises", []):
                if "bench" in ex.get("name", "").lower():
                    sets = ex.get("sets", [])
                    weights = [s.get("weight") for s in sets]
                    reps_list = [s.get("reps") for s in sets]
                    if len(sets) == 3 and weights == [185, 185, 185] and reps_list == [5, 5, 4]:
                        bench_sets_ok = True
                        bench_detail = f"Correct: 3 sets {sets}"
                    else:
                        bench_detail = f"Wrong sets: {sets}"
    checks.append({
        "name": "Bench Press sets parsed correctly (185x5, 185x5, 185x4)",
        "passed": bench_sets_ok,
        "detail": bench_detail
    })
    if bench_sets_ok:
        total_score += 0.10

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 3: Tricep Pushdown x3 shorthand → 3 sets of 50x12
    # ─────────────────────────────────────────────────────────────────────
    tricep_ok = False
    tricep_detail = "Tricep Pushdown not found in June 2 workout"
    if has_june2:
        for w in june2_workouts:
            for ex in w.get("exercises", []):
                if "tricep" in ex.get("name", "").lower() or "pushdown" in ex.get("name", "").lower():
                    sets = ex.get("sets", [])
                    if (len(sets) == 3 and
                            all(s.get("weight") == 50 for s in sets) and
                            all(s.get("reps") == 12 for s in sets)):
                        tricep_ok = True
                        tricep_detail = f"Correct: 3 sets 50x12. sets={sets}"
                    else:
                        tricep_detail = f"Wrong: sets={sets}"
    checks.append({
        "name": "Tricep Pushdown x3 shorthand parsed as 3×(50×12)",
        "passed": tricep_ok,
        "detail": tricep_detail
    })
    if tricep_ok:
        total_score += 0.12  # This is the Proprietary Trap check

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 4: Wednesday June 4 workout (Legs) logged
    # ─────────────────────────────────────────────────────────────────────
    june4_workouts = [w for w in workouts if w.get("date") == "2026-06-04"]
    has_june4 = len(june4_workouts) > 0
    checks.append({
        "name": "June 4 legs workout logged",
        "passed": has_june4,
        "detail": f"Found {len(june4_workouts)} workout(s) dated 2026-06-04"
    })
    if has_june4:
        total_score += 0.05

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 5: Epley 1RM for Bench Press correctly computed and PR updated
    # New: 185×5 → 1RM = 185*(1+5/30) = 185*1.1667 = 215.833...
    # Old PR: 210.0 → should update
    # ─────────────────────────────────────────────────────────────────────
    expected_bench_1rm = epley_1rm(185, 5)  # = 215.833...
    bench_pr = prs.get("Bench Press", {})
    bench_pr_1rm = bench_pr.get("1rm", 0)
    bench_pr_ok = abs(bench_pr_1rm - expected_bench_1rm) < 1.0  # within 1 lb tolerance
    bench_pr_detail = (f"Expected 1RM ≈ {expected_bench_1rm:.2f}, got {bench_pr_1rm}. "
                       f"Old PR was 210.0, new beats it: {expected_bench_1rm:.2f} > 210.0")
    checks.append({
        "name": f"Bench Press PR updated via Epley formula (expected ≈{expected_bench_1rm:.2f})",
        "passed": bench_pr_ok,
        "detail": bench_pr_detail
    })
    if bench_pr_ok:
        total_score += 0.12  # Core Proprietary Trap

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 6: Epley 1RM for Squat — 225x10 → 1RM = 225*(1+10/30) = 300.0
    # Old PR: 290.0 → should update to 300.0
    # ─────────────────────────────────────────────────────────────────────
    expected_squat_1rm = epley_1rm(225, 10)  # = 300.0
    squat_pr = prs.get("Squat", {})
    squat_pr_1rm = squat_pr.get("1rm", 0)
    squat_pr_ok = abs(squat_pr_1rm - expected_squat_1rm) < 1.0
    checks.append({
        "name": f"Squat PR updated via Epley formula (expected ≈{expected_squat_1rm:.2f})",
        "passed": squat_pr_ok,
        "detail": f"Expected ≈{expected_squat_1rm:.2f}, got {squat_pr_1rm}"
    })
    if squat_pr_ok:
        total_score += 0.10

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 7: Epley 1RM for Deadlift — 275x8 → 1RM = 275*(1+8/30) = 348.33...
    # Old PR: 340.0 → should update
    # ─────────────────────────────────────────────────────────────────────
    expected_dl_1rm = epley_1rm(275, 8)  # = 348.333...
    dl_pr = prs.get("Deadlift", {})
    dl_pr_1rm = dl_pr.get("1rm", 0)
    dl_pr_ok = abs(dl_pr_1rm - expected_dl_1rm) < 1.0
    checks.append({
        "name": f"Deadlift PR updated via Epley formula (expected ≈{expected_dl_1rm:.2f})",
        "passed": dl_pr_ok,
        "detail": f"Expected ≈{expected_dl_1rm:.2f}, got {dl_pr_1rm}"
    })
    if dl_pr_ok:
        total_score += 0.10

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 8: Overhead Press — 115x8 → 1RM = 115*(1+8/30) = 145.67
    # Old PR: 145.0 → 145.67 > 145.0 → SHOULD update (barely)
    # ─────────────────────────────────────────────────────────────────────
    expected_ohp_1rm = epley_1rm(115, 8)  # = 145.666...
    ohp_pr = prs.get("Overhead Press", {})
    ohp_pr_1rm = ohp_pr.get("1rm", 0)
    ohp_pr_ok = abs(ohp_pr_1rm - expected_ohp_1rm) < 1.0 and ohp_pr_1rm > 145.0
    checks.append({
        "name": f"Overhead Press PR updated (145.67 > 145.0 old PR, Epley required)",
        "passed": ohp_pr_ok,
        "detail": f"Expected ≈{expected_ohp_1rm:.2f} (must exceed 145.0), got {ohp_pr_1rm}"
    })
    if ohp_pr_ok:
        total_score += 0.08  # Edge-case trap

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 9: Tricep Pushdown gets a NEW PR entry (didn't exist before)
    # 50x12 → 1RM = 50*(1+12/30) = 50*1.4 = 70.0
    # ─────────────────────────────────────────────────────────────────────
    expected_tri_1rm = epley_1rm(50, 12)  # = 70.0
    tricep_pr_keys = [k for k in prs if "tricep" in k.lower() or "pushdown" in k.lower()]
    tricep_pr_ok = False
    tricep_pr_detail = "No Tricep Pushdown PR entry found"
    if tricep_pr_keys:
        tri_pr_1rm = prs[tricep_pr_keys[0]].get("1rm", 0)
        tricep_pr_ok = abs(tri_pr_1rm - expected_tri_1rm) < 1.0
        tricep_pr_detail = f"Expected ≈{expected_tri_1rm:.2f}, got {tri_pr_1rm}"
    checks.append({
        "name": f"New Tricep Pushdown PR created via Epley (expected ≈{expected_tri_1rm:.2f})",
        "passed": tricep_pr_ok,
        "detail": tricep_pr_detail
    })
    if tricep_pr_ok:
        total_score += 0.05

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 10: Meal entries for June 4 (protein shake + chipotle dinner)
    # ─────────────────────────────────────────────────────────────────────
    june4_meals = [m for m in meals if m.get("date") == "2026-06-04"]
    has_shake = any("shake" in m.get("description", "").lower() or "protein" in m.get("description", "").lower()
                    for m in june4_meals)
    has_chipotle = any("chipotle" in m.get("description", "").lower() for m in june4_meals)

    meal_ok = has_shake and has_chipotle
    checks.append({
        "name": "June 4 meals logged (protein shake + chipotle dinner)",
        "passed": meal_ok,
        "detail": f"Found {len(june4_meals)} meals on June 4. Shake: {has_shake}, Chipotle: {has_chipotle}"
    })
    if meal_ok:
        total_score += 0.05

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 11: Chipotle calorie estimate in reasonable range (600–750)
    # ─────────────────────────────────────────────────────────────────────
    chipotle_cal_ok = False
    chipotle_cal_detail = "Chipotle meal not found"
    for m in june4_meals:
        if "chipotle" in m.get("description", "").lower():
            cal = m.get("estimated_calories", 0)
            chipotle_cal_ok = 500 <= cal <= 900
            chipotle_cal_detail = f"Chipotle estimated_calories={cal} (expected 500–900)"
            break
    checks.append({
        "name": "Chipotle calorie estimate reasonable (500–900 cal)",
        "passed": chipotle_cal_ok,
        "detail": chipotle_cal_detail
    })
    if chipotle_cal_ok:
        total_score += 0.03

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 12: Injury note for knee sore → Friday June 6 workout
    # notes field should mention knee or rest or injury
    # ─────────────────────────────────────────────────────────────────────
    june6_workouts = [w for w in workouts if w.get("date") == "2026-06-06"]
    injury_noted = False
    injury_detail = "No June 6 workout found OR no injury note"
    for w in june6_workouts:
        notes = w.get("notes", "").lower()
        # Check at least one workout around that time has an injury mention
        if any(k in notes for k in ["knee", "sore", "injury", "rest", "pain"]):
            injury_noted = True
            injury_detail = f"Injury/rest note found: '{w.get('notes')}'"
            break
    # Also check June 4 workouts for knee note
    if not injury_noted:
        for w in june4_workouts:
            notes = w.get("notes", "").lower()
            if any(k in notes for k in ["knee", "sore", "injury", "rest", "pain"]):
                injury_noted = True
                injury_detail = f"Injury/rest note found in June 4: '{w.get('notes')}'"
                break
    checks.append({
        "name": "Knee soreness / injury noted in workout record",
        "passed": injury_noted,
        "detail": injury_detail
    })
    if injury_noted:
        total_score += 0.03

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 13: current_week.workout_count updated (was 2, now should be 5)
    # June 2 (upper), June 4 (legs), June 6 (cardio+arms) = 3 new + 2 existing = 5
    # Accept 4 or 5 (agent may recount from scratch or add incrementally)
    # ─────────────────────────────────────────────────────────────────────
    wc = current_week.get("workout_count", 0)
    wc_ok = wc >= 4  # at minimum the 3 new sessions were added
    checks.append({
        "name": "current_week.workout_count reflects new sessions (≥4)",
        "passed": wc_ok,
        "detail": f"current_week.workout_count = {wc} (expected ≥4)"
    })
    if wc_ok:
        total_score += 0.05

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 14: weekly_summary has a new entry for current week
    # ─────────────────────────────────────────────────────────────────────
    # Should have at least one entry for the week of June 2 (2026-06-02)
    june_week_summaries = [s for s in weekly_summary
                           if "2026-06" in s.get("week_start", "") or
                              s.get("workout_count", 0) >= 4]
    has_new_summary = len(weekly_summary) >= 2  # original had 1, now should have more OR be updated
    # More lenient: just check a summary entry references the june 2 week
    june2_summary = any(
        "06-02" in s.get("week_start", "") or "2026-06-0" in s.get("week_start", "")
        for s in weekly_summary
    )
    summary_ok = has_new_summary or june2_summary
    checks.append({
        "name": "Weekly summary updated with current week's data",
        "passed": summary_ok,
        "detail": (f"weekly_summary count={len(weekly_summary)}, "
                   f"june2 entry found={june2_summary}")
    })
    if summary_ok:
        total_score += 0.04

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 15: Friday June 6 cardio workout (5k, 27 min) logged
    # ─────────────────────────────────────────────────────────────────────
    has_june6 = len(june6_workouts) > 0
    june6_cardio = any(
        w.get("type") == "cardio" or
        any("run" in str(w).lower() or "5k" in str(w).lower() or "cardio" in str(w).lower()
            for _ in [w])
        for w in june6_workouts
    )
    checks.append({
        "name": "June 6 cardio workout (5k run) logged",
        "passed": has_june6,
        "detail": f"Found {len(june6_workouts)} workout(s) on June 6, cardio={june6_cardio}"
    })
    if has_june6:
        total_score += 0.05

    # ─────────────────────────────────────────────────────────────────────
    # Final scoring
    # ─────────────────────────────────────────────────────────────────────
    total_score = min(total_score, 1.0)
    passed = total_score >= 0.60

    result = {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)