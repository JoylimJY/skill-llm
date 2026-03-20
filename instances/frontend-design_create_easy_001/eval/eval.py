#!/usr/bin/env python3
import sys
import os
import json
from bs4 import BeautifulSoup
import re

def main(workspace_dir):
    checks = []
    score = 0.0
    
    # Look for HTML file
    html_files = [f for f in os.listdir(workspace_dir) if f.endswith('.html')]
    
    if not html_files:
        checks.append({"name": "HTML file exists", "passed": False, "detail": "No HTML file found"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    html_file = html_files[0]
    checks.append({"name": "HTML file exists", "passed": True, "detail": f"Found {html_file}"})
    score += 20
    
    # Parse HTML content
    try:
        with open(os.path.join(workspace_dir, html_file), 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
    except Exception as e:
        checks.append({"name": "HTML parsing", "passed": False, "detail": f"Failed to parse HTML: {str(e)}"})
        print(json.dumps({"passed": False, "score": score, "checks": checks}))
        return
    
    checks.append({"name": "HTML parsing", "passed": True, "detail": "HTML parsed successfully"})
    score += 15
    
    # Check for coffee shop name
    text_content = soup.get_text().lower()
    if 'brew' in text_content and 'bean' in text_content:
        checks.append({"name": "Coffee shop name present", "passed": True, "detail": "Found shop name reference"})
        score += 15
    else:
        checks.append({"name": "Coffee shop name present", "passed": False, "detail": "Shop name not found in content"})
    
    # Check for location info
    if 'main street' in text_content or '123' in text_content:
        checks.append({"name": "Location information", "passed": True, "detail": "Found location details"})
        score += 15
    else:
        checks.append({"name": "Location information", "passed": False, "detail": "Location not found"})
    
    # Check for menu items
    menu_items = ['espresso', 'cappuccino', 'latte', 'americano']
    found_items = sum(1 for item in menu_items if item in text_content)
    if found_items >= 2:
        checks.append({"name": "Menu items present", "passed": True, "detail": f"Found {found_items} menu items"})
        score += 15
    else:
        checks.append({"name": "Menu items present", "passed": False, "detail": "Insufficient menu items found"})
    
    # Check for CSS styling
    has_styles = bool(soup.find('style') or soup.find('link', {'rel': 'stylesheet'}) or [tag for tag in soup.find_all() if tag.get('style')])
    if has_styles:
        checks.append({"name": "CSS styling present", "passed": True, "detail": "Found styling elements"})
        score += 20
    else:
        checks.append({"name": "CSS styling present", "passed": False, "detail": "No CSS styling detected"})
    
    passed = score >= 70
    print(json.dumps({"passed": passed, "score": score, "checks": checks}))

if __name__ == '__main__':
    main(sys.argv[1])