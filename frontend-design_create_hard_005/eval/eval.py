import sys
import os
import re
import json
from pathlib import Path
from bs4 import BeautifulSoup

def main(workspace_dir):
    checks = []
    os.chdir(workspace_dir)
    
    # Check 1: index.html exists and has proper structure
    index_exists = os.path.exists('index.html')
    checks.append({
        "name": "index_html_exists",
        "passed": index_exists,
        "detail": "index.html file found" if index_exists else "index.html file missing"
    })
    
    # Check 2: README.md exists with design explanation
    readme_exists = os.path.exists('README.md')
    design_concept_explained = False
    if readme_exists:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read().lower()
            design_keywords = ['design', 'aesthetic', 'concept', 'style', 'visual', 'art', 'digital']
            design_concept_explained = any(keyword in readme_content for keyword in design_keywords)
    
    checks.append({
        "name": "readme_with_design_concept",
        "passed": readme_exists and design_concept_explained,
        "detail": "README.md exists with design concept explanation" if readme_exists and design_concept_explained else "README.md missing or lacks design concept explanation"
    })
    
    # Check 3: Multiple page structure (at least 4 pages)
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    page_keywords = ['about', 'gallery', 'contact']
    additional_pages = 0
    
    for html_file in html_files:
        if html_file != 'index.html':
            filename_lower = html_file.lower()
            if any(keyword in filename_lower for keyword in page_keywords):
                additional_pages += 1
    
    # Also check if pages are referenced in index.html
    navigation_links = 0
    if index_exists:
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                links = soup.find_all('a')
                for link in links:
                    href = link.get('href', '').lower()
                    if any(keyword in href for keyword in page_keywords):
                        navigation_links += 1
        except:
            pass
    
    multi_page_structure = additional_pages >= 3 or navigation_links >= 3
    checks.append({
        "name": "multi_page_structure",
        "passed": multi_page_structure,
        "detail": f"Found {additional_pages} additional pages and {navigation_links} navigation links" if multi_page_structure else "Insufficient multi-page structure"
    })
    
    # Check 4: Artist name and digital art context present
    alex_rivera_mentioned = False
    digital_art_context = False
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                if 'alex rivera' in content or 'rivera' in content:
                    alex_rivera_mentioned = True
                art_keywords = ['digital art', 'generative', 'installation', 'interactive', 'algorithm', 'sculpture']
                if any(keyword in content for keyword in art_keywords):
                    digital_art_context = True
        except:
            continue
    
    checks.append({
        "name": "artist_identity_and_context",
        "passed": alex_rivera_mentioned and digital_art_context,
        "detail": "Artist name and digital art context found" if alex_rivera_mentioned and digital_art_context else "Missing artist identity or digital art context"
    })
    
    # Check 5: Gallery with artwork display
    gallery_artwork_count = 0
    gallery_found = False
    
    for html_file in html_files:
        if 'gallery' in html_file.lower():
            gallery_found = True
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    # Count potential artwork entries by looking for titles and descriptions
                    title_patterns = content.count('title') + content.count('piece') + content.count('work')
                    if title_patterns >= 6:
                        gallery_artwork_count = title_patterns
            except:
                continue
    
    # Also check if gallery content is in index.html
    if not gallery_found and index_exists:
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                content = f.read().lower()
                if 'gallery' in content or 'portfolio' in content:
                    title_patterns = content.count('title') + content.count('piece') + content.count('work')
                    if title_patterns >= 6:
                        gallery_artwork_count = title_patterns
                        gallery_found = True
        except:
            pass
    
    checks.append({
        "name": "gallery_with_artworks",
        "passed": gallery_found and gallery_artwork_count >= 6,
        "detail": f"Gallery found with {gallery_artwork_count} artwork references" if gallery_found else "Gallery section not found or insufficient artworks"
    })
    
    # Check 6: Contact form or contact information
    contact_found = False
    contact_form_or_info = False
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                content_text = soup.get_text().lower()
                
                if 'contact' in content_text:
                    contact_found = True
                    # Check for form elements or contact information
                    forms = soup.find_all('form')
                    inputs = soup.find_all('input')
                    email_patterns = re.findall(r'\b[a-za-z0-9._%+-]+@[a-za-z0-9.-]+\.[a-z]{2,}\b', content_text)
                    social_keywords = ['twitter', 'instagram', 'linkedin', 'social']
                    social_mentions = any(keyword in content_text for keyword in social_keywords)
                    
                    if forms or len(inputs) >= 3 or email_patterns or social_mentions:
                        contact_form_or_info = True
        except:
            continue
    
    checks.append({
        "name": "contact_functionality",
        "passed": contact_found and contact_form_or_info,
        "detail": "Contact section with form or information found" if contact_found and contact_form_or_info else "Contact functionality missing or incomplete"
    })
    
    # Check 7: Distinctive visual design (CSS and aesthetic elements)
    distinctive_design = False
    design_complexity = 0
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                
                # Look for CSS indicators of distinctive design
                css_indicators = [
                    'gradient', 'animation', 'transform', 'transition', 'keyframes',
                    'backdrop-filter', 'filter', 'shadow', 'rgba', 'hsla',
                    'flex', 'grid', 'position', 'z-index', 'overflow',
                    'font-family', 'font-weight', 'line-height', 'letter-spacing'
                ]
                
                for indicator in css_indicators:
                    if indicator in content:
                        design_complexity += 1
                
                # Look for custom fonts (not generic ones)
                generic_fonts = ['arial', 'helvetica', 'times', 'courier', 'serif', 'sans-serif']
                font_family_matches = re.findall(r'font-family[^;]+', content)
                has_custom_fonts = False
                for match in font_family_matches:
                    if not any(generic in match.lower() for generic in generic_fonts):
                        has_custom_fonts = True
                        break
                
                if design_complexity >= 8 or has_custom_fonts:
                    distinctive_design = True
        except:
            continue
    
    checks.append({
        "name": "distinctive_visual_design",
        "passed": distinctive_design,
        "detail": f"Distinctive design elements found (complexity score: {design_complexity})" if distinctive_design else "Generic or minimal design detected"
    })
    
    # Check 8: Functional navigation and structure
    functional_navigation = False
    
    if index_exists:
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                
                # Check for navigation elements
                nav_elements = soup.find_all(['nav', 'header']) + soup.find_all(attrs={'class': re.compile(r'nav', re.I)})
                links = soup.find_all('a')
                
                # Check for proper HTML structure
                has_title = bool(soup.find('title'))
                has_meta = bool(soup.find('meta'))
                has_body = bool(soup.find('body'))
                
                if (nav_elements or len(links) >= 3) and has_title and has_body:
                    functional_navigation = True
        except:
            pass
    
    checks.append({
        "name": "functional_navigation_structure",
        "passed": functional_navigation,
        "detail": "Functional navigation and HTML structure found" if functional_navigation else "Navigation or HTML structure issues detected"
    })
    
    # Calculate final score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    overall_passed = score >= 0.8
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "error", "passed": False, "detail": "Usage: python eval_script.py <workspace_dir>"}]}))
    else:
        main(sys.argv[1])