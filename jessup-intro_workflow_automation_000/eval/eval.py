import sys
import json
import os
from pathlib import Path

def compute_expected_results(workspace):
    """
    Recompute from raw data using the correct Jessup scoring rules:
    
    Per match (total 9 points):
    - Memorial points (3 pts): each team has 3 memorial scores [low, mid, high].
      Compare low vs low, mid vs mid, high vs high. Each comparison: higher score gets 1 point.
      (If tied, neither gets the point — or both get 0.5? SKILL.md says "更高者得一分", so tie = 0 each)
    
    - Oral argument points (6 pts): 3 judges, each judge gives both players on each team a score.
      For each judge j: 
        applicant_sum_j = applicant_oral[j][0] + applicant_oral[j][1]
        respondent_sum_j = respondent_oral[j][0] + respondent_oral[j][1]
        Higher sum gets 2 points (the "两分" for that judge's comparison).
      Total oral points for applicant = sum over 3 judges of (2 if app_sum_j > resp_sum_j else 0)
      Total oral points for respondent = 6 - applicant_oral_points
    
    - Win condition: a team wins the match if their total points >= 5 out of 9.
    
    Group stage standings:
    - Sort by wins (descending) first
    - Then by total "大分" (big points = total match points accumulated across all matches) descending
    
    Knockout bracket:
    - Rank teams 1-16 across all groups by wins then big points
    - Pairings: 1v16, 2v15, 3v14, ..., 8v9
    """
    
    teams_path = Path(workspace) / "competition_admin/participants/teams.json"
    groups_path = Path(workspace) / "competition_admin/schedule/groups.json"
    matches_path = Path(workspace) / "competition_admin/results/group_stage_raw.json"
    
    with open(teams_path) as f:
        teams_list = json.load(f)
    with open(groups_path) as f:
        groups = json.load(f)
    with open(matches_path) as f:
        matches = json.load(f)
    
    team_map = {t["id"]: t for t in teams_list}
    
    # Initialize stats
    stats = {t["id"]: {"wins": 0, "losses": 0, "big_points": 0} for t in teams_list}
    match_results = []
    
    for m in matches:
        app_id = m["applicant"]
        resp_id = m["respondent"]
        app_mem = sorted(m["applicant_memorial_scores"])  # [low, mid, high]
        resp_mem = sorted(m["respondent_memorial_scores"])
        app_oral = m["applicant_oral_scores"]  # list of 3 judges, each [p1, p2]
        resp_oral = m["respondent_oral_scores"]
        
        # Memorial points
        app_mem_pts = 0
        resp_mem_pts = 0
        for i in range(3):
            if app_mem[i] > resp_mem[i]:
                app_mem_pts += 1
            elif resp_mem[i] > app_mem[i]:
                resp_mem_pts += 1
            # tie: both get 0
        
        # Oral argument points
        app_oral_pts = 0
        resp_oral_pts = 0
        for j in range(3):
            app_sum = app_oral[j][0] + app_oral[j][1]
            resp_sum = resp_oral[j][0] + resp_oral[j][1]
            if app_sum > resp_sum:
                app_oral_pts += 2
            elif resp_sum > app_sum:
                resp_oral_pts += 2
            # tie: both get 0 (edge case, unlikely with floats)
        
        app_total = app_mem_pts + app_oral_pts
        resp_total = resp_mem_pts + resp_oral_pts
        
        # Win condition: >= 5 points
        app_win = app_total >= 5
        resp_win = resp_total >= 5
        
        # Update stats
        if app_win:
            stats[app_id]["wins"] += 1
        else:
            stats[app_id]["losses"] += 1
        if resp_win:
            stats[resp_id]["wins"] += 1
        else:
            stats[resp_id]["losses"] += 1
        
        stats[app_id]["big_points"] += app_total
        stats[resp_id]["big_points"] += resp_total
        
        match_results.append({
            "match_id": m["match_id"],
            "applicant": app_id,
            "respondent": resp_id,
            "applicant_points": app_total,
            "respondent_points": resp_total,
            "applicant_wins": app_win,
            "respondent_wins": resp_win
        })
    
    # Group standings: sort by wins desc, then big_points desc
    group_standings = {}
    for group_name, team_ids in groups.items():
        sorted_teams = sorted(
            team_ids,
            key=lambda tid: (-stats[tid]["wins"], -stats[tid]["big_points"])
        )
        group_standings[group_name] = [
            {
                "rank": i+1,
                "team_id": tid,
                "wins": stats[tid]["wins"],
                "losses": stats[tid]["losses"],
                "big_points": stats[tid]["big_points"]
            }
            for i, tid in enumerate(sorted_teams)
        ]
    
    # Overall ranking: all 16 teams sorted by wins desc, then big_points desc
    all_team_ids = list(stats.keys())
    overall_ranking = sorted(
        all_team_ids,
        key=lambda tid: (-stats[tid]["wins"], -stats[tid]["big_points"])
    )
    
    # Knockout bracket: 1v16, 2v15, ..., 8v9
    knockout_bracket = []
    for i in range(8):
        seed_high = i + 1      # 1, 2, ..., 8
        seed_low = 16 - i      # 16, 15, ..., 9
        t_high = overall_ranking[seed_high - 1]
        t_low = overall_ranking[seed_low - 1]
        knockout_bracket.append({
            "match": i + 1,
            "seed_1": seed_high,
            "team_1": t_high,
            "seed_2": seed_low,
            "team_2": t_low,
        })
    
    return stats, group_standings, overall_ranking, knockout_bracket, match_results


