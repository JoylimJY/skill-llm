import sys
import json
import re
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        return None

def find_report(workspace):
    """Find the campaign_audit_report.json anywhere in workspace."""
    hits = list(Path(workspace).rglob("campaign_audit_report.json"))
    if hits:
        return hits[0]
    return None

def check_text_contains(text, patterns, case_insensitive=True):
    """Return True if all patterns found in text."""
    flags = re.IGNORECASE if case_insensitive else 0
    return all(re.search(p, text, flags) for p in patterns)

def run_eval(workspace):
    checks = []
    overall_passed = True

    def add_check(name, passed, detail):
        nonlocal overall_passed
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            overall_passed = False

    # ---- FIND REPORT FILE ----
    report_path = find_report(workspace)
    if report_path is None:
        add_check("report_file_exists", False, "campaign_audit_report.json not found anywhere in workspace")
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("report_file_exists", True, f"Found at {report_path}")

    # ---- LOAD REPORT ----
    try:
        with open(report_path) as f:
            raw = f.read()
        report = json.loads(raw)
    except Exception as e:
        add_check("report_is_valid_json", False, f"Failed to parse JSON: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("report_is_valid_json", True, "Report parsed as valid JSON")

    # ---- CHECK 1: All 5 Output Contract Sections Present ----
    required_keys = [
        "account_health_and_structure_score",
        "bid_and_budget_efficiency_findings",
        "ab_test_structure_blueprint",
        "scale_model",
        "monitoring_and_alert_rules"
    ]
    missing_keys = [k for k in required_keys if k not in report]
    if missing_keys:
        add_check("all_five_output_sections_present", False,
                  f"Missing required top-level sections: {missing_keys}")
    else:
        add_check("all_five_output_sections_present", True,
                  "All 5 output contract sections present")

    # ---- CHECK 2: Account Health - Naming Violations Detected ----
    health = report.get("account_health_and_structure_score", {})
    health_str = json.dumps(health).lower()
    naming_issues = any(p in health_str for p in [
        "naming", "summer sale", "google retarget", "convention", "hygiene"
    ])
    add_check("account_health_naming_violations_flagged", naming_issues,
              "Report must identify naming hygiene issues (e.g., 'summer sale', 'google retarget' violate naming conventions)" if not naming_issues else "Naming violations correctly identified")

    # ---- CHECK 3: Account Health - Complexity vs Spend Decision Rule Applied ----
    # Rule: "If structure complexity is high and spend is low, simplify before adding tests"
    simplify_signal = any(p in health_str for p in [
        "simplif", "complexity", "fragmentation", "too many adsets", "low budget", "low spend"
    ])
    add_check("account_health_simplify_recommendation", simplify_signal,
              "Must apply the 'simplify before adding tests' decision rule (high complexity + low spend detected)" if not simplify_signal else "Simplification recommendation present")

    # ---- CHECK 4: Bid Strategy Misalignment Flagged ----
    bid_findings = report.get("bid_and_budget_efficiency_findings", {})
    bid_str = json.dumps(bid_findings).lower()
    roas_mismatch = any(p in bid_str for p in [
        "roas", "target_cpa", "misalign", "kpi", "bid strategy", "blended_roas"
    ])
    add_check("bid_strategy_roas_misalignment_flagged", roas_mismatch,
              "Must flag that KPI is blended_roas but bid strategies are target_cpa (misalignment)" if not roas_mismatch else "ROAS/CPA bid strategy misalignment flagged")

    # ---- CHECK 5: Budget Fragmentation Flagged ----
    budget_issue = any(p in bid_str for p in [
        "fragment", "$17", "17.14", "below threshold", "learning", "minimum", "adset budget", "per adset"
    ])
    add_check("budget_fragmentation_flagged", budget_issue,
              "Must flag budget fragmentation ($17/adset below learning threshold)" if not budget_issue else "Budget fragmentation correctly identified")

    # ---- CHECK 6: AB Test Blueprint - Required Schema Fields ----
    ab = report.get("ab_test_structure_blueprint", {})
    ab_str = json.dumps(ab).lower()

    # Must include test_id, variable, cells with control+challenger, success_metric
    has_test_id = "test_id" in ab_str
    has_variable = "variable" in ab_str
    has_control = "control" in ab_str
    has_challenger = "challenger" in ab_str
    has_success_metric = "success_metric" in ab_str

    schema_ok = all([has_test_id, has_variable, has_control, has_challenger, has_success_metric])
    detail = (
        f"test_id:{has_test_id}, variable:{has_variable}, control:{has_control}, "
        f"challenger:{has_challenger}, success_metric:{has_success_metric}"
    )
    add_check("ab_test_blueprint_schema_correct", schema_ok,
              f"AB test must include test_id, variable, cells(control+challenger), success_metric. Got: {detail}")

    # ---- CHECK 7: AB Test - Statistical Significance Constraint Enforced ----
    # Rule: "Do not claim statistical significance without threshold checks"
    # Rule: "If winning cells are statistically weak, extend learning window"
    # Must reference significance AND call out past tests as insufficient
    sig_check = any(p in ab_str for p in [
        "significance", "confidence", "threshold", "95%", "0.95", "statistical"
    ])
    weak_test_flag = any(p in ab_str for p in [
        "weak", "inconclusive", "extend", "learning window", "underpowered", "71%", "68%", "prior test", "ab-2026"
    ])
    add_check("ab_test_significance_threshold_enforced", sig_check,
              "AB test blueprint must include statistical significance threshold" if not sig_check else "Significance threshold present")
    add_check("ab_test_weak_history_addressed", weak_test_flag,
              "Must flag that prior tests (71%, 68% confidence) are below significance threshold and require extended learning window" if not weak_test_flag else "Prior weak test history addressed")

    # ---- CHECK 8: Anomaly Detection - Spend Spike Correctly Computed and Flagged ----
    # 2026-07-15: spend=998 vs avg prev 7 days ~695 => spike ~43.6% > 35% threshold
    # conversions=24 vs avg ~38.4 => drop ~37.5% > 25% threshold
    # Must trigger: severity: high, action: notify_and_limit_budget
    monitor = report.get("monitoring_and_alert_rules", {})
    monitor_str = json.dumps(monitor).lower()

    spend_spike_rule = any(p in monitor_str for p in [
        "35", "spend_spike", "spend spike"
    ])
    conv_drop_rule = any(p in monitor_str for p in [
        "25", "conversions_drop", "conversion drop", "conv drop"
    ])
    severity_high = "high" in monitor_str
    notify_action = any(p in monitor_str for p in [
        "notify_and_limit_budget", "notify and limit", "limit_budget", "limit budget"
    ])

    add_check("anomaly_rule_spend_spike_threshold_correct", spend_spike_rule,
              "Must define spend spike threshold at >35% per SKILL.md anomaly rule" if not spend_spike_rule else "Spend spike threshold (35%) correctly specified")
    add_check("anomaly_rule_conversion_drop_threshold_correct", conv_drop_rule,
              "Must define conversion drop threshold at >25% per SKILL.md anomaly rule" if not conv_drop_rule else "Conversion drop threshold (25%) correctly specified")
    add_check("anomaly_rule_severity_high_triggered", severity_high,
              "Anomaly on 2026-07-15 must trigger severity: high" if not severity_high else "Severity: high correctly triggered")
    add_check("anomaly_rule_action_correct", notify_action,
              "Action must be notify_and_limit_budget per SKILL.md anomaly rule" if not notify_action else "Action notify_and_limit_budget correctly specified")

    # ---- CHECK 9: Anomaly - Performance Series Anomaly Day Identified ----
    # Agent must note the July 15 anomaly even though anomaly_detected=False in raw data
    anomaly_date = any(p in monitor_str for p in [
        "2026-07-15", "july 15", "july-15", "07-15", "07/15"
    ])
    add_check("anomaly_date_identified", anomaly_date,
              "Must identify 2026-07-15 as the anomaly day despite anomaly_detected=False in source data" if not anomaly_date else "Anomaly date 2026-07-15 correctly identified")

    # ---- CHECK 10: Scale Model Present and Non-Empty ----
    scale = report.get("scale_model", {})
    scale_str = json.dumps(scale).strip()
    scale_non_empty = len(scale_str) > 30 and scale_str not in ["{}", "[]", '""', "null"]
    # Must include trigger conditions per Output Contract
    has_trigger = any(p in scale_str.lower() for p in [
        "trigger", "condition", "gate", "threshold", "roas", "cpa", "scale"
    ])
    add_check("scale_model_non_empty", scale_non_empty,
              f"Scale model section must be non-empty and substantive. Got: {scale_str[:80]}" if not scale_non_empty else "Scale model is present and non-empty")
    add_check("scale_model_has_trigger_conditions", has_trigger,
              "Scale model must include trigger conditions (gate conditions before budget jumps)" if not has_trigger else "Scale model includes trigger conditions")

    # ---- CHECK 11: Alert Rules Tied to Action Ownership ----
    # Constraint: "Keep alert rules tied to action ownership"
    ownership = any(p in monitor_str for p in [
        "owner", "responsible", "team", "action_owner", "notify", "escalat", "contact", "@"
    ])
    add_check("alert_rules_tied_to_action_ownership", ownership,
              "Alert rules must specify action ownership per SKILL.md constraint" if not ownership else "Action ownership specified in alert rules")

    # ---- SCORING ----
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    final_pass = passed_count >= int(total * 0.75)  # 75% threshold to pass

    return {
        "passed": final_pass,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))