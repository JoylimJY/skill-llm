import sys
import os
import json
import re
from glob import glob


def check_json_theme_file(path):
    checks = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return [{"name": "theme_json_loadable", "passed": False, "detail": f"Failed to read JSON: {e}"}]

    colors = data.get('colors') or data.get('palette') or None
    fonts = data.get('fonts')

    # Check keys
    color_keys = ['primary', 'secondary', 'accent']
    required_color_hexes = ['#2A4365', '#E2E8F0', '#FFFFFF']

    if colors and isinstance(colors, dict):
        # Check if required colors present with close hex representation
        # Allow partial case insensitivity
        found_colors = [v.lower() for v in colors.values()]
        color_check = all(any(req_hex.lower() == val for val in found_colors) for req_hex in required_color_hexes)
    else:
        color_check = False

    if fonts and isinstance(fonts, dict):
        header_font = fonts.get('header', '').lower()
        body_font = fonts.get('body', '').lower()
        fonts_check = ('open sans' in header_font) and ('roboto' in body_font)
    else:
        fonts_check = False

    checks.append({
        "name": "theme_contains_required_colors",
        "passed": color_check,
        "detail": "Theme JSON must contain calm blues (#2A4365), soft grays (#E2E8F0), and crisp whites (#FFFFFF) in its color palette."
    })

    checks.append({
        "name": "theme_contains_required_fonts",
        "passed": fonts_check,
        "detail": "Theme JSON must specify 'Open Sans' for header font and 'Roboto' for body font."
    })

    # Check theme name (accept 'name' or 'theme_name' as valid keys)
    theme_name = data.get('name', '') or data.get('theme_name', '')
    name_check = 'corporate clarity' in theme_name.lower()

    checks.append({
        "name": "theme_name_correct",
        "passed": name_check,
        "detail": "Theme name must include 'Corporate Clarity'."
    })

    return checks


def check_html_styled_file(path):
    checks = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            html = f.read().lower()
    except Exception as e:
        return [{"name": "html_loadable", "passed": False, "detail": f"Failed to read HTML file: {e}"}]

    # Check for color hex codes in style
    color_hexes = ['#2a4365', '#e2e8f0', '#ffffff']
    color_checks = [hexcode in html for hexcode in color_hexes]

    # Check for font families
    header_fonts_ok = any(font in html for font in ['open sans', 'open-sans'])
    body_fonts_ok = 'roboto' in html

    # Check usage of headers: <h1>, <h2> etc
    has_headers = bool(re.search(r'<h[1-6]>', html))
    has_body_text = bool(re.search(r'<p>', html))

    checks.append({
        "name": "html_contains_all_theme_colors",
        "passed": all(color_checks),
        "detail": f"HTML must include all theme colors {color_hexes}, found presence: {color_checks}"
    })
    checks.append({
        "name": "html_uses_header_font",
        "passed": header_fonts_ok,
        "detail": "HTML must use 'Open Sans' font for headers."
    })
    checks.append({
        "name": "html_uses_body_font",
        "passed": body_fonts_ok,
        "detail": "HTML must use 'Roboto' font for body text."
    })
    checks.append({
        "name": "html_contains_headers",
        "passed": has_headers,
        "detail": "HTML must contain header tags like <h1> to <h6>."
    })
    checks.append({
        "name": "html_contains_body_paragraphs",
        "passed": has_body_text,
        "detail": "HTML must contain body text paragraphs."
    })

    return checks


def main(workspace):
    # Find theme JSON
    theme_files = [f for f in os.listdir(workspace) if f.lower().endswith('.json') and 'corporate' in f.lower()]
    html_files = [f for f in os.listdir(workspace) if f.lower().endswith('.html') and 'quarterly_results_styled' in f.lower()]

    best_checks = []
    best_score = 0.0

    # Evaluate theme JSONs - keep best scoring
    for theme_file in theme_files:
        checks = check_json_theme_file(os.path.join(workspace, theme_file))
        score = sum(c['passed'] for c in checks)/len(checks) if checks else 0
        if score > best_score:
            best_score = score
            best_checks = checks

    theme_checks = best_checks
    theme_score = best_score

    # Evaluate HTML files - keep best scoring
    best_html_checks = []
    best_html_score = 0.0

    for html_file in html_files:
        checks = check_html_styled_file(os.path.join(workspace, html_file))
        score = sum(c['passed'] for c in checks)/len(checks) if checks else 0
        if score > best_html_score:
            best_html_score = score
            best_html_checks = checks

    # Aggregate results
    all_checks = []
    all_checks.extend(theme_checks)
    all_checks.extend(best_html_checks)

    if not all_checks:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "no_output_files", "passed": False, "detail": "Required output files not found."}]}))
        return

    total_passed = sum(c['passed'] for c in all_checks)
    total_checks = len(all_checks)

    result = {
        "passed": total_passed == total_checks and total_checks > 0,
        "score": total_passed / total_checks if total_checks > 0 else 0.0,
        "checks": all_checks
    }

    print(json.dumps(result))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg_missing", "passed": False, "detail": "Workspace directory argument missing."}]}))
        sys.exit(1)
    main(sys.argv[1])
