import sys
import os
import re
import json
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    notes_dir = Path(workspace) / "dev_notes"

    # ---- Helper ----
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # =========================================================
    # CHECK 1: Numeric-prefix top-level directories exist
    # =========================================================
    try:
        all_dirs = [d for d in notes_dir.iterdir() if d.is_dir()]
        numeric_prefix_dirs = [d for d in all_dirs if re.match(r'^\d+_', d.name)]
        # Expect at least 3 top-level numbered directories covering frontend, backend, algo/tools
        if len(numeric_prefix_dirs) >= 3:
            add_check(
                "numeric_prefix_dirs_created",
                True,
                f"Found {len(numeric_prefix_dirs)} numeric-prefix directories: {[d.name for d in numeric_prefix_dirs]}"
            )
        else:
            add_check(
                "numeric_prefix_dirs_created",
                False,
                f"Expected >=3 numeric-prefix dirs (e.g. 01_xxx/), found: {[d.name for d in all_dirs]}"
            )
    except Exception as e:
        add_check("numeric_prefix_dirs_created", False, f"Exception: {e}")

    # =========================================================
    # CHECK 2: Core notes have been MOVED (not still flat in root)
    # =========================================================
    try:
        root_md_files = list(notes_dir.glob("*.md"))
        # After reorganization, major content notes should be in subdirs
        # Allow for a few stragglers (like .gitignore / scratch) but not the main 15 notes
        if len(root_md_files) <= 2:
            add_check(
                "files_moved_to_subdirs",
                True,
                f"Only {len(root_md_files)} markdown files remain in root (good). Files: {[f.name for f in root_md_files]}"
            )
        else:
            add_check(
                "files_moved_to_subdirs",
                False,
                f"{len(root_md_files)} markdown files still in root — files not reorganized: {[f.name for f in root_md_files]}"
            )
    except Exception as e:
        add_check("files_moved_to_subdirs", False, f"Exception: {e}")

    # =========================================================
    # CHECK 3: All original 15 core notes still exist somewhere
    # =========================================================
    original_notes = [
        "react_hooks.md", "vue3_composition.md", "css_flexbox.md", "css_grid.md",
        "nodejs_express.md", "python_fastapi.md", "mysql_basics.md", "redis_cache.md",
        "docker_basics.md", "kubernetes_intro.md", "git_workflow.md",
        "sorting_algorithms.md", "binary_search.md", "design_patterns.md",
        "typescript_basics.md"
    ]
    try:
        all_md = list(notes_dir.rglob("*.md"))
        all_md_names = [f.name for f in all_md]
        missing = [n for n in original_notes if n not in all_md_names]
        if not missing:
            add_check(
                "no_files_deleted",
                True,
                "All 15 original notes are present (no data loss)."
            )
        else:
            add_check(
                "no_files_deleted",
                False,
                f"Missing notes after reorganization: {missing}"
            )
    except Exception as e:
        add_check("no_files_deleted", False, f"Exception: {e}")

    # =========================================================
    # CHECK 4: Obsidian-style bidirectional links present in files
    # The format must be: [[filename|display_name]] or [[filename]]
    # inside a > **相关链接**: block OR similar header block
    # =========================================================
    try:
        # Collect all md files in subdirectories
        subdir_mds = [f for f in notes_dir.rglob("*.md")
                      if f.parent != notes_dir and f.parent.name != "temp"]
        files_with_links = []
        obsidian_link_pattern = re.compile(r'\[\[.+?\]\]')
        related_block_pattern = re.compile(r'相关链接|related|Related')

        for md_file in subdir_mds:
            try:
                content = md_file.read_text(encoding='utf-8')
                if obsidian_link_pattern.search(content):
                    files_with_links.append(md_file.name)
            except Exception:
                pass

        ratio = len(files_with_links) / max(len(subdir_mds), 1)
        if ratio >= 0.5 and len(files_with_links) >= 5:
            add_check(
                "obsidian_links_present",
                True,
                f"{len(files_with_links)}/{len(subdir_mds)} files contain [[...]] Obsidian-style links."
            )
        else:
            add_check(
                "obsidian_links_present",
                False,
                f"Only {len(files_with_links)}/{len(subdir_mds)} files have Obsidian links. Need >= 5 and >= 50% coverage."
            )
    except Exception as e:
        add_check("obsidian_links_present", False, f"Exception: {e}")

    # =========================================================
    # CHECK 5: Links are BIDIRECTIONAL
    # If file A links to file B, file B must link back to A
    # =========================================================
    try:
        subdir_mds = [f for f in notes_dir.rglob("*.md")
                      if f.parent != notes_dir and f.parent.name != "temp"]
        link_pattern = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

        file_links = {}  # filename -> set of linked filenames (without path)
        for md_file in subdir_mds:
            try:
                content = md_file.read_text(encoding='utf-8')
                raw_links = link_pattern.findall(content)
                # Normalize: strip path, keep just filename stem or full name
                normalized = set()
                for lnk in raw_links:
                    lnk = lnk.strip()
                    if not lnk.endswith('.md'):
                        lnk = lnk + '.md'
                    normalized.add(lnk)
                file_links[md_file.name] = normalized
            except Exception:
                file_links[md_file.name] = set()

        bidirectional_pairs = 0
        one_way_violations = 0
        checked_pairs = set()

        for fname, links in file_links.items():
            for linked in links:
                pair = tuple(sorted([fname, linked]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                if linked in file_links:
                    if fname in file_links.get(linked, set()):
                        bidirectional_pairs += 1
                    else:
                        one_way_violations += 1

        if bidirectional_pairs >= 3:
            add_check(
                "bidirectional_links_verified",
                True,
                f"Found {bidirectional_pairs} confirmed bidirectional link pairs. One-way: {one_way_violations}."
            )
        else:
            add_check(
                "bidirectional_links_verified",
                False,
                f"Only {bidirectional_pairs} bidirectional pairs found (need >= 3). One-way violations: {one_way_violations}."
            )
    except Exception as e:
        add_check("bidirectional_links_verified", False, f"Exception: {e}")

    # =========================================================
    # CHECK 6: Links appear at END of files (not beginning)
    # The last non-empty lines should contain [[...]] links
    # =========================================================
    try:
        subdir_mds = [f for f in notes_dir.rglob("*.md")
                      if f.parent != notes_dir and f.parent.name != "temp"]
        obsidian_link_pattern = re.compile(r'\[\[.+?\]\]')
        end_link_count = 0
        start_link_count = 0
        checked = 0

        for md_file in subdir_mds:
            try:
                content = md_file.read_text(encoding='utf-8')
                if not obsidian_link_pattern.search(content):
                    continue
                checked += 1
                lines = content.strip().split('\n')
                # Check last 5 lines for links
                last_5 = '\n'.join(lines[-5:])
                # Check first 5 lines for links
                first_5 = '\n'.join(lines[:5])
                if obsidian_link_pattern.search(last_5):
                    end_link_count += 1
                elif obsidian_link_pattern.search(first_5):
                    start_link_count += 1
            except Exception:
                pass

        if checked == 0:
            add_check("links_at_end_of_file", False, "No files with links found to check position.")
        elif end_link_count / max(checked, 1) >= 0.6:
            add_check(
                "links_at_end_of_file",
                True,
                f"{end_link_count}/{checked} files with links have them at the end (>=60% threshold met)."
            )
        else:
            add_check(
                "links_at_end_of_file",
                False,
                f"Only {end_link_count}/{checked} files have links at end. Start: {start_link_count}. Need >=60%."
            )
    except Exception as e:
        add_check("links_at_end_of_file", False, f"Exception: {e}")

    # =========================================================
    # CHECK 7: Empty directories cleaned up
    # =========================================================
    try:
        empty_dirs = []
        for root, dirs, files in os.walk(str(notes_dir), topdown=False):
            if root == str(notes_dir):
                continue
            if not os.listdir(root):
                empty_dirs.append(root)

        if not empty_dirs:
            add_check(
                "empty_dirs_cleaned",
                True,
                "No empty directories found — cleanup was performed."
            )
        else:
            add_check(
                "empty_dirs_cleaned",
                False,
                f"Found {len(empty_dirs)} empty directories not cleaned: {empty_dirs}"
            )
    except Exception as e:
        add_check("empty_dirs_cleaned", False, f"Exception: {e}")

    # =========================================================
    # CHECK 8: Thematic grouping sanity check
    # Frontend notes (react, vue, css, typescript) should be together
    # Backend notes (express, fastapi, mysql, redis) should be together
    # =========================================================
    try:
        all_mds = list(notes_dir.rglob("*.md"))
        file_to_dir = {f.name: f.parent.name for f in all_mds}

        frontend_files = ["react_hooks.md", "vue3_composition.md", "css_flexbox.md",
                          "css_grid.md", "typescript_basics.md"]
        backend_files = ["nodejs_express.md", "python_fastapi.md", "mysql_basics.md",
                         "redis_cache.md"]

        frontend_dirs = [file_to_dir.get(f, "NOT_FOUND") for f in frontend_files
                         if f in file_to_dir]
        backend_dirs = [file_to_dir.get(f, "NOT_FOUND") for f in backend_files
                        if f in file_to_dir]

        # Most frontend files should be in same parent dir
        from collections import Counter
        frontend_dir_counts = Counter(frontend_dirs)
        backend_dir_counts = Counter(backend_dirs)

        frontend_majority = frontend_dir_counts.most_common(1)[0][1] if frontend_dir_counts else 0
        backend_majority = backend_dir_counts.most_common(1)[0][1] if backend_dir_counts else 0

        fe_ratio = frontend_majority / max(len(frontend_files), 1)
        be_ratio = backend_majority / max(len(backend_files), 1)

        if fe_ratio >= 0.6 and be_ratio >= 0.6:
            add_check(
                "thematic_grouping_correct",
                True,
                f"Frontend grouping: {dict(frontend_dir_counts)}, Backend grouping: {dict(backend_dir_counts)}"
            )
        else:
            add_check(
                "thematic_grouping_correct",
                False,
                f"Files not thematically grouped. FE ratio={fe_ratio:.2f} (dirs: {dict(frontend_dir_counts)}), "
                f"BE ratio={be_ratio:.2f} (dirs: {dict(backend_dir_counts)})"
            )
    except Exception as e:
        add_check("thematic_grouping_correct", False, f"Exception: {e}")

    # =========================================================
    # Final scoring
    # =========================================================
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks) if checks else 0.0
    all_passed = score >= 0.75  # Need at least 6/8 checks to pass

    return {
        "passed": all_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))