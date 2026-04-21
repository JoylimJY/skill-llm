import json
import os
import re
import sys

LEAD_HEADER_RE = re.compile(r'^\s*##\s*Lead\s+(\d+)\s*:', re.IGNORECASE | re.MULTILINE)


def split_lead_sections(content):
    matches = list(LEAD_HEADER_RE.finditer(content))
    sections = {}
    for index, match in enumerate(matches):
        lead_num = int(match.group(1))
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        sections[lead_num] = content[start:end]
    return sections


def count_bullets(text):
    return len(re.findall(r'^\s*(?:[-*?]|\d+\.)\s+.+', text, re.MULTILINE))


def extract_conversation_block(section_text):
    patterns = [
        r'\*\*Conversation Starters\*\*\s*:\s*(.*?)(?=\n\s*---\s*\n|\n\s*##\s*Lead\s+\d+\s*:|\Z)',
        r'Conversation Starters\s*:\s*(.*?)(?=\n\s*---\s*\n|\n\s*##\s*Lead\s+\d+\s*:|\Z)',
    ]
    for pattern in patterns:
        match = re.search(pattern, section_text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return ''


def check_markdown_format(content, workspace):
    low = content.lower()
    checks = []
    sections = split_lead_sections(content)

    checks.append((len(sections) >= 5, f'Found {len(sections)} lead sections, expected 5'))

    total_leads_match = re.search(r'total leads found\s*:\s*5', low)
    checks.append((total_leads_match is not None, 'Summary with total leads found: 5'))

    required_fields = ['website', 'priority score', 'industry', 'size']
    found_all = True
    missing_fields = []
    for i in range(1, 6):
        section = sections.get(i, '')
        if not section:
            found_all = False
            missing_fields.append(f'Lead {i} section missing')
            continue
        section_low = section.lower()
        for field in required_fields:
            if field not in section_low:
                found_all = False
                missing_fields.append(f'Lead {i} missing field: {field}')
    checks.append((found_all, 'All leads have required basic fields' if found_all else '; '.join(missing_fields)))

    conversation_present = True
    conversation_details = []
    for i in range(1, 6):
        section = sections.get(i, '')
        if not section:
            conversation_present = False
            conversation_details.append(f'Lead {i} section missing')
            continue
        block = extract_conversation_block(section)
        bullets = count_bullets(block)
        if bullets < 1:
            conversation_present = False
            conversation_details.append(f'Lead {i} conversation bullets found: {bullets}')
    checks.append((conversation_present, 'All leads include conversation starters with at least one bullet' if conversation_present else '; '.join(conversation_details)))

    md_files = [f for f in os.listdir(workspace) if f.lower().endswith('.md')]
    exact_file = 'lead_research_results.md'
    file_exists = any(f.lower() == exact_file for f in md_files)
    checks.append((file_exists, 'Markdown output file lead_research_results.md exists'))

    passed_checks = sum(1 for c in checks if c[0])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks else 0.0
    passed = score == 1.0

    checks_out = []
    for name, (passed_c, detail) in zip(
        [
            'Five leads present',
            'Summary section present',
            'Lead fields complete',
            'Conversation starters present',
            'Correct output filename',
        ],
        checks,
    ):
        checks_out.append({'name': name, 'passed': passed_c, 'detail': detail})

    print(json.dumps({'passed': passed, 'score': score, 'checks': checks_out}))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python eval_script.py <workspace_dir>')
        sys.exit(1)

    workspace = sys.argv[1]
    target_file = None
    for f in os.listdir(workspace):
        if f.lower() == 'lead_research_results.md':
            target_file = os.path.join(workspace, f)
            break

    if not target_file:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'File presence', 'passed': False, 'detail': 'lead_research_results.md not found'}]}))
        sys.exit(0)

    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()

    check_markdown_format(content, workspace)
