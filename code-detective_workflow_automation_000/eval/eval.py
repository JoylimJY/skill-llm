import sys
import json
import os
from pathlib import Path

def load_fixture(workspace):
    """Find the output fixture file."""
    candidates = list(Path(workspace).rglob("medium_session_fixture.json"))
    if not candidates:
        return None, "File 'medium_session_fixture.json' not found anywhere in workspace"
    # Prefer the one not in 'old' dirs
    for c in candidates:
        if 'old' not in str(c):
            return c, None
    return candidates[0], None

def check_structure(data):
    """Check that data is a list of message objects."""
    if not isinstance(data, list):
        return False, f"Root element must be a JSON array of messages, got {type(data).__name__}"
    if len(data) < 4:
        return False, f"Expected at least 4 messages in session (intro + 3 questions + finale), got {len(data)}"
    return True, f"Array with {len(data)} messages"

def check_all_messages_have_required_fields(data):
    """Every bot message must have action, channel, target, message fields."""
    issues = []
    for i, msg in enumerate(data):
        if not isinstance(msg, dict):
            issues.append(f"Message {i} is not a dict")
            continue
        for field in ["action", "channel", "target", "message"]:
            if field not in msg:
                issues.append(f"Message {i} missing field '{field}'")
        if msg.get("action") != "send":
            issues.append(f"Message {i}: action must be 'send', got '{msg.get('action')}'")
        if msg.get("channel") != "telegram":
            issues.append(f"Message {i}: channel must be 'telegram', got '{msg.get('channel')}'")
        if msg.get("target") != "user_77042":
            issues.append(f"Message {i}: target must be 'user_77042', got '{msg.get('target')}'")
    if issues:
        return False, "; ".join(issues[:5])
    return True, "All messages have required fields with correct values"

def check_buttons_nested_arrays(data):
    """Buttons must be nested arrays (array of arrays of button objects)."""
    issues = []
    for i, msg in enumerate(data):
        if not isinstance(msg, dict):
            continue
        if "buttons" not in msg:
            continue
        buttons = msg["buttons"]
        if not isinstance(buttons, list):
            issues.append(f"Message {i}: buttons must be a list, got {type(buttons).__name__}")
            continue
        for j, row in enumerate(buttons):
            if not isinstance(row, list):
                issues.append(f"Message {i}, button row {j}: each row must be a list (nested array), got {type(row).__name__}")
                continue
            for k, btn in enumerate(row):
                if not isinstance(btn, dict):
                    issues.append(f"Message {i}, row {j}, btn {k}: button must be a dict")
                    continue
                if "text" not in btn:
                    issues.append(f"Message {i}, row {j}, btn {k}: missing 'text'")
                if "callback_data" not in btn:
                    issues.append(f"Message {i}, row {j}, btn {k}: missing 'callback_data'")
    if issues:
        return False, "; ".join(issues[:5])
    return True, "All buttons use correct nested array format"

def check_callback_data_prefixes(data):
    """callback_data must use hint:qN or skip:qN or next:qN patterns."""
    import re
    valid_patterns = [
        r'^hint:q\d+$',
        r'^skip:q\d+$', 
        r'^next:q\d+$',
        r'^play_again$',
        r'^difficulty:\w+$',
        r'^replay$',
        r'^easy$', r'^medium$', r'^hard$',
    ]
    issues = []
    found_hint = False
    found_skip = False
    
    for i, msg in enumerate(data):
        if not isinstance(msg, dict) or "buttons" not in msg:
            continue
        for row in msg["buttons"]:
            if not isinstance(row, list):
                continue
            for btn in row:
                if not isinstance(btn, dict):
                    continue
                cd = btn.get("callback_data", "")
                if re.match(r'^hint:q\d+$', cd):
                    found_hint = True
                if re.match(r'^skip:q\d+$', cd):
                    found_skip = True
                # Check format is reasonable (colon-separated or known keyword)
                if cd and not any(re.match(p, cd) for p in valid_patterns):
                    # Allow some flexibility but must have structured format
                    if ':' not in cd and cd not in ['play_again', 'replay', 'easy', 'medium', 'hard']:
                        issues.append(f"Suspicious callback_data format: '{cd}'")
    
    if not found_hint:
        issues.append("No hint:qN callback_data found — hint button missing from question messages")
    if not found_skip:
        issues.append("No skip:qN callback_data found — skip button missing from question messages")
    
    if issues:
        return False, "; ".join(issues[:5])
    return True, "callback_data uses correct hint:qN / skip:qN prefixes"

