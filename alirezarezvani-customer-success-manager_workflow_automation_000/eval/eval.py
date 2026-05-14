#!/usr/bin/env python3
"""Evaluation script for customer-success-manager pipeline task."""
import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    with open(path, "r") as f:
        return json.load(f)

def find_file(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    if not matches:
        return None
    # Prefer the most recently created/modified
    return str(sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0])

def run_checks(workspace):
    checks = []
    workspace = str(workspace)

    # ── Locate the output file ────────────────────────────────────────────────
    target = find_file(workspace, "portfolio_analysis.json")
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    if not target:
        add_check("output_file_exists", False, "portfolio_analysis.json not found anywhere in workspace")
        return checks, False

    add_check("output_file_exists", True, f"Found at {target}")

    try:
        data = load_json_file(target)
    except Exception as e:
        add_check("output_file_valid_json", False, f"JSON parse error: {e}")
        return checks, False

    add_check("output_file_valid_json", True, "Valid JSON")

    # ── Check top-level keys representing all three pipeline outputs ──────────
    has_health = any(k in data for k in ["health_scores", "health", "customers_health"])
    has_churn  = any(k in data for k in ["churn_risks", "churn", "risk_analysis", "churn_risk"])
    has_expansion = any(k in data for k in ["expansion_opportunities", "expansion", "expansion_analysis"])

    add_check("contains_health_data",
              has_health,
              "health_scores key found" if has_health else "Missing health_scores/health data section")
    add_check("contains_churn_data",
              has_churn,
              "churn_risks key found" if has_churn else "Missing churn_risks/churn data section")
    add_check("contains_expansion_data",
              has_expansion,
              "expansion_opportunities key found" if has_expansion else "Missing expansion data section")

    if not (has_health and has_churn and has_expansion):
        return checks, False

    # ── Extract customer records from health section ──────────────────────────
    health_key = next(k for k in ["health_scores", "health", "customers_health"] if k in data)
    churn_key  = next(k for k in ["churn_risks", "churn", "risk_analysis", "churn_risk"] if k in data)
    exp_key    = next(k for k in ["expansion_opportunities", "expansion", "expansion_analysis"] if k in data)

    health_records = data[health_key]
    churn_records  = data[churn_key]
    exp_records    = data[exp_key]

    # Handle both list and dict wrapping
    if isinstance(health_records, dict):
        health_records = list(health_records.values())
    if isinstance(churn_records, dict):
        churn_records = list(churn_records.values())
    if isinstance(exp_records, dict):
        exp_records = list(exp_records.values())

    # ── Check all 4 customers present in each section ────────────────────────
    expected_ids = {"C-ENT-001", "C-MM-002", "C-ENT-003", "C-SMB-004"}

    def get_ids(records):
        return {r.get("customer_id") for r in records if isinstance(r, dict)}

    health_ids = get_ids(health_records)
    churn_ids  = get_ids(churn_records)
    exp_ids    = get_ids(exp_records)

    add_check("all_4_customers_in_health",
              expected_ids == health_ids,
              f"Health IDs: {health_ids}")
    add_check("all_4_customers_in_churn",
              expected_ids == churn_ids,
              f"Churn IDs: {churn_ids}")
    add_check("all_4_customers_in_expansion",
              expected_ids == exp_ids,
              f"Expansion IDs: {exp_ids}")

    # ── Health score classification checks (proprietary thresholds) ───────────
    # Build lookup by customer_id
    health_by_id = {r["customer_id"]: r for r in health_records if isinstance(r, dict) and "customer_id" in r}

    # C-ENT-001: score ~75+, should be Green and trend improving (prev=70)
    c001 = health_by_id.get("C-ENT-001", {})
    c001_score = c001.get("health_score", 0)
    c001_status = c001.get("status", "")
    c001_green = c001_status == "Green" and c001_score >= 75
    add_check("C-ENT-001_health_green_and_improving",
              c001_green and c001.get("trend") == "improving",
              f"score={c001_score}, status={c001_status}, trend={c001.get('trend')}")

    # C-MM-002: should be Yellow (50-74 range) and declining (prev=68)
    c002 = health_by_id.get("C-MM-002", {})
    c002_score = c002.get("health_score", 0)
    c002_status = c002.get("status", "")
    c002_yellow = c002_status == "Yellow" and 50 <= c002_score < 75
    add_check("C-MM-002_health_yellow_declining",
              c002_yellow and c002.get("trend") == "declining",
              f"score={c002_score}, status={c002_status}, trend={c002.get('trend')}")

    # C-ENT-003: should be Green (strong), stable or improving
    c003 = health_by_id.get("C-ENT-003", {})
    c003_score = c003.get("health_score", 0)
    c003_status = c003.get("status", "")
    c003_green = c003_status == "Green" and c003_score >= 75
    add_check("C-ENT-003_health_green",
              c003_green,
              f"score={c003_score}, status={c003_status}")

    # C-SMB-004: should be Red (0-49)
    c004 = health_by_id.get("C-SMB-004", {})
    c004_score = c004.get("health_score", 0)
    c004_status = c004.get("status", "")
    c004_red = c004_status == "Red" and c004_score < 50
    add_check("C-SMB-004_health_red",
              c004_red,
              f"score={c004_score}, status={c004_status}")

    # ── Churn risk tier checks (proprietary tiers) ────────────────────────────
    churn_by_id = {r["customer_id"]: r for r in churn_records if isinstance(r, dict) and "customer_id" in r}

    # C-ENT-001: Medium risk (40-59 range)
    r001 = churn_by_id.get("C-ENT-001", {})
    r001_tier = r001.get("risk_tier", "")
    r001_score = r001.get("risk_score", -1)
    add_check("C-ENT-001_churn_medium",
              r001_tier == "Medium" and 40 <= r001_score < 60,
              f"risk_score={r001_score}, risk_tier={r001_tier}")

    # C-MM-002: High risk (60-79) — champion left, pricing complaint, meeting cancellations
    r002 = churn_by_id.get("C-MM-002", {})
    r002_tier = r002.get("risk_tier", "")
    r002_score = r002.get("risk_score", -1)
    add_check("C-MM-002_churn_high_or_critical",
              r002_tier in ("High", "Critical") and r002_score >= 60,
              f"risk_score={r002_score}, risk_tier={r002_tier}")

    # C-ENT-003: Low risk
    r003 = churn_by_id.get("C-ENT-003", {})
    r003_tier = r003.get("risk_tier", "")
    r003_score = r003.get("risk_score", -1)
    add_check("C-ENT-003_churn_low",
              r003_tier == "Low" and r003_score < 40,
              f"risk_score={r003_score}, risk_tier={r003_tier}")

    # C-SMB-004: Critical risk (80-100)
    r004 = churn_by_id.get("C-SMB-004", {})
    r004_tier = r004.get("risk_tier", "")
    r004_score = r004.get("risk_score", -1)
    add_check("C-SMB-004_churn_critical",
              r004_tier == "Critical" and r004_score >= 80,
              f"risk_score={r004_score}, risk_tier={r004_tier}")

    # ── Expansion priority checks ─────────────────────────────────────────────
    exp_by_id = {r["customer_id"]: r for r in exp_records if isinstance(r, dict) and "customer_id" in r}

    # C-ENT-003: High priority (high ARR, upsell available, dept expansion, seat expansion)
    e003 = exp_by_id.get("C-ENT-003", {})
    e003_pri = e003.get("priority", "")
    add_check("C-ENT-003_expansion_high_priority",
              e003_pri == "High",
              f"priority={e003_pri}")

    # C-ENT-001: High priority (upsell available, dept expansion, seat expansion)
    e001 = exp_by_id.get("C-ENT-001", {})
    e001_pri = e001.get("priority", "")
    add_check("C-ENT-001_expansion_high_priority",
              e001_pri == "High",
              f"priority={e001_pri}")

    # C-SMB-004: Low priority (no meaningful expansion signals)
    e004 = exp_by_id.get("C-SMB-004", {})
    e004_pri = e004.get("priority", "")
    add_check("C-SMB-004_expansion_low_priority",
              e004_pri == "Low",
              f"priority={e004_pri}")

    # C-ENT-003 upsell_available should be True (professional → enterprise)
    add_check("C-ENT-003_upsell_available",
              e003.get("upsell_available", False) == True,
              f"upsell_available={e003.get('upsell_available')}")

    # C-ENT-001 seat_expansion recommended (92% utilization)
    e001_seat = e001.get("seat_expansion_recommended", 0)
    add_check("C-ENT-001_seat_expansion_recommended",
              e001_seat > 0,
              f"seat_expansion_recommended={e001_seat}")

    # ── Cross-reference: no Red health + Low churn risk simultaneously for same customer ─
    # (This tests that the agent ran both tools correctly and integrated results)
    health_status_map = {r["customer_id"]: r.get("status") for r in health_records if isinstance(r, dict)}
    churn_tier_map    = {r["customer_id"]: r.get("risk_tier") for r in churn_records if isinstance(r, dict)}

    # C-SMB-004 must be Red health AND Critical churn (cross-pipeline consistency)
    smb_health_red   = health_status_map.get("C-SMB-004") == "Red"
    smb_churn_crit   = churn_tier_map.get("C-SMB-004") == "Critical"
    add_check("cross_pipeline_smb_red_and_critical",
              smb_health_red and smb_churn_crit,
              f"C-SMB-004: health={health_status_map.get('C-SMB-004')}, churn={churn_tier_map.get('C-SMB-004')}")

    # C-ENT-003 must be Green health AND Low churn (cross-pipeline consistency)
    ent3_health_green = health_status_map.get("C-ENT-003") == "Green"
    ent3_churn_low    = churn_tier_map.get("C-ENT-003") == "Low"
    add_check("cross_pipeline_ent3_green_and_low_risk",
              ent3_health_green and ent3_churn_low,
              f"C-ENT-003: health={health_status_map.get('C-ENT-003')}, churn={churn_tier_map.get('C-ENT-003')}")

    return checks, None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, early_exit = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_script_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result))
        return

    passed_count = sum(1 for c in checks if c["passed"])
    total_count  = len(checks)
    score = round(passed_count / total_count, 4) if total_count > 0 else 0.0

    # Must pass ALL structural + at least 12 of the proprietary checks to be considered passing
    structural_checks = ["output_file_exists", "output_file_valid_json",
                         "contains_health_data", "contains_churn_data", "contains_expansion_data",
                         "all_4_customers_in_health", "all_4_customers_in_churn", "all_4_customers_in_expansion"]
    structural_passed = all(c["passed"] for c in checks if c["name"] in structural_checks)
    overall_passed = structural_passed and passed_count >= 16

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()