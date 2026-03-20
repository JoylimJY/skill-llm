#!/usr/bin/env python3
import sys
import os
import json
from bs4 import BeautifulSoup
import re

def eval_task(workspace_dir):
    checks = []
    score = 0.0
    
    # Check for philosophy markdown file
    philosophy_files = [f for f in os.listdir(workspace_dir) if f.endswith('.md')]
    philosophy_exists = len(philosophy_files) > 0
    checks.append({
        "name": "philosophy_file_exists",
        "passed": philosophy_exists,
        "detail": f"Found {len(philosophy_files)} .md files" if philosophy_exists else "No philosophy .md file found"
    })
    if philosophy_exists:
        score += 0.2
    
    # Check philosophy content if exists
    if philosophy_exists:
        with open(os.path.join(workspace_dir, philosophy_files[0]), 'r', encoding='utf-8') as f:
            philosophy_content = f.read()
        
        # Check for algorithmic concepts
        algorithmic_terms = ['algorithm', 'computational', 'generative', 'emergence', 'parameter']
        found_terms = sum(1 for term in algorithmic_terms if term.lower() in philosophy_content.lower())
        algorithmic_focus = found_terms >= 3
        checks.append({
            "name": "philosophy_algorithmic_focus",
            "passed": algorithmic_focus,
            "detail": f"Found {found_terms}/5 key algorithmic terms"
        })
        if algorithmic_focus:
            score += 0.15
        
        # Check for neural/network concepts
        neural_terms = ['neural', 'synap', 'connection', 'network', 'plasticity', 'brain']
        neural_found = sum(1 for term in neural_terms if term.lower() in philosophy_content.lower())
        neural_focus = neural_found >= 2
        checks.append({
            "name": "philosophy_neural_concepts",
            "passed": neural_focus,
            "detail": f"Found {neural_found}/6 neural/network terms"
        })
        if neural_focus:
            score += 0.15
    
    # Check for HTML artifact
    html_files = [f for f in os.listdir(workspace_dir) if f.endswith('.html')]
    html_exists = len(html_files) > 0
    checks.append({
        "name": "html_artifact_exists",
        "passed": html_exists,
        "detail": f"Found {len(html_files)} .html files" if html_exists else "No HTML artifact found"
    })
    if html_exists:
        score += 0.2
    
    if html_exists:
        with open(os.path.join(workspace_dir, html_files[0]), 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for p5.js CDN
        p5_script = soup.find('script', src=re.compile(r'p5\.js'))
        has_p5 = p5_script is not None
        checks.append({
            "name": "p5js_included",
            "passed": has_p5,
            "detail": "p5.js CDN found" if has_p5 else "p5.js CDN not found"
        })
        if has_p5:
            score += 0.1
        
        # Check for seed controls
        has_seed_controls = 'seed' in html_content.lower() and ('prev' in html_content.lower() or 'next' in html_content.lower())
        checks.append({
            "name": "seed_controls_present",
            "passed": has_seed_controls,
            "detail": "Seed navigation controls found" if has_seed_controls else "Missing seed controls"
        })
        if has_seed_controls:
            score += 0.1
        
        # Check for parameter controls
        has_sliders = 'type="range"' in html_content or 'input' in html_content.lower()
        checks.append({
            "name": "parameter_controls_present",
            "passed": has_sliders,
            "detail": "Parameter controls found" if has_sliders else "No parameter controls found"
        })
        if has_sliders:
            score += 0.1
        
        # Check for p5.js functions
        has_setup = 'function setup()' in html_content
        has_draw = 'function draw()' in html_content or 'draw =' in html_content
        p5_structure = has_setup and has_draw
        checks.append({
            "name": "p5js_structure",
            "passed": p5_structure,
            "detail": "setup() and draw() functions found" if p5_structure else "Missing p5.js structure"
        })
        if p5_structure:
            score += 0.1
        
        # Check for seeded randomness
        has_seeded_random = 'randomSeed' in html_content or 'noiseSeed' in html_content
        checks.append({
            "name": "seeded_randomness",
            "passed": has_seeded_random,
            "detail": "Seeded randomness implemented" if has_seeded_random else "No seeded randomness found"
        })
        if has_seeded_random:
            score += 0.05
        
        # Check for neural/network implementation concepts
        neural_impl_terms = ['particle', 'node', 'connection', 'line', 'vertex', 'edge', 'network']
        impl_found = sum(1 for term in neural_impl_terms if term.lower() in html_content.lower())
        neural_implementation = impl_found >= 2
        checks.append({
            "name": "neural_network_implementation",
            "passed": neural_implementation,
            "detail": f"Found {impl_found}/7 network implementation terms"
        })
        if neural_implementation:
            score += 0.05
    
    # Overall assessment
    passed = score >= 0.7  # Need 70% to pass
    
    return {
        "passed": passed,
        "score": round(score, 2),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: eval_script.py <workspace_dir>"}))
        sys.exit(1)
    
    result = eval_task(sys.argv[1])
    print(json.dumps(result))