def check_medium_difficulty_bugs(data):
    """Questions must contain JavaScript or logical bugs (medium difficulty)."""
    all_messages = " ".join(msg.get("message", "") for msg in data if isinstance(msg, dict))
    
    # Medium should have logical errors (JS var/let, logical bugs, etc.)
    medium_indicators = [
        "var", "let", "const", "setTimeout", "===", "==",  # JS patterns
        "логическ", "паттерн",  # Russian descriptors
        "await", "this",  # JS concepts
        "off-by-one", "switch", "break",
        "!=", "==",  # comparison bugs
    ]
    
    # Check for question numbering
    has_q1 = "1/3" in all_messages or "вопрос 1" in all_messages.lower()
    has_q2 = "2/3" in all_messages or "вопрос 2" in all_messages.lower()
    has_q3 = "3/3" in all_messages or "вопрос 3" in all_messages.lower()
    
    issues = []
    if not has_q1:
        issues.append("Question 1/3 numbering not found in messages")
    if not has_q2:
        issues.append("Question 2/3 numbering not found in messages")
    if not has_q3:
        issues.append("Question 3/3 numbering not found in messages")
    
    if issues:
        return False, "; ".join(issues)
    return True, "All 3 questions (1/3, 2/3, 3/3) present with correct numbering"

def check_correct_answer_messages(data):
    """Must have correct answer responses with ✅ and +15 очков."""
    all_messages = " ".join(msg.get("message", "") for msg in data if isinstance(msg, dict))
    
    issues = []
    if "✅" not in all_messages:
        issues.append("No ✅ emoji found — correct answer messages missing")
    if "+15" not in all_messages:
        issues.append("No '+15' found — point scoring for correct answers missing")
    if "❌" not in all_messages and "Пропуск" not in all_messages and "пропуск" not in all_messages:
        # For the skipped/wrong answer on q3
        issues.append("No ❌ or skip indicator found — wrong/skipped answer message missing")
    
    if issues:
        return False, "; ".join(issues)
    return True, "Correct/incorrect answer messages present with ✅ +15 scoring"

def check_hint_message(data):
    """Must have a hint message with 💡 that gives direction without full answer."""
    all_messages = " ".join(msg.get("message", "") for msg in data if isinstance(msg, dict))
    
    if "💡" not in all_messages:
        return False, "No 💡 hint emoji found — hint message missing (scenario requires hint on q2)"
    if "Подсказка" not in all_messages:
        return False, "Hint message must contain 'Подсказка'"
    return True, "Hint message present with 💡 Подсказка"

def check_finale_message(data):
    """Final message must have exact format with separator ━, score 2/3, XP calculation."""
    finale_found = False
    finale_msg = None
    
    for msg in data:
        if not isinstance(msg, dict):
            continue
        text = msg.get("message", "")
        if "Code Detective завершён" in text or "Code Detective завершен" in text:
            finale_found = True
            finale_msg = text
            break
    
    if not finale_found:
        return False, "Finale message with 'Code Detective завершён' not found"
    
    issues = []
    
    # Check heavy horizontal bar separator (━ U+2501)
    if "━" not in finale_msg:
        issues.append("Separator '━' (U+2501 BOX DRAWINGS HEAVY HORIZONTAL) not found in finale — must use ━━━━━━━━━━━━━━━━━━")
    
    # Check bugs found: 2/3
    if "2/3" not in finale_msg and "2 из 3" not in finale_msg:
        issues.append("Finale must show '2/3' bugs found (scenario: answered 2 correctly, skipped 1)")
    
    # Check XP: 2 bugs * 100 XP = 200 XP (based on SKILL.md: 4 bugs = +400 XP → 100 XP each)
    # Allow some variation but must have XP field
    if "XP" not in finale_msg:
        issues.append("Finale must show XP earned")
    
    # Check replay button exists
    has_replay = False
    for msg in data:
        if not isinstance(msg, dict):
            continue
        text = msg.get("message", "")
        if "Code Detective завершён" in text or "Code Detective завершен" in text:
            buttons = msg.get("buttons", [])
            for row in buttons:
                if isinstance(row, list):
                    for btn in row:
                        if isinstance(btn, dict) and ("снова" in btn.get("text","").lower() or "replay" in btn.get("callback_data","").lower() or "play_again" in btn.get("callback_data","").lower()):
                            has_replay = True
    
    if not has_replay:
        issues.append("Finale must have a 'Играть снова' / replay button")
    
    if issues:
        return False, "; ".join(issues)
    return True, f"Finale message correct: separator ━ present, 2/3 bugs found, XP shown, replay button present"

