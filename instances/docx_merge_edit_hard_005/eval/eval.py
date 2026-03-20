import sys
import os
from pathlib import Path
import zipfile
import subprocess
import json
from xml.etree import ElementTree as ET

def run_check(name, check_func):
    try:
        passed, detail = check_func()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Error: {str(e)}"}

def check_final_document_exists():
    final_doc = Path(workspace_dir) / 'final_report.docx'
    if final_doc.exists():
        return True, "final_report.docx exists"
    return False, "final_report.docx not found"

def check_document_structure():
    final_doc = Path(workspace_dir) / 'final_report.docx'
    if not final_doc.exists():
        return False, "Document does not exist"
    
    # Extract text content using pandoc
    try:
        result = subprocess.run(['pandoc', str(final_doc), '-t', 'plain'], 
                              capture_output=True, text=True, cwd=workspace_dir)
        content = result.stdout
        
        # Check for key structural elements
        has_exec_summary = 'Executive Summary' in content and 'MARKER_EXECUTIVE_SUMMARY_KEY' in content
        has_toc = 'Table of Contents' in content or 'Contents' in content
        has_financial = 'Financial Overview' in content
        has_operations = 'Operations Summary' in content
        has_future = 'Future Outlook' in content
        
        missing = []
        if not has_exec_summary: missing.append('Executive Summary')
        if not has_toc: missing.append('Table of Contents')
        if not has_financial: missing.append('Financial Overview')
        if not has_operations: missing.append('Operations Summary') 
        if not has_future: missing.append('Future Outlook')
        
        if not missing:
            return True, "All required sections present"
        return False, f"Missing sections: {', '.join(missing)}"
        
    except Exception as e:
        return False, f"Could not analyze document structure: {str(e)}"

def check_marker_content_merged():
    final_doc = Path(workspace_dir) / 'final_report.docx'
    if not final_doc.exists():
        return False, "Document does not exist"
    
    try:
        result = subprocess.run(['pandoc', str(final_doc), '-t', 'plain'], 
                              capture_output=True, text=True, cwd=workspace_dir)
        content = result.stdout
        
        # Check for markers from all three source documents
        markers_found = []
        expected_markers = [
            'MARKER_EXECUTIVE_SUMMARY_KEY',
            'MARKER_EXECUTIVE_CONCLUSION', 
            'MARKER_DRAFT_REVENUE_DATA',
            'MARKER_DRAFT_OPERATIONS_TEXT'
        ]
        
        for marker in expected_markers:
            if marker in content:
                markers_found.append(marker)
        
        if len(markers_found) >= 3:
            return True, f"Found {len(markers_found)}/{len(expected_markers)} content markers"
        return False, f"Only found {len(markers_found)}/{len(expected_markers)} content markers: {markers_found}"
        
    except Exception as e:
        return False, f"Could not check marker content: {str(e)}"

def check_legal_review_integration():
    final_doc = Path(workspace_dir) / 'final_report.docx'
    if not final_doc.exists():
        return False, "Document does not exist"
    
    try:
        result = subprocess.run(['pandoc', str(final_doc), '-t', 'plain'], 
                              capture_output=True, text=True, cwd=workspace_dir)
        content = result.stdout
        
        # Look for evidence that legal review content was integrated
        legal_markers = [
            'MARKER_LEGAL_REVENUE_CHANGE',
            'MARKER_LEGAL_OPERATIONS_COMMENT', 
            'MARKER_LEGAL_RISK_ADDITION'
        ]
        
        legal_content_found = 0
        for marker in legal_markers:
            if marker in content:
                legal_content_found += 1
        
        # Also check for legal review related terms
        legal_terms = ['approximately $50 million', 'footnote', 'risk factors', 'compliance']
        legal_terms_found = sum(1 for term in legal_terms if term.lower() in content.lower())
        
        if legal_content_found >= 1 or legal_terms_found >= 2:
            return True, f"Legal review content integrated (markers: {legal_content_found}, terms: {legal_terms_found})"
        return False, f"Legal review content not properly integrated (markers: {legal_content_found}, terms: {legal_terms_found})"
        
    except Exception as e:
        return False, f"Could not check legal review integration: {str(e)}"

def check_signature_block():
    final_doc = Path(workspace_dir) / 'final_report.docx'
    if not final_doc.exists():
        return False, "Document does not exist"
    
    try:
        result = subprocess.run(['pandoc', str(final_doc), '-t', 'plain'], 
                              capture_output=True, text=True, cwd=workspace_dir)
        content = result.stdout
        
        # Look for signature-related content
        signature_indicators = ['signature', 'sign', 'date', '____', '---', 'approved']
        found_indicators = [indicator for indicator in signature_indicators if indicator.lower() in content.lower()]
        
        if len(found_indicators) >= 2:
            return True, f"Signature block elements found: {found_indicators}"
        return False, f"Signature block not found (only found: {found_indicators})"
        
    except Exception as e:
        return False, f"Could not check signature block: {str(e)}"

def check_page_count():
    final_doc = Path(workspace_dir) / 'final_report.docx'
    if not final_doc.exists():
        return False, "Document does not exist"
    
    try:
        # Convert to PDF to count pages
        subprocess.run(['python3', 'scripts/office/soffice.py', '--headless', '--convert-to', 'pdf', str(final_doc)], 
                      capture_output=True, cwd=workspace_dir)
        
        pdf_file = final_doc.with_suffix('.pdf')
        if pdf_file.exists():
            result = subprocess.run(['pdfinfo', str(pdf_file)], capture_output=True, text=True, cwd=workspace_dir)
            if 'Pages:' in result.stdout:
                pages = int(result.stdout.split('Pages:')[1].split()[0])
                if pages >= 4:  # Should have exec summary + TOC + content + signature page
                    return True, f"Document has {pages} pages (appropriate length)"
                return False, f"Document only has {pages} pages (seems too short)"
        
        return False, "Could not determine page count"
        
    except Exception as e:
        return False, f"Could not check page count: {str(e)}"

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python eval_script.py <workspace_dir>')
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    os.chdir(workspace_dir)
    
    checks = [
        ('Final document exists', check_final_document_exists),
        ('Document structure', check_document_structure), 
        ('Source content merged', check_marker_content_merged),
        ('Legal review integrated', check_legal_review_integration),
        ('Signature block present', check_signature_block),
        ('Appropriate page count', check_page_count)
    ]
    
    results = []
    for name, check_func in checks:
        results.append(run_check(name, check_func))
    
    passed_count = sum(1 for r in results if r['passed'])
    score = passed_count / len(results)
    
    output = {
        'passed': score >= 0.7,  # Must pass at least 70% of checks
        'score': score,
        'checks': results
    }
    
    print(json.dumps(output, indent=2))