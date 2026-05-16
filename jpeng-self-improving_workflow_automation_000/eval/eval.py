import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
si_dir = Path.home() / "self-improving"

checks = []
score_total = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global score_total, max_score
    max_score += weight
    if passed:
        score_total += weight

# ── Load task metadata ────────────────────────────────────────────────────
try:
    meta = json.loads((workspace / ".task_meta.json").read_text())
    now = datetime.fromisoformat(meta["now_iso"])
except Exception as e:
    add_check("load_task_meta", False, f"Could not load .task_meta.json: {e}", 0.1)
    now = datetime.now()

# ─────────────────────────────────────────────────────────────────────────
# CHECK 1: corrections.md — last 50 limit enforced
# ─────────────────────────────────────────────────────────────────────────
try:
    corr_path = si_dir / "corrections.md"
    assert corr_path.exists(), "corrections.md missing"
    corr_text = corr_path.read_text()
    # Count non-empty, non-header lines that look like correction entries
    entries = [l for l in corr_text.splitlines() if l.strip() and not l.startswith("#")]
    passed = len(entries) <= 50
    add_check(
        "corrections_max_50",
        passed,
        f"corrections.md has {len(entries)} non-header entries (limit: 50). {'OK' if passed else 'EXCEEDS LIMIT'}",
        weight=1.5
    )
except Exception as e:
    add_check("corrections_max_50", False, f"Exception: {e}", 1.5)

# ─────────────────────────────────────────────────────────────────────────
# CHECK 2: corrections.md — contains new corrections from session log
# ─────────────────────────────────────────────────────────────────────────
try:
    corr_text = (si_dir / "corrections.md").read_text().lower()
    has_new_corrections = (
        "indentation" in corr_text or
        "spaces" in corr_text or
        "tabs" in corr_text or
        "4-space" in corr_text
    )
    add_check(
        "corrections_new_entries_present",
        has_new_corrections,
        "New corrections from session_log.txt (indentation pattern) found in corrections.md" if has_new_corrections
        else "No new corrections from session_log.txt found in corrections.md",
        weight=1.5
    )
except Exception as e:
    add_check("corrections_new_entries_present", False, f"Exception: {e}", 1.5)

# ─────────────────────────────────────────────────────────────────────────
# CHECK 3: memory.md — HOT tier ≤ 100 lines
# ─────────────────────────────────────────────────────────────────────────
try:
    mem_path = si_dir / "memory.md"
    assert mem_path.exists(), "memory.md missing"
    mem_lines = mem_path.read_text().splitlines()
    passed = len(mem_lines) <= 100
    add_check(
        "memory_md_max_100_lines",
        passed,
        f"memory.md has {len(mem_lines)} lines (limit: 100). {'OK' if passed else 'EXCEEDS LIMIT — compaction required'}",
        weight=2.0
    )
except Exception as e:
    add_check("memory_md_max_100_lines", False, f"Exception: {e}", 2.0)

# ─────────────────────────────────────────────────────────────────────────
# CHECK 4: memory.md — global preferences from session log are present
# ─────────────────────────────────────────────────────────────────────────
try:
    mem_text = (si_dir / "memory.md").read_text().lower()
    checks_detail = []
    prefs_found = 0
    prefs = [
        ("snake_case", "snake_case"),
        ("summarize changes", "summarize"),
        ("f-string", "f-string"),
        ("minimal comments", "minimal comment"),
    ]
    for label, keyword in prefs:
        if keyword in mem_text:
            prefs_found += 1
            checks_detail.append(f"✓ '{label}'")
        else:
            checks_detail.append(f"✗ '{label}'")

    passed = prefs_found >= 2
    add_check(
        "memory_md_global_prefs",
        passed,
        f"Global preferences in memory.md: {', '.join(checks_detail)} ({prefs_found}/4 found, need ≥2)",
        weight=2.0
    )
except Exception as e:
    add_check("memory_md_global_prefs", False, f"Exception: {e}", 2.0)

# ─────────────────────────────────────────────────────────────────────────
# CHECK 5: memory.md — promoted type-hints pattern (3x in 7 days)
# ─────────────────────────────────────────────────────────────────────────
try:
    mem_text = (si_dir / "memory.md").read_text().lower()
    promoted = "type hint" in mem_text or "type hints" in mem_text
    add_check(
        "memory_md_promoted_type_hints",
        promoted,
        "Type hints pattern (repeated 3x in 7 days) promoted to HOT (memory.md)" if promoted
        else "Type hints pattern NOT found in memory.md — promotion rule not applied",
        weight=2.5
    )
