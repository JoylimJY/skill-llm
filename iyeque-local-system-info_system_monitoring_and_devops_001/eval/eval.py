import sys
import json
import subprocess
from pathlib import Path

def main(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_score = 5

    # --- Locate the output file ---
    target_files = list(workspace.rglob("pre_deploy_health_snapshot.json"))

    check_file_exists = {
        "name": "Output file pre_deploy_health_snapshot.json exists",
        "passed": len(target_files) > 0,
        "detail": f"Found {len(target_files)} matching file(s): {[str(f) for f in target_files]}"
    }
    checks.append(check_file_exists)
    if not check_file_exists["passed"]:
        return finalize(checks, 0.0, max_score)

    target_file = target_files[0]

    # --- Parse JSON ---
    try:
        data = json.loads(target_file.read_text())
    except Exception as e:
        checks.append({"name": "File is valid JSON", "passed": False, "detail": str(e)})
        return finalize(checks, 0.0, max_score)

    checks.append({"name": "File is valid JSON", "passed": True, "detail": "Parsed successfully."})

    # --- Check: summary section with required keys ---
    summary_ok = False
    summary_detail = ""
    try:
        assert "summary" in data, "Missing top-level 'summary' key"
        s = data["summary"]
        assert "cpu" in s, "Missing summary.cpu"
        assert "memory" in s, "Missing summary.memory"
        assert "disk" in s, "Missing summary.disk"
        cpu = s["cpu"]
        assert "cpu_percent" in cpu, "Missing cpu.cpu_percent"
        assert "cpu_count" in cpu, "Missing cpu.cpu_count"
        assert "load_avg" in cpu, "Missing cpu.load_avg"
        mem = s["memory"]
        assert "total" in mem, "Missing memory.total"
        assert "available" in mem, "Missing memory.available"
        assert "percent" in mem, "Missing memory.percent"
        disk = s["disk"]
        assert "percent" in disk, "Missing disk.percent"
        assert "total" in disk, "Missing disk.total"
        assert "free" in disk, "Missing disk.free"
        summary_ok = True
        summary_detail = "All required summary fields present."
        total_score += 1
    except AssertionError as e:
        summary_detail = str(e)

    checks.append({"name": "summary section has correct structure (cpu/memory/disk fields)", "passed": summary_ok, "detail": summary_detail})

    # --- Check: processes section with exactly 5 entries ---
    processes_ok = False
    processes_detail = ""
    try:
        assert "processes" in data, "Missing top-level 'processes' key"
        procs = data["processes"]
        assert isinstance(procs, list), f"'processes' must be a list, got {type(procs)}"
        assert len(procs) == 5, f"Expected exactly 5 processes (--limit 5), got {len(procs)}"
        for i, p in enumerate(procs):
            assert "pid" in p, f"Process {i} missing 'pid'"
            assert "name" in p, f"Process {i} missing 'name'"
            assert "cpu_percent" in p, f"Process {i} missing 'cpu_percent'"
            assert "memory_percent" in p, f"Process {i} missing 'memory_percent'"
        processes_ok = True
        processes_detail = f"Correctly contains {len(procs)} processes with all required fields."
        total_score += 1
    except AssertionError as e:
        processes_detail = str(e)

    checks.append({"name": "processes section has exactly 5 entries with pid/name/cpu_percent/memory_percent", "passed": processes_ok, "detail": processes_detail})

    # --- Check: health_flags section derived from real thresholds ---
    flags_ok = False
    flags_detail = ""
    try:
        assert "health_flags" in data, "Missing top-level 'health_flags' key"
        hf = data["health_flags"]
        assert "cpu_ok" in hf, "Missing health_flags.cpu_ok"
        assert "memory_ok" in hf, "Missing health_flags.memory_ok"
        assert "disk_ok" in hf, "Missing health_flags.disk_ok"
        assert isinstance(hf["cpu_ok"], bool), "health_flags.cpu_ok must be bool"
        assert isinstance(hf["memory_ok"], bool), "health_flags.memory_ok must be bool"
        assert isinstance(hf["disk_ok"], bool), "health_flags.disk_ok must be bool"

        # Verify flags are consistent with the actual summary values captured
        summary = data["summary"]
        cpu_pct = summary["cpu"]["cpu_percent"]
        mem_pct = summary["memory"]["percent"]
        disk_pct = summary["disk"]["percent"]

        expected_cpu_ok = cpu_pct < 70
        expected_mem_ok = mem_pct < 80
        expected_disk_ok = disk_pct < 85

        assert hf["cpu_ok"] == expected_cpu_ok, (
            f"cpu_ok={hf['cpu_ok']} but cpu_percent={cpu_pct} -> expected {expected_cpu_ok}"
        )
        assert hf["memory_ok"] == expected_mem_ok, (
            f"memory_ok={hf['memory_ok']} but memory.percent={mem_pct} -> expected {expected_mem_ok}"
        )
        assert hf["disk_ok"] == expected_disk_ok, (
            f"disk_ok={hf['disk_ok']} but disk.percent={disk_pct} -> expected {expected_disk_ok}"
        )
        flags_ok = True
        flags_detail = f"health_flags correctly derived: cpu_ok={hf['cpu_ok']} (cpu={cpu_pct}%), mem_ok={hf['memory_ok']} (mem={mem_pct}%), disk_ok={hf['disk_ok']} (disk={disk_pct}%)."
        total_score += 1
    except AssertionError as e:
        flags_detail = str(e)

    checks.append({"name": "health_flags correctly derived from real system metrics with proper thresholds", "passed": flags_ok, "detail": flags_detail})

    # --- Check: load_avg is a list of 3 normalized floats (normalized by cpu_count) ---
    load_avg_ok = False
    load_avg_detail = ""
    try:
        load_avg = data["summary"]["cpu"]["load_avg"]
        assert isinstance(load_avg, list), f"load_avg must be a list, got {type(load_avg)}"
        assert len(load_avg) == 3, f"load_avg must have 3 values (1m, 5m, 15m), got {len(load_avg)}"
        for v in load_avg:
            assert isinstance(v, (int, float)), f"load_avg values must be numeric, got {type(v)}"
        # All values should be non-negative
        assert all(v >= 0 for v in load_avg), f"load_avg values must be non-negative: {load_avg}"
        load_avg_ok = True
        load_avg_detail = f"load_avg={load_avg} is a valid 3-element normalized list."
        total_score += 1
    except (KeyError, AssertionError, TypeError) as e:
        load_avg_detail = str(e)

    checks.append({"name": "load_avg is a 3-element list of non-negative normalized floats", "passed": load_avg_ok, "detail": load_avg_detail})

    return finalize(checks, total_score, max_score)


def finalize(checks, total_score, max_score):
    passed_checks = sum(1 for c in checks if c["passed"])
    all_passed = all(c["passed"] for c in checks)
    score = round(total_score / max_score, 4)
    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "argument check", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    main(sys.argv[1])