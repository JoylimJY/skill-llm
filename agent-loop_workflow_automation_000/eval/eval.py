import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []

    # ── 1. config.ini is correctly fixed ─────────────────────────────────────
    config_path = ws / "config.ini"
    config_ok_port = False
    config_ok_db_url = False
    config_ok_timeout = False
    try:
        import configparser
        cfg = configparser.ConfigParser()
        cfg.read(config_path)
        try:
            port = cfg.getint("server", "port")
            config_ok_port = (port == 8080)
        except Exception:
            config_ok_port = False
        try:
            db_url = cfg.get("database", "db_url")
            config_ok_db_url = db_url.startswith("postgres://")
        except Exception:
            config_ok_db_url = False
        try:
            timeout = cfg.getint("server", "timeout")
            config_ok_timeout = (timeout == 30)
        except Exception:
            config_ok_timeout = False
    except Exception as e:
        pass

    checks.append({
        "name": "config.ini: port fixed to integer 8080",
        "passed": config_ok_port,
        "detail": f"port == 8080: {config_ok_port}"
    })
    checks.append({
        "name": "config.ini: db_url key present with postgres URI",
        "passed": config_ok_db_url,
        "detail": f"db_url starts with postgres://: {config_ok_db_url}"
    })
    checks.append({
        "name": "config.ini: timeout = 30 added under [server]",
        "passed": config_ok_timeout,
        "detail": f"timeout == 30: {config_ok_timeout}"
    })

    # ── 2. service_rules.json is valid JSON ───────────────────────────────────
    rules_path = ws / "data" / "raw" / "service_rules.json"
    rules_valid = False
    rules_has_currencies = False
    try:
        with open(rules_path) as f:
            rules = json.load(f)
        rules_valid = True
        rules_has_currencies = "allowed_currencies" in rules
    except Exception as e:
        pass

    checks.append({
        "name": "service_rules.json: valid JSON (no trailing comma)",
        "passed": rules_valid,
        "detail": f"Parsed successfully: {rules_valid}"
    })
    checks.append({
        "name": "service_rules.json: contains allowed_currencies key",
        "passed": rules_has_currencies,
        "detail": f"allowed_currencies present: {rules_has_currencies}"
    })

    # ── 3. All 5 pytest tests pass ────────────────────────────────────────────
    import subprocess
    tests_passed = False
    test_detail = ""
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_service.py", "-v", "--tb=short"],
            cwd=str(ws),
            capture_output=True,
            text=True,
            timeout=60
        )
        output = result.stdout + result.stderr
        test_detail = output[-1000:] if len(output) > 1000 else output
        tests_passed = (result.returncode == 0) and ("5 passed" in output)
    except Exception as e:
        test_detail = str(e)

    checks.append({
        "name": "All 5 pytest tests pass",
        "passed": tests_passed,
        "detail": test_detail
    })

    # ── 4. memory/tasks.md exists and contains a numbered plan ───────────────
    tasks_path = ws / "memory" / "tasks.md"
    tasks_exists = False
    tasks_has_plan = False
    tasks_has_progress = False
    try:
        content = tasks_path.read_text()
        tasks_exists = True
        # Must contain a numbered list (plan)
        tasks_has_plan = bool(re.search(r'^\s*\d+\.', content, re.MULTILINE))
        # Must contain progress/step completion notes (e.g., "Step X complete", "completed", "done", "verified", "✓")
        tasks_has_progress = bool(re.search(
            r'(step\s*\d+\s*(complete|done|finished|verified)|completed|✓|progress|executed|verified)',
            content, re.IGNORECASE
        ))
    except Exception as e:
        pass

    checks.append({
        "name": "memory/tasks.md exists",
        "passed": tasks_exists,
        "detail": f"File present: {tasks_exists}"
    })
    checks.append({
        "name": "memory/tasks.md contains a numbered plan",
        "passed": tasks_has_plan,
        "detail": f"Numbered steps found: {tasks_has_plan}"
    })
    checks.append({
        "name": "memory/tasks.md contains per-step progress records",
        "passed": tasks_has_progress,
        "detail": f"Progress/completion markers found: {tasks_has_progress}"
    })

    # ── 5. report.md exists with exactly 3 required sections ─────────────────
    # Search for report.md anywhere in workspace
    report_path = None
    for candidate in ws.rglob("report.md"):
        report_path = candidate
        break

    report_exists = report_path is not None
    report_has_what = False
    report_has_evidence = False
    report_has_caveats = False
    report_detail = "File not found"

    if report_exists:
        try:
            report_content = report_path.read_text()
            report_detail = report_content[:500]
            # Section 1: What was done
            report_has_what = bool(re.search(
                r'(what\s+was\s+done|## ?1\.|### ?1\.|what\s+i\s+did)',
                report_content, re.IGNORECASE
            ))
            # Section 2: Verification evidence
            report_has_evidence = bool(re.search(
                r'(verification\s+evidence|## ?2\.|### ?2\.|evidence|verified)',
                report_content, re.IGNORECASE
            ))
            # Section 3: Caveats / next steps
            report_has_caveats = bool(re.search(
                r'(caveats|next\s+steps|## ?3\.|### ?3\.|follow.?up)',
                report_content, re.IGNORECASE
            ))
        except Exception as e:
            report_detail = str(e)

    checks.append({
        "name": "report.md exists",
        "passed": report_exists,
        "detail": f"Found at: {report_path}"
    })
    checks.append({
        "name": "report.md: Section 1 — What was done",
        "passed": report_has_what,
        "detail": f"Section found: {report_has_what}"
    })
    checks.append({
        "name": "report.md: Section 2 — Verification evidence",
        "passed": report_has_evidence,
        "detail": f"Section found: {report_has_evidence}"
    })
    checks.append({
        "name": "report.md: Section 3 — Caveats / next steps",
        "passed": report_has_caveats,
        "detail": f"Section found: {report_has_caveats}"
    })

    # ── Score ─────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = (passed_count == total)

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))