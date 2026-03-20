#!/usr/bin/env python3
import sys
import os
import subprocess
import json
from pathlib import Path

def check_docx_file(workspace_dir):
    checks = []
    score = 0.0
    
    # Check if file exists
    docx_path = Path(workspace_dir) / 'company_memo.docx'
    if not docx_path.exists():
        checks.append({"name": "file_exists", "passed": False, "detail": "company_memo.docx not found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "file_exists", "passed": True, "detail": "company_memo.docx found"})
    score += 0.2
    
    # Extract text using pandoc
    try:
        result = subprocess.run(['pandoc', str(docx_path), '-t', 'plain'], 
                              capture_output=True, text=True, check=True)
        text_content = result.stdout.lower()
        
        # Check for required elements
        required_elements = [
            ('memorandum_header', 'memorandum'),
            ('to_field', 'to:'),
            ('from_field', 'from:'),
            ('date_field', 'date:'),
            ('re_field', 're:'),
            ('staff_recipient', 'all staff'),
            ('hr_sender', 'hr department'),
            ('remote_work', 'remote work')
        ]
        
        for element_name, search_text in required_elements:
            if search_text in text_content:
                checks.append({"name": element_name, "passed": True, "detail": f"Found '{search_text}'"})
                score += 0.1
            else:
                checks.append({"name": element_name, "passed": False, "detail": f"Missing '{search_text}'"})
        
        # Check document length (should have substantial content)
        if len(text_content.strip()) > 200:
            checks.append({"name": "adequate_content", "passed": True, "detail": f"Document has {len(text_content)} characters"})
            score += 0.1
        else:
            checks.append({"name": "adequate_content", "passed": False, "detail": f"Document too short: {len(text_content)} characters"})
            
    except subprocess.CalledProcessError as e:
        checks.append({"name": "text_extraction", "passed": False, "detail": f"Failed to extract text: {e}"})
        return {"passed": False, "score": score, "checks": checks}
    
    # Validate DOCX structure
    try:
        import zipfile
        with zipfile.ZipFile(docx_path, 'r') as z:
            files = z.namelist()
            required_files = ['word/document.xml', '[Content_Types].xml', '_rels/.rels']
            for req_file in required_files:
                if req_file in files:
                    checks.append({"name": f"structure_{req_file.replace('/', '_').replace('[', '').replace(']', '')}", "passed": True, "detail": f"Found {req_file}"})
                    score += 0.03
                else:
                    checks.append({"name": f"structure_{req_file.replace('/', '_').replace('[', '').replace(']', '')}", "passed": False, "detail": f"Missing {req_file}"})
    except Exception as e:
        checks.append({"name": "docx_structure", "passed": False, "detail": f"Invalid DOCX structure: {e}"})
    
    passed = score >= 0.7
    return {"passed": passed, "score": min(score, 1.0), "checks": checks}

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = check_docx_file(sys.argv[1])
    print(json.dumps(result))