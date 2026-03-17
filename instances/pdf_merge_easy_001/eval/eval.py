#!/usr/bin/env python3
import sys
import os
from pypdf import PdfReader
import json

def check_task(workspace_dir):
    checks = []
    passed_all = True
    score = 0.0
    
    # Check if output file exists
    output_path = os.path.join(workspace_dir, "combined_report.pdf")
    if os.path.exists(output_path):
        checks.append({"name": "output_file_exists", "passed": True, "detail": "combined_report.pdf exists"})
        score += 25
    else:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "combined_report.pdf not found"})
        passed_all = False
        return {"passed": False, "score": 0.0, "checks": checks}
    
    try:
        reader = PdfReader(output_path)
        
        # Check page count (should be 3 pages, one from each input)
        expected_pages = 3
        actual_pages = len(reader.pages)
        if actual_pages == expected_pages:
            checks.append({"name": "page_count", "passed": True, "detail": f"Correct page count: {actual_pages}"})
            score += 25
        else:
            checks.append({"name": "page_count", "passed": False, "detail": f"Expected {expected_pages} pages, got {actual_pages}"})
            passed_all = False
        
        # Extract all text and check for markers in correct order
        all_text = ""
        for page in reader.pages:
            all_text += page.extract_text()
        
        # Check for report1 markers
        if "MARKER_REPORT1_START" in all_text and "MARKER_REPORT1_END" in all_text:
            checks.append({"name": "report1_content", "passed": True, "detail": "Report1 content found"})
            score += 15
        else:
            checks.append({"name": "report1_content", "passed": False, "detail": "Report1 markers not found"})
            passed_all = False
        
        # Check for report2 markers
        if "MARKER_REPORT2_START" in all_text and "MARKER_REPORT2_END" in all_text:
            checks.append({"name": "report2_content", "passed": True, "detail": "Report2 content found"})
            score += 15
        else:
            checks.append({"name": "report2_content", "passed": False, "detail": "Report2 markers not found"})
            passed_all = False
        
        # Check for summary markers
        if "MARKER_SUMMARY_START" in all_text and "MARKER_SUMMARY_END" in all_text:
            checks.append({"name": "summary_content", "passed": True, "detail": "Summary content found"})
            score += 15
        else:
            checks.append({"name": "summary_content", "passed": False, "detail": "Summary markers not found"})
            passed_all = False
        
        # Check order (report1 should come before report2, report2 before summary)
        report1_pos = all_text.find("MARKER_REPORT1_START")
        report2_pos = all_text.find("MARKER_REPORT2_START")
        summary_pos = all_text.find("MARKER_SUMMARY_START")
        
        if report1_pos < report2_pos < summary_pos and report1_pos != -1:
            checks.append({"name": "correct_order", "passed": True, "detail": "PDFs merged in correct order"})
            score += 5
        else:
            checks.append({"name": "correct_order", "passed": False, "detail": "PDFs not in expected order (report1, report2, summary)"})
            passed_all = False
        
    except Exception as e:
        checks.append({"name": "pdf_readable", "passed": False, "detail": f"Error reading PDF: {str(e)}"})
        passed_all = False
    
    return {"passed": passed_all, "score": score, "checks": checks}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: eval_script.py <workspace_dir>")
        sys.exit(1)
    
    result = check_task(sys.argv[1])
    print(json.dumps(result))