#!/usr/bin/env python3
import sys
import os
import json
from bs4 import BeautifulSoup

def eval_task(workspace_dir):
    checks = []
    passed = True
    score = 0.0
    
    # Check if HTML file exists
    html_files = [f for f in os.listdir(workspace_dir) if f.endswith('.html')]
    if not html_files:
        checks.append({'name': 'HTML file exists', 'passed': False, 'detail': 'No HTML file found'})
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    html_file = html_files[0]
    checks.append({'name': 'HTML file exists', 'passed': True, 'detail': f'Found {html_file}'})
    score += 0.2
    
    # Read and parse HTML
    try:
        with open(os.path.join(workspace_dir, html_file), 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        checks.append({'name': 'HTML readable', 'passed': False, 'detail': f'Error reading HTML: {e}'})
        return {'passed': False, 'score': score, 'checks': checks}
    
    checks.append({'name': 'HTML readable', 'passed': True, 'detail': 'HTML file parsed successfully'})
    score += 0.1
    
    # Check for p5.js CDN
    p5_script = soup.find('script', src=lambda x: x and 'p5.js' in x)
    if p5_script:
        checks.append({'name': 'p5.js CDN included', 'passed': True, 'detail': 'Found p5.js script tag'})
        score += 0.1
    else:
        checks.append({'name': 'p5.js CDN included', 'passed': False, 'detail': 'p5.js CDN not found'})
        passed = False
    
    # Check for setup() function
    if 'function setup()' in html_content:
        checks.append({'name': 'setup() function', 'passed': True, 'detail': 'setup() function found'})
        score += 0.1
    else:
        checks.append({'name': 'setup() function', 'passed': False, 'detail': 'setup() function not found'})
        passed = False
    
    # Check for draw() function
    if 'function draw()' in html_content:
        checks.append({'name': 'draw() function', 'passed': True, 'detail': 'draw() function found'})
        score += 0.1
    else:
        checks.append({'name': 'draw() function', 'passed': False, 'detail': 'draw() function not found'})
        passed = False
    
    # Check for seeded randomness
    has_seed = 'randomSeed(' in html_content or 'noiseSeed(' in html_content
    if has_seed:
        checks.append({'name': 'Seeded randomness', 'passed': True, 'detail': 'Found randomSeed or noiseSeed'})
        score += 0.1
    else:
        checks.append({'name': 'Seeded randomness', 'passed': False, 'detail': 'No seeded randomness found'})
        passed = False
    
    # Check for parameter controls (sliders)
    has_controls = 'type="range"' in html_content
    if has_controls:
        checks.append({'name': 'Parameter controls', 'passed': True, 'detail': 'Found input sliders'})
        score += 0.1
    else:
        checks.append({'name': 'Parameter controls', 'passed': False, 'detail': 'No parameter sliders found'})
        passed = False
    
    # Check for wave/flow related terms in comments or variables
    wave_terms = ['wave', 'flow', 'fluid', 'water', 'organic', 'noise', 'sin', 'cos']
    found_terms = [term for term in wave_terms if term.lower() in html_content.lower()]
    if found_terms:
        checks.append({'name': 'Wave/flow concepts', 'passed': True, 'detail': f'Found terms: {found_terms}'})
        score += 0.1
    else:
        checks.append({'name': 'Wave/flow concepts', 'passed': False, 'detail': 'No wave/flow related concepts found'})
        passed = False
    
    # Check for algorithmic philosophy (markdown file)
    md_files = [f for f in os.listdir(workspace_dir) if f.endswith('.md')]
    if md_files:
        checks.append({'name': 'Algorithmic philosophy', 'passed': True, 'detail': f'Found {md_files[0]}'})
        score += 0.1
    else:
        checks.append({'name': 'Algorithmic philosophy', 'passed': False, 'detail': 'No markdown philosophy file found'})
    
    return {'passed': passed, 'score': score, 'checks': checks}

if __name__ == '__main__':
    result = eval_task(sys.argv[1])
    print(json.dumps(result))