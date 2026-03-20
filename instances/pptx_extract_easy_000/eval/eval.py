#!/usr/bin/env python3
import sys
import os
import subprocess
import json
from pathlib import Path

def run_markitdown(pptx_file):
    """Run markitdown on the PPTX file and return the output"""
    try:
        result = subprocess.run(
            ['python', '-m', 'markitdown', pptx_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return '', 'Timeout expired', 1
    except Exception as e:
        return '', str(e), 1

def check_extracted_content(content):
    """Check if all marker content is present in extracted text"""
    required_markers = [
        'MARKER_TITLE_2024',
        'MARKER_SUBTITLE_PLANNING', 
        'MARKER_KPI_SECTION',
        'MARKER_REVENUE_42_PERCENT',
        'MARKER_SATISFACTION_94_SCORE',
        'MARKER_EXPANSION_5_REGIONS',
        'MARKER_TEAM_28_MEMBERS',
        'MARKER_GOALS_Q1_2025',
        'MARKER_PRODUCT_INNOVATION',
        'MARKER_MARKET_SHARE_TARGET',
        'MARKER_HIRING_PLAN_10'
    ]
    
    found_markers = []
    missing_markers = []
    
    for marker in required_markers:
        if marker in content:
            found_markers.append(marker)
        else:
            missing_markers.append(marker)
    
    return found_markers, missing_markers

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        return
    
    workspace_dir = Path(sys.argv[1])
    pptx_file = workspace_dir / 'quarterly_review.pptx'
    
    checks = []
    
    # Check if input file exists
    if not pptx_file.exists():
        checks.append({"name": "input_file_exists", "passed": False, "detail": f"Input file {pptx_file} not found"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    checks.append({"name": "input_file_exists", "passed": True, "detail": "Input PPTX file found"})
    
    # Run markitdown extraction
    stdout, stderr, returncode = run_markitdown(str(pptx_file))
    
    if returncode != 0:
        checks.append({"name": "extraction_success", "passed": False, "detail": f"markitdown failed: {stderr}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    checks.append({"name": "extraction_success", "passed": True, "detail": "Text extraction completed successfully"})
    
    # Check if content was extracted (not empty)
    if not stdout.strip():
        checks.append({"name": "content_extracted", "passed": False, "detail": "No content extracted from presentation"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    checks.append({"name": "content_extracted", "passed": True, "detail": f"Extracted {len(stdout)} characters of content"})
    
    # Check for marker content
    found_markers, missing_markers = check_extracted_content(stdout)
    
    marker_check_passed = len(missing_markers) == 0
    marker_detail = f"Found {len(found_markers)}/11 required markers"
    if missing_markers:
        marker_detail += f". Missing: {', '.join(missing_markers[:3])}{'...' if len(missing_markers) > 3 else ''}"
    
    checks.append({"name": "marker_content_present", "passed": marker_check_passed, "detail": marker_detail})
    
    # Check for key business terms (shows meaningful extraction)
    business_terms = ['Revenue Growth', 'Customer Satisfaction', 'Market Expansion', 'Next Quarter Goals']
    found_terms = [term for term in business_terms if term in stdout]
    
    terms_check_passed = len(found_terms) >= 3
    checks.append({"name": "business_terms_extracted", "passed": terms_check_passed, "detail": f"Found {len(found_terms)}/4 expected business terms"})
    
    # Calculate overall score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    overall_passed = score >= 0.8  # Need 80% of checks to pass
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()