def load_agent_output(workspace):
    results = list(Path(workspace).rglob("tournament_results.json"))
    if not results:
        return None
    with open(results[0]) as f:
        return json.load(f)


def main():
    workspace = sys.argv[1]
    checks = []
    
    try:
        exp_stats, exp_group_standings, exp_overall, exp_knockout, exp_match_results = \
            compute_expected_results(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False, "score": 0.0,
            "checks": [{"name": "setup", "passed": False, "detail": f"Failed to compute expected: {e}"}]
        }))
        return
    
    # Load agent output
    agent_output = load_agent_output(workspace)
    if agent_output is None:
        print(json.dumps({
            "passed": False, "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "tournament_results.json not found anywhere in workspace"}]
        }))
        return
    
    checks.append({"name": "file_exists", "passed": True, "detail": "tournament_results.json found"})
    
    # ---- CHECK 1: Match-level scoring correctness ----
    # Check that the agent correctly computed big_points for each team
    try:
        agent_team_stats = agent_output.get("team_stats", agent_output.get("standings", {}))
        
        # Try to find team stats in various formats
        correct_scores = 0
        total_teams = len(exp_stats)
        
        for tid, exp in exp_stats.items():
            # Try multiple possible keys
            agent_stat = None
            if isinstance(agent_team_stats, dict):
                agent_stat = agent_team_stats.get(tid)
            elif isinstance(agent_team_stats, list):
                for item in agent_team_stats:
                    if item.get("team_id") == tid or item.get("id") == tid:
                        agent_stat = item
                        break
            
            if agent_stat is None:
                continue
            
            agent_wins = agent_stat.get("wins", agent_stat.get("win_count", -1))
            agent_bp = agent_stat.get("big_points", agent_stat.get("total_points", -1))
            
            if agent_wins == exp["wins"] and abs(float(agent_bp) - exp["big_points"]) < 0.01:
                correct_scores += 1
        
        win_accuracy = correct_scores / total_teams
        check_passed = win_accuracy >= 0.875  # 14/16 teams correct
        checks.append({
            "name": "match_scoring_correctness",
            "passed": check_passed,
            "detail": f"{correct_scores}/{total_teams} teams have correct wins and big_points ({win_accuracy:.1%})"
        })
    except Exception as e:
        checks.append({
            "name": "match_scoring_correctness",
            "passed": False,
            "detail": f"Error checking match scoring: {e}"
        })
    
    # ---- CHECK 2: Scoring formula — oral argument points use per-judge comparison ----
    # Verify a specific match's oral calculation
    try:
        with open(Path(workspace) / "competition_admin/results/group_stage_raw.json") as f:
            raw_matches = json.load(f)
        
        # Pick first match and verify
        m = raw_matches[0]
        app_oral = m["applicant_oral_scores"]
        resp_oral = m["respondent_oral_scores"]
        
        # Correct oral computation
        expected_app_oral_pts = 0
        for j in range(3):
            app_sum = app_oral[j][0] + app_oral[j][1]
            resp_sum = resp_oral[j][0] + resp_oral[j][1]
            if app_sum > resp_sum:
                expected_app_oral_pts += 2
        
        # Wrong computation (simple total): would give different result
        simple_app_oral = sum(app_oral[j][0] + app_oral[j][1] for j in range(3))
        simple_resp_oral = sum(resp_oral[j][0] + resp_oral[j][1] for j in range(3))
        naive_winner_is_app = simple_app_oral > simple_resp_oral
        
        # The key proprietary check: is the per-judge comparison giving different results from naive sum?
        # This verifies they implemented it correctly vs naive approach
        agent_match_results = agent_output.get("match_results", [])
        match_found = False
        oral_formula_correct = False
        
        for amr in agent_match_results:
            if amr.get("match_id") == m["match_id"]:
                match_found = True
                agent_app_pts = amr.get("applicant_points", amr.get("applicant_total_points", None))
                if agent_app_pts is not None:
                    # Compute what the CORRECT total should be
                    app_mem = sorted(m["applicant_memorial_scores"])
                    resp_mem = sorted(m["respondent_memorial_scores"])
                    app_mem_pts = sum(1 for i in range(3) if app_mem[i] > resp_mem[i])
                    expected_total = app_mem_pts + expected_app_oral_pts
                    oral_formula_correct = (int(agent_app_pts) == expected_total)
                break
        
        if not match_found:
            checks.append({
                "name": "oral_scoring_formula",
                "passed": False,
                "detail": "match_results not found or first match not present in agent output"
            })
        else:
            checks.append({
                "name": "oral_scoring_formula",
                "passed": oral_formula_correct,
                "detail": f"Match {m['match_id']}: expected applicant total={expected_total}, got {agent_app_pts if match_found else 'N/A'}. Per-judge comparison (2pts each) must be used."
            })
    except Exception as e:
        checks.append({
            "name": "oral_scoring_formula",
            "passed": False,
            "detail": f"Error verifying oral formula: {e}"
        })
    
    # ---- CHECK 3: Group standings tiebreaker (wins first, then big_points) ----
    try:
        agent_group_standings = agent_output.get("group_standings", {})
        correct_groups = 0
        total_groups = len(exp_group_standings)
        
        for gname, exp_standing in exp_group_standings.items():
            agent_standing = agent_group_standings.get(gname, [])
            if not agent_standing:
                continue
            
            # Check rank 1 team (group leader) is correct
            exp_rank1 = exp_standing[0]["team_id"]
            agent_rank1 = None
            
            if isinstance(agent_standing, list) and len(agent_standing) > 0:
                first = agent_standing[0]
                agent_rank1 = first.get("team_id", first.get("id", None))
            
            if agent_rank1 == exp_rank1:
                correct_groups += 1
        
        check_passed = correct_groups == total_groups
        checks.append({
            "name": "group_standings_tiebreaker",
            "passed": check_passed,
            "detail": f"{correct_groups}/{total_groups} group leaders correctly identified using wins-first, then big_points tiebreaker"
        })
    except Exception as e:
        checks.append({
            "name": "group_standings_tiebreaker",
            "passed": False,
            "detail": f"Error checking group standings: {e}"
        })
    
    # ---- CHECK 4: Overall ranking and knockout bracket seeding (1v16, 2v15...) ----
    try:
        agent_knockout = agent_output.get("knockout_bracket", [])
        
        correct_pairings = 0
        total_pairings = len(exp_knockout)
        
        for exp_pairing in exp_knockout:
            exp_t1 = exp_pairing["team_1"]
            exp_t2 = exp_pairing["team_2"]
            exp_match_num = exp_pairing["match"]
            
            # Find corresponding agent pairing
            agent_pairing = None
            for ap in agent_knockout:
                am = ap.get("match", ap.get("match_number", ap.get("pairing", None)))
                if am == exp_match_num:
                    agent_pairing = ap
                    break
            
            if agent_pairing is None:
                continue
            
            agent_t1 = agent_pairing.get("team_1", agent_pairing.get("high_seed_team", None))
            agent_t2 = agent_pairing.get("team_2", agent_pairing.get("low_seed_team", None))
            
            # Check if the pairing is correct (order may differ: t1 vs t2 or t2 vs t1)
            pairing_correct = (
                (agent_t1 == exp_t1 and agent_t2 == exp_t2) or
                (agent_t1 == exp_t2 and agent_t2 == exp_t1)
            )
            if pairing_correct:
                correct_pairings += 1
        
        check_passed = correct_pairings >= 6  # at least 6/8 correct pairings
        checks.append({
            "name": "knockout_bracket_seeding",
            "passed": check_passed,
            "detail": f"{correct_pairings}/{total_pairings} knockout pairings correct. Expected 1v16, 2v15, 3v14, 4v13, 5v12, 6v11, 7v10, 8v9 seeding."
        })
    except Exception as e:
        checks.append({
            "name": "knockout_bracket_seeding",
            "passed": False,
            "detail": f"Error checking knockout bracket: {e}"
        })
    
    # ---- CHECK 5: Win condition is >= 5 out of 9 ----
    try:
        with open(Path(workspace) / "competition_admin/results/group_stage_raw.json") as f:
            raw_matches = json.load(f)
        
        agent_match_results = agent_output.get("match_results", [])
        agent_mr_map = {amr.get("match_id"): amr for amr in agent_match_results}
        
        win_condition_correct = 0
        win_condition_total = 0
        
        for m in raw_matches[:16]:  # check first 16 matches
            mid = m["match_id"]
            if mid not in agent_mr_map:
                continue
            
            amr = agent_mr_map[mid]
            
            # Compute expected
            app_mem = sorted(m["applicant_memorial_scores"])
            resp_mem = sorted(m["respondent_memorial_scores"])
            app_mem_pts = sum(1 for i in range(3) if app_mem[i] > resp_mem[i])
            resp_mem_pts = sum(1 for i in range(3) if resp_mem[i] > app_mem[i])
            
            app_oral = m["applicant_oral_scores"]
            resp_oral = m["respondent_oral_scores"]
            app_oral_pts = sum(2 for j in range(3) if (app_oral[j][0]+app_oral[j][1]) > (resp_oral[j][0]+resp_oral[j][1]))
            resp_oral_pts = sum(2 for j in range(3) if (resp_oral[j][0]+resp_oral[j][1]) > (app_oral[j][0]+app_oral[j][1]))
            
            exp_app_total = app_mem_pts + app_oral_pts
            exp_app_wins = exp_app_total >= 5
            
            agent_app_wins = amr.get("applicant_wins", amr.get("applicant_win", None))
            if agent_app_wins is None:
                continue
            
            win_condition_total += 1
            if bool(agent_app_wins) == exp_app_wins:
                win_condition_correct += 1
        
        if win_condition_total == 0:
            checks.append({
                "name": "win_condition_5_of_9",
                "passed": False,
                "detail": "Could not verify win condition: match_results missing or no applicant_wins field"
            })
        else:
            check_passed = win_condition_correct / win_condition_total >= 0.875
            checks.append({
                "name": "win_condition_5_of_9",
                "passed": check_passed,
                "detail": f"{win_condition_correct}/{win_condition_total} matches have correct win flag (threshold: 5 out of 9 total points)"
            })
    except Exception as e:
        checks.append({
            "name": "win_condition_5_of_9",
            "passed": False,
            "detail": f"Error checking win condition: {e}"
        })
    
    # Final scoring
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks) if checks else 0.0
    overall_passed = score >= 0.7 and checks[0]["passed"]  # file must exist + 70% checks pass
    
    print(json.dumps({
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()