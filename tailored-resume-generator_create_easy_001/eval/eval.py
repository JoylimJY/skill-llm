import os
import re
import sys
import json

def find_best_md_file(workspace):
    md_files = [f for f in os.listdir(workspace) if f.lower().endswith('.md')]
    if not md_files:
        return None
    # Evaluate all md files and choose best scoring
    return md_files

def check_professional_summary(text):
    # Check presence of approx 3-4 lines summary mentioning years experience, Python, Django, React
    patterns = [
        r'\b3\+? years?\b',
        r'python',
        r'django',
        r'react',
        r'software engineer',
        r'problem[- ]solving',
        r'communication',
    ]
    count = sum(1 for p in patterns if re.search(p, text, re.I))
    passed = count >= 4  # At least 4 key phrases present
    return passed, f'Matched {count}/7 required summary keywords'

def check_technical_skills(text):
    # Check python, django, react, aws, ci/cd, testing frameworks present
    required_skills = ['python', 'django', 'react', 'aws', 'ci/cd', 'testing', 'unit test']
    hits = [skill for skill in required_skills if skill.lower() in text.lower()]
    passed = len(hits) >= 5
    return passed, f'Matched skills: {hits}'

def check_professional_experience(text):
    # Check for mentions of 'backend', 'api', 'test', 'integrate', 'automated', 'coverage', 'flask', 'aws EC2'
    keywords = ['backend', 'api', 'test', 'integration', 'automated', 'coverage', 'flask', 'aws ec2', 'aws s3']
    hits = [kw for kw in keywords if kw.lower() in text.lower()]
    passed = len(hits) >= 5
    # Also check numeric metric 80% coverage present
    coverage_match = re.search(r'80\s*%|80\s*percent', text, re.I)
    if coverage_match:
        passed = passed and True
    else:
        passed = False
    return passed, f'Matched experience keywords: {hits}; coverage found: {bool(coverage_match)}'

def check_education(text):
    # Check 'bachelor' and 'computer science' present
    if re.search(r'bachelor', text, re.I) and re.search(r'computer science', text, re.I):
        return True, 'Education degree found'
    else:
        return False, 'Bachelor degree in Computer Science missing'

def evaluate_md_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    checks = []

    ps_passed, ps_detail = check_professional_summary(text)
    checks.append({'name': 'Professional Summary', 'passed': ps_passed, 'detail': ps_detail})

    ts_passed, ts_detail = check_technical_skills(text)
    checks.append({'name': 'Technical Skills', 'passed': ts_passed, 'detail': ts_detail})

    pe_passed, pe_detail = check_professional_experience(text)
    checks.append({'name': 'Professional Experience', 'passed': pe_passed, 'detail': pe_detail})

    ed_passed, ed_detail = check_education(text)
    checks.append({'name': 'Education', 'passed': ed_passed, 'detail': ed_detail})

    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count/len(checks) if checks else 0
    passed_overall = (score == 1.0)

    result = {
        'passed': passed_overall,
        'score': score,
        'checks': checks
    }
    return result

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'General', 'passed': False, 'detail': 'Workspace path argument missing'}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    md_files = find_best_md_file(workspace)
    if not md_files:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'File check', 'passed': False, 'detail': 'No markdown file found in workspace'}]}))
        sys.exit(1)

    # Evaluate all markdown files, keep best score
    best_result = None
    for md_file in md_files:
        full_path = os.path.join(workspace, md_file)
        result = evaluate_md_file(full_path)
        if not best_result or result['score'] > best_result['score']:
            best_result = result

    print(json.dumps(best_result))

if __name__ == '__main__':
    main()
