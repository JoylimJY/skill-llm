import os
import json
import random
import hashlib
import struct
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ────────────────────────────────────────────────────────
# Simulate a Windows-like layout inside Linux paths
primary   = workspace / "primary_storage" / "Users" / "mlteam" / "AppData" / "Local" / "ollama" / "models"
secondary = workspace / "secondary_storage"
scripts   = workspace / "scripts"
logs_dir  = workspace / "logs"
config_dir = workspace / "config"

for d in [primary, secondary, scripts, logs_dir, config_dir,
          workspace / "projects" / "nlp_pipeline",
          workspace / "projects" / "cv_pipeline",
          workspace / "projects" / "data_prep",
          workspace / "tmp" / "downloads",
          workspace / "tmp" / "cache"]:
    d.mkdir(parents=True, exist_ok=True)

# ── Fake Ollama model blobs ────────────────────────────────────────────────────
# Real Ollama stores: models/blobs/sha256-<hash>  and  models/manifests/registry.ollama.ai/library/<name>/latest
models = {
    "qwen2.5:7b":   {"size_mb": 4_200, "hash_seed": 1},
    "llama3.2:3b":  {"size_mb": 2_100, "hash_seed": 2},
    "mistral:7b":   {"size_mb": 4_100, "hash_seed": 3},
}

blobs_dir     = primary / "blobs"
manifests_dir = primary / "manifests" / "registry.ollama.ai" / "library"
blobs_dir.mkdir(parents=True, exist_ok=True)

for model_name, info in models.items():
    name, tag = model_name.split(":")
    manifest_model_dir = manifests_dir / name
    manifest_model_dir.mkdir(parents=True, exist_ok=True)

    # Create blob file (small representative size for testing, ~50KB each)
    rng = random.Random(info["hash_seed"])
    blob_content = bytes([rng.randint(0, 255) for _ in range(51_200)])
    blob_hash = hashlib.sha256(blob_content).hexdigest()
    blob_file = blobs_dir / f"sha256-{blob_hash}"
    blob_file.write_bytes(blob_content)

    # Create manifest JSON
    manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {"digest": f"sha256-{blob_hash}", "size": len(blob_content)},
        "layers": [{"digest": f"sha256-{blob_hash}", "size": len(blob_content), "mediaType": "application/vnd.ollama.image.model"}],
        "model_name": model_name,
        "size_mb_actual": info["size_mb"]
    }
    (manifest_model_dir / "latest").write_text(json.dumps(manifest, indent=2))

# ── Distractor files ───────────────────────────────────────────────────────────
distractors = [
    (workspace / "projects" / "nlp_pipeline" / "train.py",           "# NLP training script\nimport torch\n"),
    (workspace / "projects" / "nlp_pipeline" / "requirements.txt",   "torch\ntransformers\n"),
    (workspace / "projects" / "cv_pipeline"  / "infer.py",           "# CV inference\nimport cv2\n"),
    (workspace / "projects" / "data_prep"    / "preprocess.py",      "# data preprocessing\n"),
    (workspace / "projects" / "data_prep"    / "config.yaml",        "batch_size: 32\nworkers: 4\n"),
    (workspace / "tmp" / "downloads"         / "model_card.txt",     "Model: qwen2.5 – Apache 2.0\n"),
    (workspace / "tmp" / "cache"             / "index.json",         '{"version":1,"entries":[]}\n'),
    (workspace / "config"                    / "app_settings.json",  json.dumps({"theme":"dark","lang":"zh-CN"}, indent=2)),
    (workspace / "logs"                      / "old_training.log",   "epoch 1 loss=2.34\nepoch 2 loss=1.98\n"),
    (workspace / "logs"                      / "deploy.log",         "2024-01-10 service started\n"),
    (workspace / "secondary_storage"         / "README_storage.txt", "Secondary storage partition – 2TB SSD\nMounted at /workspace/secondary_storage\n"),
]
for path, content in distractors:
    path.write_text(content)

# ── Ollama service state file (simulates a running/stopped service) ────────────
service_state = {
    "status": "running",
    "pid": 12345,
    "port": 11434
}
(workspace / "config" / "ollama_service_state.json").write_text(json.dumps(service_state, indent=2))

