import sys
import os
import json
import re

def read_file(filepath):
    try:
        with open(filepath, encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return None

def check_json_theme_file(filepath):
    content = read_file(filepath)
    if not content:
        return False, "File not found or empty."
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"

    # Check keys: colors and fonts
    colors = data.get('colors') or data.get('color_palette') or data.get('palette')
    fonts = data.get('fonts') or data.get('font_pairings')

    if not colors or not isinstance(colors, dict):
        return False, "Missing or invalid 'colors' dictionary."
    if len(colors) < 4:
        return False, f"Insufficient colors in palette (found {len(colors)}). Must be at least 4."

    hex_color_pattern = re.compile(r'^#([0-9A-Fa-f]{6})$')
    for key, val in colors.items():
        if not isinstance(val, str) or not hex_color_pattern.match(val.strip()):
            return False, f"Color '{key}' does not have valid hex code: '{val}'."

    if not fonts or not isinstance(fonts, dict):
        return False, "Missing or invalid 'fonts' dictionary."

    header_font = fonts.get('header') or fonts.get('header_font')
    body_font = fonts.get('body') or fonts.get('body_font')
    if not header_font or not isinstance(header_font, str) or not header_font.strip():
        return False, "Missing or empty 'header' font."
    if not body_font or not isinstance(body_font, str) or not body_font.strip():
        return False, "Missing or empty 'body' font."

    # Optional: Check theme name in JSON matches filename (elegant-evening)
    return True, "Theme JSON structure valid."

def check_summary_file_contents(filepath):
    content = read_file(filepath)
    if not content:
        return False, "File missing or empty."
    content_lower = content.lower()
    # Check the summary mentions 'elegant evening' and at least the colors and fonts words
    if 'elegant evening' not in content_lower:
        return False, "Summary does not mention 'elegant evening'."
    if not any(c in content_lower for c in ['color', 'palette', 'colors']):
        return False, "Summary does not discuss colors."
    if not any(f in content_lower for f in ['font', 'fonts', 'typeface']):
        return False, "Summary does not discuss fonts."
    return True, "Summary content looks good."

def check_styled_presentation(filepath):
    content = read_file(filepath)
    if not content:
        return False, "Styled presentation file not found or empty."
    content_lower = content.lower()

    # Check that original header lines remain
    expected_headers = [
        'slide 1: introduction',
        'slide 2: problem statement',
        'slide 3: current themes',
        'slide 4: need for custom theme',
        'slide 5: conclusion'
    ]
    for header in expected_headers:
        if header not in content_lower:
            return False, f"Missing expected header '{header}'."

    # Check for presence of theme colors as hex codes anywhere
    # We require at least 4 hex colors from theme
    hex_colors_found = set(re.findall(r'#[0-9a-f]{6}', content_lower))

    if len(hex_colors_found) < 4:
        return False, f"Not enough theme colors found in styled file; found {len(hex_colors_found)}."

    # Check the fonts appear in some annotations or comments
    font_mentioned = re.search(r'font[s]?:?\s*\w+', content_lower)
    if not font_mentioned:
        return False, "No font annotations or mentions found in styled presentation."

    # Check that stylings are consistent (e.g., all headers have similar font styling lines)
    # We'll try to find at least one header and check if font/color style mention is nearby
    headers = re.findall(r'^(#+)\s.*$', content, flags=re.MULTILINE)
    if not headers:
        return False, "No markdown headers found."

    # To avoid false negatives, accept if font/color styles appear anywhere near the headers
    # but since we have checks above, sufficient

    return True, "Styled presentation file looks correct."

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Invocation", "passed": False, "detail": "Workspace path argument missing."}]}))
        return

    workspace = sys.argv[1]

    # Find relevant output files
    files = os.listdir(workspace)
    files_lower = [f.lower() for f in files]

    # Identify theme JSON file
    theme_files = [f for f in files if f.lower() == 'elegant-evening.json']
    summary_files = [f for f in files if f.lower() == 'elegant-evening-summary.txt']
    styled_files = [f for f in files if f.lower() == 'styled-presentation.md']

    checks = []

    # Check theme JSON
    if theme_files:
        theme_file = os.path.join(workspace, theme_files[0])
        passed, detail = check_json_theme_file(theme_file)
    else:
        passed, detail = False, "Theme JSON file 'elegant-evening.json' not found."
    checks.append({"name": "Custom Theme JSON File", "passed": passed, "detail": detail})

    # Check summary
    if summary_files:
        summary_file = os.path.join(workspace, summary_files[0])
        passed_summary, detail_summary = check_summary_file_contents(summary_file)
    else:
        passed_summary, detail_summary = False, "Summary file 'elegant-evening-summary.txt' not found."
    checks.append({"name": "Theme Summary Text File", "passed": passed_summary, "detail": detail_summary})

    # Check styled presentation
    if styled_files:
        styled_file = os.path.join(workspace, styled_files[0])
        passed_styled, detail_styled = check_styled_presentation(styled_file)
    else:
        passed_styled, detail_styled = False, "Styled presentation file 'styled-presentation.md' not found."
    checks.append({"name": "Styled Presentation File", "passed": passed_styled, "detail": detail_styled})

    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c['passed'])
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    passed = score == 1.0

    result = {"passed": passed, "score": score, "checks": checks}

    print(json.dumps(result))

if __name__ == '__main__':
    main()
