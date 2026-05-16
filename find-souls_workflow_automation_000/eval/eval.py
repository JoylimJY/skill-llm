import sys
import json
import os
import pathlib

workspace = pathlib.Path(sys.argv[1])
home = pathlib.Path.home()

checks = []

def check(name, condition, detail):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return bool(condition)

# ── Expected content constants (must match mock server) ──────────────────────
CONFUCIUS_MARKER = "Confucius Persona"
CONFUCIUS_CONTENT_SNIPPET = "ren (benevolence)"
SUN_WUKONG_MARKER = "Sun Wukong Persona"
SUN_WUKONG_CONTENT_SNIPPET = "72 transformations"
ORIGINAL_MARKER = "Default Assistant Persona"
ORIGINAL_SNIPPET = "Aria"

# ── CHECK 1: Cache was refreshed (must contain Confucius from mock server) ───
try:
    cache_path = home / ".cache" / "agent-souls" / "search.json"
    cache_data = json.loads(cache_path.read_text())
    names = [e.get("name_en", "") for e in cache_data]
    has_confucius = "Confucius" in names
    has_sun_wukong = "Sun Wukong" in names
    cache_ok = has_confucius and has_sun_wukong
    check(
        "cache_refreshed",
        cache_ok,
        f"Cache contains: {names}. Expected Confucius and Sun Wukong (from mock server, not stale data)."
    )
except Exception as e:
    check("cache_refreshed", False, f"Error reading cache: {e}")

# ── CHECK 2: .soul_backups directory exists ──────────────────────────────────
backups_dir = workspace / ".soul_backups"
check(
    "soul_backups_dir_exists",
    backups_dir.is_dir(),
    f".soul_backups/ directory {'exists' if backups_dir.is_dir() else 'does NOT exist'} at {backups_dir}"
)

# ── CHECK 3: Original backup preserved correctly ─────────────────────────────
try:
    original_backup = backups_dir / "SOUL.md.original"
    content = original_backup.read_text()
    has_original_marker = ORIGINAL_MARKER in content and ORIGINAL_SNIPPET in content
    check(
        "original_backup_correct",
        has_original_marker,
        f"SOUL.md.original {'contains' if has_original_marker else 'does NOT contain'} expected original persona content ('{ORIGINAL_MARKER}', '{ORIGINAL_SNIPPET}')."
    )
except Exception as e:
    check("original_backup_correct", False, f"Error reading SOUL.md.original: {e}")

# ── CHECK 4: Confucius backup exists with correct slug ───────────────────────
try:
    confucius_backup = backups_dir / "SOUL.md.confucius"
    content = confucius_backup.read_text()
    has_marker = CONFUCIUS_MARKER in content and CONFUCIUS_CONTENT_SNIPPET in content
    check(
        "confucius_backup_correct",
        has_marker,
        f"SOUL.md.confucius {'contains' if has_marker else 'does NOT contain'} Confucius soul content. "
        f"(Slug must be extracted from URL '/real_world/confucius/' → 'confucius')"
    )
except Exception as e:
    check("confucius_backup_correct", False, f"Error reading SOUL.md.confucius: {e}")

# ── CHECK 5: Sun Wukong backup exists with correct slug ──────────────────────
try:
    sun_wukong_backup = backups_dir / "SOUL.md.sun_wukong"
    content = sun_wukong_backup.read_text()
    has_marker = SUN_WUKONG_MARKER in content and SUN_WUKONG_CONTENT_SNIPPET in content
    check(
        "sun_wukong_backup_correct",
        has_marker,
        f"SOUL.md.sun_wukong {'contains' if has_marker else 'does NOT contain'} Sun Wukong soul content. "
        f"(Slug must be extracted from URL '/virtual_world/sun_wukong/' → 'sun_wukong')"
    )
except Exception as e:
    check("sun_wukong_backup_correct", False, f"Error reading SOUL.md.sun_wukong: {e}")

# ── CHECK 6: Original backup was NOT overwritten on second install ────────────
try:
    original_backup = backups_dir / "SOUL.md.original"
    content = original_backup.read_text()
    # It must still be the ORIGINAL content (Aria), NOT confucius or sun_wukong
    not_overwritten = (ORIGINAL_MARKER in content) and (CONFUCIUS_MARKER not in content) and (SUN_WUKONG_MARKER not in content)
    check(
        "original_not_overwritten",
        not_overwritten,
        f"SOUL.md.original must contain original persona only. "
        f"Contains original: {ORIGINAL_MARKER in content}, "
        f"Contains confucius: {CONFUCIUS_MARKER in content}, "
        f"Contains sun_wukong: {SUN_WUKONG_MARKER in content}."
    )
except Exception as e:
    check("original_not_overwritten", False, f"Error in original overwrite check: {e}")

# ── CHECK 7: Current SOUL.md is Confucius (after rollback) ──────────────────
try:
    current_soul = workspace / "SOUL.md"
    content = current_soul.read_text()
    is_confucius = CONFUCIUS_MARKER in content and CONFUCIUS_CONTENT_SNIPPET in content
    is_not_sun_wukong = SUN_WUKONG_MARKER not in content
    check(
        "current_soul_is_confucius",
        is_confucius and is_not_sun_wukong,
        f"Current SOUL.md should be Confucius (after rollback). "
        f"Has Confucius marker: {is_confucius}, Is not Sun Wukong: {is_not_sun_wukong}."
    )
except Exception as e:
    check("current_soul_is_confucius", False, f"Error reading current SOUL.md: {e}")

# ── CHECK 8: No unexpected files in .soul_backups ────────────────────────────
try:
    if backups_dir.is_dir():
        backup_files = [f.name for f in backups_dir.iterdir() if f.is_file()]
        unexpected = [f for f in backup_files if f not in ("SOUL.md.original", "SOUL.md.confucius", "SOUL.md.sun_wukong")]
        check(
            "no_unexpected_backups",
            len(unexpected) == 0,
            f"Unexpected files in .soul_backups/: {unexpected}. Expected only: SOUL.md.original, SOUL.md.confucius, SOUL.md.sun_wukong."
        )
    else:
        check("no_unexpected_backups", False, ".soul_backups/ dir missing.")
except Exception as e:
    check("no_unexpected_backups", False, f"Error checking backup files: {e}")

# ── SCORE & RESULT ────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = passed_count / total

result = {
    "passed": all(c["passed"] for c in checks),
    "score": round(score, 4),
    "checks": checks
}

print(json.dumps(result, indent=2))