# ── Write the primary storage location config (what check script reads) ────────
location_config = {
    "OLLAMA_MODELS_DEFAULT": str(primary),
    "platform": "linux-simulated",
    "note": "Simulated Windows C-drive primary storage path"
}
(workspace / "config" / "storage_location.json").write_text(json.dumps(location_config, indent=2))

# ── scripts/check_ollama_status.py ────────────────────────────────────────────
check_script = r'''#!/usr/bin/env python3
"""
check_ollama_status.py - Checks current Ollama model storage location and disk usage.
Reads from config/storage_location.json and scans models directory.
"""
import json, os, sys
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
CONFIG    = WORKSPACE / "config" / "storage_location.json"
SVC_STATE = WORKSPACE / "config" / "ollama_service_state.json"

def main():
    if not CONFIG.exists():
        print("[ERROR] storage_location.json not found.")
        sys.exit(1)

    cfg = json.loads(CONFIG.read_text())
    models_path = Path(cfg["OLLAMA_MODELS_DEFAULT"])
    svc = json.loads(SVC_STATE.read_text()) if SVC_STATE.exists() else {"status": "unknown"}

    print(f"=== Ollama Status Check ===")
    print(f"Service status : {svc.get('status','unknown')}")
    print(f"Models location: {models_path}")

    if not models_path.exists():
        print("[WARN] Models directory does not exist.")
        return

    blobs_dir = models_path / "blobs"
    manifests_dir = models_path / "manifests"

    # Count models
    model_list = []
    if manifests_dir.exists():
        for lib_dir in (manifests_dir / "registry.ollama.ai" / "library").iterdir():
            for tag_file in lib_dir.iterdir():
                manifest = json.loads(tag_file.read_text())
                model_list.append({
                    "name": manifest.get("model_name", lib_dir.name + ":" + tag_file.name),
                    "size_mb": manifest.get("size_mb_actual", 0)
                })

    total_mb = sum(m["size_mb"] for m in model_list)
    print(f"\nModels found ({len(model_list)}):")
    for m in model_list:
        print(f"  {m['name']:30s}  {m['size_mb']:,} MB")
    print(f"\nTotal model storage: {total_mb:,} MB ({total_mb/1024:.1f} GB)")

    # Check actual disk usage of blob files
    blob_bytes = sum(f.stat().st_size for f in blobs_dir.iterdir()) if blobs_dir.exists() else 0
    print(f"Actual blob data : {blob_bytes:,} bytes")

    # Save status report
    report = {
        "service_status": svc.get("status"),
        "models_location": str(models_path),
        "model_count": len(model_list),
        "models": model_list,
        "total_size_mb": total_mb,
        "blob_bytes": blob_bytes
    }
    report_path = WORKSPACE / "logs" / "status_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\nStatus report saved to: {report_path}")

if __name__ == "__main__":
    main()
'''
(scripts / "check_ollama_status.py").write_text(check_script)

