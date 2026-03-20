#!/usr/bin/env python3

import sys
import os
import json
import zipfile
import xml.etree.ElementTree as ET
from xml.dom import minidom
import subprocess
import tempfile

def check_file_exists(workspace_path):
    """Check if proposal.docx exists"""
    filepath = os.path.join(workspace_path, 'proposal.docx')
    return os.path.exists(filepath), filepath

def extract_text_content(docx_path):
    """Extract text content from docx using pandoc"""
    try:
        result = subprocess.run(
            ['pandoc', '--to', 'plain', docx_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error extracting text: {e}"

def check_docx_structure(docx_path):
    """Check internal DOCX structure for headings, TOC, and tables"""
    try:
        with zipfile.ZipFile(docx_path, 'r') as zf:
            doc_xml = zf.read('word/document.xml')
            
        # Parse XML
        root = ET.fromstring(doc_xml)
        
        # Define namespaces
        ns = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }
        
        # Check for table of contents
        toc_elements = root.findall('.//w:fldChar[@w:fldCharType="begin"]/../w:instrText', ns)
        has_toc = any('TOC' in elem.text for elem in toc_elements if elem.text)
        
        # Check for headings (paragraphs with heading styles)
        heading_elements = root.findall('.//w:pStyle', ns)
        heading_count = sum(1 for elem in heading_elements if elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '').startswith('Heading'))
        
        # Check for tables
        table_elements = root.findall('.//w:tbl', ns)
        has_table = len(table_elements) > 0
        
        return {
            'has_toc': has_toc,
            'heading_count': heading_count,
            'has_table': has_table,
            'table_count': len(table_elements)
        }
        
    except Exception as e:
        return {'error': str(e)}

def evaluate_task(workspace_path):
    """Main evaluation function"""
    checks = []
    total_score = 0
    max_score = 100
    
    # Load expected content
    expected_file = os.path.join(workspace_path, 'expected_content.json')
    if os.path.exists(expected_file):
        with open(expected_file, 'r') as f:
            expected = json.load(f)
    else:
        expected = {
            "title": "Smart City Initiative Proposal",
            "subtitle": "Transforming Urban Infrastructure Through Technology",
            "sections": ["Executive Summary", "Project Overview", "Technical Implementation", "Budget Analysis"],
            "conclusion": "Conclusion"
        }
    
    # Check 1: File exists (20 points)
    file_exists, filepath = check_file_exists(workspace_path)
    if file_exists:
        checks.append({"name": "File exists", "passed": True, "detail": "proposal.docx found"})
        total_score += 20
    else:
        checks.append({"name": "File exists", "passed": False, "detail": "proposal.docx not found"})
        return {"passed": False, "score": 0, "checks": checks}
    
    # Check 2: Valid DOCX format (10 points)
    try:
        with zipfile.ZipFile(filepath, 'r') as zf:
            zf.testzip()
        checks.append({"name": "Valid DOCX format", "passed": True, "detail": "File is a valid ZIP/DOCX"})
        total_score += 10
    except Exception as e:
        checks.append({"name": "Valid DOCX format", "passed": False, "detail": f"Invalid DOCX: {e}"})
    
    # Check 3: Extract and verify content (40 points total)
    text_content = extract_text_content(filepath)
    if "Error extracting" not in text_content:
        content_checks = [
            (expected['title'], 10, "Title present"),
            (expected['subtitle'], 10, "Subtitle present"),
            ("Executive Summary", 5, "Executive Summary section"),
            ("Project Overview", 5, "Project Overview section"),
            ("Technical Implementation", 5, "Technical Implementation section"),
            ("Budget Analysis", 5, "Budget Analysis section")
        ]
        
        for term, points, desc in content_checks:
            if term.lower() in text_content.lower():
                checks.append({"name": desc, "passed": True, "detail": f"Found: {term}"})
                total_score += points
            else:
                checks.append({"name": desc, "passed": False, "detail": f"Missing: {term}"})
    else:
        checks.append({"name": "Content extraction", "passed": False, "detail": text_content})
    
    # Check 4: Document structure (30 points)
    structure = check_docx_structure(filepath)
    if 'error' not in structure:
        # TOC check (10 points)
        if structure.get('has_toc', False):
            checks.append({"name": "Table of Contents", "passed": True, "detail": "TOC found in document"})
            total_score += 10
        else:
            checks.append({"name": "Table of Contents", "passed": False, "detail": "No TOC found"})
        
        # Headings check (10 points)
        if structure.get('heading_count', 0) >= 4:
            checks.append({"name": "Proper headings", "passed": True, "detail": f"Found {structure['heading_count']} headings"})
            total_score += 10
        else:
            checks.append({"name": "Proper headings", "passed": False, "detail": f"Only {structure.get('heading_count', 0)} headings found, expected at least 4"})
        
        # Table check (10 points)
        if structure.get('has_table', False):
            checks.append({"name": "Budget table", "passed": True, "detail": f"Found {structure['table_count']} table(s)"})
            total_score += 10
        else:
            checks.append({"name": "Budget table", "passed": False, "detail": "No tables found"})
    else:
        checks.append({"name": "Document structure", "passed": False, "detail": structure['error']})
    
    # Final assessment
    final_score = (total_score / max_score) * 100
    passed = final_score >= 70  # Pass if 70% or better
    
    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0, "checks": [{"name": "Usage", "passed": False, "detail": "Workspace path required"}]}))
        sys.exit(1)
    
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result, indent=2))