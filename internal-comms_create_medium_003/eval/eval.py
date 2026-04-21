import sys
import os
import json
import re

def check_3p_format(text):
    # Check for emoji and team name with date range first line
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if not lines:
        return False, 'Empty file'
    first_line = lines[0]
    # Emoji: Unicode range is large; check presence of any emoji-like char
    emoji_found = bool(re.search(r'\p{Emoji}', first_line, re.UNICODE)) if hasattr(re, 'p') else False
    # Be more permissive: emoji usually non-alphanumeric at start
    emoji_found = emoji_found or bool(re.match(r'^[^\w\s].*', first_line))
    team_and_date = False
    # Check "Mobile Dev Team" and date match
    if re.search(r'mobile dev team', first_line, re.IGNORECASE) and re.search(r'april\s*15.*april\s*21', first_line, re.IGNORECASE):
        team_and_date = True

    return emoji_found and team_and_date, 'Emoji and team/date line check'

def extract_section(text, section_name):
    pattern = re.compile(rf'{section_name}:(.*?)(?=\n\w+:|$)', re.IGNORECASE | re.DOTALL)
    match = pattern.search(text)
    return match.group(1).strip() if match else ''

def contains_metric(text):
    # Look for numerical data with units or percentages
    return bool(re.search(r'\b\d+\b|\b\d+\.\d+%|percent|bugs|issues|blocked', text, re.IGNORECASE))

def main(workspace):
    passed_checks = 0
    checks = []
    files = [f for f in os.listdir(workspace) if f.endswith('.md')]
    if not files:
        print(json.dumps({
            'passed': False,
            'score': 0.0,
            'checks': [{'name': 'File presence', 'passed': False, 'detail': 'No .md output file found.'}]
        }))
        return

    best_score = 0
    best_detail = []
    # Evaluate all .md files found, keep best
    for fname in files:
        path = os.path.join(workspace, fname)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check first line emoji and team/date
        emoji_team_ok, emoji_team_detail = check_3p_format(content)

        # Extract sections
        progress = extract_section(content, 'Progress')
        plans = extract_section(content, 'Plans')
        problems = extract_section(content, 'Problems')

        # Checks
        c1 = emoji_team_ok
        c2 = len(progress) > 10 and len(progress.split()) <= 60
        c3 = len(plans) > 5 and len(plans.split()) <= 60
        c4 = len(problems) > 5 and len(problems.split()) <= 60
        c5 = contains_metric(progress)
        c6 = contains_metric(problems)

        score = sum([c1,c2,c3,c4,c5,c6])/6
        if score > best_score:
            best_score = score
            best_detail = [
                {'name': 'Emoji and header line present', 'passed': c1, 'detail': emoji_team_detail},
                {'name': 'Progress section length', 'passed': c2, 'detail': f'Length {len(progress.split())} words'},
                {'name': 'Plans section length', 'passed': c3, 'detail': f'Length {len(plans.split())} words'},
                {'name': 'Problems section length', 'passed': c4, 'detail': f'Length {len(problems.split())} words'},
                {'name': 'Progress contains metric(s)', 'passed': c5, 'detail': 'Numeric metric found' if c5 else 'No numeric metric'},
                {'name': 'Problems contains metric(s)', 'passed': c6, 'detail': 'Numeric metric found' if c6 else 'No numeric metric'},
            ]

    passed = best_score == 1.0
    print(json.dumps({
        'passed': passed,
        'score': best_score,
        'checks': best_detail
    }))

if __name__ == '__main__':
    main(sys.argv[1])
