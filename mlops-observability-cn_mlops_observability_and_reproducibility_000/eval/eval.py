import sys
import json
import os
import subprocess
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    weights = {}

    # ─── Helper ────────────────────────────────────────────────────────────────
    def add(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score
        if passed:
            total_score += weight
        weights[name] = weight

    total_weight = 0.0

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 1: Reproducibility — triple seed pattern (weight 1.5 each)
    # ══════════════════════════════════════════════════════════════════════════
    train_script = ws / "src" / "train.py"
    script_text = ""
    try:
        script_text = train_script.read_text()
    except Exception as e:
        add("train_script_readable", False, f"Cannot read src/train.py: {e}", 1.0)
        total_weight += 1.0

    if script_text:
        # Check random.seed(42)
        import re
        has_random_seed = bool(re.search(r'random\.seed\s*\(\s*42\s*\)', script_text))
        add("seed_random_42", has_random_seed,
            "random.seed(42) found in train.py" if has_random_seed else "MISSING: random.seed(42) not found in train.py",
            1.5)
        total_weight += 1.5

        # Check np.random.seed(42)
        has_np_seed = bool(re.search(r'np\.random\.seed\s*\(\s*42\s*\)', script_text))
        add("seed_numpy_42", has_np_seed,
            "np.random.seed(42) found in train.py" if has_np_seed else "MISSING: np.random.seed(42) not found in train.py",
            1.5)
        total_weight += 1.5

        # Check torch.manual_seed(42)
        has_torch_seed = bool(re.search(r'torch\.manual_seed\s*\(\s*42\s*\)', script_text))
        add("seed_torch_42", has_torch_seed,
            "torch.manual_seed(42) found in train.py" if has_torch_seed else "MISSING: torch.manual_seed(42) not found in train.py",
            1.5)
        total_weight += 1.5

        # Check git commit tracking via gitpython pattern
        has_git_hexsha = bool(re.search(r'git\.Repo\s*\(', script_text) and re.search(r'hexsha', script_text))
        add("git_commit_code", has_git_hexsha,
            "gitpython Repo().head.commit.hexsha pattern found" if has_git_hexsha else "MISSING: git.Repo()/hexsha pattern not in train.py",
            1.5)
        total_weight += 1.5

        # Check mlflow.log_param("git_commit", ...) call
        has_git_param = bool(re.search(r'log_param\s*\(\s*["\']git_commit["\']', script_text))
        add("mlflow_git_commit_param", has_git_param,
            'mlflow.log_param("git_commit", ...) call found' if has_git_param else 'MISSING: log_param("git_commit", ...) not found',
            2.0)
        total_weight += 2.0

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 2: MLflow experiment run was actually executed
    # ══════════════════════════════════════════════════════════════════════════
    mlruns_dir = None
    # Search for mlruns anywhere under workspace
    candidates = list(ws.rglob("mlruns"))
    mlruns_dir = next((p for p in candidates if p.is_dir()), None)

    add("mlruns_exists", mlruns_dir is not None,
        f"mlruns directory found at {mlruns_dir}" if mlruns_dir else "MISSING: no mlruns/ directory found anywhere under workspace",
        2.0)
    total_weight += 2.0

    run_meta_found = False
    accuracy_logged = False
    loss_logged = False
    git_commit_logged = False
    model_artifact_found = False

    if mlruns_dir:
        # Find all run meta.yaml files
        meta_files = list(mlruns_dir.rglob("meta.yaml"))
        # Filter to actual run directories (they live under experiment_id/run_id/)
        run_metas = [m for m in meta_files if m.parent.parent.parent.name == "mlruns" or
                     len(m.parts) >= 4]  # loose check

        # Also scan for params and metrics directories
        param_files = list(mlruns_dir.rglob("params/git_commit"))
        git_commit_logged = len(param_files) > 0
        add("mlflow_git_commit_logged", git_commit_logged,
            f"git_commit param file found: {param_files[0]}" if git_commit_logged else "MISSING: no mlflow param file named 'git_commit' found",
            2.0)
        total_weight += 2.0

        # Check if the git_commit value is a real 40-char hex sha
        if git_commit_logged:
            try:
                gc_val = param_files[0].read_text().strip()
                is_valid_sha = bool(re.match(r'^[0-9a-f]{40}$', gc_val))
                add("mlflow_git_commit_is_sha", is_valid_sha,
                    f"git_commit value '{gc_val}' is valid 40-char hex SHA" if is_valid_sha else f"git_commit value '{gc_val}' is NOT a valid SHA",
                    1.5)
                total_weight += 1.5
            except Exception as ex:
                add("mlflow_git_commit_is_sha", False, f"Error reading git_commit param: {ex}", 1.5)
                total_weight += 1.5

        accuracy_files = list(mlruns_dir.rglob("metrics/accuracy"))
        accuracy_logged = len(accuracy_files) > 0
        add("mlflow_accuracy_metric", accuracy_logged,
            f"accuracy metric logged: {accuracy_files[0]}" if accuracy_logged else "MISSING: no 'accuracy' metric file in mlruns",
            2.0)
        total_weight += 2.0

        loss_files = list(mlruns_dir.rglob("metrics/loss")) + list(mlruns_dir.rglob("metrics/log_loss"))
        loss_logged = len(loss_files) > 0
        add("mlflow_loss_metric", loss_logged,
            f"loss metric logged: {loss_files[0]}" if loss_logged else "MISSING: no 'loss' or 'log_loss' metric file in mlruns",
            1.5)
        total_weight += 1.5

        # Check for model artifact (any pickle / mlmodel file inside artifacts)
        artifact_files = list(mlruns_dir.rglob("MLmodel")) + list(mlruns_dir.rglob("*.pkl"))
        model_artifact_found = len(artifact_files) > 0
        add("mlflow_model_artifact", model_artifact_found,
            f"model artifact found: {artifact_files[0]}" if model_artifact_found else "MISSING: no MLmodel or .pkl artifact in mlruns",
            2.0)
        total_weight += 2.0

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 3: Evidently drift report saved as drift_report.json
    # ══════════════════════════════════════════════════════════════════════════
    drift_files = list(ws.rglob("drift_report.json"))
    drift_file = drift_files[0] if drift_files else None

    add("drift_report_exists", drift_file is not None,
        f"drift_report.json found at {drift_file}" if drift_file else "MISSING: no drift_report.json found anywhere under workspace",
        2.5)
    total_weight += 2.5

    if drift_file:
        try:
            drift_data = json.loads(drift_file.read_text())
            # Evidently JSON output should contain "metrics" key with drift analysis
            has_metrics = "metrics" in drift_data
            add("drift_report_has_metrics", has_metrics,
                "drift_report.json contains 'metrics' key" if has_metrics else "drift_report.json missing 'metrics' key — not a valid Evidently report",
                2.0)
            total_weight += 2.0

            # Check that DataDriftTable results are present (look for 'DataDriftTable' or 'data_drift' in JSON string)
            drift_str = json.dumps(drift_data).lower()
            has_drift_table = "datadrifttable" in drift_str or "data_drift" in drift_str or "drift_share" in drift_str or "number_of_drifted_columns" in drift_str
            add("drift_report_has_drift_table", has_drift_table,
                "DataDriftTable results found in drift_report.json" if has_drift_table else "drift_report.json does not appear to contain DataDriftTable results",
                2.0)
            total_weight += 2.0

            # Verify drift was actually detected (data was designed to drift heavily)
            drift_detected = "true" in drift_str or '"dataset_drift": true' in drift_str.replace(" ", "") or "drifted" in drift_str
            add("drift_detected_in_report", drift_detected,
                "Drift detected flag found in report (expected given injected distribution shift)" if drift_detected else "WARNING: no drift detected — may indicate wrong data was used",
                1.0)
            total_weight += 1.0

        except json.JSONDecodeError as je:
            add("drift_report_valid_json", False, f"drift_report.json is not valid JSON: {je}", 2.0)
            total_weight += 2.0
        except Exception as ex:
            add("drift_report_readable", False, f"Error reading drift_report.json: {ex}", 2.0)
            total_weight += 2.0

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 4: Evidently API usage in any Python file
    # ══════════════════════════════════════════════════════════════════════════
    py_files = list(ws.rglob("*.py"))
    evidently_used = False
    drift_table_used = False
    report_run_used = False

    for pf in py_files:
        try:
            text = pf.read_text()
            if "from evidently" in text or "import evidently" in text:
                evidently_used = True
            if "DataDriftTable" in text:
                drift_table_used = True
            if re.search(r'report\.run\s*\(', text) or re.search(r'Report\s*\(', text):
                report_run_used = True
        except Exception:
            pass

    add("evidently_imported", evidently_used,
        "Evidently import found in a Python file" if evidently_used else "MISSING: no 'from evidently' or 'import evidently' found in any .py file",
        1.5)
    total_weight += 1.5

    add("DataDriftTable_used", drift_table_used,
        "DataDriftTable used in a Python file" if drift_table_used else "MISSING: DataDriftTable not found in any .py file",
        1.5)
    total_weight += 1.5

    add("evidently_report_run", report_run_used,
        "Evidently Report(...) / report.run(...) pattern found" if report_run_used else "MISSING: Evidently Report/run pattern not found",
        1.0)
    total_weight += 1.0

    # ══════════════════════════════════════════════════════════════════════════
    # Final scoring
    # ══════════════════════════════════════════════════════════════════════════
    score = round(total_score / total_weight, 4) if total_weight > 0 else 0.0
    passed = score >= 0.75 and git_commit_logged and accuracy_logged and drift_file is not None

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))