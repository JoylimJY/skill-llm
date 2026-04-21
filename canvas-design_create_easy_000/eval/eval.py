import sys
import os
import json
from pathlib import Path

def main(workspace_dir):
    workspace_path = Path(workspace_dir)
    checks = []
    
    # Check for design philosophy markdown file
    philosophy_found = False
    philosophy_content = ''
    for file in workspace_path.glob('*.md'):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                if any(keyword in content for keyword in ['philosophy', 'design', 'visual', 'aesthetic']):
                    philosophy_found = True
                    philosophy_content = content
                    break
        except:
            continue
    
    checks.append({
        'name': 'Design philosophy file exists',
        'passed': philosophy_found,
        'detail': 'Found design philosophy markdown file' if philosophy_found else 'No design philosophy file found'
    })
    
    # Check philosophy content quality
    philosophy_quality = False
    if philosophy_content:
        quality_keywords = ['form', 'space', 'color', 'composition', 'visual', 'craftsmanship', 'minimal']
        keyword_count = sum(1 for keyword in quality_keywords if keyword in philosophy_content)
        philosophy_quality = keyword_count >= 3 and len(philosophy_content) > 500
    
    checks.append({
        'name': 'Philosophy content is substantial',
        'passed': philosophy_quality,
        'detail': f'Philosophy contains design concepts and is detailed' if philosophy_quality else 'Philosophy needs more design detail'
    })
    
    # Check for PDF output
    pdf_found = False
    pdf_files = list(workspace_path.glob('*.pdf'))
    if pdf_files:
        pdf_found = True
    
    checks.append({
        'name': 'PDF poster file created',
        'passed': pdf_found,
        'detail': f'Found PDF file: {pdf_files[0].name}' if pdf_found else 'No PDF file found'
    })
    
    # Check PDF file size (should be substantial for quality art)
    pdf_size_ok = False
    if pdf_files:
        try:
            file_size = pdf_files[0].stat().st_size
            pdf_size_ok = file_size > 1000  # At least 1KB
        except:
            pass
    
    checks.append({
        'name': 'PDF has substantial content',
        'passed': pdf_size_ok,
        'detail': 'PDF contains visual content' if pdf_size_ok else 'PDF appears empty or corrupted'
    })
    
    # Check for specific filename if requested
    specific_filename = any(f.name.lower() == 'abstract_poster.pdf' for f in pdf_files)
    
    checks.append({
        'name': 'Correct filename used',
        'passed': specific_filename,
        'detail': 'Used requested filename abstract_poster.pdf' if specific_filename else 'Filename does not match request'
    })
    
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8
    
    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main(sys.argv[1])