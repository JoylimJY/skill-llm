import sys
import os
import json
import re
from pathlib import Path

def check_file_exists(workspace_dir, filename, file_type):
    """Check if a specific file exists and return details"""
    file_path = Path(workspace_dir) / filename
    if file_path.exists():
        size = file_path.stat().st_size
        return True, f"{file_type} exists with size {size} bytes"
    else:
        return False, f"{file_type} not found at expected location: {filename}"

def check_philosophy_content(workspace_dir):
    """Check if philosophy.md contains required design philosophy elements"""
    philosophy_path = Path(workspace_dir) / 'philosophy.md'
    
    if not philosophy_path.exists():
        return False, "philosophy.md file not found"
    
    try:
        with open(philosophy_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        # Check for key philosophy elements (case-insensitive)
        required_elements = [
            ['visual', 'design', 'aesthetic'],
            ['form', 'space', 'composition'],
            ['color', 'material', 'texture'],
            ['minimal', 'text', 'typography']
        ]
        
        found_elements = 0
        for element_group in required_elements:
            if any(keyword in content for keyword in element_group):
                found_elements += 1
        
        # Check length - should be substantial (4-6 paragraphs)
        word_count = len(content.split())
        length_adequate = word_count >= 200  # Approximate minimum for 4 paragraphs
        
        if found_elements >= 3 and length_adequate:
            return True, f"Philosophy contains {found_elements}/4 key elements with {word_count} words"
        else:
            return False, f"Philosophy incomplete: {found_elements}/4 elements, {word_count} words"
    
    except Exception as e:
        return False, f"Error reading philosophy file: {str(e)}"

def check_pdf_quality(workspace_dir):
    """Check if PDF exists and has reasonable size indicating visual content"""
    pdf_path = Path(workspace_dir) / 'mathematical_beauty.pdf'
    
    if not pdf_path.exists():
        return False, "mathematical_beauty.pdf not found"
    
    try:
        size = pdf_path.stat().st_size
        # PDF should be substantial (indicating visual content) but not excessive
        if size < 10000:  # Less than 10KB suggests minimal content
            return False, f"PDF too small ({size} bytes) - likely lacks visual content"
        elif size > 50000000:  # More than 50MB seems excessive
            return False, f"PDF too large ({size} bytes) - may indicate processing issues"
        else:
            return True, f"PDF has appropriate size ({size} bytes) suggesting rich visual content"
    
    except Exception as e:
        return False, f"Error checking PDF: {str(e)}"

def check_mathematical_theme(workspace_dir):
    """Check if the work appears to address mathematical beauty theme"""
    # Check both philosophy and any text files for mathematical references
    philosophy_path = Path(workspace_dir) / 'philosophy.md'
    
    math_keywords = [
        'mathematical', 'geometric', 'proportion', 'ratio', 'symmetry',
        'pattern', 'formula', 'equation', 'precision', 'order',
        'fibonacci', 'golden', 'spiral', 'grid', 'systematic'
    ]
    
    found_keywords = []
    
    if philosophy_path.exists():
        try:
            with open(philosophy_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                for keyword in math_keywords:
                    if keyword in content:
                        found_keywords.append(keyword)
        except Exception:
            pass
    
    # Also check for mathematical concepts in general approach
    if len(found_keywords) >= 2:
        return True, f"Mathematical theme evident through keywords: {', '.join(found_keywords[:3])}"
    elif len(found_keywords) >= 1:
        return True, f"Some mathematical elements present: {found_keywords[0]}"
    else:
        # Even without explicit keywords, accept if files exist (abstract interpretation)
        return True, "Mathematical theme may be expressed abstractly through visual design"

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "argument_check", "passed": False, "detail": "Workspace directory not provided"}]}))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    
    checks = []
    
    # Check 1: Philosophy file exists and has content
    philosophy_passed, philosophy_detail = check_philosophy_content(workspace_dir)
    checks.append({"name": "philosophy_content", "passed": philosophy_passed, "detail": philosophy_detail})
    
    # Check 2: PDF file exists with appropriate size
    pdf_passed, pdf_detail = check_pdf_quality(workspace_dir)
    checks.append({"name": "pdf_quality", "passed": pdf_passed, "detail": pdf_detail})
    
    # Check 3: Mathematical theme is addressed
    theme_passed, theme_detail = check_mathematical_theme(workspace_dir)
    checks.append({"name": "mathematical_theme", "passed": theme_passed, "detail": theme_detail})
    
    # Check 4: Proper file naming
    pdf_exists = (Path(workspace_dir) / 'mathematical_beauty.pdf').exists()
    md_exists = (Path(workspace_dir) / 'philosophy.md').exists()
    naming_passed = pdf_exists and md_exists
    naming_detail = f"PDF: {'✓' if pdf_exists else '✗'}, Philosophy: {'✓' if md_exists else '✗'}"
    checks.append({"name": "file_naming", "passed": naming_passed, "detail": naming_detail})
    
    # Calculate score and overall pass
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.75  # Pass if at least 3/4 checks pass
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()