def check_bug_emoji(data):
    """Messages must use 🐛 🔍 emojis as specified in SKILL.md."""
    all_messages = " ".join(msg.get("message", "") for msg in data if isinstance(msg, dict))
    issues = []
    if "🐛" not in all_messages:
        issues.append("Missing 🐛 emoji in question messages")
    if "🔍" not in all_messages:
        issues.append("Missing 🔍 emoji")
    if issues:
        return False, "; ".join(issues)
    return True, "Required emojis 🐛 🔍 present"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = []
    total_score = 0.0
    weights = {
        "file_found": 0.05,
        "structure": 0.10,
        "required_fields": 0.15,
        "nested_buttons": 0.20,
        "callback_data": 0.10,
        "question_numbering": 0.10,
        "answer_messages": 0.10,
        "hint_message": 0.05,
        "finale": 0.10,
        "emojis": 0.05,
    }
    
    # --- Check 1: File found ---
    fixture_path, err = load_fixture(workspace)
    file_passed = fixture_path is not None
    checks.append({
        "name": "file_found",
        "passed": file_passed,
        "detail": str(fixture_path) if file_passed else err
    })
    if file_passed:
        total_score += weights["file_found"]
    
    if not file_passed:
        result = {
            "passed": False,
            "score": total_score,
            "checks": checks
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # --- Load JSON ---
    try:
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({"name": "json_parse", "passed": False, "detail": f"JSON parse error: {e}"})
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}, ensure_ascii=False, indent=2))
        return
    
    # --- Check 2: Structure ---
    try:
        passed, detail = check_structure(data)
        checks.append({"name": "structure", "passed": passed, "detail": detail})
        if passed:
            total_score += weights["structure"]
    except Exception as e:
        checks.append({"name": "structure", "passed": False, "detail": f"Error: {e}"})
    
    # --- Check 3: Required fields ---
    try:
        passed, detail = check_all_messages_have_required_fields(data)
        checks.append({"name": "required_fields", "passed": passed, "detail": detail})
        if passed:
            total_score += weights["required_fields"]
    except Exception as e:
        checks.append({"name": "required_fields", "passed": False, "detail": f"Error: {e}"})
    
    # --- Check 4: Nested button arrays ---
    try:
        passed, detail = check_buttons_nested_arrays(data)
        checks.append({"name": "nested_buttons", "passed": passed, "detail": detail})
        if passed:
            total_score += weights["nested_buttons"]
    except Exception as e:
        checks.append({"name": "nested_buttons", "passed": False, "detail": f"Error: {e}"})
    
    # --- Check 5: callback_data prefixes ---
    try:
        passed, detail = check_callback_data_prefixes(data)
        checks.append({"name": "callback_data", "passed": passed, "detail": detail})
        if passed:
            total_score += weights["callback_data"]
    except Exception as e:
        checks.append({"name": "callback_data", "passed": False, "detail": f"Error: {e}"})
    
    # --- Check 6: Question numbering (medium difficulty, 3 questions) ---
    try:
        passed, detail = check_medium_difficulty_bugs(data)
        checks.append({"name": "question_numbering", "passed": passed, "detail": detail})
        if passed:
            total_score += weights["question_numbering"]
    except Exception as e:
        checks.append({"name": "question_numbering", "passed": False, "detail": f"Error: {e}"})
    
    # --- Check 7: Answer messages ---
    try:
        passed, detail = check_correct_answer_messages(data)
        checks.append({"name": "answer_messages", "passed": passed, "detail": detail})
        if passed:
            total_score += weights["answer_messages"]
    except Exception as e:
        checks.append({"name": "answer_messages", "passed": False, "detail": f"Error: {e}"})
    
    # --- Check 8: Hint message ---
    try:
        passed, detail = check_hint_message(data)
        checks.append({"name": "hint_message", "passed": passed, "detail": detail})
        if passed:
            total_score += weights["hint_message"]
    except Exception as e:
        checks.append({"name": "hint_message", "passed": False, "detail": f"Error: {e}"})
    
    # --- Check 9: Finale ---
    try:
        passed, detail = check_finale_message(data)
        checks.append({"name": "finale", "passed": passed, "detail": detail})
        if passed:
            total_score += weights["finale"]
    except Exception as e:
        checks.append({"name": "finale", "passed": False, "detail": f"Error: {e}"})
    
    # --- Check 10: Emojis ---
    try:
        passed, detail = check_bug_emoji(data)
        checks.append({"name": "emojis", "passed": passed, "detail": detail})
        if passed:
            total_score += weights["emojis"]
    except Exception as e:
        checks.append({"name": "emojis", "passed": False, "detail": f"Error: {e}"})
    
    final_passed = total_score >= 0.75
    
    result = {
        "passed": final_passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()