import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]
checks = []

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── Expected values derived from scenario.json ──────────────────────────────
GROUP_ID = "team-alpha-2025"
PLAYERS = [
    {"id": "u001", "name": "Alice"},
    {"id": "u002", "name": "Bob"},
    {"id": "u003", "name": "Carol"},
]
PLAYER_IDS = [p["id"] for p in PLAYERS]
PLAYER_NAMES = [p["name"] for p in PLAYERS]

# ── CHECK 1: Game state file exists and is settled ───────────────────────────
game_file = Path(workspace) / "scripts" / "data" / "games" / f"{GROUP_ID}.json"
try:
    game = load_json(game_file)
    settled = game.get("status") == "settled"
    add_check("game_state_file_exists_and_settled",
              settled,
              f"Game status: {game.get('status', 'MISSING')}")
except Exception as e:
    add_check("game_state_file_exists_and_settled", False, f"Error loading game file: {e}")
    game = None

# ── CHECK 2: All 3 players have 3 rounds of clues ────────────────────────────
try:
    if game:
        all_clues_ok = all(
            len(p.get("clues", [])) == 3
            for p in game["players"]
        )
        detail = str({p["name"]: len(p.get("clues", [])) for p in game["players"]})
        add_check("all_players_have_3_rounds_of_clues", all_clues_ok, detail)
    else:
        add_check("all_players_have_3_rounds_of_clues", False, "No game data")
except Exception as e:
    add_check("all_players_have_3_rounds_of_clues", False, str(e))

# ── CHECK 3: Clue content matches scenario ────────────────────────────────────
EXPECTED_CLUES = {
    "u001": ["我每天都要研究云层的变化", "我的工作离不开气压计和温度表", "我能提前告诉你明天要不要带伞"],
    "u002": ["我用双手创造美丽的空间", "我的作品会矗立几百年", "我和结构工程师是最好的搭档"],
    "u003": ["我的实验室里住着很多六条腿的小家伙", "我对蜂巢的构造着迷", "我的研究可能帮助研发新型抗菌药物"]
}
try:
    if game:
        clue_match = True
        details = []
        for p in game["players"]:
            expected = EXPECTED_CLUES.get(p["id"], [])
            actual_texts = [c["text"] for c in p.get("clues", [])]
            if actual_texts != expected:
                clue_match = False
                details.append(f"{p['name']}: expected {expected}, got {actual_texts}")
        add_check("clue_content_matches_scenario", clue_match,
                  "All clues match" if clue_match else "; ".join(details))
    else:
        add_check("clue_content_matches_scenario", False, "No game data")
except Exception as e:
    add_check("clue_content_matches_scenario", False, str(e))

# ── CHECK 4: All players have submitted guesses ───────────────────────────────
try:
    if game:
        all_guessed = all(len(p.get("guesses", {})) >= 2 for p in game["players"])
        detail = str({p["name"]: len(p.get("guesses", {})) for p in game["players"]})
        add_check("all_players_submitted_guesses", all_guessed, detail)
    else:
        add_check("all_players_submitted_guesses", False, "No game data")
except Exception as e:
    add_check("all_players_submitted_guesses", False, str(e))

# ── CHECK 5: guess uses targetName (display name), not player ID ─────────────
try:
    if game:
        for p in game["players"]:
            guesses = p.get("guesses", {})
            for key in guesses:
                if key in PLAYER_IDS:
                    add_check("guesses_use_display_names_not_ids", False,
                              f"Player {p['name']} used ID '{key}' as target — must use display name")
                    break
            else:
                continue
            break
        else:
            add_check("guesses_use_display_names_not_ids", True, "All guess keys are display names")
    else:
        add_check("guesses_use_display_names_not_ids", False, "No game data")
except Exception as e:
    add_check("guesses_use_display_names_not_ids", False, str(e))

# ── CHECK 6: Private DM files exist for all players ──────────────────────────
try:
    messages_dir = Path(workspace) / "messages"
    dm_checks = []
    all_dm_ok = True
    for p in PLAYERS:
        dm_file = messages_dir / f"{p['id']}.txt"
        if dm_file.exists():
            content = dm_file.read_text(encoding="utf-8")
            dm_checks.append(f"{p['name']}({p['id']}): OK (len={len(content)})")
        else:
            all_dm_ok = False
            dm_checks.append(f"{p['name']}({p['id']}): MISSING")
    add_check("private_dm_sent_to_all_players", all_dm_ok, "; ".join(dm_checks))
except Exception as e:
    add_check("private_dm_sent_to_all_players", False, str(e))

