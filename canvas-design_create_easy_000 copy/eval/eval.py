import os
import sys
import json
from pathlib import Path

def main(workspace_path):
    workspace = Path(workspace_path)
    checks = []
    
    # Check for design philosophy markdown file
    md_files = list(workspace.glob('*.md'))
    philosophy_found = False
    philosophy_content = ''
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            if any(keyword in content.lower() for keyword in ['philosophy', 'design', 'visual', 'aesthetic']):
                philosophy_found = True
                philosophy_content = content
                break
        except:
            continue
    
    checks.append({
        'name': 'design_philosophy_exists',
        'passed': philosophy_found,
        'detail': f'Found design philosophy document: {philosophy_found}'
    })
    
    # Check philosophy content quality
    philosophy_quality = False
    if philosophy_found and philosophy_content:
        quality_keywords = ['visual', 'space', 'form', 'color', 'composition', 'minimal', 'craftsmanship']
        found_keywords = sum(1 for keyword in quality_keywords if keyword in philosophy_content.lower())
        philosophy_quality = found_keywords >= 3 and len(philosophy_content.strip()) > 200
    
    checks.append({
        'name': 'philosophy_quality',
        'passed': philosophy_quality,
        'detail': f'Philosophy contains design concepts and sufficient detail: {philosophy_quality}'
    })
    
    # Check for poster image file
    image_files = list(workspace.glob('*.png')) + list(workspace.glob('*.pdf'))
    poster_found = False
    
    for img_file in image_files:
        if any(keyword in img_file.name.lower() for keyword in ['meditation', 'poster', 'breathe']):
            poster_found = True
            break
    
    if not poster_found and image_files:
        poster_found = True  # Accept any image file as the poster
    
    checks.append({
        'name': 'poster_file_exists',
        'passed': poster_found,
        'detail': f'Found poster image file: {poster_found}'
    })
    
    # Check file format
    correct_format = False
    if image_files:
        for img_file in image_files:
            if img_file.suffix.lower() in ['.png', '.pdf']:
                correct_format = True
                break
    
    checks.append({
        'name': 'correct_format',
        'passed': correct_format,
        'detail': f'Output in PNG or PDF format: {correct_format}'
    })
    
    # Calculate score
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.75  # Allow for some flexibility in creative tasks
    
    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python eval_script.py <workspace_path>')
        sys.exit(1)
    main(sys.argv[1])