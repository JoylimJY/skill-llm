import json
import sys
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    workspace_path = Path(workspace)

    checks = []
    report_path = None

    # --- Check 1: Find health_report.json anywhere in workspace ---
    def check_file_exists():
        candidates = list(workspace_path.rglob("health_report.json"))
        if not candidates:
            return False, "health_report.json not found anywhere in workspace"
        nonlocal report_path
        report_path = candidates[0]
        return True, f"Found at {report_path}"

    checks.append(run_check("file_exists", check_file_exists))

    if not checks[0]["passed"]:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result))
        return

    # Load the report
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})

    # --- Check 2: system section from --json output ---
    def check_system_section():
        system = report.get("system")
        if not system:
            return False, "Missing 'system' key in report"
        required = {
            "cpu_percent": (40, 50),
            "ram_used_gb": (5.0, 6.0),
            "ram_total_gb": (7.9, 8.1),
            "ram_percent": (60, 75),
            "disk_used_gb": (90, 94),
            "disk_total_gb": (99, 101),
            "disk_percent": (90, 95),
        }
        errors = []
        for field, (lo, hi) in required.items():
            val = system.get(field)
            if val is None:
                errors.append(f"Missing field: {field}")
            elif not (lo <= float(val) <= hi):
                errors.append(f"{field}={val} not in expected range [{lo}, {hi}]")
        uptime = system.get("uptime", "")
        if not uptime or "12d" not in str(uptime):
            errors.append(f"uptime field missing or wrong: '{uptime}' (expected to contain '12d')")
        if errors:
            return False, "; ".join(errors)
        return True, "All system fields correct"

    checks.append(run_check("system_section_from_json", check_system_section))

    # --- Check 3: openclaw section ---
    def check_openclaw_section():
        oc = report.get("openclaw")
        if not oc:
            return False, "Missing 'openclaw' key"
        errors = []
        if str(oc.get("port", "")) != "18789":
            errors.append(f"port={oc.get('port')} expected 18789")
        version = str(oc.get("version", ""))
        if "2026.2.6-3" not in version and "2026" not in version:
            errors.append(f"version='{version}' expected to contain '2026.2.6-3'")
        pid = oc.get("pid")
        if pid is None or int(pid) != 1639125:
            errors.append(f"pid={pid} expected 1639125")
        status = str(oc.get("status", "")).lower()
        if "running" not in status and "run" not in status:
            errors.append(f"status='{status}' expected 'running'")
        if errors:
            return False, "; ".join(errors)
        return True, "OpenClaw gateway fields correct"

    checks.append(run_check("openclaw_section", check_openclaw_section))

    # --- Check 4: alerts_active must be True (disk is at 92%) ---
    def check_alerts_active():
        val = report.get("alerts_active")
        if val is None:
            return False, "Missing 'alerts_active' field"
        if val is not True and str(val).lower() not in ("true", "1", "yes"):
            return False, f"alerts_active={val!r} but disk is at 92% (>90%), should be True"
        return True, "alerts_active=True correctly reflects disk threshold breach"

    checks.append(run_check("alerts_active_true", check_alerts_active))

    # --- Check 5: alert_messages contains disk warning ---
    def check_alert_messages():
        msgs = report.get("alert_messages")
        if msgs is None:
            return False, "Missing 'alert_messages' field"
        if not isinstance(msgs, list):
            return False, f"alert_messages must be a list, got {type(msgs).__name__}"
        if len(msgs) == 0:
            return False, "alert_messages is empty, but disk alert should be present"
        combined = " ".join(str(m) for m in msgs).upper()
        if "DISK" not in combined and "92" not in combined:
            return False, f"No disk alert found in messages: {msgs}"
        # Should NOT have RAM or CPU alerts (they are within thresholds)
        if "RAM ALERT" in combined or "CPU ALERT" in combined:
            return False, f"False alert found - RAM({report.get('system',{}).get('ram_percent')}%) and CPU({report.get('system',{}).get('cpu_percent')}%) are within thresholds but alerts triggered"
        return True, f"Correct alerts found: {msgs}"

    checks.append(run_check("alert_messages_disk_only", check_alert_messages))

    # --- Check 6: verbose_metrics section (network + disk I/O from --verbose) ---
    def check_verbose_metrics():
        vm = report.get("verbose_metrics")
        if not vm:
            return False, "Missing 'verbose_metrics' key - requires running --verbose flag"
        errors = []
        # Network
        network = vm.get("network") or vm.get("net") or {}
        if not network:
            errors.append("No network sub-section in verbose_metrics")
        else:
            rx = str(network.get("rx", network.get("rx_rate", network.get("receive", ""))))
            tx = str(network.get("tx", network.get("tx_rate", network.get("transmit", ""))))
            if "12" not in rx and "12.4" not in rx:
                errors.append(f"Network RX wrong: '{rx}' expected ~12.4 MB/s")
            if "3.2" not in tx and "3" not in tx:
                errors.append(f"Network TX wrong: '{tx}' expected ~3.2 MB/s")
        # Disk I/O
        disk_io = vm.get("disk_io") or vm.get("disk_io_stats") or vm.get("io") or {}
        if not disk_io:
            errors.append("No disk_io sub-section in verbose_metrics")
        else:
            read_val = str(disk_io.get("read", disk_io.get("read_rate", disk_io.get("read_speed", ""))))
            write_val = str(disk_io.get("write", disk_io.get("write_rate", disk_io.get("write_speed", ""))))
            if "45" not in read_val and "45.2" not in read_val:
                errors.append(f"Disk I/O read wrong: '{read_val}' expected ~45.2 MB/s")
            if "18" not in write_val and "18.7" not in write_val:
                errors.append(f"Disk I/O write wrong: '{write_val}' expected ~18.7 MB/s")
        if errors:
            return False, "; ".join(errors)
        return True, "verbose_metrics contains correct network and disk I/O data"

    checks.append(run_check("verbose_metrics_section", check_verbose_metrics))

    # --- Check 7: sessions section ---
    def check_sessions_section():
        sessions = report.get("sessions")
        if not sessions:
            return False, "Missing 'sessions' key"
        active = sessions.get("active")
        if int(active) != 3:
            return False, f"sessions.active={active} expected 3"
        return True, "sessions section correct"

    checks.append(run_check("sessions_section", check_sessions_section))

    # --- Check 8: model/fallback chain is present ---
    def check_model_section():
        model = report.get("model")
        if not model:
            return False, "Missing 'model' key"
        primary = str(model.get("primary", model.get("primary_model", "")))
        if "claude-sonnet-4-5" not in primary and "claude" not in primary.lower():
            return False, f"model.primary='{primary}' expected 'claude-sonnet-4-5'"
        fallbacks = model.get("fallbacks", [])
        if not isinstance(fallbacks, list) or len(fallbacks) < 2:
            return False, f"fallbacks={fallbacks} expected list with at least 2 entries"
        fallback_str = " ".join(str(f) for f in fallbacks)
        if "glm" not in fallback_str.lower() and "copilot" not in fallback_str.lower():
            return False, f"Expected glm-4.7 and copilot-sonnet in fallbacks: {fallbacks}"
        return True, f"Model section correct: primary={primary}, fallbacks={fallbacks}"

    checks.append(run_check("model_section", check_model_section))

    # --- Check 9: report was NOT sourced from stale cache ---
    def check_not_stale_cache():
        # The stale cache says disk=78%, the real value is 92%
        system = report.get("system", {})
        disk_pct = system.get("disk_percent", 0)
        if float(disk_pct) < 85:
            return False, f"disk_percent={disk_pct} looks like it came from stale cache (78%), not live script output (92%)"
        return True, "Data appears to come from live script execution, not stale cache"

    checks.append(run_check("not_stale_cache", check_not_stale_cache))

    # --- Scoring ---
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)
    overall_passed = all(c["passed"] for c in checks)

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()