#!/usr/bin/env python3
import sys
import os
import json
from pypdf import PdfReader
import pandas as pd
from datetime import datetime

def evaluate_task(workspace_dir):
    checks = []
    overall_passed = True
    score = 0.0
    
    os.chdir(workspace_dir)
    
    # Check if final output exists
    expected_files = ['filled_form.pdf', 'merged_final.pdf', 'protected_final.pdf']
    output_file = None
    
    for filename in expected_files:
        if os.path.exists(filename):
            output_file = filename
            break
    
    if not output_file:
        # Look for any PDF that might be the final output
        pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf') and f not in ['form_template.pdf', 'doc1.pdf', 'doc2.pdf']]
        if pdf_files:
            output_file = pdf_files[0]  # Take the first one
    
    if not output_file:
        checks.append({'name': 'output_file_exists', 'passed': False, 'detail': 'No output PDF file found'})
        overall_passed = False
        return {'passed': overall_passed, 'score': score, 'checks': checks}
    
    checks.append({'name': 'output_file_exists', 'passed': True, 'detail': f'Found output file: {output_file}'})
    score += 0.2
    
    try:
        # Try to read the PDF
        reader = PdfReader(output_file)
        
        # Check if it's password protected (bonus points)
        is_encrypted = reader.is_encrypted
        if is_encrypted:
            checks.append({'name': 'password_protection', 'passed': True, 'detail': 'PDF is password protected'})
            score += 0.1
            # Try common passwords to decrypt for further testing
            passwords = ['password', '123456', 'admin', output_file.replace('.pdf', ''), 'filled']
            decrypted = False
            for pwd in passwords:
                try:
                    if reader.decrypt(pwd):
                        decrypted = True
                        break
                except:
                    continue
            
            if not decrypted:
                checks.append({'name': 'pdf_readable', 'passed': False, 'detail': 'Cannot decrypt PDF with common passwords'})
                # Still award partial credit for encryption
                return {'passed': False, 'score': score, 'checks': checks}
        else:
            checks.append({'name': 'password_protection', 'passed': False, 'detail': 'PDF is not password protected'})
        
        # Check page count (should be at least 4: 2 from form + 1 from doc1 + 1 from doc2)
        page_count = len(reader.pages)
        if page_count >= 4:
            checks.append({'name': 'page_count', 'passed': True, 'detail': f'PDF has {page_count} pages (expected >= 4)'})
            score += 0.2
        else:
            checks.append({'name': 'page_count', 'passed': False, 'detail': f'PDF has only {page_count} pages (expected >= 4)'})
            overall_passed = False
        
        # Extract text and check for filled data
        full_text = ''
        for page in reader.pages:
            try:
                full_text += page.extract_text()
            except:
                continue
        
        # Check if applicant data was filled in
        if 'applicant_data.csv' in os.listdir('.'):
            df = pd.read_csv('applicant_data.csv')
            applicant = df.iloc[0]
            
            filled_fields = 0
            total_fields = 0
            
            # Check for key data fields
            for field, value in applicant.items():
                total_fields += 1
                if str(value).upper() in full_text.upper():
                    filled_fields += 1
            
            fill_rate = filled_fields / total_fields if total_fields > 0 else 0
            if fill_rate >= 0.5:  # At least half the fields should be found
                checks.append({'name': 'data_filled', 'passed': True, 'detail': f'Found {filled_fields}/{total_fields} data fields in PDF'})
                score += 0.2
            else:
                checks.append({'name': 'data_filled', 'passed': False, 'detail': f'Only found {filled_fields}/{total_fields} data fields in PDF'})
                overall_passed = False
        
        # Check for markers from supporting documents
        doc_markers = ['MARKER_DOC1', 'MARKER_DOC2', 'SUP-001-2024', 'SUP-002-2024']
        found_markers = 0
        for marker in doc_markers:
            if marker in full_text:
                found_markers += 1
        
        if found_markers >= 2:  # Should find markers from both docs
            checks.append({'name': 'supporting_docs_merged', 'passed': True, 'detail': f'Found {found_markers}/4 supporting document markers'})
            score += 0.15
        else:
            checks.append({'name': 'supporting_docs_merged', 'passed': False, 'detail': f'Only found {found_markers}/4 supporting document markers'})
            overall_passed = False
        
        # Check for original form markers
        form_markers = ['MARKER_FORM_TITLE', 'MARKER_SECTION_B', 'MARKER_PAGE2']
        found_form_markers = 0
        for marker in form_markers:
            if marker in full_text:
                found_form_markers += 1
        
        if found_form_markers >= 2:
            checks.append({'name': 'original_form_preserved', 'passed': True, 'detail': f'Found {found_form_markers}/3 original form markers'})
            score += 0.1
        else:
            checks.append({'name': 'original_form_preserved', 'passed': False, 'detail': f'Only found {found_form_markers}/3 original form markers'})
        
        # Check for watermark or date (bonus)
        current_year = str(datetime.now().year)
        if current_year in full_text or 'watermark' in full_text.lower():
            checks.append({'name': 'watermark_date', 'passed': True, 'detail': 'Found date/watermark in PDF'})
            score += 0.05
        else:
            checks.append({'name': 'watermark_date', 'passed': False, 'detail': 'No date/watermark found'})
        
    except Exception as e:
        checks.append({'name': 'pdf_processing', 'passed': False, 'detail': f'Error processing PDF: {str(e)}'})
        overall_passed = False
    
    # Final score adjustment
    if overall_passed and score >= 0.8:
        score = min(1.0, score)
    elif overall_passed:
        score = max(0.6, score)  # Minimum score for passing
    else:
        score = min(0.5, score)  # Cap score for failing
    
    return {
        'passed': overall_passed,
        'score': round(score, 2),
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_dir>')
        sys.exit(1)
    
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result))