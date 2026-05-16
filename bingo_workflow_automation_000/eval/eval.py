import sys
import json
import os
from pathlib import Path

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # -------------------------------------------------------
    # CHECK 1: game_session_report.json exists somewhere
    # -------------------------------------------------------
    report_files = list(workspace.rglob("game_session_report.json"))
    if report_files:
        report_file = report_files[0]
        check1_passed = True
        check1_detail = f"Found report at: {report_file}"
    else:
        check1_passed = False
        check1_detail = "game_session_report.json not found anywhere in workspace"
    checks.append({"name": "report_file_exists", "passed": check1_passed, "detail": check1_detail})
    if check1_passed:
        total_score += 0.15

    # -------------------------------------------------------
    # CHECK 2: Report contains valid JSON with required keys
    # -------------------------------------------------------
    report_data = None
    if check1_passed:
        try:
            with open(report_file) as f:
                report_data = json.load(f)
            required_keys = {"game_id", "calls_made", "card", "called_numbers", "result"}
            missing = required_keys - set(report_data.keys())
            if not missing:
                check2_passed = True
                check2_detail = f"Report has all required keys: {required_keys}"
            else:
                check2_passed = False
                check2_detail = f"Report missing keys: {missing}. Found keys: {set(report_data.keys())}"
        except Exception as e:
            check2_passed = False
            check2_detail = f"Failed to parse report JSON: {e}"
            report_data = None
    else:
        check2_passed = False
        check2_detail = "Skipped: report file not found"
    checks.append({"name": "report_json_valid_structure", "passed": check2_passed, "detail": check2_detail})
    if check2_passed:
        total_score += 0.15

    # -------------------------------------------------------
    # CHECK 3: Bingo data directory was used (new-game ran)
    # -------------------------------------------------------
    bingo_dir = Path.home() / ".local" / "share" / "bingo"
    game_file = bingo_dir / "current_game.json"
    try:
        if game_file.exists():
            with open(game_file) as f:
                game_data = json.load(f)
            check3_passed = "game_id" in game_data
            check3_detail = f"Game file exists with game_id={game_data.get('game_id')}. Status: {game_data.get('status')}"
        else:
            check3_passed = False
            check3_detail = "No current_game.json found in ~/.local/share/bingo/"
    except Exception as e:
        check3_passed = False
        check3_detail = f"Error reading game file: {e}"
    checks.append({"name": "new_game_was_run", "passed": check3_passed, "detail": check3_detail})
    if check3_passed:
        total_score += 0.10

    # -------------------------------------------------------
    # CHECK 4: Card was generated (card command was run)
    # -------------------------------------------------------
    card_file = bingo_dir / "current_card.json"
    card_data = None
    try:
        if card_file.exists():
            with open(card_file) as f:
                card_data = json.load(f)
            expected_cols = {'B', 'I', 'N', 'G', 'O'}
            has_all_cols = expected_cols.issubset(set(card_data.keys()))
            all_5_rows = all(len(card_data[c]) == 5 for c in expected_cols if c in card_data)
            free_space = card_data.get('N', [None, None, None])[2] == 0
            check4_passed = has_all_cols and all_5_rows and free_space
            check4_detail = f"Card has cols={list(card_data.keys())}, free_space_in_N={free_space}, 5rows={all_5_rows}"
        else:
            check4_passed = False
            check4_detail = "No current_card.json found in ~/.local/share/bingo/"
    except Exception as e:
        check4_passed = False
        check4_detail = f"Error reading card file: {e}"
    checks.append({"name": "card_was_generated", "passed": check4_passed, "detail": check4_detail})
    if check4_passed:
        total_score += 0.15

    # -------------------------------------------------------
    # CHECK 5: Numbers were called (at least 10 calls made)
    # -------------------------------------------------------
    try:
        if game_file.exists():
            with open(game_file) as f:
                game_data = json.load(f)
            called = game_data.get("called", [])
            num_called = len(called)
            check5_passed = num_called >= 10
            check5_detail = f"Numbers called: {num_called} (need >= 10). Called: {sorted(called)}"
        else:
            check5_passed = False
            check5_detail = "No game file found"
    except Exception as e:
        check5_passed = False
        check5_detail = f"Error: {e}"
    checks.append({"name": "numbers_were_called_minimum_10", "passed": check5_passed, "detail": check5_detail})
    if check5_passed:
        total_score += 0.10

    # -------------------------------------------------------
    # CHECK 6: check command was used (history or stats updated, or game completed)
    # -------------------------------------------------------
    stats_file = bingo_dir / "stats.json"
    history_file = bingo_dir / "history.json"
    try:
        check_was_run = False
        check6_detail_parts = []

        if stats_file.exists():
            with open(stats_file) as f:
                stats = json.load(f)
            if stats.get("games_played", 0) > 0:
                check_was_run = True
                check6_detail_parts.append(f"stats: games_played={stats.get('games_played')}, wins={stats.get('wins')}, total_calls={stats.get('total_calls')}")

        if history_file.exists():
            with open(history_file) as f:
                hist = json.load(f)
            if len(hist) > 0:
                check_was_run = True
                check6_detail_parts.append(f"history: {len(hist)} completed game(s)")

        # Also check if game status is 'completed'
        if game_file.exists():
            with open(game_file) as f:
                gd = json.load(f)
            if gd.get("status") == "completed":
                check_was_run = True
                check6_detail_parts.append("game status=completed (check command produced a BINGO)")

        check6_passed = check_was_run
        check6_detail = "; ".join(check6_detail_parts) if check6_detail_parts else "No evidence of check command being run"
    except Exception as e:
        check6_passed = False
        check6_detail = f"Error: {e}"
    checks.append({"name": "check_command_was_used", "passed": check6_passed, "detail": check6_detail})
    if check6_passed:
        total_score += 0.10

    # -------------------------------------------------------
    # CHECK 7: stats command output captured in report
    # -------------------------------------------------------
    try:
        if report_data is not None:
            stats_in_report = report_data.get("stats", None)
            if stats_in_report is not None and isinstance(stats_in_report, dict):
                has_games_played = "games_played" in stats_in_report
                check7_passed = has_games_played
                check7_detail = f"Stats in report: {stats_in_report}"
            else:
                check7_passed = False
                check7_detail = f"'stats' key missing or not a dict in report. Got: {type(stats_in_report)}"
        else:
            check7_passed = False
            check7_detail = "No report data available to check stats"
    except Exception as e:
        check7_passed = False
        check7_detail = f"Error: {e}"
    checks.append({"name": "stats_captured_in_report", "passed": check7_passed, "detail": check7_detail})
    if check7_passed:
        total_score += 0.10

    # -------------------------------------------------------
    # CHECK 8: Report called_numbers matches actual game state
    # -------------------------------------------------------
    try:
        if report_data is not None and game_file.exists():
            with open(game_file) as f:
                gd = json.load(f)
            actual_called = sorted(gd.get("called", []))
            report_called = sorted(report_data.get("called_numbers", []))

            # Called numbers in report should be a subset of or equal to actual (agent may have called more after writing report)
            report_set = set(report_called)
            actual_set = set(actual_called)
            # All numbers in report should be in actual called
            all_in_actual = report_set.issubset(actual_set)
            reasonable_count = len(report_called) >= 10

            check8_passed = all_in_actual and reasonable_count
            check8_detail = f"Report called={len(report_called)} nums, actual called={len(actual_called)} nums, all_in_actual={all_in_actual}"
        else:
            check8_passed = False
            check8_detail = "Cannot compare: missing report or game file"
    except Exception as e:
        check8_passed = False
        check8_detail = f"Error: {e}"
    checks.append({"name": "called_numbers_consistent", "passed": check8_passed, "detail": check8_detail})
    if check8_passed:
        total_score += 0.10

    # -------------------------------------------------------
    # CHECK 9: calls_made field in report is a positive integer
    # -------------------------------------------------------
    try:
        if report_data is not None:
            calls_made = report_data.get("calls_made", None)
            if isinstance(calls_made, int) and calls_made >= 10:
                check9_passed = True
                check9_detail = f"calls_made={calls_made} (valid positive integer >= 10)"
            else:
                check9_passed = False
                check9_detail = f"calls_made={calls_made} (must be integer >= 10)"
        else:
            check9_passed = False
            check9_detail = "No report data"
    except Exception as e:
        check9_passed = False
        check9_detail = f"Error: {e}"
    checks.append({"name": "calls_made_field_valid", "passed": check9_passed, "detail": check9_detail})
    if check9_passed:
        total_score += 0.05

    # -------------------------------------------------------
    # CHECK 10: result field indicates game outcome
    # -------------------------------------------------------
    try:
        if report_data is not None:
            result = report_data.get("result", "")
            valid_results = {"bingo", "no_bingo", "win", "loss", "completed", "in_progress", "BINGO"}
            # Be lenient - result just needs to be a non-empty string
            if isinstance(result, str) and len(result) > 0:
                check10_passed = True
                check10_detail = f"result field present: '{result}'"
            else:
                check10_passed = False
                check10_detail = f"result field missing or empty: {result!r}"
        else:
            check10_passed = False
            check10_detail = "No report data"
    except Exception as e:
        check10_passed = False
        check10_detail = f"Error: {e}"
    checks.append({"name": "result_field_present", "passed": check10_passed, "detail": check10_detail})
    if check10_passed:
        total_score += 0.05

    # Final score
    total_score = round(min(total_score, 1.0), 3)
    all_critical = (
        checks[0]["passed"] and  # file exists
        checks[2]["passed"] and  # new-game ran
        checks[3]["passed"] and  # card generated
        checks[4]["passed"]      # numbers called
    )
    passed = all_critical and total_score >= 0.5

    return {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))