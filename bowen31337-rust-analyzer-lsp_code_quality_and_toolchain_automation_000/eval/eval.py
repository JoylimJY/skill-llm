import subprocess
import json
import sys
import os
from pathlib import Path

def run(cmd, cwd):
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True, timeout=120
    )
    return result

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    project_dir = os.path.join(workspace, "sensor_firmware")
    checks = []

    # -------------------------------------------------------------------------
    # CHECK 1: .rust-analyzer.json exists and has correct structure
    # -------------------------------------------------------------------------
    ra_config_path = None
    try:
        candidates = list(Path(project_dir).rglob(".rust-analyzer.json"))
        # Must be in project root
        root_candidate = Path(project_dir) / ".rust-analyzer.json"
        if root_candidate.exists():
            ra_config_path = root_candidate
        elif candidates:
            ra_config_path = candidates[0]

        if ra_config_path is None:
            checks.append({
                "name": "rust_analyzer_config_exists",
                "passed": False,
                "detail": ".rust-analyzer.json not found in sensor_firmware project"
            })
        else:
            with open(ra_config_path) as f:
                config = json.load(f)

            # Verify exact structure from SKILL.md
            cos_cmd = config.get("checkOnSave", {}).get("command", "")
            type_hints = config.get("inlayHints", {}).get("typeHints", None)
            param_hints = config.get("inlayHints", {}).get("parameterHints", None)

            correct_structure = (
                cos_cmd == "clippy" and
                type_hints is True and
                param_hints is True
            )
            checks.append({
                "name": "rust_analyzer_config_correct",
                "passed": correct_structure,
                "detail": (
                    f"checkOnSave.command={cos_cmd!r}, "
                    f"inlayHints.typeHints={type_hints}, "
                    f"inlayHints.parameterHints={param_hints}. "
                    f"Expected checkOnSave.command='clippy', typeHints=true, parameterHints=true"
                )
            })
    except Exception as e:
        checks.append({
            "name": "rust_analyzer_config_correct",
            "passed": False,
            "detail": f"Error reading .rust-analyzer.json: {e}"
        })

    # -------------------------------------------------------------------------
    # CHECK 2: cargo test passes (all tests green, including the Fahrenheit fix)
    # -------------------------------------------------------------------------
    try:
        result = run("cargo test 2>&1", cwd=project_dir)
        test_passed = result.returncode == 0
        # Also verify key test names appear as "ok"
        output = result.stdout + result.stderr
        fahrenheit_test_ok = "test tests::test_to_fahrenheit ... ok" in output or \
                             "test_to_fahrenheit" in output and "FAILED" not in output
        checks.append({
            "name": "cargo_test_passes",
            "passed": test_passed,
            "detail": f"cargo test exit code: {result.returncode}. Output tail: {output[-600:] if len(output) > 600 else output}"
        })
    except Exception as e:
        checks.append({
            "name": "cargo_test_passes",
            "passed": False,
            "detail": f"Exception running cargo test: {e}"
        })

    # -------------------------------------------------------------------------
    # CHECK 3: to_fahrenheit bug is fixed — unit test for correctness
    # -------------------------------------------------------------------------
    try:
        result = run("cargo test test_to_fahrenheit -- --nocapture 2>&1", cwd=project_dir)
        output = result.stdout + result.stderr
        fahrenheit_fixed = result.returncode == 0 and "FAILED" not in output
        checks.append({
            "name": "fahrenheit_formula_fixed",
            "passed": fahrenheit_fixed,
            "detail": f"to_fahrenheit tests exit={result.returncode}. Output: {output[-400:]}"
        })
    except Exception as e:
        checks.append({
            "name": "fahrenheit_formula_fixed",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # -------------------------------------------------------------------------
    # CHECK 4: cargo fmt --check passes (code is properly formatted)
    # -------------------------------------------------------------------------
    try:
        result = run("cargo fmt --all -- --check 2>&1", cwd=project_dir)
        fmt_passed = result.returncode == 0
        checks.append({
            "name": "cargo_fmt_check_passes",
            "passed": fmt_passed,
            "detail": f"cargo fmt --check exit code: {result.returncode}. Output: {result.stdout[-400:] if result.stdout else result.stderr[-400:]}"
        })
    except Exception as e:
        checks.append({
            "name": "cargo_fmt_check_passes",
            "passed": False,
            "detail": f"Exception running cargo fmt --check: {e}"
        })

    # -------------------------------------------------------------------------
    # CHECK 5: cargo clippy passes without warnings
    # -------------------------------------------------------------------------
    try:
        result = run("cargo clippy -- -D warnings 2>&1", cwd=project_dir)
        output = result.stdout + result.stderr
        clippy_passed = result.returncode == 0
        checks.append({
            "name": "cargo_clippy_no_warnings",
            "passed": clippy_passed,
            "detail": f"cargo clippy exit code: {result.returncode}. Output tail: {output[-600:] if len(output) > 600 else output}"
        })
    except Exception as e:
        checks.append({
            "name": "cargo_clippy_no_warnings",
            "passed": False,
            "detail": f"Exception running cargo clippy: {e}"
        })

    # -------------------------------------------------------------------------
    # CHECK 6: cargo check passes (basic compilation health)
    # -------------------------------------------------------------------------
    try:
        result = run("cargo check 2>&1", cwd=project_dir)
        check_passed = result.returncode == 0
        checks.append({
            "name": "cargo_check_passes",
            "passed": check_passed,
            "detail": f"cargo check exit code: {result.returncode}. Stderr: {result.stderr[-300:]}"
        })
    except Exception as e:
        checks.append({
            "name": "cargo_check_passes",
            "passed": False,
            "detail": f"Exception running cargo check: {e}"
        })

    # -------------------------------------------------------------------------
    # Scoring
    # -------------------------------------------------------------------------
    # Weights: config(25%), test_pass(25%), fahrenheit_fix(15%), fmt(15%), clippy(15%), check(5%)
    weights = {
        "rust_analyzer_config_correct": 0.25,
        "cargo_test_passes": 0.25,
        "fahrenheit_formula_fixed": 0.15,
        "cargo_fmt_check_passes": 0.15,
        "cargo_clippy_no_warnings": 0.15,
        "cargo_check_passes": 0.05,
    }

    score = 0.0
    for check in checks:
        name = check["name"]
        if check["passed"] and name in weights:
            score += weights[name]

    # Special: config_exists check doesn't add to score (subsumed by config_correct)
    # But if it's failed, config_correct is also failed, already handled.

    all_passed = all(c["passed"] for c in checks if c["name"] != "rust_analyzer_config_exists")

    print(json.dumps({
        "passed": all_passed,
        "score": round(score, 3),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()