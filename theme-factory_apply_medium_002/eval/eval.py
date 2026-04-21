import sys
import os
import json
import re
from pathlib import Path

def case_insensitive_contains(text, keywords):
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in keywords)

def read_file_contents(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return ''

def find_theme_file(themes_dir, chosen_theme):
    # Try to find theme file matching chosen theme name (spaces replaced by underscores, lowercase)
    normalized = chosen_theme.replace(' ', '_').lower()
    for f in os.listdir(themes_dir):
        if normalized in f.lower() and f.endswith('.txt'):
            return os.path.join(themes_dir, f)
    return None

def parse_theme_spec(spec_text):
    colors = {}
    fonts = {}
    # Simple parsing
    lines = spec_text.splitlines()
    color_section = False
    font_section = False
    for line in lines:
        lstrip = line.strip().lower()
        if 'colors' in lstrip:
            color_section = True
            font_section = False
            continue
        if 'fonts' in lstrip:
            font_section = True
            color_section = False
            continue
        if color_section:
            # Expect lines like 'primary: #hexcode'
            m = re.match(r'\s*([a-z]+)\s*:\s*(#[0-9a-fA-F]{6})', line)
            if m:
                colors[m.group(1)] = m.group(2).lower()
        if font_section:
            m = re.match(r'\s*([a-z]+)\s*:\s*([\w\s\-]+)', line, flags=re.IGNORECASE)
            if m:
                fonts[m.group(1).lower()] = m.group(2).strip()
    return colors, fonts

def check_styling_applied(content, colors, fonts):
    # We expect the output styled_presentation.txt to contain header and body font and colors
    # Check that each header line is annotated with header font and primary or secondary color
    # Check that each body line is annotated with body font and background or complementary color

    lines = content.splitlines()
    found_headers = 0
    found_body_lines = 0
    header_font = fonts.get('header', '').lower()
    body_font = fonts.get('body', '').lower()
    primary_color = colors.get('primary', '').lower()
    secondary_color = colors.get('secondary', '').lower()
    background_color = colors.get('background', '').lower()

    # Tolerate either primary or secondary for headers (as per style), body with background or secondary
    for line in lines:
        line_lower = line.lower()
        if not line.strip():
            continue
        # Heuristic: slide titles are single lines followed by body lines
        # If line contains 'title' word or is capitalized mostly, consider it header
        # Instead just require each line to have font and color annotation
        # Looking for substrings like 'header font: fontname' and 'color: #hexcode'

        # Try to detect header line if line contains word 'slide' or 'title' or is in title case
        is_header = False
        # due to wide variance, just check if "header font" annotation exists on line
        if 'header font:' in line_lower:
            is_header = True
            found_headers += 1
            # Check header font and color presence
            font_check = header_font in line_lower
            color_check = any(c in line_lower for c in [primary_color, secondary_color])
            if not font_check or not color_check:
                return False
        elif 'body font:' in line_lower:
            found_body_lines += 1
            font_check = body_font in line_lower
            color_check = any(c in line_lower for c in [background_color, secondary_color])
            if not font_check or not color_check:
                return False
        else:
            # If line does not mention fonts, fail
            return False

    # Minimal checks: at least 2 header lines, 2 body lines annotated correctly
    if found_headers < 2 or found_body_lines < 2:
        return False

    return True

def main(workspace_path):
    results = []
    passes = 0

    # Check 1: theme-showcase.pdf exists and is accessible
    pdf_path = os.path.join(workspace_path, 'theme-showcase.pdf')
    pdf_exists = os.path.isfile(pdf_path) and os.path.getsize(pdf_path) > 0
    results.append({"name": "theme_showcase_pdf_exists", "passed": pdf_exists,
                    "detail": "theme-showcase.pdf file found and non-empty" if pdf_exists else "missing or empty theme-showcase.pdf"})

    # Check 2: presentation.txt exists
    pres_path = os.path.join(workspace_path, 'presentation.txt')
    pres_exists = os.path.isfile(pres_path)
    results.append({"name": "presentation_input_exists", "passed": pres_exists,
                    "detail": "presentation.txt found" if pres_exists else "presentation.txt missing"})

    # Check 3: themes/ directory exists and has at least 10 txt files
    themes_dir = os.path.join(workspace_path, 'themes')
    themes_exist = os.path.isdir(themes_dir)
    theme_files = []
    if themes_exist:
        theme_files = [f for f in os.listdir(themes_dir) if f.endswith('.txt')]
    themes_correct_count = len(theme_files) >= 10
    results.append({"name": "themes_directory_and_files", "passed": themes_exist and themes_correct_count,
                    "detail": f'themes directory with 10+ .txt files found: {len(theme_files)}' if themes_exist else 'themes directory missing or insufficient files'})

    # Check 4: styled_presentation.txt created
    styled_path = os.path.join(workspace_path, 'styled_presentation.txt')
    styled_exists = os.path.isfile(styled_path)
    results.append({"name": "styled_output_created", "passed": styled_exists,
                    "detail": "styled_presentation.txt file found" if styled_exists else "styled_presentation.txt missing"})

    if not styled_exists:
        print(json.dumps({"passed": False, "score": 0.0, "checks": results}))
        return

    # Check 5+: Verify styled output contains annotations for a valid chosen theme
    # Infer chosen theme by scanning styled_presentation.txt for any theme name from list
    theme_names = [
        "Ocean Depths", "Sunset Boulevard", "Forest Canopy", "Modern Minimalist", "Golden Hour",
        "Arctic Frost", "Desert Rose", "Tech Innovation", "Botanical Garden", "Midnight Galaxy"
    ]
    styled_text = read_file_contents(styled_path)
    chosen_theme = None
    for theme in theme_names:
        if re.search(re.escape(theme), styled_text, re.IGNORECASE):
            chosen_theme = theme
            break

    if not chosen_theme:
        results.append({"name": "chosen_theme_mentioned", "passed": False,
                        "detail": "No valid theme name mention found in styled_presentation.txt"})
    else:
        results.append({"name": "chosen_theme_mentioned", "passed": True,
                        "detail": f'Chosen theme "{chosen_theme}" found in output'})

    # If chosen theme found, check if style annotations correspond to that theme specs
    if chosen_theme:
        theme_file = find_theme_file(themes_dir, chosen_theme)
        if not theme_file:
            results.append({"name": "theme_spec_file_found", "passed": False,
                            "detail": f"Theme spec file for {chosen_theme} not found"})
        else:
            results.append({"name": "theme_spec_file_found", "passed": True,
                            "detail": f"Theme spec file {os.path.basename(theme_file)} found"})
            theme_spec_text = read_file_contents(theme_file)
            colors, fonts = parse_theme_spec(theme_spec_text)
            styling_correct = check_styling_applied(styled_text, colors, fonts)
            results.append({"name": "styling_correctly_applied", "passed": styling_correct,
                            "detail": "Styled output correctly annotated with fonts and colors" if styling_correct else "Styled output missing or incorrect font/color annotations"})
    else:
        # Can't check further without theme
        results.append({"name": "theme_spec_file_found", "passed": False,
                        "detail": "Skipping styling checks due to missing theme"})
        results.append({"name": "styling_correctly_applied", "passed": False,
                        "detail": "Skipping styling checks due to missing theme"})

    # Calculate score and final pass
    passed_checks = sum(1 for c in results if c.get('passed'))
    score = passed_checks / max(len(results), 1)
    passed = score == 1.0

    print(json.dumps({"passed": passed, "score": score, "checks": results}))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: eval.py <workspace>")
        sys.exit(1)
    workspace = sys.argv[1]
    main(workspace)
