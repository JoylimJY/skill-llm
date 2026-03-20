#!/usr/bin/env python3
import sys
import os
import json
import re
from bs4 import BeautifulSoup

def evaluate_task(workspace_dir):
    checks = []
    passed = True
    score = 0.0
    
    # Check for algorithmic philosophy markdown file
    philosophy_files = [f for f in os.listdir(workspace_dir) if f.endswith('.md')]
    if philosophy_files:
        checks.append({"name": "Philosophy file exists", "passed": True, "detail": f"Found {philosophy_files[0]}"})
        score += 20
        
        # Check philosophy content
        with open(os.path.join(workspace_dir, philosophy_files[0]), 'r') as f:
            philosophy_content = f.read().lower()
            
        neural_terms = ['neural', 'neuron', 'synap', 'network', 'brain', 'electrical', 'pulse', 'connection']
        neural_found = sum(1 for term in neural_terms if term in philosophy_content)
        if neural_found >= 3:
            checks.append({"name": "Neural-themed philosophy", "passed": True, "detail": f"Found {neural_found} neural-related terms"})
            score += 15
        else:
            checks.append({"name": "Neural-themed philosophy", "passed": False, "detail": f"Only found {neural_found} neural terms"})
            passed = False
    else:
        checks.append({"name": "Philosophy file exists", "passed": False, "detail": "No .md file found"})
        passed = False
    
    # Check for HTML artifact
    html_files = [f for f in os.listdir(workspace_dir) if f.endswith('.html')]
    if html_files:
        checks.append({"name": "HTML artifact exists", "passed": True, "detail": f"Found {html_files[0]}"})
        score += 20
        
        with open(os.path.join(workspace_dir, html_files[0]), 'r') as f:
            html_content = f.read()
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for p5.js inclusion
        p5_script = soup.find('script', {'src': re.compile(r'p5\.js')})
        if p5_script:
            checks.append({"name": "p5.js included", "passed": True, "detail": "Found p5.js CDN link"})
            score += 10
        else:
            checks.append({"name": "p5.js included", "passed": False, "detail": "No p5.js CDN found"})
            passed = False
        
        # Check for seed controls
        if 'seed' in html_content.lower() and ('previous' in html_content.lower() or 'next' in html_content.lower()):
            checks.append({"name": "Seed navigation controls", "passed": True, "detail": "Found seed controls"})
            score += 10
        else:
            checks.append({"name": "Seed navigation controls", "passed": False, "detail": "Missing seed navigation"})
            passed = False
        
        # Check for parameter controls (sliders or inputs)
        sliders = soup.find_all('input', {'type': 'range'})
        if len(sliders) >= 2:
            checks.append({"name": "Interactive parameters", "passed": True, "detail": f"Found {len(sliders)} parameter sliders"})
            score += 15
        else:
            checks.append({"name": "Interactive parameters", "passed": False, "detail": f"Only found {len(sliders)} sliders, need at least 2"})
            passed = False
        
        # Check for neural-themed variables/functions in JavaScript
        js_neural_terms = ['neuron', 'synapse', 'branch', 'pulse', 'network', 'node', 'connection']
        js_neural_found = sum(1 for term in js_neural_terms if term in html_content.lower())
        if js_neural_found >= 2:
            checks.append({"name": "Neural-themed algorithm", "passed": True, "detail": f"Found {js_neural_found} neural terms in code"})
            score += 10
        else:
            checks.append({"name": "Neural-themed algorithm", "passed": False, "detail": f"Only found {js_neural_found} neural terms in code"})
            passed = False
    else:
        checks.append({"name": "HTML artifact exists", "passed": False, "detail": "No .html file found"})
        passed = False
    
    return {
        "passed": passed,
        "score": min(score, 100.0),
        "checks": checks
    }

if __name__ == '__main__':
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    result = evaluate_task(workspace_dir)
    print(json.dumps(result))