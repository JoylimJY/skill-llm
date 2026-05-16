#!/usr/bin/env python3
"""
Evaluation script for PureRoot Botanicals SEO memory management task.
Checks:
1. Hot-cache.md trimmed to ≤80 lines
2. Stale WARM files (>90 days) archived to memory/archive/ with YYYY-MM-DD- prefix
3. Archived files keep original filename (with date prefix)
4. Frontmatter issues identified/fixed in the three defective files
5. Bakuchiol opportunity promoted to hot-cache.md (≤3 line summary)
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

def run_eval(workspace: str) -> dict:
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # ─────────────────────────────────────────────────────────────────
    # CHECK 1: hot-cache.md ≤ 80 lines
    # ─────────────────────────────────────────────────────────────────
    hot_cache_path = ws / "memory" / "hot-cache.md"
    try:
        content = hot_cache_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        line_count = len(lines)
        passed = line_count <= 80
        add_check(
            "hot_cache_line_limit",
            passed,
            f"hot-cache.md has {line_count} lines (must be ≤80)",
            weight=2.0
        )
    except Exception as e:
        add_check("hot_cache_line_limit", False, f"Error reading hot-cache.md: {e}", weight=2.0)

    # ─────────────────────────────────────────────────────────────────
    # CHECK 2: Stale files archived — presence in memory/archive/
    # We check that the 4 files older than 90 days have been archived
    # ─────────────────────────────────────────────────────────────────
    archive_dir = ws / "memory" / "archive"
    
    # Expected original filenames (without date prefix)
    stale_files = [
        "hero-keywords-initial.md",
        "innisfree-analysis-old.md", 
        "corewebvitals-audit-q1.md",
        "algorithm-update-mar.md",
    ]

    try:
        archive_files = list(archive_dir.iterdir()) if archive_dir.exists() else []
        archive_names = [f.name for f in archive_files]
    except Exception as e:
        archive_files = []
        archive_names = []

    # Check each stale file was archived with YYYY-MM-DD- prefix pattern
    DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")
    
    archived_count = 0
    missing_archives = []
    
    for stale_fn in stale_files:
        # Look for any archive file that ends with the original name and has date prefix
        found = any(
            DATE_PREFIX.match(arc_name) and arc_name.endswith(stale_fn)
            for arc_name in archive_names
        )
        if found:
            archived_count += 1
        else:
            missing_archives.append(stale_fn)

    add_check(
        "stale_files_archived_count",
        archived_count >= 3,  # at least 3 of 4 must be archived
        f"{archived_count}/4 stale files (>90 days) archived to memory/archive/. "
        f"Missing: {missing_archives if missing_archives else 'none'}",
        weight=2.0
    )

    # CHECK 2b: All archived files have valid YYYY-MM-DD- date prefix
    try:
        archive_files_list = list(archive_dir.iterdir()) if archive_dir.exists() else []
        correctly_prefixed = [f for f in archive_files_list if DATE_PREFIX.match(f.name)]
        incorrectly_named = [f.name for f in archive_files_list if not DATE_PREFIX.match(f.name) and f.name != ".gitkeep"]
        passed = len(incorrectly_named) == 0
        add_check(
            "archive_filename_date_prefix",
            passed,
            f"All archived files have YYYY-MM-DD- prefix: {passed}. "
            f"Incorrectly named: {incorrectly_named if incorrectly_named else 'none'}",
            weight=1.5
        )
    except Exception as e:
        add_check("archive_filename_date_prefix", False, f"Error checking archive filenames: {e}", weight=1.5)

    # CHECK 2c: Original stale files removed from their original WARM locations
    original_stale_paths = [
        ws / "memory" / "research" / "keywords" / "hero-keywords-initial.md",
        ws / "memory" / "research" / "competitors" / "innisfree-analysis-old.md",
        ws / "memory" / "audits" / "technical" / "corewebvitals-audit-q1.md",
        ws / "memory" / "monitoring" / "alerts" / "algorithm-update-mar.md",
    ]
    still_present = [str(p.relative_to(ws)) for p in original_stale_paths if p.exists()]
    removed_count = len(original_stale_paths) - len(still_present)
    add_check(
        "stale_files_removed_from_warm",
        removed_count >= 3,
        f"{removed_count}/4 original stale files removed from WARM storage. "
        f"Still present: {still_present if still_present else 'none'}",
        weight=1.5
    )

    # ─────────────────────────────────────────────────────────────────
    # CHECK 3: Bakuchiol opportunity promoted to hot-cache.md
    # Must appear as ≤3 line summary in hot-cache.md
    # ─────────────────────────────────────────────────────────────────
    try:
        hot_content = hot_cache_path.read_text(encoding="utf-8")
        # Check for bakuchiol mention in hot cache
        has_bakuchiol = "bakuchiol" in hot_content.lower()
        
        # Verify it's a summary (not a full dump) — check that the word count
        # near any bakuchiol mention is concise
        if has_bakuchiol:
            # Find lines containing bakuchiol
            hot_lines = hot_content.splitlines()
            bak_lines = [l for l in hot_lines if "bakuchiol" in l.lower()]
            # A promoted summary should be ≤3 lines about bakuchiol
            concise = len(bak_lines) <= 3
            add_check(
                "bakuchiol_promoted_to_hot_cache",
                True,
                f"Bakuchiol opportunity found in hot-cache.md across {len(bak_lines)} line(s). "
                f"Concise (≤3 lines): {concise}",
                weight=2.0
            )
            add_check(
                "bakuchiol_summary_concise",
                concise,
                f"Bakuchiol summary uses {len(bak_lines)} line(s) in hot-cache.md (must be ≤3)",
                weight=1.0
            )
        else:
            add_check(
                "bakuchiol_promoted_to_hot_cache",
                False,
                "Bakuchiol opportunity NOT found in hot-cache.md — promotion from WARM missed",
                weight=2.0
            )
            add_check(
                "bakuchiol_summary_concise",
                False,
                "Cannot check conciseness: bakuchiol not in hot-cache.md",
                weight=1.0
            )
    except Exception as e:
        add_check("bakuchiol_promoted_to_hot_cache", False, f"Error reading hot-cache: {e}", weight=2.0)
        add_check("bakuchiol_summary_concise", False, f"Error: {e}", weight=1.0)

    # ─────────────────────────────────────────────────────────────────
    # CHECK 4: Frontmatter audit — files with missing fields identified/fixed
    # 
    # Defective files:
    # A) memory/research/serp/hero-serp-snapshot.md — missing 'type'
    # B) memory/content/briefs/organic-serum-pillar-brief.md — missing 'name'
    # C) memory/audits/domain/da-audit-current.md — missing 'description'
    # ─────────────────────────────────────────────────────────────────
    
    def extract_frontmatter_fields(file_path: Path) -> set:
        """Extract which of name/description/type are present in YAML frontmatter."""
        try:
            text = file_path.read_text(encoding="utf-8")
            if not text.startswith("---"):
                return set()
            # Find closing ---
            end = text.find("---", 3)
            if end == -1:
                return set()
            fm_block = text[3:end]
            present = set()
            for field in ["name", "description", "type"]:
                if re.search(rf"^{field}\s*:", fm_block, re.MULTILINE):
                    present.add(field)
            return present
        except Exception:
            return set()

    # Check if defective files were fixed OR if a report was created documenting them
    
    # File A: hero-serp-snapshot.md should now have 'type'
    serp_path = ws / "memory" / "research" / "serp" / "hero-serp-snapshot.md"
    try:
        fields_a = extract_frontmatter_fields(serp_path)
        passed_a = "type" in fields_a
        add_check(
            "frontmatter_fix_serp_snapshot_type",
            passed_a,
            f"hero-serp-snapshot.md has 'type' in frontmatter: {passed_a}. "
            f"Present fields: {fields_a}",
            weight=1.0
        )
    except Exception as e:
        add_check("frontmatter_fix_serp_snapshot_type", False, f"Error: {e}", weight=1.0)

    # File B: organic-serum-pillar-brief.md should now have 'name'
    brief_path = ws / "memory" / "content" / "briefs" / "organic-serum-pillar-brief.md"
    try:
        fields_b = extract_frontmatter_fields(brief_path)
        passed_b = "name" in fields_b
        add_check(
            "frontmatter_fix_brief_name",
            passed_b,
            f"organic-serum-pillar-brief.md has 'name' in frontmatter: {passed_b}. "
            f"Present fields: {fields_b}",
            weight=1.0
        )
    except Exception as e:
        add_check("frontmatter_fix_brief_name", False, f"Error: {e}", weight=1.0)

    # File C: da-audit-current.md should now have 'description'
    da_path = ws / "memory" / "audits" / "domain" / "da-audit-current.md"
    try:
        fields_c = extract_frontmatter_fields(da_path)
        passed_c = "description" in fields_c
        add_check(
            "frontmatter_fix_da_audit_description",
            passed_c,
            f"da-audit-current.md has 'description' in frontmatter: {passed_c}. "
            f"Present fields: {fields_c}",
            weight=1.0
        )
    except Exception as e:
        add_check("frontmatter_fix_da_audit_description", False, f"Error: {e}", weight=1.0)

    # ─────────────────────────────────────────────────────────────────
    # CHECK 5: Hot-cache.md still contains core project content
    # (Not just gutted — must retain hero keywords, competitors, metrics)
    # ─────────────────────────────────────────────────────────────────
    try:
        hot_content = hot_cache_path.read_text(encoding="utf-8")
        has_hero_kw = "organic face serum" in hot_content.lower() or "hero keyword" in hot_content.lower()
        has_competitors = "beautycounter" in hot_content.lower() or "competitor" in hot_content.lower()
        has_metrics = "organic session" in hot_content.lower() or "metric" in hot_content.lower() or "rank" in hot_content.lower()
        
        substance_preserved = has_hero_kw and has_competitors
        add_check(
            "hot_cache_retains_core_content",
            substance_preserved,
            f"Hot-cache retains: hero_kw={has_hero_kw}, competitors={has_competitors}, metrics={has_metrics}",
            weight=1.5
        )
    except Exception as e:
        add_check("hot_cache_retains_core_content", False, f"Error: {e}", weight=1.5)

    # ─────────────────────────────────────────────────────────────────
    # CHECK 6: Archive directory is not empty and has reasonable content
    # ─────────────────────────────────────────────────────────────────
    try:
        archive_files_final = list(archive_dir.iterdir()) if archive_dir.exists() else []
        non_hidden = [f for f in archive_files_final if not f.name.startswith(".")]
        has_archives = len(non_hidden) >= 3
        add_check(
            "archive_directory_populated",
            has_archives,
            f"memory/archive/ contains {len(non_hidden)} files (need ≥3): "
            f"{[f.name for f in non_hidden[:6]]}",
            weight=1.0
        )
    except Exception as e:
        add_check("archive_directory_populated", False, f"Error checking archive dir: {e}", weight=1.0)

    # ─────────────────────────────────────────────────────────────────
    # Final scoring
    # ─────────────────────────────────────────────────────────────────
    overall_passed = all(c["passed"] for c in checks)
    score = round(total_score / max_score, 3) if max_score > 0 else 0.0
    # Require score > 0.7 for overall pass
    overall_passed = score >= 0.70

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "arg_error", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    
    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))