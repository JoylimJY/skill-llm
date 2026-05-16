import sys
import json
import traceback
from pathlib import Path
from datetime import date, datetime

WORKSPACE = Path(sys.argv[1])
AUDIT_DATE = date(2025, 6, 15)

checks = []
total_score = 0.0

def find_file(name):
    results = list(WORKSPACE.rglob(name))
    return results[0] if results else None

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── Expected outcomes based on gen_inputs_script ─────────────────────────────
# audit_date = 2025-06-15
# REG-001: version_date=2024-05-01 → 410 days → stale (no conflict) → medium
# REG-002: version_date=2025-03-10 → 97 days → conflict_count=3>0 → conflicting → critical
# REG-003: version_date=2024-11-20 → 207 days → stale (no conflict) → medium
# REG-004: version_date=2025-05-01 → 45 days → active → low
# REG-005: version_date=2024-06-01 → 379 days → stale AND conflict_count=2 → conflicting (priority) → critical

EXPECTED_STATUS = {
    "REG-001": "stale",
    "REG-002": "conflicting",
    "REG-003": "stale",
    "REG-004": "active",
    "REG-005": "conflicting",
}

EXPECTED_RISK = {
    "REG-001": "medium",
    "REG-002": "critical",
    "REG-003": "medium",
    "REG-004": "low",
    "REG-005": "critical",
}

EXPECTED_DAYS_OLD = {
    "REG-001": (date(2025, 6, 15) - date(2024, 5, 1)).days,   # 410
    "REG-002": (date(2025, 6, 15) - date(2025, 3, 10)).days,  # 97
    "REG-003": (date(2025, 6, 15) - date(2024, 11, 20)).days, # 207
    "REG-004": (date(2025, 6, 15) - date(2025, 5, 1)).days,   # 45
    "REG-005": (date(2025, 6, 15) - date(2024, 6, 1)).days,   # 379
}

# ════════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 1: staleness_matrix.json
# ════════════════════════════════════════════════════════════════════════════════
matrix_file = find_file("staleness_matrix.json")
matrix_data = None

try:
    if matrix_file is None:
        raise FileNotFoundError("staleness_matrix.json not found anywhere in workspace")
    matrix_data = json.loads(matrix_file.read_text())

    # 1a. audit_date field
    audit_date_val = matrix_data.get("audit_date", "")
    score_part = add_check(
        "matrix_audit_date",
        audit_date_val == "2025-06-15",
        f"audit_date is '{audit_date_val}', expected '2025-06-15'",
        weight=0.5
    )
    total_score += score_part

    # 1b. Has 'rules' list with 5 entries
    rules_list = matrix_data.get("rules", [])
    score_part = add_check(
        "matrix_rules_count",
        len(rules_list) == 5,
        f"Found {len(rules_list)} rules in staleness matrix, expected 5",
        weight=1.0
    )
    total_score += score_part

    # 1c. Correct status for each rule
    rules_by_id = {r.get("rule_id"): r for r in rules_list}
    status_correct = 0
    status_details = []
    for rid, expected_status in EXPECTED_STATUS.items():
        actual = rules_by_id.get(rid, {}).get("status", "MISSING")
        if actual == expected_status:
            status_correct += 1
        else:
            status_details.append(f"{rid}: got '{actual}', expected '{expected_status}'")

    score_part = add_check(
        "matrix_rule_statuses",
        status_correct == 5,
        f"{status_correct}/5 correct. Issues: {'; '.join(status_details) if status_details else 'none'}",
        weight=2.0
    )
    total_score += score_part

    # 1d. days_old correctness (allow ±1 for boundary edge)
    days_correct = 0
    days_details = []
    for rid, expected_days in EXPECTED_DAYS_OLD.items():
        actual_days = rules_by_id.get(rid, {}).get("days_old", None)
        if actual_days is not None and abs(int(actual_days) - expected_days) <= 1:
            days_correct += 1
        else:
            days_details.append(f"{rid}: got {actual_days}, expected {expected_days}")
    score_part = add_check(
        "matrix_days_old",
        days_correct == 5,
        f"{days_correct}/5 correct days_old. Issues: {'; '.join(days_details) if days_details else 'none'}",
        weight=1.0
    )
    total_score += score_part

    # 1e. Conflicting-takes-priority for REG-005 (stale AND conflicting → must be 'conflicting')
    reg005_status = rules_by_id.get("REG-005", {}).get("status", "MISSING")
    score_part = add_check(
        "matrix_conflict_priority_reg005",
        reg005_status == "conflicting",
        f"REG-005 must be 'conflicting' (conflict takes priority over stale). Got: '{reg005_status}'",
        weight=1.5
    )
    total_score += score_part

    # 1f. Evidence field present and non-empty for stale/conflicting rules
    evidence_ok = all(
        bool(rules_by_id.get(rid, {}).get("evidence", "").strip())
        for rid in ["REG-001", "REG-002", "REG-003", "REG-005"]
    )
    score_part = add_check(
        "matrix_evidence_populated",
        evidence_ok,
        "Evidence field must be non-empty for stale/conflicting rules",
        weight=0.5
    )
    total_score += score_part

