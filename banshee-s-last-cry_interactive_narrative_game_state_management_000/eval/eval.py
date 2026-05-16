import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # Find game_state.json
    game_state_path = None
    candidates = list(Path(workspace_dir).rglob("game_state.json"))
    # Prefer the one directly in workspace, not in backup/
    for c in candidates:
        if "backup" not in str(c) and "partial" not in str(c).lower():
            game_state_path = c
            break
    if game_state_path is None and candidates:
        game_state_path = candidates[0]

    if game_state_path is None:
        add_check("game_state.json exists", False, "No game_state.json found in workspace", weight=3.0)
        return checks, 0.0

    add_check("game_state.json exists", True, f"Found at {game_state_path}", weight=1.0)

    # Load and parse JSON
    try:
        with open(game_state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception as e:
        add_check("game_state.json is valid JSON", False, f"JSON parse error: {e}", weight=3.0)
        return checks, 0.0

    add_check("game_state.json is valid JSON", True, "File parsed successfully", weight=1.0)

    # ---- CHECK 1: game_version must be "0.0.2" (proprietary trap: old version 0.0.1 is a distractor) ----
    version = state.get("game_version", "")
    add_check(
        "game_version is '0.0.2'",
        version == "0.0.2",
        f"Expected '0.0.2', got '{version}'. The ch00_start.md specifies v0.0.2, not the 0.0.1 in backup files.",
        weight=1.5
    )

    # ---- CHECK 2: player_name must be "透" ----
    player_name = state.get("player_name", "")
    add_check(
        "player_name is '透'",
        player_name == "透",
        f"Expected '透', got '{player_name}'",
        weight=1.0
    )

    # ---- CHECK 3: current_chapter must be "ch2b_suspect" (progressed through both chapters) ----
    current_chapter = state.get("current_chapter", "")
    add_check(
        "current_chapter is 'ch2b_suspect'",
        current_chapter == "ch2b_suspect",
        f"Expected 'ch2b_suspect' (after completing ch00→ch1a→ch2b flow), got '{current_chapter}'",
        weight=2.0
    )

    # ---- CHECK 4: chapter_history must include all 3 chapters in order ----
    chapter_history = state.get("chapter_history", [])
    required_chapters = ["ch00_start", "ch1a_investigate", "ch2b_suspect"]
    history_ok = all(ch in chapter_history for ch in required_chapters)
    # Also check order
    if history_ok:
        indices = [chapter_history.index(ch) for ch in required_chapters]
        history_ok = indices == sorted(indices)
    add_check(
        "chapter_history contains all 3 chapters in order",
        history_ok,
        f"chapter_history = {chapter_history}. Must contain ch00_start, ch1a_investigate, ch2b_suspect in order.",
        weight=2.0
    )

    # ---- CHECK 5: alive_characters must use the Japanese-name characters from ch00_start.md ----
    # NOT the Chinese names from SKILL.md overview (李明, 王芳, etc.)
    alive = state.get("alive_characters", [])
    required_alive = {"透", "真理", "小林敏夫", "小林惠子", "佐藤健", "铃木美香", "田边晃", "大阪龙一", "大阪绫子"}
    # 田中一郎 should be dead
    wrong_names = {"李明", "王芳", "张伟", "刘洋", "陈静", "赵磊"}
    no_wrong_names = not any(n in alive for n in wrong_names)
    has_correct_alive = required_alive.issubset(set(alive))
    add_check(
        "alive_characters uses correct character names from ch00_start.md (not SKILL.md overview names)",
        has_correct_alive and no_wrong_names,
        f"alive_characters={alive}. Must contain {required_alive} and must NOT contain {wrong_names}.",
        weight=2.5
    )

    # ---- CHECK 6: 田中一郎 must be in dead_characters ----
    dead = state.get("dead_characters", [])
    tanaka_dead = "田中一郎" in dead
    add_check(
        "田中一郎 is in dead_characters",
        tanaka_dead,
        f"dead_characters={dead}. 田中一郎 died in ch00_start and must be in dead_characters.",
        weight=2.0
    )

    # ---- CHECK 7: 田中一郎 must NOT be in alive_characters ----
    tanaka_not_alive = "田中一郎" not in alive
    add_check(
        "田中一郎 is NOT in alive_characters",
        tanaka_not_alive,
        f"alive_characters={alive}. Dead characters must be removed from alive list.",
        weight=1.0
    )

    # ---- CHECK 8: Initial trust levels preserved or updated per ch2b rules ----
    trust = state.get("trust_levels", {})
    # 真理 must remain 100 (no reason to reduce)
    mari_trust_ok = trust.get("真理", 0) == 100
    add_check(
        "真理's trust_level remains 100",
        mari_trust_ok,
        f"trust_levels['真理']={trust.get('真理', 'MISSING')}. Should be 100 (unchanged).",
        weight=1.0
    )
    # 小林敏夫 should be reduced after confession in ch2b (from 50 → 15)
    kobayashi_trust = trust.get("小林敏夫", 999)
    kobayashi_reduced = kobayashi_trust < 50
    add_check(
        "小林敏夫's trust_level reduced after confession in ch2b",
        kobayashi_reduced,
        f"trust_levels['小林敏夫']={kobayashi_trust}. Should be reduced below 50 after bribe revelation in ch2b_suspect.",
        weight=1.5
    )
    # 大阪龙一 should be reduced after confrontation in ch2b (from 35 → 10)
    osaka_trust = trust.get("大阪龙一", 999)
    osaka_reduced = osaka_trust < 35
    add_check(
        "大阪龙一's trust_level reduced after confrontation in ch2b",
        osaka_reduced,
        f"trust_levels['大阪龙一']={osaka_trust}. Should be reduced below 35 after confrontation in ch2b_suspect.",
        weight=1.5
    )

    # ---- CHECK 9: suspicion_points for key suspects ----
    suspicion = state.get("suspicion_points", {})
    # 小林敏夫 should have suspicion points > 0
    kobayashi_susp = suspicion.get("小林敏夫", 0)
    add_check(
        "小林敏夫 has suspicion_points > 0",
        kobayashi_susp > 0,
        f"suspicion_points['小林敏夫']={kobayashi_susp}. Should be positive after confession.",
        weight=1.5
    )
    # 大阪龙一 should have higher suspicion
    osaka_susp = suspicion.get("大阪龙一", 0)
    add_check(
        "大阪龙一 has suspicion_points > 0",
        osaka_susp > 0,
        f"suspicion_points['大阪龙一']={osaka_susp}. Should be positive after confrontation.",
        weight=1.5
    )

    # ---- CHECK 10: collected_clues must have at least 2 clues from ch1a ----
    clues = state.get("collected_clues", [])
    clues_from_ch1a = [c for c in clues if isinstance(c, dict) and c.get("found_in") == "ch1a_investigate"]
    add_check(
        "At least 2 clues collected from ch1a_investigate",
        len(clues_from_ch1a) >= 2,
        f"Found {len(clues_from_ch1a)} clues with found_in='ch1a_investigate'. Need at least 2.",
        weight=2.0
    )

    # ---- CHECK 11: Clue structure must include Chinese field "真实性" ----
    # This is the most proprietary trap - the field name is in Chinese
    clues_with_zhenshixing = [
        c for c in clues
        if isinstance(c, dict) and "真实性" in c
    ]
    add_check(
        "Clues contain the required '真实性' field (Chinese field name)",
        len(clues_with_zhenshixing) >= 1,
        f"Only {len(clues_with_zhenshixing)}/{len(clues)} clues have '真实性' field. "
        "This field is specified in system_clue_system.md and ch1a_investigate.md. "
        "Generic agents will miss this Chinese-named required field.",
        weight=2.5
    )

    # ---- CHECK 12: Clue structure must have all required fields ----
    required_clue_fields = {"id", "name", "description", "importance", "found_in",
                             "found_at", "category", "points_to", "related_clues", "真实性"}
    if clues:
        # Check first clue from ch1a specifically
        ch1a_clue = clues_from_ch1a[0] if clues_from_ch1a else (clues[0] if clues else None)
        if ch1a_clue:
            missing_fields = required_clue_fields - set(ch1a_clue.keys())
            add_check(
                "Clue objects contain all required fields including 'points_to', 'related_clues', '真实性'",
                len(missing_fields) == 0,
                f"Missing fields in clue: {missing_fields}. Clue keys: {set(ch1a_clue.keys())}",
                weight=2.0
            )
        else:
            add_check("Clue objects contain all required fields", False, "No clues found to check", weight=2.0)
    else:
        add_check("Clue objects contain all required fields", False, "collected_clues is empty", weight=2.0)

    # ---- CHECK 13: discovered_secrets mentions the bribe/cover-up ----
    secrets = state.get("discovered_secrets", [])
    bribe_discovered = any(
        "贿赂" in str(s) or "收受" in str(s) or "封口" in str(s) or "掩盖" in str(s)
        for s in secrets
    )
    add_check(
        "discovered_secrets includes small林's bribe/cover-up revelation",
        bribe_discovered,
        f"discovered_secrets={secrets}. Must include revelation about 小林 accepting bribe to cover up the 20-year-old accident.",
        weight=1.5
    )

    # ---- CHECK 14: player_choices has entry for ch2b confrontation ----
    player_choices = state.get("player_choices", [])
    ch2b_choice = any(
        isinstance(c, dict) and c.get("chapter") == "ch2b_suspect"
        for c in player_choices
    )
    add_check(
        "player_choices contains entry for ch2b_suspect chapter",
        ch2b_choice,
        f"player_choices={player_choices}. Must have entry with chapter='ch2b_suspect'.",
        weight=1.5
    )

    # ---- CHECK 15: scene_progress updated for ch2b ----
    scene_progress = state.get("scene_progress", "")
    # Should not still be "scene1_arrival" from ch00
    not_initial = scene_progress != "scene1_arrival" and scene_progress != ""
    add_check(
        "scene_progress updated beyond initial 'scene1_arrival'",
        not_initial,
        f"scene_progress='{scene_progress}'. Should be updated from initial 'scene1_arrival' after progressing through chapters.",
        weight=1.0
    )

    # ---- CHECK 16: mental_state is an integer between 0-100 ----
    mental = state.get("mental_state", None)
    mental_ok = isinstance(mental, (int, float)) and 0 <= mental <= 100
    add_check(
        "mental_state is a valid integer 0-100",
        mental_ok,
        f"mental_state={mental}. Should be integer between 0-100.",
        weight=0.5
    )

    # ---- CHECK 17: time_elapsed updated from initial value ----
    time_elapsed = state.get("time_elapsed", "")
    # Should not still be "第一天晚上6点" (the very start)
    # After ch2b it should be around "第一天晚上11点30分" or later
    time_updated = time_elapsed != "第一天晚上6点" and time_elapsed != ""
    add_check(
        "time_elapsed updated from initial '第一天晚上6点'",
        time_updated,
        f"time_elapsed='{time_elapsed}'. Should advance past initial '第一天晚上6点' as game progresses.",
        weight=1.0
    )

    # ---- CHECK 18: All required top-level fields exist ----
    required_top_fields = [
        "player_name", "current_chapter", "scene_progress", "interaction_count",
        "chapter_history", "alive_characters", "dead_characters", "collected_clues",
        "trust_levels", "suspicion_points", "player_choices", "discovered_secrets",
        "mental_state", "time_elapsed", "game_version"
    ]
    missing_top = [f for f in required_top_fields if f not in state]
    add_check(
        "All required top-level fields present in game_state.json",
        len(missing_top) == 0,
        f"Missing top-level fields: {missing_top}",
        weight=1.5
    )

    # Compute final score
    final_score = total_score / max_score if max_score > 0 else 0.0
    return checks, final_score


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace_dir = sys.argv[1]
    checks, score = evaluate(workspace_dir)
    passed = score >= 0.65  # Need 65% to pass

    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))