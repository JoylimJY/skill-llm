import sys
import os
import json
import subprocess
from pathlib import Path
import re

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def main():
    # BrainRepo is always at ~/Documents/brainrepo/ (fixed path per SKILL.md)
    brain = Path("/root/Documents/brainrepo")
    checks = []

    # ─────────────────────────────────────────────
    # CHECK 1: Core directory structure exists
    # ─────────────────────────────────────────────
    required_dirs = [
        "Inbox", "Projects", "Areas", "Notes",
        "Resources", "Journal", "People", "Tasks", "Archive"
    ]
    missing_dirs = [d for d in required_dirs if not (brain / d).is_dir()]
    checks.append(check(
        "core_directory_structure",
        len(missing_dirs) == 0,
        f"Missing dirs: {missing_dirs}" if missing_dirs else "All required top-level directories present"
    ))

    # ─────────────────────────────────────────────
    # CHECK 2: Tasks/index.md exists and has checkbox format
    # ─────────────────────────────────────────────
    tasks_file = brain / "Tasks" / "index.md"
    tasks_content = load_file(tasks_file)
    if tasks_content is None:
        checks.append(check("tasks_index_exists", False, "Tasks/index.md not found"))
        tasks_ok = False
    else:
        has_checkbox = "- [ ]" in tasks_content
        has_invoice_task = re.search(r"invoice|acme|ACME|Invoice", tasks_content, re.IGNORECASE) is not None
        task_passed = has_checkbox and has_invoice_task
        checks.append(check(
            "tasks_index_content",
            task_passed,
            f"has_checkbox={has_checkbox}, has_invoice_task={has_invoice_task}. Content snippet: {tasks_content[:300]}"
        ))
        tasks_ok = task_passed

    # ─────────────────────────────────────────────
    # CHECK 3: People/sarah-chen.md exists with correct naming and frontmatter
    # ─────────────────────────────────────────────
    # File naming: firstname-lastname.md (kebab-case)
    people_dir = brain / "People"
    people_files = list(people_dir.glob("*.md")) if people_dir.is_dir() else []
    sarah_file = None
    for f in people_files:
        if "sarah" in f.name.lower() and "chen" in f.name.lower():
            sarah_file = f
            break

    if sarah_file is None:
        checks.append(check("people_sarah_chen_file", False, 
                           f"No file found for Sarah Chen in People/. Files present: {[f.name for f in people_files]}"))
        checks.append(check("people_sarah_chen_frontmatter", False, "File not found"))
        checks.append(check("people_sarah_chen_naming", False, "File not found"))
    else:
        # Check kebab-case naming convention
        correct_name = sarah_file.name == "sarah-chen.md"
        checks.append(check(
            "people_sarah_chen_naming",
            correct_name,
            f"File name is '{sarah_file.name}', expected 'sarah-chen.md'"
        ))
        
        sarah_content = load_file(sarah_file)
        checks.append(check("people_sarah_chen_file", True, f"Found: {sarah_file.name}"))
        
        # Check frontmatter
        has_frontmatter = sarah_content.startswith("---") if sarah_content else False
        has_created = re.search(r"created:\s*\d{4}-\d{2}-\d{2}", sarah_content or "") is not None
        has_tags = "tags:" in (sarah_content or "")
        has_meridian_or_context = re.search(r"meridian|product manager|accessibility|health|summit", 
                                             sarah_content or "", re.IGNORECASE) is not None
        
        fm_passed = has_frontmatter and has_created and has_tags
        checks.append(check(
            "people_sarah_chen_frontmatter",
            fm_passed,
            f"has_frontmatter={has_frontmatter}, has_created={has_created}, has_tags={has_tags}, has_context={has_meridian_or_context}"
        ))
        checks.append(check(
            "people_sarah_chen_context",
            has_meridian_or_context,
            f"Content includes Meridian/PM/accessibility context: {has_meridian_or_context}"
        ))

    # ─────────────────────────────────────────────
    # CHECK 4: Projects/meridian-health-app-audit/ exists with index.md
    # ─────────────────────────────────────────────
    projects_dir = brain / "Projects"
    project_folders = [d for d in projects_dir.iterdir() if d.is_dir()] if projects_dir.is_dir() else []
    meridian_project = None
    for d in project_folders:
        if "meridian" in d.name.lower():
            meridian_project = d
            break

    if meridian_project is None:
        checks.append(check("project_meridian_folder", False, 
                           f"No Meridian project folder in Projects/. Folders: {[d.name for d in project_folders]}"))
        checks.append(check("project_meridian_index", False, "Project folder not found"))
        checks.append(check("project_meridian_frontmatter", False, "Project folder not found"))
    else:
        checks.append(check("project_meridian_folder", True, f"Found: {meridian_project.name}"))
        
        index_file = meridian_project / "index.md"
        index_content = load_file(index_file)
        
        if index_content is None:
            checks.append(check("project_meridian_index", False, "Projects/<name>/index.md not found"))
            checks.append(check("project_meridian_frontmatter", False, "index.md not found"))
        else:
            checks.append(check("project_meridian_index", True, "index.md exists"))
            
            # Check required frontmatter fields per SKILL.md template
            has_frontmatter = index_content.startswith("---")
            has_status_active = re.search(r"status:\s*active", index_content) is not None
            has_deadline = re.search(r"deadline:\s*2025-09-30", index_content) is not None
            has_created = re.search(r"created:\s*\d{4}-\d{2}-\d{2}", index_content) is not None
            has_tags_project = re.search(r"tags:.*project", index_content) is not None
            has_goals = re.search(r"## Goals", index_content) is not None
            has_log = re.search(r"## Log", index_content) is not None
            
            fm_ok = has_frontmatter and has_status_active and has_created
            checks.append(check(
                "project_meridian_frontmatter",
                fm_ok,
                f"frontmatter={has_frontmatter}, status_active={has_status_active}, deadline={has_deadline}, created={has_created}, goals={has_goals}, log={has_log}"
            ))
            checks.append(check(
                "project_meridian_deadline",
                has_deadline,
                f"Deadline 2025-09-30 present: {has_deadline}"
            ))

    # ─────────────────────────────────────────────
    # CHECK 5: Notes/ contains a note about "Progressive Disclosure"
    # ─────────────────────────────────────────────
    notes_dir = brain / "Notes"
    notes_files = list(notes_dir.glob("*.md")) if notes_dir.is_dir() else []
    progressive_note = None
    for f in notes_files:
        content = load_file(f) or ""
        if re.search(r"progressive.?disclosure", content, re.IGNORECASE) or \
           re.search(r"progressive.?disclosure", f.name, re.IGNORECASE):
            progressive_note = f
            break

    if progressive_note is None:
        checks.append(check("notes_progressive_disclosure", False, 
                           f"No note about Progressive Disclosure in Notes/. Files: {[f.name for f in notes_files]}"))
        checks.append(check("notes_progressive_kebab_name", False, "Note not found"))
        checks.append(check("notes_progressive_frontmatter", False, "Note not found"))
    else:
        checks.append(check("notes_progressive_disclosure", True, f"Found: {progressive_note.name}"))
        
        # Check kebab-case naming
        is_kebab = bool(re.match(r'^[a-z0-9]+(-[a-z0-9]+)*\.md$', progressive_note.name))
        checks.append(check(
            "notes_progressive_kebab_name",
            is_kebab,
            f"File name '{progressive_note.name}' is kebab-case: {is_kebab}"
        ))
        
        content = load_file(progressive_note) or ""
        has_frontmatter = content.startswith("---")
        has_created = re.search(r"created:\s*\d{4}-\d{2}-\d{2}", content) is not None
        has_tags = "tags:" in content
        checks.append(check(
            "notes_progressive_frontmatter",
            has_frontmatter and has_created and has_tags,
            f"frontmatter={has_frontmatter}, created={has_created}, tags={has_tags}"
        ))

    # ─────────────────────────────────────────────
    # CHECK 6: Resources/ contains a11y checklist article
    # ─────────────────────────────────────────────
    resources_dir = brain / "Resources"
    resource_files = list(resources_dir.rglob("*.md")) if resources_dir.is_dir() else []
    a11y_resource = None
    for f in resource_files:
        content = load_file(f) or ""
        if re.search(r"a11y|accessibility.*checklist|wcag|a11yproject", content, re.IGNORECASE) or \
           re.search(r"a11y|accessibility", f.name, re.IGNORECASE):
            a11y_resource = f
            break

    if a11y_resource is None:
        checks.append(check("resources_a11y_article", False, 
                           f"No a11y article in Resources/. Files: {[str(f.relative_to(brain)) for f in resource_files]}"))
        checks.append(check("resources_a11y_has_url", False, "Resource not found"))
    else:
        checks.append(check("resources_a11y_article", True, f"Found: {a11y_resource.name}"))
        content = load_file(a11y_resource) or ""
        has_url = "a11yproject.com" in content or "https://" in content
        checks.append(check(
            "resources_a11y_has_url",
            has_url,
            f"Resource includes source URL: {has_url}"
        ))

    # ─────────────────────────────────────────────
    # CHECK 7: Journal/2025-07-14.md exists with correct structure
    # ─────────────────────────────────────────────
    journal_file = brain / "Journal" / "2025-07-14.md"
    journal_content = load_file(journal_file)

    if journal_content is None:
        checks.append(check("journal_2025_07_14_exists", False, "Journal/2025-07-14.md not found"))
        checks.append(check("journal_structure", False, "File not found"))
        checks.append(check("journal_links_to_items", False, "File not found"))
    else:
        checks.append(check("journal_2025_07_14_exists", True, "Journal/2025-07-14.md exists"))
        
        # Check for required sections per the Journal template
        has_captured_section = re.search(r"## Captured Today", journal_content) is not None
        has_progress_section = re.search(r"## Progress", journal_content) is not None
        has_frontmatter = journal_content.startswith("---")
        has_journal_tag = re.search(r"tags:.*journal", journal_content) is not None
        
        structure_ok = has_frontmatter and (has_captured_section or has_progress_section)
        checks.append(check(
            "journal_structure",
            structure_ok,
            f"frontmatter={has_frontmatter}, captured_section={has_captured_section}, progress_section={has_progress_section}, journal_tag={has_journal_tag}"
        ))
        
        # Check journal links back to created items (wiki-link style or at least mentions)
        mentions_sarah = re.search(r"sarah|chen|Sarah|Chen|\[\[People", journal_content) is not None
        mentions_meridian = re.search(r"meridian|Meridian|\[\[Projects", journal_content, re.IGNORECASE) is not None
        
        checks.append(check(
            "journal_links_to_items",
            mentions_sarah or mentions_meridian,
            f"Journal mentions Sarah: {mentions_sarah}, mentions Meridian: {mentions_meridian}"
        ))

    # ─────────────────────────────────────────────
    # CHECK 8: Git repository initialized with correct commit
    # ─────────────────────────────────────────────
    try:
        # Check git repo exists
        git_dir = brain / ".git"
        git_initialized = git_dir.is_dir()
        checks.append(check("git_initialized", git_initialized, 
                           f".git directory exists at {brain}/.git: {git_initialized}"))
        
        if git_initialized:
            # Check for the daily commit with correct message format
            result = subprocess.run(
                ["git", "log", "--oneline", "--all"],
                cwd=str(brain),
                capture_output=True,
                text=True,
                timeout=10
            )
            log_output = result.stdout.strip()
            
            # Must have commit with "daily: YYYY-MM-DD" format per SKILL.md
            has_daily_commit = bool(re.search(r"daily:\s*\d{4}-\d{2}-\d{2}", log_output))
            has_init_commit = bool(re.search(r"init.*brainrepo|initial", log_output, re.IGNORECASE))
            
            checks.append(check(
                "git_daily_commit_message",
                has_daily_commit,
                f"Commit log: {log_output[:400]}. Has 'daily: YYYY-MM-DD' commit: {has_daily_commit}"
            ))
    except Exception as e:
        checks.append(check("git_initialized", False, f"Exception checking git: {e}"))
        checks.append(check("git_daily_commit_message", False, f"Exception: {e}"))

    # ─────────────────────────────────────────────
    # CHECK 9: Wiki-links used somewhere (proprietary syntax)
    # ─────────────────────────────────────────────
    all_md_files = list(brain.rglob("*.md"))
    wikilink_found = False
    wikilink_file = ""
    for f in all_md_files:
        content = load_file(f) or ""
        if re.search(r"\[\[.+\]\]", content):
            wikilink_found = True
            wikilink_file = str(f.relative_to(brain))
            break

    checks.append(check(
        "wikilinks_used",
        wikilink_found,
        f"[[wiki-link]] syntax found in at least one file: {wikilink_found}. Example: {wikilink_file}"
    ))

    # ─────────────────────────────────────────────
    # CHECK 10: Inbox is empty or doesn't contain unprocessed items from the dump
    # (Items should have been processed out of Inbox)
    # The dump items all have permanent homes — Inbox should be clear of them
    # ─────────────────────────────────────────────
    inbox_dir = brain / "Inbox"
    inbox_files = list(inbox_dir.glob("*.md")) if inbox_dir.is_dir() else []
    
    # Check that the key items aren't stuck in Inbox
    inbox_has_sarah = any(
        re.search(r"sarah|chen", load_file(f) or "", re.IGNORECASE) for f in inbox_files
    )
    inbox_has_meridian_project = any(
        re.search(r"meridian.*audit|health.*app.*audit", load_file(f) or "", re.IGNORECASE) 
        for f in inbox_files
    )
    
    # Items with clear destinations should NOT still be in Inbox only
    items_properly_routed = not inbox_has_sarah and not inbox_has_meridian_project
    checks.append(check(
        "items_routed_out_of_inbox",
        items_properly_routed,
        f"Inbox files: {[f.name for f in inbox_files]}. Sarah still in inbox: {inbox_has_sarah}, Meridian project still in inbox: {inbox_has_meridian_project}"
    ))

    # ─────────────────────────────────────────────
    # Scoring
    # ─────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()