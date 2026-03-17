#!/usr/bin/env python3
import os
import sys
import json
import pandas as pd
from pypdf import PdfReader
import pdfplumber
from PIL import Image

def check_task_completion(workspace_dir):
    checks = []
    total_score = 0
    max_score = 100
    
    # Check 1: Excel files created from table extraction (30 points)
    excel_files = [f for f in os.listdir(workspace_dir) if f.endswith('.xlsx') and 'summary' not in f.lower()]
    if len(excel_files) >= 3:
        checks.append({"name": "Excel files created", "passed": True, "detail": f"Found {len(excel_files)} Excel files"})
        total_score += 15
        
        # Verify Excel content
        valid_excel_count = 0
        for excel_file in excel_files:
            try:
                df = pd.read_excel(os.path.join(workspace_dir, excel_file))
                if len(df) > 0 and len(df.columns) > 2:  # Should have meaningful table data
                    valid_excel_count += 1
            except:
                pass
        
        if valid_excel_count >= 2:
            checks.append({"name": "Excel content validation", "passed": True, "detail": f"{valid_excel_count} Excel files contain valid table data"})
            total_score += 15
        else:
            checks.append({"name": "Excel content validation", "passed": False, "detail": f"Only {valid_excel_count} Excel files contain valid data"})
    else:
        checks.append({"name": "Excel files created", "passed": False, "detail": f"Found only {len(excel_files)} Excel files, expected at least 3"})
    
    # Check 2: Summary report PDF created (25 points)
    summary_pdfs = [f for f in os.listdir(workspace_dir) if f.endswith('.pdf') and 'summary' in f.lower()]
    if summary_pdfs:
        summary_pdf = summary_pdfs[0]
        try:
            reader = PdfReader(os.path.join(workspace_dir, summary_pdf))
            if len(reader.pages) >= 1:
                checks.append({"name": "Summary PDF created", "passed": True, "detail": f"Created {summary_pdf} with {len(reader.pages)} pages"})
                total_score += 15
                
                # Check for statistics content
                text = ""
                for page in reader.pages:
                    text += page.extract_text().lower()
                
                stats_keywords = ['page', 'table', 'annotation', 'word', 'count']
                found_stats = sum(1 for keyword in stats_keywords if keyword in text)
                
                if found_stats >= 3:
                    checks.append({"name": "Summary statistics included", "passed": True, "detail": f"Found {found_stats}/5 expected statistics keywords"})
                    total_score += 10
                else:
                    checks.append({"name": "Summary statistics included", "passed": False, "detail": f"Found only {found_stats}/5 expected statistics keywords"})
            else:
                checks.append({"name": "Summary PDF created", "passed": False, "detail": "Summary PDF is empty"})
        except Exception as e:
            checks.append({"name": "Summary PDF created", "passed": False, "detail": f"Error reading summary PDF: {str(e)}"})
    else:
        checks.append({"name": "Summary PDF created", "passed": False, "detail": "No summary PDF found"})
    
    # Check 3: Annotation extraction (20 points)
    annotation_files = [f for f in os.listdir(workspace_dir) if 'annotation' in f.lower() and (f.endswith('.txt') or f.endswith('.json') or f.endswith('.csv'))]
    if annotation_files:
        checks.append({"name": "Annotation data extracted", "passed": True, "detail": f"Found annotation files: {', '.join(annotation_files)}"})
        total_score += 10
        
        # Verify annotation content contains markers
        marker_found = False
        for ann_file in annotation_files:
            try:
                with open(os.path.join(workspace_dir, ann_file), 'r') as f:
                    content = f.read().lower()
                    if 'marker_annotation' in content:
                        marker_found = True
                        break
            except:
                pass
        
        if marker_found:
            checks.append({"name": "Annotation content validation", "passed": True, "detail": "Found expected marker annotations"})
            total_score += 10
        else:
            checks.append({"name": "Annotation content validation", "passed": False, "detail": "No marker annotations found in extracted data"})
    else:
        checks.append({"name": "Annotation data extracted", "passed": False, "detail": "No annotation files found"})
    
    # Check 4: Thumbnail images (15 points)
    image_files = [f for f in os.listdir(workspace_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if len(image_files) >= 3:
        checks.append({"name": "Thumbnail images created", "passed": True, "detail": f"Found {len(image_files)} image files"})
        total_score += 15
    else:
        checks.append({"name": "Thumbnail images created", "passed": False, "detail": f"Found only {len(image_files)} image files, expected at least 3"})
    
    # Check 5: Original marker content preserved (10 points)
    marker_checks = 0
    expected_markers = ['MARKER_FINANCIAL_REPORT', 'MARKER_SCIENTIFIC_STUDY', 'MARKER_ENGINEERING_DIAGRAM']
    
    for marker in expected_markers:
        found = False
        # Check in Excel files
        for excel_file in excel_files:
            try:
                df = pd.read_excel(os.path.join(workspace_dir, excel_file))
                if marker.lower() in str(df.values).lower():
                    found = True
                    break
            except:
                pass
        
        # Check in text files
        if not found:
            for file in os.listdir(workspace_dir):
                if file.endswith(('.txt', '.csv')):
                    try:
                        with open(os.path.join(workspace_dir, file), 'r') as f:
                            if marker.lower() in f.read().lower():
                                found = True
                                break
                    except:
                        pass
        
        if found:
            marker_checks += 1
    
    if marker_checks >= 2:
        checks.append({"name": "Marker content preserved", "passed": True, "detail": f"Found {marker_checks}/3 expected markers"})
        total_score += 10
    else:
        checks.append({"name": "Marker content preserved", "passed": False, "detail": f"Found only {marker_checks}/3 expected markers"})
    
    final_score = total_score / max_score
    passed = final_score >= 0.7
    
    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: eval_script.py <workspace_directory>")
        sys.exit(1)
    
    result = check_task_completion(sys.argv[1])
    print(json.dumps(result, indent=2))