import os
import sys
import json
import re

def case_insensitive_contains(text, keywords):
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in keywords)

def find_best_md_report(directory):
    # Find all .md files
    md_files = [f for f in os.listdir(directory) if f.lower().endswith('.md')]
    if not md_files:
        return None
    # Return path (use first for evaluation)
    return os.path.join(directory, md_files[0])

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ''

def eval_report(report_content, ads_metadata):
    checks = []
    # Total ads check
    total_ads_declared = None
    match = re.search(r'total\s+number\s+of\s+ads\s+.*?(\d+)', report_content, re.IGNORECASE)
    if match:
        total_ads_declared = int(match.group(1))
    else:
        # Try with 'total ads: 5' pattern
        match = re.search(r'total\s+ads\s*[:\-]\s*(\d+)', report_content, re.IGNORECASE)
        if match:
            total_ads_declared = int(match.group(1))

    expected_total_ads = len(ads_metadata)
    checks.append({
        'name': 'Total Ads Count',
        'passed': total_ads_declared == expected_total_ads,
        'detail': f'Declared total ads = {total_ads_declared}, expected = {expected_total_ads}'
    })

    # Check top 3 problems addressed with example copy (at least 2 ads per problem)
    problems = [ad.get('problem', '').lower() for ad in ads_metadata]
    unique_problems = list(sorted(set(problems), key=problems.count, reverse=True))[:3]

    problem_sections_found = []
    for problem in unique_problems:
        # Look for section about this problem (allow some fuzziness)
        problem_pattern = re.compile(re.escape(problem), re.IGNORECASE)
        found = bool(problem_pattern.search(report_content))
        problem_sections_found.append((problem, found))

    passed_problems = sum(found for _, found in problem_sections_found)
    checks.append({
        'name': 'Top 3 Problems Discussed',
        'passed': passed_problems >= 3,
        'detail': f'Discussed problems: {[(p, f) for p,f in problem_sections_found]}'
    })

    # Check for at least 2 example ads per problem: look for repeated ad copy excerpts
    # We'll check if example copy (from ads_metadata) appears at least twice per problem
    problem_examples_passed = True
    for problem in unique_problems:
        ads_with_problem = [ad for ad in ads_metadata if ad.get('problem', '').lower() == problem]
        count_with_copy_in_report = 0
        for ad in ads_with_problem:
            # Use the ad copy text
            copy = ad.get('copy', '').lower()
            if copy and copy in report_content.lower():
                count_with_copy_in_report += 1
        if count_with_copy_in_report < 2:
            problem_examples_passed = False
            break

    checks.append({
        'name': 'Example Copy For Problems',
        'passed': problem_examples_passed,
        'detail': f'At least 2 example ad copies per problem in report'
    })

    # Check at least 2 creative approaches described
    # We accept keywords like 'video', 'static image', 'before/after', 'visual metaphor', 'creative pattern'
    creative_keywords = ['video', 'static image', 'before/after', 'creative pattern', 'visual metaphor', 'gif', 'testimonials']
    creative_found = any(k in report_content.lower() for k in creative_keywords)
    # Check at least two distinct keywords present
    found_keyword_count = sum(1 for k in creative_keywords if k in report_content.lower())
    checks.append({
        'name': 'At Least 2 Creative Approaches',
        'passed': found_keyword_count >= 2,
        'detail': f'Creative keywords found count: {found_keyword_count}'
    })

    # Check call-to-action phrases frequently used
    ctas_expected = set(ad.get('cta', '').lower() for ad in ads_metadata)
    # Check if at least 3 of those CTAs appear in the report
    ctas_in_report = [cta for cta in ctas_expected if cta and cta in report_content.lower()]
    checks.append({
        'name': 'Key CTAs Mentioned',
        'passed': len(ctas_in_report) >= 3,
        'detail': f'CTAs found in report: {ctas_in_report}'
    })

    # Check for presence of required files/folders
    folder_exists = os.path.isdir(os.path.join('.', 'acme-facebook-ads'))
    checks.append({
        'name': 'Ads Screenshot Folder Exists',
        'passed': folder_exists,
        'detail': f'acme-facebook-ads folder found: {folder_exists}'
    })

    # Check PNG files count matches ads count
    if folder_exists:
        png_files = [f for f in os.listdir('acme-facebook-ads') if f.lower().endswith('.png')]
        checks.append({
            'name': 'PNG Screenshot Count Matches Ads',
            'passed': len(png_files) == expected_total_ads,
            'detail': f'PNG files = {len(png_files)}, expected = {expected_total_ads}'
        })
    else:
        checks.append({
            'name': 'PNG Screenshot Count Matches Ads',
            'passed': False,
            'detail': 'Folder not found, cannot verify PNG files'
        })

    # Check markdown report file exists and has content
    md_files = [f for f in os.listdir('.') if f.lower().endswith('.md')]
    report_found = False
    if md_files:
        for md in md_files:
            content = read_file(md)
            if 'problem' in content.lower() and 'cta' in content.lower():
                report_found = True
                break
    checks.append({
        'name': 'Markdown Report Present',
        'passed': report_found,
        'detail': f'Markdown report found with expected analysis content: {report_found}'
    })

    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c['passed'])
    score = passed_checks / total_checks if total_checks > 0 else 0.0

    result = {
        'passed': score >= 0.8,
        'score': score,
        'checks': checks
    }
    print(json.dumps(result))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0, "checks": [{"name": "Invocation", "passed": False, "detail": "Workspace directory required as an argument"}]}))
        sys.exit(1)

    workspace = sys.argv[1]

    # Read ads metadata to know expected properties
    ads_metadata = []
    metadata_path = os.path.join(workspace, 'acme-facebook-ads', 'ads_metadata.json')
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            ads_metadata = json.load(f)
    except Exception:
        ads_metadata = []

    # Try to find markdown report in workspace
    md_report = find_best_md_report(workspace)

    md_content = ''
    if md_report:
        md_content = read_file(md_report)

    os.chdir(workspace)

    eval_report(md_content, ads_metadata)
