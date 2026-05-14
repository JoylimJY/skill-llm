#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import yaml
from pathlib import Path

def run(cmd, cwd=None, capture=True):
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd,
                           capture_output=capture, text=True, timeout=60)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    project_dir = Path(workspace) / "ecu_firmware"
    checks = []
    total_score = 0.0

    # ── CHECK 1: .clangd exists ──────────────────────────────────────────
    clangd_path = project_dir / ".clangd"
    check1 = {"name": ".clangd file exists", "passed": False, "detail": ""}
    if clangd_path.exists():
        check1["passed"] = True
        check1["detail"] = f"Found at {clangd_path}"
    else:
        check1["detail"] = f"Missing: {clangd_path}"
    checks.append(check1)

    # ── CHECK 2: .clangd has correct structure ───────────────────────────
    check2 = {"name": ".clangd has correct CompileFlags and Diagnostics", "passed": False, "detail": ""}
    if clangd_path.exists():
        try:
            with open(clangd_path) as f:
                content = f.read()
            cfg = yaml.safe_load(content)
            errors = []
            if not isinstance(cfg, dict):
                errors.append("Root is not a YAML mapping")
            else:
                # CompileFlags
                cf = cfg.get("CompileFlags", {})
                if not cf:
                    errors.append("Missing CompileFlags section")
                else:
                    add_flags = cf.get("Add", [])
                    if not isinstance(add_flags, list):
                        errors.append("CompileFlags.Add must be a list")
                    else:
                        required_add = {"-std=c++17", "-Wall", "-Wextra"}
                        missing = required_add - set(add_flags)
                        if missing:
                            errors.append(f"CompileFlags.Add missing: {missing}")
                    remove_flags = cf.get("Remove", [])
                    if not isinstance(remove_flags, list):
                        errors.append("CompileFlags.Remove must be a list")
                    else:
                        # Must contain -W* wildcard removal
                        if not any("-W" in str(f) for f in remove_flags):
                            errors.append("CompileFlags.Remove should contain a -W* entry")
                # Diagnostics
                diag = cfg.get("Diagnostics", {})
                if not diag:
                    errors.append("Missing Diagnostics section")
                else:
                    ui = str(diag.get("UnusedIncludes", "")).strip()
                    mi = str(diag.get("MissingIncludes", "")).strip()
                    if ui.lower() != "strict":
                        errors.append(f"Diagnostics.UnusedIncludes should be 'Strict', got '{ui}'")
                    if mi.lower() != "strict":
                        errors.append(f"Diagnostics.MissingIncludes should be 'Strict', got '{mi}'")

            if not errors:
                check2["passed"] = True
                check2["detail"] = "All required keys present with correct values"
            else:
                check2["detail"] = "; ".join(errors)
        except Exception as e:
            check2["detail"] = f"Parse error: {e}"
    else:
        check2["detail"] = ".clangd not found, skipping structure check"
    checks.append(check2)

    # ── CHECK 3: compile_commands.json exists ────────────────────────────
    ccj_candidates = list(project_dir.rglob("compile_commands.json"))
    check3 = {"name": "compile_commands.json exists", "passed": False, "detail": ""}
    if ccj_candidates:
        check3["passed"] = True
        check3["detail"] = f"Found at {ccj_candidates[0]}"
    else:
        check3["detail"] = "compile_commands.json not found anywhere in ecu_firmware/"
    checks.append(check3)

    # ── CHECK 4: compile_commands.json has valid structure ───────────────
    check4 = {"name": "compile_commands.json has valid entries", "passed": False, "detail": ""}
    if ccj_candidates:
        try:
            with open(ccj_candidates[0]) as f:
                ccj = json.load(f)
            if not isinstance(ccj, list) or len(ccj) == 0:
                check4["detail"] = "Must be a non-empty JSON array"
            else:
                required_keys = {"directory", "command", "file"}
                bad_entries = []
                has_cpp17 = False
                for i, entry in enumerate(ccj):
                    missing = required_keys - set(entry.keys())
                    if missing:
                        bad_entries.append(f"Entry {i} missing keys: {missing}")
                    cmd_str = entry.get("command", "") + " " + " ".join(entry.get("arguments", []))
                    if "c++17" in cmd_str or "cpp17" in cmd_str or "std=c++17" in cmd_str:
                        has_cpp17 = True
                if bad_entries:
                    check4["detail"] = "; ".join(bad_entries)
                elif not has_cpp17:
                    check4["detail"] = "No entry contains -std=c++17 in command"
                else:
                    check4["passed"] = True
                    check4["detail"] = f"{len(ccj)} valid entries with -std=c++17"
        except Exception as e:
            check4["detail"] = f"JSON parse error: {e}"
    else:
        check4["detail"] = "compile_commands.json not found, skipping"
    checks.append(check4)

    # ── CHECK 5: clang-format was applied (files are properly formatted) ──
    check5 = {"name": "C++ source/header files are clang-formatted", "passed": False, "detail": ""}
    cpp_files = (
        list((project_dir / "src").glob("*.cpp")) +
        list((project_dir / "include").glob("*.hpp"))
    )
    unformatted = []
    try:
        for fp in cpp_files:
            rc, stdout, stderr = run(
                f"clang-format --dry-run --Werror '{fp}'",
                cwd=str(project_dir)
            )
            if rc != 0:
                unformatted.append(fp.name)
        if not cpp_files:
            check5["detail"] = "No .cpp/.hpp files found to check"
        elif unformatted:
            check5["detail"] = f"Unformatted files: {unformatted}"
        else:
            check5["passed"] = True
            check5["detail"] = f"All {len(cpp_files)} checked files are properly formatted"
    except Exception as e:
        check5["detail"] = f"Error running clang-format check: {e}"
    checks.append(check5)

    # ── CHECK 6: project compiles successfully with -std=c++17 -Wall -Wextra
    check6 = {"name": "Project compiles with g++ -std=c++17 -Wall -Wextra", "passed": False, "detail": ""}
    try:
        src_dir = project_dir / "src"
        inc_dir = project_dir / "include"
        srcs = " ".join(
            str(p) for p in src_dir.glob("*.cpp")
        )
        compile_cmd = (
            f"g++ -std=c++17 -Wall -Wextra -I{inc_dir} {srcs} -o /tmp/ecu_firmware_test"
        )
        rc, stdout, stderr = run(compile_cmd, cwd=str(project_dir))
        if rc == 0:
            check6["passed"] = True
            check6["detail"] = "Compilation succeeded with no errors"
        else:
            check6["detail"] = f"Compilation failed (rc={rc}): {stderr[:500]}"
    except Exception as e:
        check6["detail"] = f"Exception during compilation: {e}"
    checks.append(check6)

    # ── CHECK 7: clang-tidy was run (evidence: clang-tidy can run on sources)
    # We verify clang-tidy can process the main source file without crashing
    # and that compile_commands.json is in a place clang-tidy can use it.
    check7 = {"name": "clang-tidy runs successfully on source files", "passed": False, "detail": ""}
    try:
        # Find compile_commands.json location for -p flag
        ccj_dir = str(ccj_candidates[0].parent) if ccj_candidates else str(project_dir)
        src_file = project_dir / "src" / "throttle_controller.cpp"
        inc_dir = project_dir / "include"
        tidy_cmd = (
            f"clang-tidy '{src_file}' -p '{ccj_dir}' -- "
            f"-std=c++17 -I{inc_dir}"
        )
        rc, stdout, stderr = run(tidy_cmd, cwd=str(project_dir))
        combined = (stdout + stderr).lower()
        # clang-tidy exits 0 or 1 (1 = warnings found, not crash)
        # A fatal crash or "error: no such file" indicates setup failure
        if "error: error reading" in combined or "fatal error" in combined.replace("note:", ""):
            check7["detail"] = f"clang-tidy encountered fatal errors: {(stdout+stderr)[:300]}"
        elif rc in (0, 1):
            check7["passed"] = True
            check7["detail"] = f"clang-tidy ran successfully (rc={rc})"
        else:
            check7["detail"] = f"clang-tidy exited with rc={rc}: {(stdout+stderr)[:300]}"
    except Exception as e:
        check7["detail"] = f"Exception: {e}"
    checks.append(check7)

    # ── SCORING ──────────────────────────────────────────────────────────
    weights = {
        ".clangd file exists": 0.10,
        ".clangd has correct CompileFlags and Diagnostics": 0.25,
        "compile_commands.json exists": 0.10,
        "compile_commands.json has valid entries": 0.15,
        "C++ source/header files are clang-formatted": 0.20,
        "Project compiles with g++ -std=c++17 -Wall -Wextra": 0.10,
        "clang-tidy runs successfully on source files": 0.10,
    }
    score = sum(weights[c["name"]] for c in checks if c["passed"])
    passed = score >= 0.75

    result = {
        "passed": passed,
        "score": round(score, 4),
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()