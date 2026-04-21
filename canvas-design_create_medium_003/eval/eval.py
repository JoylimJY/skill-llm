import sys
import os
import json
import glob
from pathlib import Path

def check_file_exists(workspace_dir, pattern):
    """Check if file matching pattern exists"""
    files = glob.glob(os.path.join(workspace_dir, pattern))
    return len(files) > 0, files

def check_markdown_content(file_path):
    """Check if markdown file contains design philosophy content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        # Check for key philosophy elements
        philosophy_indicators = [
            'philosophy', 'aesthetic', 'movement', 'visual', 
            'design', 'manifesto', 'expression', 'form'
        ]
        
        found_indicators = sum(1 for indicator in philosophy_indicators if indicator in content)
        has_substantial_content = len(content.strip()) > 200
        
        return found_indicators >= 3 and has_substantial_content, f"Found {found_indicators}/8 philosophy indicators, content length: {len(content)}"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def check_pdf_creation(file_path):
    """Check if PDF file was created and has reasonable size"""
    try:
        if not os.path.exists(file_path):
            return False, "PDF file not found"
        
        file_size = os.path.getsize(file_path)
        if file_size < 1000:  # Very small file, likely empty
            return False, f"PDF file too small: {file_size} bytes"
        
        # Check if it's actually a PDF by reading header
        with open(file_path, 'rb') as f:
            header = f.read(10)
            if not header.startswith(b'%PDF'):
                return False, "File doesn't appear to be a valid PDF"
        
        return True, f"Valid PDF created, size: {file_size} bytes"
    except Exception as e:
        return False, f"Error checking PDF: {str(e)}"

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": []}))
        return
    
    workspace_dir = sys.argv[1]
    checks = []
    
    # Check 1: Design philosophy markdown file exists
    md_exists, md_files = check_file_exists(workspace_dir, "design_philosophy.md")
    if md_exists:
        md_content_valid, md_detail = check_markdown_content(md_files[0])
        checks.append({
            "name": "design_philosophy_content",
            "passed": md_content_valid,
            "detail": md_detail
        })
    else:
        checks.append({
            "name": "design_philosophy_content",
            "passed": False,
            "detail": "design_philosophy.md file not found"
        })
    
    # Check 2: PDF file with correct name exists
    pdf_exists, pdf_files = check_file_exists(workspace_dir, "digital_archaeology.pdf")
    if pdf_exists:
        pdf_valid, pdf_detail = check_pdf_creation(pdf_files[0])
        checks.append({
            "name": "pdf_creation",
            "passed": pdf_valid,
            "detail": pdf_detail
        })
    else:
        checks.append({
            "name": "pdf_creation",
            "passed": False,
            "detail": "digital_archaeology.pdf file not found"
        })
    
    # Check 3: Overall file structure compliance
    has_both_files = md_exists and pdf_exists
    checks.append({
        "name": "file_structure",
        "passed": has_both_files,
        "detail": f"Both required files present: {has_both_files}"
    })
    
    # Check 4: Digital archaeology theme integration
    theme_integrated = False
    theme_detail = "No theme indicators found"
    
    if md_exists:
        try:
            with open(md_files[0], 'r', encoding='utf-8') as f:
                md_content = f.read().lower()
            
            digital_terms = ['digital', 'technology', 'interface', 'obsolete', 'vintage', 'archaeology', 'format', 'pixel']
            found_terms = sum(1 for term in digital_terms if term in md_content)
            
            theme_integrated = found_terms >= 2
            theme_detail = f"Found {found_terms}/8 digital archaeology terms in philosophy"
        except:
            theme_detail = "Could not analyze theme integration"
    
    checks.append({
        "name": "theme_integration",
        "passed": theme_integrated,
        "detail": theme_detail
    })
    
    # Calculate score and overall pass
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.75  # Allow for some flexibility
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()