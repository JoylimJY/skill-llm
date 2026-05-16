import sys
import json
import re
from pathlib import Path
from datetime import date, datetime, timedelta

workspace = Path(sys.argv[1])

checks = []

def fail(name, detail):
    checks.append({"name": name, "passed": False, "detail": detail})

def ok(name, detail):
    checks.append({"name": name, "passed": True, "detail": detail})

# ── Locate the output file ────────────────────────────────────────────────────
candidates = list(workspace.rglob("seed_lot_audit.json"))
if not candidates:
    fail("file_exists", "seed_lot_audit.json not found anywhere in workspace")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

audit_path = candidates[0]
try:
    with open(audit_path) as f:
        audit = json.load(f)
    ok("file_exists", f"Found at {audit_path}")
except Exception as e:
    fail("file_exists", f"Found file but failed to parse JSON: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Check top-level structure ─────────────────────────────────────────────────
if not isinstance(audit, dict):
    fail("top_level_structure", "Root must be a JSON object/dict")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)
ok("top_level_structure", "Root is a JSON object")

# ── Locate lot entries ─────────────────────────────────────────────────────────
# Accept "lots", "lot_assessments", "assessments", or a list at root, etc.
lots = None
for key in ("lots", "lot_assessments", "assessments", "results", "seed_lots"):
    if key in audit and isinstance(audit[key], list):
        lots = audit[key]
        break
if lots is None and isinstance(audit.get("lots"), list):
    lots = audit["lots"]
# Fallback: check if audit itself is a list
if lots is None and isinstance(audit, list):
    lots = audit

