import sys
import json
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # --- Find bot_response.json ---
    candidates = list(workspace.rglob("bot_response.json"))
    
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "bot_response.json not found anywhere in workspace."}]
        }
    
    # Prefer root-level file if multiple found
    root_candidate = workspace / "bot_response.json"
    target_file = root_candidate if root_candidate in candidates else candidates[0]
    
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {target_file}"})

    # --- Load JSON ---
    try:
        data = json.loads(target_file.read_text(encoding="utf-8"))
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "json_parseable", "passed": True, "detail": "File is valid JSON."})

    # --- Check message/reply text field ---
    # The agent must include the bot_reply_text from conversation_log.json
    expected_message = (
        "I've prepared the board meeting agenda draft and gathered last quarter's budget data. "
        "Reminder set for investor pre-reads. What would you like to do next?"
    )
    
    # Accept common field names: message, text, reply, body
    message_value = None
    for key in ["message", "text", "reply", "body", "content"]:
        if key in data:
            message_value = data[key]
            break
    
    message_check_passed = message_value is not None and expected_message in str(message_value)
    checks.append({
        "name": "correct_message_text",
        "passed": message_check_passed,
        "detail": f"Expected bot_reply_text to be present. Found: {str(message_value)[:200] if message_value else 'None'}"
    })

    # --- Check buttons structure ---
    # Must have a 'buttons' key
    buttons_raw = data.get("buttons", None)
    if buttons_raw is None:
        checks.append({"name": "buttons_field_present", "passed": False, "detail": "No 'buttons' key found in payload."})
        # Score partial and return
        score = sum(c["passed"] for c in checks) / len(checks)
        return {"passed": False, "score": round(score, 2), "checks": checks}
    
    checks.append({"name": "buttons_field_present", "passed": True, "detail": f"'buttons' key found."})

    # Must be array of arrays (rows), not flat list
    is_array_of_arrays = (
        isinstance(buttons_raw, list) and
        len(buttons_raw) > 0 and
        all(isinstance(row, list) for row in buttons_raw)
    )
    checks.append({
        "name": "buttons_array_of_arrays",
        "passed": is_array_of_arrays,
        "detail": f"Expected list of lists. Got: {type(buttons_raw).__name__} with first element type: {type(buttons_raw[0]).__name__ if buttons_raw else 'N/A'}"
    })

    if not is_array_of_arrays:
        score = sum(c["passed"] for c in checks) / len(checks)
        return {"passed": False, "score": round(score, 2), "checks": checks}

    # --- Flatten all button objects for inspection ---
    all_buttons = [btn for row in buttons_raw for btn in row]

    # Each button must have 'text' and 'callback_data'
    all_have_correct_keys = all(
        isinstance(btn, dict) and "text" in btn and "callback_data" in btn
        for btn in all_buttons
    )
    checks.append({
        "name": "buttons_have_text_and_callback_data",
        "passed": all_have_correct_keys,
        "detail": f"All {len(all_buttons)} buttons checked for 'text' and 'callback_data' keys."
    })

    # --- Time-slot validation: simulated_time=16:30 → Afternoon/Wrap-up (15:00–18:00) ---
    # CANONICAL source: references/time_logic.md Afternoon/Wrap-up preset:
    # Row 1: [{"text": "⏮️ Daily Recap", "callback_data": "/update"}, {"text": "🏠 Route Home", "callback_data": "Check route home"}]
    # Row 2: [{"text": "⏭️ Tomorrow's Agenda", "callback_data": "What is the agenda for tomorrow?"}, {"text": "⌨️ Manual Input", "callback_data": "keyboard_manual"}]

    callback_data_values = {btn.get("callback_data", "") for btn in all_buttons}
    text_values = {btn.get("text", "") for btn in all_buttons}

    # Must NOT contain morning/midday/night presets
    forbidden_callbacks = {
        "/update_morning",  # unlikely but guard
        "Check commute",
        "What is the agenda for today?",
        "Help me research a topic",
        "/status",
        "Give me a productivity tip",
        "Help me reflect on today",
        "I want to note an idea for tomorrow",
        "Turn off notifications until morning",
    }
    forbidden_texts = {
        "☀️ Morning Briefing",
        "🚗 Commute Status",
        "📅 Today's Agenda",
        "🔬 Deep Research",
        "📊 Progress Check",
        "💡 Quick Tip",
        "🌙 Night Reflection",
        "📝 Note Idea",
        "🔕 Do Not Disturb",
    }
    
    no_forbidden_callbacks = len(callback_data_values & forbidden_callbacks) == 0
    no_forbidden_texts = len(text_values & forbidden_texts) == 0
    
    checks.append({
        "name": "no_wrong_time_slot_buttons",
        "passed": no_forbidden_callbacks and no_forbidden_texts,
        "detail": f"Forbidden callbacks found: {callback_data_values & forbidden_callbacks}. Forbidden texts found: {text_values & forbidden_texts}"
    })

    # --- Must contain the EXACT afternoon preset callback_data values ---
    required_callbacks = {"/update", "Check route home", "What is the agenda for tomorrow?", "keyboard_manual"}
    found_callbacks = required_callbacks & callback_data_values
    all_required_callbacks_present = found_callbacks == required_callbacks
    
    checks.append({
        "name": "correct_afternoon_callback_data_values",
        "passed": all_required_callbacks_present,
        "detail": f"Required callback_data values: {required_callbacks}. Found: {callback_data_values}. Missing: {required_callbacks - callback_data_values}"
    })

    # --- Must contain EXACT afternoon preset text values from time_logic.md ---
    # Note: time_logic.md uses "⏮️ Daily Recap" NOT "📝 Daily Recap" (the SKILL.md example is a mismatch)
    required_texts = {"⏮️ Daily Recap", "🏠 Route Home", "⏭️ Tomorrow's Agenda", "⌨️ Manual Input"}
    found_texts = required_texts & text_values
    all_required_texts_present = found_texts == required_texts

    checks.append({
        "name": "correct_afternoon_button_texts",
        "passed": all_required_texts_present,
        "detail": f"Required texts: {required_texts}. Found: {text_values}. Missing: {required_texts - text_values}"
    })

    # --- Must include "keyboard_manual" as fallback (Manual Input always required) ---
    has_manual_fallback = "keyboard_manual" in callback_data_values
    checks.append({
        "name": "manual_input_fallback_present",
        "passed": has_manual_fallback,
        "detail": f"'keyboard_manual' callback_data {'found' if has_manual_fallback else 'MISSING'} in buttons."
    })

    # --- Must be exactly 2 rows (as per the preset) ---
    correct_row_count = len(buttons_raw) == 2
    checks.append({
        "name": "correct_two_rows",
        "passed": correct_row_count,
        "detail": f"Expected 2 rows of buttons. Found: {len(buttons_raw)}"
    })

    # --- Row 1 must have 2 buttons, Row 2 must have 2 buttons ---
    if correct_row_count:
        row1_correct = len(buttons_raw[0]) == 2
        row2_correct = len(buttons_raw[1]) == 2
        correct_buttons_per_row = row1_correct and row2_correct
        checks.append({
            "name": "two_buttons_per_row",
            "passed": correct_buttons_per_row,
            "detail": f"Row 1 has {len(buttons_raw[0])} buttons, Row 2 has {len(buttons_raw[1])} buttons. Both should be 2."
        })
    else:
        checks.append({
            "name": "two_buttons_per_row",
            "passed": False,
            "detail": "Cannot check per-row count since row count is wrong."
        })

    # --- Check target/user_id field is present ---
    has_target = any(k in data for k in ["target", "user_id", "chat_id", "recipient"])
    checks.append({
        "name": "target_user_present",
        "passed": has_target,
        "detail": f"A target/user_id/chat_id field {'found' if has_target else 'MISSING'} in payload."
    })

    # --- Final scoring ---
    total = len(checks)
    passed_count = sum(c["passed"] for c in checks)
    score = round(passed_count / total, 4)
    
    # Must pass all critical checks to be considered passing
    critical_checks = [
        "file_exists",
        "json_parseable",
        "buttons_field_present",
        "buttons_array_of_arrays",
        "buttons_have_text_and_callback_data",
        "no_wrong_time_slot_buttons",
        "correct_afternoon_callback_data_values",
        "correct_afternoon_button_texts",
        "manual_input_fallback_present",
        "correct_two_rows",
    ]
    
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    return {
        "passed": critical_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))