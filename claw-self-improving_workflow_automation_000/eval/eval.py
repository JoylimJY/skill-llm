import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

def count_lines(text):
    """Count non-empty lines that are content (not just whitespace)."""
    return len([l for l in text.splitlines() if l.strip()])

def total_lines(text):
    """Count all lines including blank."""
    return len(text.splitlines())

checks = []
score_weights = []

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    score_weights.append((passed, weight))

base = Path.home() / "self-improving"

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 1: memory.md exists and is within 100-line HOT limit
# ──────────────────────────────────────────────────────────────────────────────
try:
    memory_path = base / "memory.md"
    if not memory_path.exists():
        add_check("memory.md_exists", False, "memory.md not found at ~/self-improving/memory.md", weight=3.0)
        memory_text = ""
    else:
        memory_text = memory_path.read_text()
        line_count = total_lines(memory_text)
        passed = line_count <= 100
        add_check(
            "memory.md_within_100_line_limit",
            passed,
            f"memory.md has {line_count} lines (limit: 100). {'PASS' if passed else 'FAIL — compaction required'}",
            weight=3.0
        )
except Exception as e:
    add_check("memory.md_within_100_line_limit", False, f"Error reading memory.md: {e}", weight=3.0)
    memory_text = ""

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 2: Stale/clearly-wrong entries removed from memory.md
# Must NOT contain Python 2 / tabs / CamelCase / semicolons / global variables stale entries
# ──────────────────────────────────────────────────────────────────────────────
try:
    stale_patterns = [
        r"python 2 compatible",
        r"print statements for debug",
        r"camelcase for variable",
        r"semicolons at end of python",
        r"global variables for configuration",
        r"john prefers tabs",           # third-party personal info — must not be stored per boundaries
        r"use tabs.*indentation",
    ]
    found_stale = []
    for pat in stale_patterns:
        if re.search(pat, memory_text, re.IGNORECASE):
            found_stale.append(pat)
    passed = len(found_stale) == 0
    add_check(
        "stale_entries_removed",
        passed,
        f"Stale/forbidden entries still present: {found_stale}" if not passed else "No stale entries found.",
        weight=2.0
    )
except Exception as e:
    add_check("stale_entries_removed", False, f"Error checking stale entries: {e}", weight=2.0)

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 3: Duplicate entries were merged/compacted (deduplication check)
# The original had many near-duplicate pairs — after compaction there should NOT
# be multiple entries saying the same thing about indentation, type hints, f-strings, line-length.
# ──────────────────────────────────────────────────────────────────────────────
try:
    # Count occurrences of key topics — should each appear at most once after merging
    topics = {
        "indentation": r"(4.space indent|indentation)",
        "type hints": r"type hint",
        "f-string": r"f.string",
        "line.length.88": r"(88 char|line.length.*88|max.*88)",
        "black formatter": r"black",
    }
    dup_violations = []
    for topic, pat in topics.items():
        matches = re.findall(pat, memory_text, re.IGNORECASE)
        if len(matches) > 2:  # allow up to 2 (slight variations OK), but 3+ = not compacted
            dup_violations.append(f"'{topic}' appears {len(matches)} times")
    
    passed = len(dup_violations) == 0
    add_check(
        "duplicates_merged",
        passed,
        f"Unmerged duplicates found: {dup_violations}" if not passed else "Duplicate entries properly merged.",
        weight=2.0
    )
except Exception as e:
    add_check("duplicates_merged", False, f"Error checking duplicates: {e}", weight=2.0)

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 4: archive/ contains the stale/archived entries
# The demoted stale entries from memory.md must land in archive/
# ──────────────────────────────────────────────────────────────────────────────
try:
    archive_dir = base / "archive"
    archive_files = list(archive_dir.glob("*.md"))
    
    # Read all archive content
    all_archive_text = ""
    for af in archive_files:
        all_archive_text += af.read_text()
    
    # At least one stale pattern should have been archived
    archived_stale_patterns = [
        r"(python 2|print.*debug|camelcase.*variable|semicolons.*python|global.*variable|tabs.*indent)",
    ]
    found_archived = any(
        re.search(p, all_archive_text, re.IGNORECASE) for p in archived_stale_patterns
    )
    
    passed = found_archived and len(archive_files) > 0
    add_check(
        "stale_entries_archived",
        passed,
        f"Archive dir has {len(archive_files)} files. Stale patterns archived: {found_archived}",
        weight=1.5
    )
