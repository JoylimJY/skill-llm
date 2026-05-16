#!/usr/bin/env python3
"""
Evaluation script for agent-memory-system task.
Checks:
1. New lesson file created with correct proprietary frontmatter format
2. Cold daily logs archived to .archive/YYYY-MM/ directories
3. extract-skill.sh was run, producing skills/production-db-rollback/SKILL.md
4. MEMORY.md updated with new lesson entry and stays under 5KB
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

def evaluate(workspace: str) -> dict:
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    
    # ── CHECK 1: New lesson file exists with correct frontmatter ──────────────
    def check_lesson_file():
        """
        Agent must create memory/lessons/production-db-rollback.md
        with proper frontmatter including:
        - title (non-empty string)
        - date (YYYY-MM-DD)
        - category: lessons
        - lesson_id: LRN-YYYYMMDD-XXX format (proprietary!)
        - priority: 🔴 or 🟡 or 🟢 (emoji, not text)
        - status: active
        """
        lesson_path = ws / "memory" / "lessons" / "production-db-rollback.md"
        if not lesson_path.exists():
            return False, "Lesson file memory/lessons/production-db-rollback.md not found"
        
        try:
            content = lesson_path.read_text(encoding="utf-8")
        except Exception as e:
            return False, f"Could not read lesson file: {e}"
        
        issues = []
        
        # Must have YAML frontmatter
        if not content.startswith("---"):
            issues.append("Missing YAML frontmatter (must start with ---)")
        
        # Check lesson_id format: LRN-YYYYMMDD-XXX
        lid_match = re.search(r'lesson_id:\s*(\S+)', content)
        if not lid_match:
            issues.append("Missing lesson_id field")
        else:
            lid = lid_match.group(1)
            if not re.match(r'^LRN-\d{8}-\d{3}$', lid):
                issues.append(f"lesson_id '{lid}' does not match required format LRN-YYYYMMDD-XXX")
        
        # Check priority is emoji
        pri_match = re.search(r'priority:\s*(.+)', content)
        if not pri_match:
            issues.append("Missing priority field")
        else:
            pri = pri_match.group(1).strip()
            valid_priorities = ['🔴', '🟡', '🟢']
            if not any(ep in pri for ep in valid_priorities):
                issues.append(f"priority '{pri}' must be an emoji (🔴/🟡/🟢), not plain text")
        
        # Check category: lessons
        cat_match = re.search(r'category:\s*(\S+)', content)
        if not cat_match:
            issues.append("Missing category field")
        else:
            cat = cat_match.group(1).strip()
            if cat != "lessons":
                issues.append(f"category must be 'lessons', got '{cat}'")
        
        # Check status: active
        sta_match = re.search(r'status:\s*(\S+)', content)
        if not sta_match:
            issues.append("Missing status field")
        else:
            sta = sta_match.group(1).strip()
            if sta != "active":
                issues.append(f"status must be 'active', got '{sta}'")
        
        # Check title is present and non-empty
        title_match = re.search(r'title:\s*"?([^"\n]+)"?', content)
        if not title_match or not title_match.group(1).strip():
            issues.append("Missing or empty title field")
        
        # Check date field
        date_match = re.search(r'\bdate:\s*(\S+)', content)
        if not date_match:
            issues.append("Missing date field")
        else:
            date_val = date_match.group(1).strip()
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_val):
                issues.append(f"date '{date_val}' must be YYYY-MM-DD format")
        
        # Check has substantive sections (at least ## 背景 or ## 问题 or ## 解决方案)
        has_sections = any(s in content for s in ['## 背景', '## 问题', '## 解决方案', '## Background', '## Problem', '## Solution'])
        if not has_sections:
            issues.append("Lesson content must include structured sections (## 背景, ## 问题, etc.)")
        
        if issues:
            return False, "Lesson file issues: " + "; ".join(issues)
        return True, f"Lesson file correct with lesson_id={lid_match.group(1)}, priority={pri_match.group(1).strip()}"
    
    passed, detail = check_lesson_file()
    checks.append({"name": "lesson_file_correct_format", "passed": passed, "detail": detail})
    if passed:
        total_score += 0.30
    
    # ── CHECK 2: Cold logs archived to .archive/YYYY-MM/ ─────────────────────
    def check_archive():
        """
        Cold daily logs (>30 days old, dated 45-62 days ago) must be moved
        to .archive/YYYY-MM/ directories. The files should NOT remain in memory/.
        """
        archive_dir = ws / "memory" / ".archive"
        memory_dir = ws / "memory"
        
        # Calculate expected cold dates (45, 50, 53, 58, 62 days ago)
        today = datetime.now()
        cold_dates = [today - timedelta(days=d) for d in [45, 50, 53, 58, 62]]
        cold_filenames = {dt.strftime("%Y-%m-%d") + ".md" for dt in cold_dates}
        cold_year_months = {dt.strftime("%Y-%m") for dt in cold_dates}
        
        issues = []
        archived_count = 0
        
        for fname in cold_filenames:
            # Should NOT be in memory/ root
            if (memory_dir / fname).exists():
                issues.append(f"{fname} still in memory/ (not archived)")
                continue
            
            # Should be in .archive/YYYY-MM/
            year_month = fname[:7]  # "YYYY-MM"
            archived_path = archive_dir / year_month / fname
            if archived_path.exists():
                archived_count += 1
            else:
                # Check if it's anywhere under .archive
                found = list(archive_dir.rglob(fname))
                if found:
                    archived_count += 1
                    # But check if it's in correct YYYY-MM subdir
                    expected_dir = archive_dir / year_month
                    if found[0].parent != expected_dir:
                        issues.append(f"{fname} archived to wrong directory: {found[0].parent.name} (expected {year_month})")
                else:
                    issues.append(f"{fname} not found in .archive/ at all")
        
        # Warm logs should NOT be archived
        warm_dates_list = [today - timedelta(days=d) for d in [10, 15, 18]]
        for dt in warm_dates_list:
            fname = dt.strftime("%Y-%m-%d") + ".md"
            # Check if incorrectly archived
            found = list(archive_dir.rglob(fname))
            if found:
                issues.append(f"Warm file {fname} was incorrectly archived (only >30 days should be archived)")
        
        if not archive_dir.exists() or not any(archive_dir.iterdir()):
            return False, "Archive directory is empty — GC was not run"
        
        if issues:
            return archived_count >= 3, f"Archived {archived_count}/{len(cold_filenames)} cold files. Issues: {'; '.join(issues)}"
        
        return True, f"All {archived_count} cold log files correctly archived to .archive/YYYY-MM/ directories"
    
    passed, detail = check_archive()
    checks.append({"name": "cold_logs_archived_correctly", "passed": passed, "detail": detail})
    if passed:
        total_score += 0.30
    
    # ── CHECK 3: Skill extracted — skills/production-db-rollback/SKILL.md ────
    def check_skill_extraction():
        """
        Agent must have run extract-skill.sh to create skills/production-db-rollback/SKILL.md
        The file must:
        - Exist at skills/production-db-rollback/SKILL.md
        - Have frontmatter with name and description fields
        - Reference the source lesson
        - Have some non-template content (not just TODO placeholders)
        """
        skill_path = ws / "skills" / "production-db-rollback" / "SKILL.md"
        if not skill_path.exists():
            # Try rglob as fallback
            found = list((ws / "skills").rglob("SKILL.md")) if (ws / "skills").exists() else []
            if not found:
                return False, "skills/production-db-rollback/SKILL.md not found; extract-skill.sh was not run"
            skill_path = found[0]
            if "production-db-rollback" not in str(skill_path):
                return False, f"Found SKILL.md but not for production-db-rollback: {skill_path}"
        
        try:
            content = skill_path.read_text(encoding="utf-8")
        except Exception as e:
            return False, f"Could not read skill file: {e}"
        
        issues = []
        
        # Must have frontmatter
        if not content.startswith("---"):
            issues.append("Missing YAML frontmatter")
        
        # Must have name field
        if not re.search(r'^name:', content, re.MULTILINE):
            issues.append("Missing 'name' field in frontmatter")
        
        # Must have description
        if not re.search(r'^description:', content, re.MULTILINE):
            issues.append("Missing 'description' field in frontmatter")
        
        # Must reference source lesson (production-db-rollback)
        if "production-db-rollback" not in content and "production_db_rollback" not in content:
            issues.append("SKILL.md does not reference source lesson 'production-db-rollback'")
        
        # File should have been created (not just template stubs everywhere)
        # At minimum the auto-generated content from extract-skill.sh should be there
        if len(content.strip()) < 100:
            issues.append("SKILL.md content too short — likely empty or corrupt")
        
        if issues:
            return False, "; ".join(issues)
        return True, f"Skill file exists at {skill_path.relative_to(ws)} with valid structure"
    
    passed, detail = check_skill_extraction()
    checks.append({"name": "skill_extracted", "passed": passed, "detail": detail})
    if passed:
        total_score += 0.20
    
    # ── CHECK 4: MEMORY.md updated with new lesson + under 5KB ───────────────
    def check_memory_md():
        """
        MEMORY.md must:
        - Exist and be under 5KB (5120 bytes)
        - Contain a reference to the new lesson (production-db-rollback or its LRN-* ID)
        - Have the lesson entry in the experience index table
        """
        memory_path = ws / "MEMORY.md"
        if not memory_path.exists():
            return False, "MEMORY.md does not exist"
        
        try:
            content = memory_path.read_text(encoding="utf-8")
            size_bytes = memory_path.stat().st_size
        except Exception as e:
            return False, f"Could not read MEMORY.md: {e}"
        
        issues = []
        
        # Under 5KB = 5120 bytes
        if size_bytes >= 5120:
            issues.append(f"MEMORY.md is {size_bytes} bytes, must be < 5120 bytes (5KB)")
        
        # Must reference new lesson (either by name or LRN ID)
        has_lesson_ref = (
            "production-db-rollback" in content or
            "production_db_rollback" in content or
            re.search(r'LRN-\d{8}-00[2-9]', content) is not None or  # new LRN ID (002+)
            "数据库回滚" in content or
            "db-rollback" in content.lower() or
            "DB回滚" in content
        )
        if not has_lesson_ref:
            issues.append("MEMORY.md does not reference the new production-db-rollback lesson")
        
        # Should still have the original content (not completely overwritten)
        if "API 超时处理" not in content and "LRN-20241110-001" not in content:
            issues.append("MEMORY.md seems to have lost the original lesson index entry (LRN-20241110-001)")
        
        if issues:
            return False, "; ".join(issues)
        return True, f"MEMORY.md is {size_bytes} bytes (<5KB) and references new lesson"
    
    passed, detail = check_memory_md()
    checks.append({"name": "memory_md_updated_and_under_5kb", "passed": passed, "detail": detail})
    if passed:
        total_score += 0.20
    
    # ── FINAL SCORE ───────────────────────────────────────────────────────────
    all_passed = all(c["passed"] for c in checks)
    
    return {
        "passed": all_passed,
        "score": round(total_score, 2),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument_error", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))