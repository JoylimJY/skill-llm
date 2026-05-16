#!/usr/bin/env python3
"""
Evaluation script for Clawdbot migration task.
Checks:
1. An export archive exists in /tmp/exports with correct naming convention
2. Archive contains session transcripts (--include-sessions was used)
3. Archive does NOT contain credentials (--include-credentials was NOT used)
4. Archive does NOT contain excluded directories (node_modules, .next, dist, build, .git, etc.)
5. Import was performed to /opt/clawd-staging (custom --workspace, not default ~/clawd)
6. Imported workspace has correct structure (config, skills, whatsapp session)
7. Import used --force (import receipt shows forced=true)
8. Imported workspace does NOT contain credentials
9. Imported workspace contains session transcripts
"""

import sys
import json
import tarfile
from pathlib import Path

workspace_arg = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
total_score = 0.0

EXPORT_DIR = Path("/tmp/exports")
STAGING_DIR = Path("/opt/clawd-staging")


def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0


# ─────────────────────────────────────────────
# CHECK 1: Archive exists in /tmp/exports with correct naming
# ─────────────────────────────────────────────
try:
    archives = list(EXPORT_DIR.glob("clawdbot-export-*.tar.gz"))
    if archives:
        archive_path = archives[0]
        archive_name = archive_path.name
        # Validate naming: clawdbot-export-YYYYMMDD_HHMMSS.tar.gz
        import re
        pattern = r"^clawdbot-export-\d{8}_\d{6}\.tar\.gz$"
        name_valid = bool(re.match(pattern, archive_name))
        total_score += add_check(
            "archive_exists_correct_naming",
            name_valid,
            f"Found archive: {archive_name} — name {'matches' if name_valid else 'does NOT match'} clawdbot-export-YYYYMMDD_HHMMSS.tar.gz format"
        )
    else:
        total_score += add_check(
            "archive_exists_correct_naming",
            False,
            f"No archive found in {EXPORT_DIR} matching clawdbot-export-*.tar.gz"
        )
        archive_path = None
except Exception as e:
    total_score += add_check("archive_exists_correct_naming", False, f"Exception: {e}")
    archive_path = None

# ─────────────────────────────────────────────
# CHECK 2: Archive contains session transcripts
# ─────────────────────────────────────────────
transcripts_in_archive = False
try:
    if archive_path and archive_path.exists():
        with tarfile.open(archive_path, "r:gz") as tf:
            members = tf.getnames()
            transcripts_in_archive = any("transcript" in m for m in members)
        total_score += add_check(
            "archive_includes_sessions",
            transcripts_in_archive,
            f"Session transcripts {'found' if transcripts_in_archive else 'NOT found'} in archive. "
            f"(--include-sessions flag must be used)"
        )
    else:
        total_score += add_check("archive_includes_sessions", False, "No archive to inspect")
except Exception as e:
    total_score += add_check("archive_includes_sessions", False, f"Exception reading archive: {e}")

# ─────────────────────────────────────────────
# CHECK 3: Archive does NOT contain credentials
# ─────────────────────────────────────────────
try:
    if archive_path and archive_path.exists():
        with tarfile.open(archive_path, "r:gz") as tf:
            members = tf.getnames()
            has_credentials = any("credential" in m or "secrets.json" in m or ".env" in m.split("/")[-1] for m in members)
        total_score += add_check(
            "archive_excludes_credentials",
            not has_credentials,
            f"Credentials {'FOUND (BAD)' if has_credentials else 'correctly excluded'} from archive. "
            f"(--include-credentials must NOT be used)"
        )
    else:
        total_score += add_check("archive_excludes_credentials", False, "No archive to inspect")
