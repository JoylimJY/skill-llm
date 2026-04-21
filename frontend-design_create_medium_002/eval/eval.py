import sys
import os
import re
from bs4 import BeautifulSoup

def main():
    workspace_dir = sys.argv[1]
    checks = []
    
    # Check if index.html exists
    html_file = os.path.join(workspace_dir, 'index.html')
    if not os.path.exists(html_file):
        checks.append({"name": "HTML file exists", "passed": False, "detail": "index.html file not found"})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(result)
        return
    
    checks.append({"name": "HTML file exists", "passed": True, "detail": "index.html file found"})
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except:
        checks.append({"name": "HTML file readable", "passed": False, "detail": "Could not read HTML file"})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(result)
        return
    
    checks.append({"name": "HTML file readable", "passed": True, "detail": "HTML file successfully read"})
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check for app name 'GreenMind'
    greenmind_found = bool(re.search(r'greenmind', html_content, re.IGNORECASE))
    checks.append({"name": "App name present", "passed": greenmind_found, "detail": "GreenMind app name found" if greenmind_found else "GreenMind app name not found"})
    
    # Check for tagline
    tagline_found = bool(re.search(r'your plants.*digital caretaker|digital caretaker.*your plants', html_content, re.IGNORECASE))
    checks.append({"name": "Tagline present", "passed": tagline_found, "detail": "Tagline found" if tagline_found else "Required tagline not found"})
    
    # Check for three key features
    smart_watering = bool(re.search(r'smart.*watering.*alert|watering.*alert', html_content, re.IGNORECASE))
    plant_health = bool(re.search(r'plant.*health.*analysis|health.*analysis', html_content, re.IGNORECASE))
    growth_tracking = bool(re.search(r'growth.*tracking', html_content, re.IGNORECASE))
    
    features_count = sum([smart_watering, plant_health, growth_tracking])
    checks.append({"name": "Key features present", "passed": features_count >= 2, "detail": f"Found {features_count}/3 required features"})
    
    # Check for CSS styling
    has_css = bool(soup.find('style')) or bool(re.search(r'<link[^>]*stylesheet', html_content, re.IGNORECASE)) or bool(re.search(r'style\s*=', html_content, re.IGNORECASE))
    checks.append({"name": "CSS styling present", "passed": has_css, "detail": "CSS styling found" if has_css else "No CSS styling detected"})
    
    # Check for animations (CSS or JS)
    has_animations = bool(re.search(r'animation|@keyframes|transition|transform', html_content, re.IGNORECASE))
    checks.append({"name": "Animations present", "passed": has_animations, "detail": "Animation code found" if has_animations else "No animation code detected"})
    
    # Check for distinctive typography (non-default fonts)
    has_custom_fonts = bool(re.search(r'font-family(?!.*system|.*arial|.*helvetica|.*times)', html_content, re.IGNORECASE)) or bool(re.search(r'google.*fonts|fonts\.google|@import.*fonts', html_content, re.IGNORECASE))
    checks.append({"name": "Custom typography", "passed": has_custom_fonts, "detail": "Custom fonts detected" if has_custom_fonts else "Only default fonts detected"})
    
    # Check for color scheme (CSS color properties)
    has_colors = bool(re.search(r'color\s*:|background.*color|background.*gradient', html_content, re.IGNORECASE))
    checks.append({"name": "Color scheme implemented", "passed": has_colors, "detail": "Color styling found" if has_colors else "No color styling detected"})
    
    # Check for proper HTML structure
    has_html_tag = bool(soup.find('html'))
    has_head_tag = bool(soup.find('head'))
    has_body_tag = bool(soup.find('body'))
    proper_structure = has_html_tag and has_head_tag and has_body_tag
    checks.append({"name": "Proper HTML structure", "passed": proper_structure, "detail": "Valid HTML document structure" if proper_structure else "Missing required HTML tags"})
    
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8
    
    result = {"passed": passed, "score": score, "checks": checks}
    print(result)

if __name__ == '__main__':
    main()