import sys
import os
import json
from pathlib import Path

def check_maya_portfolio(workspace_path):
    checks = []
    score = 0.0
    
    # Check if main HTML file exists
    html_files = list(Path(workspace_path).glob('*.html'))
    if not html_files:
        checks.append({"name": "HTML file exists", "passed": False, "detail": "No HTML files found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    main_html = html_files[0]
    checks.append({"name": "HTML file exists", "passed": True, "detail": f"Found {main_html.name}"})
    score += 0.2
    
    # Read HTML content
    try:
        with open(main_html, 'r', encoding='utf-8') as f:
            html_content = f.read().lower()
    except Exception as e:
        checks.append({"name": "Read HTML content", "passed": False, "detail": f"Error reading HTML: {str(e)}"})
        return {"passed": False, "score": score, "checks": checks}
    
    checks.append({"name": "Read HTML content", "passed": True, "detail": "HTML content loaded successfully"})
    score += 0.1
    
    # Check for photographer name Maya Chen
    maya_found = 'maya chen' in html_content or 'maya' in html_content
    checks.append({"name": "Maya Chen name present", "passed": maya_found, "detail": "Maya Chen's name found in content" if maya_found else "Maya Chen's name not found"})
    if maya_found:
        score += 0.15
    
    # Check for architectural photography mention
    arch_photo = any(term in html_content for term in ['architectural', 'architecture', 'photographer', 'photography'])
    checks.append({"name": "Photography specialty mentioned", "passed": arch_photo, "detail": "Architectural photography context found" if arch_photo else "No photography specialty context"})
    if arch_photo:
        score += 0.15
    
    # Check for required sections
    sections_found = 0
    required_sections = ['about', 'portfolio', 'contact']
    for section in required_sections:
        found = section in html_content
        checks.append({"name": f"Section: {section}", "passed": found, "detail": f"{section} section found" if found else f"{section} section missing"})
        if found:
            sections_found += 1
            score += 0.1
    
    # Check for CSS styling
    css_found = '<style' in html_content or '.css' in html_content or 'font-family' in html_content
    checks.append({"name": "CSS styling present", "passed": css_found, "detail": "CSS styling detected" if css_found else "No CSS styling found"})
    if css_found:
        score += 0.15
    
    # Check for modern/creative elements
    creative_elements = any(term in html_content for term in ['grid', 'flex', 'transform', 'animation', 'gradient', 'opacity', 'transition'])
    checks.append({"name": "Modern CSS features", "passed": creative_elements, "detail": "Modern CSS features detected" if creative_elements else "Basic styling only"})
    if creative_elements:
        score += 0.15
    
    # Bonus points for external CSS file
    css_files = list(Path(workspace_path).glob('*.css'))
    if css_files:
        checks.append({"name": "External CSS file", "passed": True, "detail": f"Found {css_files[0].name}"})
        score += 0.05
    
    passed = score >= 0.6
    return {"passed": passed, "score": min(score, 1.0), "checks": checks}

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Usage", "passed": False, "detail": "Workspace path required"}]}))
        sys.exit(1)
    
    result = check_maya_portfolio(sys.argv[1])
    print(json.dumps(result, indent=2))