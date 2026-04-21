import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)
    
    # Check 1: merged_report.pdf exists
    merged_pdf = workspace / 'merged_report.pdf'
    check1 = {
        'name': 'merged_report.pdf exists',
        'passed': merged_pdf.exists(),
        'detail': 'merged_report.pdf file was created' if merged_pdf.exists() else 'merged_report.pdf not found'
    }
    checks.append(check1)
    
    # Check 2: merged PDF is valid and has 3 pages
    check2 = {'name': 'merged PDF has 3 pages', 'passed': False, 'detail': ''}
    if merged_pdf.exists():
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(merged_pdf))
            page_count = len(reader.pages)
            check2['passed'] = page_count == 3
            check2['detail'] = f'Merged PDF has {page_count} pages (expected 3)'
        except Exception as e:
            check2['detail'] = f'Error reading merged PDF: {str(e)}'
    else:
        check2['detail'] = 'Cannot check pages: merged_report.pdf not found'
    checks.append(check2)
    
    # Check 3: extracted_text.txt exists
    extracted_txt = workspace / 'extracted_text.txt'
    check3 = {
        'name': 'extracted_text.txt exists',
        'passed': extracted_txt.exists(),
        'detail': 'extracted_text.txt file was created' if extracted_txt.exists() else 'extracted_text.txt not found'
    }
    checks.append(check3)
    
    # Check 4: extracted text contains marker from first PDF
    check4 = {'name': 'extracted text contains 2023 report marker', 'passed': False, 'detail': ''}
    if extracted_txt.exists():
        try:
            with open(extracted_txt, 'r', encoding='utf-8') as f:
                text = f.read().lower()
            check4['passed'] = 'marker_report_2023' in text
            check4['detail'] = 'Found MARKER_REPORT_2023 in extracted text' if check4['passed'] else 'MARKER_REPORT_2023 not found in extracted text'
        except Exception as e:
            check4['detail'] = f'Error reading extracted text: {str(e)}'
    else:
        check4['detail'] = 'Cannot check: extracted_text.txt not found'
    checks.append(check4)
    
    # Check 5: extracted text contains marker from second PDF
    check5 = {'name': 'extracted text contains 2024 report marker', 'passed': False, 'detail': ''}
    if extracted_txt.exists():
        try:
            with open(extracted_txt, 'r', encoding='utf-8') as f:
                text = f.read().lower()
            check5['passed'] = 'marker_report_2024' in text
            check5['detail'] = 'Found MARKER_REPORT_2024 in extracted text' if check5['passed'] else 'MARKER_REPORT_2024 not found in extracted text'
        except Exception as e:
            check5['detail'] = f'Error reading extracted text: {str(e)}'
    else:
        check5['detail'] = 'Cannot check: extracted_text.txt not found'
    checks.append(check5)
    
    # Check 6: extracted text contains marker from third PDF
    check6 = {'name': 'extracted text contains appendix marker', 'passed': False, 'detail': ''}
    if extracted_txt.exists():
        try:
            with open(extracted_txt, 'r', encoding='utf-8') as f:
                text = f.read().lower()
            check6['passed'] = 'marker_appendix' in text
            check6['detail'] = 'Found MARKER_APPENDIX in extracted text' if check6['passed'] else 'MARKER_APPENDIX not found in extracted text'
        except Exception as e:
            check6['detail'] = f'Error reading extracted text: {str(e)}'
    else:
        check6['detail'] = 'Cannot check: extracted_text.txt not found'
    checks.append(check6)
    
    # Check 7: text order is preserved (2023 before 2024 before appendix)
    check7 = {'name': 'text order preserved in extraction', 'passed': False, 'detail': ''}
    if extracted_txt.exists():
        try:
            with open(extracted_txt, 'r', encoding='utf-8') as f:
                text = f.read().lower()
            pos_2023 = text.find('marker_report_2023')
            pos_2024 = text.find('marker_report_2024')
            pos_appendix = text.find('marker_appendix')
            check7['passed'] = (pos_2023 >= 0 and pos_2024 >= 0 and pos_appendix >= 0 and 
                               pos_2023 < pos_2024 < pos_appendix)
            check7['detail'] = 'Text markers appear in correct order' if check7['passed'] else 'Text markers not in expected order'
        except Exception as e:
            check7['detail'] = f'Error checking order: {str(e)}'
    else:
        check7['detail'] = 'Cannot check: extracted_text.txt not found'
    checks.append(check7)
    
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks)
    overall_passed = score == 1.0
    
    result = {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }
    print(json.dumps(result))

if __name__ == '__main__':
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    evaluate(workspace)