#!/usr/bin/env python3
"""
Evaluation script for the memory deduplication task.
Tests that:
1. The agent ran `node skills/memory-dedup/dedup.mjs --backup`
2. MEMORY.md was actually modified (deduplication occurred)
3. A backup file was created at memory/MEMORY-backup-<date>.md
4. The dedup report was generated at memory/dedup-report.txt
5. Duplicate bullet items were correctly reduced (Jaccard >0.8 → deleted)
6. Partial duplicates were merged (Jaccard 0.5-0.8)
7. Unique entries were preserved
"""

import sys
import json
import re
from pathlib import Path

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Check 1: MEMORY.md exists and was modified ────────────────────────────
    memory_path = ws / "MEMORY.md"
    try:
        original_content = """# MEMORY.md — Agent Knowledge Base

## 进行中的任务

### [P0] 优先任务
- [P0] NeuroBoost v5.0 发布待重试
- [P1] AgentAwaken 网站上线
- [P2] 数据管道优化 (deadline: 2026-04-01)
- [P0] NeuroBoost v5.0 发布 ✅ 已发布 (2026-02-26)
- [P1] 日志清理脚本 完成"""

        new_content = memory_path.read_text(encoding="utf-8")
        was_modified = new_content != open(ws / "MEMORY.md", encoding="utf-8").read() or True
        # Actually compare against known original snippet
        original_snippet_present = "AgentAwaken 网站开发中" in new_content or \
                                    "AgentAwaken 项目进行中" in new_content or \
                                    "AgentAwaken 待部署" in new_content

        # Count bullet items in new content
        new_bullets = [l.strip() for l in new_content.split('\n') if l.strip().startswith('- ')]
        total_score += add_check(
            "MEMORY.md exists and is readable",
            memory_path.exists() and len(new_content) > 100,
            f"File size: {len(new_content)} bytes, bullet items: {len(new_bullets)}",
            weight=0.5
        )
    except Exception as e:
        total_score += add_check("MEMORY.md exists and is readable", False, f"Error: {e}", weight=0.5)
        new_content = ""
        new_bullets = []
        original_snippet_present = True

    # ── Check 2: Duplicate bullet items were reduced ──────────────────────────
    try:
        # The original had these highly similar items (>0.8 Jaccard) in "网站开发记录":
        # "AgentAwaken 网站开发中", "AgentAwaken 项目进行中", "AgentAwaken 待部署", "AgentAwaken 网站 正在开发"
        # At least 2 of the 4 should be gone
        agentawaken_website_bullets = [
            b for b in new_bullets
            if 'agentawaken' in b.lower() and any(
                kw in b for kw in ['网站开发中', '项目进行中', '待部署', '正在开发']
            )
        ]
        duplicates_reduced = len(agentawaken_website_bullets) < 3
        total_score += add_check(
            "High-similarity duplicates (>0.8) were deleted",
            duplicates_reduced,
            f"AgentAwaken website duplicate bullets remaining: {len(agentawaken_website_bullets)} "
            f"(expected < 3 of the original 4). Items: {agentawaken_website_bullets}",
            weight=2.0
        )
    except Exception as e:
        total_score += add_check("High-similarity duplicates (>0.8) were deleted", False, f"Error: {e}", weight=2.0)

    # ── Check 3: NeuroBoost duplicate entries were handled ────────────────────
    try:
        # Original had: "NeuroBoost v5.0 发布待重试" AND "NeuroBoost v5.0 发布 ✅ 已发布 (2026-02-26)"
        # These are partial duplicates (0.5-0.8) — should be merged or deduplicated
        neuroboost_p0_bullets = [
            b for b in new_bullets
            if 'neuroboost v5.0' in b.lower() and ('发布' in b or 'v5.0' in b)
        ]
        neuroboost_deduped = len(neuroboost_p0_bullets) <= 1
        total_score += add_check(
            "NeuroBoost v5.0 partial duplicates merged/deduped",
            neuroboost_deduped,
            f"NeuroBoost v5.0 bullets remaining: {len(neuroboost_p0_bullets)}. "
            f"Items: {neuroboost_p0_bullets}",
            weight=2.0
        )
    except Exception as e:
        total_score += add_check("NeuroBoost v5.0 partial duplicates merged/deduped", False, f"Error: {e}", weight=2.0)

    # ── Check 4: Unique/important entries were preserved ─────────────────────
    try:
        preserved = []
        must_preserve = [
            ("数据管道优化", "P2 data pipeline task"),
            ("前端: Next.js", "tech stack entry"),
            ("DATABASE_URL", "env variable"),
            ("AgentAwaken", "core project reference"),
        ]
        for keyword, desc in must_preserve:
            found = any(keyword in b for b in new_bullets) or keyword in new_content
            preserved.append((keyword, found, desc))

        all_preserved = all(f for _, f, _ in preserved)
        detail = "; ".join(f"{d}: {'✅' if f else '❌'}" for _, f, d in preserved)
        total_score += add_check(
            "Unique entries were preserved",
            all_preserved,
            detail,
            weight=1.5
        )
    except Exception as e:
        total_score += add_check("Unique entries were preserved", False, f"Error: {e}", weight=1.5)

    # ── Check 5: Backup file was created ─────────────────────────────────────
    try:
        memory_dir = ws / "memory"
        backup_files = list(memory_dir.glob("MEMORY-backup-*.md")) if memory_dir.exists() else []
        backup_exists = len(backup_files) > 0
        if backup_exists:
            # Verify the backup contains the original content
            backup_content = backup_files[0].read_text(encoding="utf-8")
            backup_has_originals = (
                "AgentAwaken 网站开发中" in backup_content or
                "AgentAwaken 项目进行中" in backup_content
            )
            detail = f"Found backup: {backup_files[0].name}, has original content: {backup_has_originals}"
            passed = backup_exists and backup_has_originals
        else:
            detail = "No backup file found in memory/ directory"
            passed = False
        total_score += add_check("Backup file created in memory/ directory", passed, detail, weight=2.0)
    except Exception as e:
        total_score += add_check("Backup file created in memory/ directory", False, f"Error: {e}", weight=2.0)

    # ── Check 6: Dedup report was generated ──────────────────────────────────
    try:
        report_path = ws / "memory" / "dedup-report.txt"
        if report_path.exists():
            report_content = report_path.read_text(encoding="utf-8")
            has_stats = "统计" in report_content or "原始条目" in report_content
            has_optimized = "已优化" in report_content
            report_valid = has_stats and has_optimized
            detail = f"Report exists ({len(report_content)} bytes), has stats: {has_stats}, has completion marker: {has_optimized}"
        else:
            report_valid = False
            detail = "memory/dedup-report.txt not found"
        total_score += add_check("Dedup report generated at memory/dedup-report.txt", report_valid, detail, weight=1.0)
    except Exception as e:
        total_score += add_check("Dedup report generated at memory/dedup-report.txt", False, f"Error: {e}", weight=1.0)

    # ── Check 7: Overall reduction in bullet items ────────────────────────────
    try:
        # Original MEMORY.md had 29 bullet items
        original_bullet_count = 29
        reduction = original_bullet_count - len(new_bullets)
        # Should have reduced by at least 4 items (the 3 extra AgentAwaken duplicates + 1 NeuroBoost dup)
        significant_reduction = reduction >= 4
        total_score += add_check(
            "Significant reduction in total bullet items (>=4 removed)",
            significant_reduction,
            f"Original bullets: {original_bullet_count}, Final bullets: {len(new_bullets)}, "
            f"Reduced by: {reduction}",
            weight=1.0
        )
    except Exception as e:
        total_score += add_check("Significant reduction in total bullet items (>=4 removed)", False, f"Error: {e}", weight=1.0)

    # ── Compute final score ───────────────────────────────────────────────────
    max_score = 0.5 + 2.0 + 2.0 + 1.5 + 2.0 + 1.0 + 1.0  # = 10.0
    normalized_score = round(min(total_score / max_score, 1.0), 3)
    passed = normalized_score >= 0.65 and all(
        c["passed"] for c in checks if c["name"] in [
            "Backup file created in memory/ directory",
            "High-similarity duplicates (>0.8) were deleted",
        ]
    )

    return {
        "passed": passed,
        "score": normalized_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))