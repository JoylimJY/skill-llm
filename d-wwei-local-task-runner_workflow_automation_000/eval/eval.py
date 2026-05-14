import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── Locate the output file ───────────────────────────────────────────────────
candidates = list(Path(workspace).rglob("portfolio_stats.json"))

if not candidates:
    add_check("output_file_exists", False, "portfolio_stats.json not found anywhere in workspace")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

output_file = candidates[0]
add_check("output_file_exists", True, f"Found at {output_file}")

# ── Load JSON ────────────────────────────────────────────────────────────────
try:
    with open(output_file) as f:
        data = json.load(f)
    add_check("valid_json", True, "File parsed as valid JSON")
except Exception as e:
    add_check("valid_json", False, f"JSON parse error: {e}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

# ── Expected values (computed from the trade data with seed 42) ──────────────
# 
# Clean trades (skip blank lines, comment lines, duplicate headers):
# T001 BUY  AAPL 100 @ 150.00 comm=1.50   cost = 100*150 + 1.50 = 15001.50
# T002 SELL AAPL  50 @ 155.00 comm=0.75   proceeds = 50*155 - 0.75 = 7749.25
# T003 BUY  MSFT 200 @ 280.00 comm=2.00   cost = 200*280 + 2.00 = 56002.00
# T004 SELL MSFT 200 @ 295.00 comm=2.00   proceeds = 200*295 - 2.00 = 58998.00
# T005 BUY  JPM  300 @ 130.00 comm=3.00   cost = 300*130 + 3.00 = 39003.00
# T006 SELL JPM  150 @ 128.00 comm=1.50   proceeds = 150*128 - 1.50 = 19198.50
# T007 BUY  XOM  400 @ 60.00  comm=4.00   cost = 400*60 + 4.00 = 24004.00
# T008 SELL XOM  400 @ 63.50  comm=4.00   proceeds = 400*63.50 - 4.00 = 25396.00
# T009 BUY  AAPL  75 @ 152.00 comm=0      cost = 75*152 + 0 = 11400.00
# T010 SELL MSFT 100 @ 290.00 comm=1.00   proceeds = 100*290 - 1.00 = 28999.00
# T011 BUY  JPM  200 @ 135.00 comm=2.00   cost = 200*135 + 2.00 = 27002.00
# T012 SELL XOM  200 @ 65.00  comm=2.00   proceeds = 200*65 - 2.00 = 12998.00
#
# total_trades = 12
# buy_count  = 6  (T001,T003,T005,T007,T009,T011)
# sell_count = 6  (T002,T004,T006,T008,T010,T012)
# total_commission = 1.50+0.75+2.00+2.00+3.00+1.50+4.00+4.00+0+1.00+2.00+2.00 = 23.75
# total_buy_value  = 15001.50+56002.00+39003.00+24004.00+11400.00+27002.00 = 172412.50
# total_sell_value = 7749.25+58998.00+19198.50+25396.00+28999.00+12998.00 = 153338.75
# net_pnl = total_sell_value - total_buy_value = 153338.75 - 172412.50 = -19073.75
# return_pct = net_pnl / total_buy_value * 100 = -19073.75 / 172412.50 * 100 ≈ -11.0630...

EXPECTED = {
    "total_trades": 12,
    "buy_count": 6,
    "sell_count": 6,
    "total_commission": 23.75,
    "total_buy_value": 172412.50,
    "total_sell_value": 153338.75,
    "net_pnl": -19073.75,
    "return_pct": round(-19073.75 / 172412.50 * 100, 4),
}

TOLERANCE = 0.05  # allow ±0.05 for float rounding

def close_enough(actual, expected, tol=TOLERANCE):
    try:
        return abs(float(actual) - float(expected)) <= tol
    except Exception:
        return False

score_points = 0
total_points = len(EXPECTED)

for key, exp_val in EXPECTED.items():
    if key not in data:
        add_check(f"field_{key}", False, f"Missing field '{key}'")
        continue
    actual = data[key]
    if close_enough(actual, exp_val):
        add_check(f"field_{key}", True, f"Got {actual}, expected ~{exp_val}")
        score_points += 1
    else:
        add_check(f"field_{key}", False, f"Got {actual}, expected ~{exp_val} (tolerance ±{TOLERANCE})")

# ── Bonus: verify runner was used (check for TASK output in any log/tmp) ─────
# We look for evidence: the runner produces [TASK: XXXX] format.
# We search workspace for any file containing this pattern.
import re
runner_evidence = False
for p in Path(workspace).rglob("*"):
    if p.is_file() and p.suffix in (".log", ".txt", ".out", "") and p.stat().st_size < 100_000:
        try:
            content = p.read_text(errors="ignore")
            if re.search(r"\[TASK: [0-9A-F]+\]", content):
                runner_evidence = True
                break
        except Exception:
            pass

# Runner evidence is a bonus check (not required for pass, but good signal)
add_check(
    "runner_output_evidence",
    runner_evidence,
    "Found [TASK: XXXX] pattern in workspace logs" if runner_evidence else
    "No runner output evidence found (agent may not have used the local task runner)"
)

passed_checks = [c for c in checks if c["passed"]]
score = round(len(passed_checks) / (len(checks)) , 3)

# Must pass all EXPECTED fields to pass overall
core_checks_passed = all(
    c["passed"] for c in checks if c["name"].startswith("field_") or c["name"] in ("output_file_exists", "valid_json")
)

result = {
    "passed": core_checks_passed,
    "score": score,
    "checks": checks,
}
print(json.dumps(result))