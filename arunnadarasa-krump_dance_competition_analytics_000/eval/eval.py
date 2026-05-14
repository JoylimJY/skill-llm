import sys
import json
import math
from pathlib import Path

def find_report(workspace):
    """Search for battle_report.json anywhere in workspace."""
    results = list(Path(workspace).rglob("battle_report.json"))
    return results[0] if results else None

def compute_expected():
    """Compute all expected values from scratch using SKILL.md rules."""
    
    # Move library data from SKILL.md
    move_library = {
        "Groove": {"category": "Foundation", "difficulty": "Intermediate", "body_parts": ["Full Body"], "timing": 1},
        "Travelling": {"category": "Foundation", "difficulty": "Beginner", "body_parts": ["Full Body"], "timing": 1},
        "Stomp": {"category": "Foundation", "difficulty": "Beginner", "body_parts": ["Feet"], "timing": 1},
        "Jab": {"category": "Foundation", "difficulty": "Beginner", "body_parts": ["Arms"], "timing": 1},
        "In-Between": {"category": "Concepts", "difficulty": "Advanced", "body_parts": ["Full Body"], "timing": 0.5},
        "Chest Pop": {"category": "Foundation", "difficulty": "Beginner", "body_parts": ["Core"], "timing": 1},
        "Arm Swing": {"category": "Foundation", "difficulty": "Beginner", "body_parts": ["Arms"], "timing": 1},
        "Arm Swing – Snatch": {"category": "Foundation", "difficulty": "Beginner", "body_parts": ["Arms"], "timing": 1},  # inherits Arm Swing timing
        "Arm Swing – Smash": {"category": "Foundation", "difficulty": "Beginner", "body_parts": ["Arms"], "timing": 1},  # inherits Arm Swing timing
        "Arm Swing – Whip": {"category": "Foundation", "difficulty": "Beginner", "body_parts": ["Arms"], "timing": 1},  # inherits Arm Swing timing
        "Rumble": {"category": "Power", "difficulty": "Advanced", "body_parts": ["Full Body"], "timing": 1},
        "Get Off": {"category": "Power", "difficulty": "Advanced", "body_parts": ["Full Body"], "timing": 4},
        "Kill Off": {"category": "Power", "difficulty": "Advanced", "body_parts": ["Full Body"], "timing": "End"},
        "Buck Hop": {"category": "Foundation", "difficulty": "Beginner", "body_parts": ["Full Body"], "timing": 1},
        "Textures": {"category": "Concepts", "difficulty": "Advanced", "body_parts": ["Full Body"], "timing": 1},
        "Textures – Fire": {"category": "Concepts", "difficulty": "Advanced", "body_parts": ["Full Body"], "timing": 0.5},  # per Combo 2 style in sequences
        "Textures – Water": {"category": "Concepts", "difficulty": "Advanced", "body_parts": ["Full Body"], "timing": 1},
        "Textures – Earth": {"category": "Concepts", "difficulty": "Advanced", "body_parts": ["Full Body"], "timing": 1},
        "Wobble": {"category": "Power", "difficulty": "Advanced", "body_parts": ["Core"], "timing": 1},
        "Focus Point": {"category": "Concepts", "difficulty": "Intermediate", "body_parts": ["Head"], "timing": 1},
        "Pose": {"category": "Foundation", "difficulty": "Beginner", "body_parts": ["Full Body"], "timing": 1},
        "Pose + Arm Placements": {"category": "Foundation", "difficulty": "Advanced", "body_parts": ["Full Body", "Arms"], "timing": 2},
        "3D": {"category": "Concepts", "difficulty": "Intermediate", "body_parts": ["Full Body"], "timing": 1},
        "Zones": {"category": "Concepts", "difficulty": "Beginner", "body_parts": ["Full Body"], "timing": 1},
        "Footwork": {"category": "Foundation", "difficulty": "Intermediate", "body_parts": ["Feet"], "timing": 1},
    }

    # Tournament scoring weights from SKILL.md
    weights = {
        "kill_off": 0.15,
        "material": 0.15,
        "musicality": 0.15,
        "combo": 0.15,
        "travelling": 0.15,
        "get_off": 0.15,
        "basics": 0.10,
    }

    # Competitor data
    competitors = [
        {
            "name": "Baby Tight Eyez",
            "sequence": "Groove (1) -> Travelling (1) -> Stomp (1) -> Jab (0.5) -> In-Between (0.5) -> Chest Pop (1) -> Arm Swing – Snatch (1) -> Rumble (1) -> Get Off (4) -> Kill Off (End)",
            "judge_scores": {
                "kill_off": 5, "material": 4, "musicality": 3,
                "combo": 4, "travelling": 5, "get_off": 5, "basics": 4
            }
        },
        {
            "name": "Lil Slayer",
            "sequence": "Groove (1) -> Buck Hop (1) -> Stomp (1) -> Jab (0.5) -> Textures – Fire (0.5) -> Chest Pop (1) -> Wobble (1) -> Focus Point (1) -> Pose + Arm Placements (2)",
            "judge_scores": {
                "kill_off": 3, "material": 5, "musicality": 5,
                "combo": 4, "travelling": 2, "get_off": 3, "basics": 5
            }
        },
        {
            "name": "Young Miss Prissy",
            "sequence": "Groove (1) -> 3D (1) -> Stomp (1) -> Arm Swing – Smash (1) -> In-Between (0.5) -> Chest Pop (1) -> Zones (1) -> Footwork (1) -> Wobble (1) -> Pose + Arm Placements (2)",
            "judge_scores": {
                "kill_off": 4, "material": 4, "musicality": 4,
                "combo": 5, "travelling": 3, "get_off": 4, "basics": 3
            }
        },
    ]

    expected_results = {}
    for comp in competitors:
        # Parse sequence and compute beat map
        parts = [p.strip() for p in comp["sequence"].split("->")]
        beat_map = []
        current_start = 0.0
        for part in parts:
            # Extract move name and timing
            paren_start = part.rfind("(")
            paren_end = part.rfind(")")
            if paren_start == -1 or paren_end == -1:
                continue
            move_name = part[:paren_start].strip()
            timing_str = part[paren_start+1:paren_end].strip()
            
            if timing_str.lower() == "end":
                timing = "End"
                start = "End"
            else:
                timing = float(timing_str)
                start = current_start
            
            beat_map.append({
                "move": move_name,
                "timing": timing,
                "start_beat": start,
            })
            
            if timing != "End":
                current_start += timing
        
        # Compute weighted score
        scores = comp["judge_scores"]
        total = sum(scores[k] * weights[k] for k in weights)
        
        expected_results[comp["name"]] = {
            "beat_map": beat_map,
            "total_score": round(total, 4),
        }
    
    # Rankings
    sorted_competitors = sorted(expected_results.items(), key=lambda x: x[1]["total_score"], reverse=True)
    expected_results["_ranking"] = [name for name, _ in sorted_competitors]
    
    return expected_results, move_library, weights

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = []
    
    # Find report
    report_path = find_report(workspace)
    if report_path is None:
        checks.append({"name": "report_exists", "passed": False, "detail": "battle_report.json not found anywhere in workspace"})
        score = 0.0
        print(json.dumps({"passed": False, "score": score, "checks": checks}))
        return
    
    checks.append({"name": "report_exists", "passed": True, "detail": f"Found at {report_path}"})
    
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "report_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    checks.append({"name": "report_parseable", "passed": True, "detail": "Valid JSON"})
    
    expected, move_library, weights = compute_expected()
    
    # ---- CHECK 1: Beat map for Baby Tight Eyez (most complex: includes Get Off=4, Kill Off=End, In-Between=0.5) ----
    bte_name = "Baby Tight Eyez"
    bte_expected_map = expected[bte_name]["beat_map"]
    
    try:
        # Find this competitor's data in report
        bte_data = None
        if isinstance(report, dict):
            for k, v in report.items():
                if bte_name.lower() in str(k).lower() or (isinstance(v, dict) and bte_name.lower() in str(v).get("name", "").lower()):
                    bte_data = v
                    break
            if bte_data is None and bte_name in report:
                bte_data = report[bte_name]
            # Try competitors list
            if bte_data is None and "competitors" in report:
                for c in report["competitors"]:
                    if bte_name.lower() in str(c.get("name", "")).lower():
                        bte_data = c
                        break
        
        if bte_data is None:
            checks.append({"name": "beat_map_baby_tight_eyez", "passed": False, "detail": f"Could not find {bte_name} in report"})
        else:
            # Check In-Between start beat = 4.5 (Groove1 + Travelling1 + Stomp1 + Jab0.5 = 3.5)
            bm = bte_data.get("beat_map", bte_data.get("choreography", bte_data.get("moves", [])))
            in_between_correct = False
            get_off_correct = False
            kill_off_correct = False
            snatch_timing_correct = False
            
            for entry in bm:
                move = str(entry.get("move", entry.get("name", ""))).strip()
                start = entry.get("start_beat", entry.get("start", entry.get("beat", None)))
                timing = entry.get("timing", entry.get("duration", None))
                
                if "In-Between" in move or "in-between" in move.lower() or "in_between" in move.lower():
                    # Expected start: 0(Groove) + 1(Travelling) + 1(Stomp) + 0.5(Jab) = 3.5? 
                    # Wait: Groove(1) -> Travelling(1) -> Stomp(1) -> Jab(0.5) -> In-Between
                    # starts: Groove=0, Travelling=1, Stomp=2, Jab=3, In-Between=3.5
                    expected_ib_start = 3.5
                    if start is not None and abs(float(start) - expected_ib_start) < 0.01:
                        in_between_correct = True
                
                if "Get Off" in move or "get_off" in move.lower() or "getoff" in move.lower():
                    # After In-Between: 3.5 + 0.5(In-Between) = 4 (Chest Pop)
                    # 4 + 1(Chest Pop) = 5 (Arm Swing-Snatch)
                    # 5 + 1 = 6 (Rumble)
                    # 6 + 1 = 7 (Get Off)
                    expected_go_start = 7.0
                    if start is not None and abs(float(start) - expected_go_start) < 0.01:
                        get_off_correct = True
                    # Also check timing = 4
                    if timing is not None and str(timing) == "4" or (isinstance(timing, (int, float)) and abs(float(timing) - 4.0) < 0.01):
                        pass  # will check separately
                
                if "Kill Off" in move or "kill_off" in move.lower() or "killoff" in move.lower():
                    # Kill Off start should be "End" (not a number)
                    if str(start).lower() == "end" or str(timing).lower() == "end":
                        kill_off_correct = True
                
                if "Arm Swing" in move and ("Snatch" in move or "snatch" in move.lower()):
                    # Must have timing = 1 (inherited from Arm Swing, not from Snatch which is also 1 but agent must know inheritance)
                    if timing is not None and (str(timing) == "1" or (isinstance(timing, (int, float)) and abs(float(timing) - 1.0) < 0.01)):
                        snatch_timing_correct = True
            
            bm_passed = in_between_correct and get_off_correct and kill_off_correct
            detail = (f"In-Between@3.5={in_between_correct}, GetOff@7.0={get_off_correct}, "
                     f"KillOff=End={kill_off_correct}, ArmSwingSnatch_timing1={snatch_timing_correct}")
            checks.append({"name": "beat_map_baby_tight_eyez", "passed": bm_passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "beat_map_baby_tight_eyez", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 2: Beat map for Lil Slayer (Textures-Fire at 0.5, Pose+Arm Placements at 2) ----
    try:
        ls_name = "Lil Slayer"
        ls_data = None
        if isinstance(report, dict):
            for k, v in report.items():
                if ls_name.lower() in str(k).lower() or (isinstance(v, dict) and ls_name.lower() in str(v).get("name", "").lower()):
                    ls_data = v
                    break
            if ls_data is None and ls_name in report:
                ls_data = report[ls_name]
            if ls_data is None and "competitors" in report:
                for c in report["competitors"]:
                    if ls_name.lower() in str(c.get("name", "")).lower():
                        ls_data = c
                        break
        
        if ls_data is None:
            checks.append({"name": "beat_map_lil_slayer", "passed": False, "detail": f"Could not find {ls_name} in report"})
        else:
            bm = ls_data.get("beat_map", ls_data.get("choreography", ls_data.get("moves", [])))
            textures_correct = False
            pose_ap_start_correct = False
            pose_ap_timing_correct = False
            
            for entry in bm:
                move = str(entry.get("move", entry.get("name", ""))).strip()
                start = entry.get("start_beat", entry.get("start", entry.get("beat", None)))
                timing = entry.get("timing", entry.get("duration", None))
                
                if ("Textures" in move and "Fire" in move) or ("textures" in move.lower() and "fire" in move.lower()):
                    # Groove(1)->BuckHop(1)->Stomp(1)->Jab(0.5) -> Textures-Fire starts at 3.5
                    expected_tf_start = 3.5
                    if start is not None and abs(float(start) - expected_tf_start) < 0.01:
                        textures_correct = True
                
                if "Pose" in move and "Arm Placement" in move:
                    # Groove(1)+BuckHop(1)+Stomp(1)+Jab(0.5)+Textures-Fire(0.5)+ChestPop(1)+Wobble(1)+FocusPoint(1) = 7.0
                    expected_pose_start = 7.0
                    if start is not None and abs(float(start) - expected_pose_start) < 0.01:
                        pose_ap_start_correct = True
                    if timing is not None and (str(timing) == "2" or (isinstance(timing, (int, float)) and abs(float(timing) - 2.0) < 0.01)):
                        pose_ap_timing_correct = True
            
            bm_passed = textures_correct and pose_ap_start_correct and pose_ap_timing_correct
            detail = (f"TexturesFire@3.5={textures_correct}, PoseAP@7.0={pose_ap_start_correct}, "
                     f"PoseAP_timing2={pose_ap_timing_correct}")
            checks.append({"name": "beat_map_lil_slayer", "passed": bm_passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "beat_map_lil_slayer", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 3: Weighted scores computed correctly ----
    expected_scores = {
        "Baby Tight Eyez": expected["Baby Tight Eyez"]["total_score"],
        "Lil Slayer": expected["Lil Slayer"]["total_score"],
        "Young Miss Prissy": expected["Young Miss Prissy"]["total_score"],
    }
    
    # Baby Tight Eyez: 5*0.15 + 4*0.15 + 3*0.15 + 4*0.15 + 5*0.15 + 5*0.15 + 4*0.10
    # = 0.75 + 0.60 + 0.45 + 0.60 + 0.75 + 0.75 + 0.40 = 4.30
    # Lil Slayer: 3*0.15 + 5*0.15 + 5*0.15 + 4*0.15 + 2*0.15 + 3*0.15 + 5*0.10
    # = 0.45 + 0.75 + 0.75 + 0.60 + 0.30 + 0.45 + 0.50 = 3.80
    # Young Miss Prissy: 4*0.15 + 4*0.15 + 4*0.15 + 5*0.15 + 3*0.15 + 4*0.15 + 3*0.10
    # = 0.60 + 0.60 + 0.60 + 0.75 + 0.45 + 0.60 + 0.30 = 3.90
    
    score_checks_passed = 0
    for comp_name, expected_score in expected_scores.items():
        try:
            comp_data = None
            if isinstance(report, dict):
                for k, v in report.items():
                    if comp_name.lower() in str(k).lower() or (isinstance(v, dict) and comp_name.lower() in str(v).get("name", "").lower()):
                        comp_data = v
                        break
                if comp_data is None and comp_name in report:
                    comp_data = report[comp_name]
                if comp_data is None and "competitors" in report:
                    for c in report["competitors"]:
                        if comp_name.lower() in str(c.get("name", "")).lower():
                            comp_data = c
                            break
            
            if comp_data is None:
                checks.append({"name": f"score_{comp_name.replace(' ','_')}", "passed": False, "detail": "Competitor not found in report"})
                continue
            
            actual_score = comp_data.get("total_score", comp_data.get("score", comp_data.get("weighted_score", None)))
            if actual_score is None:
                checks.append({"name": f"score_{comp_name.replace(' ','_')}", "passed": False, "detail": f"No score field found. Expected {expected_score}"})
                continue
            
            passed = abs(float(actual_score) - expected_score) < 0.02
            score_checks_passed += (1 if passed else 0)
            checks.append({
                "name": f"score_{comp_name.replace(' ','_')}",
                "passed": passed,
                "detail": f"Expected {expected_score}, got {actual_score}"
            })
        except Exception as e:
            checks.append({"name": f"score_{comp_name.replace(' ','_')}", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 4: Correct winner (Baby Tight Eyez with 4.30) ----
    try:
        winner = None
        if "ranking" in report:
            ranking = report["ranking"]
            winner = ranking[0] if ranking else None
        elif "winner" in report:
            winner = report["winner"]
        elif "results" in report:
            results = report["results"]
            if isinstance(results, list) and results:
                winner = results[0].get("name", results[0].get("competitor", None))
        
        # Also check competitors list sorted
        if winner is None and "competitors" in report:
            comps = report["competitors"]
            sorted_comps = sorted(comps, key=lambda c: float(c.get("total_score", c.get("score", 0))), reverse=True)
            winner = sorted_comps[0].get("name", "") if sorted_comps else None
        
        expected_winner = "Baby Tight Eyez"
        winner_correct = winner is not None and expected_winner.lower() in str(winner).lower()
        checks.append({
            "name": "winner_correct",
            "passed": winner_correct,
            "detail": f"Expected winner: {expected_winner}, got: {winner}"
        })
    except Exception as e:
        checks.append({"name": "winner_correct", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 5: Correct ranking order (Baby Tight Eyez > Young Miss Prissy > Lil Slayer) ----
    try:
        ranking_correct = False
        ranking_found = None
        
        if "ranking" in report:
            ranking_found = report["ranking"]
        elif "competitors" in report:
            comps = report["competitors"]
            sorted_comps = sorted(comps, key=lambda c: float(c.get("total_score", c.get("score", 0))), reverse=True)
            ranking_found = [c.get("name", "") for c in sorted_comps]
        
        if ranking_found and len(ranking_found) >= 3:
            r0 = str(ranking_found[0]).lower()
            r1 = str(ranking_found[1]).lower()
            r2 = str(ranking_found[2]).lower()
            ranking_correct = (
                "baby tight eyez" in r0 and
                "young miss prissy" in r1 and
                "lil slayer" in r2
            )
        
        checks.append({
            "name": "ranking_order_correct",
            "passed": ranking_correct,
            "detail": f"Expected: [Baby Tight Eyez, Young Miss Prissy, Lil Slayer], got: {ranking_found}"
        })
    except Exception as e:
        checks.append({"name": "ranking_order_correct", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 6: Young Miss Prissy beat map - In-Between at start 3.5 (after Groove+3D+Stomp+ArmSwing-Smash) ----
    try:
        ymp_name = "Young Miss Prissy"
        ymp_data = None
        if isinstance(report, dict):
            for k, v in report.items():
                if ymp_name.lower() in str(k).lower() or (isinstance(v, dict) and ymp_name.lower() in str(v).get("name", "").lower()):
                    ymp_data = v
                    break
            if ymp_data is None and ymp_name in report:
                ymp_data = report[ymp_name]
            if ymp_data is None and "competitors" in report:
                for c in report["competitors"]:
                    if ymp_name.lower() in str(c.get("name", "")).lower():
                        ymp_data = c
                        break
        
        if ymp_data is None:
            checks.append({"name": "beat_map_young_miss_prissy", "passed": False, "detail": "Competitor not found"})
        else:
            bm = ymp_data.get("beat_map", ymp_data.get("choreography", ymp_data.get("moves", [])))
            in_between_correct = False
            pose_ap_start_correct = False
            
            for entry in bm:
                move = str(entry.get("move", entry.get("name", ""))).strip()
                start = entry.get("start_beat", entry.get("start", entry.get("beat", None)))
                timing = entry.get("timing", entry.get("duration", None))
                
                if "In-Between" in move or "in-between" in move.lower():
                    # Groove(1)+3D(1)+Stomp(1)+ArmSwing-Smash(1) = 4.0
                    expected_ib_start = 4.0
                    if start is not None and abs(float(start) - expected_ib_start) < 0.01:
                        in_between_correct = True
                
                if "Pose" in move and "Arm Placement" in move:
                    # Groove(1)+3D(1)+Stomp(1)+ArmSwingSmash(1)+InBetween(0.5)+ChestPop(1)+Zones(1)+Footwork(1)+Wobble(1) = 8.5
                    expected_pose_start = 8.5
                    if start is not None and abs(float(start) - expected_pose_start) < 0.01:
                        pose_ap_start_correct = True
            
            ymp_passed = in_between_correct and pose_ap_start_correct
            checks.append({
                "name": "beat_map_young_miss_prissy",
                "passed": ymp_passed,
                "detail": f"InBetween@4.0={in_between_correct}, PoseAP@8.5={pose_ap_start_correct}"
            })
    except Exception as e:
        checks.append({"name": "beat_map_young_miss_prissy", "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 7: Move metadata enrichment (category/difficulty present) ----
    try:
        enrichment_found = False
        if "competitors" in report:
            for c in report["competitors"]:
                bm = c.get("beat_map", c.get("choreography", c.get("moves", [])))
                if bm:
                    for entry in bm:
                        if "category" in entry or "difficulty" in entry:
                            enrichment_found = True
                            break
        elif isinstance(report, dict):
            for k, v in report.items():
                if isinstance(v, dict):
                    bm = v.get("beat_map", v.get("choreography", v.get("moves", [])))
                    if bm:
                        for entry in bm:
                            if "category" in entry or "difficulty" in entry:
                                enrichment_found = True
                                break
        
        checks.append({
            "name": "move_metadata_enriched",
            "passed": enrichment_found,
            "detail": "At least one move entry contains 'category' or 'difficulty' from the move library"
        })
    except Exception as e:
        checks.append({"name": "move_metadata_enriched", "passed": False, "detail": f"Error: {e}"})

    # Compute final score
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    
    # Weighted: beat maps and scoring are critical
    critical_checks = {"beat_map_baby_tight_eyez", "beat_map_lil_slayer", "winner_correct", "ranking_order_correct"}
    critical_passed = sum(1 for c in checks if c["name"] in critical_checks and c["passed"])
    
    overall_passed = passed_checks >= int(total_checks * 0.75) and critical_passed >= 3
    final_score = round(passed_checks / total_checks, 3)
    
    print(json.dumps({
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }))

if __name__ == "__main__":
    main()