except Exception as e:
    add_check("matrix_file_load", False, f"Could not load staleness_matrix.json: {e}")
    traceback.print_exc()

# ════════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 2: config/proposed/config_diffs.json
# ════════════════════════════════════════════════════════════════════════════════
diffs_file = find_file("config_diffs.json")
diffs_data = None

try:
    if diffs_file is None:
        raise FileNotFoundError("config_diffs.json not found")
    diffs_data = json.loads(diffs_file.read_text())

    # 2a. Top-level structure
    has_generated_at = "generated_at" in diffs_data
    has_diffs_key = "diffs" in diffs_data
    score_part = add_check(
        "diffs_top_level_structure",
        has_generated_at and has_diffs_key,
        f"generated_at present: {has_generated_at}, diffs key present: {has_diffs_key}",
        weight=0.5
    )
    total_score += score_part

    diffs_list = diffs_data.get("diffs", [])
    diffs_by_id = {d.get("rule_id"): d for d in diffs_list}

    # 2b. Only stale/conflicting rules have diffs (REG-001, REG-002, REG-003, REG-005) — NOT REG-004
    expected_diff_ids = {"REG-001", "REG-002", "REG-003", "REG-005"}
    actual_diff_ids = set(diffs_by_id.keys())
    score_part = add_check(
        "diffs_correct_rule_selection",
        expected_diff_ids == actual_diff_ids,
        f"Expected diffs for {sorted(expected_diff_ids)}, got {sorted(actual_diff_ids)}",
        weight=1.5
    )
    total_score += score_part

    # 2c. Stale rule config diff: REG-001 (stale)
    # policy_checks.after.version = old + 1 = 4
    # fact_resolution.after.refresh_required = True
    # routing_impacts.after.review_queue = "compliance_backlog"
    reg001_diff = diffs_by_id.get("REG-001", {})
    pc_after = reg001_diff.get("policy_checks", {}).get("after", {})
    fr_after = reg001_diff.get("fact_resolution", {}).get("after", {})
    ri_after = reg001_diff.get("routing_impacts", {}).get("after", {})
    stale_diff_ok = (
        pc_after.get("version") == 4 and
        fr_after.get("refresh_required") == True and
        ri_after.get("review_queue") == "compliance_backlog"
    )
    score_part = add_check(
        "diffs_stale_rule_reg001",
        stale_diff_ok,
        f"REG-001 stale diff: policy_checks.after.version={pc_after.get('version')} (exp 4), "
        f"fact_resolution.after.refresh_required={fr_after.get('refresh_required')} (exp True), "
        f"routing_impacts.after.review_queue={ri_after.get('review_queue')} (exp 'compliance_backlog')",
        weight=2.0
    )
    total_score += score_part

    # 2d. Conflicting rule config diff: REG-002 (conflicting)
    # policy_checks.after.suspended = True
    # fact_resolution.after.override_mode = "manual"
    # routing_impacts.after.review_queue = "conflict_resolution"
    reg002_diff = diffs_by_id.get("REG-002", {})
    pc_after2 = reg002_diff.get("policy_checks", {}).get("after", {})
    fr_after2 = reg002_diff.get("fact_resolution", {}).get("after", {})
    ri_after2 = reg002_diff.get("routing_impacts", {}).get("after", {})
    conflict_diff_ok = (
        pc_after2.get("suspended") == True and
        fr_after2.get("override_mode") == "manual" and
        ri_after2.get("review_queue") == "conflict_resolution"
    )
    score_part = add_check(
        "diffs_conflicting_rule_reg002",
        conflict_diff_ok,
        f"REG-002 conflicting diff: suspended={pc_after2.get('suspended')} (exp True), "
        f"override_mode={fr_after2.get('override_mode')} (exp 'manual'), "
        f"review_queue={ri_after2.get('review_queue')} (exp 'conflict_resolution')",
        weight=2.0
    )
    total_score += score_part

    # 2e. REG-005 (conflicting-priority): must use conflicting diff pattern, not stale
    reg005_diff = diffs_by_id.get("REG-005", {})
    pc_after5 = reg005_diff.get("policy_checks", {}).get("after", {})
    ri_after5 = reg005_diff.get("routing_impacts", {}).get("after", {})
    reg005_uses_conflict_pattern = (
        pc_after5.get("suspended") == True and
        ri_after5.get("review_queue") == "conflict_resolution"
    )
    score_part = add_check(
        "diffs_reg005_uses_conflict_pattern",
        reg005_uses_conflict_pattern,
        f"REG-005 must use conflicting diff pattern (suspended=True, review_queue='conflict_resolution'). "
        f"Got suspended={pc_after5.get('suspended')}, review_queue={ri_after5.get('review_queue')}",
        weight=2.0
    )
    total_score += score_part

    # 2f. before values preserved from original regulation
    reg001_pc_before = reg001_diff.get("policy_checks", {}).get("before", {})
    before_version_ok = reg001_pc_before.get("version") == 3
    score_part = add_check(
        "diffs_before_values_preserved",
        before_version_ok,
        f"REG-001 policy_checks.before.version should be 3 (original), got {reg001_pc_before.get('version')}",
        weight=1.0
    )
    total_score += score_part

