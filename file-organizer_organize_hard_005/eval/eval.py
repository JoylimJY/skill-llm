import sys
import os
import json
import re
import pathlib

# Helper functions

def find_markdown_file(workspace, possible_names):
    # Returns path of the first markdown file matching name or substring
    candidates = []
    for f in os.listdir(workspace):
        fname = f.lower()
        for name in possible_names:
            if name.lower() in fname and fname.endswith('.md'):
                candidates.append(os.path.join(workspace, f))
    # Return all candidates, score best
    return candidates

# Parse key stats from text (case insensitive, allow whitespace)
def extract_number(text, keywords):
    # keywords is list of strings, match any
    lowered = text.lower()
    if not any(k.lower() in lowered for k in keywords):
        return None
    nums = re.findall(r'([\d,.]+)', text)
    if not nums:
        return None
    # Return first number as int if possible
    try:
        n = nums[0].replace(',', '')
        if '.' in n:
            return float(n)
        return int(n)
    except:
        return None

def extract_size_bytes(text):
    # e.g. '1.4 MB' or '700 KB' -> bytes
    match = re.search(r'([\d.]+)\s*(kb|mb|gb)', text, re.IGNORECASE)
    if not match:
        return None
    val = float(match.group(1))
    unit = match.group(2).lower()
    factor = {'kb': 1024, 'mb': 1024**2, 'gb': 1024**3} 
    return val * factor.get(unit, 1)

def check_analysis_file(workspace, path):
    checks = []
    if not os.path.isfile(path):
        return False, ['Analysis.md file not found']
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read().lower()
    # Check for mention of total files
    if 'total' in text and 'files' in text:
        checks.append(True)
    else:
        checks.append(False)
    # Check breakdown of file types (look for extensions or general types like pdf, jpg)
    types_found = any(ext in text for ext in ['pdf', 'jpg', 'png', 'zip', 'dmg', 'txt', 'docx', 'xlsx'])
    checks.append(types_found)
    # Size distribution mention
    size_mentioned = any(unit in text for unit in ['kb', 'mb', 'gb'])
    checks.append(size_mentioned)
    # Date range mention
    date_mentioned = any(word in text for word in ['date', 'modified', 'created', 'range'])
    checks.append(date_mentioned)
    passed = all(checks)
    detail = f'Checks passed: {sum(checks)}/{len(checks)}'
    return passed, [detail]

def check_duplicates_section(text):
    # Check that full paths appear multiple times for same file name
    # Look for lines with "/downloads" and file size or date
    lines = text.lower().splitlines()
    found_paths = 0
    found_sizes = 0
    found_dates = 0
    for line in lines:
        if '/downloads' in line:
            found_paths += 1
        if re.search(r'\d+(\.\d+)?\s*(kb|mb|gb)', line, re.IGNORECASE):
            found_sizes += 1
        if re.search(r'modified[:]?\s*\d{4}-\d{2}-\d{2}', line, re.IGNORECASE):
            found_dates += 1
    # We want at least 5 of each ideally
    return found_paths >=5 and found_sizes >=3 and found_dates >=3

def check_plan_file(workspace, path):
    if not os.path.isfile(path):
        return False, ['OrganizationPlan.md missing']
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read().lower()
    checks = []
    # Check for directory tree diagram with common folder names installed, work, personal, archive
    folder_terms = ['installers', 'work', 'personal', 'archive', 'tosort', 'downloads']
    found_folders = sum(1 for term in folder_terms if term in text)
    checks.append(found_folders >= 3)
    # Check for numbered change list
    changes_pattern = re.compile(r'\d+\.\s*')
    changes_found = bool(changes_pattern.search(text))
    checks.append(changes_found)
    # Check for mention of duplicate handling
    dup_found = any(k in text for k in ['duplicate', 'recommend', 'keep', 'delete'])
    checks.append(dup_found)
    passed = all(checks)
    detail = f'Checks passed: {sum(checks)}/{len(checks)}'
    return passed, [detail]

def check_summary_file(workspace, path):
    if not os.path.isfile(path):
        return False, ['Summary.md file missing']
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read().lower()
    checks = []
    # Check new folder tree presence
    tree_terms = ['work/', 'personal/', 'installers/', 'archive/', 'tosort/']
    checks.append(any(t in text for t in tree_terms))
    # Check for files moved counts
    files_moved_found = any(k in text for k in ['moved', 'files', 'organized'])
    checks.append(files_moved_found)
    # Check for space saved (in kb/mb/gb)
    space_saved = any(s in text for s in ['kb', 'mb', 'gb']) and ('saved' in text or 'freed' in text)
    checks.append(space_saved)
    # Check for maintenance tips section
    tips = any(k in text for k in ['maintenance', 'tips', 'keep', 'organized'])
    checks.append(tips)
    passed = all(checks)
    detail = f'Checks passed: {sum(checks)}/{len(checks)}'
    return passed, [detail]

