import sys
import os
import json
import re
from pathlib import Path

def safe_lower(text):
    return text.lower() if text else ''

def find_markdown_file(workspace):
    for f in os.listdir(workspace):
        if f.lower().endswith('.md') and 'organization' in f.lower():
            return os.path.join(workspace, f)
    return None

def parse_markdown_sections(md_content):
    # Rough split by line to find headings and content
    sections = {}
    current_section = None
    lines = md_content.splitlines()
    buffer = []

    for line in lines:
        header_match = re.match(r'#+\s*(.*)', line)
        if header_match:
            if current_section and buffer:
                # Save previous section
                sections.setdefault(current_section.lower(), []).append('\n'.join(buffer).strip())
            current_section = header_match.group(1).strip()
            buffer = []
        else:
            buffer.append(line)
    if current_section and buffer:
        sections.setdefault(current_section.lower(), []).append('\n'.join(buffer).strip())
    return sections

def count_files_in_dir(path):
    count = 0
    for root, dirs, files in os.walk(path):
        count += len(files)
    return count

def read_file_lines(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read().splitlines()
    except Exception:
        return []

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg check", "passed": False, "detail": "Missing workspace directory argument"}]}))
        return

    workspace = sys.argv[1]
    downloads = os.path.join(workspace, 'Downloads')
    if not os.path.isdir(downloads):
        # Maybe root workspace is Downloads
        if os.path.basename(workspace).lower() == 'downloads':
            downloads = workspace
        elif os.path.isdir(workspace):
            # fallback
            downloads = workspace
        else:
            print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Downloads folder", "passed": False, "detail": f"Downloads folder does not exist at {downloads}"}]}))
            return

    checks = []

    # Check for required subfolders
    expected_subfolders = ['Documents', 'Images', 'Installers', 'Archive']
    existing_subfolders = [d.lower() for d in os.listdir(downloads) if os.path.isdir(os.path.join(downloads, d))]
    created_folders_pass = all(sub.lower() in existing_subfolders for sub in expected_subfolders)
    checks.append({
        'name': 'Folder structure created',
        'passed': created_folders_pass,
        'detail': 'All expected folders Documents, Images, Installers, Archive exist' if created_folders_pass else f'Missing folders: {[f for f in expected_subfolders if f.lower() not in existing_subfolders]}'
    })

    # Check that files were moved correctly by verifying example files
    # File lists per folder from gen_inputs_script:
    documents_files = ['report1.pdf', 'notes.docx', 'todo.txt']
    images_files = ['photo1.jpg', 'diagram.png']
    installers_files = ['app.dmg', 'setup.pkg']
    archive_files = ['old_data.csv', 'legacy.zip', 'readme.md']

    def files_exist_in_folder(files, folder):
        folder_path = os.path.join(downloads, folder)
        found = []
        for f in files:
            # Accept if file present directly or with numeric suffix (e.g. notes (1).docx)
            base, ext = os.path.splitext(f)
            expected_names = [f]
            # also allow suffixes
            for idx in range(1,4):
                expected_names.append(f'{base} ({idx}){ext}')

            found_file = False
            for candidate in expected_names:
                candidate_path = os.path.join(folder_path, candidate)
                if os.path.isfile(candidate_path):
                    found_file = True
                    break
            found.append(found_file)
        return found

    docs_checks = files_exist_in_folder(documents_files, 'Documents')
    docs_pass = all(docs_checks)
    checks.append({
        'name': 'Documents files moved correctly',
        'passed': docs_pass,
        'detail': f'Moved {sum(docs_checks)}/{len(documents_files)} expected files to Documents'
    })

    images_checks = files_exist_in_folder(images_files, 'Images')
    images_pass = all(images_checks)
    checks.append({
        'name': 'Images files moved correctly',
        'passed': images_pass,
        'detail': f'Moved {sum(images_checks)}/{len(images_files)} expected files to Images'
    })

    installers_checks = files_exist_in_folder(installers_files, 'Installers')
    installers_pass = all(installers_checks) = all(installers_checks)
    checks.append({
        'name': 'Installers files moved correctly',
        'passed': all(installers_checks),
        'detail': f'Moved {sum(installers_checks)}/{len(installers_files)} expected files to Installers'
    })

    archive_checks = files_exist_in_folder(archive_files, 'Archive')
    archive_pass = all(archive_checks)
    checks.append({
        'name': 'Archive files moved correctly',
        'passed': archive_pass,
        'detail': f'Moved {sum(archive_checks)}/{len(archive_files)} expected files to Archive'
    })

    # Check that organization-plan.md summary exists and contains key info
    md_file = find_markdown_file(downloads)
    md_pass = False
    md_detail = 'Could not find organization-plan.md in Downloads.'

    if md_file:
        try:
            with open(md_file, 'r') as f:
                md_text = f.read().lower()
            # Check some required phrases:
            required_keywords = [
                'current file count',
                'breakdown by file types',
                'proposed folder structure',
                'list of files moved',
                'archive'
            ]
            found_all = all(any(word in md_text for word in [kw]) for kw in required_keywords)
            md_pass = found_all
            md_detail = 'organization-plan.md includes all required summary sections.' if found_all else f'Missing keywords in organization-plan.md: {[kw for kw in required_keywords if kw not in md_text]}'
        except Exception as e:
            md_detail = f'Error reading organization-plan.md: {str(e)}'

    checks.append({
        'name': 'Organization plan summary file check',
        'passed': md_pass,
        'detail': md_detail
    })

    # Check for filename conflict handling: notes.docx appeared twice originally
    # Check that at least one notes.docx renamed (notes (1).docx or notes (2).docx) exists
    documents_path = os.path.join(downloads, 'Documents')
    notes_variants = [f for f in os.listdir(documents_path) if re.match(r'notes( \(\d+\))?\.docx', f, re.IGNORECASE)]
    conflict_pass = len(notes_variants) >= 2
    checks.append({
        'name': 'Filename conflict resolution for notes.docx',
        'passed': conflict_pass,
        'detail': f'Found notes.docx variants: {notes_variants}'
    })

    # Calculate overall score
    passed_count = sum(1 for c in checks if c.get('passed'))
    total_checks = len(checks)
    score = passed_count / total_checks if total_checks > 0 else 0.0
    passed = score >= 0.8

    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }

    print(json.dumps(result))

if __name__ == '__main__':
    main()