# ── CHECK 7: DM content includes correct identity ────────────────────────────
try:
    if game:
        identity_map = {p["id"]: p["identity"] for p in game["players"]}
        dm_identity_ok = True
        details = []
        for pid, identity in identity_map.items():
            dm_file = Path(workspace) / "messages" / f"{pid}.txt"
            if not dm_file.exists():
                dm_identity_ok = False
                details.append(f"{pid}: DM file missing")
                continue
            content = dm_file.read_text(encoding="utf-8")
            if identity not in content:
                dm_identity_ok = False
                details.append(f"{pid}: identity '{identity}' not found in DM")
            else:
                details.append(f"{pid}: identity '{identity}' confirmed in DM")
        add_check("dm_content_contains_correct_identity", dm_identity_ok, "; ".join(details))
    else:
        add_check("dm_content_contains_correct_identity", False, "No game data to check identities")
except Exception as e:
    add_check("dm_content_contains_correct_identity", False, str(e))

# ── CHECK 8: Rankings file updated ───────────────────────────────────────────
rankings_file = Path(workspace) / "scripts" / "data" / "rankings" / f"{GROUP_ID}.json"
try:
    rankings = load_json(rankings_file)
    ranked_ids = set(rankings.get("players", {}).keys())
    expected_ids = set(PLAYER_IDS)
    all_ranked = expected_ids.issubset(ranked_ids)
    add_check("rankings_file_updated_for_all_players", all_ranked,
              f"Expected {expected_ids}, found {ranked_ids}")
except Exception as e:
    add_check("rankings_file_updated_for_all_players", False, f"Error: {e}")

# ── CHECK 9: game_result.json exists with correct structure ──────────────────
result_files = list(Path(workspace).rglob("game_result.json"))
try:
    if not result_files:
        add_check("game_result_json_exists_and_valid", False, "game_result.json not found anywhere in workspace")
    else:
        result = load_json(result_files[0])
        has_scores = "scores" in result or "identities" in result or "status" in result
        is_settled = result.get("status") == "settled"
        has_all_players = all(
            any(p.get("name") == pn or p.get("id") == pid
                for p in result.get("scores", []) + result.get("identities", []))
            for pn, pid in zip(PLAYER_NAMES, PLAYER_IDS)
        )
        ok = has_scores and is_settled
        add_check("game_result_json_exists_and_valid", ok,
                  f"Found at {result_files[0]}, status={result.get('status')}, has_scores={has_scores}")
except Exception as e:
    add_check("game_result_json_exists_and_valid", False, str(e))

# ── CHECK 10: Scoring logic correct ──────────────────────────────────────────
# Expected guesses:
#   Alice (u001): Bob->建筑师, Carol->昆虫学家
#   Bob   (u002): Alice->气象学家, Carol->昆虫学家
#   Carol (u003): Alice->气象学家, Bob->外交官
# We compute expected scores from actual identities assigned by engine
try:
    if game and game.get("status") == "settled":
        identity_map = {p["name"]: p["identity"] for p in game["players"]}
        score_map = {p["id"]: p["score"] for p in game["players"]}
        name_to_id = {p["name"]: p["id"] for p in game["players"]}

        expected_guesses = {
            "u001": {"Bob": "建筑师", "Carol": "昆虫学家"},
            "u002": {"Alice": "气象学家", "Carol": "昆虫学家"},
            "u003": {"Alice": "气象学家", "Bob": "外交官"}
        }

        scoring_ok = True
        score_details = []

        for p in game["players"]:
            pid = p["id"]
            pg = expected_guesses.get(pid, {})
            correct = sum(1 for tname, gid in pg.items() if identity_map.get(tname) == gid)
            expected_correct_score = correct * 10

            wrong_from_others = 0
            for other in game["players"]:
                if other["id"] == pid:
                    continue
                og = expected_guesses.get(other["id"], {})
                guess = og.get(p["name"])
                if guess is not None and guess != p["identity"]:
                    wrong_from_others += 1
            expected_camo_score = wrong_from_others * 5
            expected_total = expected_correct_score + expected_camo_score

            actual = score_map.get(pid, {})
            if (actual.get("correct") == expected_correct_score and
                    actual.get("camouflage") == expected_camo_score and
                    actual.get("total") == expected_total):
                score_details.append(f"{p['name']}: OK ({expected_total}pts)")
            else:
                scoring_ok = False
                score_details.append(
                    f"{p['name']}: expected c={expected_correct_score} cam={expected_camo_score} tot={expected_total}, "
                    f"got c={actual.get('correct')} cam={actual.get('camouflage')} tot={actual.get('total')}"
                )

        add_check("scoring_logic_correct", scoring_ok, "; ".join(score_details))
    else:
        add_check("scoring_logic_correct", False, "Game not settled or missing")
except Exception as e:
    add_check("scoring_logic_correct", False, str(e))

# ── Final result ──────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 4)
passed = passed_count >= 8  # need at least 8/10 to pass

output = {
    "passed": passed,
    "score": score,
    "checks": checks
}
print(json.dumps(output, ensure_ascii=False, indent=2))