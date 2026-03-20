#!/usr/bin/env python3
import sys
import os
import json
import re
from bs4 import BeautifulSoup

def evaluate_landing_page(workspace_dir):
    checks = []
    passed_count = 0
    total_checks = 0
    
    # Check if HTML file exists
    html_files = [f for f in os.listdir(workspace_dir) if f.endswith('.html')]
    total_checks += 1
    if html_files:
        checks.append({"name": "HTML file exists", "passed": True, "detail": f"Found {len(html_files)} HTML file(s)"})
        passed_count += 1
        html_file = html_files[0]  # Use first HTML file found
    else:
        checks.append({"name": "HTML file exists", "passed": False, "detail": "No HTML file found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Read and parse HTML content
    try:
        with open(os.path.join(workspace_dir, html_file), 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        checks.append({"name": "HTML parsing", "passed": False, "detail": f"Failed to parse HTML: {str(e)}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Check for basic HTML structure
    total_checks += 1
    if soup.find('html') and soup.find('head') and soup.find('body'):
        checks.append({"name": "Basic HTML structure", "passed": True, "detail": "HTML, head, and body tags present"})
        passed_count += 1
    else:
        checks.append({"name": "Basic HTML structure", "passed": False, "detail": "Missing basic HTML structure"})
    
    # Check for coffee roastery branding (Ember & Oak)
    total_checks += 1
    text_content = soup.get_text().lower()
    if 'ember' in text_content and 'oak' in text_content:
        checks.append({"name": "Brand name present", "passed": True, "detail": "Ember & Oak branding found in content"})
        passed_count += 1
    else:
        checks.append({"name": "Brand name present", "passed": False, "detail": "Ember & Oak branding not found"})
    
    # Check for coffee/roastery related content
    total_checks += 1
    coffee_keywords = ['coffee', 'roast', 'bean', 'brew', 'artisan', 'craft', 'batch']
    found_keywords = [kw for kw in coffee_keywords if kw in text_content]
    if found_keywords:
        checks.append({"name": "Coffee-related content", "passed": True, "detail": f"Found keywords: {', '.join(found_keywords)}"})
        passed_count += 1
    else:
        checks.append({"name": "Coffee-related content", "passed": False, "detail": "No coffee-related keywords found"})
    
    # Check for CSS styling (inline or external)
    total_checks += 1
    has_styling = False
    if soup.find('style') or soup.find('link', rel='stylesheet') or soup.find(attrs={'style': True}):
        has_styling = True
        checks.append({"name": "CSS styling present", "passed": True, "detail": "Found CSS styling"})
        passed_count += 1
    else:
        checks.append({"name": "CSS styling present", "passed": False, "detail": "No CSS styling found"})
    
    # Check for contact information section
    total_checks += 1
    contact_indicators = ['contact', 'email', 'phone', 'address', 'touch', 'reach']
    found_contact = any(indicator in text_content for indicator in contact_indicators)
    if found_contact:
        checks.append({"name": "Contact information section", "passed": True, "detail": "Contact section or information found"})
        passed_count += 1
    else:
        checks.append({"name": "Contact information section", "passed": False, "detail": "No contact information found"})
    
    # Check for hero/header section indicators
    total_checks += 1
    hero_indicators = soup.find_all(['h1', 'header', 'hero']) or soup.find_all(attrs={'class': re.compile(r'hero|header|banner', re.I)})
    if hero_indicators or soup.find('h1'):
        checks.append({"name": "Hero/header section", "passed": True, "detail": "Found hero section or main heading"})
        passed_count += 1
    else:
        checks.append({"name": "Hero/header section", "passed": False, "detail": "No clear hero section or main heading found"})
    
    # Calculate final score
    score = passed_count / total_checks if total_checks > 0 else 0.0
    passed = score >= 0.7  # Need 70% of checks to pass
    
    return {
        "passed": passed,
        "score": round(score, 2),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Arguments", "passed": False, "detail": "Expected workspace directory argument"}]}))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = evaluate_landing_page(workspace_dir)
    print(json.dumps(result))