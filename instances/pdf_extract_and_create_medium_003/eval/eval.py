import sys
import os
import pdfplumber
from pypdf import PdfReader
import json

def check_task_completion(workspace_dir):
    checks = []
    score = 0.0
    
    # Check if summary_report.pdf exists
    summary_file = os.path.join(workspace_dir, 'summary_report.pdf')
    if not os.path.exists(summary_file):
        checks.append({
            'name': 'Output file exists',
            'passed': False,
            'detail': 'summary_report.pdf not found'
        })
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    checks.append({
        'name': 'Output file exists',
        'passed': True,
        'detail': 'summary_report.pdf found'
    })
    score += 0.2
    
    try:
        # Read the generated PDF
        reader = PdfReader(summary_file)
        page_count = len(reader.pages)
        
        # Check page count
        if page_count >= 1:
            checks.append({
                'name': 'Valid PDF structure',
                'passed': True,
                'detail': f'PDF has {page_count} page(s)'
            })
            score += 0.2
        else:
            checks.append({
                'name': 'Valid PDF structure',
                'passed': False,
                'detail': 'PDF has no pages'
            })
            return {'passed': False, 'score': score, 'checks': checks}
        
        # Extract text to check for title
        with pdfplumber.open(summary_file) as pdf:
            full_text = ''
            tables_found = []
            
            for page in pdf.pages:
                page_text = page.extract_text() or ''
                full_text += page_text
                
                # Extract tables
                page_tables = page.extract_tables()
                tables_found.extend(page_tables)
        
        # Check for required title
        if 'Financial Summary Report' in full_text:
            checks.append({
                'name': 'Title present',
                'passed': True,
                'detail': 'Found required title "Financial Summary Report"'
            })
            score += 0.2
        else:
            checks.append({
                'name': 'Title present',
                'passed': False,
                'detail': 'Title "Financial Summary Report" not found in PDF'
            })
        
        # Check for table data
        if len(tables_found) > 0:
            checks.append({
                'name': 'Tables extracted',
                'passed': True,
                'detail': f'Found {len(tables_found)} table(s) in output PDF'
            })
            score += 0.2
            
            # Check for financial data markers
            marker_12345_found = False
            marker_6789_found = False
            
            for table in tables_found:
                table_text = str(table)
                if '12345' in table_text or '1,012,345' in table_text or '1012345' in table_text:
                    marker_12345_found = True
                if '6789' in table_text or '706,789' in table_text or '706789' in table_text:
                    marker_6789_found = True
            
            # Also check in full text for markers
            if '12345' in full_text.replace(',', '').replace('$', '') or marker_12345_found:
                marker_12345_found = True
            if '6789' in full_text.replace(',', '').replace('$', '') or marker_6789_found:
                marker_6789_found = True
            
            if marker_12345_found and marker_6789_found:
                checks.append({
                    'name': 'Financial data preserved',
                    'passed': True,
                    'detail': 'Original financial data markers found in output'
                })
                score += 0.2
            else:
                checks.append({
                    'name': 'Financial data preserved',
                    'passed': False,
                    'detail': f'Financial data markers missing (12345: {marker_12345_found}, 6789: {marker_6789_found})'
                })
        else:
            checks.append({
                'name': 'Tables extracted',
                'passed': False,
                'detail': 'No tables found in output PDF'
            })
        
    except Exception as e:
        checks.append({
            'name': 'PDF processing',
            'passed': False,
            'detail': f'Error processing PDF: {str(e)}'
        })
        return {'passed': False, 'score': score, 'checks': checks}
    
    passed = score >= 0.8  # Need at least 80% to pass
    return {'passed': passed, 'score': score, 'checks': checks}

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_dir>')
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = check_task_completion(workspace_dir)
    print(json.dumps(result))