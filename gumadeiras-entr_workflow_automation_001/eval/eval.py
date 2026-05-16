import sys
import json
import os
import subprocess
from pathlib import Path

def run_checks(workspace):
    checks = []
    passed_all = True

    workspace = Path(workspace)

    # --- Check 1: watcher_setup.sh exists and is a valid shell script ---
    watcher_scripts = list(workspace.rglob("watcher_setup.sh"))
    if not watcher_scripts:
        checks.append({
            "name": "watcher_setup.sh exists",
            "passed": False,
            "detail": "Could not find 'watcher_setup.sh' anywhere in the workspace."
        })
        passed_all = False
    else:
        script_path = watcher_scripts[0]
        checks.append({
            "name": "watcher_setup.sh exists",
            "passed": True,
            "detail": f"Found at {script_path}"
        })

        # --- Check 2: Script uses entr ---
        content = script_path.read_text()
        uses_entr = "entr" in content
        checks.append({
            "name": "watcher_setup.sh invokes entr",
            "passed": uses_entr,
            "detail": content[:400] if not uses_entr else "entr found in script."
        })
        if not uses_entr:
            passed_all = False

        # --- Check 3: Uses stdin pipe to feed files to entr (pipe pattern) ---
        has_pipe_to_entr = "|" in content and "entr" in content
        checks.append({
            "name": "File list piped to entr via stdin",
            "passed": has_pipe_to_entr,
            "detail": "Script must pipe a file-listing command into entr via '|'." if not has_pipe_to_entr else "Pipe pattern detected."
        })
        if not has_pipe_to_entr:
            passed_all = False

        # --- Check 4: Uses -s flag for shell interpretation ---
        has_s_flag = "-s" in content
        checks.append({
            "name": "Uses entr -s flag for shell evaluation",
            "passed": has_s_flag,
            "detail": "The -s flag must be used so entr evaluates the command via $SHELL." if not has_s_flag else "-s flag found."
        })
        if not has_s_flag:
            passed_all = False

        # --- Check 5: Watches .py files in pipeline/src ---
        watches_py = ".py" in content and ("pipeline/src" in content or "src/" in content or "find" in content or "ls" in content)
        checks.append({
            "name": "Watches Python source files in pipeline/src",
            "passed": watches_py,
            "detail": "Script should watch *.py files in the pipeline/src directory." if not watches_py else "Python source watching detected."
        })
        if not watches_py:
            passed_all = False

        # --- Check 6: Output is redirected to pipeline/logs/watcher.log ---
        log_file = workspace / "pipeline" / "logs" / "watcher.log"
        has_log_redirect = "watcher.log" in content or "logs/" in content
        checks.append({
            "name": "Log file path referenced in script",
            "passed": has_log_redirect,
            "detail": "Script should redirect output to pipeline/logs/watcher.log." if not has_log_redirect else "Log redirect found."
        })
        if not has_log_redirect:
            passed_all = False

    # --- Check 7: Functional test — run the watcher, trigger a file change, verify output ---
    report_path = workspace / "pipeline" / "output" / "report.json"
    log_path = workspace / "pipeline" / "logs" / "watcher.log"

    # Clean up any pre-existing report
    if report_path.exists():
        report_path.unlink()

    watcher_scripts2 = list(workspace.rglob("watcher_setup.sh"))
    if watcher_scripts2:
        script_path = watcher_scripts2[0]
        # Make executable
        os.chmod(script_path, 0o755)

        try:
            # Launch watcher in background
            proc = subprocess.Popen(
                ["bash", str(script_path)],
                cwd=str(workspace),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            import time
            time.sleep(2)  # Let entr start up

            # Trigger a file change by touching a watched .py file
            trigger_file = workspace / "pipeline" / "src" / "aggregate.py"
            original_content = trigger_file.read_text()
            trigger_file.write_text(original_content + "\n# trigger\n")

            # Wait for entr to detect and react
            time.sleep(4)

            # Kill the watcher
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                pass
            # Kill any lingering entr processes
            subprocess.run(["pkill", "-f", "entr"], capture_output=True)

            # Check report.json was created by the triggered run
            report_created = report_path.exists()
            checks.append({
                "name": "report.json created after file change trigger",
                "passed": report_created,
                "detail": f"Expected {report_path} to be created after triggering file change." if not report_created else "report.json found."
            })
            if not report_created:
                passed_all = False
            else:
                # --- Check 8: report.json has correct content ---
                try:
                    with open(report_path) as f:
                        report = json.load(f)
                    correct_total = report.get("total") == 60
                    correct_count = report.get("count") == 3
                    correct_status = report.get("status") == "ok"
                    content_ok = correct_total and correct_count and correct_status
                    checks.append({
                        "name": "report.json has correct aggregation values",
                        "passed": content_ok,
                        "detail": f"Got {report}. Expected total=60, count=3, status=ok." if not content_ok else f"Correct: {report}"
                    })
                    if not content_ok:
                        passed_all = False
                except Exception as e:
                    checks.append({
                        "name": "report.json has correct aggregation values",
                        "passed": False,
                        "detail": f"Failed to parse report.json: {e}"
                    })
                    passed_all = False

            # --- Check 9: watcher.log contains output ---
            if log_path.exists() and log_path.stat().st_size > 0:
                log_content = log_path.read_text()
                log_has_output = "Aggregation complete" in log_content or "total" in log_content or len(log_content.strip()) > 0
                checks.append({
                    "name": "watcher.log contains captured output",
                    "passed": log_has_output,
                    "detail": f"Log content: {log_content[:200]}" if log_has_output else "Log file empty or missing expected output."
                })
                if not log_has_output:
                    passed_all = False
            else:
                checks.append({
                    "name": "watcher.log contains captured output",
                    "passed": False,
                    "detail": f"watcher.log does not exist or is empty at {log_path}."
                })
                passed_all = False

        except Exception as e:
            checks.append({
                "name": "Functional watcher execution",
                "passed": False,
                "detail": f"Exception during functional test: {e}"
            })
            passed_all = False
    else:
        checks.append({
            "name": "Functional watcher execution",
            "passed": False,
            "detail": "No watcher_setup.sh found; skipping functional test."
        })
        passed_all = False

    score = sum(1 for c in checks if c["passed"]) / len(checks) if checks else 0.0
    return {"passed": passed_all, "score": round(score, 3), "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, indent=2))