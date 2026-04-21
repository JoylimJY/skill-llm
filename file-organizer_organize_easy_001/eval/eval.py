import sys
import os
import json
import re
from datetime import datetime

def contains_ignore_case(haystack, needles):
    haystack = haystack.lower()
    return any(n.lower() in haystack for n in needles)

def read_file_safe(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

def check_markdown_plan(workspace):
    # Find a markdown file with ORGANIZATION_PLAN.md exact name or containing "plan" (case-insensitive)
    candidates = []
    for fn in os.listdir(workspace):
        if fn.lower() == 'organization_plan.md'.lower() or ('.md' in fn.lower() and 'plan' in fn.lower()):
            candidates.append(fn)
    if not candidates:
        return False, 'No organization plan markdown file found'
    # Read all candidates and check for plan content
    for fn in candidates:
        content = read_file_safe(os.path.join(workspace, fn))
        if not content:
            continue
        content_lower = content.lower()
        # Check it mentions the five folders
        required_folders = ['work', 'personal', 'installers', 'archive', 'tosort']
        if all(f in content_lower for f in required_folders):
            # Check it mentions move PDFs to Work, images (jpg) to Personal, installers (dmg and pkg) to Installers
            if contains_ignore_case(content, ['pdf', 'work']) and contains_ignore_case(content, ['jpg', 'personal']) and contains_ignore_case(content, ['dmg', 'pkg', 'installers']):
                if contains_ignore_case(content, ['older than 3 months', 'archive']):
                    return True, 'Found valid organization plan markdown file'
    return False, 'Organization plan file does not contain required folder names and plan details'

def check_file_moved(workspace, filename, target_folder):
    folder_path = os.path.join(workspace, 'Downloads', target_folder)
    if not os.path.isdir(folder_path):
        return False, f'Folder {target_folder} does not exist'
    # Check file exists in target folder
    for f in os.listdir(folder_path):
        if f.lower() == filename.lower():
            return True, f'File {filename} correctly moved to {target_folder}'
    return False, f'File {filename} not found in {target_folder}'

def check_old_files_in_archive(workspace):
    archive_path = os.path.join(workspace, 'Downloads', 'Archive')
    if not os.path.isdir(archive_path):
        return False, 'Archive folder does not exist'
    # old_notes.txt is the clearly age-based archive candidate.
    # installer_2023.pkg is already required in Installers by the task,
    # so the evaluator should not demand it in two places.
    expected_files = ['old_notes.txt']
    found_files = os.listdir(archive_path)
    missing = [f for f in expected_files if not any(f.lower() == ff.lower() for ff in found_files)]
    if missing:
        return False, f'Missing files in Archive folder: {missing}'
    return True, 'Old files correctly moved to Archive'

def check_unclassified_files_in_tosort(workspace):
    tosort_path = os.path.join(workspace, 'Downloads', 'ToSort')
    if not os.path.isdir(tosort_path):
        return False, 'ToSort folder does not exist'
    # random.bin should be in ToSort
    files_here = os.listdir(tosort_path)
    if not any(f.lower() == 'random.bin' for f in files_here):
        return False, 'random.bin not found in ToSort'
    return True, 'Misc file correctly placed in ToSort'

def check_folder_structure(workspace):
    base_path = os.path.join(workspace, 'Downloads')
    expected_folders = ['Work', 'Personal', 'Installers', 'Archive', 'ToSort']
    missing = [f for f in expected_folders if not os.path.isdir(os.path.join(base_path, f))]
    if missing:
        return False, f'Missing folders in Downloads: {missing}'
    return True, 'All expected folders created'

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg", "passed": False, "detail": "Missing workspace directory argument"}]}))
        return
    workspace = sys.argv[1]
    checks = []

    plan_ok, plan_detail = check_markdown_plan(workspace)
    checks.append({"name": "organization_plan_file", "passed": plan_ok, "detail": plan_detail})

    folders_ok, folders_detail = check_folder_structure(workspace)
    checks.append({"name": "folder_structure_created", "passed": folders_ok, "detail": folders_detail})

    files_checks = []
    # PDFs to Work
    for pdf in ['report1.pdf', 'proposal2.pdf']:
        ok, detail = check_file_moved(workspace, pdf, 'Work')
        files_checks.append({"name": f"pdf_in_work_{pdf}", "passed": ok, "detail": detail})

    # JPG to Personal
    for jpg in ['photo1.jpg', 'photo2.JPG']:
        ok, detail = check_file_moved(workspace, jpg, 'Personal')
        files_checks.append({"name": f"jpg_in_personal_{jpg}", "passed": ok, "detail": detail})

    # Installers (DMG, PKG) to Installers
    for inst in ['setup1.dmg', 'installer_2023.pkg']:
        ok, detail = check_file_moved(workspace, inst, 'Installers')
        files_checks.append({"name": f"installer_in_installers_{inst}", "passed": ok, "detail": detail})

    # Old non-installer files (old_notes.txt) should be in Archive. Installer files go to Installers even if old.
    archive_ok, archive_detail = check_old_files_in_archive(workspace)
    files_checks.append({"name": "old_files_in_archive", "passed": archive_ok, "detail": archive_detail})

    # Misc files in ToSort
    tosort_ok, tosort_detail = check_unclassified_files_in_tosort(workspace)
    checks.append({"name": "misc_files_in_tosort", "passed": tosort_ok, "detail": tosort_detail})

    checks.extend(files_checks)

    passed = all(c['passed'] for c in checks)
    score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0

    print(json.dumps({"passed": passed, "score": score, "checks": checks}))

if __name__ == "__main__":
    main()