except Exception as e:
    add_check("memory_md_promoted_type_hints", False, f"Exception: {e}", 2.5)

# ─────────────────────────────────────────────────────────────────────────
# CHECK 6: projects/atlas.md exists with atlas-specific rules
# ─────────────────────────────────────────────────────────────────────────
try:
    atlas_path = si_dir / "projects" / "atlas.md"
    assert atlas_path.exists(), "projects/atlas.md missing"
    atlas_text = atlas_path.read_text().lower()
    has_transaction = "transaction" in atlas_text
    has_service_layer = "service layer" in atlas_text or "service" in atlas_text
    passed = has_transaction and has_service_layer
    add_check(
        "projects_atlas_md",
        passed,
        f"projects/atlas.md: transaction={'✓' if has_transaction else '✗'}, service_layer={'✓' if has_service_layer else '✗'}",
        weight=2.0
    )
except Exception as e:
    add_check("projects_atlas_md", False, f"Exception: {e}", 2.0)

# ─────────────────────────────────────────────────────────────────────────
# CHECK 7: projects/phoenix.md exists with phoenix-specific rules
# ─────────────────────────────────────────────────────────────────────────
try:
    phoenix_path = si_dir / "projects" / "phoenix.md"
    assert phoenix_path.exists(), "projects/phoenix.md missing"
    phoenix_text = phoenix_path.read_text().lower()
    has_strict = "strict" in phoenix_text or "typescript" in phoenix_text
    has_jsend = "jsend" in phoenix_text
    passed = has_strict and has_jsend
    add_check(
        "projects_phoenix_md",
        passed,
        f"projects/phoenix.md: typescript_strict={'✓' if has_strict else '✗'}, jsend={'✓' if has_jsend else '✗'}",
        weight=2.0
    )
except Exception as e:
    add_check("projects_phoenix_md", False, f"Exception: {e}", 2.0)

# ─────────────────────────────────────────────────────────────────────────
# CHECK 8: domains/code.md contains code-domain patterns from session
# ─────────────────────────────────────────────────────────────────────────
try:
    code_path = si_dir / "domains" / "code.md"
    assert code_path.exists(), "domains/code.md missing"
    code_text = code_path.read_text().lower()
    has_try_except = "try/except" in code_text or "try except" in code_text or "try" in code_text
    has_reraise = "re-raise" in code_text or "reraise" in code_text or "raise" in code_text
    passed = has_try_except and has_reraise
    add_check(
        "domains_code_md",
        passed,
        f"domains/code.md: try_except={'✓' if has_try_except else '✗'}, reraise={'✓' if has_reraise else '✗'}",
        weight=1.5
    )
except Exception as e:
    add_check("domains_code_md", False, f"Exception: {e}", 1.5)

# ─────────────────────────────────────────────────────────────────────────
# CHECK 9: Namespace isolation — atlas rules NOT duplicated in memory.md
# ─────────────────────────────────────────────────────────────────────────
try:
    mem_text = (si_dir / "memory.md").read_text().lower()
    # Atlas-specific rules should NOT be in the global HOT tier
    atlas_in_global = "for atlas" in mem_text or ("service layer" in mem_text and "transaction" in mem_text and "atlas" in mem_text)
    passed = not atlas_in_global
    add_check(
        "namespace_isolation_atlas_not_in_global",
        passed,
        "Atlas-specific rules correctly isolated to projects/atlas.md (not leaked to memory.md)" if passed
        else "Atlas-specific rules found in global memory.md — namespace isolation violated",
        weight=1.5
    )
except Exception as e:
    add_check("namespace_isolation_atlas_not_in_global", False, f"Exception: {e}", 1.5)

