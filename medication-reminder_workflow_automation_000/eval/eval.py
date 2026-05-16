import sys
import json
import os
import subprocess
from pathlib import Path

def run_cmd(cmd, cwd):
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=15
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    script = str(Path(workspace) / "scripts" / "script.sh")

    data_dir = Path.home() / ".local/share/medication-reminder"
    meds_file = data_dir / "medications.json"
    hist_file = data_dir / "history.json"

    checks = []

    # ── CHECK 1: All three medications were registered via `add` ──────────────
    try:
        meds_raw = meds_file.read_text()
        meds = json.loads(meds_raw)
        names = {m["name"].lower() for m in meds}
        required = {"metformin", "lisinopril", "aspirin"}
        missing = required - names
        checks.append({
            "name": "all_three_meds_added",
            "passed": len(missing) == 0,
            "detail": (
                f"Found medications: {sorted(names)}. Missing: {sorted(missing)}"
                if missing else
                f"All required medications present: {sorted(names)}"
            )
        })
    except Exception as e:
        checks.append({
            "name": "all_three_meds_added",
            "passed": False,
            "detail": f"Could not read medications.json: {e}"
        })

    # ── CHECK 2: Correct dose and frequency for each med ─────────────────────
    try:
        meds_map = {m["name"].lower(): m for m in meds}
        expected_specs = {
            "metformin":  {"dose": "500mg",  "frequency": "twice-daily"},
            "lisinopril": {"dose": "10mg",   "frequency": "once-daily"},
            "aspirin":    {"dose": "81mg",   "frequency": "once-daily"},
        }
        spec_errors = []
        for med_name, expected in expected_specs.items():
            if med_name not in meds_map:
                spec_errors.append(f"{med_name}: not found")
                continue
            actual = meds_map[med_name]
            for field, val in expected.items():
                actual_val = actual.get(field, "").lower()
                if actual_val != val.lower():
                    spec_errors.append(
                        f"{med_name}.{field}: expected '{val}', got '{actual_val}'"
                    )
        checks.append({
            "name": "correct_dose_and_frequency",
            "passed": len(spec_errors) == 0,
            "detail": "; ".join(spec_errors) if spec_errors else "All doses and frequencies correct."
        })
    except Exception as e:
        checks.append({
            "name": "correct_dose_and_frequency",
            "passed": False,
            "detail": f"Error checking dose/frequency: {e}"
        })

    # ── CHECK 3: All three medications have been taken (history entries exist) ─
    try:
        hist_raw = hist_file.read_text()
        history = json.loads(hist_raw)
        taken_names = {h["name"].lower() for h in history}
        required = {"metformin", "lisinopril", "aspirin"}
        not_taken = required - taken_names
        checks.append({
            "name": "all_three_meds_taken",
            "passed": len(not_taken) == 0,
            "detail": (
                f"Not recorded as taken: {sorted(not_taken)}"
                if not_taken else
                f"All medications recorded as taken: {sorted(taken_names)}"
            )
        })
    except Exception as e:
        checks.append({
            "name": "all_three_meds_taken",
            "passed": False,
            "detail": f"Could not read history.json: {e}"
        })

    # ── CHECK 4: `history 7` returns valid JSON with the correct entries ───────
    try:
        stdout, stderr, rc = run_cmd(f"bash {script} history 7", workspace)
        history_output = json.loads(stdout)
        # Must be a list
        is_list = isinstance(history_output, list)
        # Must contain at least 3 entries (one per med taken)
        has_entries = len(history_output) >= 3
        # Each entry must have 'name' and 'taken_at' keys
        keys_ok = all("name" in e and "taken_at" in e for e in history_output)
        passed = is_list and has_entries and keys_ok
        checks.append({
            "name": "history_7_days_returns_valid_data",
            "passed": passed,
            "detail": (
                f"history 7 returned {len(history_output)} entries, "
                f"is_list={is_list}, keys_ok={keys_ok}, stderr={stderr}"
            )
        })
    except Exception as e:
        checks.append({
            "name": "history_7_days_returns_valid_data",
            "passed": False,
            "detail": f"Error running or parsing `history 7`: {e}. stdout={stdout!r}"
        })

    # ── CHECK 5: `list` output includes all three medications ─────────────────
    try:
        stdout, stderr, rc = run_cmd(f"bash {script} list", workspace)
        lines = stdout.lower()
        list_has_all = all(med in lines for med in ["metformin", "lisinopril", "aspirin"])
        checks.append({
            "name": "list_shows_all_meds",
            "passed": list_has_all and rc == 0,
            "detail": f"list output: {stdout!r}, rc={rc}"
        })
    except Exception as e:
        checks.append({
            "name": "list_shows_all_meds",
            "passed": False,
            "detail": f"Error running `list`: {e}"
        })

    # ── CHECK 6: `due` shows none (all taken today) ───────────────────────────
    try:
        stdout, stderr, rc = run_cmd(f"bash {script} due", workspace)
        # If all were taken today, due should return empty or no "DUE:" lines
        due_lines = [l for l in stdout.splitlines() if l.strip().startswith("DUE:")]
        checks.append({
            "name": "due_empty_after_taking_all",
            "passed": len(due_lines) == 0 and rc == 0,
            "detail": f"`due` returned: {stdout!r} (rc={rc}). Expected no DUE entries."
        })
    except Exception as e:
        checks.append({
            "name": "due_empty_after_taking_all",
            "passed": False,
            "detail": f"Error running `due`: {e}"
        })

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall = passed_count == total

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()