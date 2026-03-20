#!/usr/bin/env python3
import sys
import os
import json
from bs4 import BeautifulSoup
import re

def eval_task(workspace_dir):
    checks = []
    score = 0.0
    
    # Check 1: Algorithmic philosophy .md file exists
    md_files = [f for f in os.listdir(workspace_dir) if f.endswith('.md')]
    philosophy_exists = len(md_files) > 0
    checks.append({
        "name": "algorithmic_philosophy_exists",
        "passed": philosophy_exists,
        "detail": f"Found {len(md_files)} .md files" if philosophy_exists else "No .md philosophy file found"
    })
    if philosophy_exists: score += 0.2
    
    # Check 2: Philosophy content quality
    philosophy_quality = False
    if philosophy_exists:
        with open(os.path.join(workspace_dir, md_files[0]), 'r') as f:
            content = f.read().lower()
            # Check for key algorithmic concepts
            has_algorithmic = any(word in content for word in ['algorithm', 'computational', 'generative', 'emergence'])
            has_urban_decay = any(word in content for word in ['urban', 'decay', 'erosion', 'weathering', 'cities', 'structures'])
            has_craftsmanship = any(phrase in content for phrase in ['meticulously', 'refined', 'expertise', 'crafted', 'master'])
            philosophy_quality = has_algorithmic and has_urban_decay and has_craftsmanship
    
    checks.append({
        "name": "philosophy_quality",
        "passed": philosophy_quality,
        "detail": "Philosophy contains algorithmic concepts, urban decay themes, and craftsmanship emphasis" if philosophy_quality else "Philosophy missing key elements"
    })
    if philosophy_quality: score += 0.3
    
    # Check 3: HTML artifact exists
    html_files = [f for f in os.listdir(workspace_dir) if f.endswith('.html')]
    html_exists = len(html_files) > 0
    checks.append({
        "name": "html_artifact_exists",
        "passed": html_exists,
        "detail": f"Found {len(html_files)} HTML files" if html_exists else "No HTML artifact found"
    })
    if html_exists: score += 0.2
    
    # Check 4: HTML uses template structure
    template_structure = False
    anthropic_branding = False
    if html_exists:
        with open(os.path.join(workspace_dir, html_files[0]), 'r') as f:
            html_content = f.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check for template marker
            template_structure = 'TEMPLATE MARKER: viewer_template_v1.0' in html_content or 'Algorithmic Art' in html_content
            
            # Check for Anthropic branding elements
            has_poppins = 'Poppins' in html_content
            has_sidebar = soup.find('div', class_='sidebar') is not None
            has_seed_section = 'seed-display' in html_content
            anthropic_branding = has_poppins and has_sidebar and has_seed_section
    
    checks.append({
        "name": "template_structure",
        "passed": template_structure,
        "detail": "HTML uses required template structure" if template_structure else "HTML does not use template structure"
    })
    if template_structure: score += 0.1
    
    checks.append({
        "name": "anthropic_branding",
        "passed": anthropic_branding,
        "detail": "Contains Anthropic fonts, sidebar, and seed controls" if anthropic_branding else "Missing required UI elements"
    })
    if anthropic_branding: score += 0.1
    
    # Check 5: P5.js algorithm implementation
    p5js_algorithm = False
    seeded_randomness = False
    if html_exists:
        # Check for p5.js functions and urban decay concepts
        setup_function = 'function setup()' in html_content
        draw_function = 'function draw()' in html_content
        p5js_cdn = 'p5.js' in html_content and 'cdnjs.cloudflare.com' in html_content
        p5js_algorithm = setup_function and draw_function and p5js_cdn
        
        # Check for seeded randomness
        seeded_randomness = 'randomSeed(' in html_content and 'noiseSeed(' in html_content
    
    checks.append({
        "name": "p5js_algorithm",
        "passed": p5js_algorithm,
        "detail": "Contains p5.js setup/draw functions and CDN" if p5js_algorithm else "Missing p5.js algorithm structure"
    })
    if p5js_algorithm: score += 0.1
    
    checks.append({
        "name": "seeded_randomness",
        "passed": seeded_randomness,
        "detail": "Implements seeded randomness with randomSeed/noiseSeed" if seeded_randomness else "Missing seeded randomness implementation"
    })
    if seeded_randomness: score += 0.1
    
    passed = score >= 0.7
    
    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: eval_script.py <workspace_dir>"}))
        sys.exit(1)
    
    result = eval_task(sys.argv[1])
    print(json.dumps(result))