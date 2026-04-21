import os
import sys
import json

import re

def find_files_by_ext(root, exts):
    matches = []
    exts = [e.lower() for e in exts]
    for dirpath, _, files in os.walk(root):
        for f in files:
            if any(f.lower().endswith(ext) for ext in exts):
                matches.append(os.path.join(dirpath, f))
    return matches

def filesize(path):
    try:
        return os.path.getsize(path)
    except:
        return -1

def read_text(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ''

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Workspace directory arg missing"}]}))
        return

    root = sys.argv[1]
    dl_path = os.path.join(root, 'Downloads')

    checks = []

    # Check 1: Check that folders Documents, Images, Installers exist inside Downloads
    folders_required = ['Documents', 'Images', 'Installers']
    missing_dirs = []
    for d in folders_required:
        path = os.path.join(dl_path, d)
        if not os.path.isdir(path):
            missing_dirs.append(d)
    passed1 = len(missing_dirs) == 0
    checks.append({
        "name": "created_folders",
        "passed": passed1,
        "detail": f"Folders missing: {missing_dirs}" if missing_dirs else "All required folders exist"
    })

    # Check 2: PDFs inside Downloads/Documents
    pdfs = find_files_by_ext(dl_path, ['.pdf'])
    pdf_in_docs = all(os.path.commonpath([f, os.path.join(dl_path, 'Documents')]) == os.path.join(dl_path, 'Documents') for f in pdfs)
    checks.append({
        "name": "pdfs_moved",
        "passed": pdf_in_docs,
        "detail": f"PDF files locations verified, count: {len(pdfs)}"
    })

    # Check 3: Images inside Downloads/Images
    image_exts = ['.png', '.jpg', '.jpeg']
    images = find_files_by_ext(dl_path, image_exts)
    img_in_images = all(os.path.commonpath([f, os.path.join(dl_path, 'Images')]) == os.path.join(dl_path, 'Images') for f in images)
    checks.append({
        "name": "images_moved",
        "passed": img_in_images,
        "detail": f"Image files locations verified, count: {len(images)}"
    })

    # Check 4: DMG installers inside Downloads/Installers
    dmg_files = find_files_by_ext(dl_path, ['.dmg'])
    dmg_in_installers = all(os.path.commonpath([f, os.path.join(dl_path, 'Installers')]) == os.path.join(dl_path, 'Installers') for f in dmg_files)
    checks.append({
        "name": "dmg_moved",
        "passed": dmg_in_installers,
        "detail": f"DMG files locations verified, count: {len(dmg_files)}"
    })

    # Check 5: random.txt still in Downloads root (not moved)
    random_path = os.path.join(dl_path, 'random.txt')
    random_exists = os.path.isfile(random_path)
    checks.append({
        "name": "random_txt_untouched",
        "passed": random_exists,
        "detail": f"random.txt presence: {random_exists}"
    })

    # Check 6: Check duplicates report found in 'organization-summary.md'
    summary_files = [f for f in os.listdir(root) if 'organization-summary' in f.lower() and f.lower().endswith('.md')]
    duplicates_found = False
    created_folders_listed = False
    moved_counts_listed = False

    highest_md_score = 0.0
    for summary_file in summary_files:
        full_path = os.path.join(root, summary_file)
        text = read_text(full_path).lower()

        dup_keywords = ['duplicate', 'duplicates', 'duplicate files']
        folders_keywords = ['documents', 'images', 'installers']
        moved_keywords = ['moved', 'files']

        dups = any(k in text for k in dup_keywords)
        folds = any(k in text for k in folders_keywords)
        moved = any(k in text for k in moved_keywords)

        score = sum([dups, folds, moved])/3
        if score > highest_md_score:
            highest_md_score = score
            duplicates_found = dups
            created_folders_listed = folds
            moved_counts_listed = moved

    checks.append({
        "name": "markdown_summary_duplicates",
        "passed": duplicates_found,
        "detail": f"Duplicates mentioned in summary: {duplicates_found}"
    })
    checks.append({
        "name": "markdown_summary_folders",
        "passed": created_folders_listed,
        "detail": f"Created folders mentioned: {created_folders_listed}"
    })
    checks.append({
        "name": "markdown_summary_moved_counts",
        "passed": moved_counts_listed,
        "detail": f"Files moved counts mentioned: {moved_counts_listed}"
    })

    # Score calculation
    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    score = passed / total if total > 0 else 0.0
    overall_passed = score == 1.0

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

    print(json.dumps(result))


if __name__ == '__main__':
    main()
