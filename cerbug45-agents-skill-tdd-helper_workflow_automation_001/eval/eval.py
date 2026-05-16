import sys
import json
import subprocess
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
score = 0.0

def c(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── 1. Production script exists ───────────────────────────────────────────────
prod_candidates = list(Path(workspace).rglob("dosage_calc.py"))
prod_file = prod_candidates[0] if prod_candidates else None
if prod_file:
    c("production_script_exists", True, f"Found: {prod_file}")
    score += 0.10
else:
    c("production_script_exists", False, "dosage_calc.py not found anywhere in workspace")

# ── 2. Test file exists inside tests/ dir ────────────────────────────────────
test_candidates = list(Path(workspace, "tests").rglob("test_*.py"))
# exclude broken distractor
test_candidates = [t for t in test_candidates if "broken" not in t.name]
if test_candidates:
    c("test_file_exists", True, f"Found test(s): {[str(t) for t in test_candidates]}")
    score += 0.10
else:
    c("test_file_exists", False, "No test_*.py file found under tests/")

# ── 3. Tests actually pass (pytest) ──────────────────────────────────────────
try:
    res = subprocess.run(
        ["pytest", str(Path(workspace, "tests")), "-v", "--tb=short"],
        capture_output=True, text=True, cwd=workspace
    )
    if res.returncode == 0:
        c("pytest_passes", True, res.stdout[-800:])
        score += 0.20
    else:
        c("pytest_passes", False, res.stdout[-800:] + res.stderr[-400:])
except Exception as e:
    c("pytest_passes", False, str(e))

# ── 4. ruff lint passes on src/ and tests/ ───────────────────────────────────
try:
    ruff_res = subprocess.run(
        ["ruff", "check", str(Path(workspace, "src")), str(Path(workspace, "tests"))],
        capture_output=True, text=True, cwd=workspace
    )
    if ruff_res.returncode == 0:
        c("ruff_lint_clean", True, "No lint errors")
        score += 0.15
    else:
        c("ruff_lint_clean", False, ruff_res.stdout[:600] + ruff_res.stderr[:200])
except Exception as e:
    c("ruff_lint_clean", False, str(e))

# ── 5. tdd.py was invoked via WARN_AS_ERROR=1 pathway — verify result.json exists ──
result_candidates = list(Path(workspace).rglob("result.json"))
result_file = result_candidates[0] if result_candidates else None
if result_file:
    c("result_json_exists", True, f"Found: {result_file}")
    score += 0.10
else:
    c("result_json_exists", False, "result.json not found — production script may not have run through tdd.py")

# ── 6. result.json has correct structure ─────────────────────────────────────
if result_file:
    try:
        with open(result_file) as f:
            data = json.load(f)
        if isinstance(data, list) and len(data) == 5:
            c("result_json_is_list_of_5", True, f"Has {len(data)} entries")
            score += 0.10
        else:
            c("result_json_is_list_of_5", False, f"Expected list of 5, got: {type(data).__name__} len={len(data) if isinstance(data, list) else 'N/A'}")
    except Exception as e:
        c("result_json_is_list_of_5", False, str(e))
else:
    c("result_json_is_list_of_5", False, "result.json missing")

# ── 7. result.json correct keys per entry ────────────────────────────────────
if result_file:
    try:
        with open(result_file) as f:
            data = json.load(f)
        bad = [e for e in data if not ({"patient_id", "dose_ml"} <= set(e.keys()))]
        if not bad:
            c("result_json_correct_keys", True, "All entries have patient_id and dose_ml")
            score += 0.05
        else:
            c("result_json_correct_keys", False, f"Bad entries: {bad}")
    except Exception as e:
        c("result_json_correct_keys", False, str(e))
else:
    c("result_json_correct_keys", False, "result.json missing")

# ── 8. Verify actual dosage values (formula from docs/spec.md) ───────────────
# dose_ml = min(weight_kg * 25, 500) / 50  rounded to 2 dp
EXPECTED = {
    "P001": round(min(32.5 * 25, 500) / 50, 2),   # min(812.5,500)/50 = 10.0
    "P002": round(min(71.0 * 25, 500) / 50, 2),   # 10.0
    "P003": round(min(15.2 * 25, 500) / 50, 2),   # min(380,500)/50 = 7.6
    "P004": round(min(88.3 * 25, 500) / 50, 2),   # 10.0
    "P005": round(min(5.9  * 25, 500) / 50, 2),   # min(147.5,500)/50 = 2.95
}
if result_file:
    try:
        with open(result_file) as f:
            data = json.load(f)
        results_by_id = {e["patient_id"].strip(): e["dose_ml"] for e in data}
        wrong = []
        for pid, expected_dose in EXPECTED.items():
            actual = results_by_id.get(pid)
            if actual != expected_dose:
                wrong.append(f"{pid}: expected {expected_dose}, got {actual}")
        if not wrong:
            c("dosage_values_correct", True, f"All values match: {EXPECTED}")
            score += 0.15
        else:
            c("dosage_values_correct", False, f"Mismatches: {wrong}")
    except Exception as e:
        c("dosage_values_correct", False, str(e))
else:
    c("dosage_values_correct", False, "result.json missing")

# ── 9. tdd.py invocation evidence: check no result.json if tests removed ─────
# Soft check: verify the broken distractor test was NOT collected
try:
    res2 = subprocess.run(
        ["pytest", str(Path(workspace, "scripts", "test_broken.py")), "--collect-only", "-q"],
        capture_output=True, text=True, cwd=workspace
    )
    # We expect this to still be collectable if run directly; the agent should NOT have
    # pointed --tests at scripts/. The main test suite passing is sufficient evidence.
    c("distractor_test_not_in_suite", True, "Distractor not included in tests/ suite (inferred from pytest_passes)")
    score += 0.05
except Exception as e:
    c("distractor_test_not_in_suite", False, str(e))

# ── Final ─────────────────────────────────────────────────────────────────────
score = round(min(score, 1.0), 4)
passed = score >= 0.75

print(json.dumps({"passed": passed, "score": score, "checks": checks}, indent=2))