import sys
import json
import subprocess
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    skill_dir = workspace / "skills" / "learning-checkin"
    skill_script = skill_dir / "learning_checkin.py"
    data_dir = skill_dir / "data"

    checks = []
    total_score = 0.0

    def check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # -------------------------
    # CHECK 1: Init was run — data directory exists
    # -------------------------
    try:
        data_exists = data_dir.exists() and data_dir.is_dir()
        score = check(
            "data_dir_created",
            data_exists,
            f"data/ directory at {data_dir}: {'exists' if data_exists else 'MISSING'}",
            weight=0.5
        )
        total_score += score
    except Exception as e:
        total_score += check("data_dir_created", False, f"Exception: {e}", weight=0.5)

    # -------------------------
    # CHECK 2: version.txt exists (created on init)
    # -------------------------
    try:
        version_file = data_dir / "version.txt"
        version_exists = version_file.exists()
        version_content = version_file.read_text(encoding="utf-8").strip() if version_exists else ""
        score = check(
            "version_txt_exists",
            version_exists and len(version_content) > 0,
            f"version.txt: {'exists, content=' + repr(version_content) if version_exists else 'MISSING'}",
            weight=0.5
        )
        total_score += score
    except Exception as e:
        total_score += check("version_txt_exists", False, f"Exception: {e}", weight=0.5)

    # -------------------------
    # CHECK 3: records.json exists and has at least one check-in
    # -------------------------
    try:
        records_file = data_dir / "records.json"
        records_exists = records_file.exists()
        if records_exists:
            records_data = json.loads(records_file.read_text(encoding="utf-8"))
            # records.json should be a list or dict with check-in data
            # Based on the skill, it stores check-in history
            has_checkin = False
            if isinstance(records_data, list) and len(records_data) > 0:
                has_checkin = True
            elif isinstance(records_data, dict):
                # Could be {"checkins": [...]} or similar
                for v in records_data.values():
                    if isinstance(v, list) and len(v) > 0:
                        has_checkin = True
                        break
                    if isinstance(v, (str, int)) and v:
                        has_checkin = True
                        break
            detail = f"records.json exists, has_checkin={has_checkin}, content_type={type(records_data).__name__}, preview={str(records_data)[:200]}"
        else:
            has_checkin = False
            detail = "records.json MISSING"

        score = check("checkin_recorded", records_exists and has_checkin, detail, weight=2.0)
        total_score += score
    except Exception as e:
        total_score += check("checkin_recorded", False, f"Exception: {e}", weight=2.0)

    # -------------------------
    # CHECK 4: Verify checkin command returns success=true (run live check)
    # -------------------------
    try:
        # Run status to see if streak > 0 or total_checkins > 0
        result = subprocess.run(
            ["python", str(skill_script), "status"],
            capture_output=True, text=True, cwd=str(skill_dir), timeout=15
        )
        status_passed = False
        status_detail = f"stdout={result.stdout[:300]}, stderr={result.stderr[:200]}"
        if result.returncode == 0:
            try:
                status_json = json.loads(result.stdout.strip())
                total_checkins = status_json.get("total_checkins", 0)
                streak = status_json.get("streak", 0)
                status_passed = (total_checkins >= 1)
                status_detail = f"total_checkins={total_checkins}, streak={streak}, checked_in_today={status_json.get('checked_in_today')}"
            except json.JSONDecodeError:
                status_detail = f"Could not parse JSON: {result.stdout[:300]}"
        score = check("status_shows_checkin", status_passed, status_detail, weight=2.0)
        total_score += score
    except Exception as e:
        total_score += check("status_shows_checkin", False, f"Exception: {e}", weight=2.0)

    # -------------------------
    # CHECK 5: cron_status.json exists and has configured=true with times
    # -------------------------
    try:
        cron_file = data_dir / "cron_status.json"
        cron_exists = cron_file.exists()
        if cron_exists:
            cron_data = json.loads(cron_file.read_text(encoding="utf-8"))
            configured = cron_data.get("configured", False)
            times = cron_data.get("times", [])
            # Agent must have called update-cron with 09:00 and 20:00
            has_09 = "09:00" in times
            has_20 = "20:00" in times
            cron_ok = configured and has_09 and has_20
            detail = f"configured={configured}, times={times}, has_09:00={has_09}, has_20:00={has_20}"
        else:
            cron_ok = False
            detail = "cron_status.json MISSING — update-cron was never called"

        score = check("cron_configured_with_times", cron_ok, detail, weight=2.0)
        total_score += score
    except Exception as e:
        total_score += check("cron_configured_with_times", False, f"Exception: {e}", weight=2.0)

    # -------------------------
    # CHECK 6: Verify `message` command works for 09:00 and 20:00
    # -------------------------
    for time_slot in ["09:00", "20:00"]:
        try:
            result = subprocess.run(
                ["python", str(skill_script), "message", time_slot],
                capture_output=True, text=True, cwd=str(skill_dir), timeout=15
            )
            msg_ok = False
            detail = f"returncode={result.returncode}, stdout={result.stdout[:300]}"
            if result.returncode == 0:
                try:
                    msg_json = json.loads(result.stdout.strip())
                    message_text = msg_json.get("message", "")
                    msg_ok = isinstance(message_text, str) and len(message_text) > 0
                    detail = f"time={time_slot}, message='{message_text[:100]}'"
                except json.JSONDecodeError:
                    detail = f"Non-JSON output for message {time_slot}: {result.stdout[:200]}"
            score = check(f"message_command_{time_slot.replace(':', '')}", msg_ok, detail, weight=1.0)
            total_score += score
        except Exception as e:
            total_score += check(f"message_command_{time_slot.replace(':', '')}", False, f"Exception: {e}", weight=1.0)

    # -------------------------
    # CHECK 7: setup_report.json exists with required fields
    # -------------------------
    try:
        report_files = list(workspace.rglob("setup_report.json"))
        if not report_files:
            score = check("setup_report_exists", False, "setup_report.json not found anywhere in workspace", weight=2.0)
            total_score += score
        else:
            report_file = report_files[0]
            report_data = json.loads(report_file.read_text(encoding="utf-8"))

            required_keys = ["streak", "total_checkins", "reminder_times", "checked_in_today"]
            missing_keys = [k for k in required_keys if k not in report_data]

            # Validate values
            streak_ok = isinstance(report_data.get("streak"), int)
            total_ok = isinstance(report_data.get("total_checkins"), int) and report_data.get("total_checkins", 0) >= 1
            reminder_times = report_data.get("reminder_times", [])
            times_ok = isinstance(reminder_times, list) and "09:00" in reminder_times and "20:00" in reminder_times
            checked_in_field = report_data.get("checked_in_today")
            checked_in_ok = isinstance(checked_in_field, bool)

            all_ok = not missing_keys and streak_ok and total_ok and times_ok and checked_in_ok
            detail = (
                f"File: {report_file}, missing_keys={missing_keys}, "
                f"streak={report_data.get('streak')}, total_checkins={report_data.get('total_checkins')}, "
                f"reminder_times={reminder_times}, checked_in_today={checked_in_field}"
            )
            score = check("setup_report_valid", all_ok, detail, weight=3.0)
            total_score += score
    except Exception as e:
        total_score += check("setup_report_exists", False, f"Exception: {e}", weight=2.0)

    # -------------------------
    # FINAL SCORE CALCULATION
    # -------------------------
    max_score = 0.5 + 0.5 + 2.0 + 2.0 + 2.0 + 1.0 + 1.0 + 3.0  # = 12.0
    normalized_score = round(total_score / max_score, 4)
    passed = normalized_score >= 0.75  # Need 75% to pass

    return {
        "passed": passed,
        "score": normalized_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))