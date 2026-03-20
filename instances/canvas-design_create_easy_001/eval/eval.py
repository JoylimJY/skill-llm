#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path

def evaluate_task(workspace_dir):
    workspace_path = Path(workspace_dir)
    checks = []
    score = 0.0
    
    # Check for design philosophy markdown file
    md_files = list(workspace_path.glob('*.md'))
    md_check = len(md_files) > 0
    checks.append({
        'name': 'design_philosophy_created',
        'passed': md_check,
        'detail': f'Found {len(md_files)} .md file(s)' if md_check else 'No .md file found'
    })
    if md_check:
        score += 0.3
        
        # Check md content quality
        md_content = md_files[0].read_text()
        has_philosophy = len(md_content) > 500 and ('philosophy' in md_content.lower() or 'movement' in md_content.lower())
        checks.append({
            'name': 'philosophy_content_substantial',
            'passed': has_philosophy,
            'detail': f'Philosophy content length: {len(md_content)} chars' if has_philosophy else 'Philosophy content too brief or missing key terms'
        })
        if has_philosophy:
            score += 0.2
    
    # Check for visual output (PDF or PNG)
    pdf_files = list(workspace_path.glob('*.pdf'))
    png_files = list(workspace_path.glob('*.png'))
    visual_files = pdf_files + png_files
    
    visual_check = len(visual_files) > 0
    checks.append({
        'name': 'visual_output_created',
        'passed': visual_check,
        'detail': f'Found {len(pdf_files)} PDF(s) and {len(png_files)} PNG(s)' if visual_check else 'No visual output files found'
    })
    if visual_check:
        score += 0.3
        
        # Check file size (should be substantial for quality artwork)
        largest_file = max(visual_files, key=lambda f: f.stat().st_size)
        file_size = largest_file.stat().st_size
        size_check = file_size > 10000  # At least 10KB for a meaningful design
        checks.append({
            'name': 'visual_output_substantial',
            'passed': size_check,
            'detail': f'Largest visual file: {file_size} bytes' if size_check else f'Visual file too small: {file_size} bytes'
        })
        if size_check:
            score += 0.2
    
    # Bonus: Check if both philosophy and visual are present (complete workflow)
    complete_workflow = md_check and visual_check
    if complete_workflow:
        score = min(1.0, score + 0.1)  # Bonus for complete workflow
    
    passed = score >= 0.6  # Need at least basic philosophy + visual output
    
    return {
        'passed': passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_directory>')
        sys.exit(1)
    
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result, indent=2))