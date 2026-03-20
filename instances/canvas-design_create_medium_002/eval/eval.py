#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path
import subprocess

def check_files(workspace_path):
    checks = []
    score = 0.0
    
    workspace = Path(workspace_path)
    
    # Check for design philosophy markdown file
    md_files = list(workspace.glob('*.md'))
    md_exists = len(md_files) > 0
    checks.append({
        'name': 'design_philosophy_file',
        'passed': md_exists,
        'detail': f'Found {len(md_files)} .md files' if md_exists else 'No .md file found'
    })
    if md_exists:
        score += 0.3
    
    # Check markdown content quality
    if md_exists:
        md_content = md_files[0].read_text()
        has_movement_name = len(md_content) > 100 and any(word in md_content.lower() for word in ['movement', 'philosophy', 'visual', 'design'])
        checks.append({
            'name': 'philosophy_content_quality',
            'passed': has_movement_name,
            'detail': f'Philosophy contains {len(md_content)} characters and design terminology' if has_movement_name else 'Philosophy lacks depth or design terminology'
        })
        if has_movement_name:
            score += 0.2
    
    # Check for visual output (PDF or PNG)
    pdf_files = list(workspace.glob('*.pdf'))
    png_files = list(workspace.glob('*.png'))
    visual_exists = len(pdf_files) > 0 or len(png_files) > 0
    
    checks.append({
        'name': 'visual_output_exists',
        'passed': visual_exists,
        'detail': f'Found {len(pdf_files)} PDF and {len(png_files)} PNG files' if visual_exists else 'No visual output files found'
    })
    if visual_exists:
        score += 0.3
    
    # Check file sizes (should be substantial for quality work)
    if visual_exists:
        total_visual_size = sum(f.stat().st_size for f in pdf_files + png_files)
        substantial_size = total_visual_size > 10000  # At least 10KB
        checks.append({
            'name': 'visual_file_size',
            'passed': substantial_size,
            'detail': f'Visual files total {total_visual_size} bytes' if substantial_size else f'Visual files only {total_visual_size} bytes - may be too small for quality artwork'
        })
        if substantial_size:
            score += 0.2
    
    # Verify concept marker was considered (check if original input was processed)
    marker_file = workspace / 'concept_marker.txt'
    marker_processed = marker_file.exists()
    checks.append({
        'name': 'concept_input_processed',
        'passed': marker_processed,
        'detail': 'Original concept marker file preserved' if marker_processed else 'Concept marker file missing - may indicate incomplete processing'
    })
    
    # Bonus: Check if both philosophy and visual are present (complete workflow)
    complete_workflow = md_exists and visual_exists
    if complete_workflow:
        score = min(1.0, score)  # Cap at 1.0
    
    passed = score >= 0.6 and complete_workflow
    
    return {
        'passed': passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'error': 'Usage: eval_script.py <workspace_path>'}))
        sys.exit(1)
    
    result = check_files(sys.argv[1])
    print(json.dumps(result, indent=2))