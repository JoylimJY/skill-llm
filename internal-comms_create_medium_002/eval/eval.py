import json
import os
import re
import sys

HEADER_RE = re.compile(r'^\s*\S+\s+mobile team\s*\(2024-06-01\s*to\s*2024-06-07\)\s*$', re.IGNORECASE | re.MULTILINE)
SECTION_NAMES = ('Progress', 'Plans', 'Problems')


def find_best_3p_update_file(workspace):
    candidates = [f for f in os.listdir(workspace) if f.lower().endswith('.md')]
    best_path = None
    best_score = -1.0
    for filename in candidates:
        path = os.path.join(workspace, filename)
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                content = handle.read()
        except Exception:
            continue
        _, _, score = score_3p_update(content)
        if score > best_score:
            best_path = path
            best_score = score
    return best_path, max(best_score, 0.0)


def extract_section(text, section_name):
    pattern = re.compile(
        rf'^\s*(?:#+\s*)?{section_name}\s*:?\s*$\n?(.*?)(?=^\s*(?:#+\s*)?(?:progress|plans|problems)\s*:?\s*$|\Z)',
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ''


def count_sentences_or_lines(text):
    stripped_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not stripped_lines:
        return 0
    cleaned = re.sub(r'(?<=\d)\.(?=\d)', '', text)
    sentence_count = len(re.findall(r'[.!?]', cleaned))
    return sentence_count if sentence_count else len(stripped_lines)


def score_3p_update(text):
    checks_passed = 0
    total_checks = 6

    header_ok = bool(HEADER_RE.search(text))
    if header_ok:
        checks_passed += 1

    sections = {name: extract_section(text, name) for name in SECTION_NAMES}
    for section_text in sections.values():
        if section_text:
            checks_passed += 1

    if sections['Progress'] and re.search(r'\b\d+\b', sections['Progress']):
        checks_passed += 1

    if all(section and count_sentences_or_lines(section) <= 3 for section in sections.values()):
        checks_passed += 1

    passed = checks_passed == total_checks
    detail = f'Passed {checks_passed} of {total_checks} checks. Header OK: {header_ok}'
    return passed, detail, checks_passed / total_checks


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'args', 'passed': False, 'detail': 'Missing workspace folder argument.'}]}))
        return

    workspace = sys.argv[1]
    file_path, _ = find_best_3p_update_file(workspace)
    checks = []

    if file_path is None:
        checks.append({'name': 'file existence', 'passed': False, 'detail': 'No markdown 3P update file found.'})
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}))
        return

    with open(file_path, 'r', encoding='utf-8') as handle:
        content = handle.read()

    header_found = bool(HEADER_RE.search(content))
    checks.append({'name': 'header format', 'passed': header_found, 'detail': 'Header contains emoji-like prefix, Mobile Team, and the correct date range.' if header_found else 'Missing or incorrect header.'})

    for section in SECTION_NAMES:
        section_text = extract_section(content, section)
        checks.append({'name': f'{section.lower()} section', 'passed': bool(section_text), 'detail': f'{section} section found.' if section_text else f'{section} section missing.'})

    progress_text = extract_section(content, 'Progress')
    prog_has_metric = bool(progress_text and re.search(r'\b\d+\b', progress_text))
    checks.append({'name': 'progress metrics', 'passed': prog_has_metric, 'detail': 'Progress section contains numeric metric.' if prog_has_metric else 'No numeric metrics found in progress section.'})

    all_short = all(extract_section(content, section) and count_sentences_or_lines(extract_section(content, section)) <= 3 for section in SECTION_NAMES)
    checks.append({'name': 'sentence length', 'passed': all_short, 'detail': 'All sections have 3 or fewer sentences.' if all_short else 'One or more sections exceed sentence length limit.'})

    passed_count = sum(1 for check in checks if check['passed'])
    score = passed_count / len(checks) if checks else 0.0
    print(json.dumps({'passed': score == 1.0, 'score': score, 'checks': checks}))


if __name__ == '__main__':
    main()
