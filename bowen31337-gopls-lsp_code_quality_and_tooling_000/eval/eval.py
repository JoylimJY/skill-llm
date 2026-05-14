#!/usr/bin/env python3
"""
Evaluation script for the currency service modernization task.
Checks:
  1. go.mod exists with a valid module declaration
  2. converter.go is properly formatted (gofmt -l returns nothing)
  3. go vet ./... passes (no errors)
  4. go build ./... succeeds
  5. go test ./... passes
  6. gopls.yaml exists in the project root with required keys
"""

import sys
import os
import subprocess
import json

def run(cmd, cwd=None, capture=True):
    r = subprocess.run(
        cmd, shell=True, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return r.returncode, r.stdout, r.stderr

def find_project_root(workspace):
    """Return the directory containing go.mod, searching under workspace."""
    for root, dirs, files in os.walk(workspace):
        if "go.mod" in files:
            return root
    return None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── 1. go.mod exists and has a module declaration ──────────────────────────
    project_root = find_project_root(workspace)
    gomod_ok = project_root is not None
    gomod_detail = f"go.mod found at: {project_root}" if gomod_ok else "go.mod not found anywhere under workspace"

    if gomod_ok:
        gomod_path = os.path.join(project_root, "go.mod")
        try:
            content = open(gomod_path).read()
            has_module = content.strip().startswith("module ")
            has_go_directive = "go 1." in content
            gomod_ok = has_module and has_go_directive
            gomod_detail = (
                f"go.mod valid (module + go directive present)" if gomod_ok
                else f"go.mod malformed — missing 'module' or 'go' directive. Content: {content[:200]}"
            )
        except Exception as e:
            gomod_ok = False
            gomod_detail = f"Error reading go.mod: {e}"

    checks.append({"name": "go_mod_exists_and_valid", "passed": gomod_ok, "detail": gomod_detail})

    if not gomod_ok:
        # Cannot run Go commands without a module
        for name in ["converter_go_formatted", "go_vet_passes", "go_build_passes", "go_tests_pass", "gopls_yaml_valid"]:
            checks.append({"name": name, "passed": False, "detail": "Skipped — go.mod missing or invalid"})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    # ── 2. converter.go is properly formatted ─────────────────────────────────
    converter_path = None
    for root, dirs, files in os.walk(project_root):
        if "converter.go" in files:
            candidate = os.path.join(root, "converter.go")
            # Prefer the one NOT in testdata
            if "testdata" not in candidate:
                converter_path = candidate
                break

    fmt_ok = False
    fmt_detail = "converter.go not found"
    if converter_path:
        rc, out, err = run(f"gofmt -l {converter_path}")
        # gofmt -l prints the filename if it needs formatting; empty output = already formatted
        if rc == 0 and out.strip() == "":
            fmt_ok = True
            fmt_detail = "converter.go is properly formatted"
        else:
            fmt_ok = False
            fmt_detail = f"converter.go still needs formatting. gofmt -l output: '{out.strip()}' stderr: '{err.strip()}'"
    checks.append({"name": "converter_go_formatted", "passed": fmt_ok, "detail": fmt_detail})

    # ── 3. go vet ./... passes ─────────────────────────────────────────────────
    rc, out, err = run("go vet ./...", cwd=project_root)
    vet_ok = rc == 0
    vet_detail = (
        "go vet passed with no issues"
        if vet_ok
        else f"go vet failed (rc={rc}):\nstdout: {out[:500]}\nstderr: {err[:500]}"
    )
    checks.append({"name": "go_vet_passes", "passed": vet_ok, "detail": vet_detail})

    # ── 4. go build ./... succeeds ────────────────────────────────────────────
    rc, out, err = run("go build ./...", cwd=project_root)
    build_ok = rc == 0
    build_detail = (
        "go build ./... succeeded"
        if build_ok
        else f"go build failed (rc={rc}):\nstdout: {out[:500]}\nstderr: {err[:500]}"
    )
    checks.append({"name": "go_build_passes", "passed": build_ok, "detail": build_detail})

    # ── 5. go test ./... passes ───────────────────────────────────────────────
    rc, out, err = run("go test ./...", cwd=project_root)
    test_ok = rc == 0
    test_detail = (
        f"go test passed:\n{out[:500]}"
        if test_ok
        else f"go test failed (rc={rc}):\nstdout: {out[:500]}\nstderr: {err[:500]}"
    )
    checks.append({"name": "go_tests_pass", "passed": test_ok, "detail": test_detail})

    # ── 6. gopls.yaml exists with required configuration keys ─────────────────
    gopls_path = None
    # Search for gopls.yaml anywhere under workspace
    for root, dirs, files in os.walk(workspace):
        if "gopls.yaml" in files:
            gopls_path = os.path.join(root, "gopls.yaml")
            break

    gopls_ok = False
    gopls_detail = "gopls.yaml not found anywhere under workspace"

    if gopls_path:
        try:
            import yaml
            with open(gopls_path) as f:
                cfg = yaml.safe_load(f)

            if not isinstance(cfg, dict):
                gopls_detail = f"gopls.yaml is not a valid YAML mapping. Parsed: {cfg}"
            else:
                required_top = {"completeUnimported", "staticcheck"}
                required_analyses = {"unusedparams", "shadow"}

                missing_top = required_top - set(cfg.keys())
                analyses = cfg.get("analyses", {})
                missing_analyses = required_analyses - set(analyses.keys() if isinstance(analyses, dict) else [])

                # Check values are truthy (true)
                bad_values = []
                for k in required_top - missing_top:
                    if not cfg.get(k):
                        bad_values.append(f"{k} is not true")
                for k in required_analyses - missing_analyses:
                    if not analyses.get(k):
                        bad_values.append(f"analyses.{k} is not true")

                if missing_top or missing_analyses or bad_values:
                    gopls_detail = (
                        f"gopls.yaml incomplete. "
                        f"Missing top-level keys: {missing_top}. "
                        f"Missing analyses keys: {missing_analyses}. "
                        f"Wrong values: {bad_values}."
                    )
                else:
                    gopls_ok = True
                    gopls_detail = f"gopls.yaml valid at {gopls_path} with all required keys set to true"
        except Exception as e:
            gopls_detail = f"Error parsing gopls.yaml: {e}"

    checks.append({"name": "gopls_yaml_valid", "passed": gopls_ok, "detail": gopls_detail})

    # ── Score ──────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 4)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()