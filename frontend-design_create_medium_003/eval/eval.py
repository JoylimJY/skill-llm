import sys
import os
import json
from bs4 import BeautifulSoup
import re

def evaluate_portfolio(workspace_dir):
    checks = []
    
    # Check if HTML file exists
    html_files = [f for f in os.listdir(workspace_dir) if f.endswith('.html')]
    if not html_files:
        checks.append({"name": "HTML file exists", "passed": False, "detail": "No HTML file found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    html_file = None
    for file in html_files:
        if 'portfolio' in file.lower():
            html_file = file
            break
    if not html_file:
        html_file = html_files[0]
    
    checks.append({"name": "HTML file exists", "passed": True, "detail": f"Found HTML file: {html_file}"})
    
    # Read and parse HTML content
    try:
        with open(os.path.join(workspace_dir, html_file), 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')
    except Exception as e:
        checks.append({"name": "HTML parsing", "passed": False, "detail": f"Failed to parse HTML: {str(e)}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "HTML parsing", "passed": True, "detail": "HTML successfully parsed"})
    
    # Check for agency name
    text_content = soup.get_text().lower()
    agency_name_found = any(phrase in text_content for phrase in ['nexus creative', 'nexus', 'creative'])
    checks.append({"name": "Agency name present", "passed": agency_name_found, "detail": "Found agency name reference" if agency_name_found else "Agency name not found"})
    
    # Check for tagline
    tagline_found = any(phrase in text_content for phrase in ['shaping tomorrow', 'tomorrow\'s stories', 'shaping', 'stories'])
    checks.append({"name": "Tagline present", "passed": tagline_found, "detail": "Found tagline reference" if tagline_found else "Tagline not found"})
    
    # Check for services
    services = ['brand strategy', 'digital experiences', 'creative direction']
    services_found = sum(1 for service in services if any(keyword in text_content for keyword in service.split()))
    services_check_passed = services_found >= 2
    checks.append({"name": "Services section", "passed": services_check_passed, "detail": f"Found {services_found}/3 services mentioned"})
    
    # Check for contact email
    email_found = 'hello@nexuscreative.com' in text_content or 'nexuscreative' in text_content or 'hello@' in text_content
    checks.append({"name": "Contact email present", "passed": email_found, "detail": "Found contact email" if email_found else "Contact email not found"})
    
    # Check for CSS styling (embedded or external)
    has_css = bool(soup.find('style') or soup.find('link', rel='stylesheet') or 'style=' in html_content)
    checks.append({"name": "CSS styling present", "passed": has_css, "detail": "Found CSS styling" if has_css else "No CSS styling detected"})
    
    # Check for JavaScript (for animations)
    has_js = bool(soup.find('script') or 'javascript' in html_content.lower())
    checks.append({"name": "JavaScript present", "passed": has_js, "detail": "Found JavaScript" if has_js else "No JavaScript detected"})
    
    # Check for creative typography (custom fonts)
    font_indicators = ['font-family', 'google fonts', 'typeface', '@import', 'font-face']
    has_custom_fonts = any(indicator in html_content.lower() for indicator in font_indicators)
    checks.append({"name": "Custom typography", "passed": has_custom_fonts, "detail": "Found custom font references" if has_custom_fonts else "No custom fonts detected"})
    
    # Check for animations/transitions
    animation_keywords = ['animation', 'transition', 'transform', '@keyframes', 'hover', 'ease']
    has_animations = any(keyword in html_content.lower() for keyword in animation_keywords)
    checks.append({"name": "Animations/transitions", "passed": has_animations, "detail": "Found animation/transition code" if has_animations else "No animations detected"})
    
    # Check for color scheme (CSS color properties)
    color_indicators = ['background-color', 'color:', 'rgb(', 'rgba(', 'hsl(', '#', 'gradient']
    has_colors = any(indicator in html_content.lower() for indicator in color_indicators)
    checks.append({"name": "Color scheme", "passed": has_colors, "detail": "Found color styling" if has_colors else "No color scheme detected"})
    
    # Calculate score and overall pass
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.8
    
    return {"passed": passed, "score": score, "checks": checks}

if __name__ == '__main__':
    workspace_dir = sys.argv[1]
    result = evaluate_portfolio(workspace_dir)
    print(json.dumps(result))