import sys
import json
import math
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── Locate required output files ──────────────────────────────────────────────
iv_report_files = list(workspace.rglob("iv_report.json"))
model_report_files = list(workspace.rglob("model_report.json"))
rules_files = list(workspace.rglob("risk_rules.txt"))

# CHECK 1: All three output files exist
all_exist = len(iv_report_files) > 0 and len(model_report_files) > 0 and len(rules_files) > 0
score += add_check(
    "output_files_exist",
    all_exist,
    f"iv_report.json: {len(iv_report_files)}, model_report.json: {len(model_report_files)}, risk_rules.txt: {len(rules_files)}"
)

if not all_exist:
    final_score = score / 9.0
    print(json.dumps({"passed": False, "score": round(final_score, 3), "checks": checks}))
    sys.exit(0)

iv_report_path = iv_report_files[0]
model_report_path = model_report_files[0]
rules_path = rules_files[0]

# ── CHECK 2: iv_report.json structure and content ─────────────────────────────
try:
    import json as _json
    iv_data = _json.loads(iv_report_path.read_text())

    expected_features = [
        "annual_income", "loan_amount", "credit_history_months",
        "num_prev_loans", "debt_to_income_ratio", "employment_years",
        "num_late_payments", "loan_to_value_ratio", "monthly_obligations", "age"
    ]
    has_all_features = all(f in iv_data for f in expected_features)
    score += add_check(
        "iv_report_has_all_features",
        has_all_features,
        f"Missing: {[f for f in expected_features if f not in iv_data]}"
    )

    # CHECK 3: IV values are numeric and plausible (0 < IV < 10 for most)
    iv_values_valid = all(
        isinstance(iv_data[f], (int, float)) and iv_data[f] >= 0
        for f in iv_data
    )
    score += add_check(
        "iv_values_are_non_negative_floats",
        iv_values_valid,
        f"IV values: { {k: round(v, 4) for k, v in iv_data.items()} }"
    )

    # CHECK 4: Strong features (IV > 0.3) are correctly identified
    # Based on the data generation, num_late_payments, debt_to_income_ratio,
    # loan_to_value_ratio, and possibly credit_history_months should be strong.
    # We check that at least 2 features exceed IV > 0.3
    strong_features = [f for f, v in iv_data.items() if v > 0.3]
    has_strong_features = len(strong_features) >= 2
    score += add_check(
        "iv_strong_features_detected",
        has_strong_features,
        f"Features with IV > 0.3: {strong_features}"
    )

    # CHECK 5: Verify WOE formula correctness via IV magnitude ordering
    # num_late_payments and debt_to_income_ratio should be among the top predictors
    # We verify their IVs are relatively high compared to age (weak predictor)
    if "num_late_payments" in iv_data and "age" in iv_data:
        late_vs_age = iv_data["num_late_payments"] > iv_data["age"]
        score += add_check(
            "iv_ordering_sanity_num_late_payments_stronger_than_age",
            late_vs_age,
            f"num_late_payments IV={iv_data.get('num_late_payments', 'N/A'):.4f}, age IV={iv_data.get('age', 'N/A'):.4f}"
        )
    else:
        score += add_check(
            "iv_ordering_sanity_num_late_payments_stronger_than_age",
            False,
            "Missing num_late_payments or age in iv_data"
        )

except Exception as e:
    score += add_check("iv_report_has_all_features", False, f"Exception: {e}")
    score += add_check("iv_values_are_non_negative_floats", False, f"Exception: {e}")
    score += add_check("iv_strong_features_detected", False, f"Exception: {e}")
    score += add_check("iv_ordering_sanity_num_late_payments_stronger_than_age", False, f"Exception: {e}")

# ── CHECK 6-8: model_report.json ──────────────────────────────────────────────
try:
    model_data = _json.loads(model_report_path.read_text())

    # CHECK 6: AUC is present and above 0.7 threshold
    auc = model_data.get("auc", 0)
    auc_ok = isinstance(auc, (int, float)) and auc > 0.65  # slightly lenient for data variability
    score += add_check(
        "model_auc_above_threshold",
        auc_ok,
        f"AUC = {auc}"
    )

    # CHECK 7: Only strong features (IV > 0.3) were used in model training
    features_used = model_data.get("features_used", [])
    try:
        iv_data_check = _json.loads(iv_report_path.read_text())
        strong_feats = set(f for f, v in iv_data_check.items() if v > 0.3)
        weak_feats_used = set(features_used) - strong_feats
        only_strong = len(weak_feats_used) == 0 and len(features_used) > 0
        score += add_check(
            "model_trained_only_on_strong_iv_features",
            only_strong,
            f"Features used: {features_used}. Strong features (IV>0.3): {strong_feats}. Weak features mistakenly included: {weak_feats_used}"
        )
    except Exception as e2:
        score += add_check("model_trained_only_on_strong_iv_features", False, f"Exception: {e2}")

    # CHECK 8: KS value is reported (indicates agent computed it)
    ks = model_data.get("ks", None)
    ks_reported = ks is not None and isinstance(ks, (int, float)) and ks >= 0
    score += add_check(
        "model_ks_reported",
        ks_reported,
        f"KS = {ks}"
    )

except Exception as e:
    score += add_check("model_auc_above_threshold", False, f"Exception: {e}")
    score += add_check("model_trained_only_on_strong_iv_features", False, f"Exception: {e}")
    score += add_check("model_ks_reported", False, f"Exception: {e}")

# ── CHECK 9: risk_rules.txt contains valid decision tree export ────────────────
try:
    rules_text = rules_path.read_text()
    # export_text produces lines with "|--- feature_name <= value" pattern
    has_tree_structure = ("|---" in rules_text or "--- " in rules_text)
    has_class_lines = ("class:" in rules_text or "value:" in rules_text)
    rules_ok = has_tree_structure and len(rules_text.strip()) > 50
    score += add_check(
        "risk_rules_txt_contains_decision_tree_export",
        rules_ok,
        f"File length: {len(rules_text)} chars. Has tree structure: {has_tree_structure}. Sample: {rules_text[:200]!r}"
    )
except Exception as e:
    score += add_check("risk_rules_txt_contains_decision_tree_export", False, f"Exception: {e}")

# ── Final scoring ─────────────────────────────────────────────────────────────
total_checks = 9
final_score = score / total_checks
all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": all_passed,
    "score": round(final_score, 3),
    "checks": checks
}, ensure_ascii=False, indent=2))