import json
import os
import re
import sys


def read_text(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ''


def read_text_from_pdf(pdf_path):
    import subprocess
    try:
        result = subprocess.run(['pdftotext', pdf_path, '-'], capture_output=True, text=True, check=True)
        return result.stdout
    except Exception:
        return ''


def strip_tags(text):
    return re.sub(r'<[^>]+>', ' ', text)


def normalize(text):
    text = strip_tags(text)
    text = text.replace('`', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()


def extract_markdown_headings(text):
    headings = []
    for line in text.splitlines():
        m = re.match(r'^\s*#+\s+(.*\S)\s*$', line)
        if m:
            headings.append(m.group(1).strip())
    return headings


def verify_theme_showcase(pdf_path):
    text = read_text_from_pdf(pdf_path).lower()
    required_themes = [
        'ocean depths', 'sunset boulevard', 'forest canopy', 'modern minimalist',
        'golden hour', 'arctic frost', 'desert rose', 'tech innovation',
        'botanical garden', 'midnight galaxy'
    ]
    passed = all(theme in text for theme in required_themes)
    detail = 'Found all theme names.' if passed else 'Missing some theme names in PDF text.'
    return {'name': 'theme-showcase-present', 'passed': passed, 'detail': detail}


def verify_styled_presentation_md(input_md_path, styled_md_path):
    source = read_text(input_md_path)
    styled = read_text(styled_md_path)
    if not styled:
        return [
            {'name': 'styled-presentation-md-checks', 'passed': False, 'detail': f'Could not read {styled_md_path}'}
        ]

    source_headings = extract_markdown_headings(source)
    styled_normalized = normalize(styled)
    headings_present = all(normalize(h) in styled_normalized for h in source_headings)

    marker = '[MARKER-PRESENTATION-FILE]'
    marker_present = marker.lower() in styled.lower()

    hex_colors = set(re.findall(r'#[0-9a-fA-F]{6}', styled))
    colors_present = len(hex_colors) >= 2

    font_markers = re.findall(r"font-family\s*:\s*([^;\n]+)", styled, re.IGNORECASE)
    common_font_names = [
        'playfair display', 'lato', 'source sans pro', 'georgia', 'arial',
        'serif', 'sans-serif', 'helvetica', 'palatino'
    ]
    fonts_present = bool(font_markers) or any(font in styled.lower() for font in common_font_names)

    styled_body = normalize(styled)
    body_snippets = [
        'welcome to our presentation about theme styling.',
        'this deck will demonstrate applying the sunset boulevard theme.',
        'thank you for reviewing our themes!'
    ]
    body_present = sum(1 for snippet in body_snippets if normalize(snippet) in styled_body) >= 2

    composite_passed = all([headings_present, marker_present, colors_present, fonts_present, body_present])
    return [
        {
            'name': 'styled-presentation-md-checks',
            'passed': composite_passed,
            'detail': 'All style checks passed.' if composite_passed else 'One or more styles missing.'
        },
        {
            'name': 'headings-preserved',
            'passed': headings_present,
            'detail': 'All expected slide headings found.' if headings_present else 'Some slide headings are missing.'
        },
        {
            'name': 'content-preserved',
            'passed': body_present and marker_present,
            'detail': 'Original slide content and marker preserved.' if body_present and marker_present else 'Original slide content or marker missing.'
        },
        {
            'name': 'sunset-colors-applied',
            'passed': colors_present,
            'detail': 'Theme color hex codes found.' if colors_present else 'Theme color hex codes missing.'
        },
        {
            'name': 'sunset-fonts-applied',
            'passed': fonts_present,
            'detail': 'Theme font information found.' if fonts_present else 'Theme font information missing.'
        }
    ]


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'arg_check', 'passed': False, 'detail': 'Missing workspace path argument.'}]}))
        return

    workspace = sys.argv[1]
    checks = []

    pdf_path = os.path.join(workspace, 'theme-showcase.pdf')
    if os.path.isfile(pdf_path):
        checks.append(verify_theme_showcase(pdf_path))
    else:
        checks.append({'name': 'theme-showcase-present', 'passed': False, 'detail': 'theme-showcase.pdf not found'})

    input_md_path = os.path.join(workspace, 'presentation.md')
    styled_md_path = os.path.join(workspace, 'styled-presentation.md')

    if not os.path.isfile(input_md_path):
        checks.append({'name': 'input-presentation-present', 'passed': False, 'detail': 'presentation.md not found'})
    else:
        checks.append({'name': 'input-presentation-present', 'passed': True, 'detail': 'presentation.md found'})

    if not os.path.isfile(styled_md_path):
        checks.append({'name': 'styled-presentation-md-checks', 'passed': False, 'detail': 'styled-presentation.md not found'})
    else:
        checks.extend(verify_styled_presentation_md(input_md_path, styled_md_path))

    score = sum(1 for c in checks if c.get('passed')) / len(checks) if checks else 0.0
    passed = score == 1.0
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))


if __name__ == '__main__':
    main()
