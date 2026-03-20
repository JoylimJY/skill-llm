#!/usr/bin/env python3
import sys
import os
import json
import re
from pathlib import Path

def check_portfolio_implementation(workspace_dir):
    checks = []
    score = 0.0
    
    # Check if main HTML file exists
    html_files = list(Path(workspace_dir).glob('*.html'))
    if not html_files:
        checks.append({"name": "HTML file exists", "passed": False, "detail": "No HTML file found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    main_html = html_files[0]
    checks.append({"name": "HTML file exists", "passed": True, "detail": f"Found {main_html.name}"})
    score += 10
    
    # Read HTML content
    try:
        with open(main_html, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        checks.append({"name": "HTML readable", "passed": False, "detail": f"Error reading HTML: {str(e)}"})
        return {"passed": False, "score": score, "checks": checks}
    
    checks.append({"name": "HTML readable", "passed": True, "detail": "HTML content loaded successfully"})
    score += 5
    
    # Check for required sections
    sections_to_check = ['hero', 'work', 'about', 'contact']
    for section in sections_to_check:
        if re.search(rf'(id|class)=["\'][^"\'\/]*{section}', html_content, re.IGNORECASE):
            checks.append({"name": f"{section} section", "passed": True, "detail": f"{section.capitalize()} section found"})
            score += 10
        else:
            checks.append({"name": f"{section} section", "passed": False, "detail": f"{section.capitalize()} section not found"})
    
    # Check for Alex Chen name
    if 'Alex Chen' in html_content:
        checks.append({"name": "Designer name included", "passed": True, "detail": "Alex Chen name found in content"})
        score += 10
    else:
        checks.append({"name": "Designer name included", "passed": False, "detail": "Alex Chen name not found"})
    
    # Check for motion graphics related content
    motion_keywords = ['motion', 'animation', 'film', 'title', 'brand', 'experimental']
    found_keywords = []
    for keyword in motion_keywords:
        if re.search(keyword, html_content, re.IGNORECASE):
            found_keywords.append(keyword)
    
    if len(found_keywords) >= 3:
        checks.append({"name": "Motion graphics context", "passed": True, "detail": f"Found relevant keywords: {', '.join(found_keywords)}"})
        score += 15
    else:
        checks.append({"name": "Motion graphics context", "passed": False, "detail": f"Only found {len(found_keywords)} relevant keywords"})
    
    # Check for CSS styling (either embedded or external)
    has_css = False
    css_content = ""
    
    if '<style' in html_content:
        has_css = True
        css_match = re.search(r'<style[^>]*>(.*?)</style>', html_content, re.DOTALL | re.IGNORECASE)
        if css_match:
            css_content = css_match.group(1)
    
    css_files = list(Path(workspace_dir).glob('*.css')) + list(Path(workspace_dir).glob('**/*.css'))
    if css_files:
        has_css = True
        try:
            with open(css_files[0], 'r', encoding='utf-8') as f:
                css_content += f.read()
        except:
            pass
    
    if has_css:
        checks.append({"name": "CSS styling present", "passed": True, "detail": "CSS found (embedded or external)"})
        score += 15
    else:
        checks.append({"name": "CSS styling present", "passed": False, "detail": "No CSS styling found"})
    
    # Check for responsive design
    if css_content and re.search(r'@media|viewport|responsive|mobile', css_content + html_content, re.IGNORECASE):
        checks.append({"name": "Responsive design elements", "passed": True, "detail": "Responsive design indicators found"})
        score += 10
    else:
        checks.append({"name": "Responsive design elements", "passed": False, "detail": "No responsive design indicators found"})
    
    # Check for creative/distinctive styling choices
    creative_indicators = ['animation', 'transform', 'gradient', 'shadow', 'transition', 'keyframes', '@keyframes']
    found_creative = []
    for indicator in creative_indicators:
        if re.search(indicator, css_content + html_content, re.IGNORECASE):
            found_creative.append(indicator)
    
    if len(found_creative) >= 3:
        checks.append({"name": "Creative visual elements", "passed": True, "detail": f"Found creative CSS: {', '.join(found_creative[:3])}"})
        score += 15
    else:
        checks.append({"name": "Creative visual elements", "passed": False, "detail": "Limited creative CSS elements found"})
    
    # Final score normalization
    max_possible_score = 100
    normalized_score = min(score / max_possible_score, 1.0)
    passed = normalized_score >= 0.7
    
    return {
        "passed": passed,
        "score": normalized_score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "eval_args", "passed": False, "detail": "Expected workspace directory argument"}]}))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = check_portfolio_implementation(workspace_dir)
    print(json.dumps(result))