except Exception as e:
    add_check("stale_entries_archived", False, f"Error checking archive: {e}", weight=1.5)

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 5: "Use logging not print" promoted to HOT (memory.md)
# This pattern appears 4 times in corrections.md within 7 days (days 1,2,3,4)
# → Must be promoted to memory.md per "3x in 7 days → promote to HOT" rule
# ──────────────────────────────────────────────────────────────────────────────
try:
    logging_in_memory = bool(re.search(
        r"(logging|log.*debug|debug.*log).*(not|instead of|avoid|no).*print|"
        r"print.*(not|instead|avoid|use logging)|"
        r"use logging.*debug|logging\.debug",
        memory_text, re.IGNORECASE
    ))
    add_check(
        "logging_pattern_promoted_to_hot",
        logging_in_memory,
        f"'Use logging not print' pattern {'found' if logging_in_memory else 'NOT found'} in memory.md (HOT). "
        "This pattern occurred 4x in 7 days and must be promoted.",
        weight=2.5
    )
except Exception as e:
    add_check("logging_pattern_promoted_to_hot", False, f"Error checking promotion: {e}", weight=2.5)

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 6: "Never use mutable default args" promoted to HOT
# Appears 3 times in corrections.md within 7 days (days 20,21,22 — wait, that's 22 days ago)
# Actually days 20,21,22 which is > 7 days. Let's re-check gen_inputs: 
# dstr(20), dstr(21), dstr(22) — 20,21,22 days ago → NOT within 7 days → should NOT be auto-promoted
# But it appeared 3 times total → after 3x (regardless of timeframe), 
# re-reading SKILL.md: "Pattern used 3x in 7 days → promote to HOT"
# So mutable defaults (20,21,22 days ago) should NOT be in HOT but corrections.md should have them.
# We check that the logging pattern (within 7 days, 4x) IS in HOT.
# ──────────────────────────────────────────────────────────────────────────────
try:
    mutable_in_corrections = bool(re.search(
        r"mutable.{0,20}default",
        (base / "corrections.md").read_text() if (base / "corrections.md").exists() else "",
        re.IGNORECASE
    ))
    corrections_text = (base / "corrections.md").read_text() if (base / "corrections.md").exists() else ""
    corrections_line_count = total_lines(corrections_text)
    
    passed = corrections_line_count <= 55  # 50 corrections + some header lines (generous)
    add_check(
        "corrections.md_within_50_limit",
        passed,
        f"corrections.md has {corrections_line_count} lines. Limit is ~50 corrections. "
        f"{'OK' if passed else 'Appears not trimmed to last 50'}",
        weight=1.0
    )
except Exception as e:
    add_check("corrections.md_within_50_limit", False, f"Error checking corrections.md: {e}", weight=1.0)

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 7: Core genuine preferences RETAINED in memory.md
# The compaction must not delete legitimate preferences
# ──────────────────────────────────────────────────────────────────────────────
try:
    required_patterns = [
        (r"4.space|four.space|4 space", "4-space indentation preference"),
        (r"type hint", "type hints preference"),
        (r"pytest", "pytest preference"),
        (r"(feature branch|never.*commit.*main|main.*branch)", "git branch workflow"),
        (r"(imperative|verb).*(commit|message)", "commit message style"),
    ]
    missing = []
    for pat, desc in required_patterns:
        if not re.search(pat, memory_text, re.IGNORECASE):
            missing.append(desc)
    
    passed = len(missing) == 0
    add_check(
        "core_preferences_retained",
        passed,
        f"Missing preferences after compaction: {missing}" if not passed else "All core preferences retained.",
        weight=2.0
    )
