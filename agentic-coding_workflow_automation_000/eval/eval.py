import sys
import json
import os
import re
import subprocess
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
agentic_dir = os.path.expanduser("~/agentic-coding")

checks = []

# ────────────────────────────────────────────────────────────────────────────
# HELPER
# ────────────────────────────────────────────────────────────────────────────
def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return None

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ════════════════════════════════════════════════════════════════════════════
# BLOCK 1: THE BUG FIX — does the code actually work?
# ════════════════════════════════════════════════════════════════════════════

# 1a. shipping.py exists and contains fix for both bugs
shipping_path = Path(workspace) / "logistics/src/utils/shipping.py"
shipping_src = read_file(shipping_path)

if shipping_src is None:
    check("shipping.py exists", False, "File not found at expected path.")
    check("bug fix: integer division removed", False, "File missing.")
    check("bug fix: 'international' key present", False, "File missing.")
else:
    check("shipping.py exists", True, "File found.")
    # Bug 1: // replaced by /
    has_float_div = ("//" not in shipping_src.split("weight_cost")[1].split("\n")[0]) if "weight_cost" in shipping_src else False
    # More robust: look for the corrected expression
    float_div_fixed = bool(re.search(r'weight_kg\s*/\s*WEIGHT_RATE', shipping_src)) and "//" not in shipping_src
    check(
        "bug fix: integer division removed (// -> /)",
        float_div_fixed,
        f"Source around weight_cost: {[l for l in shipping_src.splitlines() if 'weight_cost' in l]}"
    )
    intl_key_fixed = "'international'" in shipping_src or '"international"' in shipping_src
    check(
        "bug fix: 'international' key in ZONE_SURCHARGES",
        intl_key_fixed,
        f"ZONE_SURCHARGES keys found: {re.findall(r\"'[^']+'\", shipping_src)}"
    )

# 1b. All tests pass after the fix
try:
    result = subprocess.run(
        ["python", "-m", "pytest", "logistics/tests/unit/test_shipping.py", "-v", "--tb=short"],
        capture_output=True, text=True, cwd=workspace, timeout=30
    )
    all_tests_pass = result.returncode == 0
    check(
        "all 4 unit tests pass after fix",
        all_tests_pass,
        f"STDOUT: {result.stdout[-800:]} STDERR: {result.stderr[-300:]}"
    )
except Exception as e:
    check("all 4 unit tests pass after fix", False, f"Exception running pytest: {e}")

# ════════════════════════════════════════════════════════════════════════════
# BLOCK 2: contracts.md — contract-first structure
# ════════════════════════════════════════════════════════════════════════════
contracts_path = os.path.join(agentic_dir, "contracts.md")
contracts_src = read_file(contracts_path)

if contracts_src is None:
    for section in ["Objective", "Acceptance", "Non-goals", "Constraints"]:
        check(f"contracts.md: '{section}' section present", False, "contracts.md not found.")
else:
    src_lower = contracts_src.lower()
    for section in ["objective", "acceptance", "non-goal", "constraint"]:
        found = section in src_lower
        check(
            f"contracts.md: '{section}' section present",
            found,
            f"Section '{section}' {'found' if found else 'MISSING'} in contracts.md"
        )
    # Objective must reference shipping or the bug fix in one sentence (not empty)
    has_substance = any(kw in src_lower for kw in ["shipping", "bug", "fix", "cost", "weight", "zone", "calculat"])
    check(
        "contracts.md: Objective references the task domain",
        has_substance,
        f"Objective substance check: keywords found={'yes' if has_substance else 'no'}"
    )

# ════════════════════════════════════════════════════════════════════════════
# BLOCK 3: evidence.md — PACT loop + before/after proof
# ════════════════════════════════════════════════════════════════════════════
evidence_path = os.path.join(agentic_dir, "evidence.md")
evidence_src = read_file(evidence_path)

if evidence_src is None:
    for label in ["P (Problem framing)", "A (Acceptance design)", "C (Change set)", "T (Trace and test)",
                  "failing evidence before fix", "passing evidence after fix"]:
        check(f"evidence.md: '{label}'", False, "evidence.md not found.")
else:
    ev_lower = evidence_src.lower()
    # PACT four phases
    pact_checks = [
        ("problem", "P (Problem framing) phase"),
        ("acceptance", "A (Acceptance design) phase"),
        ("change", "C (Change set) phase"),
        ("trace", "T (Trace and test) phase"),
    ]
    for kw, label in pact_checks:
        found = kw in ev_lower
        check(f"evidence.md: PACT phase '{label}' documented", found,
              f"Keyword '{kw}' {'found' if found else 'MISSING'} in evidence.md")

    # Must show FAILING condition (before)
    failure_words = ["fail", "error", "assert", "wrong", "incorrect", "before", "broken"]
    has_failure_evidence = any(w in ev_lower for w in failure_words)
    check(
        "evidence.md: failing condition captured (before-fix evidence)",
        has_failure_evidence,
        f"Failure evidence keywords present: {has_failure_evidence}"
    )
    # Must show PASSING condition (after)
    pass_words = ["pass", "fixed", "correct", "after", "green", "resolved", "7.99", "28.99", "14.49", "9.99"]
    has_pass_evidence = any(w in ev_lower for w in pass_words)
    check(
        "evidence.md: passing condition captured (after-fix evidence)",
        has_pass_evidence,
        f"Pass evidence keywords present: {has_pass_evidence}"
    )

# ════════════════════════════════════════════════════════════════════════════
# BLOCK 4: handoffs.md — delivery packet completeness
# ════════════════════════════════════════════════════════════════════════════
handoffs_path = os.path.join(agentic_dir, "handoffs.md")
handoffs_src = read_file(handoffs_path)

if handoffs_src is None:
    for label in ["what changed", "files touched", "validation", "risk/rollback"]:
        check(f"handoffs.md: '{label}' section present", False, "handoffs.md not found.")
else:
    hf_lower = handoffs_src.lower()
    handoff_sections = [
        (["what changed", "what was changed", "changes"], "what changed / why"),
        (["files touched", "blast radius", "files modified", "file touched"], "files touched / blast radius"),
        (["validation", "test run", "verified", "pytest"], "validation run / results"),
        (["rollback", "risk", "known risk"], "known risks / rollback path"),
    ]
    for kw_list, label in handoff_sections:
        found = any(kw in hf_lower for kw in kw_list)
        check(
            f"handoffs.md: '{label}' documented",
            found,
            f"Keywords {kw_list}: {'found' if found else 'MISSING'} in handoffs.md"
        )
    # Must reference the specific file changed
    file_ref = "shipping.py" in handoffs_src
    check(
        "handoffs.md: references 'shipping.py' as touched file",
        file_ref,
        f"'shipping.py' {'found' if file_ref else 'MISSING'} in handoffs.md"
    )

# ════════════════════════════════════════════════════════════════════════════
# SCORING
# ════════════════════════════════════════════════════════════════════════════
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall_passed = score >= 0.85  # Must pass ≥85% of checks

output = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(output, indent=2))