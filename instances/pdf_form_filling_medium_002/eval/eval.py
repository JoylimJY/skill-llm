#!/usr/bin/env python3
import sys
import os
import json
from pypdf import PdfReader
import pdfplumber

def eval_task(workspace_dir):
    """Evaluate if the PDF form filling task was completed correctly"""
    checks = []
    passed = True
    score = 0.0
    
    os.chdir(workspace_dir)
    
    # Check 1: Verify input files exist
    input_files = ["employee_form.pdf", "employee_data.json"]
    for filename in input_files:
        if os.path.exists(filename):
            checks.append({"name": f"Input file {filename} exists", "passed": True, "detail": "Found input file"})
            score += 0.1
        else:
            checks.append({"name": f"Input file {filename} exists", "passed": False, "detail": "Input file missing"})
            passed = False
    
    # Check 2: Look for output PDF file (common names)
    output_files = ["filled_form.pdf", "completed_form.pdf", "employee_form_filled.pdf", "output.pdf", "result.pdf"]
    output_pdf = None
    for filename in output_files:
        if os.path.exists(filename):
            output_pdf = filename
            checks.append({"name": "Output PDF created", "passed": True, "detail": f"Found output file: {filename}"})
            score += 0.2
            break
    
    if not output_pdf:
        checks.append({"name": "Output PDF created", "passed": False, "detail": "No output PDF file found"})
        passed = False
        return {"passed": passed, "score": score, "checks": checks}
    
    # Check 3: Verify output PDF is valid and readable
    try:
        reader = PdfReader(output_pdf)
        if len(reader.pages) > 0:
            checks.append({"name": "Output PDF is valid", "passed": True, "detail": f"PDF has {len(reader.pages)} pages"})
            score += 0.2
        else:
            checks.append({"name": "Output PDF is valid", "passed": False, "detail": "PDF has no pages"})
            passed = False
    except Exception as e:
        checks.append({"name": "Output PDF is valid", "passed": False, "detail": f"Cannot read PDF: {e}"})
        passed = False
        return {"passed": passed, "score": score, "checks": checks}
    
    # Check 4: Extract text and verify form was filled with correct data
    try:
        with pdfplumber.open(output_pdf) as pdf:
            page = pdf.pages[0]
            text = page.extract_text().lower()
            
            # Check for expected marker text from the form
            if "marker_form_2024" in text:
                checks.append({"name": "Form marker present", "passed": True, "detail": "Form marker found in text"})
                score += 0.1
            else:
                checks.append({"name": "Form marker present", "passed": False, "detail": "Form marker not found"})
                passed = False
            
            # Check for filled data - John Smith
            if "john" in text and "smith" in text:
                checks.append({"name": "Name filled correctly", "passed": True, "detail": "Found 'John Smith' in PDF"})
                score += 0.2
            else:
                checks.append({"name": "Name filled correctly", "passed": False, "detail": "John Smith not found in PDF text"})
                passed = False
            
            # Check for employee ID
            if "emp001" in text:
                checks.append({"name": "Employee ID filled", "passed": True, "detail": "Found employee ID EMP001"})
                score += 0.1
            else:
                checks.append({"name": "Employee ID filled", "passed": False, "detail": "Employee ID EMP001 not found"})
                passed = False
                
            # Check for department
            if "engineering" in text:
                checks.append({"name": "Department filled", "passed": True, "detail": "Found department 'Engineering'"})
                score += 0.1
            else:
                checks.append({"name": "Department filled", "passed": False, "detail": "Department 'Engineering' not found"})
                passed = False
                
    except Exception as e:
        checks.append({"name": "Text extraction", "passed": False, "detail": f"Cannot extract text from PDF: {e}"})
        passed = False
    
    # Check 5: Verify the form structure is preserved  
    try:
        with pdfplumber.open(output_pdf) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
            
            required_labels = ["first name", "last name", "employee id", "department", "benefits"]
            labels_found = 0
            for label in required_labels:
                if label in text.lower():
                    labels_found += 1
            
            if labels_found >= 4:
                checks.append({"name": "Form structure preserved", "passed": True, "detail": f"Found {labels_found}/5 expected form labels"})
                score += 0.1
            else:
                checks.append({"name": "Form structure preserved", "passed": False, "detail": f"Only found {labels_found}/5 expected form labels"})
                # Don't fail completely for this, just reduce score
    except Exception as e:
        checks.append({"name": "Form structure check", "passed": False, "detail": f"Cannot verify form structure: {e}"})
    
    return {"passed": passed, "score": min(1.0, score), "checks": checks}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Usage", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = eval_task(sys.argv[1])
    print(json.dumps(result))