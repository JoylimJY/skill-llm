import sys
import json
import math
from pathlib import Path

def load_report(workspace):
    """Find retention_audit_report.json anywhere in workspace."""
    matches = list(Path(workspace).rglob("retention_audit_report.json"))
    if not matches:
        return None, "File retention_audit_report.json not found anywhere in workspace"
    return matches[0], None

def safe_get(d, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
        if d is None:
            return default
    return d

def run_eval(workspace):
    checks = []

    report_path, err = load_report(workspace)
    if err:
        checks.append({"name": "report_exists", "passed": False, "detail": err})
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append({"name": "report_exists", "passed": True, "detail": str(report_path)})

    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "report_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "report_parseable", "passed": True, "detail": "Valid JSON"})

    # ── CHECK 1: Monthly churn rates calculated correctly ─────────────────────
    # Formula: (customers_lost / customers_start) * 100
    # Expected from monthly_snapshot.csv:
    # 2023-10: 7/60 = 11.67% → CRITICAL (>10%)
    # 2023-11: 4/68 = 5.88%  → NEEDS WORK (5-10%)
    # 2023-12: 9/78 = 11.54% → CRITICAL (>10%)
    # 2024-01: 6/85 = 7.06%  → NEEDS WORK (5-10%)
    # 2024-02: 5/115 = 4.35% → HEALTHY (<5%)
    # 2024-03: 4/125 = 3.20% → HEALTHY (<5%)
    expected_churn = {
        "2023-10": (7/60*100, "critical"),
        "2023-11": (4/68*100, "needs_work"),
        "2023-12": (9/78*100, "critical"),
        "2024-01": (6/85*100, "needs_work"),
        "2024-02": (5/115*100, "healthy"),
        "2024-03": (4/125*100, "healthy"),
    }

    monthly_churn = safe_get(report, "monthly_metrics")
    churn_check_passed = True
    churn_details = []
    if not monthly_churn or not isinstance(monthly_churn, (list, dict)):
        churn_check_passed = False
        churn_details.append("monthly_metrics missing or wrong type")
    else:
        # Support both list and dict
        if isinstance(monthly_churn, list):
            monthly_dict = {m.get("month", m.get("period", "")): m for m in monthly_churn}
        else:
            monthly_dict = monthly_churn

        for month, (expected_rate, expected_status) in expected_churn.items():
            entry = monthly_dict.get(month)
            if not entry:
                churn_check_passed = False
                churn_details.append(f"Missing month {month}")
                continue
            # Check churn rate (within 0.1%)
            actual_rate = None
            for key in ["churn_rate", "churn_rate_pct", "monthly_churn_rate", "churn_percentage"]:
                if key in entry:
                    try:
                        actual_rate = float(entry[key])
                    except:
                        pass
                    break
            if actual_rate is None:
                churn_check_passed = False
                churn_details.append(f"{month}: churn_rate field missing")
                continue
            if abs(actual_rate - expected_rate) > 0.15:
                churn_check_passed = False
                churn_details.append(f"{month}: churn_rate {actual_rate:.2f}% expected ~{expected_rate:.2f}%")
                continue
            # Check benchmark status
            actual_status = None
            for key in ["health_status", "benchmark_status", "status", "classification"]:
                if key in entry:
                    actual_status = str(entry[key]).lower().replace(" ", "_").replace("-", "_")
                    break
            if actual_status is None:
                churn_check_passed = False
                churn_details.append(f"{month}: health_status field missing")
                continue
            # Normalize
            if expected_status == "critical" and "critical" not in actual_status:
                churn_check_passed = False
                churn_details.append(f"{month}: expected status 'critical' got '{actual_status}'")
            elif expected_status == "needs_work" and not any(x in actual_status for x in ["needs_work", "needs work", "warning"]):
                churn_check_passed = False
                churn_details.append(f"{month}: expected status 'needs_work' got '{actual_status}'")
            elif expected_status == "healthy" and "healthy" not in actual_status:
                churn_check_passed = False
                churn_details.append(f"{month}: expected status 'healthy' got '{actual_status}'")

    checks.append({
        "name": "monthly_churn_rates_and_benchmarks",
        "passed": churn_check_passed,
        "detail": "; ".join(churn_details) if churn_details else "All monthly churn rates and benchmarks correct"
    })

    # ── CHECK 2: Cohort retention % computed correctly ────────────────────────
    # 2023-01 cohort: m1=50/55=90.9%, m3=42/55=76.4%, m6=38/55=69.1%, m12=30/55=54.5% → NEEDS WORK (50-70%)
    # 2023-07 cohort: m1=55/62=88.7%, m3=46/62=74.2%
    cohort_retention = safe_get(report, "cohort_retention")
    cohort_check_passed = True
    cohort_details = []

    if not cohort_retention or not isinstance(cohort_retention, (list, dict)):
        cohort_check_passed = False
        cohort_details.append("cohort_retention missing or wrong type")
    else:
        if isinstance(cohort_retention, list):
            cohort_dict = {str(c.get("cohort", "")): c for c in cohort_retention}
        else:
            cohort_dict = cohort_retention

        # Check 2023-01 cohort 12-month retention: 30/55 = 54.5% → needs_work (50-70%)
        c = cohort_dict.get("2023-01")
        if not c:
            cohort_check_passed = False
            cohort_details.append("2023-01 cohort missing")
        else:
            m12_val = None
            for key in ["month_12_retention", "m12_retention", "month_12_retention_pct", "12m_retention"]:
                if key in c:
                    try:
                        m12_val = float(c[key])
                    except:
                        pass
                    break
            if m12_val is None:
                cohort_check_passed = False
                cohort_details.append("2023-01 cohort month_12_retention missing")
            elif abs(m12_val - 54.545) > 1.0:
                cohort_check_passed = False
                cohort_details.append(f"2023-01 m12 retention {m12_val:.1f}% expected ~54.5%")
            # Check benchmark
            status_12 = None
            for key in ["month_12_status", "health_status", "12m_status", "benchmark"]:
                if key in c:
                    status_12 = str(c[key]).lower().replace(" ", "_").replace("-", "_")
                    break
            if status_12 and "needs_work" not in status_12 and "needs work" not in status_12 and "warning" not in status_12:
                # 54.5% is in 50-70% range = needs_work
                cohort_check_passed = False
                cohort_details.append(f"2023-01 12m benchmark should be needs_work, got '{status_12}'")

    checks.append({
        "name": "cohort_retention_percentages",
        "passed": cohort_check_passed,
        "detail": "; ".join(cohort_details) if cohort_details else "Cohort retention percentages correct"
    })

    # ── CHECK 3: At-risk customers correctly identified ───────────────────────
    # At-risk = active customers who haven't logged in 30+ days OR usage dropped 50%+
    # Must read customers.csv and apply these rules
    import csv
    from datetime import datetime
    REFERENCE_DATE = datetime(2024, 4, 1)

    customers_path = Path(workspace) / "data/raw/exports/customers.csv"
    expected_at_risk_ids = set()
    try:
        with open(customers_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["status"] != "active":
                    continue
                last_login = datetime.strptime(row["last_login_date"], "%Y-%m-%d")
                days_inactive = (REFERENCE_DATE - last_login).days
                baseline = int(row["monthly_logins_baseline"])
                last30 = int(row["monthly_logins_last30"])
                usage_drop = (baseline - last30) / baseline if baseline > 0 else 0

                is_inactive_30 = days_inactive >= 30
                is_usage_drop_50 = usage_drop >= 0.5

                if is_inactive_30 or is_usage_drop_50:
                    expected_at_risk_ids.add(row["customer_id"])
    except Exception as e:
        checks.append({"name": "at_risk_customers_identified", "passed": False, "detail": f"Error computing expected at-risk: {e}"})
        expected_at_risk_ids = set()

    at_risk_data = safe_get(report, "at_risk_customers")
    at_risk_passed = True
    at_risk_details = []

    if at_risk_data is None:
        at_risk_passed = False
        at_risk_details.append("at_risk_customers field missing from report")
    else:
        # Extract IDs from at_risk_data (could be list of strings or list of dicts)
        actual_at_risk_ids = set()
        if isinstance(at_risk_data, list):
            for item in at_risk_data:
                if isinstance(item, str):
                    actual_at_risk_ids.add(item)
                elif isinstance(item, dict):
                    for key in ["customer_id", "id", "customer"]:
                        if key in item:
                            actual_at_risk_ids.add(item[key])
                            break
        elif isinstance(at_risk_data, dict):
            for key in ["ids", "customers", "customer_ids"]:
                if key in at_risk_data:
                    for item in at_risk_data[key]:
                        if isinstance(item, str):
                            actual_at_risk_ids.add(item)
                        elif isinstance(item, dict):
                            for k2 in ["customer_id", "id"]:
                                if k2 in item:
                                    actual_at_risk_ids.add(item[k2])

        if len(expected_at_risk_ids) > 0:
            # Allow small tolerance: must get at least 80% right
            correct_ids = actual_at_risk_ids & expected_at_risk_ids
            false_positives = actual_at_risk_ids - expected_at_risk_ids
            false_negatives = expected_at_risk_ids - actual_at_risk_ids
            precision = len(correct_ids) / len(actual_at_risk_ids) if actual_at_risk_ids else 0
            recall = len(correct_ids) / len(expected_at_risk_ids) if expected_at_risk_ids else 0

            if recall < 0.75:
                at_risk_passed = False
                at_risk_details.append(f"Recall too low: {recall:.2f}. Missing: {list(false_negatives)[:5]}")
            if precision < 0.75:
                at_risk_passed = False
                at_risk_details.append(f"Precision too low: {precision:.2f}. False positives: {list(false_positives)[:5]}")
            if at_risk_passed:
                at_risk_details.append(f"At-risk: {len(correct_ids)}/{len(expected_at_risk_ids)} correct (recall={recall:.2f}, precision={precision:.2f})")

    checks.append({
        "name": "at_risk_customers_identified",
        "passed": at_risk_passed,
        "detail": "; ".join(at_risk_details) if at_risk_details else f"At-risk customers correctly identified"
    })

    # ── CHECK 4: Lifecycle stage classification correct ───────────────────────
    # Stage 1 (Onboarding): days since signup 0-7
    # Stage 2 (Habit Formation): days 8-90
    # Stage 3 (Ongoing Value): days 91+
    lifecycle_data = safe_get(report, "lifecycle_stages") or safe_get(report, "customer_lifecycle_stages")
    lifecycle_passed = True
    lifecycle_details = []

    if lifecycle_data is None:
        lifecycle_passed = False
        lifecycle_details.append("lifecycle_stages field missing from report")
    else:
        # Check counts/assignments are roughly right
        # Compute expected from customers.csv
        expected_stages = {}
        try:
            with open(customers_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["status"] != "active":
                        continue
                    signup = datetime.strptime(row["signup_date"], "%Y-%m-%d")
                    days = (REFERENCE_DATE - signup).days
                    if days <= 7:
                        stage = "onboarding"
                    elif days <= 90:
                        stage = "habit_formation"
                    else:
                        stage = "ongoing_value"
                    expected_stages[row["customer_id"]] = stage
        except Exception as e:
            lifecycle_details.append(f"Could not compute expected stages: {e}")

        # Check that stage counts are right
        if expected_stages:
            from collections import Counter
            exp_counts = Counter(expected_stages.values())

            # Check if lifecycle_data is a dict with stage keys or a list
            if isinstance(lifecycle_data, dict):
                for stage_key in ["onboarding", "habit_formation", "ongoing_value"]:
                    stage_entries = lifecycle_data.get(stage_key, [])
                    actual_count = len(stage_entries) if isinstance(stage_entries, list) else safe_get(lifecycle_data, stage_key + "_count", default=0)
                    expected_count = exp_counts.get(stage_key, 0)
                    if isinstance(actual_count, int) and abs(actual_count - expected_count) > 2:
                        lifecycle_passed = False
                        lifecycle_details.append(f"{stage_key}: expected ~{expected_count} got {actual_count}")
            elif isinstance(lifecycle_data, list):
                # Each item has customer_id and stage
                actual_map = {}
                for item in lifecycle_data:
                    if isinstance(item, dict):
                        cid = item.get("customer_id", item.get("id"))
                        stage = str(item.get("stage", item.get("lifecycle_stage", ""))).lower().replace(" ", "_").replace("-", "_")
                        if cid:
                            actual_map[cid] = stage

                correct = 0
                for cid, exp_stage in expected_stages.items():
                    act_stage = actual_map.get(cid, "")
                    if exp_stage in act_stage or act_stage in exp_stage:
                        correct += 1
                if len(expected_stages) > 0:
                    acc = correct / len(expected_stages)
                    if acc < 0.80:
                        lifecycle_passed = False
                        lifecycle_details.append(f"Lifecycle accuracy {acc:.2f} < 0.80 threshold")
                    else:
                        lifecycle_details.append(f"Lifecycle accuracy: {acc:.2f}")

    checks.append({
        "name": "lifecycle_stage_classification",
        "passed": lifecycle_passed,
        "detail": "; ".join(lifecycle_details) if lifecycle_details else "Lifecycle stages classified correctly"
    })

    # ── CHECK 5: Re-engagement campaign schedule present with correct timing ──
    # Must have 5 emails at days 0, 3, 7, 10, 14
    reengagement = safe_get(report, "reengagement_campaign") or safe_get(report, "re_engagement_campaign")
    reengage_passed = True
    reengage_details = []

    if reengagement is None:
        reengage_passed = False
        reengage_details.append("reengagement_campaign field missing from report")
    else:
        emails = None
        if isinstance(reengagement, list):
            emails = reengagement
        elif isinstance(reengagement, dict):
            for key in ["emails", "sequence", "steps", "campaign_emails"]:
                if key in reengagement:
                    emails = reengagement[key]
                    break
            if emails is None and any(isinstance(v, list) for v in reengagement.values()):
                for v in reengagement.values():
                    if isinstance(v, list):
                        emails = v
                        break

        if not emails:
            reengage_passed = False
            reengage_details.append("No email sequence found in reengagement_campaign")
        else:
            expected_days = {0, 3, 7, 10, 14}
            actual_days = set()
            for email in emails:
                if isinstance(email, dict):
                    for key in ["day", "send_day", "day_offset", "day_number"]:
                        if key in email:
                            try:
                                actual_days.add(int(email[key]))
                            except:
                                pass
                            break
            missing_days = expected_days - actual_days
            if missing_days:
                reengage_passed = False
                reengage_details.append(f"Missing email days: {sorted(missing_days)}. Found days: {sorted(actual_days)}")
            else:
                reengage_details.append(f"All 5 email send days correct: {sorted(actual_days)}")

            # Check email count
            if len(emails) < 5:
                reengage_passed = False
                reengage_details.append(f"Only {len(emails)} emails defined, need 5")

    checks.append({
        "name": "reengagement_campaign_schedule",
        "passed": reengage_passed,
        "detail": "; ".join(reengage_details) if reengage_details else "Re-engagement campaign schedule correct"
    })

    # ── CHECK 6: Loyalty recommendations respect 100-customer threshold ────────
    loyalty = safe_get(report, "loyalty_recommendations") or safe_get(report, "loyalty_strategy")
    loyalty_passed = True
    loyalty_details = []

    if loyalty is None:
        loyalty_passed = False
        loyalty_details.append("loyalty_recommendations missing from report")
    else:
        # Business has 130 active customers → VIP tier IS recommended (threshold: 100+)
        loyalty_str = json.dumps(loyalty).lower()
        if "vip" not in loyalty_str:
            loyalty_passed = False
            loyalty_details.append("VIP tier recommendation missing (business has 130 customers, threshold is 100+)")
        else:
            loyalty_details.append("VIP tier correctly recommended (130 customers >= 100 threshold)")

        # Annual discount should be mentioned for SaaS
        if "annual" not in loyalty_str:
            loyalty_passed = False
            loyalty_details.append("Annual discount recommendation missing (applicable for SaaS subscriptions)")

    checks.append({
        "name": "loyalty_recommendations_threshold",
        "passed": loyalty_passed,
        "detail": "; ".join(loyalty_details) if loyalty_details else "Loyalty recommendations correct"
    })

    # ── CHECK 7: Top churn reasons analyzed from cancellation data ────────────
    churn_analysis = safe_get(report, "churn_analysis") or safe_get(report, "churn_reasons")
    churn_reasons_passed = True
    churn_reasons_details = []

    if churn_analysis is None:
        churn_reasons_passed = False
        churn_reasons_details.append("churn_analysis missing from report")
    else:
        # Should include not_using_enough as a top reason (most common in data)
        analysis_str = json.dumps(churn_analysis).lower()
        expected_reasons = ["not_using_enough", "not using", "usage", "too_expensive", "expensive", "missing_feature", "feature"]
        found_any = any(r in analysis_str for r in expected_reasons)
        if not found_any:
            churn_reasons_passed = False
            churn_reasons_details.append("No recognized churn reasons found in churn_analysis")
        else:
            churn_reasons_details.append("Churn reasons identified from cancellation data")

    checks.append({
        "name": "churn_reasons_analyzed",
        "passed": churn_reasons_passed,
        "detail": "; ".join(churn_reasons_details) if churn_reasons_details else "Churn reasons correctly analyzed"
    })

    # ── Final scoring ─────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks

    # Must pass at least 5 of 7 checks (plus report exists/parseable)
    critical_checks = ["monthly_churn_rates_and_benchmarks", "at_risk_customers_identified",
                       "reengagement_campaign_schedule", "lifecycle_stage_classification",
                       "loyalty_recommendations_threshold"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)

    overall_passed = score >= 0.75 and critical_passed

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))