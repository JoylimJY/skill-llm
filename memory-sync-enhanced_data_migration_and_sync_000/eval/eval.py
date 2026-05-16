#!/usr/bin/env python3
"""
Evaluation script for the memory-sync-enhanced audit task.
Expected output: /workspace/audit_report.json  (or anywhere in workspace, found via rglob)

The agent must:
1. Read STM JSONL records and compute Ebbinghaus decay scores:
   score = (use_count)^0.6 * exp(-ln(2)/3 * delta_t) * strength   [STM, half_life=3]
2. Read co-occurrence DB and compute effective_weight = weight * 2^(-age_days/30)
3. Apply co-occurrence boost to scores:
   boosted_score = base_score + sum(effective_weights for neighbours) * 0.3
4. Classify memories: gc (<0.1), danger (0.15-0.35), healthy (0.35-0.65), strong (>0.65)
5. Identify promoted memories: danger zone STM with use_count >= 10
6. Output audit_report.json with the correct structure and values.
"""
import sys
import json
import math
import sqlite3
from pathlib import Path
from datetime import datetime, date

WORKSPACE = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
TODAY = datetime(2026, 3, 1)
BETA = 0.6
STM_HALF_LIFE = 3
LTM_HALF_LIFE = 30
LAMBDA_STM = math.log(2) / STM_HALF_LIFE
CO_BOOST_FACTOR = 0.3
CO_HALF_LIFE_DAYS = 30
GC_THRESHOLD = 0.1
DANGER_LO, DANGER_HI = 0.15, 0.35
HEALTHY_LO, HEALTHY_HI = 0.35, 0.65

checks = []
total_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score
    if passed:
        total_score += weight

# ── helpers ───────────────────────────────────────────────────────────────────

def ebbinghaus_score(use_count, delta_t_days, strength, half_life=STM_HALF_LIFE):
    lam = math.log(2) / half_life
    return (use_count ** BETA) * math.exp(-lam * delta_t_days) * strength

def co_effective_weight(weight, age_days):
    return weight * (2 ** (-age_days / CO_HALF_LIFE_DAYS))

# ── Load ground truth STM ─────────────────────────────────────────────────────
stm_path = Path(WORKSPACE) / "memory" / "stm" / "records.jsonl"
stm_records = []
try:
    with open(stm_path) as f:
        for line in f:
            line = line.strip()
            if line:
                stm_records.append(json.loads(line))
except Exception as e:
    checks.append({"name": "load_stm", "passed": False, "detail": str(e)})
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Load co-occurrence DB ─────────────────────────────────────────────────────
db_path = Path(WORKSPACE) / "memory" / "graph" / "co_occurrence.db"
co_map = {}  # memory_id -> list of (neighbour, effective_weight)
try:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT memory_a, memory_b, weight, last_updated FROM co_occurrence")
    for ma, mb, w, lu in cur.fetchall():
        lu_date = datetime.strptime(lu, "%Y-%m-%d")
        age_days = (TODAY - lu_date).days
        ew = co_effective_weight(w, age_days)
        co_map.setdefault(ma, []).append((mb, ew))
        co_map.setdefault(mb, []).append((ma, ew))  # symmetric already in DB but deduplicate later
    conn.close()
except Exception as e:
    checks.append({"name": "load_co_db", "passed": False, "detail": str(e)})

# ── Compute expected scores ───────────────────────────────────────────────────
expected = {}
for rec in stm_records:
    rid = rec["id"]
    lu = datetime.strptime(rec["last_used"], "%Y-%m-%d")
    delta_t = (TODAY - lu).days
    base = ebbinghaus_score(rec["use_count"], delta_t, rec["strength"], STM_HALF_LIFE)
    # co-occurrence boost: sum of effective weights from direct neighbours
    neighbours = co_map.get(rid, [])
    # deduplicate (since we may have loaded both directions)
    seen = {}
    for nb, ew in neighbours:
        if nb not in seen or ew > seen[nb]:
            seen[nb] = ew
    co_boost_sum = sum(seen.values())
    boosted = base + co_boost_sum * CO_BOOST_FACTOR
    expected[rid] = {
        "base_score": round(base, 6),
        "co_boost_sum": round(co_boost_sum, 6),
        "boosted_score": round(boosted, 6),
        "delta_t": delta_t,
    }

# Classify
def classify(score):
    if score < GC_THRESHOLD:
        return "gc"
    elif score < DANGER_LO:
        return "below_danger"
    elif score <= DANGER_HI:
        return "danger"
    elif score <= HEALTHY_HI:
        return "healthy"
    else:
        return "strong"

expected_gc = sorted([r["id"] for r in stm_records
                       if classify(expected[r["id"]]["boosted_score"]) == "gc"])
