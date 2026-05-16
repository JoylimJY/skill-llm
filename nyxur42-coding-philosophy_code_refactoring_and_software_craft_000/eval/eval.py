import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    
    # Find the refactored file
    ws = Path(workspace)
    candidates = list(ws.rglob("game_refactored.js"))
    
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "game_refactored.js not found anywhere in workspace"}]
        }
    
    refactored_path = candidates[0]
    try:
        content = refactored_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 1: Comment-Before-Delete Rule — splice changes must have // OLD: markers
    # The file has 4 uses of .splice(i, 1) in update loops.
    # The skill mandates: comment old code with // OLD: marker before writing new code.
    # ─────────────────────────────────────────────────────────────────────
    old_marker_present = bool(re.search(r'//\s*OLD\s*:', content, re.IGNORECASE))
    checks.append({
        "name": "comment_before_delete_old_marker",
        "passed": old_marker_present,
        "detail": "Expected '// OLD:' marker comments preserving old splice() code before swap-and-pop replacement" if not old_marker_present else "Found // OLD: marker(s) as required by Comment-Before-Delete rule"
    })

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 2: Swap-and-Pop replaces splice in at least one update loop
    # Skill: "Array removal in loops: swap-and-pop instead of splice"
    # Pattern: array[i] = array[array.length-1]; array.pop();
    # OR array[i] = array[array.length-1]; array.length--
    # ─────────────────────────────────────────────────────────────────────
    swap_and_pop = bool(re.search(
        r'\w+\[i\]\s*=\s*\w+\[\w+\.length\s*-\s*1\]',
        content
    ))
    # Also accept the pattern: arr[i] = arr[arr.length-1]; arr.pop()
    swap_and_pop_v2 = bool(re.search(r'\.pop\(\)', content) and re.search(r'\[i\]\s*=\s*\w+\[', content))
    checks.append({
        "name": "swap_and_pop_pattern",
        "passed": swap_and_pop or swap_and_pop_v2,
        "detail": "Expected swap-and-pop array removal pattern replacing .splice(i,1) in at least one update loop" if not (swap_and_pop or swap_and_pop_v2) else "Found swap-and-pop pattern as required"
    })

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 3: Repeated pattern extracted — getUpgradeById helper
    # The UPGRADES.find(u => u.id === X) pattern appears 4 times (>=3 threshold from skill).
    # Skill: "Any pattern that appears 3+ times → helper function"
    # Must create a named function that does the lookup.
    # ─────────────────────────────────────────────────────────────────────
    # Check that inline UPGRADES.find appears fewer times than original (4 → reduced)
    inline_find_count = len(re.findall(r'UPGRADES\.find\(', content))
    # And check that a helper function for upgrade lookup exists
    helper_func = bool(re.search(
        r'function\s+\w*[Uu]pgrade[Bb]y[Ii]d\w*\s*\(|function\s+\w*[Gg]et[Uu]pgrade\w*\s*\(|function\s+\w*[Ff]ind[Uu]pgrade\w*\s*\(',
        content
    ))
    # More flexible: any function that takes an id and searches UPGRADES
    any_lookup_helper = bool(re.search(
        r'function\s+\w+\s*\(\s*\w*[Ii]d\w*\s*\)[\s\S]{0,200}UPGRADES\.find',
        content
    ))
    extracted_pattern = helper_func or any_lookup_helper or (inline_find_count <= 1)
    checks.append({
        "name": "repeated_pattern_extracted",
        "passed": extracted_pattern,
        "detail": f"Expected UPGRADES.find() pattern (appeared 4x) to be extracted into a helper function. Found {inline_find_count} remaining inline uses. Helper detected: {helper_func or any_lookup_helper}" if not extracted_pattern else f"Repeated UPGRADES.find pattern extracted into helper function. Remaining inline uses: {inline_find_count}"
    })

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 4: Data moved to top / Data-Logic separation
    # Skill: "moving all data to the top and all logic below it"
    # UPGRADES array and CREATURE_PARTS must appear before any function definitions
    # ─────────────────────────────────────────────────────────────────────
    upgrades_pos = content.find('UPGRADES')
    creature_parts_pos = content.find('CREATURE_PARTS')
    first_function_pos = content.find('function ')
    
    data_at_top = False
    data_detail = ""
    if upgrades_pos == -1 or first_function_pos == -1:
        data_detail = "Could not find UPGRADES array or function definitions in refactored file"
    elif upgrades_pos < first_function_pos and (creature_parts_pos == -1 or creature_parts_pos < first_function_pos):
        data_at_top = True
        data_detail = f"UPGRADES (pos {upgrades_pos}) and CREATURE_PARTS (pos {creature_parts_pos}) both appear before first function (pos {first_function_pos})"
    else:
        data_detail = f"Data not moved to top: UPGRADES at {upgrades_pos}, CREATURE_PARTS at {creature_parts_pos}, first function at {first_function_pos}"
    
    checks.append({
        "name": "data_logic_separation",
        "passed": data_at_top,
        "detail": data_detail
    })

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 5: Dead code removed — abandonedFeature variable gone
    # Skill: "Remove unused variables"
    # abandonedFeature is declared but never used — must be removed
    # ─────────────────────────────────────────────────────────────────────
    abandoned_removed = 'abandonedFeature' not in content or bool(re.search(r'abandonedFeature\s*[^=]', content) is None and 'abandonedFeature' in content)
    # More precise: it should not be declared as an active variable
    # Check if it's only in a comment or gone entirely
    abandoned_lines = [line for line in content.split('\n') if 'abandonedFeature' in line]
    all_commented = all(line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().startswith('*') for line in abandoned_lines)
    abandoned_cleaned = len(abandoned_lines) == 0 or all_commented
    checks.append({
        "name": "dead_code_removed",
        "passed": abandoned_cleaned,
        "detail": f"abandonedFeature (unused variable) should be removed or commented out. Found {len(abandoned_lines)} active line(s): {abandoned_lines[:2]}" if not abandoned_cleaned else "abandonedFeature unused variable properly removed/commented"
    })

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 6: Parts-Based Rendering Pipeline — save/load fix
    # Skill: "Save/load restoration: don't forget parts!"
    # loadGame() must pass c.parts to addCreature()
    # ─────────────────────────────────────────────────────────────────────
    # Find the loadGame function body
    load_game_match = re.search(r'function\s+loadGame\s*\(\)[^}]*\{([\s\S]*?)(?=\nfunction|\nconst|\nlet|\Z)', content)
    parts_in_load = False
    load_detail = "loadGame function not found"
    
    if load_game_match:
        load_body = load_game_match.group(0)
        # Check if addCreature is called with parts inside loadGame
        add_creature_with_parts = bool(re.search(r'addCreature\s*\([^)]*c\.parts[^)]*\)', load_body))
        add_creature_with_parts_v2 = bool(re.search(r'addCreature\s*\([^)]+,\s*[^)]+\)', load_body))
        parts_in_load = add_creature_with_parts or add_creature_with_parts_v2
        load_detail = f"loadGame body found. addCreature called with parts: {add_creature_with_parts or add_creature_with_parts_v2}"
    else:
        # Try broader search
        load_section = re.search(r'loadGame[\s\S]{0,500}addCreature', content)
        if load_section:
            section_text = load_section.group(0)
            parts_in_load = bool(re.search(r'addCreature\s*\([^)]*\.[Pp]arts', section_text))
            load_detail = f"loadGame->addCreature call found, parts passed: {parts_in_load}"

    checks.append({
        "name": "save_load_parts_fix",
        "passed": parts_in_load,
        "detail": load_detail if not parts_in_load else "loadGame() correctly passes c.parts to addCreature() fixing the save/load restoration bug"
    })

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 7: testDialogue dead variable removed/commented
    # Skill: "Remove unused variables" 
    # testDialogue is clearly a leftover from testing
    # ─────────────────────────────────────────────────────────────────────
    dialogue_lines = [line for line in content.split('\n') if 'testDialogue' in line]
    dialogue_commented_or_gone = len(dialogue_lines) == 0 or all(
        line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().startswith('*')
        for line in dialogue_lines
    )
    checks.append({
        "name": "test_dialogue_cleaned",
        "passed": dialogue_commented_or_gone,
        "detail": f"testDialogue (unused test variable) should be removed. Found {len(dialogue_lines)} active lines." if not dialogue_commented_or_gone else "testDialogue test variable properly cleaned up"
    })

    # ─────────────────────────────────────────────────────────────────────
    # SCORING
    # ─────────────────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks

    # Must pass critical checks to pass overall
    critical_checks = ["comment_before_delete_old_marker", "repeated_pattern_extracted", "save_load_parts_fix"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    
    overall_passed = critical_passed and score >= 0.7

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))