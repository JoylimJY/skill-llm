import sys
import json
import os
import re
import requests
from pathlib import Path

def run_eval(workspace_dir):
    checks = []
    total_score = 0.0

    workspace = Path(workspace_dir)

    # --- CHECK 1: chat_report.json exists ---
    report_files = list(workspace.rglob('chat_report.json'))
    if not report_files:
        checks.append({"name": "chat_report.json exists", "passed": False, "detail": "No chat_report.json file found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = report_files[0]
    checks.append({"name": "chat_report.json exists", "passed": True, "detail": f"Found at {report_path}"})
    total_score += 0.15

    # --- CHECK 2: Valid JSON ---
    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
        checks.append({"name": "chat_report.json is valid JSON", "passed": True, "detail": "Parsed successfully."})
        total_score += 0.10
    except Exception as e:
        checks.append({"name": "chat_report.json is valid JSON", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": total_score, "checks": checks}

    # --- CHECK 3: Contains rooms info (get-rooms-info was called) ---
    has_rooms_info = False
    rooms_data = None
    # Look for any key that plausibly holds room counts
    def find_rooms_info(obj, depth=0):
        if depth > 5:
            return None
        if isinstance(obj, dict):
            # Check if this dict looks like room counts {room_name: count}
            known_rooms = {'welcome', 'mim', 'crustafarianism', 'rap-battles', 'memes'}
            if any(k in known_rooms for k in obj.keys()):
                return obj
            for v in obj.values():
                result = find_rooms_info(v, depth+1)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = find_rooms_info(item, depth+1)
                if result:
                    return result
        return None

    rooms_data = find_rooms_info(report)
    if rooms_data and 'mim' in rooms_data:
        has_rooms_info = True
        checks.append({"name": "Room info (get-rooms-info) present", "passed": True,
                        "detail": f"Found room info with mim count={rooms_data.get('mim')}. Data: {json.dumps(rooms_data)[:200]}"})
        total_score += 0.15
    else:
        checks.append({"name": "Room info (get-rooms-info) present", "passed": False,
                        "detail": f"Could not find rooms info with known room IDs in the report. Report keys: {list(report.keys()) if isinstance(report, dict) else 'N/A'}"})

    # --- CHECK 4: Message history from a non-default room ---
    # The report must contain message history (array of messages) from a room that is NOT 'welcome'
    has_non_welcome_history = False
    history_room_found = None

    def find_message_history(obj, depth=0):
        """Look for an array of objects that look like chat messages with screenName/text fields."""
        if depth > 6:
            return None, None
        if isinstance(obj, list) and len(obj) > 0:
            # Check if items look like messages
            if all(isinstance(m, dict) and ('screenName' in m or 'screen_name' in m or 'text' in m) for m in obj[:3]):
                # Try to find roomId
                for m in obj:
                    room_id = m.get('roomId') or m.get('room_id') or m.get('room')
                    if room_id and room_id != 'welcome':
                        return obj, room_id
                # Return anyway if messages exist without clear roomId
                return obj, None
        if isinstance(obj, dict):
            for k, v in obj.items():
                result, room = find_message_history(v, depth+1)
                if result:
                    # If key gives room context
                    if room is None and k not in ('welcome',) and k in ('mim', 'crustafarianism', 'rap-battles', 'memes'):
                        room = k
                    return result, room
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    result, room = find_message_history(item, depth+1)
                    if result:
                        return result, room
        return None, None

    history, history_room = find_message_history(report)

    if history and history_room and history_room != 'welcome':
        has_non_welcome_history = True
        history_room_found = history_room
        checks.append({"name": "Non-welcome room history present", "passed": True,
                        "detail": f"Found {len(history)} messages from room '{history_room}'."})
        total_score += 0.20
    elif history:
        # History exists but couldn't confirm non-welcome room from roomId field
        # Check if the history contains messages that match known non-welcome room content
        all_text = ' '.join([m.get('text', '') for m in history if isinstance(m, dict)])
        mim_keywords = ['$MIM', 'pumping', 'dip', 'moon', 'announcement', 'financial advice', 'all in']
        if any(kw.lower() in all_text.lower() for kw in mim_keywords):
            has_non_welcome_history = True
            history_room_found = 'mim'
            checks.append({"name": "Non-welcome room history present", "passed": True,
                            "detail": f"Found message history with content matching 'mim' room ({len(history)} messages)."})
            total_score += 0.20
        else:
            checks.append({"name": "Non-welcome room history present", "passed": False,
                            "detail": f"Message history found but appears to be from #welcome or couldn't confirm non-welcome room."})
    else:
        checks.append({"name": "Non-welcome room history present", "passed": False,
                        "detail": "No message history array found in chat_report.json."})

    # --- CHECK 5: Screen name recorded in report ---
    report_str = json.dumps(report)
    # Look for screen name - must be 2-20 characters
    screen_name_found = None
    # Check for common keys
    for key in ['screenName', 'screen_name', 'botName', 'bot_name', 'name', 'screenname']:
        if isinstance(report, dict) and key in report:
            val = report[key]
            if isinstance(val, str) and 2 <= len(val) <= 20:
                screen_name_found = val
                break

    # Also search recursively for AuditBot42 specifically
    if 'AuditBot42' in report_str:
        screen_name_found = 'AuditBot42'

    if screen_name_found:
        checks.append({"name": "Screen name recorded in report", "passed": True,
                        "detail": f"Screen name '{screen_name_found}' found in report."})
        total_score += 0.10
    else:
        checks.append({"name": "Screen name recorded in report", "passed": False,
                        "detail": "No valid screen name (2-20 chars) found in report."})

    # --- CHECK 6: Verify a message was actually sent to a non-welcome room (server-side verification) ---
    try:
        resp = requests.get('http://localhost:3456/recorded-messages', timeout=5)
        if resp.status_code == 200:
            recorded = resp.json()
            non_welcome_msgs = [m for m in recorded if m.get('roomId') != 'welcome']
            if non_welcome_msgs:
                msg = non_welcome_msgs[0]
                room_id = msg.get('roomId')
                text = msg.get('text', '')
                screen = msg.get('screenName', '')
                # Validate screen name length
                valid_name = 2 <= len(screen) <= 20 if screen else False
                checks.append({"name": "Message sent to non-welcome room (server verified)", "passed": True,
                                "detail": f"Server recorded message in room '{room_id}': '{text[:80]}' from '{screen}'. Valid screen name: {valid_name}"})
                total_score += 0.20

                # Bonus: screen name is specifically AuditBot42
                if screen == 'AuditBot42':
                    checks.append({"name": "Correct screen name AuditBot42 used", "passed": True,
                                    "detail": "Agent used the exact screen name 'AuditBot42' as specified."})
                    total_score += 0.05
                else:
                    checks.append({"name": "Correct screen name AuditBot42 used", "passed": False,
                                    "detail": f"Expected 'AuditBot42' but got '{screen}'."})
            else:
                checks.append({"name": "Message sent to non-welcome room (server verified)", "passed": False,
                                "detail": f"Server has {len(recorded)} total recorded messages, but none in non-welcome rooms. All rooms: {list(set(m.get('roomId') for m in recorded))}"})
        else:
            checks.append({"name": "Message sent to non-welcome room (server verified)", "passed": False,
                            "detail": f"Mock server returned HTTP {resp.status_code}"})
    except Exception as e:
        checks.append({"name": "Message sent to non-welcome room (server verified)", "passed": False,
                        "detail": f"Could not reach mock server: {e}"})

    # --- CHECK 7: Report contains room_id where message was sent ---
    non_welcome_rooms = {'mim', 'crustafarianism', 'rap-battles', 'memes'}
    room_id_in_report = None
    for room in non_welcome_rooms:
        if room in report_str:
            room_id_in_report = room
            break

    if room_id_in_report:
        checks.append({"name": "Target room ID in report", "passed": True,
                        "detail": f"Report references room '{room_id_in_report}'."})
        total_score += 0.05
    else:
        checks.append({"name": "Target room ID in report", "passed": False,
                        "detail": "No non-welcome room ID found in report."})

    # Final pass/fail: require at minimum checks 1,2,6 pass (file exists, valid JSON, server confirmed message)
    critical_passed = all(c["passed"] for c in checks if c["name"] in [
        "chat_report.json exists",
        "chat_report.json is valid JSON",
        "Message sent to non-welcome room (server verified)"
    ])

    total_score = min(total_score, 1.0)

    return {
        "passed": critical_passed and total_score >= 0.50,
        "score": round(total_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))