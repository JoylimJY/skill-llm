import json
import os
import sys

def evaluate(workspace_dir):
    checks = []
    
    # Check 1: extracted_text.txt exists
    output_file = os.path.join(workspace_dir, 'extracted_text.txt')
    exists = os.path.isfile(output_file)
    checks.append({
        'name': 'Output file exists',
        'passed': exists,
        'detail': f'File extracted_text.txt found: {exists}'
    })
    
    if not exists:
        result = {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
        print(json.dumps(result))
        return
    
    # Check 2: File is not empty
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    not_empty = len(content.strip()) > 0
    checks.append({
        'name': 'Output file is not empty',
        'passed': not_empty,
        'detail': f'File size: {len(content)} characters'
    })
    
    # Check 3: Contains text from page 1
    has_page1 = 'first page' in content.lower() or 'marker_page_1' in content.lower()
    checks.append({
        'name': 'Contains text from page 1',
        'passed': has_page1,
        'detail': 'Page 1 content found in output'
    })
    
    # Check 4: Contains text from page 2
    has_page2 = 'second page' in content.lower() or 'marker_page_2' in content.lower()
    checks.append({
        'name': 'Contains text from page 2',
        'passed': has_page2,
        'detail': 'Page 2 content found in output'
    })
    
    # Check 5: Contains text from page 3
    has_page3 = 'third' in content.lower() or 'final page' in content.lower() or 'marker_page_3' in content.lower()
    checks.append({
        'name': 'Contains text from page 3',
        'passed': has_page3,
        'detail': 'Page 3 content found in output'
    })
    
    # Check 6: Contains marker indicating page separation or multiple pages
    has_markers = content.lower().count('marker') >= 3 or 'page' in content.lower()
    checks.append({
        'name': 'Evidence of multi-page extraction',
        'passed': has_markers,
        'detail': 'Output shows content from multiple pages'
    })
    
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks)
    
    result = {
        'passed': score >= 0.8,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    evaluate(workspace)