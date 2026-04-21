#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

def check_docx_exists(workspace):
    """Check if contract_revised.docx exists"""
    path = Path(workspace) / 'contract_revised.docx'
    return path.exists(), str(path)

def extract_docx_xml(docx_path):
    """Extract document.xml from docx"""
    try:
        with ZipFile(docx_path, 'r') as z:
            return z.read('word/document.xml').decode('utf-8')
    except Exception as e:
        return None

def check_tracked_changes(xml_content):
    """Check for tracked changes (insertions and deletions)"""
    if xml_content is None:
        return False
    xml_lower = xml_content.lower()
    has_ins = '<w:ins' in xml_lower
    has_del = '<w:del' in xml_lower
    return has_ins and has_del

def check_sixty_days_change(xml_content):
    """Check if '60' or 'sixty' appears in tracked changes"""
    if xml_content is None:
        return False
    xml_lower = xml_content.lower()
    # Look for 60 or sixty in the content
    has_sixty = '60' in xml_content or 'sixty' in xml_lower
    # Should also have deletion of 30
    has_thirty_deleted = '<w:deltext>30</w:deltext>' in xml_lower or '<w:deltext>thirty</w:deltext>' in xml_lower
    return has_sixty and has_thirty_deleted

def check_acme_industries_change(xml_content):
    """Check if 'Acme Industries' appears and 'Acme Corp' is tracked as deleted"""
    if xml_content is None:
        return False
    xml_lower = xml_content.lower()
    has_industries = 'acme industries' in xml_lower
    # Check for deletion of 'Acme Corp' or 'Corp'
    has_corp_deleted = '<w:deltext>' in xml_lower and 'corp' in xml_lower
    return has_industries and has_corp_deleted

def check_comment_exists(xml_content):
    """Check if comments exist in the document"""
    if xml_content is None:
        return False
    xml_lower = xml_content.lower()
    # Look for comment markers
    has_comment_range = '<w:commentrangestart' in xml_lower or '<w:commentrangeend' in xml_lower
    has_comment_ref = '<w:commentreference' in xml_lower
    return has_comment_range or has_comment_ref

def check_comments_xml(docx_path):
    """Check if comments.xml exists and has content"""
    try:
        with ZipFile(docx_path, 'r') as z:
            if 'word/comments.xml' in z.namelist():
                comments_xml = z.read('word/comments.xml').decode('utf-8')
                return '<w:comment' in comments_xml.lower()
    except Exception:
        pass
    return False

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    checks = []
    
    # Check 1: File exists
    exists, path = check_docx_exists(workspace)
    checks.append({
        'name': 'Output file exists',
        'passed': exists,
        'detail': f'contract_revised.docx found at {path}' if exists else 'contract_revised.docx not found'
    })
    
    if not exists:
        result = {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
        print(json.dumps(result))
        return
    
    # Extract XML
    xml_content = extract_docx_xml(path)
    
    # Check 2: Tracked changes exist
    has_tracked = check_tracked_changes(xml_content)
    checks.append({
        'name': 'Tracked changes present',
        'passed': has_tracked,
        'detail': 'Document contains insertions and deletions' if has_tracked else 'No tracked changes found'
    })
    
    # Check 3: Days change (30 to 60)
    has_days_change = check_sixty_days_change(xml_content)
    checks.append({
        'name': 'Payment days updated (30 to 60)',
        'passed': has_days_change,
        'detail': 'Found tracked change from 30 to 60 days' if has_days_change else 'Days change not properly tracked'
    })
    
    # Check 4: Company name change
    has_company_change = check_acme_industries_change(xml_content)
    checks.append({
        'name': 'Company name updated (Acme Corp to Acme Industries)',
        'passed': has_company_change,
        'detail': 'Found tracked change to Acme Industries' if has_company_change else 'Company name change not properly tracked'
    })
    
    # Check 5: Comment in document.xml
    has_comment_marker = check_comment_exists(xml_content)
    checks.append({
        'name': 'Comment markers in document',
        'passed': has_comment_marker,
        'detail': 'Comment range markers found' if has_comment_marker else 'No comment markers found'
    })
    
    # Check 6: Comments file exists
    has_comments_file = check_comments_xml(path)
    checks.append({
        'name': 'Comments file exists',
        'passed': has_comments_file,
        'detail': 'comments.xml contains comment data' if has_comments_file else 'No comments.xml or empty'
    })
    
    # Calculate score
    passed_count = sum(1 for c in checks if c['passed'])
    total_count = len(checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    
    result = {
        'passed': score >= 0.8,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()