# ── scripts/migrate_ollama.py ──────────────────────────────────────────────────
migrate_script = r'''#!/usr/bin/env python3
"""
migrate_ollama.py - Safely migrates Ollama model storage to a new location.

Usage:
  python scripts/migrate_ollama.py --target <destination_path>
  python scripts/migrate_ollama.py --cleanup

Safety rules enforced:
  1. Ollama service MUST be stopped before migration starts.
  2. Target disk must have sufficient free space.
  3. All blobs are copied with SHA256 integrity verification.
  4. Source files are preserved until --cleanup is explicitly called.
  5. --cleanup is blocked unless verify_ollama.py has been run and passed.
  6. Sets OLLAMA_MODELS environment variable in workspace/.env_config after migration.
"""
import argparse, json, shutil, hashlib, sys, time
from pathlib import Path

WORKSPACE   = Path(__file__).parent.parent
CONFIG      = WORKSPACE / "config" / "storage_location.json"
SVC_STATE   = WORKSPACE / "config" / "ollama_service_state.json"
ENV_CONFIG  = WORKSPACE / ".env_config"
MIG_LOG     = WORKSPACE / "logs" / "migration_log.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def load_service_state():
    if SVC_STATE.exists():
        return json.loads(SVC_STATE.read_text())
    return {"status": "unknown"}

def save_service_state(state: dict):
    SVC_STATE.write_text(json.dumps(state, indent=2))

def stop_service():
    """Simulate stopping Ollama service."""
    state = load_service_state()
    if state.get("status") == "stopped":
        print("[INFO] Ollama service is already stopped.")
        return True
    print("[ACTION] Stopping Ollama service...")
    time.sleep(0.2)
    state["status"] = "stopped"
    state.pop("pid", None)
    save_service_state(state)
    print("[OK] Ollama service stopped.")
    return True

def do_migrate(target: Path):
    cfg = json.loads(CONFIG.read_text())
    source = Path(cfg["OLLAMA_MODELS_DEFAULT"])

    print(f"\n=== Migration Plan ===")
    print(f"  Source : {source}")
    print(f"  Target : {target}")

    # RULE 1: Service must be stopped
    svc = load_service_state()
    if svc.get("status") != "stopped":
        print(f"\n[ERROR] Ollama service is still {svc.get('status')}.")
        print("        You must stop the service before migrating.")
        print("        Run with --stop-service flag or stop it manually first.")
        sys.exit(1)

    # RULE 2: Check target space (simulated – always passes here)
    target.mkdir(parents=True, exist_ok=True)

    # RULE 3: Copy all files with integrity verification
    print("\n[ACTION] Copying model files with integrity verification...")
    copied_files = []
    errors = []

    for src_file in source.rglob("*"):
        if src_file.is_file():
            rel = src_file.relative_to(source)
            dst_file = target / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            # Verify
            src_hash = sha256_file(src_file)
            dst_hash = sha256_file(dst_file)
            if src_hash != dst_hash:
                errors.append(str(rel))
                print(f"  [FAIL] Integrity check failed: {rel}")
            else:
                copied_files.append(str(rel))
                print(f"  [OK]   {rel}")

    if errors:
        print(f"\n[ERROR] {len(errors)} file(s) failed integrity check. Aborting.")
        sys.exit(1)

    # RULE 4: Set OLLAMA_MODELS env variable in .env_config
    env_lines = []
    if ENV_CONFIG.exists():
        env_lines = [l for l in ENV_CONFIG.read_text().splitlines() if not l.startswith("OLLAMA_MODELS=")]
    env_lines.append(f"OLLAMA_MODELS={target}")
    ENV_CONFIG.write_text("\n".join(env_lines) + "\n")
    print(f"\n[OK] Set OLLAMA_MODELS={target} in {ENV_CONFIG}")

    # Write migration log
    log = {
        "status": "migrated_pending_verification",
        "source": str(source),
        "target": str(target),
        "copied_files": copied_files,
        "file_count": len(copied_files),
        "verified_by_migrate": True,
        "verified_by_verify_script": False,
        "cleanup_done": False,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    MIG_LOG.write_text(json.dumps(log, indent=2))

    print(f"\n[OK] Migration complete. {len(copied_files)} file(s) copied.")
    print(f"     Source files PRESERVED at: {source}")
    print(f"     Run 'python scripts/verify_ollama.py' to validate before cleanup.")
    print(f"     Migration log: {MIG_LOG}")

def do_cleanup():
    """Remove source files. Blocked unless verify script has confirmed success."""
    if not MIG_LOG.exists():
        print("[ERROR] No migration log found. Run --target first.")
        sys.exit(1)

    log = json.loads(MIG_LOG.read_text())

    # RULE 5: Cleanup blocked until verification
    if not log.get("verified_by_verify_script", False):
        print("[ERROR] Cleanup blocked: verify_ollama.py has not confirmed migration success.")
        print("        Run 'python scripts/verify_ollama.py' first, then retry --cleanup.")
        sys.exit(1)

    source = Path(log["source"])
    print(f"[ACTION] Removing source files at: {source}")
    shutil.rmtree(source, ignore_errors=True)
    log["cleanup_done"] = True
    log["status"] = "migration_complete"
    MIG_LOG.write_text(json.dumps(log, indent=2))
    print("[OK] Source files removed. Migration fully complete.")

def main():
    parser = argparse.ArgumentParser(description="Ollama model migrator")
    parser.add_argument("--target",        type=Path, help="Target path for model storage")
    parser.add_argument("--stop-service",  action="store_true", help="Stop Ollama service before migration")
    parser.add_argument("--cleanup",       action="store_true", help="Remove source files after verified migration")
    args = parser.parse_args()

    if args.stop_service:
        stop_service()
        if not args.target and not args.cleanup:
            return

    if args.target:
        # Auto-stop service if still running
        svc = load_service_state()
        if svc.get("status") != "stopped":
            print("[INFO] Auto-stopping service before migration...")
            stop_service()
        do_migrate(args.target)
    elif args.cleanup:
        do_cleanup()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''
(scripts / "migrate_ollama.py").write_text(migrate_script)

# ── scripts/verify_ollama.py ───────────────────────────────────────────────────
verify_script = r'''#!/usr/bin/env python3
"""
verify_ollama.py - Verifies migrated Ollama models are intact and accessible.
Reads .env_config for OLLAMA_MODELS path and validates model manifests.
Updates migration_log.json upon success.
"""
import json, hashlib, sys
from pathlib import Path