def check_file_moves(workspace):
    # Check if files have been moved into the proposed folders
    # We expect these folders inside ./Downloads
    expected_dirs = ['Work', 'Personal', 'Installers', 'Archive', 'ToSort']
    downloads_path = os.path.join(workspace, 'Downloads')
    dirs_present = [d for d in expected_dirs if os.path.isdir(os.path.join(downloads_path, d))]
    if len(dirs_present) < 3:
        return False, [f'Missing most expected folders inside Downloads: found {dirs_present}']

    # Check that duplicates removed or isolated
    # Find duplicate files by name in entire Downloads
    from collections import defaultdict
    file_map = defaultdict(list)
    for root, _, files in os.walk(downloads_path):
        for file in files:
            file_map[file].append(os.path.join(root, file))
    duplicates = {f:p for f, p in file_map.items() if len(p)>1}

    # Check that duplicates are either removed or only one copy remains (allow one per duplicate group)
    # Since prompt says do NOT delete duplicates without confirmation, allow duplicates moved to ToSort or Archive.
    tosort_dir = os.path.join(downloads_path, 'ToSort')
    archive_dir = os.path.join(downloads_path, 'Archive')

    duplicates_handled = True
    for f, paths in duplicates.items():
        # Check if at least one copy inside ToSort or Archive
        has_in_special = any(p.startswith(tosort_dir) or p.startswith(archive_dir) for p in paths)
        # Or at least only one copy in top level (could be acceptable)
        if not has_in_special and len(paths) > 1:
            duplicates_handled = False
            break

    if not duplicates_handled:
        return False, ['Duplicates not properly handled (expected to isolate or reduce duplicates)']

    return True, ['Files moved into expected folder structure and duplicates handled']

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Usage: eval_script.py <workspace>"}]}))
        return

    workspace = sys.argv[1]
    result = {"checks": []}

    # Find candidates for Analysis.md
    analysis_candidates = find_markdown_file(workspace, ['analysis'])
    plan_candidates = find_markdown_file(workspace, ['organizationplan', 'organization_plan', 'orgplan'])
    summary_candidates = find_markdown_file(workspace, ['summary'])

    scores = {"analysis": (False, []), "plan": (False, []), "summary": (False, []), "file_moves": (False, [])}

    # Evaluate analysis
    analysis_results = []
    for path in analysis_candidates:
        passed, detail = check_analysis_file(workspace, path)
        analysis_results.append((passed, detail))
    if analysis_results:
        scores['analysis'] = max(analysis_results, key=lambda x: x[0])

    # Evaluate plan
    plan_results = []
    for path in plan_candidates:
        passed, detail = check_plan_file(workspace, path)
        plan_results.append((passed, detail))
    if plan_results:
        scores['plan'] = max(plan_results, key=lambda x: x[0])

    # Evaluate summary
    summary_results = []
    for path in summary_candidates:
        passed, detail = check_summary_file(workspace, path)
        summary_results.append((passed, detail))
    if summary_results:
        scores['summary'] = max(summary_results, key=lambda x: x[0])

    # Check file moves
    fm_passed, fm_detail = check_file_moves(workspace)
    scores['file_moves'] = (fm_passed, fm_detail)

    # Compose checks and score
    result['checks'] = [
        {"name": "Analysis File Present & Valid", "passed": bool(scores['analysis'][0]), "detail": '; '.join(scores['analysis'][1])},
        {"name": "Organization Plan File Present & Valid", "passed": bool(scores['plan'][0]), "detail": '; '.join(scores['plan'][1])},
        {"name": "Summary File Present & Valid", "passed": bool(scores['summary'][0]), "detail": '; '.join(scores['summary'][1])},
        {"name": "Files Moved & Duplicates Handled", "passed": bool(scores['file_moves'][0]), "detail": '; '.join(scores['file_moves'][1])}
    ]

    score = sum(1 for c in result['checks'] if c['passed']) / len(result['checks'])
    result['score'] = score
    result['passed'] = score == 1.0

    print(json.dumps(result))

if __name__ == '__main__':
    main()
