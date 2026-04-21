#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Check 1: HTML file exists with correct name
    html_path = os.path.join(workspace_dir, 'erosion-art.html')
    html_exists = os.path.isfile(html_path)
    checks.append({
        "name": "HTML file exists with correct filename",
        "passed": html_exists,
        "detail": f"File 'erosion-art.html' found" if html_exists else "File 'erosion-art.html' not found"
    })
    
    if not html_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    
    # Read HTML content
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read().lower()
    
    # Check 2: Contains p5.js
    has_p5 = 'p5.js' in html_content or 'p5.min.js' in html_content
    checks.append({
        "name": "p5.js library included",
        "passed": has_p5,
        "detail": "p5.js CDN or library found" if has_p5 else "p5.js not found"
    })
    
    # Check 3: Contains seeded randomness
    has_seed = 'randomseed' in html_content or 'noiseseed' in html_content or 'seed' in html_content
    checks.append({
        "name": "Seeded randomness implemented",
        "passed": has_seed,
        "detail": "randomSeed or noiseSeed found" if has_seed else "No seeded randomness detected"
    })
    
    # Check 4: Contains parameter controls
    has_params = 'parameter' in html_content or 'slider' in html_content or 'input type="range"' in html_content
    checks.append({
        "name": "Parameter controls present",
        "passed": has_params,
        "detail": "Parameter controls or sliders found" if has_params else "No parameter controls detected"
    })
    
    # Check 5: Contains seed navigation
    has_seed_nav = any(keyword in html_content for keyword in ['previous', 'next', 'random', 'seed'])
    checks.append({
        "name": "Seed navigation controls",
        "passed": has_seed_nav,
        "detail": "Seed navigation buttons found" if has_seed_nav else "No seed navigation detected"
    })
    
    # Check 6: Contains regenerate button
    has_regenerate = 'regenerate' in html_content or 'regen' in html_content
    checks.append({
        "name": "Regenerate button present",
        "passed": has_regenerate,
        "detail": "Regenerate button found" if has_regenerate else "Regenerate button not found"
    })
    
    # Check 7: Contains reset button
    has_reset = 'reset' in html_content
    checks.append({
        "name": "Reset button present",
        "passed": has_reset,
        "detail": "Reset button found" if has_reset else "Reset button not found"
    })
    
    # Check 8: Contains setup and draw functions
    has_setup_draw = 'function setup' in html_content and 'function draw' in html_content
    checks.append({
        "name": "p5.js setup and draw functions",
        "passed": has_setup_draw,
        "detail": "Both setup() and draw() functions found" if has_setup_draw else "Missing setup() or draw() function"
    })
    
    # Check 9: Contains canvas creation
    has_canvas = 'createcanvas' in html_content
    checks.append({
        "name": "Canvas creation",
        "passed": has_canvas,
        "detail": "createCanvas() call found" if has_canvas else "No canvas creation detected"
    })
    
    # Check 10: Self-contained (no external file imports except p5.js)
    has_external_imports = bool(re.search(r'<script\s+src=["\'](?!.*p5)', html_content))
    is_self_contained = not has_external_imports or 'p5.js' in html_content
    checks.append({
        "name": "Self-contained artifact",
        "passed": is_self_contained,
        "detail": "HTML is self-contained with inline scripts" if is_self_contained else "External dependencies detected"
    })
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    score = passed_count / len(checks)
    
    return {
        "passed": score >= 0.8,
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    result = evaluate(workspace)
    print(json.dumps(result))
