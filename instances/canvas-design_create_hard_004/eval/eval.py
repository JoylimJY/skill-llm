import sys
import os
import json
from pathlib import Path

def evaluate_canvas_design(workspace_path):
    checks = []
    score = 0.0
    
    workspace = Path(workspace_path)
    
    # Check 1: Verify task marker exists (confirms proper setup)
    marker_file = workspace / 'task_marker.txt'
    marker_check = {
        'name': 'Task Setup Verification',
        'passed': False,
        'detail': 'Task marker file not found'
    }
    
    if marker_file.exists():
        try:
            marker_content = marker_file.read_text().strip()
            if 'CANVAS_DESIGN_TASK_ELECTRONIC_MUSIC_COLLECTIVE_RESONANCE_DRIFT' in marker_content:
                marker_check['passed'] = True
                marker_check['detail'] = 'Task setup verified'
                score += 0.1
            else:
                marker_check['detail'] = 'Invalid marker content'
        except Exception as e:
            marker_check['detail'] = f'Error reading marker: {str(e)}'
    
    checks.append(marker_check)
    
    # Check 2: Design philosophy markdown file exists
    md_files = list(workspace.glob('*.md'))
    philosophy_check = {
        'name': 'Design Philosophy Created',
        'passed': False,
        'detail': 'No markdown file found'
    }
    
    philosophy_content = ''
    if md_files:
        try:
            philosophy_content = md_files[0].read_text()
            if len(philosophy_content) > 500 and ('philosophy' in philosophy_content.lower() or 'visual' in philosophy_content.lower()):
                philosophy_check['passed'] = True
                philosophy_check['detail'] = f'Design philosophy found ({len(philosophy_content)} chars)'
                score += 0.3
            else:
                philosophy_check['detail'] = 'Markdown file too short or missing design content'
        except Exception as e:
            philosophy_check['detail'] = f'Error reading markdown: {str(e)}'
    
    checks.append(philosophy_check)
    
    # Check 3: Visual output file exists (PDF or PNG)
    pdf_files = list(workspace.glob('*.pdf'))
    png_files = list(workspace.glob('*.png'))
    
    visual_check = {
        'name': 'Visual Canvas Created',
        'passed': False,
        'detail': 'No PDF or PNG output found'
    }
    
    output_files = pdf_files + png_files
    if output_files:
        # Check file size (should be substantial for a proper design)
        largest_file = max(output_files, key=lambda f: f.stat().st_size)
        file_size = largest_file.stat().st_size
        
        if file_size > 10000:  # At least 10KB
            visual_check['passed'] = True
            visual_check['detail'] = f'Visual output created: {largest_file.name} ({file_size} bytes)'
            score += 0.4
        else:
            visual_check['detail'] = f'Output file too small: {file_size} bytes'
    
    checks.append(visual_check)
    
    # Check 4: Content sophistication (check philosophy for key terms)
    sophistication_check = {
        'name': 'Sophisticated Design Approach',
        'passed': False,
        'detail': 'Philosophy lacks sophisticated design terminology'
    }
    
    if philosophy_content:
        sophisticated_terms = [
            'composition', 'spatial', 'visual', 'form', 'aesthetic',
            'minimal', 'typography', 'craftsmanship', 'geometric',
            'brutalist', 'organic', 'electronic', 'resonance'
        ]
        
        found_terms = sum(1 for term in sophisticated_terms if term.lower() in philosophy_content.lower())
        
        if found_terms >= 5:
            sophistication_check['passed'] = True
            sophistication_check['detail'] = f'Found {found_terms} sophisticated design terms'
            score += 0.2
        else:
            sophistication_check['detail'] = f'Only found {found_terms} design terms, needs more sophistication'
    
    checks.append(sophistication_check)
    
    # Final score normalization
    final_score = min(1.0, score)
    all_passed = all(check['passed'] for check in checks)
    
    return {
        'passed': all_passed,
        'score': final_score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'error': 'Usage: eval_script.py <workspace_path>'}))
        sys.exit(1)
    
    result = evaluate_canvas_design(sys.argv[1])
    print(json.dumps(result))