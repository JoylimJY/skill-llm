#!/usr/bin/env python3
import sys
import os
import json
import re
from bs4 import BeautifulSoup

def evaluate_task(workspace_dir):
    checks = []
    score = 0.0
    total_checks = 7
    
    # Check 1: Algorithmic philosophy file exists
    philosophy_files = [f for f in os.listdir(workspace_dir) if f.endswith('.md') and 'philosophy' in f.lower()]
    if not philosophy_files:
        philosophy_files = [f for f in os.listdir(workspace_dir) if f.endswith('.md')]
    
    philosophy_exists = len(philosophy_files) > 0
    checks.append({
        "name": "philosophy_file_exists",
        "passed": philosophy_exists,
        "detail": f"Found {len(philosophy_files)} philosophy file(s)" if philosophy_exists else "No philosophy markdown file found"
    })
    if philosophy_exists:
        score += 1.0
    
    # Check 2: Philosophy content quality and quantum theme
    philosophy_quality = False
    quantum_theme = False
    if philosophy_exists:
        with open(os.path.join(workspace_dir, philosophy_files[0]), 'r', encoding='utf-8') as f:
            philosophy_content = f.read().lower()
            
        # Check for quantum-related terms
        quantum_terms = ['quantum', 'entanglement', 'particle', 'measurement', 'superposition', 'coherence', 'decoherence']
        quantum_matches = sum(1 for term in quantum_terms if term in philosophy_content)
        quantum_theme = quantum_matches >= 3
        
        # Check for algorithmic art concepts
        algo_terms = ['algorithmic', 'generative', 'computational', 'parametric', 'emergent', 'noise', 'seeded']
        algo_matches = sum(1 for term in algo_terms if term in philosophy_content)
        philosophy_quality = algo_matches >= 4 and len(philosophy_content) > 1000
    
    checks.append({
        "name": "quantum_theme_in_philosophy",
        "passed": quantum_theme,
        "detail": "Philosophy addresses quantum entanglement concepts" if quantum_theme else "Philosophy lacks quantum mechanics theme"
    })
    if quantum_theme:
        score += 1.0
        
    checks.append({
        "name": "philosophy_quality",
        "passed": philosophy_quality,
        "detail": "Philosophy demonstrates algorithmic art understanding" if philosophy_quality else "Philosophy lacks depth or algorithmic focus"
    })
    if philosophy_quality:
        score += 1.0
    
    # Check 3: HTML artifact exists
    html_files = [f for f in os.listdir(workspace_dir) if f.endswith('.html')]
    html_exists = len(html_files) > 0
    checks.append({
        "name": "html_artifact_exists",
        "passed": html_exists,
        "detail": f"Found {len(html_files)} HTML file(s)" if html_exists else "No HTML artifact found"
    })
    if html_exists:
        score += 1.0
    
    # Check 4: HTML structure and p5.js integration
    html_structure = False
    p5js_integration = False
    if html_exists:
        with open(os.path.join(workspace_dir, html_files[0]), 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for p5.js CDN
        p5js_scripts = soup.find_all('script', src=re.compile(r'p5\.js'))
        p5js_integration = len(p5js_scripts) > 0
        
        # Check for essential HTML structure
        has_sidebar = soup.find('div', class_=re.compile(r'sidebar'))
        has_canvas_container = soup.find('div', id=re.compile(r'container|canvas'))
        html_structure = has_sidebar is not None and has_canvas_container is not None
    
    checks.append({
        "name": "html_structure_valid",
        "passed": html_structure,
        "detail": "HTML has proper sidebar and canvas structure" if html_structure else "HTML missing required structure elements"
    })
    if html_structure:
        score += 1.0
        
    checks.append({
        "name": "p5js_integration",
        "passed": p5js_integration,
        "detail": "p5.js library properly integrated" if p5js_integration else "p5.js CDN not found in HTML"
    })
    if p5js_integration:
        score += 1.0
    
    # Check 5: Quantum-themed algorithm implementation
    quantum_algorithm = False
    interactive_params = False
    if html_exists:
        # Look for quantum/particle-related code
        quantum_code_terms = ['particle', 'entangl', 'quantum', 'pair', 'correlation', 'measurement', 'spin', 'state']
        quantum_code_matches = sum(1 for term in quantum_code_terms if term.lower() in html_content.lower())
        quantum_algorithm = quantum_code_matches >= 2
        
        # Check for interactive parameters
        param_indicators = ['input type="range"', 'slider', 'updateParam', 'oninput', 'params.']
        param_matches = sum(1 for indicator in param_indicators if indicator in html_content)
        interactive_params = param_matches >= 3
    
    checks.append({
        "name": "quantum_algorithm_implementation",
        "passed": quantum_algorithm,
        "detail": "Algorithm implements quantum/particle concepts" if quantum_algorithm else "Algorithm lacks quantum mechanics implementation"
    })
    if quantum_algorithm:
        score += 1.0
        
    checks.append({
        "name": "interactive_parameters",
        "passed": interactive_params,
        "detail": "Interactive parameter controls implemented" if interactive_params else "Missing interactive parameter system"
    })
    if interactive_params:
        score += 1.0
    
    # Calculate final score
    final_score = score / total_checks
    passed = final_score >= 0.7  # Need to pass at least 70% of checks
    
    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python eval_script.py <workspace_directory>")
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = evaluate_task(workspace_dir)
    print(json.dumps(result))