# ─────────────────────────────────────────────────────────────────────────
# CHECK 10: COLD archive — legacy-crm or 95-day-stale pattern archived
# ─────────────────────────────────────────────────────────────────────────
try:
    archive_dir = si_dir / "archive"
    archive_files = list(archive_dir.iterdir()) if archive_dir.exists() else []
    archive_texts = [f.read_text().lower() for f in archive_files if f.is_file()]
    all_archive = " ".join(archive_texts)
    # Check: either legacy-crm content moved to archive, or stale-95d entries archived
    has_archived_stale = (
        "legacy-crm" in all_archive or
        "camelcase" in all_archive or
        "jquery" in all_archive or
        "ftp" in all_archive or
        any("stale" in t for t in archive_texts)
    )
    # Also accept if legacy-crm.md was moved (no longer in projects/ as stale)
    legacy_crm_still_in_projects = (si_dir / "projects" / "legacy-crm.md").exists()
    if legacy_crm_still_in_projects:
        legacy_text = (si_dir / "projects" / "legacy-crm.md").read_text().lower()
        still_stale_unprocessed = "stale-95d" in legacy_text
    else:
        still_stale_unprocessed = False

    archived_properly = has_archived_stale or not still_stale_unprocessed
    add_check(
        "cold_archive_stale_95d",
        archived_properly,
        f"90-day-stale patterns archived: archive_files={len(archive_files)}, "
        f"legacy_crm_archived={'✓' if not still_stale_unprocessed or has_archived_stale else '✗'}",
        weight=2.0
    )
except Exception as e:
    add_check("cold_archive_stale_95d", False, f"Exception: {e}", 2.0)

# ─────────────────────────────────────────────────────────────────────────
# CHECK 11: WARM demotion — 30-35 day stale patterns demoted from HOT
# ─────────────────────────────────────────────────────────────────────────
try:
    mem_text = (si_dir / "memory.md").read_text().lower()
    # Patterns marked stale-35d should NOT be in memory.md (HOT)
    stale_in_hot = "async/await over callbacks" in mem_text and "[stale-35d]" in mem_text
    # They should appear in domains/ or projects/ (WARM)
    warm_files = list((si_dir / "domains").glob("*.md")) + list((si_dir / "projects").glob("*.md"))
    warm_texts = " ".join(f.read_text().lower() for f in warm_files)
    demoted_to_warm = "async/await" in warm_texts or "eslint" in warm_texts

    passed = not stale_in_hot  # primary: not still marked stale in HOT
    add_check(
        "warm_demotion_35d_stale",
        passed,
        f"30-day-stale patterns: not_in_hot={'✓' if not stale_in_hot else '✗'}, demoted_to_warm={'✓' if demoted_to_warm else '✗ (acceptable if cleaned)'}",
        weight=1.5
    )
except Exception as e:
    add_check("warm_demotion_35d_stale", False, f"Exception: {e}", 1.5)

# ─────────────────────────────────────────────────────────────────────────
# CHECK 12: index.md updated to reflect current state
# ─────────────────────────────────────────────────────────────────────────
try:
    index_path = si_dir / "index.md"
    assert index_path.exists(), "index.md missing"
    index_text = index_path.read_text().lower()
    has_atlas = "atlas" in index_text
    has_phoenix = "phoenix" in index_text
    has_code = "code" in index_text
    updated = has_atlas or has_phoenix or has_code
    add_check(
        "index_md_updated",
        updated,
        f"index.md updated: atlas={'✓' if has_atlas else '✗'}, phoenix={'✓' if has_phoenix else '✗'}, code_domain={'✓' if has_code else '✗'}",
        weight=1.0
    )
except Exception as e:
    add_check("index_md_updated", False, f"Exception: {e}", 1.0)

# ─────────────────────────────────────────────────────────────────────────
# CHECK 13: One-time/hypothetical signals NOT logged
# ─────────────────────────────────────────────────────────────────────────
try:
    all_si_text = ""
    for f in si_dir.rglob("*.md"):
        if "archive" not in str(f):
            all_si_text += f.read_text().lower()
    # "skip the docstring" was a context-specific one-time instruction
    has_oneoff = "skip the docstring" in all_si_text or "in this file only" in all_si_text
    # "what if redis" was hypothetical
    has_hypothetical = "redis" in all_si_text and "what if" in all_si_text
    passed = not has_oneoff and not has_hypothetical
    add_check(
        "ignored_oneoff_hypotheticals",
        passed,
        "One-time and hypothetical signals correctly NOT logged" if passed
        else f"One-time/hypothetical signals incorrectly stored: oneoff={has_oneoff}, hypothetical={has_hypothetical}",
        weight=1.5
    )
except Exception as e:
    add_check("ignored_oneoff_hypotheticals", False, f"Exception: {e}", 1.5)

# ─────────────────────────────────────────────────────────────────────────
# FINAL SCORE
# ─────────────────────────────────────────────────────────────────────────
final_score = round(score_total / max_score, 4) if max_score > 0 else 0.0
overall_passed = final_score >= 0.70

result = {
    "passed": overall_passed,
    "score": final_score,
    "checks": checks
}
print(json.dumps(result, indent=2))