import sys
import json
import subprocess
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    all_passed = True

    # ---------------------------------------------------------------
    # Helper
    # ---------------------------------------------------------------
    def fail(name, detail):
        nonlocal all_passed
        all_passed = False
        checks.append({"name": name, "passed": False, "detail": detail})

    def ok(name, detail):
        checks.append({"name": name, "passed": True, "detail": detail})

    # ---------------------------------------------------------------
    # CHECK 1: todo.js USERS constant was reconfigured
    # ---------------------------------------------------------------
    todo_js_path = workspace / "skills/family-todo/todo.js"
    try:
        todo_js_content = todo_js_path.read_text()
        # Must NOT contain placeholder strings
        if "YOUR_TELEGRAM_ID_HERE" in todo_js_content:
            fail("users_configured_mark", "USERS['Mark'] still contains placeholder 'YOUR_TELEGRAM_ID_HERE'")
        else:
            # Check specific IDs from family_setup.json
            if "112233445" in todo_js_content:
                ok("users_configured_mark", "Mark's Telegram ID (112233445) correctly set in USERS")
            else:
                fail("users_configured_mark", "Mark's Telegram ID '112233445' not found in todo.js USERS config")

        if "PARTNER_TELEGRAM_ID_HERE" in todo_js_content:
            fail("users_configured_jane", "USERS['Jane'] still contains placeholder 'PARTNER_TELEGRAM_ID_HERE'")
        else:
            if "998877665" in todo_js_content:
                ok("users_configured_jane", "Jane's Telegram ID (998877665) correctly set in USERS")
            else:
                fail("users_configured_jane", "Jane's Telegram ID '998877665' not found in todo.js USERS config")

        if "GROUP_ID" in todo_js_content and "550011223" not in todo_js_content:
            fail("users_configured_shared", "USERS['Shared'] still contains placeholder 'GROUP_ID'")
        else:
            if "550011223" in todo_js_content:
                ok("users_configured_shared", "Shared group ID (550011223) correctly set in USERS")
            else:
                fail("users_configured_shared", "Shared group ID '550011223' not found in todo.js USERS config")

    except Exception as e:
        fail("users_configured_mark", f"Could not read todo.js: {e}")
        fail("users_configured_jane", f"Could not read todo.js: {e}")
        fail("users_configured_shared", f"Could not read todo.js: {e}")

    # ---------------------------------------------------------------
    # CHECK 2: memory/todo.json exists and is valid JSON
    # ---------------------------------------------------------------
    todo_json_path = workspace / "memory/todo.json"
    tasks = []
    try:
        content = todo_json_path.read_text()
        tasks = json.loads(content)
        if not isinstance(tasks, list):
            fail("todo_json_valid", f"memory/todo.json is not a JSON array, got: {type(tasks)}")
        else:
            ok("todo_json_valid", f"memory/todo.json is valid JSON array with {len(tasks)} tasks")
    except FileNotFoundError:
        fail("todo_json_valid", "memory/todo.json does not exist")
    except json.JSONDecodeError as e:
        fail("todo_json_valid", f"memory/todo.json is invalid JSON: {e}")
    except Exception as e:
        fail("todo_json_valid", f"Unexpected error reading memory/todo.json: {e}")

    # ---------------------------------------------------------------
    # CHECK 3: All 5 tasks were added (check by description)
    # ---------------------------------------------------------------
    expected_tasks = [
        {"description": "Buy groceries", "user": "Mark"},
        {"description": "Pick up kids from school", "user": "Jane"},
        {"description": "Pay electricity bill", "user": "Mark"},
        {"description": "Family movie night", "user": "Shared"},
        {"description": "Schedule dentist appointment", "user": "Jane"},
    ]

    for expected in expected_tasks:
        desc = expected["description"]
        user = expected["user"]
        found = [t for t in tasks if t.get("description", "").lower() == desc.lower() and t.get("user") == user]
        if found:
            ok(f"task_added_{desc[:15].replace(' ','_')}", f"Task '{desc}' for {user} found in todo.json")
        else:
            fail(f"task_added_{desc[:15].replace(' ','_')}", f"Task '{desc}' for user '{user}' NOT found in todo.json")

    # ---------------------------------------------------------------
    # CHECK 4: "Buy groceries" and "Family movie night" are marked done
    # ---------------------------------------------------------------
    tasks_to_complete = ["Buy groceries", "Family movie night"]
    for desc in tasks_to_complete:
        matching = [t for t in tasks if t.get("description", "").lower() == desc.lower()]
        if not matching:
            fail(f"task_completed_{desc[:10].replace(' ','_')}", f"Task '{desc}' not found in todo.json at all")
        else:
            if all(t.get("status") == "done" for t in matching):
                ok(f"task_completed_{desc[:10].replace(' ','_')}", f"Task '{desc}' is correctly marked as 'done'")
            else:
                statuses = [t.get("status") for t in matching]
                fail(f"task_completed_{desc[:10].replace(' ','_')}", f"Task '{desc}' status is {statuses}, expected 'done'")

    # ---------------------------------------------------------------
    # CHECK 5: "Pay electricity bill" and others NOT completed remain active
    # ---------------------------------------------------------------
    tasks_still_active = ["Pay electricity bill", "Pick up kids from school", "Schedule dentist appointment"]
    for desc in tasks_still_active:
        matching = [t for t in tasks if t.get("description", "").lower() == desc.lower()]
        if not matching:
            fail(f"task_active_{desc[:12].replace(' ','_')}", f"Task '{desc}' not found in todo.json")
        else:
            if all(t.get("status") == "active" for t in matching):
                ok(f"task_active_{desc[:12].replace(' ','_')}", f"Task '{desc}' is correctly still 'active'")
            else:
                statuses = [t.get("status") for t in matching]
                fail(f"task_active_{desc[:12].replace(' ','_')}", f"Task '{desc}' should be active but status is {statuses}")

    # ---------------------------------------------------------------
    # CHECK 6: Functional verification — list Mark shows Mark + Shared tasks
    # ---------------------------------------------------------------
    try:
        result = subprocess.run(
            ["node", "skills/family-todo/todo.js", "list", "Mark"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout
        stderr = result.stderr

        if result.returncode != 0:
            fail("list_mark_functional", f"'list Mark' command failed (rc={result.returncode}): {stderr}")
        else:
            # Should show Pay electricity bill (Mark, active)
            # Should show Family movie night? No — it's done, not active
            # Should NOT show Pick up kids (Jane, active) — wrong user
            has_electricity = "Pay electricity bill" in output
            no_jane_task = "Pick up kids from school" not in output

            if has_electricity and no_jane_task:
                ok("list_mark_functional", "'list Mark' correctly shows Mark's active tasks and excludes Jane's tasks")
            elif not has_electricity:
                fail("list_mark_functional", f"'list Mark' missing 'Pay electricity bill'. Output: {output[:300]}")
            else:
                fail("list_mark_functional", f"'list Mark' incorrectly includes Jane's tasks. Output: {output[:300]}")
    except subprocess.TimeoutExpired:
        fail("list_mark_functional", "Command 'list Mark' timed out")
    except Exception as e:
        fail("list_mark_functional", f"Error running 'list Mark': {e}")

    # ---------------------------------------------------------------
    # CHECK 7: Task IDs are timestamp-based (numeric, 13 digits = ms)
    # ---------------------------------------------------------------
    try:
        if tasks:
            bad_ids = [t for t in tasks if not str(t.get("id", "")).isdigit()]
            if bad_ids:
                fail("timestamp_ids", f"Some tasks have non-numeric IDs: {[t.get('id') for t in bad_ids[:3]]}")
            else:
                # Check length roughly corresponds to Unix ms timestamp (13 digits for year ~2001+)
                short_ids = [t for t in tasks if len(str(t.get("id", ""))) < 10]
                if short_ids:
                    fail("timestamp_ids", f"Some task IDs are too short to be timestamps: {[t.get('id') for t in short_ids[:3]]}")
                else:
                    ok("timestamp_ids", "All task IDs are valid numeric timestamp IDs")
        else:
            fail("timestamp_ids", "No tasks found to verify IDs")
    except Exception as e:
        fail("timestamp_ids", f"Error verifying task IDs: {e}")

    # ---------------------------------------------------------------
    # Score
    # ---------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace directory provided"}
        ]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))