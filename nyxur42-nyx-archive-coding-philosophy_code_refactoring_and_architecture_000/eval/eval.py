import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)
    target_file = workspace / "src" / "refactored_game.js"

    # ─── 0. File existence ────────────────────────────────────────────────────
    if not target_file.exists():
        # Also search anywhere in workspace in case agent placed it elsewhere
        found = list(workspace.rglob("refactored_game.js"))
        if found:
            target_file = found[0]
        else:
            checks.append({"name": "file_exists", "passed": False,
                           "detail": "refactored_game.js not found anywhere in workspace"})
            score = 0.0
            return {"passed": False, "score": score, "checks": checks}

    checks.append({"name": "file_exists", "passed": True,
                   "detail": f"Found at {target_file}"})

    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": "File read successfully"})

    # ─── 1. Comment-Before-Delete Rule ──────────────────────────────────────
    # Old summonCreature function must be COMMENTED OUT with // OLD: marker, not deleted
    # The SKILL.md says: comment out old code with "// OLD:" marker + brief explanation
    
    has_old_marker = bool(re.search(r'//\s*OLD\s*:', content))
    checks.append({
        "name": "comment_before_delete_OLD_marker",
        "passed": has_old_marker,
        "detail": ("Found '// OLD:' comment marker — old code was commented, not deleted"
                   if has_old_marker else
                   "MISSING '// OLD:' marker. Per coding philosophy, old code must be commented "
                   "with '// OLD:' before writing new code, not deleted outright.")
    })

    # Old summonCreature body should be preserved in a comment block (/* ... */)
    old_code_commented = bool(re.search(r'/\*[\s\S]*?summonCreature[\s\S]*?\*/', content))
    checks.append({
        "name": "old_summonCreature_commented_not_deleted",
        "passed": old_code_commented,
        "detail": ("Old summonCreature code found preserved in a block comment"
                   if old_code_commented else
                   "Old summonCreature function not found in a block comment. "
                   "It should be commented with /* */ block, not simply deleted.")
    })

    # ─── 2. Helper function extracted for repeated pattern ───────────────────
    # 4 instances of CREATURE_TYPES.find(t => t.id === X) must be replaced by a helper
    # SKILL.md: "if 3+ places do the same dance, that's a function waiting to be born"
    
    # Count remaining raw inline find() calls for creature type lookup
    inline_find_count = len(re.findall(
        r'CREATURE_TYPES\.find\s*\(\s*t\s*=>\s*t\.id\s*===', content
    ))
    # The helper function should exist
    has_helper_fn = bool(re.search(
        r'function\s+\w+\s*\(\s*\w+\s*\)\s*\{[^}]*CREATURE_TYPES\.find', content
    ))
    # Or an arrow function assigned to a const
    has_helper_arrow = bool(re.search(
        r'const\s+\w+\s*=\s*\(?[^)]*\)?\s*=>\s*(?:\{[^}]*\}|CREATURE_TYPES\.find)', content
    ))
    helper_exists = has_helper_fn or has_helper_arrow
    
    checks.append({
        "name": "repeated_pattern_extracted_to_helper",
        "passed": helper_exists,
        "detail": (f"Helper function found that wraps CREATURE_TYPES.find lookup"
                   if helper_exists else
                   "No helper function found. The 4 repeated CREATURE_TYPES.find() calls "
                   "must be extracted into a named helper (SKILL.md: 3+ repetitions = extract helper).")
    })

    # After extraction, inline find calls should be reduced (max 1 remaining in helper itself)
    inline_reduced = inline_find_count <= 1
    checks.append({
        "name": "inline_find_calls_reduced",
        "passed": inline_reduced,
        "detail": (f"Inline CREATURE_TYPES.find calls reduced to {inline_find_count} (acceptable ≤1)"
                   if inline_reduced else
                   f"Still {inline_find_count} raw CREATURE_TYPES.find() calls found. "
                   "These should be consolidated into the extracted helper function.")
    })

    # ─── 3. Hot-path Map cache ───────────────────────────────────────────────
    # SKILL.md: "Object searches (find, filter) in loops → pre-index with a Map"
    # updateCreatures runs 60fps — must use Map instead of find()
    
    has_map_index = bool(re.search(r'new\s+Map\s*\(', content))
    checks.append({
        "name": "hot_path_map_cache",
        "passed": has_map_index,
        "detail": ("Map pre-index found — hot-path .find() in game loop replaced with Map lookup"
                   if has_map_index else
                   "No Map() found. The CREATURE_TYPES.find() call inside updateCreatures() "
                   "runs 60fps per creature and must be replaced with a pre-indexed Map "
                   "(SKILL.md: Object searches in loops → pre-index with a Map).")
    })

    # updateCreatures should NOT contain a raw .find() on CREATURE_TYPES anymore
    # Find the updateCreatures function body
    update_fn_match = re.search(
        r'function\s+updateCreatures\s*\([^)]*\)\s*\{([\s\S]*?)(?=\n(?:function|const|let|var|//\s*----|$))',
        content
    )
    if update_fn_match:
        update_body = update_fn_match.group(1)
        find_in_hot_path = bool(re.search(r'CREATURE_TYPES\.find', update_body))
        checks.append({
            "name": "no_find_in_hot_path_loop",
            "passed": not find_in_hot_path,
            "detail": ("updateCreatures no longer calls CREATURE_TYPES.find() — hot path is clean"
                       if not find_in_hot_path else
                       "updateCreatures still calls CREATURE_TYPES.find() on every frame. "
                       "Must use pre-indexed Map for 60fps hot path.")
        })
    else:
        checks.append({
            "name": "no_find_in_hot_path_loop",
            "passed": False,
            "detail": "Could not locate updateCreatures function to verify hot path fix."
        })

    # ─── 4. Data at top / Logic below (organize by concern) ─────────────────
    # SKILL.md: "moving all data to the top and all logic below it"
    # CREATURE_TYPES data should appear before function definitions
    
    ct_pos = content.find("CREATURE_TYPES")
    first_fn_pos = content.find("function ")
    
    data_before_logic = (ct_pos != -1 and first_fn_pos != -1 and ct_pos < first_fn_pos)
    checks.append({
        "name": "data_organized_before_logic",
        "passed": data_before_logic,
        "detail": (f"CREATURE_TYPES data appears before function definitions (pos {ct_pos} < {first_fn_pos})"
                   if data_before_logic else
                   "CREATURE_TYPES data does not appear before function definitions. "
                   "SKILL.md: highest-value refactor is moving all data to top, all logic below.")
    })

    # Summon dialogue lines (SUMMON_LINES) should be extracted to top as data, not inside function
    summon_lines_in_fn = bool(re.search(
        r'function\s+\w+[^}]*SUMMON_LINES\s*=\s*\[', content, re.DOTALL
    ))
    summon_lines_at_top = bool(re.search(r'const\s+SUMMON_LINES\s*=\s*\[', content))
    summon_data_extracted = summon_lines_at_top and not summon_lines_in_fn
    checks.append({
        "name": "dialogue_data_extracted_from_function",
        "passed": summon_data_extracted,
        "detail": ("SUMMON_LINES extracted from function body to top-level data"
                   if summon_data_extracted else
                   "SUMMON_LINES still defined inside a function. "
                   "Dialogue data should be moved to the top data section (data/logic separation).")
    })

    # ─── 5. Save migration for stamina → energy rename ───────────────────────
    # SKILL.md: "When renaming/removing game state fields, add migration code in loadGame()"
    # Pattern: if (State.creatures[i].stamina) { State.creatures[i].energy = ...; delete ...; }
    
    has_stamina_migration = bool(re.search(
        r'stamina[\s\S]{0,200}energy|energy[\s\S]{0,200}stamina',
        content
    ))
    # More specific: should have delete of stamina field in migration
    has_delete_stamina = bool(re.search(r'delete\s+\S*\.stamina', content))
    # And the new field should be 'energy'
    uses_energy_field = bool(re.search(r'\.energy\b', content))
    
    migration_complete = has_stamina_migration and has_delete_stamina and uses_energy_field
    checks.append({
        "name": "save_migration_stamina_to_energy",
        "passed": migration_complete,
        "detail": (f"Save migration found: stamina→energy, delete old field. energy field in use."
                   if migration_complete else
                   f"Save migration incomplete. stamina_migration:{has_stamina_migration}, "
                   f"delete_stamina:{has_delete_stamina}, uses_energy:{uses_energy_field}. "
                   "SKILL.md: when renaming state fields, add migration in loadGame() that "
                   "copies old field to new field then deletes it.")
    })

    # Migration should be inside loadGame function
    load_fn_match = re.search(
        r'function\s+loadGame\s*\([^)]*\)\s*\{([\s\S]*?)(?=\nfunction\s|\nconst\s+[A-Z]|\n//\s*----|$)',
        content
    )
    if load_fn_match:
        load_body = load_fn_match.group(1)
        migration_in_load = bool(re.search(r'stamina', load_body)) and bool(re.search(r'energy', load_body))
        checks.append({
            "name": "migration_inside_loadGame",
            "passed": migration_in_load,
            "detail": ("Migration code correctly placed inside loadGame() function"
                       if migration_in_load else
                       "Migration code not found inside loadGame(). "
                       "SKILL.md pattern: migration belongs in loadGame() so old saves are upgraded on load.")
        })
    else:
        checks.append({
            "name": "migration_inside_loadGame",
            "passed": False,
            "detail": "Could not locate loadGame() function to verify migration placement."
        })

    # ─── 6. Ghost variables removed (or commented) ──────────────────────────
    # LEGACY_COLORS, comboMultiplier, comboTimer, leaderboardCache are dead code
    # Per SKILL.md: dead code should be cleaned in structure mode
    # (They may be commented out with OLD: marker OR removed — but if present uncommented and unused, that's a fail)
    
    ghost_vars = ['LEGACY_COLORS', 'comboMultiplier', 'comboTimer', 'leaderboardCache']
    active_ghosts = []
    for ghost in ghost_vars:
        # Check if the variable is declared (not in a comment) and appears only once (declaration, never used)
        # Count non-comment occurrences
        lines_with_ghost = [
            line for line in content.split('\n')
            if ghost in line and not line.strip().startswith('//')
        ]
        if len(lines_with_ghost) >= 1:
            # Check if it appears in /* */ block comments
            # Remove block comments then check
            no_block_comments = re.sub(r'/\*[\s\S]*?\*/', '', content)
            no_line_comments = re.sub(r'//[^\n]*', '', no_block_comments)
            occurrences = len(re.findall(r'\b' + re.escape(ghost) + r'\b', no_line_comments))
            if occurrences >= 1:
                active_ghosts.append(ghost)

    ghosts_cleaned = len(active_ghosts) == 0
    checks.append({
        "name": "ghost_variables_cleaned",
        "passed": ghosts_cleaned,
        "detail": (f"All ghost variables cleaned (commented or removed)"
                   if ghosts_cleaned else
                   f"Ghost variables still active (not commented/removed): {active_ghosts}. "
                   "SKILL.md: Remove unused variables when shifting to structure mode.")
    })

    # ─── 7. New summon function exists (NEW: code written) ──────────────────
    # The old summonCreature should be replaced by a new, cleaner version
    # Per comment-before-delete: new code must ALSO exist below the commented old code
    
    # Count function definitions named summon* or createCreature or spawnCreature
    new_summon_fns = re.findall(
        r'function\s+(summon\w*|create\w*|spawn\w*)\s*\(', content, re.IGNORECASE
    )
    # At least one new summon-type function should exist that is NOT inside a block comment
    no_block_comments_content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    active_summon_fns = re.findall(
        r'function\s+(summon\w*|create\w*|spawn\w*)\s*\(', no_block_comments_content, re.IGNORECASE
    )
    has_new_summon = len(active_summon_fns) >= 1
    checks.append({
        "name": "new_replacement_function_exists",
        "passed": has_new_summon,
        "detail": (f"New summon/create function found: {active_summon_fns}"
                   if has_new_summon else
                   "No active summon/create creature function found. "
                   "Comment-before-delete requires NEW code to exist below commented old code.")
    })

    # ─── Final scoring ────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 3)
    
    # Must pass all critical checks to pass overall
    critical_checks = [
        "file_exists",
        "comment_before_delete_OLD_marker",
        "hot_path_map_cache",
        "save_migration_stamina_to_energy",
        "repeated_pattern_extracted_to_helper",
    ]
    critical_passed = all(
        any(c["name"] == cc and c["passed"] for c in checks)
        for cc in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))