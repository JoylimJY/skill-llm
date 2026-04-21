#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)
    
    # Check 1: form_structure.json exists and is valid JSON
    structure_file = workspace / 'form_structure.json'
    check1_passed = False
    check1_detail = ''
    if structure_file.exists():
        try:
            with open(structure_file) as f:
                structure = json.load(f)
            check1_passed = isinstance(structure, dict)
            check1_detail = 'form_structure.json is valid JSON' if check1_passed else 'Invalid JSON structure'
        except Exception as e:
            check1_detail = f'Failed to parse form_structure.json: {e}'
    else:
        check1_detail = 'form_structure.json not found'
    checks.append({'name': 'form_structure.json exists and valid', 'passed': check1_passed, 'detail': check1_detail})
    
    # Check 2: fields.json exists and is valid JSON
    fields_file = workspace / 'fields.json'
    check2_passed = False
    check2_detail = ''
    fields_data = None
    if fields_file.exists():
        try:
            with open(fields_file) as f:
                fields_data = json.load(f)
            check2_passed = isinstance(fields_data, dict)
            check2_detail = 'fields.json is valid JSON' if check2_passed else 'Invalid JSON structure'
        except Exception as e:
            check2_detail = f'Failed to parse fields.json: {e}'
    else:
        check2_detail = 'fields.json not found'
    checks.append({'name': 'fields.json exists and valid', 'passed': check2_passed, 'detail': check2_detail})
    
    # Check 3: fields.json contains required fields
    check3_passed = False
    check3_detail = ''
    if fields_data:
        form_fields = fields_data.get('form_fields', [])
        required_labels = {'last name', 'first name', 'age', 'us citizen', 'employment'}
        found_labels = set()
        for field in form_fields:
            label = field.get('field_label', '').lower()
            for req in required_labels:
                if req in label:
                    found_labels.add(req)
        check3_passed = len(found_labels) >= 4
        check3_detail = f'Found {len(found_labels)}/5 required field types'
    else:
        check3_detail = 'fields.json not loaded'
    checks.append({'name': 'fields.json contains required fields', 'passed': check3_passed, 'detail': check3_detail})
    
    # Check 4: filled_form.pdf exists
    filled_pdf = workspace / 'filled_form.pdf'
    check4_passed = filled_pdf.exists()
    check4_detail = 'filled_form.pdf exists' if check4_passed else 'filled_form.pdf not found'
    checks.append({'name': 'filled_form.pdf exists', 'passed': check4_passed, 'detail': check4_detail})
    
    # Check 5: filled_form.pdf is valid PDF
    check5_passed = False
    check5_detail = ''
    if check4_passed:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(filled_pdf))
            check5_passed = len(reader.pages) > 0
            check5_detail = f'PDF has {len(reader.pages)} page(s)'
        except Exception as e:
            check5_detail = f'Failed to read PDF: {e}'
    else:
        check5_detail = 'PDF file not found'
    checks.append({'name': 'filled_form.pdf is valid PDF', 'passed': check5_passed, 'detail': check5_detail})
    
    # Check 6: filled_form.pdf contains text annotations
    check6_passed = False
    check6_detail = ''
    if check5_passed:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(filled_pdf))
            page = reader.pages[0]
            text = page.extract_text()
            has_text = text and len(text.strip()) > 0
            check6_passed = has_text
            check6_detail = 'Text annotations found in PDF' if has_text else 'No text found in PDF'
        except Exception as e:
            check6_detail = f'Failed to extract text: {e}'
    else:
        check6_detail = 'PDF not valid'
    checks.append({'name': 'filled_form.pdf contains text', 'passed': check6_passed, 'detail': check6_detail})
    
    # Check 7: Verify sample data was filled (check for expected values)
    check7_passed = False
    check7_detail = ''
    if check6_passed:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(filled_pdf))
            page = reader.pages[0]
            text = page.extract_text().lower()
            # Check for any indication of filled data
            has_filled_data = any(keyword in text for keyword in ['smith', 'john', '30', 'employed', 'x'])
            check7_passed = has_filled_data
            check7_detail = 'Sample data appears to be filled' if has_filled_data else 'No sample data found'
        except Exception as e:
            check7_detail = f'Failed to verify data: {e}'
    else:
        check7_detail = 'Cannot verify without valid PDF'
    checks.append({'name': 'Sample data filled in form', 'passed': check7_passed, 'detail': check7_detail})
    
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8
    
    return {
        'passed': passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '/workspace'
    result = evaluate(workspace)
    print(json.dumps(result))