except Exception as e:
    add_check("core_preferences_retained", False, f"Error checking retained prefs: {e}", weight=2.0)

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 8: index.md updated with current line counts
# ──────────────────────────────────────────────────────────────────────────────
try:
    index_path = base / "index.md"
    if not index_path.exists():
        add_check("index.md_updated", False, "index.md not found", weight=1.0)
    else:
        index_text = index_path.read_text()
        actual_memory_lines = total_lines(memory_text)
        
        # Check that index.md no longer shows the stale "85" count for memory.md
        # and shows a number ≤ 100
        old_stale_count = bool(re.search(r"memory\.md\s*\|\s*85\b", index_text))
        has_updated_count = bool(re.search(
            r"memory\.md\s*\|\s*(\d+)",
            index_text
        ))
        
        # Extract the number
        m = re.search(r"memory\.md\s*\|\s*(\d+)", index_text)
        reported_count = int(m.group(1)) if m else -1
        
        # The reported count should roughly match actual (within 5 lines tolerance)
        count_accurate = abs(reported_count - actual_memory_lines) <= 5 if reported_count != -1 else False
        
        passed = has_updated_count and not old_stale_count and count_accurate
        add_check(
            "index.md_updated",
            passed,
            f"index.md reports memory.md={reported_count} lines, actual={actual_memory_lines}. "
            f"Stale '85' count still present: {old_stale_count}. Count accurate: {count_accurate}",
            weight=1.0
        )
except Exception as e:
    add_check("index.md_updated", False, f"Error checking index.md: {e}", weight=1.0)

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 9: Namespace isolation — alpha-service project preferences NOT mixed into global memory.md
# The alpha-service specific "structlog" or "UUID4" or "/api/v1/" should be in projects/, not HOT
# ──────────────────────────────────────────────────────────────────────────────
try:
    project_specifics_in_hot = []
    project_specific_patterns = [
        (r"structlog", "structlog (alpha-service specific)"),
        (r"UUID4.*primary key|primary key.*UUID4", "UUID4 primary keys"),
        (r"/api/v1/", "API versioning route (alpha-service)"),
        (r"docker.compose.*server|deploy.*docker.compose", "Docker Compose deploy rule"),
    ]
    for pat, desc in project_specific_patterns:
        if re.search(pat, memory_text, re.IGNORECASE):
            project_specifics_in_hot.append(desc)
    
    # These SHOULD be in projects/alpha-service.md
    alpha_path = base / "projects" / "alpha-service.md"
    alpha_text = alpha_path.read_text() if alpha_path.exists() else ""
    alpha_preserved = bool(re.search(r"structlog|UUID4|/api/v1/", alpha_text, re.IGNORECASE))
    
    # Ideally project-specific items not in HOT (or if they are, they're labeled as project-specific)
    passed = alpha_preserved  # minimum: alpha-service.md must still exist with its content
    add_check(
        "namespace_isolation_respected",
        passed,
        f"projects/alpha-service.md preserved with project-specific rules: {alpha_preserved}. "
        f"Project-specific items leaked to HOT memory.md: {project_specifics_in_hot}",
        weight=1.5
    )
except Exception as e:
    add_check("namespace_isolation_respected", False, f"Error checking namespace isolation: {e}", weight=1.5)

# ──────────────────────────────────────────────────────────────────────────────
# CHECK 10: One-time notes removed (not stored as permanent rules)
# "Note: John prefers tabs", "Reminder: update dependencies monthly",
# "Note: discussed with team, will migrate to FastAPI" — these are one-time/third-party
# ──────────────────────────────────────────────────────────────────────────────
try:
    one_time_patterns = [
        (r"john prefers", "John's personal preference (third-party info)"),
        (r"reminder.*update dependencies monthly", "one-time reminder"),
        (r"reminder.*open PRs every Monday", "one-time reminder"),
        (r"discussed.*migrate to FastAPI|migrate to FastAPI.*discussed", "one-time note"),
    ]
    found_one_time = []
    for pat, desc in one_time_patterns:
        if re.search(pat, memory_text, re.IGNORECASE):
            found_one_time.append(desc)
    
    passed = len(found_one_time) == 0
    add_check(
        "one_time_notes_and_third_party_info_removed",
        passed,
        f"One-time/third-party entries still in memory.md: {found_one_time}" if not passed
        else "One-time notes and third-party info correctly excluded.",
        weight=1.5
    )
except Exception as e:
    add_check("one_time_notes_and_third_party_info_removed", False, f"Error: {e}", weight=1.5)

# ──────────────────────────────────────────────────────────────────────────────
# FINAL SCORE COMPUTATION
# ──────────────────────────────────────────────────────────────────────────────
total_weight = sum(w for _, w in score_weights)
earned_weight = sum(w for passed, w in score_weights if passed)
score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0
overall_passed = score >= 0.70

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))