except Exception as e:
    add_check("diffs_file_load", False, f"Could not load config_diffs.json: {e}")
    traceback.print_exc()

# ════════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 3: reports/change_report.json
# ════════════════════════════════════════════════════════════════════════════════
report_file = find_file("change_report.json")
report_data = None

try:
    if report_file is None:
        raise FileNotFoundError("change_report.json not found")
    report_data = json.loads(report_file.read_text())

    # 3a. report_date
    score_part = add_check(
        "report_date",
        report_data.get("report_date") == "2025-06-15",
        f"report_date is '{report_data.get('report_date')}', expected '2025-06-15'",
        weight=0.5
    )
    total_score += score_part

    # 3b. Summary counts
    summary = report_data.get("summary", {})
    summary_ok = (
        summary.get("total_rules") == 5 and
        summary.get("stale_count") == 2 and      # REG-001, REG-003
        summary.get("conflicting_count") == 2 and  # REG-002, REG-005
        summary.get("active_count") == 1           # REG-004
    )
    score_part = add_check(
        "report_summary_counts",
        summary_ok,
        f"summary: total={summary.get('total_rules')}/5, stale={summary.get('stale_count')}/2, "
        f"conflicting={summary.get('conflicting_count')}/2, active={summary.get('active_count')}/1",
        weight=1.5
    )
    total_score += score_part

    # 3c. Risk class correct for each rule
    changes_list = report_data.get("changes", [])
    changes_by_id = {c.get("rule_id"): c for c in changes_list}
    risk_correct = 0
    risk_details = []
    for rid, expected_risk in EXPECTED_RISK.items():
        actual_risk = changes_by_id.get(rid, {}).get("risk_class", "MISSING")
        if actual_risk == expected_risk:
            risk_correct += 1
        else:
            risk_details.append(f"{rid}: got '{actual_risk}', expected '{expected_risk}'")
    score_part = add_check(
        "report_risk_classes",
        risk_correct == 5,
        f"{risk_correct}/5 risk classes correct. Issues: {'; '.join(risk_details) if risk_details else 'none'}",
        weight=2.0
    )
    total_score += score_part

    # 3d. Rollout recommendations match expected strings
    expected_rollout = {
        "REG-001": "Schedule update in next sprint cycle with regression testing.",
        "REG-002": "Immediate suspension pending manual conflict resolution.",
        "REG-003": "Schedule update in next sprint cycle with regression testing.",
        "REG-004": "No action required. Monitor in next quarterly review.",
        "REG-005": "Immediate suspension pending manual conflict resolution.",
    }
    rollout_correct = 0
    rollout_details = []
    for rid, exp_rec in expected_rollout.items():
        actual_rec = changes_by_id.get(rid, {}).get("rollout_recommendation", "MISSING")
        if actual_rec == exp_rec:
            rollout_correct += 1
        else:
            rollout_details.append(f"{rid}: got '{actual_rec}'")
    score_part = add_check(
        "report_rollout_recommendations",
        rollout_correct == 5,
        f"{rollout_correct}/5 rollout recommendations correct. Issues: {'; '.join(rollout_details) if rollout_details else 'none'}",
        weight=2.0
    )
    total_score += score_part

    # 3e. Backward compatibility: critical rules → False, others → True
    bc_correct = 0
    bc_details = []
    expected_bc = {
        "REG-001": True,
        "REG-002": False,
        "REG-003": True,
        "REG-004": True,
        "REG-005": False,
    }
    for rid, exp_bc in expected_bc.items():
        actual_bc = changes_by_id.get(rid, {}).get("backward_compatible", None)
        if actual_bc == exp_bc:
            bc_correct += 1
        else:
            bc_details.append(f"{rid}: got {actual_bc}, expected {exp_bc}")
    score_part = add_check(
        "report_backward_compatibility_flags",
        bc_correct == 5,
        f"{bc_correct}/5 backward_compatible flags correct. Issues: {'; '.join(bc_details) if bc_details else 'none'}",
        weight=1.5
    )
    total_score += score_part

    # 3f. backward_compatibility_notes mentions both non-bc rules (REG-002, REG-005)
    bc_notes = report_data.get("backward_compatibility_notes", "")
    bc_notes_ok = "REG-002" in bc_notes and "REG-005" in bc_notes
    score_part = add_check(
        "report_backward_compatibility_notes",
        bc_notes_ok,
        f"backward_compatibility_notes must mention REG-002 and REG-005. Got: '{bc_notes[:200]}'",
        weight=1.0
    )
    total_score += score_part