if not lots or not isinstance(lots, list) or len(lots) < 3:
    fail("lot_entries", f"Expected a list of 3 lot assessments; got: {lots}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)
ok("lot_entries", f"Found {len(lots)} lot entries")

def find_lot(lot_id):
    for entry in lots:
        if isinstance(entry, dict):
            lid = str(entry.get("lot_id", "")).strip()
            if lid == lot_id:
                return entry
    return None

# ─────────────────────────────────────────────────────────────────────────────
# ISTA COMPLIANCE CHECK
# From testing command:
#   Min sample size = 400 seeds (4 replicates × 100 seeds)
#   Commercial threshold: Tomato=85%, Pepper=80%, Lettuce=80%
# ─────────────────────────────────────────────────────────────────────────────

ista_thresholds = {"tomato": 85, "lettuce": 80, "pepper": 80}
observed = {"L2024-010": ("tomato", 87), "L2024-011": ("lettuce", 76), "L2024-012": ("pepper", 82)}

# Expected compliance: tomato 87>=85 PASS, lettuce 76<80 FAIL, pepper 82>=80 PASS
expected_compliance = {
    "L2024-010": True,   # 87 >= 85
    "L2024-011": False,  # 76 < 80
    "L2024-012": True,   # 82 >= 80
}

compliance_score = 0
for lot_id, expected_pass in expected_compliance.items():
    crop, obs_pct = observed[lot_id]
    entry = find_lot(lot_id)
    if entry is None:
        fail(f"ista_compliance_{lot_id}", f"Lot {lot_id} not found in output")
        continue

    # Look for compliance field (flexible naming)
    comp_val = None
    for key in ("ista_compliant", "compliant", "passes_ista", "ista_pass", "meets_standard", "compliance"):
        if key in entry:
            comp_val = entry[key]
            break

    if comp_val is None:
        # Try to infer from a "status" field
        status_val = str(entry.get("status", "")).lower()
        if "pass" in status_val or "compliant" in status_val or "ok" in status_val:
            comp_val = True
        elif "fail" in status_val or "non" in status_val or "below" in status_val:
            comp_val = False

    if comp_val is None:
        fail(f"ista_compliance_{lot_id}", f"No compliance/status field found for {lot_id}; entry keys: {list(entry.keys())}")
        continue

    # Normalize to bool
    if isinstance(comp_val, str):
        comp_val = comp_val.lower() in ("true", "yes", "pass", "compliant", "1")
    else:
        comp_val = bool(comp_val)

    if comp_val == expected_pass:
        ok(f"ista_compliance_{lot_id}",
           f"{lot_id} ({crop}): {obs_pct}% vs threshold {ista_thresholds[crop]}% → {'PASS' if expected_pass else 'FAIL'} ✓")
        compliance_score += 1
    else:
        fail(f"ista_compliance_{lot_id}",
             f"{lot_id} ({crop}): {obs_pct}% vs threshold {ista_thresholds[crop]}% → expected {'PASS' if expected_pass else 'FAIL'}, got {'PASS' if comp_val else 'FAIL'}")

# ─────────────────────────────────────────────────────────────────────────────
# ISTA SAMPLE SIZE CHECK
# The testing command mandates: 400 seeds per lot (4 replicates × 100)
# The audit should reference this standard (400 seeds OR 4x100 structure)
# ─────────────────────────────────────────────────────────────────────────────
audit_str = json.dumps(audit).lower()
found_400 = "400" in audit_str
found_replicates = any(x in audit_str for x in ["4 replicates", "4x100", "4 × 100", "replicates", "replicate"])
if found_400 or found_replicates:
    ok("ista_sample_size", "ISTA 400-seed / 4-replicate standard referenced in output")
else:
    fail("ista_sample_size", "No reference to ISTA 400-seed sample size or 4 replicates found")

# ─────────────────────────────────────────────────────────────────────────────
# SOW DATE CALCULATION
# From schedule command:
#   Sow Date = Transplant Date − (Days to Germ midpoint + Seedling Growth midpoint + Hardening-off)
#
# Tomato: transplant 2024-04-20
#   daysToGerm midpoint = (5+10)/2 = 7.5 → round to 8 (or 7)
#   seedling growth midpoint = (35+42)/2 = 38.5 → 39 (or 38)
#   hardening = 7
#   total = ~54 days back from 2024-04-20 → around 2024-02-26 ± 3 days
#
# Lettuce: transplant 2024-03-30
#   daysToGerm midpoint = (2+8)/2 = 5
#   seedling growth midpoint = (21+28)/2 = 24.5 → 25 (or 24)
#   hardening = 4
#   total = ~34 days back from 2024-03-30 → around 2024-02-25 ± 3 days
#
# Pepper: transplant 2024-05-10
#   daysToGerm midpoint = (7+14)/2 = 10.5 → 11 (or 10)
#   seedling growth midpoint = (42+49)/2 = 45.5 → 46 (or 45)
#   hardening = 7
#   total = ~62 days back from 2024-05-10 → around 2024-03-09 ± 3 days

sow_date_params = {
    "L2024-010": {
        "crop": "tomato",
        "transplant": date(2024, 4, 20),
        "germ_mid": (5 + 10) / 2,
        "seedling_mid": (35 + 42) / 2,
        "hardening": 7,
    },
    "L2024-011": {
        "crop": "lettuce",
        "transplant": date(2024, 3, 30),
        "germ_mid": (2 + 8) / 2,
        "seedling_mid": (21 + 28) / 2,
        "hardening": 4,
    },
    "L2024-012": {
        "crop": "pepper",
        "transplant": date(2024, 5, 10),
        "germ_mid": (7 + 14) / 2,
        "seedling_mid": (42 + 49) / 2,
        "hardening": 7,
    },
}

sow_score = 0
for lot_id, params in sow_date_params.items():
    total_days = round(params["germ_mid"] + params["seedling_mid"] + params["hardening"])
    expected_sow = params["transplant"] - timedelta(days=total_days)

    entry = find_lot(lot_id)
    if entry is None:
        fail(f"sow_date_{lot_id}", f"Lot {lot_id} entry not found")
        continue

    sow_val = None
    for key in ("recommended_sow_date", "sow_date", "start_date", "seed_date", "sowing_date"):
        if key in entry:
            sow_val = entry[key]
            break

    if sow_val is None:
        fail(f"sow_date_{lot_id}", f"No sow_date / recommended_sow_date field in entry; keys={list(entry.keys())}")
        continue

    try:
        sow_parsed = datetime.strptime(str(sow_val).strip(), "%Y-%m-%d").date()
    except Exception:
        fail(f"sow_date_{lot_id}", f"Could not parse sow date '{sow_val}' as YYYY-MM-DD")
        continue

    diff = abs((sow_parsed - expected_sow).days)
    tolerance = 5  # allow ±5 days for rounding differences

    if diff <= tolerance:
        ok(f"sow_date_{lot_id}",
           f"{lot_id} ({params['crop']}): sow date {sow_parsed} within {tolerance}-day tolerance of expected {expected_sow} (diff={diff}d)")
        sow_score += 1
    else:
        fail(f"sow_date_{lot_id}",
             f"{lot_id} ({params['crop']}): sow date {sow_parsed} is {diff} days off from expected ~{expected_sow} (transplant={params['transplant']}, total_offset={total_days}d). Tolerance=±{tolerance}d")

# ─────────────────────────────────────────────────────────────────────────────
# CROP DATA ACCURACY CHECK (from crops command)
# Benchmark germination rates from crops command must be referenced/present
# ─────────────────────────────────────────────────────────────────────────────
bench_rates = {
    "tomato": ("85", "95"),
    "lettuce": ("80", "90"),
    "pepper": ("80", "90"),
}
bench_score = 0
for lot_id, (crop, (lo, hi)) in [("L2024-010", ("tomato", ("85", "95"))),
                                   ("L2024-011", ("lettuce", ("80", "90"))),
                                   ("L2024-012", ("pepper", ("80", "90")))]:
    entry = find_lot(lot_id)
    if entry is None:
        fail(f"bench_rate_{lot_id}", f"Lot {lot_id} not found")
        continue
    entry_str = json.dumps(entry).lower()
    # Look for benchmark rate range OR the individual numbers
    found = lo in entry_str or hi in entry_str or f"{lo}–{hi}" in entry_str or f"{lo}-{hi}" in entry_str
    if found:
        ok(f"bench_rate_{lot_id}", f"Benchmark rate for {crop} ({lo}–{hi}%) referenced in lot entry")
        bench_score += 1
    else:
        fail(f"bench_rate_{lot_id}", f"Benchmark germination rate for {crop} not found in lot entry (expected {lo}–{hi}%). Entry: {entry_str[:200]}")

# ─────────────────────────────────────────────────────────────────────────────
# FINAL SCORING
# ─────────────────────────────────────────────────────────────────────────────
total_checks = len(checks)
passed_checks = sum(1 for c in checks if c["passed"])

# Weighted scoring
# compliance (3 checks × 2pts) = 6
# sample_size (1 check × 1pt) = 1
# sow_dates (3 checks × 2pts) = 6
# bench_rates (3 checks × 1pt) = 3
# file+structure (2 checks × 1pt) = 2
# total possible = 18

weight_map = {
    "file_exists": 1, "top_level_structure": 1,
    "lot_entries": 1, "ista_sample_size": 1,
    "ista_compliance_L2024-010": 2, "ista_compliance_L2024-011": 2, "ista_compliance_L2024-012": 2,
    "sow_date_L2024-010": 2, "sow_date_L2024-011": 2, "sow_date_L2024-012": 2,
    "bench_rate_L2024-010": 1, "bench_rate_L2024-011": 1, "bench_rate_L2024-012": 1,
}
max_score = sum(weight_map.values())
earned = sum(weight_map.get(c["name"], 1) for c in checks if c["passed"])
score = round(earned / max_score, 3)

overall_passed = (
    checks[0]["passed"]  # file exists
    and compliance_score == 3
    and sow_score == 3
    and bench_score >= 2
)

print(json.dumps({
    "passed": overall_passed,
    "score": score,
    "checks": checks
}, indent=2))