import sys
import os
import ast
import json
import subprocess
import tempfile
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    total_score = 0.0
    max_score = 10.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Find game.py ─────────────────────────────────────────────────────────
    candidates = list(Path(workspace).rglob("game.py"))
    # Exclude old_versions
    candidates = [p for p in candidates if "old_version" not in str(p) and "scratch" not in str(p)]

    if not candidates:
        checks.append({"name": "file_exists", "passed": False, "detail": "game.py not found in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    game_path = candidates[0]
    # Prefer workspace root
    for c in candidates:
        if c.parent == Path(workspace):
            game_path = c
            break

    total_score += add_check("file_exists", True, f"Found game.py at {game_path}", 0.5)

    # ── Syntax check ─────────────────────────────────────────────────────────
    try:
        source = game_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        total_score += add_check("syntax_valid", True, "game.py parses without syntax errors", 0.5)
    except SyntaxError as e:
        total_score += add_check("syntax_valid", False, f"SyntaxError: {e}", 0.5)
        return {"passed": False, "score": total_score / max_score, "checks": checks}
    except Exception as e:
        total_score += add_check("syntax_valid", False, f"Error reading file: {e}", 0.5)
        return {"passed": False, "score": total_score / max_score, "checks": checks}

    # ── Execute and extract game data ─────────────────────────────────────────
    # We'll exec the module-level code (excluding main() call) to inspect data structures
    try:
        # Patch input to avoid blocking
        exec_globals = {"__name__": "__not_main__"}
        patched_source = source.replace('if __name__ == "__main__":', 'if __name__ == "__never__":')
        # Also patch input() calls at module level
        exec(compile(patched_source, str(game_path), "exec"), exec_globals)
        exec_success = True
    except Exception as e:
        exec_success = False
        exec_error = str(e)

    if not exec_success:
        total_score += add_check("module_executes", False, f"Module-level execution failed: {exec_error}", 1.0)
        # Still try static analysis
    else:
        total_score += add_check("module_executes", True, "Module-level code executes without errors", 1.0)

    # ── Check rooms dict ──────────────────────────────────────────────────────
    if exec_success and "rooms" in exec_globals:
        rooms = exec_globals["rooms"]
        try:
            # At least 5 rooms
            num_rooms = len(rooms)
            passed_room_count = num_rooms >= 5
            total_score += add_check(
                "rooms_count_ge5",
                passed_room_count,
                f"Found {num_rooms} rooms (need ≥5)",
                0.5
            )

            # All rooms have required keys
            required_room_keys = {"name", "desc", "exits", "items", "npcs"}
            rooms_valid = all(required_room_keys.issubset(set(r.keys())) for r in rooms.values())
            total_score += add_check(
                "rooms_schema_valid",
                rooms_valid,
                f"All rooms have required keys (name/desc/exits/items/npcs): {rooms_valid}",
                0.5
            )

            # Bidirectional exits consistency
            reverse_map = {"北": "南", "南": "北", "东": "西", "西": "东",
                           "上": "下", "下": "上", "前": "后", "后": "前",
                           "north": "south", "south": "north", "east": "west", "west": "east"}
            inconsistencies = []
            for room_id, room_data in rooms.items():
                for direction, target_id in room_data.get("exits", {}).items():
                    if target_id not in rooms:
                        inconsistencies.append(f"{room_id} -> {direction} -> {target_id} (target missing)")
                        continue
                    reverse_dir = reverse_map.get(direction)
                    if reverse_dir:
                        target_room = rooms[target_id]
                        if reverse_dir not in target_room.get("exits", {}):
                            inconsistencies.append(
                                f"{room_id} -[{direction}]-> {target_id} but {target_id} has no [{reverse_dir}] back"
                            )
            exits_consistent = len(inconsistencies) == 0
            total_score += add_check(
                "exits_bidirectional",
                exits_consistent,
                f"Exit consistency: {'OK' if exits_consistent else 'Issues: ' + '; '.join(inconsistencies[:3])}",
                1.0
            )

            # At least one locked room
            locked_rooms = [rid for rid, r in rooms.items() if r.get("locked") == True]
            has_locked = len(locked_rooms) >= 1
            total_score += add_check(
                "has_locked_room",
                has_locked,
                f"Locked rooms found: {locked_rooms}" if has_locked else "No room with 'locked': True found",
                0.5
            )

        except Exception as e:
            total_score += add_check("rooms_analysis", False, f"Error analyzing rooms: {e}", 2.5)
    else:
        total_score += add_check("rooms_dict_present", False, "No 'rooms' dict found in module", 2.5)

    # ── Check npcs dict ───────────────────────────────────────────────────────
    if exec_success and "npcs" in exec_globals:
        npcs = exec_globals["npcs"]
        try:
            num_npcs = len(npcs)
            total_score += add_check(
                "npcs_count_ge2",
                num_npcs >= 2,
                f"Found {num_npcs} NPCs (need ≥2)",
                0.5
            )

            required_npc_keys = {"name", "desc", "hp", "attack", "dialogue", "hostile"}
            npcs_schema_valid = all(required_npc_keys.issubset(set(n.keys())) for n in npcs.values())
            total_score += add_check(
                "npcs_schema_valid",
                npcs_schema_valid,
                f"All NPCs have required keys: {npcs_schema_valid}",
                0.5
            )

            # At least one hostile NPC with hp > 0 and attack > 0
            hostile_npcs = [nid for nid, n in npcs.items()
                           if n.get("hostile") == True and n.get("hp", 0) > 0 and n.get("attack", 0) > 0]
            has_hostile = len(hostile_npcs) >= 1
            total_score += add_check(
                "has_hostile_npc",
                has_hostile,
                f"Hostile NPC(s) with hp>0 and attack>0: {hostile_npcs}" if has_hostile else "No valid hostile NPC found",
                0.5
            )

            # At least one friendly NPC (hostile=False)
            friendly_npcs = [nid for nid, n in npcs.items() if n.get("hostile") == False]
            has_friendly = len(friendly_npcs) >= 1
            total_score += add_check(
                "has_friendly_npc",
                has_friendly,
                f"Friendly NPC(s): {friendly_npcs}" if has_friendly else "No friendly NPC found",
                0.3
            )

        except Exception as e:
            total_score += add_check("npcs_analysis", False, f"Error analyzing npcs: {e}", 1.8)
    else:
        total_score += add_check("npcs_dict_present", False, "No 'npcs' dict found in module", 1.8)

    # ── Check items dict ──────────────────────────────────────────────────────
    if exec_success and "items" in exec_globals:
        items = exec_globals["items"]
        try:
            num_items = len(items)
            total_score += add_check(
                "items_count_ge3",
                num_items >= 3,
                f"Found {num_items} items (need ≥3)",
                0.3
            )

            has_heal = any(v.get("effect") == "heal" for v in items.values())
            has_power = any(v.get("effect") == "power" for v in items.values())

            total_score += add_check(
                "item_heal_effect",
                has_heal,
                "At least one item with effect='heal' found" if has_heal else "No item with effect='heal'",
                0.3
            )
            total_score += add_check(
                "item_power_effect",
                has_power,
                "At least one item with effect='power' found" if has_power else "No item with effect='power'",
                0.3
            )

        except Exception as e:
            total_score += add_check("items_analysis", False, f"Error analyzing items: {e}", 0.9)
    else:
        total_score += add_check("items_dict_present", False, "No 'items' dict found in module", 0.9)

    # ── Check player flags pre-declared ──────────────────────────────────────
    if exec_success and "player" in exec_globals:
        player = exec_globals["player"]
        try:
            flags = player.get("flags", {})
            # Must have at least 2 flags pre-declared (quest tracking)
            has_flags = isinstance(flags, dict) and len(flags) >= 2
            total_score += add_check(
                "player_flags_predeclared",
                has_flags,
                f"player['flags'] has {len(flags)} pre-declared keys: {list(flags.keys())}" if isinstance(flags, dict)
                else "player['flags'] is not a dict",
                0.5
            )

            # Must include "有钥匙" key tracking (key-flag logic)
            # Check source code for "有钥匙" pattern
            has_key_flag = "有钥匙" in source
            total_score += add_check(
                "key_flag_wired",
                has_key_flag,
                "Source contains '有钥匙' flag reference (key pickup mechanism)" if has_key_flag
                else "Missing '有钥匙' flag — locked room key mechanism not wired",
                0.5
            )

        except Exception as e:
            total_score += add_check("player_analysis", False, f"Error analyzing player: {e}", 1.0)
    else:
        total_score += add_check("player_dict_present", False, "No 'player' dict found in module", 1.0)

    # ── Check combat function exists and has unlock logic ────────────────────
    try:
        has_combat_func = "def combat" in source
        total_score += add_check(
            "combat_function_exists",
            has_combat_func,
            "combat() function defined in source" if has_combat_func else "No combat() function found",
            0.5
        )

        # Combat should reference room unlock (locked=False or flags update)
        has_unlock_logic = ('locked"] = False' in source or "locked'] = False" in source or
                           '"locked": False' in source or "'locked': False" in source)
        total_score += add_check(
            "combat_unlock_logic",
            has_unlock_logic,
            "Source contains room unlock logic after combat (locked=False)" if has_unlock_logic
            else "No room-unlock logic found — defeating boss won't open locked room",
            0.5
        )
    except Exception as e:
        total_score += add_check("combat_analysis", False, f"Error: {e}", 1.0)

    # ── Theme check: underwater/ocean related ─────────────────────────────────
    try:
        ocean_keywords = ["海", "深海", "水下", "潜水", "海底", "深渊", "鱼", "章鱼", "珊瑚",
                         "ocean", "sea", "deep", "underwater", "submarine", "aqua", "coral", "abyss"]
        desc_text = ""
        if exec_success and "rooms" in exec_globals:
            for r in exec_globals["rooms"].values():
                desc_text += r.get("desc", "") + r.get("name", "")
        if exec_success and "npcs" in exec_globals:
            for n in exec_globals["npcs"].values():
                desc_text += n.get("desc", "") + n.get("name", "")

        is_ocean_themed = any(kw in desc_text for kw in ocean_keywords)
        total_score += add_check(
            "ocean_theme",
            is_ocean_themed,
            "Game content contains ocean/underwater theme keywords" if is_ocean_themed
            else "No ocean/underwater theme detected in room/NPC descriptions",
            0.5
        )
    except Exception as e:
        total_score += add_check("theme_check", False, f"Error: {e}", 0.5)

    # ── Runtime smoke test ────────────────────────────────────────────────────
    try:
        # Simulate: look, go <first_exit>, take <first_item_if_any>, inventory, quit
        if exec_success and "rooms" in exec_globals and "player" in exec_globals:
            rooms_data = exec_globals["rooms"]
            player_data = exec_globals["player"]
            start_loc = player_data.get("location", list(rooms_data.keys())[0])
            first_exit_dir = list(rooms_data[start_loc]["exits"].keys())[0] if rooms_data[start_loc]["exits"] else "北"
            first_item = rooms_data[start_loc]["items"][0] if rooms_data[start_loc].get("items") else None

            inputs = ["look", f"go {first_exit_dir}"]
            if first_item:
                inputs.append(f"take {first_item}")
            inputs += ["inventory", "status", "quit"]
            stdin_data = "\n".join(inputs) + "\n"

            result = subprocess.run(
                [sys.executable, str(game_path)],
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=15
            )
            runtime_ok = result.returncode == 0
            detail = f"returncode={result.returncode}"
            if not runtime_ok:
                detail += f" stderr={result.stderr[:200]}"
            total_score += add_check(
                "runtime_smoke_test",
                runtime_ok,
                detail,
                1.0
            )
        else:
            total_score += add_check("runtime_smoke_test", False, "Skipped: module data unavailable", 1.0)
    except subprocess.TimeoutExpired:
        total_score += add_check("runtime_smoke_test", False, "Timeout: game hung waiting for input", 1.0)
    except Exception as e:
        total_score += add_check("runtime_smoke_test", False, f"Runtime error: {e}", 1.0)

    # ── Final scoring ─────────────────────────────────────────────────────────
    # Normalize to 0-1 range
    # Count critical checks: module_executes, exits_bidirectional, has_hostile_npc, key_flag_wired, combat_unlock_logic, runtime_smoke_test
    critical_checks = {
        "module_executes", "exits_bidirectional", "has_hostile_npc",
        "key_flag_wired", "combat_unlock_logic", "runtime_smoke_test"
    }
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    score = round(total_score / max_score, 3)

    overall_passed = (
        critical_passed and
        passed_count >= int(total_count * 0.75) and
        score >= 0.65
    )

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(ws)
    print(json.dumps(result, ensure_ascii=False, indent=2))