import sys
import os
import json
import subprocess

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0

    # ── Check 1: lifecycle_report.txt exists ────────────────────────────────
    from pathlib import Path
    report_candidates = list(Path(workspace).rglob("lifecycle_report.txt"))
    report_exists = len(report_candidates) > 0
    report_path = report_candidates[0] if report_exists else None

    checks.append({
        "name": "lifecycle_report.txt exists",
        "passed": report_exists,
        "detail": f"Found at {report_path}" if report_exists else "lifecycle_report.txt not found anywhere in workspace"
    })
    if report_exists:
        total_score += 0.15

    # ── Check 2: Watchdog was started (state file or log) ───────────────────
    state_file = "/tmp/gateway_watchdog_state.json"
    log_file = "/tmp/gateway_watchdog.log"

    started_evidence = False
    start_pid = None
    try:
        if os.path.exists(state_file):
            with open(state_file) as f:
                state = json.load(f)
            # Either currently running OR was started at some point
            if state.get("started_at") is not None:
                started_evidence = True
                start_pid = state.get("pid")
    except Exception as e:
        pass

    # Also check log
    log_content = ""
    try:
        if os.path.exists(log_file):
            with open(log_file) as f:
                log_content = f.read()
            if "Gateway Watchdog 已启动" in log_content or "✅ Gateway Watchdog 已启动" in log_content:
                started_evidence = True
    except Exception:
        pass

    checks.append({
        "name": "gateway_watchdog.py start was invoked",
        "passed": started_evidence,
        "detail": f"PID recorded: {start_pid}" if started_evidence else "No evidence of watchdog start in state file or log"
    })
    if started_evidence:
        total_score += 0.20

    # ── Check 3: Status was checked ─────────────────────────────────────────
    status_checked = False
    try:
        if log_content and ("STATUS:running" in log_content or "STATUS:stopped" in log_content or "Gateway Watchdog 运行中" in log_content):
            status_checked = True
    except Exception:
        pass

    # Also check lifecycle_report.txt for evidence
    report_content = ""
    if report_exists:
        try:
            with open(report_path) as f:
                report_content = f.read()
            report_lower = report_content.lower()
            if any(kw in report_lower for kw in ["status", "running", "pid", "运行", "state"]):
                status_checked = True
        except Exception:
            pass

    checks.append({
        "name": "gateway_watchdog.py status was checked",
        "passed": status_checked,
        "detail": "Status command invoked, evidence found in log or report" if status_checked else "No evidence of status check in log or lifecycle_report.txt"
    })
    if status_checked:
        total_score += 0.20

    # ── Check 4: Restart was performed ──────────────────────────────────────
    restart_done = False
    try:
        if log_content and ("重启 Gateway Watchdog" in log_content or "🔄" in log_content):
            restart_done = True
    except Exception:
        pass

    if not restart_done and report_exists:
        try:
            if any(kw in report_content.lower() for kw in ["restart", "重启", "restarted"]):
                restart_done = True
        except Exception:
            pass

    checks.append({
        "name": "gateway_watchdog.py restart was performed",
        "passed": restart_done,
        "detail": "Restart command found in watchdog log or lifecycle report" if restart_done else "No evidence of restart in log or lifecycle_report.txt"
    })
    if restart_done:
        total_score += 0.20

    # ── Check 5: Stop was performed ─────────────────────────────────────────
    stop_done = False
    try:
        if log_content and ("已停止" in log_content or "🛑" in log_content):
            stop_done = True
    except Exception:
        pass

    final_state_stopped = False
    try:
        if os.path.exists(state_file):
            with open(state_file) as f:
                state = json.load(f)
            if not state.get("running", True):
                final_state_stopped = True
                stop_done = True
    except Exception:
        pass

    if not stop_done and report_exists:
        try:
            if any(kw in report_content.lower() for kw in ["stop", "stopped", "停止", "halt"]):
                stop_done = True
        except Exception:
            pass

    checks.append({
        "name": "gateway_watchdog.py stop was performed",
        "passed": stop_done,
        "detail": f"Stop evidence found. Final state running={not final_state_stopped}" if stop_done else "No evidence of stop command in log or report"
    })
    if stop_done:
        total_score += 0.15

    # ── Check 6: lifecycle_report.txt contains meaningful content ───────────
    report_meaningful = False
    if report_exists:
        try:
            with open(report_path) as f:
                content = f.read()
            # Must have at least some lifecycle phase recorded
            phase_keywords = ["start", "status", "restart", "stop", "pid", "running",
                              "启动", "状态", "重启", "停止", "运行", "7/24"]
            matched = sum(1 for kw in phase_keywords if kw.lower() in content.lower())
            if matched >= 3:
                report_meaningful = True
        except Exception as e:
            pass

    checks.append({
        "name": "lifecycle_report.txt contains meaningful lifecycle content",
        "passed": report_meaningful,
        "detail": f"Report at {report_path} has sufficient lifecycle content" if report_meaningful else "Report is missing or lacks lifecycle phase documentation (start/status/restart/stop)"
    })
    if report_meaningful:
        total_score += 0.10

    # ── Check 7: Used gateway_watchdog.py (not cron/systemd) ────────────────
    no_cron_abuse = True
    cron_evidence = []
    try:
        # Check if cron or systemd was configured (would be wrong approach per SKILL.md)
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode == 0 and "gateway" in result.stdout.lower():
            cron_evidence.append("crontab entry for gateway found")
            no_cron_abuse = False
    except Exception:
        pass

    try:
        systemd_paths = ["/etc/systemd/system", "/lib/systemd/system"]
        for sp in systemd_paths:
            if os.path.exists(sp):
                for f in os.listdir(sp):
                    if "gateway" in f.lower() or "openclaw" in f.lower():
                        cron_evidence.append(f"systemd unit: {f}")
                        no_cron_abuse = False
    except Exception:
        pass

    checks.append({
        "name": "Used external watchdog, not cron/systemd (architecture compliance)",
        "passed": no_cron_abuse,
        "detail": "No cron/systemd gateway entries found — correct external watchdog approach used" if no_cron_abuse else f"Incorrect approach detected: {cron_evidence}"
    })
    if no_cron_abuse:
        total_score += 0.10  # bonus for architectural correctness

    # ── Final result ─────────────────────────────────────────────────────────
    passed = total_score >= 0.55  # Must pass majority of checks

    result = {
        "passed": passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()