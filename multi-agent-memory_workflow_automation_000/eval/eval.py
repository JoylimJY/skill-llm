#!/usr/bin/env python3
"""
Evaluation script for the multi-agent-memory task.
Checks:
1. Version rotation for maker.md was done correctly (3-version system)
2. New maker.md has updated content (Phase 1 completion)
3. A timestamped dev log exists with Chinese filename convention
4. knowledge/decisions/decisions.md was updated with a new entry
5. A handoff document exists with correct naming, AND latest.md is a symlink
6. The symlink points to the actual handoff file
"""

import sys
import json
import os
import re
from pathlib import Path

BASE = Path("/root/.openclaw")
PROJ = BASE / "projects" / "phoenix-engine"
KNOWLEDGE = BASE / "knowledge"

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── ORIGINAL file contents to verify version rotation ─────────────────────────
EXPECTED_V2 = "Maker Status - 2026-03-09"  # what was in .md.1 → should now be in .md.2
EXPECTED_V1 = "Maker Status - 2026-03-10"  # what was in .md   → should now be in .md.1

# ── Check 1: maker.md.2 contains what was in maker.md.1 ──────────────────────
try:
    v2_path = PROJ / "status" / "maker.md.2"
    content = v2_path.read_text(encoding="utf-8")
    ok = EXPECTED_V2 in content
    check(
        "version_rotation_md2_correct",
        ok,
        f"maker.md.2 should contain '{EXPECTED_V2}' (old .md.1 content). Got: {content[:200]}"
    )
except Exception as e:
    check("version_rotation_md2_correct", False, f"Could not read maker.md.2: {e}")

# ── Check 2: maker.md.1 contains what was in maker.md ────────────────────────
try:
    v1_path = PROJ / "status" / "maker.md.1"
    content = v1_path.read_text(encoding="utf-8")
    ok = EXPECTED_V1 in content
    check(
        "version_rotation_md1_correct",
        ok,
        f"maker.md.1 should contain '{EXPECTED_V1}' (old .md content). Got: {content[:200]}"
    )
except Exception as e:
    check("version_rotation_md1_correct", False, f"Could not read maker.md.1: {e}")

# ── Check 3: maker.md (current) has new content indicating completion ─────────
try:
    md_path = PROJ / "status" / "maker.md"
    content = md_path.read_text(encoding="utf-8")
    # Should be a new entry (not the old "90%" entry, ideally 100% or "完成")
    is_new = content != (
        "# Maker Status - 2026-03-10\n\n"
        "**当前任务：** 渲染管线 Phase 1 最终调试\n"
        "**进度：** 90%\n"
        "**阻碍：** 需要 killjoy 确认测试通过\n"
    )
    # Also check it references Phase 1 completion somehow
    mentions_completion = any(kw in content for kw in [
        "完成", "100%", "Phase 1", "渲染管线", "done", "Done", "finished", "complete"
    ])
    ok = is_new and mentions_completion
    check(
        "maker_status_updated_with_completion",
        ok,
        f"maker.md should be updated with Phase 1 completion info. is_new={is_new}, mentions_completion={mentions_completion}. Content: {content[:300]}"
    )
except Exception as e:
    check("maker_status_updated_with_completion", False, f"Could not read maker.md: {e}")

# ── Check 4: Dev log file exists with correct naming convention ───────────────
try:
    logs_dir = PROJ / "logs"
    # Pattern: YYYY-MM-DD-HH-mm-开发日志-*.md (Chinese characters required)
    log_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-开发日志-.+\.md$")
    log_files = [f for f in logs_dir.iterdir() if log_pattern.match(f.name)]
    
    # Exclude the distractor from data-pipeline (that's in a different dir, but just in case)
    phoenix_logs = [f for f in log_files]
    
    ok = len(phoenix_logs) >= 1
    detail = f"Found {len(phoenix_logs)} properly named dev log(s): {[f.name for f in phoenix_logs]}"
    check("dev_log_naming_convention", ok, detail)
    
    if ok:
        # Also verify the log content is meaningful (not empty)
        log_content = phoenix_logs[0].read_text(encoding="utf-8")
        has_content = len(log_content.strip()) > 50
        check(
            "dev_log_has_content",
            has_content,
            f"Dev log '{phoenix_logs[0].name}' has {len(log_content)} chars. Excerpt: {log_content[:200]}"
        )
    else:
        check("dev_log_has_content", False, "No dev log found to check content")

