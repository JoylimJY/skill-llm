import os
import sys
import json
import re

# Helper: read all markdown files content lowercased
def read_all_md_texts(workspace):
    md_texts = []
    for root, _, files in os.walk(workspace):
        for f in files:
            if f.lower().endswith('.md'):
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as fd:
                        md_texts.append(fd.read().lower())
                except:
                    pass
    return md_texts

# Helper: check if substrings exist in any md files
def any_md_contains(workspace, keywords):
    texts = read_all_md_texts(workspace)
    for kw in keywords:
        if not any(kw.lower() in text for text in texts):
            return False
    return True

# Helper: check proposed folder structure in markdown text
def check_folder_structure_in_md(workspace):
    texts = read_all_md_texts(workspace)
    # Look for markers of proposed folders
    required_folders = ['work/documents', 'personal/photos', 'installers', 'archive', 'tosort']
    for folder in required_folders:
        found = any(any(folder.lower() in line for line in text.splitlines()) for text in texts)
        if not found:
            return False
    return True

# Verify rename of download artifacts
def check_rename_artifacts(workspace):
    # Check no filenames contain (1) or " copy" ignoring case
    for root, _, files in os.walk(workspace):
        for f in files:
            fname = f.lower()
            if re.search(r'\(1\)', fname) or ' copy' in fname:
                return False
    return True

# Check that files with older modification time are moved to Archive
import time

# Gather file info to cross-check
def gather_files_and_mod_times(base):
    info = {}
    for root, _, files in os.walk(base):
        for f in files:
            path = os.path.join(root, f)
            stat = os.stat(path)
            info[os.path.relpath(path, base).lower()] = stat.st_mtime
    return info

# Score and checking function

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "ArgsCheck", "passed": False, "detail": "Workspace path argument missing."}]}))
        return

    workspace = sys.argv[1]
    downloads_path = os.path.join(workspace, 'Downloads')
    checks = []

    # 1. Check presence of organization plan markdown file with proposed structure
    plan_present = check_folder_structure_in_md(downloads_path)
    checks.append({
        "name": "PlanWithProposedStructure",
        "passed": plan_present,
        "detail": "Found markdown file describing proposed folder structure with all required folders." if plan_present else "Missing proposed structure folders in plan markdown."
    })

    # 2. Check rename of download artifacts
    rename_ok = check_rename_artifacts(downloads_path)
    checks.append({
        "name": "RenameDownloadArtifacts",
        "passed": rename_ok,
        "detail": "No filenames contain download artifacts like (1) or ' copy'." if rename_ok else "Some filenames still contain download artifacts like (1) or ' copy'."
    })

    # 3. Check duplicates reported in markdown somewhere (must mention duplicates and at least one file)
    duplicate_reported = any_md_contains(downloads_path, ['duplicate', 'work-proposal.pdf'])
    checks.append({
        "name": "DuplicateFilesReported",
        "passed": duplicate_reported,
        "detail": "Duplicate files mentioned with examples in markdown." if duplicate_reported else "No duplicate files mentioned in any markdown file."
    })

    # 4. Check actual folder structure created with subfolders
    expected_subfolders = ['Work/Documents', 'Personal/Photos', 'Installers', 'Archive', 'ToSort']
    all_exist = True
    for sf in expected_subfolders:
        path = os.path.join(downloads_path, sf)
        if not os.path.isdir(path):
            all_exist = False
            break
    checks.append({
        "name": "FolderStructureCreated",
        "passed": all_exist,
        "detail": "All expected subfolders are present under Downloads." if all_exist else "Some expected subfolders missing under Downloads."
    })

    # 5. Check old files (>90 days) moved into Archive
    now = time.time()
    archive_path = os.path.join(downloads_path, 'Archive')
    old_file_moved = True
    # Get all old files originally (using file names from gen_inputs: old-report.pdf, old_photo.png, and also any files modified >90 days old)
    # We'll check at least one known old file is inside Archive and not at root
    known_old_files = ['old-report.pdf', 'old_photo.png', 'readme.txt', 'todo.txt']
    found_in_archive = any(os.path.isfile(os.path.join(archive_path, f)) for f in known_old_files)
    found_in_root = any(os.path.isfile(os.path.join(downloads_path, f)) for f in known_old_files if f != 'readme.txt')
    # readme.txt likely recent but checking anyway
    # We expect old files are inside Archive and NOT at root
    old_file_moved = found_in_archive and not found_in_root

    checks.append({
        "name": "OldFilesArchived",
        "passed": old_file_moved,
        "detail": "Old files moved inside Archive folder." if old_file_moved else "Old files still in root Downloads folder or missing from Archive."
    })

    # Compute final score
    passed_checks = sum(1 for c in checks if c.get('passed'))
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks else 0.0
    passed_overall = score == 1.0

    result = {
        "passed": passed_overall,
        "score": score,
        "checks": checks
    }

    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
