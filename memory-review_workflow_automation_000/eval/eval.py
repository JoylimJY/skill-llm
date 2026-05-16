import sys
import os
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime, timedelta, date

workspace = Path(sys.argv[1])
today = datetime.now().date()

checks = []
score_total = 0.0
score_max = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global score_total, score_max
    score_max += weight
    if passed:
        score_total += weight

def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()

# ─── Helper ───────────────────────────────────────────────────────────────────
def find_file_containing(directory: Path, pattern: str):
    """Find files matching glob pattern."""
    return list(directory.rglob(pattern))

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 1: Report file exists at correct path
# ══════════════════════════════════════════════════════════════════════════════
report_path = workspace / "memory" / "daily" / f"{today}-memory-review.md"
report_exists = report_path.exists()
add_check(
    "report_file_exists",
    report_exists,
    f"Report at {report_path}: {'found' if report_exists else 'MISSING'}",
    weight=1.0,
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 2: Execution log exists at correct path
# ══════════════════════════════════════════════════════════════════════════════
log_path = workspace / "data" / "exec-logs" / "memory-review" / f"{today}.md"
log_exists = log_path.exists()
add_check(
    "exec_log_file_exists",
    log_exists,
    f"Exec log at {log_path}: {'found' if log_exists else 'MISSING'}",
    weight=1.0,
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 3: post-mortems.md exists and contains Celery content (from d1)
# ══════════════════════════════════════════════════════════════════════════════
pm_path = workspace / "memory" / "post-mortems.md"
try:
    pm_content = pm_path.read_text(encoding="utf-8")
    # Must mention Celery or memory leak or OOM
    has_celery = any(kw in pm_content for kw in ["Celery", "celery", "OOM", "内存泄漏", "task_ignore_result"])
    add_check(
        "post_mortems_contains_celery_lesson",
        has_celery,
        f"post-mortems.md {'contains' if has_celery else 'MISSING'} Celery error content",
        weight=2.0,
    )
except Exception as e:
    add_check("post_mortems_contains_celery_lesson", False, f"Cannot read post-mortems.md: {e}", weight=2.0)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 4: fw-*.md files exist for technical content (asyncio from d2)
# ══════════════════════════════════════════════════════════════════════════════
knowledge_dir = workspace / "memory" / "knowledge"
fw_files = list(knowledge_dir.glob("fw-*.md"))
fw_names = [f.name for f in fw_files]

add_check(
    "fw_files_use_correct_naming_convention",
    len(fw_files) >= 2,  # at least asyncio + something new
    f"fw-*.md files found: {fw_names}",
    weight=1.5,
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 5: asyncio fw file was APPENDED (not overwritten) — must have old content
# ══════════════════════════════════════════════════════════════════════════════
asyncio_candidates = list(knowledge_dir.glob("fw-asyncio*"))
try:
    if not asyncio_candidates:
        # Maybe the agent named it differently but still should have asyncio content
        # Search all fw files for asyncio content
        asyncio_candidates = [f for f in fw_files if "asyncio" in f.read_text(encoding="utf-8").lower()]
    
    if asyncio_candidates:
        asyncio_content = asyncio_candidates[0].read_text(encoding="utf-8")
        has_old = "旧内容" in asyncio_content or "Coroutine 基础略" in asyncio_content or "2024-11-01" in asyncio_content
        has_new = any(kw in asyncio_content for kw in ["uvloop", "asyncio", "gather", "协程", "event loop"])
        appended_correctly = has_old and has_new
        add_check(
            "asyncio_fw_file_appended_not_overwritten",
            appended_correctly,
            f"asyncio fw file: has_old_content={has_old}, has_new_content={has_new}",
            weight=2.0,
        )
    else:
        add_check(
            "asyncio_fw_file_appended_not_overwritten",
            False,
            "No asyncio-related fw file found",
            weight=2.0,
        )
except Exception as e:
    add_check("asyncio_fw_file_appended_not_overwritten", False, f"Error: {e}", weight=2.0)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 6: ripgrep tool content landed in a fw-*.md (from d3, tool type)
# ══════════════════════════════════════════════════════════════════════════════
try:
    rg_in_fw = False
    for fw in fw_files:
        content = fw.read_text(encoding="utf-8")
        if any(kw in content for kw in ["ripgrep", "rg ", "rg -t", "rg -n"]):
            rg_in_fw = True
            break
    add_check(
        "ripgrep_tool_content_in_fw_file",
        rg_in_fw,
        f"ripgrep content found in fw-*.md: {rg_in_fw}",
        weight=1.5,
    )
except Exception as e:
    add_check("ripgrep_tool_content_in_fw_file", False, f"Error: {e}", weight=1.5)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 7: TOOLS.md was NOT modified for d1/d2/d3 entries (config was already scanned)
#           AND TOOLS.md/AGENTS.md should not have been filled with non-config content
# ══════════════════════════════════════════════════════════════════════════════
# The config/preference content was in d4/d5 which are already in state (old).
# So TOOLS.md should NOT have new Python/pyenv config from d4 appended
# (it was already scanned). But the agent might not know this without MD5 check.
# We verify: TOOLS.md should NOT contain d1/d2/d3 content (Celery, asyncio, ripgrep)
try:
    tools_content = (workspace / "TOOLS.md").read_text(encoding="utf-8")
    contaminated = any(kw in tools_content for kw in ["Celery", "celery", "uvloop", "ripgrep", "rg -t"])
    add_check(
        "tools_md_not_contaminated_with_non_config",
        not contaminated,
        f"TOOLS.md contamination check: {'clean' if not contaminated else 'CONTAMINATED with non-config content'}",
        weight=1.0,
    )
except Exception as e:
    add_check("tools_md_not_contaminated_with_non_config", False, f"Error reading TOOLS.md: {e}", weight=1.0)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 8: State file was updated after scan (must now include d1, d2, d3)
# ══════════════════════════════════════════════════════════════════════════════
state_path = workspace / "data" / "cache" / "memory-review-state.json"
d1_date = today - timedelta(days=1)
d2_date = today - timedelta(days=2)
d3_date = today - timedelta(days=3)

try:
    state_data = json.loads(state_path.read_text(encoding="utf-8"))
    scanned = state_data.get("scanned", {})
    
    d1_key = f"memory/daily/{d1_date}.md"
    d2_key = f"memory/daily/{d2_date}.md"
    d3_key = f"memory/daily/{d3_date}.md"
    
    d1_tracked = d1_key in scanned
    d2_tracked = d2_key in scanned
    d3_tracked = d3_key in scanned
    
    all_new_tracked = d1_tracked and d2_tracked and d3_tracked
    
    # Verify MD5 values are correct
    md5_correct = True
    for key, path_suffix in [(d1_key, f"memory/daily/{d1_date}.md"),
                               (d2_key, f"memory/daily/{d2_date}.md"),
                               (d3_key, f"memory/daily/{d3_date}.md")]:
        if key in scanned:
            actual_md5 = md5_of(workspace / path_suffix)
            if scanned[key] != actual_md5:
                md5_correct = False
    
    add_check(
        "state_file_updated_with_new_diaries",
        all_new_tracked and md5_correct,
        f"State tracks d1={d1_tracked}, d2={d2_tracked}, d3={d3_tracked}, MD5_correct={md5_correct}",
        weight=2.0,
    )
except Exception as e:
    add_check("state_file_updated_with_new_diaries", False, f"Cannot read state file: {e}", weight=2.0)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 9: State file retains old entries for d4, d5 (incremental, not wiped)
# ══════════════════════════════════════════════════════════════════════════════
d4_date = today - timedelta(days=5)
d5_date = today - timedelta(days=7)
try:
    state_data = json.loads(state_path.read_text(encoding="utf-8"))
    scanned = state_data.get("scanned", {})
    d4_key = f"memory/daily/{d4_date}.md"
    d5_key = f"memory/daily/{d5_date}.md"
    d4_kept = d4_key in scanned
    d5_kept = d5_key in scanned
    add_check(
        "state_file_retains_old_scanned_entries",
        d4_kept and d5_kept,
        f"Old entries retained: d4={d4_kept}, d5={d5_kept}",
        weight=1.5,
    )
except Exception as e:
    add_check("state_file_retains_old_scanned_entries", False, f"Error: {e}", weight=1.5)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 10: Report contains scan summary with correct numbers
# ══════════════════════════════════════════════════════════════════════════════
try:
    report_content = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    # Should mention scanning at least 3 new/changed files (d1, d2, d3)
    has_scan_info = bool(re.search(r"新增.{0,10}变更|新增|变更|scanned|扫描", report_content, re.IGNORECASE))
    has_detail_table = "|" in report_content  # markdown table present
    add_check(
        "report_contains_scan_summary",
        has_scan_info and has_detail_table,
        f"Report has scan info={has_scan_info}, detail table={has_detail_table}",
        weight=1.0,
    )
except Exception as e:
    add_check("report_contains_scan_summary", False, f"Error: {e}", weight=1.0)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 11: No knowledge content from already-scanned d4/d5 was re-deposited
#            (d4 has config, d5 has project content — both already in state)
# ══════════════════════════════════════════════════════════════════════════════
try:
    pm_content_check = pm_path.read_text(encoding="utf-8") if pm_path.exists() else ""
    # d5 has project retrospective about Debezium/Kafka — if agent re-processed d5, 
    # it would add it to fw-*.md. Check that d4/d5 content isn't in post-mortems
    # (the d5 project content should NOT be there since it's already scanned)
    # More importantly: d4 python config should not be NEWLY added to TOOLS.md
    # (it was already processed). We check that TOOLS.md doesn't have duplicate pyenv entries
    tools_c = (workspace / "TOOLS.md").read_text(encoding="utf-8")
    pyenv_count = tools_c.lower().count("pyenv")
    debezium_in_pm = "debezium" in pm_content_check.lower() or "Debezium" in pm_content_check
    
    # Debezium is project content (d5) not error content, so it should NOT be in post-mortems
    # pyenv appearing more than once suggests duplicate processing
    no_reprocessing = not debezium_in_pm and pyenv_count <= 1
    add_check(
        "no_reprocessing_of_already_scanned_entries",
        no_reprocessing,
        f"Debezium in post-mortems={debezium_in_pm}, pyenv_count_in_TOOLS={pyenv_count}",
        weight=2.0,
    )
except Exception as e:
    add_check("no_reprocessing_of_already_scanned_entries", False, f"Error: {e}", weight=2.0)

# ══════════════════════════════════════════════════════════════════════════════
# FINAL SCORE
# ══════════════════════════════════════════════════════════════════════════════
final_score = round(score_total / score_max, 4) if score_max > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": final_score,
    "checks": checks,
}
print(json.dumps(result, ensure_ascii=False, indent=2))