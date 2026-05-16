#!/usr/bin/env python3
"""
Evaluation script for the Ollama model migration task.
Checks that the agent correctly:
  1. Ran check_ollama_status.py (status_report.json exists and is valid)
  2. Migrated models to the correct secondary_storage target path
  3. Set OLLAMA_MODELS in .env_config pointing to the correct new location
  4. Ran verify_ollama.py (migration_log shows verified_by_verify_script=True)
  5. Ran --cleanup (source files removed, cleanup_done=True in log)
  6. Did NOT run cleanup before verification (enforced by state machine, but we check log order)
  7. All 3 model blobs exist at the target location with correct directory structure
"""
import json
import sys
import hashlib
from pathlib import Path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []

    # ── Helper ────────────────────────────────────────────────────────────────
    def add(name, passed, detail=""):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
        return bool(passed)

    # ── Check 1: Status report was generated ──────────────────────────────────
    try:
        status_report = ws / "logs" / "status_report.json"
        if not status_report.exists():
            add("status_report_generated", False, "logs/status_report.json not found; check_ollama_status.py was not run")
        else:
            report = json.loads(status_report.read_text())
            ok = (report.get("model_count", 0) == 3
                  and report.get("total_size_mb", 0) > 0
                  and "models_location" in report)
            add("status_report_generated", ok,
                f"model_count={report.get('model_count')}, total_size_mb={report.get('total_size_mb')}")
    except Exception as e:
        add("status_report_generated", False, f"Exception: {e}")

    # ── Check 2: Migration log exists and shows migration happened ─────────────
    try:
        mig_log_path = ws / "logs" / "migration_log.json"
        if not mig_log_path.exists():
            add("migration_log_exists", False, "logs/migration_log.json not found; migrate_ollama.py was not run")
            mig_log = {}
        else:
            mig_log = json.loads(mig_log_path.read_text())
            add("migration_log_exists", True, f"status={mig_log.get('status')}")
    except Exception as e:
        add("migration_log_exists", False, f"Exception: {e}")
        mig_log = {}

    # ── Check 3: Target path is inside secondary_storage ─────────────────────
    try:
        target_str = mig_log.get("target", "")
        target_path = Path(target_str) if target_str else None
        secondary = ws / "secondary_storage"
        correct_target = (
            target_path is not None
            and secondary in target_path.parents or target_path == secondary
            or str(target_path).startswith(str(secondary))
        )
        add("target_in_secondary_storage", correct_target,
            f"target='{target_str}', secondary='{secondary}'")
    except Exception as e:
        add("target_in_secondary_storage", False, f"Exception: {e}")

    # ── Check 4: OLLAMA_MODELS set correctly in .env_config ───────────────────
    try:
        env_config = ws / ".env_config"
        if not env_config.exists():
            add("env_config_ollama_models_set", False, ".env_config not found")
        else:
            env_content = env_config.read_text()
            ollama_models_line = None
            for line in env_content.splitlines():
                if line.startswith("OLLAMA_MODELS="):
                    ollama_models_line = line
                    break
            if ollama_models_line is None:
                add("env_config_ollama_models_set", False,
                    "OLLAMA_MODELS not found in .env_config")
            else:
                env_target = Path(ollama_models_line.split("=", 1)[1].strip())
                secondary  = ws / "secondary_storage"
                env_ok = str(env_target).startswith(str(secondary))
                add("env_config_ollama_models_set", env_ok,
                    f"OLLAMA_MODELS={env_target}")
    except Exception as e:
        add("env_config_ollama_models_set", False, f"Exception: {e}")

    # ── Check 5: Model files exist at target with correct structure ────────────
    try:
        target_str = mig_log.get("target", "")
        target_path = Path(target_str) if target_str else None
        if target_path is None or not target_path.exists():
            add("model_files_at_target", False, f"Target path missing: {target_str}")
        else:
            blobs_dir     = target_path / "blobs"
            manifests_dir = target_path / "manifests" / "registry.ollama.ai" / "library"

            blobs_ok      = blobs_dir.exists() and any(blobs_dir.iterdir())
            manifests_ok  = manifests_dir.exists() and any(manifests_dir.iterdir())

            # Count manifests
            model_count = 0
            if manifests_dir.exists():
                for lib_dir in manifests_dir.iterdir():
                    if lib_dir.is_dir():
                        model_count += sum(1 for _ in lib_dir.iterdir())

            add("model_files_at_target", blobs_ok and manifests_ok and model_count == 3,
                f"blobs={blobs_ok}, manifests={manifests_ok}, model_count={model_count}")
    except Exception as e:
        add("model_files_at_target", False, f"Exception: {e}")

    # ── Check 6: Blob integrity at target ─────────────────────────────────────
    try:
        target_str  = mig_log.get("target", "")
        target_path = Path(target_str) if target_str else None
        blobs_dir   = target_path / "blobs" if target_path else None
        if blobs_dir is None or not blobs_dir.exists():
            add("blob_integrity_at_target", False, "Blobs directory missing at target")
        else:
            all_ok = True
            details = []
            for blob_file in blobs_dir.iterdir():
                expected_hash = blob_file.name.replace("sha256-", "")
                actual_hash   = sha256_file(blob_file)
                if actual_hash != expected_hash:
                    all_ok = False
                    details.append(f"FAIL: {blob_file.name}")
                else:
                    details.append(f"OK: {blob_file.name[:20]}...")
            add("blob_integrity_at_target", all_ok, "; ".join(details))
    except Exception as e:
        add("blob_integrity_at_target", False, f"Exception: {e}")

    # ── Check 7: verify_ollama.py was run (migration log updated) ─────────────
    try:
        verified = mig_log.get("verified_by_verify_script", False)
        verified_models = mig_log.get("verified_models", [])
        add("verify_script_was_run", verified and len(verified_models) == 3,
            f"verified={verified}, verified_models={verified_models}")
    except Exception as e:
        add("verify_script_was_run", False, f"Exception: {e}")

    # ── Check 8: Cleanup was performed (source files removed) ─────────────────
    try:
        cleanup_done = mig_log.get("cleanup_done", False)
        source_str   = mig_log.get("source", "")
        source_path  = Path(source_str) if source_str else None
        source_gone  = (source_path is not None and not source_path.exists())

        # Final status in log should be "migration_complete"
        final_status = mig_log.get("status", "")
        add("cleanup_completed", cleanup_done and source_gone and final_status == "migration_complete",
            f"cleanup_done={cleanup_done}, source_exists={source_path.exists() if source_path else 'N/A'}, status={final_status}")
    except Exception as e:
        add("cleanup_completed", False, f"Exception: {e}")

    # ── Check 9: Correct sequential ordering (cleanup only after verify) ───────
    try:
        # If cleanup_done is True but verified_by_verify_script is False → wrong order
        cleanup_done = mig_log.get("cleanup_done", False)
        verified     = mig_log.get("verified_by_verify_script", False)
        if cleanup_done and not verified:
            add("correct_workflow_order", False,
                "Cleanup was done before verification – safety rules violated")
        else:
            add("correct_workflow_order", True,
                "Verification completed before cleanup (correct order)")
    except Exception as e:
        add("correct_workflow_order", False, f"Exception: {e}")

    # ── Score ──────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total        = len(checks)
    score        = round(passed_count / total, 3)
    all_passed   = passed_count == total

    result = {
        "passed": all_passed,
        "score":  score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "workspace path argument missing"}
        ]}))
        sys.exit(1)
    evaluate(sys.argv[1])