import sys
import os
import json
import subprocess
import csv
import re
from pathlib import Path

def run_checks(workspace):
    checks = []
    score_total = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal score_total, max_score
        max_score += weight
        if passed:
            score_total += weight

    # =========================================================
    # PART 1: audit_gpus.sh
    # =========================================================

    # Find audit_gpus.sh
    audit_script_paths = list(Path(workspace).rglob("audit_gpus.sh"))
    audit_script_path = audit_script_paths[0] if audit_script_paths else None

    add_check(
        "audit_gpus.sh exists",
        audit_script_path is not None,
        f"Found at: {audit_script_path}" if audit_script_path else "File not found anywhere in workspace",
        weight=1.0
    )

    if audit_script_path:
        script_content = ""
        try:
            with open(audit_script_path) as f:
                script_content = f.read()
        except Exception as e:
            add_check("audit_gpus.sh readable", False, str(e), weight=0.5)

        # Check uses nvidia-smi -L
        uses_list = bool(re.search(r'nvidia-smi\s+.*-L|-L\s+.*nvidia-smi|nvidia-smi\s+-L', script_content))
        add_check(
            "audit_gpus.sh uses 'nvidia-smi -L' for GPU listing",
            uses_list,
            f"Script contains '-L' flag: {uses_list}",
            weight=1.0
        )

        # Check uses -q -d MEMORY,POWER (or -d POWER,MEMORY)
        uses_qd = bool(re.search(r'nvidia-smi.*-q.*-d.*(MEMORY|POWER)', script_content, re.IGNORECASE) or
                       re.search(r'nvidia-smi.*-d.*(MEMORY|POWER).*-q', script_content, re.IGNORECASE))
        add_check(
            "audit_gpus.sh uses '-q -d MEMORY,POWER' style query",
            uses_qd,
            f"Found memory/power query pattern: {uses_qd}",
            weight=1.0
        )

        # Check uses --query-compute-apps with correct fields
        uses_compute_apps = bool(re.search(
            r'--query-compute-apps=["\']?.*pid.*process_name.*used_memory|--query-compute-apps=["\']?.*pid.*used_memory',
            script_content, re.IGNORECASE
        ) or re.search(r'--query-compute-apps', script_content))
        add_check(
            "audit_gpus.sh uses --query-compute-apps",
            uses_compute_apps,
            f"Found --query-compute-apps: {uses_compute_apps}",
            weight=1.5
        )

        # Check --format=csv is used alongside --query-compute-apps
        uses_csv_format = bool(re.search(r'--format=csv', script_content))
        add_check(
            "audit_gpus.sh uses --format=csv",
            uses_csv_format,
            f"Found --format=csv: {uses_csv_format}",
            weight=1.0
        )

        # Check output is redirected to process_report.csv
        saves_csv = bool(re.search(r'process_report\.csv', script_content))
        add_check(
            "audit_gpus.sh saves output to process_report.csv",
            saves_csv,
            f"Found 'process_report.csv' in script: {saves_csv}",
            weight=1.0
        )

        # Run the script and check process_report.csv is generated
        try:
            script_dir = str(audit_script_path.parent)
            os.chmod(str(audit_script_path), 0o755)
            result = subprocess.run(
                ["bash", str(audit_script_path)],
                cwd=script_dir,
                capture_output=True, text=True, timeout=30
            )
            run_success = result.returncode == 0
            add_check(
                "audit_gpus.sh executes without error",
                run_success,
                f"Return code: {result.returncode}. Stderr: {result.stderr[:300]}",
                weight=2.0
            )
        except Exception as e:
            add_check("audit_gpus.sh executes without error", False, str(e), weight=2.0)
            run_success = False

        # Check process_report.csv content
        csv_paths = list(Path(workspace).rglob("process_report.csv"))
        csv_path = csv_paths[0] if csv_paths else None
        add_check(
            "process_report.csv exists",
            csv_path is not None,
            f"Found at: {csv_path}" if csv_path else "process_report.csv not found",
            weight=1.5
        )

        if csv_path:
            try:
                with open(csv_path) as f:
                    content = f.read().strip()

                # Must have data rows with PIDs
                has_pid_12345 = "12345" in content
                has_pid_12346 = "12346" in content
                has_pid_12347 = "12347" in content
                has_pids = has_pid_12345 and has_pid_12346 and has_pid_12347
                add_check(
                    "process_report.csv contains expected PIDs (12345, 12346, 12347)",
                    has_pids,
                    f"12345: {has_pid_12345}, 12346: {has_pid_12346}, 12347: {has_pid_12347}",
                    weight=2.0
                )

                # Must contain process names
                has_python = "python" in content.lower()
                add_check(
                    "process_report.csv contains process names",
                    has_python,
                    f"Contains python process entries: {has_python}",
                    weight=1.0
                )

                # Must contain memory values
                has_memory = bool(re.search(r'\d+\s*(MiB|MB|mib)?', content))
                add_check(
                    "process_report.csv contains memory usage values",
                    has_memory,
                    f"Memory values found: {has_memory}",
                    weight=1.0
                )
            except Exception as e:
                add_check("process_report.csv is parseable", False, str(e), weight=2.0)

    # =========================================================
    # PART 2: gpu_health_report.py and gpu_health_report.json
    # =========================================================

    py_script_paths = list(Path(workspace).rglob("gpu_health_report.py"))
    py_script_path = py_script_paths[0] if py_script_paths else None

    add_check(
        "gpu_health_report.py exists",
        py_script_path is not None,
        f"Found at: {py_script_path}" if py_script_path else "gpu_health_report.py not found",
        weight=1.0
    )

    if py_script_path:
        try:
            with open(py_script_path) as f:
                py_content = f.read()
        except Exception as e:
            py_content = ""
            add_check("gpu_health_report.py readable", False, str(e), weight=0.5)

        # Check uses pynvml
        uses_pynvml = "pynvml" in py_content
        add_check(
            "gpu_health_report.py imports pynvml",
            uses_pynvml,
            f"Found 'pynvml': {uses_pynvml}",
            weight=1.0
        )

        # Check uses nvmlInit
        uses_init = "nvmlInit" in py_content
        add_check(
            "gpu_health_report.py calls nvmlInit()",
            uses_init,
            f"Found nvmlInit: {uses_init}",
            weight=0.5
        )

        # Check power conversion: must divide by 1000 (mW -> W)
        power_conversion = bool(re.search(r'/\s*1000', py_content))
        add_check(
            "gpu_health_report.py converts power from mW to W (divides by 1000)",
            power_conversion,
            f"Found division by 1000 for power conversion: {power_conversion}",
            weight=2.0
        )

        # Check uses NVML_TEMPERATURE_GPU constant
        uses_temp_const = "NVML_TEMPERATURE_GPU" in py_content
        add_check(
            "gpu_health_report.py uses NVML_TEMPERATURE_GPU constant",
            uses_temp_const,
            f"Found NVML_TEMPERATURE_GPU: {uses_temp_const}",
            weight=1.5
        )

        # Check uses decode('utf-8') or decode() for GPU name
        uses_decode = bool(re.search(r'\.decode\s*\(', py_content))
        add_check(
            "gpu_health_report.py decodes GPU name bytes (uses .decode())",
            uses_decode,
            f"Found .decode(): {uses_decode}",
            weight=1.5
        )

        # Run the Python script
        try:
            script_dir = str(py_script_path.parent)
            result = subprocess.run(
                ["python3", str(py_script_path)],
                cwd=script_dir,
                capture_output=True, text=True, timeout=30
            )
            py_run_ok = result.returncode == 0
            add_check(
                "gpu_health_report.py executes without error",
                py_run_ok,
                f"Return code: {result.returncode}. Stderr: {result.stderr[:300]}",
                weight=2.0
            )
        except Exception as e:
            add_check("gpu_health_report.py executes without error", False, str(e), weight=2.0)
            py_run_ok = False

    # Evaluate gpu_health_report.json
    json_paths = list(Path(workspace).rglob("gpu_health_report.json"))
    json_path = json_paths[0] if json_paths else None

    add_check(
        "gpu_health_report.json exists",
        json_path is not None,
        f"Found at: {json_path}" if json_path else "gpu_health_report.json not found",
        weight=1.5
    )

    if json_path:
        try:
            with open(json_path) as f:
                report = json.load(f)

            # Must be a list or dict with GPU entries
            # Support both list-of-dicts and dict with 'gpus' key
            if isinstance(report, list):
                gpu_entries = report
            elif isinstance(report, dict) and "gpus" in report:
                gpu_entries = report["gpus"]
            elif isinstance(report, dict):
                # Could be indexed by GPU id
                gpu_entries = list(report.values()) if report else []
            else:
                gpu_entries = []

            add_check(
                "gpu_health_report.json contains GPU entries (non-empty)",
                len(gpu_entries) > 0,
                f"Number of GPU entries: {len(gpu_entries)}",
                weight=1.0
            )

            if len(gpu_entries) >= 3:
                # Check GPU 0: temp=62, power=312W, mem_used=61440MB, gpu_util=87
                # Check GPU 1: power=398W -> power_critical; mem_used=79872 out of 81920 = 97.5% -> memory_critical
                # Check GPU 2: idle

                def find_gpu_entry(entries, expected_temp=None, expected_util=None):
                    for e in entries:
                        if isinstance(e, dict):
                            temp_val = e.get("temperature") or e.get("temp") or e.get("temperature_c")
                            util_val = e.get("gpu_util") or e.get("utilization") or e.get("gpu_utilization") or e.get("util")
                            if expected_temp and temp_val == expected_temp:
                                return e
                            if expected_util is not None and util_val == expected_util:
                                return e
                    return None

                # Check temperature values are present
                all_temps_present = all(
                    any(
                        e.get("temperature") == t or e.get("temp") == t or e.get("temperature_c") == t
                        for e in gpu_entries if isinstance(e, dict)
                    )
                    for t in [62, 71, 45]
                )
                add_check(
                    "gpu_health_report.json has correct temperature values (62, 71, 45°C)",
                    all_temps_present,
                    f"Temperatures match expected values: {all_temps_present}",
                    weight=2.0
                )

                # Check power values are in Watts (312, 398, 28) NOT milliwatts (312000, 398000, 28000)
                all_powers_present = all(
                    any(
                        abs((e.get("power") or e.get("power_w") or e.get("power_watts") or 0) - p) < 1.0
                        for e in gpu_entries if isinstance(e, dict)
                    )
                    for p in [312.0, 398.0, 28.0]
                )
                any_mw_values = any(
                    any(
                        (e.get("power") or e.get("power_w") or e.get("power_watts") or 0) > 1000
                        for e in gpu_entries if isinstance(e, dict)
                    )
                    for _ in [1]
                )
                add_check(
                    "gpu_health_report.json power values are in Watts (~312, ~398, ~28), NOT milliwatts",
                    all_powers_present and not any_mw_values,
                    f"Correct watt values found: {all_powers_present}, mW values detected: {any_mw_values}",
                    weight=3.0
                )

                # Check memory values are in MB
                def mem_mb_close(val, expected_mb, tol=50):
                    return abs(val - expected_mb) < tol

                # mem_used in MB: GPU0=61440, GPU1=79872, GPU2=512
                all_mem_present = False
                for e in gpu_entries:
                    if isinstance(e, dict):
                        mem_used = e.get("memory_used_mb") or e.get("mem_used") or e.get("memory_used") or e.get("mem_used_mb")
                        if mem_used and mem_mb_close(mem_used, 61440, 200):
                            all_mem_present = True
                            break
                add_check(
                    "gpu_health_report.json memory values are in MB (e.g., ~61440 for GPU 0)",
                    all_mem_present,
                    f"Found MB-scale memory value for GPU 0: {all_mem_present}",
                    weight=2.0
                )

                # Check power_critical flag: GPU 1 (398W > 390W threshold)
                gpu1_power_critical = False
                gpu0_power_not_critical = False
                gpu2_power_not_critical = False
                for e in gpu_entries:
                    if isinstance(e, dict):
                        power_val = e.get("power") or e.get("power_w") or e.get("power_watts") or 0
                        is_power_crit = e.get("power_critical") or e.get("is_power_critical")
                        if abs(power_val - 398.0) < 2.0 and is_power_crit:
                            gpu1_power_critical = True
                        if abs(power_val - 312.0) < 2.0 and not is_power_crit:
                            gpu0_power_not_critical = True
                        if abs(power_val - 28.0) < 2.0 and not is_power_crit:
                            gpu2_power_not_critical = True

                add_check(
                    "gpu_health_report.json correctly flags GPU 1 as power_critical (398W > 390W)",
                    gpu1_power_critical,
                    f"GPU with 398W marked as power_critical: {gpu1_power_critical}",
                    weight=2.0
                )
                add_check(
                    "gpu_health_report.json does not falsely flag GPU 0 or 2 as power_critical",
                    gpu0_power_not_critical and gpu2_power_not_critical,
                    f"GPU 0 (312W) not critical: {gpu0_power_not_critical}, GPU 2 (28W) not critical: {gpu2_power_not_critical}",
                    weight=1.0
                )

                # Check memory_critical: GPU 1 has 79872/81920 MB = 97.5% > 90%
                # GPU 0: 61440/81920 = 75% -> not critical
                gpu1_mem_critical = False
                gpu0_mem_not_critical = False
                for e in gpu_entries:
                    if isinstance(e, dict):
                        mem_used = e.get("memory_used_mb") or e.get("mem_used") or e.get("memory_used") or e.get("mem_used_mb") or 0
                        is_mem_crit = e.get("memory_critical") or e.get("is_memory_critical")
                        if mem_mb_close(mem_used, 79872, 500) and is_mem_crit:
                            gpu1_mem_critical = True
                        if mem_mb_close(mem_used, 61440, 500) and not is_mem_crit:
                            gpu0_mem_not_critical = True

                add_check(
                    "gpu_health_report.json correctly flags GPU 1 as memory_critical (97.5% > 90%)",
                    gpu1_mem_critical,
                    f"GPU 1 (79872/81920 MB) marked as memory_critical: {gpu1_mem_critical}",
                    weight=2.0
                )
                add_check(
                    "gpu_health_report.json does not falsely flag GPU 0 as memory_critical (75% < 90%)",
                    gpu0_mem_not_critical,
                    f"GPU 0 (61440/81920 MB) not flagged as memory_critical: {gpu0_mem_not_critical}",
                    weight=1.0
                )

                # Check GPU utilization values present
                all_utils_present = all(
                    any(
                        (e.get("gpu_util") or e.get("utilization") or e.get("gpu_utilization") or e.get("util") or -1) == u
                        for e in gpu_entries if isinstance(e, dict)
                    )
                    for u in [87, 99, 0]
                )
                add_check(
                    "gpu_health_report.json has correct GPU utilization values (87, 99, 0%)",
                    all_utils_present,
                    f"Utilization values match: {all_utils_present}",
                    weight=1.5
                )

                # Check GPU names are decoded strings (not bytes)
                name_is_string = False
                for e in gpu_entries:
                    if isinstance(e, dict):
                        name = e.get("name") or e.get("gpu_name") or ""
                        if isinstance(name, str) and "A100" in name:
                            name_is_string = True
                            break
                add_check(
                    "gpu_health_report.json GPU names are decoded strings containing 'A100'",
                    name_is_string,
                    f"Found decoded A100 name string: {name_is_string}",
                    weight=1.5
                )

            else:
                add_check(
                    "gpu_health_report.json has entries for all 3 GPUs",
                    False,
                    f"Only {len(gpu_entries)} entries found, expected 3",
                    weight=5.0
                )

        except json.JSONDecodeError as e:
            add_check("gpu_health_report.json is valid JSON", False, f"JSON parse error: {e}", weight=8.0)
        except Exception as e:
            add_check("gpu_health_report.json evaluation", False, f"Unexpected error: {e}", weight=8.0)

    final_score = round(score_total / max_score, 4) if max_score > 0 else 0.0
    passed = final_score >= 0.75

    return {"passed": passed, "score": final_score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))