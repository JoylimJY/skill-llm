#!/usr/bin/env python3
import sys
import os
import json
import glob
import re
from pathlib import Path

def evaluate_canvas_task(workspace_dir):
    checks = []
    
    # Check 1: Philosophy markdown file exists
    philosophy_files = glob.glob(os.path.join(workspace_dir, '*philosophy*.md')) + glob.glob(os.path.join(workspace_dir, '*.md'))
    philosophy_found = False
    philosophy_content = ''
    
    for file_path in philosophy_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if len(content) > 200:  # Substantial content
                    philosophy_found = True
                    philosophy_content = content.lower()
                    break
        except:
            continue
    
    checks.append({
        'name': 'Philosophy markdown file created',
        'passed': philosophy_found,
        'detail': f'Found philosophy file: {philosophy_found}'
    })
    
    # Check 2: Philosophy contains design movement concepts
    design_concepts = False
    if philosophy_content:
        design_keywords = ['visual', 'form', 'space', 'color', 'composition', 'aesthetic', 'design', 'movement', 'philosophy']
        found_keywords = sum(1 for keyword in design_keywords if keyword in philosophy_content)
        design_concepts = found_keywords >= 4
    
    checks.append({
        'name': 'Philosophy contains design concepts',
        'passed': design_concepts,
        'detail': f'Contains sufficient design vocabulary: {design_concepts}'
    })
    
    # Check 3: Philosophy emphasizes craftsmanship
    craftsmanship_emphasis = False
    if philosophy_content:
        craft_keywords = ['craft', 'meticulous', 'expert', 'master', 'precision', 'careful', 'labored', 'hours']
        found_craft = any(keyword in philosophy_content for keyword in craft_keywords)
        craftsmanship_emphasis = found_craft
    
    checks.append({
        'name': 'Philosophy emphasizes craftsmanship',
        'passed': craftsmanship_emphasis,
        'detail': f'Contains craftsmanship emphasis: {craftsmanship_emphasis}'
    })
    
    # Check 4: Temporal layers PDF file exists with correct name
    pdf_files = glob.glob(os.path.join(workspace_dir, 'temporal_layers.pdf'))
    correct_pdf_found = len(pdf_files) > 0
    
    checks.append({
        'name': 'Temporal layers PDF created with correct filename',
        'passed': correct_pdf_found,
        'detail': f'Found temporal_layers.pdf: {correct_pdf_found}'
    })
    
    # Check 5: PDF file has reasonable size (indicating substantial content)
    pdf_has_content = False
    if pdf_files:
        try:
            file_size = os.path.getsize(pdf_files[0])
            pdf_has_content = file_size > 1000  # At least 1KB
        except:
            pass
    
    checks.append({
        'name': 'PDF contains substantial content',
        'passed': pdf_has_content,
        'detail': f'PDF has reasonable file size: {pdf_has_content}'
    })
    
    # Check 6: Alternative PDF file exists (if temporal_layers.pdf not found)
    alternative_pdf_found = False
    if not correct_pdf_found:
        all_pdfs = glob.glob(os.path.join(workspace_dir, '*.pdf'))
        for pdf_file in all_pdfs:
            try:
                file_size = os.path.getsize(pdf_file)
                if file_size > 1000:
                    alternative_pdf_found = True
                    break
            except:
                continue
    
    checks.append({
        'name': 'Alternative PDF artwork exists',
        'passed': alternative_pdf_found or correct_pdf_found,
        'detail': f'Found valid PDF artwork: {alternative_pdf_found or correct_pdf_found}'
    })
    
    # Check 7: Philosophy has appropriate length (4-6 paragraphs worth)
    appropriate_length = False
    if philosophy_content:
        # Rough estimation: 4-6 paragraphs should be 800-2000 characters
        content_length = len(philosophy_content)
        appropriate_length = 500 <= content_length <= 3000
    
    checks.append({
        'name': 'Philosophy has appropriate length',
        'passed': appropriate_length,
        'detail': f'Philosophy length is appropriate: {appropriate_length}'
    })
    
    # Check 8: Both required files exist
    both_files_exist = philosophy_found and (correct_pdf_found or alternative_pdf_found)
    
    checks.append({
        'name': 'Both philosophy and artwork files created',
        'passed': both_files_exist,
        'detail': f'Created both required deliverables: {both_files_exist}'
    })
    
    # Calculate score
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.8
    
    return {
        'passed': passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_dir>')
        sys.exit(1)
    
    result = evaluate_canvas_task(sys.argv[1])
    print(json.dumps(result))