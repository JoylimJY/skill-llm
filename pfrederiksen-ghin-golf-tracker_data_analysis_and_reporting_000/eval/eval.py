import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
score = 0.0

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── 1. Find the consolidated GHIN data file ──────────────────────────────────
ghin_data_file = None
candidates = list(Path(workspace).rglob("*.json"))
for c in candidates:
    try:
        with open(c) as f:
            d = json.load(f)
        # Must have the required top-level keys
        if all(k in d for k in ("handicap_index", "lifetime_rounds", "handicap_history", "scores")):
            ghin_data_file = c
            break
    except Exception:
        pass

if not add_check(
    "consolidated_ghin_file_exists",
    ghin_data_file is not None,
    f"Found consolidated GHIN data file at: {ghin_data_file}" if ghin_data_file else "No valid GHIN data JSON file with required keys found"
):
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── 2. Validate schema correctness ───────────────────────────────────────────
try:
    with open(ghin_data_file) as f:
        ghin_data = json.load(f)
except Exception as e:
    add_check("ghin_data_valid_json", False, str(e))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

add_check("ghin_data_valid_json", True, "Valid JSON")

# handicap_index should be 14.2
hi = ghin_data.get("handicap_index")
add_check(
    "correct_handicap_index",
    hi == 14.2,
    f"handicap_index={hi} (expected 14.2)"
)

# lifetime_rounds should be 57
lr = ghin_data.get("lifetime_rounds")
add_check(
    "correct_lifetime_rounds",
    lr == 57,
    f"lifetime_rounds={lr} (expected 57)"
)

# handicap_history must have correct key 'index' (not 'idx' or 'hcp')
hh = ghin_data.get("handicap_history", [])
hh_keys_ok = len(hh) >= 5 and all("date" in e and "index" in e for e in hh[:5])
add_check(
    "handicap_history_correct_schema",
    hh_keys_ok,
    f"handicap_history has {len(hh)} entries; key check on first 5: {hh_keys_ok}"
)

# scores must use "score" field with string format like "82A" or "83" (no letter required for non-adjusted)
# and cr_slope must be a single string like "71.2/128"
scores = ghin_data.get("scores", [])
score_field_ok = len(scores) >= 10
add_check(
    "scores_count_adequate",
    score_field_ok,
    f"scores has {len(scores)} entries (need >= 10)"
)

import re
cr_slope_ok = False
score_format_ok = False
if scores:
    # Check at least one score has cr_slope as a slash-separated string
    cr_slope_samples = [s.get("cr_slope","") for s in scores[:5]]
    cr_slope_ok = all(re.match(r'^\d+\.?\d*/\d+$', str(v)) for v in cr_slope_samples if v)
    # Check score field is a string (not int)
    score_vals = [s.get("score") for s in scores[:5]]
    score_format_ok = all(isinstance(v, str) for v in score_vals if v is not None)

add_check(
    "cr_slope_correct_format",
    cr_slope_ok,
    f"cr_slope samples: {[s.get('cr_slope') for s in scores[:3]]}"
)
add_check(
    "score_field_is_string",
    score_format_ok,
    f"score field samples: {[s.get('score') for s in scores[:3]]}"
)

# stats field with correct keys (par3_avg, par4_avg, par5_avg, gir_pct, fairways_pct, putts_avg)
stats = ghin_data.get("stats", {})
required_stat_keys = {"par3_avg", "par4_avg", "par5_avg", "gir_pct", "fairways_pct", "putts_avg"}
stats_keys_ok = required_stat_keys.issubset(set(stats.keys()))
add_check(
    "stats_field_correct_keys",
    stats_keys_ok,
    f"stats keys found: {list(stats.keys())}, required: {list(required_stat_keys)}"
)

# ── 3. Find the analysis output summary file ─────────────────────────────────
# The agent must run the script with --format json and save output
summary_file = None
for c in Path(workspace).rglob("*.json"):
    if c == ghin_data_file:
        continue
    try:
        with open(c) as f:
            d = json.load(f)
        if all(k in d for k in ("trend", "best_differentials", "yearly_breakdown")):
            summary_file = c
            break
    except Exception:
        pass

if not add_check(
    "json_analysis_output_exists",
    summary_file is not None,
    f"Found JSON analysis output at: {summary_file}" if summary_file else "No JSON analysis output file found (must contain 'trend', 'best_differentials', 'yearly_breakdown')"
):
    # partial score for just building the data file
    total_passed = sum(1 for c in checks if c["passed"])
    partial = total_passed / (len(checks) + 4)  # account for remaining checks
    print(json.dumps({"passed": False, "score": round(partial, 2), "checks": checks}))
    sys.exit(0)

# ── 4. Validate analysis output correctness ──────────────────────────────────
try:
    with open(summary_file) as f:
        analysis = json.load(f)
except Exception as e:
    add_check("analysis_output_valid_json", False, str(e))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

add_check("analysis_output_valid_json", True, "Valid JSON")

# Trend should be "improving" (index went from 15.9->15.6->15.1->14.8->14.2 = decreasing = improving)
trend = analysis.get("trend","")
add_check(
    "correct_trend_improving",
    trend == "improving",
    f"trend='{trend}' (expected 'improving')"
)

# Best differentials: should be sorted ascending, first must be <= 6.1
bds = analysis.get("best_differentials", [])
bds_ok = (
    len(bds) >= 3 and
    all("differential" in d for d in bds) and
    bds[0]["differential"] <= 6.1
)
add_check(
    "best_differentials_correct",
    bds_ok,
    f"best_differentials count={len(bds)}, first differential={bds[0]['differential'] if bds else 'N/A'}"
)

# Yearly breakdown: must have 2025 and 2024 entries
yb = analysis.get("yearly_breakdown", [])
years_present = {y["year"] for y in yb}
years_ok = "2025" in years_present and "2024" in years_present
add_check(
    "yearly_breakdown_has_2025_and_2024",
    years_ok,
    f"years found: {sorted(years_present)}"
)

# 2025 round count: should be 15 rounds (15 records from 2025)
rounds_2025 = next((y["rounds"] for y in yb if y["year"] == "2025"), None)
add_check(
    "correct_2025_round_count",
    rounds_2025 == 15,
    f"2025 rounds={rounds_2025} (expected 15)"
)

# 2024 round count: should be 12 rounds
rounds_2024 = next((y["rounds"] for y in yb if y["year"] == "2024"), None)
add_check(
    "correct_2024_round_count",
    rounds_2024 == 12,
    f"2024 rounds={rounds_2024} (expected 12)"
)

# ── 5. Also check for text report ────────────────────────────────────────────
text_report = None
for c in Path(workspace).rglob("*.txt"):
    try:
        content = c.read_text()
        if "GHIN Golf Statistics Report" in content and "YEARLY BREAKDOWN" in content:
            text_report = c
            break
    except Exception:
        pass

add_check(
    "text_report_exists",
    text_report is not None,
    f"Found text report at: {text_report}" if text_report else "No text report file found containing 'GHIN Golf Statistics Report' and 'YEARLY BREAKDOWN'"
)

if text_report:
    content = text_report.read_text()
    has_handicap = "14.2" in content
    has_trend = "Improving" in content or "improving" in content
    add_check(
        "text_report_correct_content",
        has_handicap and has_trend,
        f"handicap 14.2 present={has_handicap}, improving trend present={has_trend}"
    )

# ── Final scoring ─────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
final_score = round(passed_count / total, 2)
all_passed = passed_count == total

print(json.dumps({
    "passed": all_passed,
    "score": final_score,
    "checks": checks
}))