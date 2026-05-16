#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path
from datetime import datetime

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
home = Path.home()

checks = []
total_score = 0.0
total_weight = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, total_weight
    total_weight += weight
    if passed:
        total_score += weight

# =========================================================
# CHECK 1: ~/.bambu/config.json has CORRECT credentials
# =========================================================
try:
    config_path = home / ".bambu" / "config.json"
    if not config_path.exists():
        add_check("correct_setup_credentials", False,
                  f"~/.bambu/config.json does not exist. Agent never ran 'bambu setup'.", weight=2.0)
    else:
        cfg = json.loads(config_path.read_text())
        ip_ok = cfg.get("ip") == "192.168.10.47"
        serial_ok = cfg.get("serial") == "01S09C382900001"
        code_ok = cfg.get("access_code") == "12345678"
        # Must NOT have stale fields
        not_stale = cfg.get("serial") != "STALE_SERIAL_XYZ" and cfg.get("ip") != "192.168.1.101"
        all_correct = ip_ok and serial_ok and code_ok and not_stale
        detail = (f"ip={'✓' if ip_ok else '✗'} serial={'✓' if serial_ok else '✗'} "
                  f"access_code={'✓' if code_ok else '✗'} not_stale={'✓' if not_stale else '✗'} | "
                  f"Got: ip={cfg.get('ip')} serial={cfg.get('serial')} code={cfg.get('access_code')}")
        add_check("correct_setup_credentials", all_correct, detail, weight=2.0)
except Exception as e:
    add_check("correct_setup_credentials", False, f"Exception reading config: {e}", weight=2.0)

# =========================================================
# CHECK 2: Command log exists and 'bambu ping' was called
# =========================================================
try:
    log_path = home / ".bambu" / "command_log.jsonl"
    if not log_path.exists():
        add_check("ping_verified", False, "command_log.jsonl missing - no commands logged", weight=1.0)
    else:
        log_entries = [json.loads(l) for l in log_path.read_text().strip().splitlines() if l.strip()]
        all_args = [e.get("args", []) for e in log_entries]
        ping_called = any(a and a[0] == "ping" for a in all_args)
        add_check("ping_verified", ping_called,
                  f"'bambu ping' called: {ping_called}. Total commands logged: {len(log_entries)}", weight=1.0)
except Exception as e:
    add_check("ping_verified", False, f"Exception reading log: {e}", weight=1.0)

# =========================================================
# CHECK 3: 'bambu heat' was called with correct PLA temps
#   nozzle:210 bed:60  (from standard PLA profile in SKILL.md and profile file)
# =========================================================
try:
    log_path = home / ".bambu" / "command_log.jsonl"
    if not log_path.exists():
        add_check("pla_temperature_set", False, "command_log.jsonl missing", weight=2.0)
    else:
        log_entries = [json.loads(l) for l in log_path.read_text().strip().splitlines() if l.strip()]
        all_args = [e.get("args", []) for e in log_entries]
        
        heat_calls = [a for a in all_args if a and a[0] == "heat"]
        
        found_correct = False
        found_nozzle_ok = False
        found_bed_ok = False
        details_seen = []
        
        for heat_args in heat_calls:
            # Parse colon-separated key:value pairs
            params = {}
            for token in heat_args[1:]:
                if ":" in token:
                    k, v = token.split(":", 1)
                    params[k.strip().lower()] = v.strip()
            details_seen.append(str(params))
            # PLA: nozzle 210, bed 60 (as per SKILL.md "Preheat for PLA" and profile)
            n_ok = params.get("nozzle") == "210"
            b_ok = params.get("bed") == "60"
            if n_ok:
                found_nozzle_ok = True
            if b_ok:
                found_bed_ok = True
            if n_ok and b_ok:
                found_correct = True
        
        detail = (f"heat calls found: {len(heat_calls)}, correct nozzle:210={found_nozzle_ok}, "
                  f"correct bed:60={found_bed_ok}, both correct={found_correct}. "
                  f"Seen params: {details_seen}")
        add_check("pla_temperature_set", found_correct, detail, weight=2.0)
except Exception as e:
    add_check("pla_temperature_set", False, f"Exception: {e}", weight=2.0)

# =========================================================
# CHECK 4: 'bambu job upload-and-print' called with the correct 3MF file
#   Must NOT be split into separate upload + print commands for this check
# =========================================================
try:
    log_path = home / ".bambu" / "command_log.jsonl"
    if not log_path.exists():
        add_check("upload_and_print_used", False, "command_log.jsonl missing", weight=2.0)
    else:
        log_entries = [json.loads(l) for l in log_path.read_text().strip().splitlines() if l.strip()]
        all_args = [e.get("args", []) for e in log_entries]
        
        # Must use 'bambu job upload-and-print <path>' not separate upload+print
        uap_calls = [a for a in all_args if len(a) >= 3 and a[0] == "job" and a[1] == "upload-and-print"]
        
        found_correct_file = False
        for call in uap_calls:
            fpath = call[2] if len(call) > 2 else ""
            if "enclosure_bracket_v4.3mf" in fpath:
                found_correct_file = True
        
        detail = (f"'bambu job upload-and-print' calls: {len(uap_calls)}, "
                  f"with correct file (enclosure_bracket_v4.3mf): {found_correct_file}. "
                  f"Calls: {uap_calls}")
        add_check("upload_and_print_used", found_correct_file, detail, weight=2.0)
