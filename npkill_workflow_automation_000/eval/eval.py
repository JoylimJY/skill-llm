#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path

def main(workspace: str):
    checks = []
    total_score = 0.0

    # ── CHECK 1: cleanup_preview.txt exists somewhere in workspace ────────────
    preview_files = list(Path(workspace).rglob("cleanup_preview.txt"))
    if preview_files:
        preview_path = preview_files[0]
        check1_passed = True
        check1_detail = f"Found cleanup_preview.txt at {preview_path}"
    else:
        check1_passed = False
        check1_detail = "cleanup_preview.txt not found anywhere in workspace"
    checks.append({"name": "dry_run_report_exists", "passed": check1_passed, "detail": check1_detail})
    if check1_passed:
        total_score += 0.15

    # ── CHECK 2: cleanup_preview.txt contains meaningful dry-run output ───────
    check2_passed = False
    check2_detail = "cleanup_preview.txt not found or empty"
    if check1_passed:
        try:
            content = preview_path.read_text(errors="replace").strip()
            if len(content) > 0:
                # Should mention .next or related paths or npkill output indicators
                keywords = [".next", "next", "dry", "0 space", "MB", "GB", "kB",
                            "storefront", "dashboard", "marketing", "legacy"]
                matched = [kw for kw in keywords if kw.lower() in content.lower()]
                if len(matched) >= 2:
                    check2_passed = True
                    check2_detail = f"File has meaningful content, matched keywords: {matched}"
                else:
                    check2_detail = f"File content too sparse or unrelated. Content preview: {content[:200]}"
            else:
                check2_detail = "cleanup_preview.txt is empty"
        except Exception as e:
            check2_detail = f"Error reading cleanup_preview.txt: {e}"
    checks.append({"name": "dry_run_report_has_content", "passed": check2_passed, "detail": check2_detail})
    if check2_passed:
        total_score += 0.10

    # ── CHECK 3: .next folders under projects/ are DELETED ───────────────────
    projects_dir = Path(workspace) / "projects"
    remaining_next = list(projects_dir.rglob(".next"))
    remaining_next_dirs = [p for p in remaining_next if p.is_dir()]

    # We expect ALL .next folders inside projects/ to be gone
    if len(remaining_next_dirs) == 0:
        check3_passed = True
        check3_detail = "All .next folders under projects/ have been deleted"
    else:
        check3_passed = False
        surviving = [str(p.relative_to(workspace)) for p in remaining_next_dirs]
        check3_detail = f"These .next folders still exist under projects/: {surviving}"
    checks.append({"name": "next_folders_deleted_in_projects", "passed": check3_passed, "detail": check3_detail})
    if check3_passed:
        total_score += 0.35

    # ── CHECK 4: node_modules under projects/ are PRESERVED ──────────────────
    remaining_nm = list(projects_dir.rglob("node_modules"))
    remaining_nm_dirs = [p for p in remaining_nm if p.is_dir()]

    # We expect all node_modules to still be intact (task is .next only)
    expected_nm_projects = {"storefront", "dashboard", "legacy-app", "api-service", "shared-ui", "mobile"}
    found_nm_projects = set()
    for p in remaining_nm_dirs:
        # get the immediate child of projects/
        try:
            rel = p.relative_to(projects_dir)
            top_level = rel.parts[0]
            found_nm_projects.add(top_level)
        except Exception:
            pass

    missing_nm = expected_nm_projects - found_nm_projects
    if len(missing_nm) == 0:
        check4_passed = True
        check4_detail = f"All node_modules preserved: {sorted(found_nm_projects)}"
    else:
        check4_passed = False
        check4_detail = f"node_modules were incorrectly deleted in projects: {sorted(missing_nm)}"
    checks.append({"name": "node_modules_preserved", "passed": check4_passed, "detail": check4_detail})
    if check4_passed:
        total_score += 0.25

    # ── CHECK 5: vendor/ .next and node_modules are UNTOUCHED ─────────────────
    vendor_dir = Path(workspace) / "vendor"
    vendor_next_dirs = list(vendor_dir.rglob(".next")) if vendor_dir.exists() else []
    vendor_nm_dirs = list(vendor_dir.rglob("node_modules")) if vendor_dir.exists() else []

    vendor_next_intact = any(p.is_dir() for p in vendor_next_dirs)
    vendor_nm_intact = any(p.is_dir() for p in vendor_nm_dirs)

    if vendor_next_intact and vendor_nm_intact:
        check5_passed = True
        check5_detail = "vendor/ directory untouched: both .next and node_modules preserved"
    elif not vendor_dir.exists():
        check5_passed = False
        check5_detail = "vendor/ directory does not exist at all - was it accidentally deleted?"
    else:
        missing_parts = []
        if not vendor_next_intact:
            missing_parts.append(".next")
        if not vendor_nm_intact:
            missing_parts.append("node_modules")
        check5_passed = False
        check5_detail = f"vendor/ had these incorrectly removed: {missing_parts}"
    checks.append({"name": "vendor_directory_untouched", "passed": check5_passed, "detail": check5_detail})
    if check5_passed:
        total_score += 0.15

    # ── FINAL ─────────────────────────────────────────────────────────────────
    all_passed = all(c["passed"] for c in checks)
    result = {
        "passed": all_passed,
        "score": round(total_score, 2),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path argument provided"}
        ]}))
        sys.exit(1)
    main(sys.argv[1])