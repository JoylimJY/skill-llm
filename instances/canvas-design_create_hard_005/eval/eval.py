#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path

def check_task_completion(workspace_path):
    workspace = Path(workspace_path)
    checks = []
    
    # Check if marker file exists (proves task was attempted)
    marker_file = workspace / 'task_marker.txt'
    marker_exists = marker_file.exists()
    if marker_exists:
        with open(marker_file, 'r') as f:
            marker_content = f.read().strip()
        marker_valid = marker_content == 'DIGITAL_ARCHAEOLOGY_TASK_MARKER_2024'
    else:
        marker_valid = False
    
    checks.append({
        'name': 'Task marker validation',
        'passed': marker_valid,
        'detail': f'Marker file exists: {marker_exists}, content valid: {marker_valid}'
    })
    
    # Check for design philosophy markdown file
    md_files = list(workspace.glob('*.md'))
    philosophy_exists = len(md_files) > 0
    
    philosophy_quality = False
    if philosophy_exists:
        md_content = md_files[0].read_text()
        # Check for key philosophy elements
        has_movement_name = len(md_content) > 200
        has_visual_focus = any(word in md_content.lower() for word in ['visual', 'space', 'form', 'color', 'composition'])
        has_craftsmanship = any(phrase in md_content.lower() for phrase in ['craft', 'meticulous', 'expertise', 'precision'])
        philosophy_quality = has_movement_name and has_visual_focus and has_craftsmanship
    
    checks.append({
        'name': 'Design philosophy creation',
        'passed': philosophy_exists and philosophy_quality,
        'detail': f'Philosophy file exists: {philosophy_exists}, quality indicators: {philosophy_quality}'
    })
    
    # Check for visual output (PDF or PNG)
    pdf_files = list(workspace.glob('*.pdf'))
    png_files = list(workspace.glob('*.png'))
    visual_output_exists = len(pdf_files) > 0 or len(png_files) > 0
    
    checks.append({
        'name': 'Visual artwork creation',
        'passed': visual_output_exists,
        'detail': f'PDF files: {len(pdf_files)}, PNG files: {len(png_files)}'
    })
    
    # Check file sizes to ensure substantial content
    substantial_output = False
    if pdf_files:
        pdf_size = pdf_files[0].stat().st_size
        substantial_output = pdf_size > 5000  # At least 5KB
    elif png_files:
        png_size = png_files[0].stat().st_size
        substantial_output = png_size > 10000  # At least 10KB
    
    checks.append({
        'name': 'Output file quality',
        'passed': substantial_output,
        'detail': f'Output file has substantial size: {substantial_output}'
    })
    
    # Check for digital archaeology thematic connection
    thematic_connection = False
    if philosophy_exists:
        md_text = md_files[0].read_text().lower()
        archaeology_terms = ['digital', 'trace', 'fragment', 'memory', 'ruin', 'ghost', 'archaeology', 'remnant', 'layer']
        thematic_connection = any(term in md_text for term in archaeology_terms)
    
    checks.append({
        'name': 'Thematic relevance',
        'passed': thematic_connection,
        'detail': f'Philosophy connects to digital archaeology concept: {thematic_connection}'
    })
    
    # Calculate overall score
    passed_checks = sum(1 for check in checks if check['passed'])
    score = passed_checks / len(checks)
    overall_passed = score >= 0.8
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_path>')
        sys.exit(1)
    
    result = check_task_completion(sys.argv[1])
    print(json.dumps(result, indent=2))