except Exception as e:
    add_check("upload_and_print_used", False, f"Exception: {e}", weight=2.0)

# =========================================================
# CHECK 5: 'bambu ams --json' was called to check AMS status
# =========================================================
try:
    log_path = home / ".bambu" / "command_log.jsonl"
    if not log_path.exists():
        add_check("ams_json_checked", False, "command_log.jsonl missing", weight=1.0)
    else:
        log_entries = [json.loads(l) for l in log_path.read_text().strip().splitlines() if l.strip()]
        all_args = [e.get("args", []) for e in log_entries]
        
        ams_json_called = any(
            a and a[0] == "ams" and "--json" in a
            for a in all_args
        )
        ams_any = any(a and a[0] == "ams" for a in all_args)
        detail = f"'bambu ams --json' called: {ams_json_called}, 'bambu ams' (any): {ams_any}"
        add_check("ams_json_checked", ams_json_called, detail, weight=1.0)
except Exception as e:
    add_check("ams_json_checked", False, f"Exception: {e}", weight=1.0)

# =========================================================
# CHECK 6: print_session_report.json exists and has required fields
# =========================================================
try:
    report_files = list(workspace.rglob("print_session_report.json"))
    if not report_files:
        # Also check home dir
        home_reports = list(home.rglob("print_session_report.json"))
        report_files = home_reports
    
    if not report_files:
        add_check("session_report_exists", False,
                  "print_session_report.json not found anywhere in workspace or home", weight=1.5)
        add_check("session_report_content", False,
                  "Cannot check content: file not found", weight=2.0)
    else:
        report_path = report_files[0]
        add_check("session_report_exists", True,
                  f"Found at: {report_path}", weight=1.5)
        
        # Validate content
        report = json.loads(report_path.read_text())
        
        sub_checks = []
        
        # Must contain printer IP
        has_ip = any(
            "192.168.10.47" in str(v) for v in report.values()
        ) or report.get("ip") == "192.168.10.47" or report.get("printer_ip") == "192.168.10.47"
        sub_checks.append(f"ip present: {has_ip}")
        
        # Must contain serial
        has_serial = any(
            "01S09C382900001" in str(v) for v in report.values()
        ) or "01S09C382900001" in json.dumps(report)
        sub_checks.append(f"serial present: {has_serial}")
        
        # Must mention the print file
        has_file = "enclosure_bracket_v4" in json.dumps(report)
        sub_checks.append(f"print file mentioned: {has_file}")
        
        # Must mention AMS slot 0 or tray 0
        report_str = json.dumps(report).lower()
        has_ams_slot = ("slot 0" in report_str or '"tray": 0' in report_str or 
                        '"tray":0' in report_str or 'tray_0' in report_str or
                        '"slot": 0' in report_str or '"slot":0' in report_str or
                        '"current_tray": 0' in report_str or 'ams_slot' in report_str or
                        'slot_0' in report_str or '"id": 0' in report_str or
                        'tray 0' in report_str or 'slot0' in report_str)
        sub_checks.append(f"AMS slot 0 mentioned: {has_ams_slot}")
        
        # Must include nozzle temperature (210)
        has_nozzle_temp = "210" in json.dumps(report)
        sub_checks.append(f"nozzle temp (210) present: {has_nozzle_temp}")
        
        # Must include bed temperature (60)
        has_bed_temp = "60" in json.dumps(report)
        sub_checks.append(f"bed temp (60) present: {has_bed_temp}")
        
        # Timestamp field exists
        has_timestamp = any(
            k in report for k in ["timestamp", "session_start", "time", "date", "started_at", "created_at"]
        )
        sub_checks.append(f"timestamp field: {has_timestamp}")
        
        critical_ok = has_ip and has_serial and has_file and has_nozzle_temp and has_bed_temp
        all_ok = critical_ok and has_ams_slot and has_timestamp
        
        detail = " | ".join(sub_checks) + f" | CRITICAL={critical_ok} ALL={all_ok}"
        add_check("session_report_content", all_ok, detail, weight=2.0)

except json.JSONDecodeError as e:
    add_check("session_report_content", False, f"Invalid JSON in report: {e}", weight=2.0)
except Exception as e:
    add_check("session_report_content", False, f"Exception: {e}", weight=2.0)

# =========================================================
# FINAL SCORING
# =========================================================
final_score = round(total_score / total_weight, 4) if total_weight > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": final_score,
    "checks": checks
}

print(json.dumps(result, indent=2))