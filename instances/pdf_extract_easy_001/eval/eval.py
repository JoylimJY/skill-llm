#!/usr/bin/env python3
import sys
import os
import json

def check_task_completion(workspace_dir):
    checks = []
    passed = True
    score = 0.0
    
    # Check if output file exists
    output_file = os.path.join(workspace_dir, 'extracted_text.txt')
    if os.path.exists(output_file):
        checks.append({"name": "Output file exists", "passed": True, "detail": "extracted_text.txt found"})
        score += 0.2
    else:
        checks.append({"name": "Output file exists", "passed": False, "detail": "extracted_text.txt not found"})
        passed = False
        return {"passed": passed, "score": score, "checks": checks}
    
    # Read the extracted text
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            extracted_text = f.read()
        checks.append({"name": "File readable", "passed": True, "detail": "Successfully read extracted text"})
        score += 0.1
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": f"Error reading file: {e}"})
        passed = False
        return {"passed": passed, "score": score, "checks": checks}
    
    # Check for marker content from the PDF
    markers = [
        "MARKER_TITLE: Sales Report Q4 2023",
        "MARKER_INTRO: This report contains sales data",
        "MARKER_PRODUCT: Special Item",
        "MARKER_CONCLUSION: Total revenue for Q4 was $65,000"
    ]
    
    for marker in markers:
        if marker in extracted_text:
            checks.append({"name": f"Marker present: {marker[:30]}...", "passed": True, "detail": "Marker content found"})
            score += 0.15
        else:
            checks.append({"name": f"Marker present: {marker[:30]}...", "passed": False, "detail": "Marker content missing"})
            passed = False
    
    # Check for table data extraction
    table_elements = ["Widget A", "Widget B", "Widget C", "150", "225", "180", "$15,000", "$22,500", "$18,000"]
    table_found = 0
    for element in table_elements:
        if element in extracted_text:
            table_found += 1
    
    if table_found >= 6:  # At least 2/3 of table elements found
        checks.append({"name": "Table data extracted", "passed": True, "detail": f"Found {table_found}/{len(table_elements)} table elements"})
        score += 0.2
    else:
        checks.append({"name": "Table data extracted", "passed": False, "detail": f"Only found {table_found}/{len(table_elements)} table elements"})
    
    # Check minimum text length (should have substantial content)
    if len(extracted_text) > 200:
        checks.append({"name": "Adequate text length", "passed": True, "detail": f"Extracted {len(extracted_text)} characters"})
        score += 0.1
    else:
        checks.append({"name": "Adequate text length", "passed": False, "detail": f"Only {len(extracted_text)} characters extracted"})
        passed = False
    
    # Ensure score doesn't exceed 1.0
    score = min(score, 1.0)
    
    return {"passed": passed, "score": score, "checks": checks}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Usage", "passed": False, "detail": "Please provide workspace directory path"}]}))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = check_task_completion(workspace_dir)
    print(json.dumps(result))