import sys
import json
import math
from pathlib import Path

def load_json(path, label):
    try:
        with open(path) as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"{label}: file not found at {path}"
    except json.JSONDecodeError as e:
        return None, f"{label}: JSON parse error — {e}"

def find_file(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    if not matches:
        return None
    return matches[0]

def run_checks(workspace):
    checks = []
    workspace = Path(workspace)

    # ─── CHECK 1: experiment_analysis.json exists ───────────────────────────
    exp_path = find_file(workspace, "experiment_analysis.json")
    if exp_path is None:
        checks.append({"name": "experiment_analysis.json exists", "passed": False,
                        "detail": "File not found anywhere in workspace"})
    else:
        checks.append({"name": "experiment_analysis.json exists", "passed": True,
                        "detail": str(exp_path)})

    # ─── CHECK 2: Bonferroni-corrected alpha applied ─────────────────────────
    # With 3 metrics (1 primary + 2 secondary) total metrics = 3, alpha = 0.05/3 ≈ 0.01667
    if exp_path:
        data, err = load_json(exp_path, "experiment_analysis.json")
        if err:
            checks.append({"name": "Bonferroni correction applied", "passed": False, "detail": err})
        else:
            # Look for evidence of corrected alpha
            raw = json.dumps(data)
            # Check that corrected_alpha or bonferroni_alpha ≈ 0.05/3 is stored
            bonf_found = False
            bonf_value = None
            for key in ["corrected_alpha", "bonferroni_alpha", "adjusted_alpha", "alpha_corrected"]:
                if key in data:
                    bonf_value = data[key]
                    bonf_found = True
                    break
            # Also search recursively in nested structures
            if not bonf_found:
                def find_key(obj, keys):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if k in keys:
                                return v
                            res = find_key(v, keys)
                            if res is not None:
                                return res
                    elif isinstance(obj, list):
                        for item in obj:
                            res = find_key(item, keys)
                            if res is not None:
                                return res
                    return None
                bonf_value = find_key(data, ["corrected_alpha", "bonferroni_alpha",
                                             "adjusted_alpha", "alpha_corrected"])
                if bonf_value is not None:
                    bonf_found = True

            if bonf_found and bonf_value is not None:
                expected = 0.05 / 3
                passed = abs(float(bonf_value) - expected) < 0.001
                checks.append({"name": "Bonferroni correction applied",
                                "passed": passed,
                                "detail": f"Found corrected_alpha={bonf_value}, expected≈{expected:.5f}"})
            else:
                # Fallback: check if the value 0.0167 appears as significance threshold
                passed = "0.0166" in raw or "0.0167" in raw or "0.01667" in raw
                checks.append({"name": "Bonferroni correction applied",
                                "passed": passed,
                                "detail": "Searched for alpha/3 ≈ 0.01667 in output; "
                                          + ("found" if passed else "not found")})
    else:
        checks.append({"name": "Bonferroni correction applied", "passed": False,
                        "detail": "Cannot check — experiment_analysis.json missing"})

    # ─── CHECK 3: Sample Ratio Mismatch flagged for diabetic_patients segment ──
    if exp_path:
        data, err = load_json(exp_path, "experiment_analysis.json")
        if err:
            checks.append({"name": "SRM flagged for diabetic_patients segment",
                            "passed": False, "detail": err})
        else:
            raw = json.dumps(data).lower()
            # The diabetic_patients segment has SRM: |3800-4025|/4025 ≈ 0.056 >> 0.01
            srm_flagged = ("srm" in raw or "sample_ratio" in raw or
                           "mismatch" in raw or "ratio_mismatch" in raw)
            diabetic_mentioned = "diabetic" in raw
            passed = srm_flagged and diabetic_mentioned
            checks.append({"name": "SRM flagged for diabetic_patients segment",
                            "passed": passed,
                            "detail": f"SRM keyword found: {srm_flagged}, diabetic mentioned: {diabetic_mentioned}"})
    else:
        checks.append({"name": "SRM flagged for diabetic_patients segment",
                        "passed": False, "detail": "experiment_analysis.json missing"})

    # ─── CHECK 4: Primary metric analysis includes lift and CI ───────────────
    if exp_path:
        data, err = load_json(exp_path, "experiment_analysis.json")
        if err:
            checks.append({"name": "Primary metric has lift and CI", "passed": False, "detail": err})
        else:
            def find_in_nested(obj, keys):
                found = set()
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if k in keys:
                            found.add(k)
                        found |= find_in_nested(v, keys)
                elif isinstance(obj, list):
                    for item in obj:
                        found |= find_in_nested(item, keys)
                return found

            found_keys = find_in_nested(data, {"lift", "ci_95", "ci", "confidence_interval",
                                                "p_value", "pvalue", "significant"})
            has_lift = "lift" in found_keys
            has_ci = bool({"ci_95", "ci", "confidence_interval"} & found_keys)
            has_pval = bool({"p_value", "pvalue"} & found_keys)
            passed = has_lift and has_ci and has_pval
            checks.append({"name": "Primary metric has lift and CI",
                            "passed": passed,
                            "detail": f"lift={has_lift}, ci={has_ci}, p_value={has_pval}"})
    else:
        checks.append({"name": "Primary metric has lift and CI", "passed": False,
                        "detail": "experiment_analysis.json missing"})

    # ─── CHECK 5: model_evaluation_report.json exists ───────────────────────
    model_path = find_file(workspace, "model_evaluation_report.json")
    if model_path is None:
        checks.append({"name": "model_evaluation_report.json exists", "passed": False,
                        "detail": "File not found anywhere in workspace"})
    else:
        checks.append({"name": "model_evaluation_report.json exists", "passed": True,
                        "detail": str(model_path)})

    # ─── CHECK 6: Model reports both AUC-ROC and AUC-PR ────────────────────
    if model_path:
        data, err = load_json(model_path, "model_evaluation_report.json")
        if err:
            checks.append({"name": "Model reports AUC-ROC and AUC-PR", "passed": False, "detail": err})
        else:
            raw = json.dumps(data).lower()
            has_roc = "roc_auc" in raw or "auc_roc" in raw or "roc-auc" in raw
            has_pr = "avg_prec" in raw or "auc_pr" in raw or "average_precision" in raw or "auc-pr" in raw
            passed = has_roc and has_pr
            checks.append({"name": "Model reports AUC-ROC and AUC-PR",
                            "passed": passed,
                            "detail": f"AUC-ROC found: {has_roc}, AUC-PR found: {has_pr}"})
    else:
        checks.append({"name": "Model reports AUC-ROC and AUC-PR", "passed": False,
                        "detail": "model_evaluation_report.json missing"})

    # ─── CHECK 7: Overfit gap reported ──────────────────────────────────────
    if model_path:
        data, err = load_json(model_path, "model_evaluation_report.json")
        if err:
            checks.append({"name": "Overfit gap reported", "passed": False, "detail": err})
        else:
            raw = json.dumps(data).lower()
            passed = "overfit" in raw or "overfit_gap" in raw or "gap" in raw
            checks.append({"name": "Overfit gap reported",
                            "passed": passed,
                            "detail": "Searched for 'overfit'/'overfit_gap'/'gap' in report"})
    else:
        checks.append({"name": "Overfit gap reported", "passed": False,
                        "detail": "model_evaluation_report.json missing"})

    # ─── CHECK 8: AUC-ROC value is plausible (between 0.55 and 0.99) ────────
    if model_path:
        data, err = load_json(model_path, "model_evaluation_report.json")
        if err:
            checks.append({"name": "AUC-ROC value is plausible", "passed": False, "detail": err})
        else:
            def extract_numeric(obj, keywords):
                """Recursively find first numeric value associated with a keyword."""
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if any(kw in k.lower() for kw in keywords):
                            if isinstance(v, (int, float)) and not isinstance(v, bool):
                                return v
                            if isinstance(v, dict) and "mean" in v:
                                return v["mean"]
                        res = extract_numeric(v, keywords)
                        if res is not None:
                            return res
                elif isinstance(obj, list):
                    for item in obj:
                        res = extract_numeric(item, keywords)
                        if res is not None:
                            return res
                return None

            roc_val = extract_numeric(data, ["roc_auc", "auc_roc", "roc-auc"])
            if roc_val is not None:
                passed = 0.55 <= float(roc_val) <= 0.99
                checks.append({"name": "AUC-ROC value is plausible",
                                "passed": passed,
                                "detail": f"AUC-ROC = {roc_val:.4f}"})
            else:
                checks.append({"name": "AUC-ROC value is plausible", "passed": False,
                                "detail": "Could not extract numeric AUC-ROC value from report"})
    else:
        checks.append({"name": "AUC-ROC value is plausible", "passed": False,
                        "detail": "model_evaluation_report.json missing"})

    # ─── CHECK 9: Cyclical time features present in processed dataset ────────
    # The agent must have applied add_time_features() producing dow_sin, dow_cos etc.
    # We check the model evaluation report or a features manifest for evidence
    features_csv = find_file(workspace, "engineered_features.csv")
    features_parquet = find_file(workspace, "engineered_features.parquet")
    features_manifest = find_file(workspace, "feature_manifest.json")
    features_report = find_file(workspace, "model_evaluation_report.json")

    time_feature_found = False
    detail_time = "No engineered_features file or manifest found"

    for candidate in [features_csv, features_parquet, features_manifest, features_report]:
        if candidate is None:
            continue
        try:
            if str(candidate).endswith(".csv"):
                import pandas as pd
                df = pd.read_csv(candidate, nrows=1)
                cols = list(df.columns)
                if any(c in cols for c in ["dow_sin", "dow_cos", "month_sin", "month_cos", "is_weekend"]):
                    time_feature_found = True
                    detail_time = f"Cyclical time features found in {candidate}"
                    break
            elif str(candidate).endswith(".parquet"):
                import pandas as pd
                df = pd.read_parquet(candidate)
                cols = list(df.columns)
                if any(c in cols for c in ["dow_sin", "dow_cos", "month_sin", "month_cos", "is_weekend"]):
                    time_feature_found = True
                    detail_time = f"Cyclical time features found in {candidate}"
                    break
            else:
                raw = candidate.read_text().lower()
                if any(feat in raw for feat in ["dow_sin", "dow_cos", "month_sin",
                                                 "month_cos", "is_weekend"]):
                    time_feature_found = True
                    detail_time = f"Cyclical time feature names found in {candidate}"
                    break
        except Exception as e:
            detail_time = f"Error reading {candidate}: {e}"
            continue

    checks.append({"name": "Cyclical time features extracted (dow_sin, dow_cos, etc.)",
                    "passed": time_feature_found,
                    "detail": detail_time})

    # ─── CHECK 10: StratifiedKFold used (5 folds) ────────────────────────────
    if model_path:
        data, err = load_json(model_path, "model_evaluation_report.json")
        if err:
            checks.append({"name": "Stratified 5-fold CV used", "passed": False, "detail": err})
        else:
            raw = json.dumps(data).lower()
            strat_found = "stratified" in raw or "stratkfold" in raw
            fold5_found = any(x in raw for x in ['"cv": 5', '"folds": 5', '"n_splits": 5',
                                                   'cv_folds": 5', '5-fold', '5 fold',
                                                   '"cv_folds": 5', '"n_folds": 5'])
            passed = strat_found or fold5_found
            checks.append({"name": "Stratified 5-fold CV used",
                            "passed": passed,
                            "detail": f"stratified={strat_found}, 5-fold={fold5_found}"})
    else:
        checks.append({"name": "Stratified 5-fold CV used", "passed": False,
                        "detail": "model_evaluation_report.json missing"})

    # ─── Scoring ─────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall = passed_count >= 7  # Must pass at least 7/10 checks

    return {"passed": overall, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))