WORKSPACE  = Path(__file__).parent.parent
ENV_CONFIG = WORKSPACE / ".env_config"
MIG_LOG    = WORKSPACE / "logs" / "migration_log.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def get_ollama_models_path() -> Path:
    if not ENV_CONFIG.exists():
        print("[ERROR] .env_config not found. Run migrate_ollama.py --target first.")
        sys.exit(1)
    for line in ENV_CONFIG.read_text().splitlines():
        if line.startswith("OLLAMA_MODELS="):
            return Path(line.split("=", 1)[1].strip())
    print("[ERROR] OLLAMA_MODELS not set in .env_config.")
    sys.exit(1)

def main():
    models_path = get_ollama_models_path()
    print(f"=== Verifying models at: {models_path} ===")

    if not models_path.exists():
        print("[FAIL] Target models path does not exist!")
        sys.exit(1)

    manifests_dir = models_path / "manifests" / "registry.ollama.ai" / "library"
    blobs_dir     = models_path / "blobs"

    model_list = []
    errors = []

    if not manifests_dir.exists():
        print("[FAIL] Manifests directory missing at target.")
        sys.exit(1)

    for lib_dir in manifests_dir.iterdir():
        for tag_file in lib_dir.iterdir():
            try:
                manifest = json.loads(tag_file.read_text())
                blob_digest = manifest["config"]["digest"]
                blob_file = blobs_dir / blob_digest
                if not blob_file.exists():
                    errors.append(f"Missing blob: {blob_digest}")
                    continue
                # Verify blob integrity
                actual_hash = "sha256-" + sha256_file(blob_file)
                if actual_hash != blob_digest:
                    errors.append(f"Hash mismatch for {blob_digest}")
                else:
                    model_list.append(manifest.get("model_name", lib_dir.name))
                    print(f"  [OK] {manifest.get('model_name', lib_dir.name)}")
            except Exception as e:
                errors.append(str(e))

    if errors:
        print(f"\n[FAIL] Verification errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"\n[OK] All {len(model_list)} models verified successfully.")
    print(f"     Models: {', '.join(model_list)}")

    # Update migration log
    if MIG_LOG.exists():
        log = json.loads(MIG_LOG.read_text())
        log["verified_by_verify_script"] = True
        log["verified_models"] = model_list
        log["status"] = "verified_ready_for_cleanup"
        MIG_LOG.write_text(json.dumps(log, indent=2))
        print(f"\n[OK] Migration log updated. You may now run --cleanup to free source storage.")
    else:
        print("[WARN] No migration log found; skipping log update.")

if __name__ == "__main__":
    main()
'''
(scripts / "verify_ollama.py").write_text(verify_script)

print("Workspace generated successfully.")
print(f"Primary storage : {primary}")
print(f"Secondary storage: {secondary}")
print(f"Scripts created  : {list(scripts.iterdir())}")