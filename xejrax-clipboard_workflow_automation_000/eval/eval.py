import sys
import json
import os
import subprocess

def run_checks(workspace):
    checks = []
    passed_all = True

    # ---- Re-derive expected values (same logic as gen_inputs_script) ----
    import random
    random.seed(42)

    ips_raw = [
        "192.168.1.10", "10.0.0.5", "172.16.0.3", "192.168.1.10",
        "10.0.0.7", "192.168.1.15", "10.0.0.5", "172.16.0.9",
        "192.168.1.10", "10.0.0.12", "172.16.0.3", "192.168.1.20",
        "10.0.0.5", "172.16.0.3", "192.168.1.25",
    ]
    statuses = [200, 200, 404, 200, 500, 200, 200, 301, 200, 404, 200, 200, 500, 200, 200]
    paths = [
        "/index.html", "/api/v1/health", "/missing", "/api/v1/data",
        "/crash", "/static/style.css", "/api/v1/users", "/old-page",
        "/favicon.ico", "/not-here", "/api/v1/metrics", "/dashboard",
        "/error", "/api/v1/config", "/home",
    ]
    log_lines = []
    for i in range(len(ips_raw)):
        ts = f"2024-06-15 12:{i:02d}:00"
        line = f'{ips_raw[i]} - - [{ts}] "GET {paths[i]} HTTP/1.1" {statuses[i]} {random.randint(200,5000)}'
        log_lines.append(line)
    log_lines.insert(3, "MALFORMED LINE - no ip or status")
    log_lines.insert(7, "::1 - - [2024-06-15 12:07:00] INVALID REQUEST")
    log_lines.insert(11, "")

    ok_lines = [l for l in log_lines if " 200 " in l]
    unique_ips_expected = set()
    for l in ok_lines:
        parts = l.split()
        if parts:
            unique_ips_expected.add(parts[0])

    expected_ok_count = len(ok_lines)
    expected_unique_ips = len(unique_ips_expected)

    # ---- Check 1: Report file exists ----
    report_path = os.path.join(workspace, "reports", "monthly", "clipboard_relay_report.txt")
    if not os.path.isfile(report_path):
        # Also search recursively as fallback
        from pathlib import Path
        found = list(Path(workspace).rglob("clipboard_relay_report.txt"))
        if found:
            report_path = str(found[0])
            checks.append({
                "name": "report_file_exists",
                "passed": True,
                "detail": f"Found report at non-standard path: {report_path}"
            })
        else:
            checks.append({
                "name": "report_file_exists",
                "passed": False,
                "detail": "clipboard_relay_report.txt not found anywhere in workspace"
            })
            passed_all = False
            return checks, passed_all
    else:
        checks.append({
            "name": "report_file_exists",
            "passed": True,
            "detail": f"Report found at expected path: {report_path}"
        })

    # ---- Check 2: Read report content ----
    try:
        with open(report_path, "r") as f:
            content = f.read().strip()
    except Exception as e:
        checks.append({
            "name": "report_readable",
            "passed": False,
            "detail": f"Could not read report: {e}"
        })
        passed_all = False
        return checks, passed_all

    checks.append({
        "name": "report_readable",
        "passed": True,
        "detail": f"Report content: {repr(content)}"
    })

    # ---- Check 3: OK_REQUESTS line present and correct ----
    ok_requests_found = False
    ok_requests_correct = False
    ok_requests_value = None
    try:
        for line in content.splitlines():
            if line.startswith("OK_REQUESTS:"):
                ok_requests_found = True
                val_str = line.split(":", 1)[1].strip()
                ok_requests_value = int(val_str)
                if ok_requests_value == expected_ok_count:
                    ok_requests_correct = True
                break
    except Exception as e:
        checks.append({
            "name": "ok_requests_line",
            "passed": False,
            "detail": f"Error parsing OK_REQUESTS line: {e}"
        })
        passed_all = False

    if ok_requests_found:
        passed = ok_requests_correct
        if not passed:
            passed_all = False
        checks.append({
            "name": "ok_requests_line",
            "passed": passed,
            "detail": f"OK_REQUESTS={ok_requests_value}, expected={expected_ok_count}"
        })
    else:
        if "ok_requests_line" not in [c["name"] for c in checks]:
            checks.append({
                "name": "ok_requests_line",
                "passed": False,
                "detail": f"OK_REQUESTS: line not found in report. Content: {repr(content)}"
            })
            passed_all = False

    # ---- Check 4: UNIQUE_IPS line present and correct ----
    unique_ips_found = False
    unique_ips_correct = False
    unique_ips_value = None
    try:
        for line in content.splitlines():
            if line.startswith("UNIQUE_IPS:"):
                unique_ips_found = True
                val_str = line.split(":", 1)[1].strip()
                unique_ips_value = int(val_str)
                if unique_ips_value == expected_unique_ips:
                    unique_ips_correct = True
                break
    except Exception as e:
        checks.append({
            "name": "unique_ips_line",
            "passed": False,
            "detail": f"Error parsing UNIQUE_IPS line: {e}"
        })
        passed_all = False

    if unique_ips_found:
        passed = unique_ips_correct
        if not passed:
            passed_all = False
        checks.append({
            "name": "unique_ips_line",
            "passed": passed,
            "detail": f"UNIQUE_IPS={unique_ips_value}, expected={expected_unique_ips}"
        })
    else:
        if "unique_ips_line" not in [c["name"] for c in checks]:
            checks.append({
                "name": "unique_ips_line",
                "passed": False,
                "detail": f"UNIQUE_IPS: line not found in report. Content: {repr(content)}"
            })
            passed_all = False

    # ---- Check 5: Verify clipboard was actually used as relay ----
    # We test this by independently loading the log file into clipboard using xclip
    # and checking the mechanism is functional. We also verify the agent left
    # correct filtered content accessible via clipboard after their pipeline.
    # We attempt to read the current clipboard state (may be stale, best-effort).
    clipboard_check_passed = False
    clipboard_detail = ""
    try:
        env = os.environ.copy()
        env["DISPLAY"] = ":99"
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True, text=True, timeout=5, env=env
        )
        clipboard_content = result.stdout
        # The clipboard may contain the filtered log lines or the final report text
        # We check loosely: either contains "200" lines or report keywords
        if ("OK_REQUESTS" in clipboard_content or
                "UNIQUE_IPS" in clipboard_content or
                " 200 " in clipboard_content or
                "192.168" in clipboard_content):
            clipboard_check_passed = True
            clipboard_detail = f"Clipboard contains relevant relay data (length={len(clipboard_content)})"
        else:
            clipboard_detail = f"Clipboard does not appear to contain relay data. Got: {repr(clipboard_content[:200])}"
    except Exception as e:
        clipboard_detail = f"Could not read clipboard for verification: {e}"

    checks.append({
        "name": "clipboard_used_as_relay",
        "passed": clipboard_check_passed,
        "detail": clipboard_detail
    })
    # clipboard relay check is advisory: don't fail overall if values are correct
    # but it must be used — make it required
    if not clipboard_check_passed:
        passed_all = False

    return checks, passed_all


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks, passed_all = run_checks(workspace)

    # Compute score
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0

    output = {
        "passed": passed_all,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))