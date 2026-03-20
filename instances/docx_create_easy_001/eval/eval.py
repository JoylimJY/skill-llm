#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import json
import zipfile
import xml.etree.ElementTree as ET

def check_docx_file(workspace_dir):
    checks = []
    score = 0
    
    # Check if file exists
    docx_path = Path(workspace_dir) / 'project_report.docx'
    if not docx_path.exists():
        checks.append({"name": "File exists", "passed": False, "detail": "project_report.docx not found"})
        return {"passed": False, "score": 0, "checks": checks}
    
    checks.append({"name": "File exists", "passed": True, "detail": "project_report.docx found"})
    score += 20
    
    try:
        # Extract and parse document.xml
        with zipfile.ZipFile(docx_path, 'r') as zf:
            with zf.open('word/document.xml') as doc_file:
                doc_content = doc_file.read().decode('utf-8')
        
        # Parse XML
        root = ET.fromstring(doc_content)
        
        # Define namespace
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        
        # Extract all text content
        text_elements = root.findall('.//w:t', ns)
        all_text = ' '.join([elem.text or '' for elem in text_elements])
        
        # Check for title
        if 'Q1 2024 Project Status Report' in all_text:
            checks.append({"name": "Title present", "passed": True, "detail": "Found required title"})
            score += 20
        else:
            checks.append({"name": "Title present", "passed": False, "detail": "Title 'Q1 2024 Project Status Report' not found"})
        
        # Check for required sections
        required_sections = ['Executive Summary', 'Key Milestones', 'Next Steps']
        found_sections = 0
        for section in required_sections:
            if section in all_text:
                found_sections += 1
                checks.append({"name": f"Section '{section}'", "passed": True, "detail": f"Found section heading"})
            else:
                checks.append({"name": f"Section '{section}'", "passed": False, "detail": f"Section heading not found"})
        
        score += (found_sections / len(required_sections)) * 30
        
        # Check for table presence
        tables = root.findall('.//w:tbl', ns)
        if tables:
            checks.append({"name": "Table present", "passed": True, "detail": f"Found {len(tables)} table(s)"})
            score += 20
            
            # Check if table has content about phases/completion
            table_text = ''
            for table in tables:
                table_cells = table.findall('.//w:t', ns)
                table_text += ' '.join([cell.text or '' for cell in table_cells])
            
            if any(word in table_text.lower() for word in ['phase', 'completion', 'percent', '%']):
                checks.append({"name": "Table content relevant", "passed": True, "detail": "Table contains project phase/completion data"})
                score += 10
            else:
                checks.append({"name": "Table content relevant", "passed": False, "detail": "Table doesn't contain expected project data"})
        else:
            checks.append({"name": "Table present", "passed": False, "detail": "No tables found in document"})
        
    except Exception as e:
        checks.append({"name": "File parsing", "passed": False, "detail": f"Error parsing DOCX: {str(e)}"})
        return {"passed": False, "score": score, "checks": checks}
    
    passed = score >= 70
    return {"passed": passed, "score": score, "checks": checks}

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0, "checks": [{"name": "Usage", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = check_docx_file(workspace_dir)
    print(json.dumps(result))