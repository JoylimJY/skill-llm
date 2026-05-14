#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def main():
    workspace = Path(sys.argv[1])
    checks = []
    total_score = 0.0
    max_checks = 10

    # --- Locate the output file ---
    candidates = list(workspace.rglob("capacity_snapshot.json"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named capacity_snapshot.json" if file_found else "capacity_snapshot.json not found anywhere in workspace"
    })
    if not file_found:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    snap_path = candidates[0]

    try:
        data = json.loads(snap_path.read_text())
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})

    # --- Check system_summary block ---
    ss = data.get("system_summary")
    has_summary = isinstance(ss, dict)
    checks.append({
        "name": "system_summary_block_exists",
        "passed": has_summary,
        "detail": "system_summary key present and is a dict" if has_summary else f"system_summary missing or wrong type: {type(ss)}"
    })

    if has_summary:
        # Verify CPU subblock
        cpu_block = ss.get("cpu", {})
        has_cpu_fields = all(k in cpu_block for k in ["cpu_percent", "cpu_count", "load_avg"])
        checks.append({
            "name": "system_summary_cpu_fields",
            "passed": has_cpu_fields,
            "detail": f"cpu block keys: {list(cpu_block.keys())}" if cpu_block else "cpu block missing"
        })

        # Verify memory subblock
        mem_block = ss.get("memory", {})
        has_mem_fields = all(k in mem_block for k in ["total", "available", "percent"])
        checks.append({
            "name": "system_summary_memory_fields",
            "passed": has_mem_fields,
            "detail": f"memory block keys: {list(mem_block.keys())}" if mem_block else "memory block missing"
        })

        # Verify disk subblock
        disk_block = ss.get("disk", {})
        has_disk_fields = all(k in disk_block for k in ["total", "used", "free", "percent"])
        checks.append({
            "name": "system_summary_disk_fields",
            "passed": has_disk_fields,
            "detail": f"disk block keys: {list(disk_block.keys())}" if disk_block else "disk block missing"
        })
    else:
        checks += [
            {"name": "system_summary_cpu_fields", "passed": False, "detail": "skipped: no system_summary"},
            {"name": "system_summary_memory_fields", "passed": False, "detail": "skipped: no system_summary"},
            {"name": "system_summary_disk_fields", "passed": False, "detail": "skipped: no system_summary"},
        ]

    # --- Check top_processes block ---
    tp = data.get("top_processes")
    has_processes = isinstance(tp, list)
    checks.append({
        "name": "top_processes_block_exists",
        "passed": has_processes,
        "detail": "top_processes key present and is a list" if has_processes else f"top_processes missing or wrong type: {type(tp)}"
    })

    if has_processes:
        exactly_five = len(tp) == 5
        checks.append({
            "name": "top_processes_exactly_5",
            "passed": exactly_five,
            "detail": f"Process count: {len(tp)} (expected exactly 5)"
        })

        # Each process should have required fields from the skill's schema
        proc_fields_ok = all(
            isinstance(p, dict) and all(k in p for k in ["pid", "name", "cpu_percent", "memory_percent"])
            for p in tp
        ) if tp else False
        checks.append({
            "name": "top_processes_schema",
            "passed": proc_fields_ok,
            "detail": "All 5 processes have pid, name, cpu_percent, memory_percent" if proc_fields_ok else "One or more process entries missing required fields"
        })
    else:
        checks += [
            {"name": "top_processes_exactly_5", "passed": False, "detail": "skipped: no top_processes list"},
            {"name": "top_processes_schema", "passed": False, "detail": "skipped: no top_processes list"},
        ]

    # --- Check derived_metrics block ---
    dm = data.get("derived_metrics")
    has_derived = isinstance(dm, dict)
    checks.append({
        "name": "derived_metrics_block_exists",
        "passed": has_derived,
        "detail": "derived_metrics key present and is a dict" if has_derived else f"derived_metrics missing or wrong type: {type(dm)}"
    })

    if has_derived and has_summary and isinstance(ss.get("memory"), dict):
        mem = ss["memory"]
        # memory_used_bytes = total - available
        expected_used = mem.get("total", 0) - mem.get("available", 0)
        actual_used = dm.get("memory_used_bytes")
        used_correct = isinstance(actual_used, (int, float)) and abs(actual_used - expected_used) < 1024 * 1024  # 1 MB tolerance
        checks.append({
            "name": "derived_memory_used_bytes_correct",
            "passed": used_correct,
            "detail": f"expected ~{expected_used}, got {actual_used}"
        })
    elif has_derived:
        # Can still check it's a number > 0
        actual_used = dm.get("memory_used_bytes")
        used_plausible = isinstance(actual_used, (int, float)) and actual_used > 0
        checks.append({
            "name": "derived_memory_used_bytes_correct",
            "passed": used_plausible,
            "detail": f"memory_used_bytes={actual_used}, plausibility check (>0)"
        })
    else:
        checks.append({"name": "derived_memory_used_bytes_correct", "passed": False, "detail": "skipped: no derived_metrics or memory block"})

    if has_derived and has_summary and isinstance(ss.get("disk"), dict):
        disk = ss["disk"]
        free_bytes = disk.get("free", 0)
        expected_free_gb = round(free_bytes / (1024 ** 3), 2)
        actual_free_gb = dm.get("disk_free_gb")
        free_correct = isinstance(actual_free_gb, (int, float)) and abs(actual_free_gb - expected_free_gb) < 0.1
        checks.append({
            "name": "derived_disk_free_gb_correct",
            "passed": free_correct,
            "detail": f"expected ~{expected_free_gb}, got {actual_free_gb}"
        })
    elif has_derived:
        actual_free_gb = dm.get("disk_free_gb")
        free_plausible = isinstance(actual_free_gb, (int, float)) and actual_free_gb >= 0
        checks.append({
            "name": "derived_disk_free_gb_correct",
            "passed": free_plausible,
            "detail": f"disk_free_gb={actual_free_gb}, plausibility check (>=0)"
        })
    else:
        checks.append({"name": "derived_disk_free_gb_correct", "passed": False, "detail": "skipped: no derived_metrics or disk block"})

    if has_derived and has_summary and isinstance(ss.get("cpu"), dict):
        cpu_pct = ss["cpu"].get("cpu_percent", 0)
        expected_pressure = cpu_pct > 80
        actual_pressure = dm.get("cpu_under_pressure")
        pressure_correct = isinstance(actual_pressure, bool) and actual_pressure == expected_pressure
        checks.append({
            "name": "derived_cpu_under_pressure_correct",
            "passed": pressure_correct,
            "detail": f"cpu_percent={cpu_pct}, expected cpu_under_pressure={expected_pressure}, got {actual_pressure}"
        })
    elif has_derived:
        actual_pressure = dm.get("cpu_under_pressure")
        pressure_type_ok = isinstance(actual_pressure, bool)
        checks.append({
            "name": "derived_cpu_under_pressure_correct",
            "passed": pressure_type_ok,
            "detail": f"cpu_under_pressure={actual_pressure}, type check (bool)"
        })
    else:
        checks.append({"name": "derived_cpu_under_pressure_correct", "passed": False, "detail": "skipped: no derived_metrics or cpu block"})

    # --- Score ---
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4)
    overall_passed = score >= 0.85

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()