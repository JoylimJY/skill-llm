#!/usr/bin/env python3
import sys
import os
import json
import glob
from pypdf import PdfReader
import re

def main(workspace_dir):
    os.chdir(workspace_dir)
    
    checks = []
    total_score = 0
    
    # Check 1: Summary report PDF exists
    report_files = glob.glob("*summary*.pdf") or glob.glob("*report*.pdf") or glob.glob("*audit*.pdf")
    if report_files:
        checks.append({"name": "report_pdf_exists", "passed": True, "detail": f"Found report: {report_files[0]}"})
        total_score += 20
        report_file = report_files[0]
    else:
        checks.append({"name": "report_pdf_exists", "passed": False, "detail": "No summary report PDF found"})
        report_file = None
    
    # Check 2: Extracted data file exists
    data_files = glob.glob("*extracted*.json") or glob.glob("*data*.json")
    extracted_data = None
    if data_files:
        try:
            with open(data_files[0], 'r') as f:
                extracted_data = json.load(f)
            checks.append({"name": "extracted_data_exists", "passed": True, "detail": f"Found data file: {data_files[0]}"})
            total_score += 15
        except:
            checks.append({"name": "extracted_data_exists", "passed": False, "detail": "Data file exists but invalid JSON"})
    else:
        checks.append({"name": "extracted_data_exists", "passed": False, "detail": "No extracted data JSON found"})
    
    # Check 3: Key marker extraction
    markers_found = 0
    expected_markers = ["MARKER_FORM_2024", "MARKER_JOHN_DOE", "POL-MARKER-123456", 
                       "MARKER_APPROVED", "MARKER_SUPPLEMENT_2024", "VALIDATION_SUPPLEMENT_COMPLETE"]
    
    if extracted_data:
        data_str = json.dumps(extracted_data).upper()
        for marker in expected_markers:
            if marker.upper() in data_str:
                markers_found += 1
    
    marker_score = (markers_found / len(expected_markers)) * 20
    total_score += marker_score
    checks.append({"name": "marker_extraction", "passed": markers_found >= 4, 
                   "detail": f"Found {markers_found}/{len(expected_markers)} key markers"})
    
    # Check 4: OCR processing of supplement
    ocr_markers = ["MARKER_RADIATOR", "MARKER_PAINT", "MARKER_ALIGNMENT"]
    ocr_found = 0
    
    if extracted_data:
        data_str = json.dumps(extracted_data).upper()
        for marker in ocr_markers:
            if marker.upper() in data_str:
                ocr_found += 1
    
    ocr_score = (ocr_found / len(ocr_markers)) * 15
    total_score += ocr_score
    checks.append({"name": "ocr_supplement_processing", "passed": ocr_found >= 2,
                   "detail": f"Found {ocr_found}/{len(ocr_markers)} OCR markers from supplement"})
    
    # Check 5: Report PDF contains charts/visualizations
    chart_indicators = False
    if report_file:
        try:
            reader = PdfReader(report_file)
            text_content = ""
            for page in reader.pages:
                text_content += page.extract_text().upper()
            
            # Look for chart/visualization indicators
            chart_keywords = ["CHART", "GRAPH", "DISTRIBUTION", "CATEGORY", "CLAIM", "SUMMARY"]
            found_keywords = sum(1 for keyword in chart_keywords if keyword in text_content)
            
            if found_keywords >= 3:
                chart_indicators = True
                total_score += 15
                checks.append({"name": "report_contains_charts", "passed": True, 
                             "detail": f"Found {found_keywords} chart-related keywords in report"})
            else:
                checks.append({"name": "report_contains_charts", "passed": False,
                             "detail": f"Only found {found_keywords} chart-related keywords"})
        except Exception as e:
            checks.append({"name": "report_contains_charts", "passed": False,
                         "detail": f"Error reading report PDF: {str(e)}"})
    else:
        checks.append({"name": "report_contains_charts", "passed": False,
                     "detail": "No report PDF to analyze"})
    
    # Check 6: Business rule validation
    validation_passed = False
    if extracted_data:
        # Check if claim amount is reasonable for auto category
        try:
            claim_amount = float(extracted_data.get('claim_amount', 0) or 
                               extracted_data.get('form_data', {}).get('claim_amount', 0))
            if 10000 <= claim_amount <= 50000:  # Reasonable auto claim range
                validation_passed = True
                total_score += 15
        except:
            pass
    
    checks.append({"name": "business_rule_validation", "passed": validation_passed,
                   "detail": "Validated claim amount against business rules" if validation_passed else "Business rule validation failed"})
    
    # Final score calculation
    final_score = min(total_score / 100.0, 1.0)
    overall_passed = final_score >= 0.7
    
    result = {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)
    
    main(sys.argv[1])