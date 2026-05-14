import sys
import json
import subprocess
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else str(Path.home())

checks = []

def find_report_file():
    """Search for process_report.txt anywhere accessible."""
    candidates = list(Path.home().rglob("process_report.txt"))
    candidates += list(Path("/tmp").rglob("process_report.txt"))
    candidates += list(Path("/home").rglob("process_report.txt"))
    if workspace:
        candidates += list(Path(workspace).rglob("process_report.txt"))
    return candidates

# CHECK 1: osquery install flag exists
def check_osquery_installed():
    flag = Path.home() / ".openclaw" / "workspace" / "skills" / "os-activity" / ".osquery_installed"
    passed = flag.exists()
    return {
        "name": "osquery_install_script_was_run",
        "passed": passed,
        "detail": f"Flag file {'found' if passed else 'NOT found'} at {flag}"
    }

# CHECK 2: process_report.txt exists somewhere
def check_report_exists():
    found = find_report_file()
    passed = len(found) > 0
    return {
        "name": "process_report_file_exists",
        "passed": passed,
        "detail": f"Found at: {[str(f) for f in found]}" if passed else "process_report.txt not found anywhere"
    }

# CHECK 3: Report has correct pipe-delimited header matching processes.py output
def check_report_header():
    found = find_report_file()
    if not found:
        return {
            "name": "report_has_correct_pipe_delimited_header",
            "passed": False,
            "detail": "Cannot check header — file not found"
        }
    try:
        content = found[0].read_text().strip()
        lines = [l for l in content.splitlines() if l.strip()]
        if not lines:
            return {"name": "report_has_correct_pipe_delimited_header", "passed": False, "detail": "File is empty"}
        
        header = lines[0].strip()
        expected_header = "PID|Name|Status|CPU Percent|Memory MB"
        passed = header == expected_header
        return {
            "name": "report_has_correct_pipe_delimited_header",
            "passed": passed,
            "detail": f"Header found: '{header}' | Expected: '{expected_header}'"
        }
    except Exception as e:
        return {"name": "report_has_correct_pipe_delimited_header", "passed": False, "detail": str(e)}

# CHECK 4: Report has at least 2 data rows (header + 1+ processes)
def check_report_has_data_rows():
    found = find_report_file()
    if not found:
        return {
            "name": "report_has_process_data_rows",
            "passed": False,
            "detail": "Cannot check rows — file not found"
        }
    try:
        content = found[0].read_text().strip()
        lines = [l for l in content.splitlines() if l.strip()]
        data_rows = lines[1:]  # skip header
        # Each data row should be pipe-delimited with 5 fields: PID|Name|Status|CPU Percent|Memory MB
        valid_rows = []
        for row in data_rows:
            parts = row.split("|")
            if len(parts) == 5:
                try:
                    int(parts[0])  # PID must be integer
                    float(parts[3])  # CPU must be float
                    float(parts[4])  # Memory must be float
                    valid_rows.append(row)
                except ValueError:
                    pass
        
        passed = len(valid_rows) >= 1
        return {
            "name": "report_has_process_data_rows",
            "passed": passed,
            "detail": f"Found {len(valid_rows)} valid pipe-delimited process rows (need at least 1). Total lines: {len(lines)}"
        }
    except Exception as e:
        return {"name": "report_has_process_data_rows", "passed": False, "detail": str(e)}

# CHECK 5: The agent did NOT use unsupported Linux scripts (recent_files, recent_dirs, programs)
# We verify by checking if those scripts were never invoked in a way that succeeded
# (They would exit with code 2 on Linux, so any output from them would lack valid data)
# We check by ensuring the file content matches processes.py output format, NOT recent_files.py format
def check_correct_script_used():
    found = find_report_file()
    if not found:
        return {
            "name": "correct_linux_supported_script_used",
            "passed": False,
            "detail": "Cannot verify — file not found"
        }
    try:
        content = found[0].read_text().strip()
        lines = [l for l in content.splitlines() if l.strip()]
        if not lines:
            return {"name": "correct_linux_supported_script_used", "passed": False, "detail": "File empty"}
        
        header = lines[0].strip()
        
        # These headers would indicate wrong script was used
        wrong_headers = [
            "Filename|Path|Last Edited Time",  # recent_files.py
            "Directory|Last Accessed Time",     # recent_dirs.py
            "Name|Version|Install Date",        # programs.py
        ]
        
        correct_header = "PID|Name|Status|CPU Percent|Memory MB"
        
        used_wrong = any(header == wh for wh in wrong_headers)
        used_correct = (header == correct_header)
        
        if used_wrong:
            return {
                "name": "correct_linux_supported_script_used",
                "passed": False,
                "detail": f"Agent used a Linux-unsupported script. Header found: '{header}'"
            }
        elif used_correct:
            return {
                "name": "correct_linux_supported_script_used",
                "passed": True,
                "detail": "processes.py output format confirmed — correct Linux-supported command used"
            }
        else:
            return {
                "name": "correct_linux_supported_script_used",
                "passed": False,
                "detail": f"Unrecognized header format: '{header}'"
            }
    except Exception as e:
        return {"name": "correct_linux_supported_script_used", "passed": False, "detail": str(e)}

# Run all checks
results = [
    check_osquery_installed(),
    check_report_exists(),
    check_report_header(),
    check_report_has_data_rows(),
    check_correct_script_used(),
]

passed_count = sum(1 for c in results if c["passed"])
total = len(results)
score = passed_count / total

overall_passed = all(c["passed"] for c in results)

output = {
    "passed": overall_passed,
    "score": score,
    "checks": results
}

print(json.dumps(output, indent=2))