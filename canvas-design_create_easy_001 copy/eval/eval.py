import sys
import os
import json
import glob
from pathlib import Path

def evaluate_task(workspace_dir):
    checks = []
    
    # Check 1: Design philosophy markdown file exists
    md_files = glob.glob(os.path.join(workspace_dir, "*.md"))
    design_md_found = False
    design_md_content = ""
    
    for md_file in md_files:
        if "design" in os.path.basename(md_file).lower() or "philosophy" in os.path.basename(md_file).lower():
            design_md_found = True
            with open(md_file, 'r', encoding='utf-8') as f:
                design_md_content = f.read().lower()
            break
    
    checks.append({
        "name": "Design philosophy markdown file exists",
        "passed": design_md_found,
        "detail": f"Found design philosophy file: {design_md_found}"
    })
    
    # Check 2: Design philosophy contains movement/philosophy content
    philosophy_keywords = ["philosophy", "visual", "design", "aesthetic", "movement", "form", "space", "color", "composition"]
    has_philosophy_content = any(keyword in design_md_content for keyword in philosophy_keywords) and len(design_md_content) > 200
    
    checks.append({
        "name": "Design philosophy contains substantive content",
        "passed": has_philosophy_content,
        "detail": f"Philosophy content check: {has_philosophy_content}, length: {len(design_md_content)}"
    })
    
    # Check 3: PDF file exists
    pdf_files = glob.glob(os.path.join(workspace_dir, "*.pdf"))
    pdf_found = len(pdf_files) > 0
    
    checks.append({
        "name": "PDF poster file exists",
        "passed": pdf_found,
        "detail": f"Found {len(pdf_files)} PDF file(s)"
    })
    
    # Check 4: PDF file has expected name pattern
    expected_pdf_found = False
    if pdf_files:
        for pdf_file in pdf_files:
            filename = os.path.basename(pdf_file).lower()
            if "exhibition" in filename and "poster" in filename:
                expected_pdf_found = True
                break
            elif "poster" in filename or "exhibition" in filename:
                expected_pdf_found = True
                break
    
    checks.append({
        "name": "PDF has appropriate filename",
        "passed": expected_pdf_found,
        "detail": f"PDF with expected name pattern found: {expected_pdf_found}"
    })
    
    # Check 5: PDF file is not empty (basic size check)
    pdf_valid_size = False
    if pdf_files:
        pdf_size = os.path.getsize(pdf_files[0])
        pdf_valid_size = pdf_size > 1000  # At least 1KB
    
    checks.append({
        "name": "PDF file has valid size",
        "passed": pdf_valid_size,
        "detail": f"PDF size check passed: {pdf_valid_size}"
    })
    
    # Calculate score
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8
    
    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: eval_script.py <workspace_dir>"}))
        sys.exit(1)
    
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result))