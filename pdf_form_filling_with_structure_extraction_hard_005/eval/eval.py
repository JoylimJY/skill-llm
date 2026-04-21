#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)
    
    # Check 1: form_structure.json exists
    structure_file = workspace / 'form_structure.json'
    check1 = {'name': 'form_structure.json exists', 'passed': False, 'detail': ''}
    if structure_file.exists():
        try:
            with open(structure_file, 'r') as f:
                structure = json.load(f)
            check1['passed'] = True
            check1['detail'] = f'File exists with {len(structure.get("labels", []))} labels'
        except Exception as e:
            check1['detail'] = f'File exists but invalid JSON: {str(e)}'
    else:
        check1['detail'] = 'File not found'
    checks.append(check1)
    
    # Check 2: fields.json exists and is valid
    fields_file = workspace / 'fields.json'
    check2 = {'name': 'fields.json exists and valid', 'passed': False, 'detail': ''}
    if fields_file.exists():
        try:
            with open(fields_file, 'r') as f:
                fields = json.load(f)
            form_fields = fields.get('form_fields', [])
            if len(form_fields) >= 5:
                check2['passed'] = True
                check2['detail'] = f'File valid with {len(form_fields)} form fields'
            else:
                check2['detail'] = f'Only {len(form_fields)} fields found, expected at least 5'
        except Exception as e:
            check2['detail'] = f'Invalid JSON: {str(e)}'
    else:
        check2['detail'] = 'File not found'
    checks.append(check2)
    
    # Check 3: fields.json has required field types
    check3 = {'name': 'fields.json contains all required field types', 'passed': False, 'detail': ''}
    required_fields = {'last name', 'first name', 'age', 'us citizen', 'employment'}
    found_fields = set()
    if fields_file.exists():
        try:
            with open(fields_file, 'r') as f:
                fields = json.load(f)
            for field in fields.get('form_fields', []):
                label = field.get('field_label', '').lower()
                for req in required_fields:
                    if req in label:
                        found_fields.add(req)
            if len(found_fields) >= 4:
                check3['passed'] = True
                check3['detail'] = f'Found {len(found_fields)} required field types: {found_fields}'
            else:
                check3['detail'] = f'Missing fields. Found: {found_fields}'
        except Exception as e:
            check3['detail'] = f'Error reading fields: {str(e)}'
    else:
        check3['detail'] = 'fields.json not found'
    checks.append(check3)
    
    # Check 4: filled_form.pdf exists
    output_file = workspace / 'filled_form.pdf'
    check4 = {'name': 'filled_form.pdf exists', 'passed': False, 'detail': ''}
    if output_file.exists():
        file_size = output_file.stat().st_size
        if file_size > 1000:
            check4['passed'] = True
            check4['detail'] = f'File exists with size {file_size} bytes'
        else:
            check4['detail'] = f'File too small: {file_size} bytes'
    else:
        check4['detail'] = 'File not found'
    checks.append(check4)
    
    # Check 5: filled_form.pdf is valid PDF
    check5 = {'name': 'filled_form.pdf is valid PDF', 'passed': False, 'detail': ''}
    if output_file.exists():
        try:
            from pypdf import PdfReader
            reader = PdfReader(output_file)
            num_pages = len(reader.pages)
            if num_pages > 0:
                check5['passed'] = True
                check5['detail'] = f'Valid PDF with {num_pages} page(s)'
            else:
                check5['detail'] = 'PDF has no pages'
        except Exception as e:
            check5['detail'] = f'Invalid PDF: {str(e)}'
    else:
        check5['detail'] = 'File not found'
    checks.append(check5)
    
    # Check 6: filled_form.pdf contains text annotations
    check6 = {'name': 'filled_form.pdf contains text content', 'passed': False, 'detail': ''}
    if output_file.exists():
        try:
            from pypdf import PdfReader
            reader = PdfReader(output_file)
            page = reader.pages[0]
            text = page.extract_text() or ''
            if any(keyword in text.lower() for keyword in ['smith', 'john', 'employed', 'student', 'unemployed', '25', '30']):
                check6['passed'] = True
                check6['detail'] = 'Text content found in PDF'
            else:
                check6['detail'] = 'No expected text found in PDF'
        except Exception as e:
            check6['detail'] = f'Error reading PDF: {str(e)}'
    else:
        check6['detail'] = 'File not found'
    checks.append(check6)
    
    # Calculate score
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks)
    overall_passed = score >= 0.8
    
    result = {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    evaluate(sys.argv[1])
