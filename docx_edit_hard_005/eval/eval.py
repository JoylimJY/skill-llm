#!/usr/bin/env python3
import sys
import os
import json
import subprocess
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

def run_eval(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)
    
    # Check 1: final_report.docx exists
    final_docx = workspace / 'final_report.docx'
    docx_exists = final_docx.exists()
    checks.append({
        'name': 'final_report.docx_exists',
        'passed': docx_exists,
        'detail': f'File exists: {docx_exists}'
    })
    
    # Check 2: final_report.pdf exists
    final_pdf = workspace / 'final_report.pdf'
    pdf_exists = final_pdf.exists()
    checks.append({
        'name': 'final_report.pdf_exists', 
        'passed': pdf_exists,
        'detail': f'PDF file exists: {pdf_exists}'
    })
    
    # Check 3: Executive Summary heading added
    exec_summary_found = False
    if docx_exists:
        try:
            # Extract text using pandoc
            result = subprocess.run(['pandoc', str(final_docx), '-t', 'plain'], 
                                  capture_output=True, text=True, cwd=workspace_dir)
            if result.returncode == 0:
                content = result.stdout.lower()
                exec_summary_found = 'executive summary' in content
        except Exception as e:
            exec_summary_found = False
    
    checks.append({
        'name': 'executive_summary_heading',
        'passed': exec_summary_found,
        'detail': f'Executive Summary heading found: {exec_summary_found}'
    })
    
    # Check 4: Comment added (check XML for comment structure)
    comment_found = False
    if docx_exists:
        try:
            with zipfile.ZipFile(final_docx, 'r') as docx_zip:
                # Check if comments.xml exists
                if 'word/comments.xml' in docx_zip.namelist():
                    comments_xml = docx_zip.read('word/comments.xml').decode('utf-8')
                    comment_found = 'updated per management feedback' in comments_xml.lower() or 'management feedback' in comments_xml.lower()
        except Exception:
            comment_found = False
    
    checks.append({
        'name': 'comment_added',
        'passed': comment_found,
        'detail': f'Management feedback comment found: {comment_found}'
    })
    
    # Check 5: Document contains original content
    content_preserved = False
    if docx_exists:
        try:
            result = subprocess.run(['pandoc', str(final_docx), '-t', 'plain'], 
                                  capture_output=True, text=True, cwd=workspace_dir)
            if result.returncode == 0:
                content = result.stdout.lower()
                # Check for key content from original document
                has_sales_report = 'sales report' in content or 'q4 2024' in content
                has_revenue = 'revenue' in content or '2.3m' in content
                has_achievements = 'achievements' in content or 'growth' in content
                content_preserved = has_sales_report and (has_revenue or has_achievements)
        except Exception:
            content_preserved = False
    
    checks.append({
        'name': 'content_preserved',
        'passed': content_preserved,
        'detail': f'Original content preserved: {content_preserved}'
    })
    
    # Check 6: PDF is valid and contains content
    pdf_valid = False
    if pdf_exists:
        try:
            # Try to extract text from PDF to verify it's valid
            result = subprocess.run(['pdftotext', str(final_pdf), '-'], 
                                  capture_output=True, text=True, cwd=workspace_dir)
            if result.returncode == 0:
                pdf_content = result.stdout.lower()
                # Check that PDF contains some expected content
                pdf_valid = ('sales' in pdf_content or 'report' in pdf_content or 
                           'executive' in pdf_content or 'summary' in pdf_content)
        except Exception:
            pdf_valid = False
    
    checks.append({
        'name': 'pdf_valid_content',
        'passed': pdf_valid,
        'detail': f'PDF contains valid content: {pdf_valid}'
    })
    
    # Calculate final score
    passed_count = sum(1 for check in checks if check['passed'])
    total_count = len(checks)
    score = passed_count / total_count
    overall_passed = score >= 0.8  # Allow some tolerance for complex multi-step task
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_dir>')
        sys.exit(1)
    
    result = run_eval(sys.argv[1])
    print(json.dumps(result))