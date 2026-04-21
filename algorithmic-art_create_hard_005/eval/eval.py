#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    passed_count = 0
    
    # Check 1: HTML file exists with correct name
    html_files = list(Path(workspace_dir).glob('*.html'))
    html_found = any('recursive' in f.name.lower() and 'echoes' in f.name.lower() for f in html_files)
    check1 = {
        "name": "HTML file exists with 'recursive-echoes' in name",
        "passed": html_found,
        "detail": f"Found {len(html_files)} HTML files. Expected file with 'recursive' and 'echoes' in name."
    }
    checks.append(check1)
    if check1["passed"]:
        passed_count += 1
    
    # Get the HTML file content
    html_content = ""
    if html_found:
        html_file = next(f for f in html_files if 'recursive' in f.name.lower() and 'echoes' in f.name.lower())
        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
    
    # Check 2: Contains p5.js CDN reference
    check2 = {
        "name": "p5.js library included from CDN",
        "passed": 'p5' in html_content.lower() and 'cdnjs' in html_content.lower(),
        "detail": "p5.js must be loaded from CDN (cdnjs or similar)"
    }
    checks.append(check2)
    if check2["passed"]:
        passed_count += 1
    
    # Check 3: Contains seed-related functionality
    check3 = {
        "name": "Seed navigation controls present",
        "passed": any(keyword in html_content.lower() for keyword in ['seed', 'previous', 'next', 'random']),
        "detail": "Must include seed display and navigation buttons (previous, next, random)"
    }
    checks.append(check3)
    if check3["passed"]:
        passed_count += 1
    
    # Check 4: Contains parameter controls
    check4 = {
        "name": "Parameter controls for recursion, angle, and thickness",
        "passed": any(keyword in html_content.lower() for keyword in ['recursion', 'angle', 'thickness']) or 'slider' in html_content.lower(),
        "detail": "Must include controls for recursion_depth, branching_angle, and line_thickness"
    }
    checks.append(check4)
    if check4["passed"]:
        passed_count += 1
    
    # Check 5: Contains setup and draw functions (p5.js pattern)
    check5 = {
        "name": "p5.js setup() and draw() functions present",
        "passed": 'function setup()' in html_content and 'function draw()' in html_content,
        "detail": "Must contain p5.js setup() and draw() functions"
    }
    checks.append(check5)
    if check5["passed"]:
        passed_count += 1
    
    # Check 6: Contains seeded randomness
    check6 = {
        "name": "Seeded randomness implementation",
        "passed": 'randomSeed' in html_content or 'noiseSeed' in html_content,
        "detail": "Must use randomSeed() or noiseSeed() for reproducibility"
    }
    checks.append(check6)
    if check6["passed"]:
        passed_count += 1
    
    # Check 7: Contains Anthropic branding elements
    check7 = {
        "name": "Anthropic branding (fonts and styling)",
        "passed": any(keyword in html_content.lower() for keyword in ['poppins', 'lora', 'anthropic']),
        "detail": "Must reference Poppins and/or Lora fonts and Anthropic branding"
    }
    checks.append(check7)
    if check7["passed"]:
        passed_count += 1
    
    # Check 8: Contains action buttons
    check8 = {
        "name": "Action buttons (regenerate, reset, download)",
        "passed": any(keyword in html_content.lower() for keyword in ['regenerate', 'reset', 'download']),
        "detail": "Must include regenerate, reset, and download buttons"
    }
    checks.append(check8)
    if check8["passed"]:
        passed_count += 1
    
    # Check 9: Self-contained (no external imports except p5.js)
    check9 = {
        "name": "Self-contained artifact (inline CSS and JavaScript)",
        "passed": '<style>' in html_content and '<script>' in html_content,
        "detail": "CSS and JavaScript must be inline, not external files"
    }
    checks.append(check9)
    if check9["passed"]:
        passed_count += 1
    
    # Check 10: Contains canvas or drawing context
    check10 = {
        "name": "Canvas setup for p5.js rendering",
        "passed": 'createCanvas' in html_content,
        "detail": "Must call createCanvas() to set up rendering surface"
    }
    checks.append(check10)
    if check10["passed"]:
        passed_count += 1
    
    score = passed_count / len(checks)
    overall_passed = score >= 0.8
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    evaluate(workspace)
