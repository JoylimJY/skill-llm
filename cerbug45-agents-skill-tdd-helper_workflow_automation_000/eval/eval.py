import sys
import json
import csv
import subprocess
import os
from pathlib import Path

workspace = sys.argv[1]
checks = []

def check(name, passed, detail=""):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── 1. tests/ directory has at least one real test file ──────────────────────
try:
    test_files = [
        p for p in Path(workspace, "tests").rglob("test_*.py")
        if p.stat().st_size > 0
    ]
    has_tests = len(test_files) > 0
    check("tests_directory_has_test_files", has_tests,
          f"Found {len(test_files)} test file(s): {[str(t) for t in test_files]}")
except Exception as e:
    check("tests_directory_has_test_files", False, str(e))

# ── 2. pytest passes ─────────────────────────────────────────────────────────
try:
    res = subprocess.run(
        ["python", "-m", "pytest", str(Path(workspace, "tests")), "-v", "--tb=short"],
        capture_output=True, text=True, cwd=workspace
    )
    pytest_passed = res.returncode == 0
    check("pytest_passes", pytest_passed,
          (res.stdout + res.stderr)[-800:])
except Exception as e:
    check("pytest_passes", False, str(e))

# ── 3. ruff lint passes (WARN_AS_ERROR gate) ─────────────────────────────────
try:
    # Only lint the production script(s) — exclude tdd.py and deprecated/
    # We run ruff on the whole workspace as tdd.py would, excluding known-bad distractor
    env = os.environ.copy()
    env["WARN_AS_ERROR"] = "1"
    ruff_res = subprocess.run(
        ["ruff", "check", "."],
        capture_output=True, text=True, cwd=workspace
    )
    ruff_passed = ruff_res.returncode == 0
    check("ruff_lint_passes", ruff_passed,
          (ruff_res.stdout + ruff_res.stderr)[-600:])
except Exception as e:
    check("ruff_lint_passes", False, str(e))

# ── 4. Output CSV exists ──────────────────────────────────────────────────────
csv_paths = list(Path(workspace).rglob("gc_results.csv"))
csv_found = len(csv_paths) > 0
check("gc_results_csv_exists", csv_found,
      f"Found at: {csv_paths[0]}" if csv_found else "gc_results.csv not found anywhere in workspace")

# ── 5. CSV has correct header ─────────────────────────────────────────────────
if csv_found:
    try:
        with open(csv_paths[0], newline="") as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames or []
            has_header = "sequence_id" in fieldnames and "gc_content" in fieldnames
            check("csv_has_correct_header", has_header,
                  f"Fieldnames found: {fieldnames}")
    except Exception as e:
        check("csv_has_correct_header", False, str(e))
else:
    check("csv_has_correct_header", False, "CSV not found")

# ── 6. CSV has correct GC values for all 5 sequences ─────────────────────────
# Expected GC% (rounded to 2 decimal places):
# seq_alpha: ATGCGCATTAGCGCGCTATTTACGCGCGATATCGCG => G+C count / total
# Let's compute expected values:
def gc_pct(seq):
    seq = seq.upper()
    gc = sum(1 for b in seq if b in "GC")
    return round(gc / len(seq) * 100, 2) if seq else 0.0

expected = {
    "seq_alpha":   gc_pct("ATGCGCATTAGCGCGCTATTTACGCGCGATATCGCG"),
    "seq_beta":    gc_pct("atgcatgcATGCATGCatgcATGC"),
    "seq_gamma":   gc_pct("AAAATTTTCCCCGGGG"),
    "seq_delta":   gc_pct("GCGCGCGCGCGCGCGCGCGC"),
    "seq_epsilon": gc_pct("ATATATAT"),
}

if csv_found:
    try:
        with open(csv_paths[0], newline="") as fh:
            reader = csv.DictReader(fh)
            rows = {row["sequence_id"]: row["gc_content"] for row in reader}

        all_correct = True
        details = []
        for seq_id, exp_val in expected.items():
            if seq_id not in rows:
                all_correct = False
                details.append(f"MISSING: {seq_id}")
                continue
            try:
                got = round(float(rows[seq_id]), 2)
            except ValueError:
                all_correct = False
                details.append(f"NON-NUMERIC for {seq_id}: {rows[seq_id]!r}")
                continue
            if abs(got - exp_val) > 0.05:
                all_correct = False
                details.append(f"{seq_id}: expected {exp_val}, got {got}")
            else:
                details.append(f"{seq_id}: OK ({got})")

        check("csv_gc_values_correct", all_correct, "; ".join(details))
    except Exception as e:
        check("csv_gc_values_correct", False, str(e))
else:
    check("csv_gc_values_correct", False, "CSV not found")

# ── 7. tdd.py was used as the execution gate (evidence check) ────────────────
# We verify by re-running tdd.py with WARN_AS_ERROR=1 and confirming it exits 0
try:
    # Find the production script that generates the CSV
    prod_candidates = list(Path(workspace).rglob("gc_pipeline.py")) + \
                      list(Path(workspace).rglob("calculate_gc.py")) + \
                      list(Path(workspace).rglob("main.py"))
    prod_candidates = [p for p in prod_candidates
                       if "deprecated" not in str(p) and "archive" not in str(p)
                       and "test_" not in p.name]

    if prod_candidates:
        prod_script = prod_candidates[0]
        env = os.environ.copy()
        env["WARN_AS_ERROR"] = "1"
        tdd_res = subprocess.run(
            ["python", "tdd.py", "--tests", "tests",
             "--run", f"python {prod_script.relative_to(workspace)}"],
            capture_output=True, text=True, cwd=workspace, env=env
        )
        tdd_used = tdd_res.returncode == 0
        check("tdd_py_gate_passes_end_to_end", tdd_used,
              (tdd_res.stdout + tdd_res.stderr)[-800:])
    else:
        check("tdd_py_gate_passes_end_to_end", False,
              "Could not find a non-deprecated production script to verify tdd.py gate")
except Exception as e:
    check("tdd_py_gate_passes_end_to_end", False, str(e))

# ── Final scoring ─────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
final_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": final_passed,
    "score": score,
    "checks": checks
}, indent=2))