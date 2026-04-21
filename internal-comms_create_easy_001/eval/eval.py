import os
import sys
import json
import re

def check_3p_update_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        return False, 'Failed to read file: ' + str(e)

    text_lower = text.lower()

    # Check file has emoji at start of first line (emoji is any UTF-8 non-ascii char or ascii emoji)
    lines = text.strip().splitlines()
    if len(lines) < 4:
        return False, 'File too short, less than 4 lines'

    first_line = lines[0].strip()
    # Must start with emoji and "mobile team"
    # To be tolerant: check first line contains "mobile team" and some emoji (non alpha numeric char)
    if 'mobile team' not in first_line.lower():
        return False, 'First line must contain "Mobile Team" (case insensitive)'

    # Emoji check: first char could be emoji if non ascii and non whitespace
    if all(c.isalnum() or c.isspace() for c in first_line):
        # No emoji detected
        return False, 'First line must start with an emoji character'

    # Check dates format present
    date_pattern = r'\b2024-06-01\b.*\b2024-06-07\b'
    if not re.search(date_pattern, first_line):
        return False, 'Dates "2024-06-01 to 2024-06-07" must be on first line'

    # Check presence and order of sections: Progress:, Plans:, Problems:
    lowercase_text = text.lower()
    sections = ['progress:', 'plans:', 'problems:']
    last_index = -1
    for section in sections:
        idx = lowercase_text.find(section)
        if idx == -1:
            return False, f'Section "{section}" missing'
        if idx <= last_index:
            return False, f'Section "{section}" out of order'
        last_index = idx

    # Extract text after each section heading, max 3 sentences per section
    # Simple splitting by 'Progress:', 'Plans:', 'Problems:'
    parts = re.split(r'progress:|plans:|problems:', lowercase_text)
    if len(parts) < 4:
        return False, 'Could not parse 3P sections correctly'

    # parts[1] = after Progress:, parts[2] after Plans:, parts[3] after Problems:
    def count_sentences(text):
        # Count sentences as segments ending with . or ! or ?
        return len(re.findall(r'[.!?]+', text))

    for i, section_name in enumerate(['Progress', 'Plans', 'Problems']):
        section_text = parts[i+1].strip()
        # Limit to 3 sentences max
        if count_sentences(section_text) > 3:
            return False, f'Section {section_name} has more than 3 sentences'

        # Check for briefness: 1-3 sentences, allowing also 1 or 2
        if count_sentences(section_text) < 1:
            return False, f'Section {section_name} must have at least 1 sentence'

    # Check at least one numeric metric mentioned in Progress
    progress_text = parts[1]
    numbers_found = re.findall(r'\b\d+[,.]?\d*\b', progress_text)
    if len(numbers_found) == 0:
        return False, 'Progress section must include at least one numeric metric'

    return True, 'File format and content appear correct'


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    # Find candidate markdown files
    md_files = [f for f in os.listdir(workspace) if f.lower().endswith('.md')]
    if not md_files:
        print(json.dumps({
            'passed': False,
            'score': 0.0,
            'checks': [{'name': 'file-exists', 'passed': False, 'detail': 'No markdown (.md) files found'}]
        }))
        return

    best_score = 0.0
    best_detail = ''

    for md_file in md_files:
        if 'mobile-team-3p-update.md' not in md_file.lower():
            continue
        file_path = os.path.join(workspace, md_file)
        passed, detail = check_3p_update_file(file_path)
        score = 1.0 if passed else 0.0
        if score > best_score:
            best_score = score
            best_detail = detail

    if best_score == 1.0:
        result = {
            'passed': True,
            'score': 1.0,
            'checks': [
                {'name': 'file-exists', 'passed': True, 'detail': 'File "mobile-team-3p-update.md" exists'},
                {'name': 'format-check', 'passed': True, 'detail': 'File formatting and content are correct'},
                {'name': 'sections-check', 'passed': True, 'detail': 'Sections Progress, Plans, Problems present, ordered correctly'},
                {'name': 'metrics-check', 'passed': True, 'detail': 'Progress section includes numeric metrics'},
                {'name': 'sentence-count-check', 'passed': True, 'detail': 'Each section has 1-3 sentences as required'},
                {'name': 'emoji-check', 'passed': True, 'detail': 'Emoji present at start of file and team name present'}
            ]
        }
    else:
        result = {
            'passed': False,
            'score': best_score,
            'checks': [
                {'name': 'file-exists', 'passed': best_score > 0, 'detail': best_detail or 'File missing or format incorrect'}
            ]
        }

    print(json.dumps(result))


if __name__ == '__main__':
    main()