expected_danger = sorted([r["id"] for r in stm_records
                           if classify(expected[r["id"]]["boosted_score"]) == "danger"])
# Promoted: danger zone AND use_count >= 10
expected_promoted = sorted([r["id"] for r in stm_records
                             if classify(expected[r["id"]]["boosted_score"]) == "danger"
                             and r["use_count"] >= 10])

# ── Find audit_report.json ────────────────────────────────────────────────────
report_files = list(Path(WORKSPACE).rglob("audit_report.json"))

if not report_files:
    checks.append({"name": "report_exists", "passed": False, "detail": "audit_report.json not found anywhere in workspace"})
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

checks.append({"name": "report_exists", "passed": True, "detail": f"Found at {report_files[0]}"})
add_check("report_exists_score", True, "", 0.5)

try:
    with open(report_files[0]) as f:
        report = json.load(f)
except Exception as e:
    checks.append({"name": "report_parseable", "passed": False, "detail": str(e)})
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

checks.append({"name": "report_parseable", "passed": True, "detail": "Valid JSON"})

# ── Check 1: GC list ──────────────────────────────────────────────────────────
try:
    reported_gc = sorted(report.get("gc_candidates", []))
    gc_match = set(reported_gc) == set(expected_gc)
    add_check(
        "gc_candidates_correct", gc_match,
        f"Expected gc={expected_gc}, got={reported_gc}",
        weight=2.0
    )
except Exception as e:
    add_check("gc_candidates_correct", False, str(e), weight=2.0)

# ── Check 2: Danger zone list ─────────────────────────────────────────────────
try:
    reported_danger = sorted(report.get("danger_zone", []))
    danger_match = set(reported_danger) == set(expected_danger)
    add_check(
        "danger_zone_correct", danger_match,
        f"Expected danger={expected_danger}, got={reported_danger}",
        weight=2.0
    )
except Exception as e:
    add_check("danger_zone_correct", False, str(e), weight=2.0)

# ── Check 3: Promoted list ────────────────────────────────────────────────────
try:
    reported_promoted = sorted(report.get("promoted_to_ltm", []))
    promo_match = set(reported_promoted) == set(expected_promoted)
    add_check(
        "promoted_to_ltm_correct", promo_match,
        f"Expected promoted={expected_promoted}, got={reported_promoted}",
        weight=2.0
    )
except Exception as e:
    add_check("promoted_to_ltm_correct", False, str(e), weight=2.0)

# ── Check 4: Individual score spot-checks with tolerance ─────────────────────
SCORE_TOLERANCE = 0.02  # allow 2% relative error or absolute 0.01
score_checks = ["stm-gc-001", "stm-dp-001", "stm-h-001"]
score_check_passed = 0
score_details = []
for sid in score_checks:
    try:
        reported_scores = report.get("scores", {})
        if isinstance(reported_scores, list):
            # agent may have used a list of objects
            r_score = None
            for item in reported_scores:
                if isinstance(item, dict) and item.get("id") == sid:
                    r_score = item.get("boosted_score", item.get("final_score", item.get("score")))
                    break
        else:
            entry = reported_scores.get(sid, {})
            if isinstance(entry, dict):
                r_score = entry.get("boosted_score", entry.get("final_score", entry.get("score")))
            else:
                r_score = entry

        exp_score = expected[sid]["boosted_score"]
        if r_score is None:
            score_details.append(f"{sid}: not found in report scores")
        else:
            r_score = float(r_score)
            rel_err = abs(r_score - exp_score) / max(abs(exp_score), 1e-9)
            abs_err = abs(r_score - exp_score)
            ok = rel_err < 0.05 or abs_err < 0.01
            if ok:
                score_check_passed += 1
            score_details.append(f"{sid}: expected={exp_score:.5f}, got={r_score:.5f}, rel_err={rel_err:.3f}")
    except Exception as e:
        score_details.append(f"{sid}: error {e}")

spot_ok = score_check_passed >= 2
add_check(
    "score_spot_checks",
    spot_ok,
    "; ".join(score_details),
    weight=2.0
)