except Exception as e:
    check("dev_log_naming_convention", False, f"Error scanning logs dir: {e}")
    check("dev_log_has_content", False, f"Error scanning logs dir: {e}")

# ── Check 5: knowledge/decisions/decisions.md has a new entry ─────────────────
try:
    dec_path = KNOWLEDGE / "decisions" / "decisions.md"
    content = dec_path.read_text(encoding="utf-8")
    # Original had D001 and D002; should now have at least D003 or new entry
    # Check there's more content than the original
    original_marker = "D002"
    has_new_entry = content.count("##") >= 3  # at least 3 decision entries
    # The new entry should reference phoenix-engine and rendering pipeline
    references_phoenix = any(kw in content for kw in [
        "phoenix-engine", "phoenix", "渲染", "rendering", "Phase 1", "管线"
    ])
    ok = has_new_entry and references_phoenix
    check(
        "knowledge_decisions_updated",
        ok,
        f"decisions.md should have new entry about phoenix-engine Phase 1. "
        f"has_new_entry={has_new_entry}, references_phoenix={references_phoenix}. "
        f"Content snippet: {content[-400:]}"
    )
except Exception as e:
    check("knowledge_decisions_updated", False, f"Could not read decisions.md: {e}")

# ── Check 6: Handoff document exists with correct naming ─────────────────────
try:
    handoffs_dir = PROJ / "handoffs"
    # Pattern: YYYY-MM-DD-{阶段/description}-交接.md
    handoff_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}-.+-交接\.md$")
    handoff_files = [f for f in handoffs_dir.iterdir() 
                     if f.is_file() and handoff_pattern.match(f.name)]
    ok = len(handoff_files) >= 1
    check(
        "handoff_document_exists",
        ok,
        f"Found {len(handoff_files)} handoff doc(s) matching YYYY-MM-DD-*-交接.md: "
        f"{[f.name for f in handoff_files]}"
    )
except Exception as e:
    check("handoff_document_exists", False, f"Error scanning handoffs dir: {e}")

# ── Check 7: latest.md in handoffs is a symlink (not a regular file copy) ─────
try:
    latest_path = PROJ / "handoffs" / "latest.md"
    exists = latest_path.exists() or latest_path.is_symlink()
    is_symlink = latest_path.is_symlink()
    
    if not exists:
        check(
            "handoff_latest_is_symlink",
            False,
            "handoffs/latest.md does not exist"
        )
    elif not is_symlink:
        check(
            "handoff_latest_is_symlink",
            False,
            f"handoffs/latest.md exists but is NOT a symlink (it's a regular file). "
            f"Per SKILL.md, it must be a symbolic link to the latest handoff version."
        )
    else:
        # Verify the symlink target is a real handoff file
        target = os.readlink(str(latest_path))
        check(
            "handoff_latest_is_symlink",
            True,
            f"handoffs/latest.md is a symlink pointing to: {target}"
        )
except Exception as e:
    check("handoff_latest_is_symlink", False, f"Error checking latest.md: {e}")

# ── Check 8: Symlink target actually resolves to an existing handoff file ──────
try:
    latest_path = PROJ / "handoffs" / "latest.md"
    if latest_path.is_symlink():
        resolved = latest_path.resolve()
        target_exists = resolved.exists()
        target_in_handoffs = "handoffs" in str(resolved) or resolved.parent == (PROJ / "handoffs")
        ok = target_exists and target_in_handoffs
        check(
            "handoff_symlink_resolves_correctly",
            ok,
            f"Symlink resolves to: {resolved}. exists={target_exists}, in_handoffs={target_in_handoffs}"
        )
    else:
        check(
            "handoff_symlink_resolves_correctly",
            False,
            "latest.md is not a symlink, cannot check resolution"
        )
except Exception as e:
    check("handoff_symlink_resolves_correctly", False, f"Error resolving symlink: {e}")

# ── Compute score ──────────────────────────────────────────────────────────────
passed_checks = sum(1 for c in checks if c["passed"])
total_checks = len(checks)
score = round(passed_checks / total_checks, 4) if total_checks > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))