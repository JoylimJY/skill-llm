import sys
import json
from pathlib import Path

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    overall_passed = True

    # ---- Check 1: File exists ----
    candidates = list(workspace.rglob("system_health_report.json"))
    # Exclude old stale file
    candidates = [c for c in candidates if "old_health_snapshot" not in c.name]
    file_found = len(candidates) > 0
    checks.append({
        "name": "system_health_report.json exists",
        "passed": file_found,
        "detail": f"Found at: {candidates[0]}" if file_found else "File not found anywhere in workspace"
    })
    if not file_found:
        overall_passed = False
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = candidates[0]

    # ---- Check 2: Valid JSON ----
    try:
        with open(report_path) as f:
            data = json.load(f)
        checks.append({"name": "Valid JSON", "passed": True, "detail": "Parsed successfully"})
    except Exception as e:
        checks.append({"name": "Valid JSON", "passed": False, "detail": str(e)})
        overall_passed = False
        return {"passed": False, "score": 0.0, "checks": checks}

    # ---- Check 3: Top-level keys include processes, memory, disk ----
    required_keys = {"processes", "memory", "disk"}
    present_keys = set(k.lower() for k in data.keys())
    has_all_keys = required_keys.issubset(present_keys)
    missing = required_keys - present_keys
    checks.append({
        "name": "Top-level keys: processes, memory, disk",
        "passed": has_all_keys,
        "detail": f"Missing keys: {missing}" if missing else "All required keys present"
    })
    if not has_all_keys:
        overall_passed = False

    # ---- Check 4: processes is a list of exactly 5 items ----
    try:
        # Allow for flexible key name (processes or top_processes, etc)
        proc_key = next(k for k in data.keys() if "process" in k.lower())
        procs = data[proc_key]
        is_list = isinstance(procs, list)
        exactly_5 = len(procs) == 5
        checks.append({
            "name": "processes is a list of exactly 5 items",
            "passed": is_list and exactly_5,
            "detail": f"Type: {type(procs).__name__}, Count: {len(procs) if is_list else 'N/A'}"
        })
        if not (is_list and exactly_5):
            overall_passed = False
    except StopIteration:
        checks.append({
            "name": "processes is a list of exactly 5 items",
            "passed": False,
            "detail": "No key containing 'process' found in report"
        })
        overall_passed = False
        procs = []

    # ---- Check 5: Each process entry has required fields ----
    try:
        required_proc_fields = {"pid", "name", "cpu_percent", "memory_percent"}
        if procs:
            first_proc = procs[0]
            proc_keys_lower = set(k.lower() for k in first_proc.keys())
            has_proc_fields = required_proc_fields.issubset(proc_keys_lower)
            missing_pf = required_proc_fields - proc_keys_lower
            checks.append({
                "name": "Process entries have pid, name, cpu_percent, memory_percent",
                "passed": has_proc_fields,
                "detail": f"Missing: {missing_pf}" if missing_pf else f"Fields present: {list(first_proc.keys())}"
            })
            if not has_proc_fields:
                overall_passed = False
        else:
            checks.append({
                "name": "Process entries have pid, name, cpu_percent, memory_percent",
                "passed": False,
                "detail": "No processes to check"
            })
            overall_passed = False
    except Exception as e:
        checks.append({"name": "Process entries structure", "passed": False, "detail": str(e)})
        overall_passed = False

    # ---- Check 6: memory section has required fields ----
    try:
        mem_key = next(k for k in data.keys() if "mem" in k.lower())
        mem = data[mem_key]
        required_mem_fields = {"total", "available", "percent"}
        mem_keys_lower = set(k.lower() for k in mem.keys())
        has_mem_fields = required_mem_fields.issubset(mem_keys_lower)
        missing_mf = required_mem_fields - mem_keys_lower
        checks.append({
            "name": "memory section has total, available, percent",
            "passed": has_mem_fields,
            "detail": f"Missing: {missing_mf}" if missing_mf else f"Memory fields: {list(mem.keys())}"
        })
        if not has_mem_fields:
            overall_passed = False
        # Check that 'percent' is a numeric value between 0 and 100
        pct = mem.get("percent", mem.get("Percent", None))
        if pct is not None:
            valid_pct = isinstance(pct, (int, float)) and 0.0 <= pct <= 100.0
            checks.append({
                "name": "memory.percent is numeric 0-100",
                "passed": valid_pct,
                "detail": f"Value: {pct}"
            })
            if not valid_pct:
                overall_passed = False
    except StopIteration:
        checks.append({
            "name": "memory section present and valid",
            "passed": False,
            "detail": "No key containing 'mem' found"
        })
        overall_passed = False

    # ---- Check 7: disk section has required fields ----
    try:
        disk_key = next(k for k in data.keys() if "disk" in k.lower())
        disk = data[disk_key]
        required_disk_fields = {"total", "used", "free", "percent"}
        disk_keys_lower = set(k.lower() for k in disk.keys())
        has_disk_fields = required_disk_fields.issubset(disk_keys_lower)
        missing_df = required_disk_fields - disk_keys_lower
        checks.append({
            "name": "disk section has total, used, free, percent",
            "passed": has_disk_fields,
            "detail": f"Missing: {missing_df}" if missing_df else f"Disk fields: {list(disk.keys())}"
        })
        if not has_disk_fields:
            overall_passed = False
        # disk.total should be a large integer (bytes)
        total = disk.get("total", disk.get("Total", None))
        if total is not None:
            valid_total = isinstance(total, (int, float)) and total > 1_000_000
            checks.append({
                "name": "disk.total is a large numeric (bytes)",
                "passed": valid_total,
                "detail": f"Value: {total}"
            })
            if not valid_total:
                overall_passed = False
    except StopIteration:
        checks.append({
            "name": "disk section present and valid",
            "passed": False,
            "detail": "No key containing 'disk' found"
        })
        overall_passed = False

    # ---- Check 8: Processes are sorted by cpu_percent descending ----
    try:
        if procs and len(procs) > 1:
            cpu_values = []
            for p in procs:
                cpu_key = next((k for k in p.keys() if "cpu" in k.lower()), None)
                if cpu_key:
                    cpu_values.append(p[cpu_key])
            if len(cpu_values) > 1:
                is_sorted = all(cpu_values[i] >= cpu_values[i+1] for i in range(len(cpu_values)-1))
                checks.append({
                    "name": "Processes sorted by cpu_percent descending",
                    "passed": is_sorted,
                    "detail": f"CPU values: {cpu_values}"
                })
                if not is_sorted:
                    overall_passed = False
    except Exception as e:
        checks.append({"name": "Process sort order", "passed": False, "detail": str(e)})
        # Not fatal for overall pass

    # ---- Compute score ----
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))