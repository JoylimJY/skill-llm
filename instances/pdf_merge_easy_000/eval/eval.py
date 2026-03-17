#!/usr/bin/env python3
import sys
import os
import json
from pypdf import PdfReader

def evaluate_task(workspace_dir):
    checks = []
    passed = True
    score = 0.0
    
    merged_file = os.path.join(workspace_dir, 'merged_report.pdf')
    
    # Check if merged file exists
    if os.path.exists(merged_file):
        checks.append({
            'name': 'merged_file_exists',
            'passed': True,
            'detail': 'merged_report.pdf file was created'
        })
        score += 0.3
    else:
        checks.append({
            'name': 'merged_file_exists',
            'passed': False,
            'detail': 'merged_report.pdf file not found'
        })
        passed = False
        return {'passed': passed, 'score': score, 'checks': checks}
    
    try:
        reader = PdfReader(merged_file)
        page_count = len(reader.pages)
        
        # Check page count (should be 3)
        if page_count == 3:
            checks.append({
                'name': 'correct_page_count',
                'passed': True,
                'detail': f'Merged PDF has correct page count: {page_count}'
            })
            score += 0.3
        else:
            checks.append({
                'name': 'correct_page_count',
                'passed': False,
                'detail': f'Expected 3 pages, found {page_count}'
            })
            passed = False
        
        # Extract all text to check content and order
        all_text = ''
        for page in reader.pages:
            all_text += page.extract_text()
        
        # Check for presence of all markers
        markers = ['DOC1_CONTENT_MARKER', 'DOC2_CONTENT_MARKER', 'DOC3_CONTENT_MARKER']
        markers_found = [marker in all_text for marker in markers]
        
        if all(markers_found):
            checks.append({
                'name': 'all_content_present',
                'passed': True,
                'detail': 'All original document content is present'
            })
            score += 0.2
        else:
            missing = [markers[i] for i, found in enumerate(markers_found) if not found]
            checks.append({
                'name': 'all_content_present',
                'passed': False,
                'detail': f'Missing content markers: {missing}'
            })
            passed = False
        
        # Check order of content (DOC1 should appear before DOC2, DOC2 before DOC3)
        doc1_pos = all_text.find('DOC1_CONTENT_MARKER')
        doc2_pos = all_text.find('DOC2_CONTENT_MARKER')
        doc3_pos = all_text.find('DOC3_CONTENT_MARKER')
        
        if doc1_pos < doc2_pos < doc3_pos and doc1_pos >= 0:
            checks.append({
                'name': 'correct_merge_order',
                'passed': True,
                'detail': 'Documents merged in correct order'
            })
            score += 0.2
        else:
            checks.append({
                'name': 'correct_merge_order',
                'passed': False,
                'detail': 'Documents not merged in correct order'
            })
            passed = False
            
    except Exception as e:
        checks.append({
            'name': 'pdf_readable',
            'passed': False,
            'detail': f'Error reading merged PDF: {str(e)}'
        })
        passed = False
    
    return {'passed': passed, 'score': score, 'checks': checks}

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'usage', 'passed': False, 'detail': 'Usage: eval_script.py <workspace_dir>'}]}))
        sys.exit(1)
    
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result))