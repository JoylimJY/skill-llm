import subprocess
import json
import sys
import os
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def check_pyrightconfig(workspace):
    config_path = Path(workspace) / "pyrightconfig.json"
    if not config_path.exists():
        return False, "pyrightconfig.json not found in project root"
    try:
        with open(config_path) as f:
            cfg = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"pyrightconfig.json is not valid JSON: {e}"

    errors = []

    # Must have include pointing to src
    include = cfg.get("include", [])
    if not isinstance(include, list) or not any("src" in str(i) for i in include):
        errors.append(f"'include' must contain 'src', got: {include}")

    # Must have typeCheckingMode
    mode = cfg.get("typeCheckingMode", "")
    if mode != "basic":
        errors.append(f"'typeCheckingMode' must be 'basic', got: '{mode}'")

    # Must have pythonVersion
    pyver = cfg.get("pythonVersion", "")
    if pyver != "3.10":
        errors.append(f"'pythonVersion' must be '3.10', got: '{pyver}'")

    if errors:
        return False, "; ".join(errors)
    return True, f"pyrightconfig.json is valid: include={include}, mode={mode}, pythonVersion={pyver}"

def check_source_files_exist(workspace):
    required = [
        "src/models/trade.py",
        "src/ingestion/parser.py",
        "src/processing/aggregator.py",
        "src/reporting/report.py",
    ]
    missing = []
    for rel in required:
        p = Path(workspace) / rel
        if not p.exists():
            missing.append(rel)
    if missing:
        return False, f"Source files missing (must not be deleted): {missing}"
    return True, "All source files present"

def check_pyright_passes(workspace):
    """Run pyright from the project root and check for zero errors."""
    env = os.environ.copy()
    result = subprocess.run(
        ["pyright", "--outputjson"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    # pyright exits 0 on success (no errors), non-zero on errors
    raw = result.stdout.strip()
    if not raw:
        # Fallback: try without --outputjson
        result2 = subprocess.run(
            ["pyright"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        combined = result2.stdout + result2.stderr
        if result2.returncode == 0:
            return True, "Pyright reported 0 errors (plain text mode)"
        else:
            # Count errors
            error_lines = [l for l in combined.splitlines() if "error" in l.lower()]
            return False, f"Pyright found errors (exit code {result2.returncode}). Sample:\n" + "\n".join(error_lines[:10])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        if result.returncode == 0:
            return True, "Pyright exited 0 (no errors)"
        return False, f"Could not parse pyright JSON output. stdout: {raw[:500]}"

    summary = data.get("summary", {})
    error_count = summary.get("errorCount", -1)
    warning_count = summary.get("warningCount", 0)

    if error_count == 0:
        return True, f"Pyright: 0 errors, {warning_count} warnings"
    else:
        # Extract diagnostics
        diags = []
        for gd in data.get("generalDiagnostics", []):
            if gd.get("severity") == "error":
                diags.append(f"{gd.get('file','?')}:{gd.get('range',{}).get('start',{}).get('line','?')} - {gd.get('message','?')}")
        return False, f"Pyright found {error_count} error(s). First errors:\n" + "\n".join(diags[:8])

def check_no_type_ignore_blanket(workspace):
    """Agent must not have simply suppressed all errors with # type: ignore."""
    src = Path(workspace) / "src"
    ignore_count = 0
    for pyfile in src.rglob("*.py"):
        content = pyfile.read_text()
        # Count lines with type: ignore
        for line in content.splitlines():
            if "type: ignore" in line:
                ignore_count += 1
    if ignore_count > 6:
        return False, f"Too many '# type: ignore' suppressions found ({ignore_count}). Errors must be fixed, not suppressed."
    return True, f"Acceptable use of type: ignore suppressions ({ignore_count} found)"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace/trade_analytics"
    workspace = Path(workspace)

    checks = []

    checks.append(run_check("pyrightconfig.json exists and has correct fields", lambda: check_pyrightconfig(workspace)))
    checks.append(run_check("Source files are present (not deleted)", lambda: check_source_files_exist(workspace)))
    checks.append(run_check("Pyright reports zero errors on project", lambda: check_pyright_passes(workspace)))
    checks.append(run_check("No excessive type: ignore suppressions", lambda: check_no_type_ignore_blanket(workspace)))

    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()