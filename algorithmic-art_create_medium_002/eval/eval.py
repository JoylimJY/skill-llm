import json
import os
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    passed_count = 0
    
    # Check 1: HTML file exists
    html_files = list(Path(workspace_dir).glob('*.html'))
    html_found = any('recursive_bloom' in f.name.lower() for f in html_files)
    check1 = {'name': 'HTML file exists with correct name', 'passed': html_found, 'detail': f'Found {len(html_files)} HTML files'}
    checks.append(check1)
    if html_found:
        passed_count += 1
    
    if not html_found:
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    html_file = next(f for f in html_files if 'recursive_bloom' in f.name.lower())
    with open(html_file, 'r') as f:
        content = f.read().lower()
    
    # Check 2: p5.js included
    check2 = {'name': 'p5.js library included', 'passed': 'p5.js' in content or 'p5.min.js' in content, 'detail': 'p5.js CDN reference found'}
    checks.append(check2)
    if check2['passed']:
        passed_count += 1
    
    # Check 3: Canvas setup
    check3 = {'name': 'Canvas setup present', 'passed': 'createcanvas' in content, 'detail': 'createCanvas function found'}
    checks.append(check3)
    if check3['passed']:
        passed_count += 1
    
    # Check 4: Recursion depth parameter
    check4 = {'name': 'Recursion depth parameter', 'passed': any(term in content for term in ['recursion', 'depth', 'recursive']), 'detail': 'Recursion-related parameter found'}
    checks.append(check4)
    if check4['passed']:
        passed_count += 1
    
    # Check 5: Branch angle parameter
    check5 = {'name': 'Branch angle variation parameter', 'passed': any(term in content for term in ['angle', 'variation', 'branch']), 'detail': 'Branch angle parameter found'}
    checks.append(check5)
    if check5['passed']:
        passed_count += 1
    
    # Check 6: Sub-branches parameter
    check6 = {'name': 'Sub-branches parameter', 'passed': any(term in content for term in ['sub', 'branches', 'subdivide']), 'detail': 'Sub-branches parameter found'}
    checks.append(check6)
    if check6['passed']:
        passed_count += 1
    
    # Check 7: Color pickers
    check7 = {'name': 'Color picker controls', 'passed': content.count('color') >= 2 or 'input type="color"' in content, 'detail': 'Color controls found'}
    checks.append(check7)
    if check7['passed']:
        passed_count += 1
    
    # Check 8: Seed controls
    seed_keywords = ['seed', 'previous', 'next', 'random', 'jump']
    check8 = {'name': 'Seed navigation controls', 'passed': any(kw in content for kw in seed_keywords), 'detail': 'Seed controls found'}
    checks.append(check8)
    if check8['passed']:
        passed_count += 1
    
    # Check 9: Action buttons
    button_keywords = ['regenerate', 'reset', 'download']
    check9 = {'name': 'Action buttons present', 'passed': any(kw in content for kw in button_keywords), 'detail': 'Action buttons found'}
    checks.append(check9)
    if check9['passed']:
        passed_count += 1
    
    # Check 10: Seeded randomness
    check10 = {'name': 'Seeded randomness implemented', 'passed': 'randomseed' in content or 'noiseseed' in content, 'detail': 'Seed functions found'}
    checks.append(check10)
    if check10['passed']:
        passed_count += 1
    
    # Check 11: Self-contained (no external imports except p5.js)
    external_imports = content.count('import') + content.count('require')
    check11 = {'name': 'Self-contained artifact', 'passed': external_imports <= 1, 'detail': f'External imports: {external_imports}'}
    checks.append(check11)
    if check11['passed']:
        passed_count += 1
    
    # Check 12: Slider controls for parameters
    check12 = {'name': 'Parameter sliders present', 'passed': 'input type="range"' in content or 'slider' in content, 'detail': 'Slider controls found'}
    checks.append(check12)
    if check12['passed']:
        passed_count += 1
    
    score = passed_count / len(checks)
    overall_passed = score >= 0.8
    
    return {'passed': overall_passed, 'score': score, 'checks': checks}

if __name__ == '__main__':
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    result = evaluate(workspace)
    print(json.dumps(result))
