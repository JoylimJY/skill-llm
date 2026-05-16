import sys
import json
import re
from pathlib import Path

def evaluate(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── 1. memory_backup.py exists ───────────────────────────────────────────
    backup_script = workspace / "skills" / "memory-compact" / "memory_backup.py"
    try:
        script_exists = backup_script.exists()
        total_score += add_check(
            "memory_backup.py exists",
            script_exists,
            f"Path: {backup_script} — {'found' if script_exists else 'NOT FOUND'}",
            weight=0.5,
        )
    except Exception as e:
        total_score += add_check("memory_backup.py exists", False, str(e), 0.5)

    # ── 2. Original memory file moved to backup/memory/ ──────────────────────
    original = workspace / "memory" / "2026-05-14.md"
    backup_file = workspace / "backup" / "memory" / "2026-05-14.md"
    try:
        original_gone = not original.exists()
        backup_present = backup_file.exists()
        passed = original_gone and backup_present
        total_score += add_check(
            "Original memory file moved to backup/memory/",
            passed,
            f"original gone={original_gone}, backup present={backup_present}",
            weight=1.5,
        )
    except Exception as e:
        total_score += add_check("Original memory file moved to backup/memory/", False, str(e), 1.5)

    # ── 3. MEMORY.md exists ──────────────────────────────────────────────────
    memory_md = workspace / "MEMORY.md"
    try:
        mem_exists = memory_md.exists()
        total_score += add_check(
            "MEMORY.md exists",
            mem_exists,
            f"MEMORY.md {'found' if mem_exists else 'NOT FOUND'}",
            weight=0.5,
        )
    except Exception as e:
        total_score += add_check("MEMORY.md exists", False, str(e), 0.5)

    # ── 4. MEMORY.md correct header ──────────────────────────────────────────
    try:
        mem_content = memory_md.read_text(encoding="utf-8")
        has_header = "# MEMORY - 长期记忆" in mem_content
        total_score += add_check(
            "MEMORY.md has correct header '# MEMORY - 长期记忆'",
            has_header,
            f"Header found: {has_header}. First 80 chars: {mem_content[:80]!r}",
            weight=1.0,
        )
    except Exception as e:
        total_score += add_check("MEMORY.md has correct header", False, str(e), 1.0)
        mem_content = ""

    # ── 5. MEMORY.md has 2026-05-14 section ─────────────────────────────────
    try:
        has_date_section = "## 2026-05-14" in mem_content
        total_score += add_check(
            "MEMORY.md contains '## 2026-05-14' section",
            has_date_section,
            f"Date section present: {has_date_section}",
            weight=1.0,
        )
    except Exception as e:
        total_score += add_check("MEMORY.md contains date section", False, str(e), 1.0)

    # ── 6. MEMORY.md preserves previous entries ──────────────────────────────
    try:
        has_old_entry = "## 2026-05-10" in mem_content or "## 2026-05-11" in mem_content
        total_score += add_check(
            "MEMORY.md preserves previous date entries",
            has_old_entry,
            f"Old entries preserved: {has_old_entry}",
            weight=1.0,
        )
    except Exception as e:
        total_score += add_check("MEMORY.md preserves previous entries", False, str(e), 1.0)

    # ── 7. MEMORY.md key points extracted from correct keywords ──────────────
    # Keywords from SKILL.md: ["决定", "喜欢", "讨厌", "记住", "重要", "计划", "目标"]
    # The 2026-05-14.md has lines containing these keywords.
    # We verify that the new section contains 2-3 numbered items.
    try:
        # Find the 2026-05-14 section
        date_section_match = re.search(
            r"## 2026-05-14\n(.*?)(?=\n## |\Z)", mem_content, re.DOTALL
        )
        if date_section_match:
            section_text = date_section_match.group(1).strip()
            # Count numbered points (1. 2. 3.)
            numbered_points = re.findall(r"^\d+\.", section_text, re.MULTILINE)
            point_count = len(numbered_points)
            in_range = 2 <= point_count <= 3
            # Check at least one point contains a keyword
            keywords = ["决定", "喜欢", "讨厌", "记住", "重要", "计划", "目标"]
            has_keyword = any(kw in section_text for kw in keywords)
            passed = in_range and has_keyword
            total_score += add_check(
                "MEMORY.md 2026-05-14 section has 2-3 keyword-based numbered points",
                passed,
                f"Point count: {point_count} (need 2-3), has_keyword: {has_keyword}. Section: {section_text[:200]!r}",
                weight=2.0,
            )
        else:
            total_score += add_check(
                "MEMORY.md 2026-05-14 section has 2-3 keyword-based numbered points",
                False,
                "Section '## 2026-05-14' not found in MEMORY.md",
                weight=2.0,
            )
    except Exception as e:
        total_score += add_check(
            "MEMORY.md 2026-05-14 section has 2-3 keyword-based numbered points",
            False, str(e), 2.0,
        )

    # ── 8. Feishu notification file generated ────────────────────────────────
    # The skill says to generate a Feishu notification file. Search for it.
    try:
        feishu_candidates = list(workspace.rglob("*feishu*")) + list(workspace.rglob("*notification*")) + list(workspace.rglob("*notify*")) + list(workspace.rglob("*lark*"))
        # Also check scripts/ for any .txt/.md files created today that look like notifications
        feishu_file = None
        for candidate in feishu_candidates:
            if candidate.is_file():
                feishu_file = candidate
                break
        if feishu_file is None:
            # Try to find any file with feishu-style content
            all_files = list(workspace.rglob("*.txt")) + list(workspace.rglob("*.md"))
            for f in all_files:
                if f.name in ("MEMORY.md",):
                    continue
                try:
                    content = f.read_text(encoding="utf-8")
                    if "每日记忆备份" in content or "backup/memory" in content:
                        feishu_file = f
                        break
                except Exception:
                    pass

        if feishu_file:
            feishu_content = feishu_file.read_text(encoding="utf-8")
            has_title = "每日记忆备份" in feishu_content
            has_backup_path = "backup/memory/2026-05-14" in feishu_content
            has_key_points_section = "关键点" in feishu_content or "提取" in feishu_content
            passed = has_title and has_backup_path and has_key_points_section
            total_score += add_check(
                "Feishu notification file generated with correct content",
                passed,
                f"File: {feishu_file}, title={has_title}, backup_path={has_backup_path}, keypoints_section={has_key_points_section}",
                weight=2.0,
            )
        else:
            total_score += add_check(
                "Feishu notification file generated with correct content",
                False,
                "No Feishu notification file found anywhere in workspace",
                weight=2.0,
            )
    except Exception as e:
        total_score += add_check("Feishu notification file generated with correct content", False, str(e), 2.0)

    # ── 9. Script log written (optional but good practice) ───────────────────
    try:
        log_file = workspace / "scripts" / "memory_backup.log"
        log_exists = log_file.exists()
        total_score += add_check(
            "memory_backup.log exists in scripts/",
            log_exists,
            f"Log file {'found' if log_exists else 'not found'} at {log_file}",
            weight=0.5,
        )
    except Exception as e:
        total_score += add_check("memory_backup.log exists in scripts/", False, str(e), 0.5)

    # ── Final score ───────────────────────────────────────────────────────────
    max_score = 0.5 + 1.5 + 0.5 + 1.0 + 1.0 + 1.0 + 2.0 + 2.0 + 0.5  # = 10.0
    normalized = round(total_score / max_score, 4)

    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": normalized,
        "checks": checks,
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/root/.openclaw/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))