import sys
import json
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = Path(sys.argv[1])
    checks = []
    score = 0.0

    # ------------------------------------------------------------------ #
    # FIND THE OUTPUT FILE: agent is asked to create health_report.json   #
    # ------------------------------------------------------------------ #
    candidates = list(workspace.rglob("health_report.json"))

    def check_file_exists():
        if not candidates:
            return False, "health_report.json not found anywhere in workspace"
        return True, f"Found at: {candidates[0]}"

    c = run_check("health_report.json exists", check_file_exists)
    checks.append(c)
    if not c["passed"]:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    report_path = candidates[0]

    # ------------------------------------------------------------------ #
    # PARSE JSON                                                           #
    # ------------------------------------------------------------------ #
    def check_valid_json():
        try:
            data = json.loads(report_path.read_text())
            return True, "Valid JSON"
        except Exception as e:
            return False, f"Invalid JSON: {e}"

    c = run_check("valid JSON", check_valid_json)
    checks.append(c)
    if not c["passed"]:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    data = json.loads(report_path.read_text())

    # ------------------------------------------------------------------ #
    # CHECK: summary section present with correct sub-keys                #
    # ------------------------------------------------------------------ #
    def check_summary_structure():
        if "summary" not in data:
            return False, "'summary' key missing from top-level report"
        s = data["summary"]
        required_top = {"cpu", "memory", "disk"}
        missing = required_top - set(s.keys())
        if missing:
            return False, f"'summary' missing keys: {missing}"
        return True, "summary has cpu, memory, disk sections"

    c = run_check("summary section structure", check_summary_structure)
    checks.append(c)

    # ------------------------------------------------------------------ #
    # CHECK: summary.cpu has correct fields from sysinfo output           #
    # ------------------------------------------------------------------ #
    def check_cpu_fields():
        s = data.get("summary", {})
        cpu = s.get("cpu", {})
        required = {"cpu_percent", "cpu_count", "load_avg"}
        missing = required - set(cpu.keys())
        if missing:
            return False, f"summary.cpu missing fields: {missing}"
        # load_avg must be a list of 3 floats (proprietary: normalized by cpu_count)
        la = cpu["load_avg"]
        if not isinstance(la, list) or len(la) != 3:
            return False, f"load_avg must be a list of 3 values, got: {la}"
        if not isinstance(cpu["cpu_count"], int) or cpu["cpu_count"] < 1:
            return False, f"cpu_count must be a positive integer, got: {cpu['cpu_count']}"
        if not (0.0 <= cpu["cpu_percent"] <= 100.0):
            return False, f"cpu_percent out of range [0,100]: {cpu['cpu_percent']}"
        return True, f"cpu fields valid: count={cpu['cpu_count']}, load_avg length=3"

    c = run_check("summary.cpu field correctness", check_cpu_fields)
    checks.append(c)

    # ------------------------------------------------------------------ #
    # CHECK: summary.memory has correct fields and byte-scale values      #
    # ------------------------------------------------------------------ #
    def check_memory_fields():
        s = data.get("summary", {})
        mem = s.get("memory", {})
        required = {"total", "available", "percent", "swap_percent"}
        missing = required - set(mem.keys())
        if missing:
            return False, f"summary.memory missing fields: {missing}"
        # total/available must be in bytes (large integers, not MB/GB strings)
        if not isinstance(mem["total"], (int, float)) or mem["total"] < 1_000_000:
            return False, f"memory.total should be bytes (large int), got: {mem['total']}"
        if not isinstance(mem["available"], (int, float)) or mem["available"] < 0:
            return False, f"memory.available invalid: {mem['available']}"
        if not (0.0 <= mem["percent"] <= 100.0):
            return False, f"memory.percent out of range: {mem['percent']}"
        return True, f"memory fields valid: total={mem['total']} bytes, percent={mem['percent']}"

    c = run_check("summary.memory field correctness", check_memory_fields)
    checks.append(c)

    # ------------------------------------------------------------------ #
    # CHECK: summary.disk has correct fields                               #
    # ------------------------------------------------------------------ #
    def check_disk_fields():
        s = data.get("summary", {})
        disk = s.get("disk", {})
        required = {"total", "used", "free", "percent"}
        missing = required - set(disk.keys())
        if missing:
            return False, f"summary.disk missing fields: {missing}"
        if not isinstance(disk["total"], (int, float)) or disk["total"] < 1_000_000:
            return False, f"disk.total should be bytes, got: {disk['total']}"
        if not (0.0 <= disk["percent"] <= 100.0):
            return False, f"disk.percent out of range: {disk['percent']}"
        return True, f"disk fields valid: total={disk['total']} bytes, percent={disk['percent']}"

    c = run_check("summary.disk field correctness", check_disk_fields)
    checks.append(c)

    # ------------------------------------------------------------------ #
    # CHECK: processes section present and is a list                      #
    # ------------------------------------------------------------------ #
    def check_processes_present():
        if "processes" not in data:
            return False, "'processes' key missing from top-level report"
        procs = data["processes"]
        if not isinstance(procs, list):
            return False, f"'processes' should be a list, got: {type(procs)}"
        if len(procs) == 0:
            return False, "processes list is empty"
        return True, f"processes is a non-empty list with {len(procs)} entries"

    c = run_check("processes section present", check_processes_present)
    checks.append(c)

    # ------------------------------------------------------------------ #
    # CHECK: exactly 5 processes (--limit 5 required by the task)         #
    # ------------------------------------------------------------------ #
    def check_processes_limit():
        procs = data.get("processes", [])
        if len(procs) > 5:
            return False, f"Expected at most 5 processes (--limit 5), got {len(procs)}"
        return True, f"processes count={len(procs)} (<= 5, consistent with --limit 5)"

    c = run_check("processes limited to 5", check_processes_limit)
    checks.append(c)

    # ------------------------------------------------------------------ #
    # CHECK: each process entry has required fields from SKILL.md schema  #
    # ------------------------------------------------------------------ #
    def check_process_fields():
        procs = data.get("processes", [])
        required = {"pid", "name", "username", "cpu_percent", "memory_percent"}
        for i, p in enumerate(procs):
            missing = required - set(p.keys())
            if missing:
                return False, f"Process entry {i} missing fields: {missing}"
            if not isinstance(p["pid"], int):
                return False, f"Process entry {i}: pid must be int, got {type(p['pid'])}"
            if not isinstance(p["cpu_percent"], (int, float)):
                return False, f"Process entry {i}: cpu_percent must be numeric"
            if not isinstance(p["memory_percent"], (int, float)):
                return False, f"Process entry {i}: memory_percent must be numeric"
        return True, f"All {len(procs)} process entries have correct fields"

    c = run_check("process entry field schema", check_process_fields)
    checks.append(c)

    # ------------------------------------------------------------------ #
    # CHECK: data was obtained via the actual skill tool (not fabricated) #
    # We verify by re-running the tool and comparing structural ranges    #
    # ------------------------------------------------------------------ #
    def check_data_is_live():
        try:
            result = subprocess.run(
                ["uv", "run", "--with", "psutil",
                 "skills/local-system-info/sysinfo.py", "summary"],
                capture_output=True, text=True, cwd=str(workspace), timeout=30
            )
            if result.returncode != 0:
                return False, f"Could not re-run sysinfo.py to verify: {result.stderr}"
            live = json.loads(result.stdout)
            # Compare cpu_count: must match (it's a static hardware fact)
            reported_count = data.get("summary", {}).get("cpu", {}).get("cpu_count")
            live_count = live.get("cpu", {}).get("cpu_count")
            if reported_count != live_count:
                return False, f"cpu_count mismatch: report={reported_count}, live={live_count}. Data may be fabricated."
            # Compare disk.total: must be within 1% (static filesystem fact)
            reported_disk_total = data.get("summary", {}).get("disk", {}).get("total")
            live_disk_total = live.get("disk", {}).get("total")
            if reported_disk_total and live_disk_total:
                ratio = abs(reported_disk_total - live_disk_total) / max(live_disk_total, 1)
                if ratio > 0.01:
                    return False, f"disk.total mismatch: report={reported_disk_total}, live={live_disk_total}"
            return True, f"cpu_count and disk.total match live system values"
        except Exception as e:
            return False, f"Verification error: {e}"

    c = run_check("data matches live system (not fabricated)", check_data_is_live)
    checks.append(c)

    # ------------------------------------------------------------------ #
    # SCORE                                                                #
    # ------------------------------------------------------------------ #
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall = all(c["passed"] for c in checks)

    print(json.dumps({
        "passed": overall,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()