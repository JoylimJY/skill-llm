import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    workspace = Path(workspace)
    checks = []
    total_score = 0.0
    max_score = 7

    # --- Check 1: User file exists ---
    user_file = workspace / "data" / "users" / "analyst_wei.json"
    try:
        assert user_file.exists(), "File does not exist"
        user_data = json.loads(user_file.read_text(encoding="utf-8"))
        checks.append({"name": "user_file_exists", "passed": True, "detail": f"Found {user_file}"})
        total_score += 1
    except Exception as e:
        checks.append({"name": "user_file_exists", "passed": False, "detail": str(e)})
        # Cannot continue without file
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks + [
                {"name": "language_correct", "passed": False, "detail": "No user file"},
                {"name": "topics_correct", "passed": False, "detail": "No user file"},
                {"name": "channel_correct", "passed": False, "detail": "No user file"},
                {"name": "preferences_correct_values", "passed": False, "detail": "No user file"},
                {"name": "preferences_decimal_format", "passed": False, "detail": "No user file"},
                {"name": "push_enabled", "passed": False, "detail": "No user file"},
                {"name": "push_morning_time", "passed": False, "detail": "No user file"},
                {"name": "push_evening_time", "passed": False, "detail": "No user file"},
                {"name": "push_channel", "passed": False, "detail": "No user file"},
            ]
        }
        print(json.dumps(result))
        return

    # --- Check 2: Language is 'zh' ---
    try:
        lang = user_data.get("language", "")
        passed = lang == "zh"
        checks.append({
            "name": "language_correct",
            "passed": passed,
            "detail": f"language={lang!r}, expected 'zh'"
        })
        if passed: total_score += 1
    except Exception as e:
        checks.append({"name": "language_correct", "passed": False, "detail": str(e)})

    # --- Check 3: Topics contain 财经, 国际, 科技 (order-insensitive) ---
    try:
        topics = user_data.get("topics", [])
        required = {"财经", "国际", "科技"}
        present = set(topics)
        has_required = required.issubset(present)
        passed = has_required
        checks.append({
            "name": "topics_correct",
            "passed": passed,
            "detail": f"topics={topics}, required={sorted(required)}"
        })
        if passed: total_score += 1
    except Exception as e:
        checks.append({"name": "topics_correct", "passed": False, "detail": str(e)})

    # --- Check 4: Channel is 'slack' ---
    try:
        channel = user_data.get("channel", "")
        passed = channel == "slack"
        checks.append({
            "name": "channel_correct",
            "passed": passed,
            "detail": f"channel={channel!r}, expected 'slack'"
        })
        if passed: total_score += 1
    except Exception as e:
        checks.append({"name": "channel_correct", "passed": False, "detail": str(e)})

    # --- Check 5: Preferences have correct topics ---
    try:
        prefs = user_data.get("preferences", {})
        # Check 财经=0.9, 国际=0.8, 科技=0.5
        expected_prefs = {"财经": 0.9, "国际": 0.8, "科技": 0.5}
        correct_values = all(
            abs(prefs.get(k, -1) - v) < 0.01
            for k, v in expected_prefs.items()
        )
        checks.append({
            "name": "preferences_correct_values",
            "passed": correct_values,
            "detail": f"preferences={prefs}, expected={expected_prefs}"
        })
        if correct_values: total_score += 1
    except Exception as e:
        checks.append({"name": "preferences_correct_values", "passed": False, "detail": str(e)})

    # --- Check 6: All preference values are decimals between 0-1 (not integers > 1) ---
    try:
        prefs = user_data.get("preferences", {})
        all_decimal = all(
            isinstance(v, (int, float)) and 0 <= v <= 1
            for v in prefs.values()
        ) and len(prefs) > 0
        # Also verify they are not all integers (0 or 1 only with no fractional content)
        has_fractional = any(
            isinstance(v, float) and v not in (0.0, 1.0)
            for v in prefs.values()
        )
        passed = all_decimal and has_fractional
        checks.append({
            "name": "preferences_decimal_format",
            "passed": passed,
            "detail": f"all values in [0,1] and at least one is fractional: {prefs}"
        })
        if passed: total_score += 0.5
    except Exception as e:
        checks.append({"name": "preferences_decimal_format", "passed": False, "detail": str(e)})

    # --- Check 7: Push is enabled ---
    try:
        push = user_data.get("push", {})
        passed = push.get("enabled") == True
        checks.append({
            "name": "push_enabled",
            "passed": passed,
            "detail": f"push.enabled={push.get('enabled')}"
        })
        if passed: total_score += 0.5
    except Exception as e:
        checks.append({"name": "push_enabled", "passed": False, "detail": str(e)})

    # --- Check 8: Push morning time is 07:30 ---
    try:
        push = user_data.get("push", {})
        morning = push.get("morning", "")
        passed = morning == "07:30"
        checks.append({
            "name": "push_morning_time",
            "passed": passed,
            "detail": f"push.morning={morning!r}, expected '07:30'"
        })
        if passed: total_score += 0.5
    except Exception as e:
        checks.append({"name": "push_morning_time", "passed": False, "detail": str(e)})

    # --- Check 9: Push evening time is 21:00 ---
    try:
        push = user_data.get("push", {})
        evening = push.get("evening", "")
        passed = evening == "21:00"
        checks.append({
            "name": "push_evening_time",
            "passed": passed,
            "detail": f"push.evening={evening!r}, expected '21:00'"
        })
        if passed: total_score += 0.5
    except Exception as e:
        checks.append({"name": "push_evening_time", "passed": False, "detail": str(e)})

    # --- Check 10: Push channel is 'slack' ---
    try:
        push = user_data.get("push", {})
        push_channel = push.get("channel", "")
        passed = push_channel == "slack"
        checks.append({
            "name": "push_channel",
            "passed": passed,
            "detail": f"push.channel={push_channel!r}, expected 'slack'"
        })
        if passed: total_score += 0.5
    except Exception as e:
        checks.append({"name": "push_channel", "passed": False, "detail": str(e)})

    # --- Check 11: Morning log exists for analyst_wei ---
    try:
        log_dir = workspace / "logs" / "morning"
        log_files = list(log_dir.glob("*.log"))
        found_entry = False
        for lf in log_files:
            content = lf.read_text(encoding="utf-8", errors="ignore")
            if "analyst_wei" in content:
                found_entry = True
                break
        checks.append({
            "name": "morning_push_triggered",
            "passed": found_entry,
            "detail": f"Searched {len(log_files)} log file(s) in logs/morning/ for 'analyst_wei'"
        })
        if found_entry: total_score += 0.5
    except Exception as e:
        checks.append({"name": "morning_push_triggered", "passed": False, "detail": str(e)})

    final_score = round(total_score / max_score, 4)
    all_critical = all(
        c["passed"] for c in checks
        if c["name"] in [
            "user_file_exists",
            "language_correct",
            "topics_correct",
            "channel_correct",
            "preferences_correct_values",
            "push_enabled",
            "push_morning_time",
            "push_evening_time",
            "push_channel",
        ]
    )

    result = {
        "passed": all_critical,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)