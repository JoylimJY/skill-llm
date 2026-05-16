import sys
import json
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        result = fn()
        return {"name": name, "passed": result[0], "detail": result[1]}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []

    # --- 1. Check lottery_report.txt exists ---
    report_files = list(workspace.rglob("lottery_report.txt"))
    report_exists = len(report_files) > 0
    checks.append({
        "name": "lottery_report.txt exists",
        "passed": report_exists,
        "detail": f"Found {len(report_files)} file(s)" if report_exists else "File not found anywhere in workspace"
    })

    report_content = ""
    if report_exists:
        report_content = report_files[0].read_text()

    # --- 2. Check stats output is in report ---
    def check_stats_content():
        required_keys = ["total_picks", "total_checks", "wins", "powerball_plays", "mega_plays"]
        missing = [k for k in required_keys if k not in report_content]
        if missing:
            return False, f"Missing stats keys: {missing}. Content snippet: {report_content[:300]}"
        return True, f"All required stat keys found in report."
    checks.append(run_check("lottery_report.txt contains stats fields", check_stats_content))

    # --- 3. Check history file exists and has entries ---
    import os
    home = Path(os.path.expanduser("~"))
    history_path = home / ".local/share/lottery/history.json"

    def check_history_exists():
        if not history_path.exists():
            return False, f"History file not found at {history_path}"
        data = json.loads(history_path.read_text())
        if not isinstance(data, list) or len(data) == 0:
            return False, "History file is empty"
        return True, f"History file has {len(data)} entries"
    checks.append(run_check("History file exists and has entries", check_history_exists))

    # --- 4. Check pick was executed (history has a pick entry) ---
    def check_pick_entry():
        if not history_path.exists():
            return False, "History file missing"
        data = json.loads(history_path.read_text())
        # history entries may be stored as dicts or stringified dicts
        pick_entries = []
        for e in data:
            if isinstance(e, dict) and e.get("type") == "pick":
                pick_entries.append(e)
            elif isinstance(e, str) and "'type': 'pick'" in e:
                pick_entries.append(e)
        if not pick_entries:
            return False, f"No 'pick' entry in history. Entries: {data[:3]}"
        # Validate count=6 and max=49
        valid = False
        for e in pick_entries:
            if isinstance(e, dict):
                if str(e.get("count")) == "6" and str(e.get("max")) == "49":
                    valid = True
                    break
            elif isinstance(e, str):
                if "'count': 6" in e or "'count':6" in e:
                    if "'max': 49" in e or "'max':49" in e:
                        valid = True
                        break
        if not valid:
            return False, f"Pick entry found but wrong count/max. Entries: {pick_entries}"
        return True, "Pick entry with count=6 max=49 found"
    checks.append(run_check("pick command used with count=6 max=49", check_pick_entry))

    # --- 5. Check powerball was executed ---
    def check_powerball_entry():
        if not history_path.exists():
            return False, "History file missing"
        data = json.loads(history_path.read_text())
        for e in data:
            if isinstance(e, dict) and e.get("type") == "powerball":
                return True, "Powerball entry found"
            elif isinstance(e, str) and "'type': 'powerball'" in e:
                return True, "Powerball entry found (string)"
        return False, f"No 'powerball' entry in history. Entries: {[str(x)[:80] for x in data]}"
    checks.append(run_check("powerball command executed", check_powerball_entry))

    # --- 6. Check mega was executed ---
    def check_mega_entry():
        if not history_path.exists():
            return False, "History file missing"
        data = json.loads(history_path.read_text())
        for e in data:
            if isinstance(e, dict) and e.get("type") == "mega":
                return True, "Mega entry found"
            elif isinstance(e, str) and "'type': 'mega'" in e:
                return True, "Mega entry found (string)"
        return False, f"No 'mega' entry in history. Entries: {[str(x)[:80] for x in data]}"
    checks.append(run_check("mega command executed", check_mega_entry))

    # --- 7. Check check command was used with correct winning numbers ---
    def check_check_entry():
        if not history_path.exists():
            return False, "History file missing"
        data = json.loads(history_path.read_text())
        for e in data:
            winning_str = "7 14 21 28 35 42"
            if isinstance(e, dict) and e.get("type") == "check":
                w = e.get("winning", "")
                if all(n in w for n in ["7", "14", "21", "28", "35", "42"]):
                    return True, f"Check entry found with correct winning numbers: {w}"
            elif isinstance(e, str) and "'type': 'check'" in e:
                if all(n in e for n in ["7", "14", "21", "28", "35", "42"]):
                    return True, f"Check entry found (string) with winning numbers"
        return False, f"No 'check' entry with winning='7 14 21 28 35 42'. Entries: {[str(x)[:100] for x in data]}"
    checks.append(run_check("check command used with winning numbers '7 14 21 28 35 42'", check_check_entry))

    # --- 8. Check stats file reflects at least all operations ---
    stats_path = home / ".local/share/lottery/stats.json"
    def check_stats_values():
        if not stats_path.exists():
            return False, f"Stats file not found at {stats_path}"
        stats = json.loads(stats_path.read_text())
        errors = []
        if stats.get("total_picks", 0) < 1:
            errors.append(f"total_picks={stats.get('total_picks')} (expected >=1)")
        if stats.get("powerball_plays", 0) < 1:
            errors.append(f"powerball_plays={stats.get('powerball_plays')} (expected >=1)")
        if stats.get("mega_plays", 0) < 1:
            errors.append(f"mega_plays={stats.get('mega_plays')} (expected >=1)")
        if stats.get("total_checks", 0) < 1:
            errors.append(f"total_checks={stats.get('total_checks')} (expected >=1)")
        if errors:
            return False, f"Stats inconsistency: {errors}"
        return True, f"Stats OK: {stats}"
    checks.append(run_check("Stats file reflects all required operations", check_stats_values))

    # --- 9. Report contains numeric values (not empty/zeroed out) ---
    def check_report_has_numbers():
        import re
        numbers = re.findall(r'\d+', report_content)
        if not numbers:
            return False, "Report contains no numeric values - stats may not have been written"
        # At minimum total_picks should be >=1
        kv_matches = re.findall(r'(\w+):\s*(\d+)', report_content)
        stat_dict = {k: int(v) for k, v in kv_matches}
        if stat_dict.get("total_picks", 0) < 1:
            return False, f"Stats in report show total_picks=0 or missing. Parsed: {stat_dict}"
        return True, f"Report contains meaningful stats: {stat_dict}"
    checks.append(run_check("lottery_report.txt has non-zero stat values", check_report_has_numbers))

    # --- Compute score ---
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    output = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()