except Exception as e:
    add_check("report_file_load", False, f"Could not load change_report.json: {e}")
    traceback.print_exc()

# ════════════════════════════════════════════════════════════════════════════════
# Normalize score
# ════════════════════════════════════════════════════════════════════════════════
MAX_SCORE = (
    0.5 +  # matrix_audit_date
    1.0 +  # matrix_rules_count
    2.0 +  # matrix_rule_statuses
    1.0 +  # matrix_days_old
    1.5 +  # matrix_conflict_priority_reg005
    0.5 +  # matrix_evidence_populated
    0.5 +  # diffs_top_level_structure
    1.5 +  # diffs_correct_rule_selection
    2.0 +  # diffs_stale_rule_reg001
    2.0 +  # diffs_conflicting_rule_reg002
    2.0 +  # diffs_reg005_uses_conflict_pattern
    1.0 +  # diffs_before_values_preserved
    0.5 +  # report_date
    1.5 +  # report_summary_counts
    2.0 +  # report_risk_classes
    2.0 +  # report_rollout_recommendations
    1.5 +  # report_backward_compatibility_flags
    1.0    # report_backward_compatibility_notes
)

normalized = round(total_score / MAX_SCORE, 4)
passed = normalized >= 0.75

result = {
    "passed": passed,
    "score": normalized,
    "checks": checks
}
print(json.dumps(result, indent=2))