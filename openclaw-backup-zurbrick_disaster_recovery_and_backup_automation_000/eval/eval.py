#!/usr/bin/env python3
"""
Evaluator for the OpenClaw backup → verify → restore-dry-run task.

Checks:
1. Operational archive exists (tar.gz) in /workspace/backups/
2. Manifest (manifest.json) exists in /workspace/backups/
3. Manifest has correct schema: tier=operational, includes_secrets=false (operational-only field checks)
4. Secrets archive exists (*.age file) — because --include-secrets was requested
5. Manifest reflects secrets: includes_secrets=true, age_recipient set, secrets_archive set
6. Verify was run and passed (we re-run verify.sh ourselves to confirm archive integrity)
7. Restore --dry-run was executed (we check for a dry-run log file OR re-run with --dry-run and assert exit 0)
"""

import sys
import os
import json
import subprocess
import glob
from pathlib import Path

def find_newest(pattern):
    files = glob.glob(pattern, recursive=True)
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def run(cmd, **kwargs):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kwargs)

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    backups_dir = workspace / "backups"
    skill_dir = workspace / "openclaw-backup"

    checks = []
    total_score = 0.0
    max_checks = 7  # total number of scored checks

    def add_check(name, passed, detail, weight=1):
        nonlocal total_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            total_score += weight

    # ── Check 1: Operational archive exists ──────────────────────────────────
    try:
        op_archives = list(backups_dir.glob("openclaw-operational-*.tar.gz"))
        if op_archives:
            op_archive = max(op_archives, key=lambda p: p.stat().st_mtime)
            add_check(
                "operational_archive_exists",
                True,
                f"Found operational archive: {op_archive.name}"
            )
        else:
            add_check(
                "operational_archive_exists",
                False,
                f"No openclaw-operational-*.tar.gz found in {backups_dir}"
            )
            op_archive = None
    except Exception as e:
        add_check("operational_archive_exists", False, f"Exception: {e}")
        op_archive = None

    # ── Check 2: Manifest exists ──────────────────────────────────────────────
    try:
        manifest_path = backups_dir / "manifest.json"
        if manifest_path.exists():
            manifest_data = json.loads(manifest_path.read_text())
            add_check("manifest_exists", True, f"manifest.json found and parseable")
        else:
            add_check("manifest_exists", False, f"manifest.json not found in {backups_dir}")
            manifest_data = None
    except Exception as e:
        add_check("manifest_exists", False, f"Exception reading manifest: {e}")
        manifest_data = None

    # ── Check 3: Manifest has correct operational-tier fields ─────────────────
    try:
        if manifest_data is not None:
            schema_ok = manifest_data.get("schema_version") == "1.0"
            tier_ok = manifest_data.get("tier") == "operational"
            checksum_present = bool(manifest_data.get("checksum_sha256"))
            workspace_present = bool(manifest_data.get("workspace_dir"))
            all_ok = schema_ok and tier_ok and checksum_present and workspace_present
            detail = (
                f"schema_version={manifest_data.get('schema_version')}, "
                f"tier={manifest_data.get('tier')}, "
                f"checksum_present={checksum_present}, "
                f"workspace_present={workspace_present}"
            )
            add_check("manifest_operational_fields", all_ok, detail)
        else:
            add_check("manifest_operational_fields", False, "No manifest to validate")
    except Exception as e:
        add_check("manifest_operational_fields", False, f"Exception: {e}")

    # ── Check 4: Secrets archive exists (age-encrypted) ──────────────────────
    try:
        secrets_archives = list(backups_dir.glob("openclaw-secrets-*.tar.gz.age"))
        if secrets_archives:
            secrets_archive = max(secrets_archives, key=lambda p: p.stat().st_mtime)
            add_check(
                "secrets_archive_exists",
                True,
                f"Found age-encrypted secrets archive: {secrets_archive.name}"
            )
        else:
            add_check(
                "secrets_archive_exists",
                False,
                f"No openclaw-secrets-*.tar.gz.age found in {backups_dir}. "
                "The task required --include-secrets with age encryption."
            )
            secrets_archive = None
    except Exception as e:
        add_check("secrets_archive_exists", False, f"Exception: {e}")
        secrets_archive = None

    # ── Check 5: Manifest reflects secrets tier ────────────────────────────────
    try:
        if manifest_data is not None:
            inc_secrets = manifest_data.get("includes_secrets") == True
            age_recipient = bool(manifest_data.get("age_recipient"))
            secrets_field = bool(manifest_data.get("secrets_archive"))
            all_ok = inc_secrets and age_recipient and secrets_field
            detail = (
                f"includes_secrets={manifest_data.get('includes_secrets')}, "
                f"age_recipient_set={age_recipient}, "
                f"secrets_archive_field_set={secrets_field}"
            )
            add_check("manifest_secrets_fields", all_ok, detail)
        else:
            add_check("manifest_secrets_fields", False, "No manifest to validate")
    except Exception as e:
        add_check("manifest_secrets_fields", False, f"Exception: {e}")

    # ── Check 6: Verify passes (run verify.sh ourselves) ─────────────────────
    try:
        verify_script = skill_dir / "scripts" / "verify.sh"
        if op_archive and manifest_path.exists() and verify_script.exists():
            result = run(
                f"bash {verify_script} --manifest {manifest_path} --archive {op_archive}",
                timeout=30
            )
            passed = result.returncode == 0
            detail = f"verify.sh exit={result.returncode}. stdout={result.stdout[-300:].strip()}"
            add_check("verify_passes", passed, detail)
        else:
            missing = []
            if not op_archive: missing.append("operational archive")
            if not manifest_path.exists(): missing.append("manifest.json")
            if not verify_script.exists(): missing.append("verify.sh")
            add_check("verify_passes", False, f"Cannot run verify: missing {', '.join(missing)}")
    except subprocess.TimeoutExpired:
        add_check("verify_passes", False, "verify.sh timed out")
    except Exception as e:
        add_check("verify_passes", False, f"Exception running verify: {e}")

    # ── Check 7: Restore dry-run exits 0 (run restore.sh --dry-run ourselves) ─
    try:
        restore_script = skill_dir / "scripts" / "restore.sh"
        dry_run_target = workspace / "restore-dryrun-eval-tmp"
        dry_run_target.mkdir(exist_ok=True)
        if op_archive and manifest_path.exists() and restore_script.exists():
            result = run(
                f"bash {restore_script} --manifest {manifest_path} --archive {op_archive} "
                f"--dry-run --target {dry_run_target}",
                timeout=30
            )
            passed = result.returncode == 0 and "DRY-RUN" in result.stdout.upper()
            detail = (
                f"restore.sh --dry-run exit={result.returncode}. "
                f"stdout={result.stdout[-400:].strip()}"
            )
            add_check("restore_dry_run_passes", passed, detail)
        else:
            missing = []
            if not op_archive: missing.append("operational archive")
            if not manifest_path.exists(): missing.append("manifest.json")
            if not restore_script.exists(): missing.append("restore.sh")
            add_check("restore_dry_run_passes", False, f"Cannot run restore: missing {', '.join(missing)}")
    except subprocess.TimeoutExpired:
        add_check("restore_dry_run_passes", False, "restore.sh --dry-run timed out")
    except Exception as e:
        add_check("restore_dry_run_passes", False, f"Exception running restore: {e}")

    # ── Final scoring ─────────────────────────────────────────────────────────
    score = round(total_score / max_checks, 4)
    overall_passed = all(c["passed"] for c in checks)

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()