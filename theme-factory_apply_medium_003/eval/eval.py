#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)
    
    # Check 1: styled_slides.html exists
    styled_file = workspace / 'styled_slides.html'
    check1 = {
        "name": "Output file exists",
        "passed": styled_file.exists(),
        "detail": f"File 'styled_slides.html' {'found' if styled_file.exists() else 'not found'}"
    }
    checks.append(check1)
    
    if not check1["passed"]:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Read the styled HTML
    with open(styled_file, 'r') as f:
        html_content = f.read()
    
    # Check 2: Contains Ocean Depths primary color
    check2 = {
        "name": "Ocean Depths primary color applied",
        "passed": "#1a4d6d" in html_content,
        "detail": "Primary color #1a4d6d from Ocean Depths theme found in HTML"
    }
    checks.append(check2)
    
    # Check 3: Contains Ocean Depths background color
    check3 = {
        "name": "Ocean Depths background color applied",
        "passed": "#e8f4f8" in html_content,
        "detail": "Background color #e8f4f8 from Ocean Depths theme found in HTML"
    }
    checks.append(check3)
    
    # Check 4: Contains Ocean Depths accent color
    check4 = {
        "name": "Ocean Depths accent color applied",
        "passed": "#2d7a99" in html_content,
        "detail": "Accent color #2d7a99 from Ocean Depths theme found in HTML"
    }
    checks.append(check4)
    
    # Check 5: Contains header font
    check5 = {
        "name": "Header font applied",
        "passed": "Segoe UI" in html_content,
        "detail": "Header font 'Segoe UI' from Ocean Depths theme found in HTML"
    }
    checks.append(check5)
    
    # Check 6: Contains body font
    check6 = {
        "name": "Body font applied",
        "passed": "Open Sans" in html_content,
        "detail": "Body font 'Open Sans' from Ocean Depths theme found in HTML"
    }
    checks.append(check6)
    
    # Check 7: HTML structure preserved
    check7 = {
        "name": "Original HTML structure preserved",
        "passed": "<h1>" in html_content and "<p>" in html_content and "Slide" in html_content,
        "detail": "Original slide content and structure maintained"
    }
    checks.append(check7)
    
    # Calculate score
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / len(checks)
    overall_passed = score >= 0.8
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result))