except Exception as e:
    total_score += add_check("archive_excludes_credentials", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 4: Archive excludes bloat directories
# ─────────────────────────────────────────────
try:
    if archive_path and archive_path.exists():
        EXCLUDED_PATTERNS = ["node_modules", ".next", "dist", "build", ".git", ".wrangler", ".open-next", ".vercel"]
        with tarfile.open(archive_path, "r:gz") as tf:
            members = tf.getnames()
        violations = []
        for pattern in EXCLUDED_PATTERNS:
            for m in members:
                parts = Path(m).parts
                if pattern in parts:
                    violations.append(f"{pattern} found in: {m}")
                    break
        total_score += add_check(
            "archive_excludes_bloat_dirs",
            len(violations) == 0,
            f"Excluded dir violations: {violations if violations else 'none — all excluded correctly'}"
        )
    else:
        total_score += add_check("archive_excludes_bloat_dirs", False, "No archive to inspect")
except Exception as e:
    total_score += add_check("archive_excludes_bloat_dirs", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 5: Import was performed to /opt/clawd-staging (not ~/clawd)
# ─────────────────────────────────────────────
try:
    staging_exists = STAGING_DIR.exists() and STAGING_DIR.is_dir()
    # It must have actual content (more than just being an empty dir)
    staging_files = list(STAGING_DIR.rglob("*")) if staging_exists else []
    staging_has_content = len(staging_files) > 3
    
    home_clawd = Path.home() / "clawd"
    default_imported = home_clawd.exists() and (home_clawd / "clawdbot.json").exists()
    
    total_score += add_check(
        "import_to_custom_workspace",
        staging_has_content and not default_imported,
        f"Staging dir {STAGING_DIR}: exists={staging_exists}, files={len(staging_files)}. "
        f"Default ~/clawd imported: {default_imported} (should be False — custom --workspace must be used)"
    )
except Exception as e:
    total_score += add_check("import_to_custom_workspace", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 6: Imported workspace has correct core structure
# ─────────────────────────────────────────────
try:
    config_path = STAGING_DIR / "clawdbot.json"
    skills_dir = STAGING_DIR / "skills"
    whatsapp_dir = STAGING_DIR / "whatsapp"
    
    has_config = config_path.exists()
    has_skills = skills_dir.exists() and len(list(skills_dir.iterdir())) > 0
    has_whatsapp = whatsapp_dir.exists()
    
    config_valid = False
    if has_config:
        try:
            cfg = json.loads(config_path.read_text())
            config_valid = cfg.get("instanceId") == "cust-support-prod-7f3a"
        except:
            pass

    structure_ok = has_config and has_skills and has_whatsapp and config_valid
    total_score += add_check(
        "imported_workspace_structure",
        structure_ok,
        f"config={has_config}(valid={config_valid}), skills={has_skills}, whatsapp={has_whatsapp}"
    )
except Exception as e:
    total_score += add_check("imported_workspace_structure", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 7: Import used --force (import receipt shows forced=true)
# ─────────────────────────────────────────────
try:
    receipt_path = STAGING_DIR / ".import-receipt.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        forced = receipt.get("forced", False)
        total_score += add_check(
            "import_used_force_flag",
            forced is True,
            f"Import receipt forced={forced}. (--force flag must be used for non-interactive migration)"
        )
    else:
        total_score += add_check(
            "import_used_force_flag",
            False,
            f"Import receipt not found at {receipt_path} — import may not have been performed or --force not used"
        )
except Exception as e:
    total_score += add_check("import_used_force_flag", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 8: Imported workspace does NOT contain credentials
# ─────────────────────────────────────────────
try:
    cred_dir = STAGING_DIR / "credentials"
    secrets_file = STAGING_DIR / "credentials" / "secrets.json"
    env_file = STAGING_DIR / "credentials" / ".env"
    
    has_creds = cred_dir.exists() and (secrets_file.exists() or env_file.exists())
    total_score += add_check(
        "imported_workspace_no_credentials",
        not has_creds,
        f"Credentials directory in imported workspace: {'FOUND (BAD)' if has_creds else 'correctly absent'}"
    )
except Exception as e:
    total_score += add_check("imported_workspace_no_credentials", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# CHECK 9: Imported workspace contains session transcripts
# ─────────────────────────────────────────────
try:
    transcripts_dir = STAGING_DIR / "transcripts"
    transcript_files = list(transcripts_dir.rglob("*.json")) if transcripts_dir.exists() else []
    has_transcripts = len(transcript_files) >= 5  # We created 8 transcript files
    total_score += add_check(
        "imported_workspace_has_transcripts",
        has_transcripts,
        f"Transcript files in imported workspace: {len(transcript_files)} "
        f"({'sufficient' if has_transcripts else 'insufficient — --include-sessions required'})"
    )
except Exception as e:
    total_score += add_check("imported_workspace_has_transcripts", False, f"Exception: {e}")

# ─────────────────────────────────────────────
# Final scoring
# ─────────────────────────────────────────────
num_checks = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
final_score = total_score / num_checks if num_checks > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": round(final_score, 4),
    "checks": checks
}

print(json.dumps(result, indent=2))