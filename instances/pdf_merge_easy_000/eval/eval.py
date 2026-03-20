#!/usr/bin/env python3

import sys
import os
from pypdf import PdfReader
import json

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Missing workspace directory argument"}]}))
        return
    
    workspace_dir = sys.argv[1]
    output_file = os.path.join(workspace_dir, "combined_report.pdf")
    
    checks = []
    passed_count = 0
    total_checks = 4
    
    # Check 1: Output file exists
    file_exists = os.path.exists(output_file)
    checks.append({
        "name": "file_exists",
        "passed": file_exists,
        "detail": f"combined_report.pdf exists: {file_exists}"
    })
    if file_exists:
        passed_count += 1
    
    if not file_exists:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result))
        return
    
    try:
        reader = PdfReader(output_file)
        
        # Check 2: Correct number of pages (2 + 1 + 2 = 5 pages)
        page_count = len(reader.pages)
        correct_pages = page_count == 5
        checks.append({
            "name": "page_count",
            "passed": correct_pages,
            "detail": f"Expected 5 pages, found {page_count}"
        })
        if correct_pages:
            passed_count += 1
        
        # Check 3: Extract text and verify markers are in correct order
        all_text = ""
        for page in reader.pages:
            all_text += page.extract_text()
        
        # Expected markers in order
        expected_markers = [
            "SALES_2023_Q1",
            "REVENUE_SUMMARY", 
            "MARKETING_2023_Q1",
            "OPERATIONS_2023_Q1",
            "FINAL_CONCLUSIONS"
        ]
        
        markers_found = []
        for marker in expected_markers:
            if marker in all_text:
                markers_found.append(marker)
        
        all_markers_present = len(markers_found) == len(expected_markers)
        checks.append({
            "name": "markers_present",
            "passed": all_markers_present,
            "detail": f"Found {len(markers_found)}/5 expected markers: {markers_found}"
        })
        if all_markers_present:
            passed_count += 1
        
        # Check 4: Verify content order by checking marker positions
        marker_positions = []
        for marker in expected_markers:
            pos = all_text.find(marker)
            if pos != -1:
                marker_positions.append(pos)
            else:
                marker_positions.append(-1)
        
        # Check if markers appear in ascending order (correct merge order)
        correct_order = all(marker_positions[i] < marker_positions[i+1] 
                          for i in range(len(marker_positions)-1) 
                          if marker_positions[i] != -1 and marker_positions[i+1] != -1)
        
        checks.append({
            "name": "correct_order",
            "passed": correct_order,
            "detail": f"Markers appear in correct sequence: {correct_order}"
        })
        if correct_order:
            passed_count += 1
            
    except Exception as e:
        checks.append({
            "name": "pdf_processing",
            "passed": False,
            "detail": f"Error processing PDF: {str(e)}"
        })
    
    score = passed_count / total_checks
    passed = score >= 0.75
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()