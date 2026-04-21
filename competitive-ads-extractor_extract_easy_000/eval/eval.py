import imghdr
import json
import os
import re
import sys


def find_best_markdown_file(dir_path):
    md_files = [f for f in os.listdir(dir_path) if f.lower().endswith('.md')]
    if not md_files:
        return None
    for fname in md_files:
        if 'analysis' in fname.lower():
            return os.path.join(dir_path, fname)
    return os.path.join(dir_path, md_files[0])


def extract_total_ads(content):
    # Priority 1: Look for explicit "active ads" mentions (to distinguish from total/inactive)
    active_patterns = [
        r'active\s+ads?(?:\s+extracted)?\s*[:\-]?\s*(\d+)',
        r'(?:total\s+)?active\s+ads?\s*[:\-]?\s*(\d+)',
        r'(?:^|\n)\s*\*?active\s+ads?\*?\s*[:\-]?\s*(\d+)',
    ]
    # Priority 2: General patterns for total ads
    general_patterns = [
        r'total\s+number\s+of\s+ads?(?:\s+extracted)?\s*[:\-]?\s*(\d+)',
        r'total\s+ads?(?:\s+extracted)?\s*[:\-]?\s*(\d+)',
    ]
    
    # Try active patterns first
    for pattern in active_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            try:
                return int(matches[0])
            except Exception:
                pass
    
    # Fallback to general patterns
    for pattern in general_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            try:
                return int(matches[0])
            except Exception:
                pass
    return None


def check_analysis_report(path):
    checks = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
    except Exception as e:
        return [{'name': 'Analysis Report Readable', 'passed': False, 'detail': f'Exception reading file: {e}'}]

    total_ads_found = extract_total_ads(content)
    if total_ads_found is None:
        checks.append({'name': 'Reports total ads count', 'passed': False, 'detail': 'Total ads count not found'})
    else:
        checks.append({'name': 'Reports total ads count', 'passed': total_ads_found == 3, 'detail': f'Found total ads: {total_ads_found}, expected 3'})

    themes = ['tool sprawl', 'meeting overload', 'collaboration']
    themes_found = [theme for theme in themes if theme in content]
    checks.append({'name': 'Mentions main messaging themes', 'passed': len(themes_found) >= 2, 'detail': f'Found themes: {themes_found}' if len(themes_found) >= 2 else f'Only found themes: {themes_found}'})

    ctas = ['try now', 'get started', 'learn more']
    ctas_found = [cta for cta in ctas if cta in content]
    checks.append({'name': 'Mentions common call-to-action phrases', 'passed': len(ctas_found) >= 2, 'detail': f'Found CTAs: {ctas_found}' if len(ctas_found) >= 2 else f'Only found CTAs: {ctas_found}'})

    rec_keywords = ['recommend', 'test', 'messaging', 'pain point', 'copy', 'ads']
    checks.append({'name': 'Includes recommendations on messaging', 'passed': any(word in content for word in rec_keywords), 'detail': 'Recommendations text found' if any(word in content for word in rec_keywords) else 'No recommendations text found'})
    return checks


def check_png_screenshots(dir_path):
    files = os.listdir(dir_path)
    png_files = [f for f in files if f.lower().endswith('.png')]
    expected_files = ['ad001.png', 'ad002.png', 'ad003.png']
    found_expected = [f for f in expected_files if f in png_files]
    checks = []
    if len(found_expected) == len(expected_files):
        valid_png = True
        for fname in found_expected:
            filepath = os.path.join(dir_path, fname)
            try:
                if imghdr.what(filepath) != 'png':
                    valid_png = False
                    break
            except Exception:
                valid_png = False
                break
        checks.append({'name': 'All required ad screenshots exist as valid PNGs', 'passed': valid_png, 'detail': f'Found {len(found_expected)} PNGs out of {len(expected_files)}'})
    else:
        checks.append({'name': 'All required ad screenshots exist as valid PNGs', 'passed': False, 'detail': f'Missing PNG files: {set(expected_files) - set(png_files)}'})
    return checks


def main():
    workspace = sys.argv[1]
    overall_checks = []

    acme_dir = os.path.join(workspace, 'acme-ads')
    if not os.path.isdir(acme_dir):
        overall_checks.append({'name': 'Exists acme-ads directory', 'passed': False, 'detail': 'acme-ads directory not found'})
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': overall_checks}))
        return
    overall_checks.append({'name': 'Exists acme-ads directory', 'passed': True, 'detail': 'Found acme-ads directory'})

    overall_checks.extend(check_png_screenshots(acme_dir))

    md_path = find_best_markdown_file(workspace)
    if md_path is None:
        overall_checks.append({'name': 'Analysis markdown file found', 'passed': False, 'detail': 'No markdown analysis file found'})
    else:
        overall_checks.append({'name': 'Analysis markdown file found', 'passed': True, 'detail': f'Found {md_path}'})
        overall_checks.extend(check_analysis_report(md_path))

    passed_count = sum(1 for c in overall_checks if c.get('passed'))
    total = len(overall_checks)
    score = passed_count / total if total > 0 else 0.0
    passed = score == 1.0
    print(json.dumps({'passed': passed, 'score': score, 'checks': overall_checks}))


if __name__ == '__main__':
    main()