# ── Check 5: Beta=0.6 discriminator ──────────────────────────────────────────
# Verify that the agent did NOT use beta=0.5 or beta=1.0 for stm-gc-002
try:
    sid = "stm-gc-002"
    rec = next(r for r in stm_records if r["id"] == sid)
    lu = datetime.strptime(rec["last_used"], "%Y-%m-%d")
    delta_t = (TODAY - lu).days
    # wrong betas
    score_b05 = (rec["use_count"] ** 0.5) * math.exp(-math.log(2)/3 * delta_t) * rec["strength"]
    score_b10 = (rec["use_count"] ** 1.0) * math.exp(-math.log(2)/3 * delta_t) * rec["strength"]
    score_correct = expected[sid]["boosted_score"]

    reported_scores = report.get("scores", {})
    r_score = None
    if isinstance(reported_scores, dict):
        entry = reported_scores.get(sid, {})
        if isinstance(entry, dict):
            r_score = entry.get("boosted_score", entry.get("final_score", entry.get("score")))
        else:
            r_score = entry
    elif isinstance(reported_scores, list):
        for item in reported_scores:
            if isinstance(item, dict) and item.get("id") == sid:
                r_score = item.get("boosted_score", item.get("final_score", item.get("score")))
                break

    if r_score is not None:
        r_score = float(r_score)
        used_correct_beta = abs(r_score - score_correct) < 0.02 or abs(r_score - score_correct) / max(score_correct, 1e-9) < 0.05
        used_wrong_b05 = abs(r_score - score_b05) < 0.02
        used_wrong_b10 = abs(r_score - score_b10) < 0.02
        detail = f"correct_beta_score={score_correct:.5f}, reported={r_score:.5f}, b0.5={score_b05:.5f}, b1.0={score_b10:.5f}"
        add_check("correct_beta_0_6_used", used_correct_beta and not (used_wrong_b05 or used_wrong_b10),
                  detail, weight=1.5)
    else:
        add_check("correct_beta_0_6_used", False, f"{sid} not in scores", weight=1.5)
except Exception as e:
    add_check("correct_beta_0_6_used", False, str(e), weight=1.5)

# ── Check 6: Hebbian effective_weight formula discriminator ───────────────────
# stm-gc-001 ↔ stm-gc-002 edge: weight=1.0, age=40 days
# correct effective_weight = 1.0 * 2^(-40/30) = 0.3969...
# wrong (linear): 1.0 * (1 - 40/30) = negative (or just 40/30)
try:
    ew_correct = 1.0 * (2 ** (-40 / 30))  # ~0.3969
    reported_ew = report.get("co_occurrence_effective_weights", {})
    # accept either direction key
    ew_val = None
    for key in ["stm-gc-001->stm-gc-002", "stm-gc-002->stm-gc-001",
                "stm-gc-001_stm-gc-002", "stm-gc-002_stm-gc-001"]:
        if key in reported_ew:
            ew_val = float(reported_ew[key])
            break
    if ew_val is None and isinstance(reported_ew, dict):
        # try nested
        for k, v in reported_ew.items():
            if "gc-001" in k or "gc-002" in k:
                ew_val = float(v) if not isinstance(v, dict) else float(list(v.values())[0])
                break

    if ew_val is not None:
        ok = abs(ew_val - ew_correct) / max(ew_correct, 1e-9) < 0.05
        add_check("hebbian_effective_weight_formula",
                  ok,
                  f"expected={ew_correct:.5f}, got={ew_val:.5f}",
                  weight=1.5)
    else:
        add_check("hebbian_effective_weight_formula", False,
                  f"co_occurrence_effective_weights key not found or edge not present; correct ew={ew_correct:.5f}",
                  weight=1.5)
except Exception as e:
    add_check("hebbian_effective_weight_formula", False, str(e), weight=1.5)

# ── Check 7: Statistics block ─────────────────────────────────────────────────
try:
    stats = report.get("statistics", {})
    total_stm = sum(1 for r in stm_records)
    reported_total = stats.get("total_stm_records", stats.get("total_records"))
    total_ok = reported_total is not None and int(reported_total) == total_stm
    gc_count_ok = stats.get("gc_count", stats.get("gc_candidates_count")) == len(expected_gc)
    danger_count_ok = stats.get("danger_count", stats.get("danger_zone_count")) == len(expected_danger)
    stats_ok = total_ok and gc_count_ok and danger_count_ok
    add_check("statistics_block",
              stats_ok,
              f"total_stm={total_stm}({reported_total}), gc={len(expected_gc)}({stats.get('gc_count')}), danger={len(expected_danger)}({stats.get('danger_count')})",
              weight=1.0)
except Exception as e:
    add_check("statistics_block", False, str(e), weight=1.0)

# ── Final result ──────────────────────────────────────────────────────────────
max_score = 0.5 + 2.0 + 2.0 + 2.0 + 2.0 + 1.5 + 1.5 + 1.0  # = 12.5
normalized = total_score / max_score
passed = normalized >= 0.65

print(json.dumps({
    "passed": passed,
    "score": round(normalized, 4),
    "checks": checks,
    "debug": {
        "expected_gc": expected_gc,
        "expected_danger": expected_danger,
        "expected_promoted": expected_promoted,
        "sample_scores": {k: v for k, v in list(expected.items())[:5]}
    }
}, ensure_ascii=False, indent=2))