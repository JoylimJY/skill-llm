#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Check 1: Output file exists
    output_file = Path(workspace_dir) / 'slides_styled.html'
    file_exists = output_file.exists()
    checks.append({
        "name": "Output file exists",
        "passed": file_exists,
        "detail": f"File 'slides_styled.html' {'found' if file_exists else 'not found'}"
    })
    
    if not file_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    
    # Read the output file
    with open(output_file, 'r') as f:
        content = f.read().lower()
    
    # Check 2: Contains Ocean Depths primary color
    has_primary_color = '#1a3a52' in content
    checks.append({
        "name": "Contains Ocean Depths primary color",
        "passed": has_primary_color,
        "detail": "Primary color #1a3a52 found in styled HTML"
    })
    
    # Check 3: Contains Ocean Depths secondary color
    has_secondary_color = '#2d5a7b' in content
    checks.append({
        "name": "Contains Ocean Depths secondary color",
        "passed": has_secondary_color,
        "detail": "Secondary color #2d5a7b found in styled HTML"
    })
    
    # Check 4: Contains Ocean Depths accent color
    has_accent_color = '#4a90a4' in content
    checks.append({
        "name": "Contains Ocean Depths accent color",
        "passed": has_accent_color,
        "detail": "Accent color #4a90a4 found in styled HTML"
    })
    
    # Check 5: Contains Ocean Depths background color
    has_background_color = '#e8f4f8' in content
    checks.append({
        "name": "Contains Ocean Depths background color",
        "passed": has_background_color,
        "detail": "Background color #e8f4f8 found in styled HTML"
    })
    
    # Check 6: Contains header font (Segoe UI)
    has_header_font = 'segoe ui' in content
    checks.append({
        "name": "Contains header font",
        "passed": has_header_font,
        "detail": "Header font 'Segoe UI' found in styled HTML"
    })
    
    # Check 7: Contains body font (Calibri)
    has_body_font = 'calibri' in content
    checks.append({
        "name": "Contains body font",
        "passed": has_body_font,
        "detail": "Body font 'Calibri' found in styled HTML"
    })
    
    # Check 8: Original content preserved
    has_original_content = 'slide 1' in content and 'introduction' in content
    checks.append({
        "name": "Original slide content preserved",
        "passed": has_original_content,
        "detail": "Original slide content found in output"
    })
    
    # Calculate score
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks)
    overall_passed = score >= 1.0
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '/workspace'
    result = evaluate(workspace)
    print(json.dumps(result))
