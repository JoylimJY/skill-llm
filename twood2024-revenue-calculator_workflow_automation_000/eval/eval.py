import sys
import json
import math
from pathlib import Path

workspace = sys.argv[1]

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── Find the output file ────────────────────────────────────────────────────
candidates = list(Path(workspace).rglob("revenue_projection.md"))
if not candidates:
    check("output_file_exists", False, "revenue_projection.md not found anywhere in workspace.")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, indent=2))
    sys.exit(0)

report_path = candidates[0]
check("output_file_exists", True, f"Found at {report_path}")

try:
    content = report_path.read_text()
except Exception as e:
    check("output_file_readable", False, str(e))
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, indent=2))
    sys.exit(0)

check("output_file_readable", True, "File read successfully.")

# ── Expected values (computed with exact script formula) ───────────────────
# Parameters: strategy=2, users=250, price=29, conv=0.75, churn=0.08, costs=0.25
def calc(users, price=29, conv=0.75, churn=0.08, costs=0.25):
    monthly_gross = users * price * conv
    annual_gross = monthly_gross * 12
    annual_net = annual_gross * (1 - churn) * (1 - costs)
    break_even = round(price * conv * 12 * (1 - costs) / price, 0)
    return {
        "monthly_gross": round(monthly_gross, 2),
        "annual_gross": round(annual_gross, 2),
        "annual_net": round(annual_net, 2),
        "break_even_users": break_even,
    }

base = calc(250)        # users=250
low  = calc(200)        # users=250 * 0.80 = 200
high = calc(300)        # users=250 * 1.20 = 300

def number_present(text, value, tolerance=0.02):
    """Check if a number within tolerance% of value appears anywhere in text."""
    import re
    # Strip commas from text numbers
    cleaned = text.replace(",", "")
    found_floats = re.findall(r'\d+(?:\.\d+)?', cleaned)
    for token in found_floats:
        try:
            if abs(float(token) - value) / max(abs(value), 1) <= tolerance:
                return True
        except:
            pass
    return False

# ── Check 1: Base monthly gross ─────────────────────────────────────────────
# base monthly_gross = 250 * 29 * 0.75 = 5437.5
ok = number_present(content, base["monthly_gross"])
check(
    "base_monthly_gross_correct",
    ok,
    f"Expected ~{base['monthly_gross']} in report. Found: {ok}"
)

# ── Check 2: Base annual gross ───────────────────────────────────────────────
# annual_gross = 5437.5 * 12 = 65250.0
ok = number_present(content, base["annual_gross"])
check(
    "base_annual_gross_correct",
    ok,
    f"Expected ~{base['annual_gross']} in report. Found: {ok}"
)

# ── Check 3: Base annual net (proprietary chaining trap) ────────────────────
# annual_net = 65250 * (1-0.08) * (1-0.25) = 65250 * 0.92 * 0.75 = 45028.5
ok = number_present(content, base["annual_net"])
check(
    "base_annual_net_correct_formula",
    ok,
    f"Expected ~{base['annual_net']} (uses churn AND costs multiplicatively). Found: {ok}"
)

# ── Check 4: Low scenario (-20% users = 200) ────────────────────────────────
ok_mg = number_present(content, low["monthly_gross"])
ok_an = number_present(content, low["annual_net"])
ok = ok_mg or ok_an
check(
    "sensitivity_low_scenario",
    ok,
    f"Expected low-scenario values (~{low['monthly_gross']} monthly or ~{low['annual_net']} net). Found: {ok}"
)

# ── Check 5: High scenario (+20% users = 300) ───────────────────────────────
ok_mg = number_present(content, high["monthly_gross"])
ok_an = number_present(content, high["annual_net"])
ok = ok_mg or ok_an
check(
    "sensitivity_high_scenario",
    ok,
    f"Expected high-scenario values (~{high['monthly_gross']} monthly or ~{high['annual_net']} net). Found: {ok}"
)

# ── Check 6: Both sensitivity rows present (low AND high) ───────────────────
low_present  = number_present(content, low["monthly_gross"])  or number_present(content, low["annual_net"])
high_present = number_present(content, high["monthly_gross"]) or number_present(content, high["annual_net"])
ok = low_present and high_present
check(
    "both_sensitivity_scenarios_present",
    ok,
    f"Both ±20% scenarios must appear. Low present: {low_present}, High present: {high_present}"
)

# ── Check 7: Report uses markdown table structure ────────────────────────────
has_table = "|" in content and "---" in content
check(
    "markdown_table_present",
    has_table,
    "Report should contain at least one markdown table (| ... | ... |)."
)

# ── Check 8: Strategy 2 / Marketplace mentioned ─────────────────────────────
lower = content.lower()
ok = "marketplace" in lower or "strategy 2" in lower or "strategy: 2" in lower
check(
    "strategy_identified",
    ok,
    "Report should identify the Marketplace / Strategy 2 approach."
)

# ── Scoring ──────────────────────────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
score = round(len(passed_checks) / len(checks), 4)
overall = score >= 0.75  # must pass at least 6/8 checks

result = {
    "passed": overall,
    "score": score,
    "checks": checks,
}
print(json.dumps(result, indent=2))