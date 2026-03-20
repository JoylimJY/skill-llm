#!/usr/bin/env python3
import sys
import os
import json
from bs4 import BeautifulSoup

def evaluate_task(workspace_dir):
    checks = []
    
    # Check if algorithmic philosophy markdown file exists
    philosophy_files = [f for f in os.listdir(workspace_dir) if f.endswith('.md') and 'philosophy' in f.lower()]
    if not philosophy_files:
        philosophy_files = [f for f in os.listdir(workspace_dir) if f.endswith('.md')]
    
    philosophy_exists = len(philosophy_files) > 0
    checks.append({
        'name': 'algorithmic_philosophy_exists',
        'passed': philosophy_exists,
        'detail': f'Found {len(philosophy_files)} markdown philosophy files'
    })
    
    # Check if HTML artifact exists
    html_files = [f for f in os.listdir(workspace_dir) if f.endswith('.html')]
    html_exists = len(html_files) > 0
    checks.append({
        'name': 'html_artifact_exists', 
        'passed': html_exists,
        'detail': f'Found {len(html_files)} HTML files'
    })
    
    html_content = ''
    if html_files:
        with open(os.path.join(workspace_dir, html_files[0]), 'r', encoding='utf-8') as f:
            html_content = f.read()
    
    # Parse HTML and check for required components
    soup = BeautifulSoup(html_content, 'html.parser') if html_content else None
    
    # Check for p5.js CDN inclusion
    p5_included = 'p5.js' in html_content and 'cdnjs.cloudflare.com' in html_content
    checks.append({
        'name': 'p5js_cdn_included',
        'passed': p5_included,
        'detail': 'p5.js CDN link found' if p5_included else 'p5.js CDN link missing'
    })
    
    # Check for seeded randomness
    has_seed = 'randomSeed' in html_content or 'noiseSeed' in html_content
    checks.append({
        'name': 'seeded_randomness',
        'passed': has_seed,
        'detail': 'Seeded randomness implementation found' if has_seed else 'Seeded randomness missing'
    })
    
    # Check for particle system (based on user request)
    has_particles = any(word in html_content.lower() for word in ['particle', 'particles', 'flowing', 'flow'])
    checks.append({
        'name': 'particle_system',
        'passed': has_particles,
        'detail': 'Particle system implementation found' if has_particles else 'Particle system not detected'
    })
    
    # Check for interactive parameters
    has_controls = 'input' in html_content and ('range' in html_content or 'slider' in html_content)
    checks.append({
        'name': 'interactive_parameters',
        'passed': has_controls,
        'detail': 'Interactive parameter controls found' if has_controls else 'Interactive controls missing'
    })
    
    # Check for seed navigation buttons
    has_seed_nav = all(word in html_content.lower() for word in ['prev', 'next', 'random'])
    checks.append({
        'name': 'seed_navigation',
        'passed': has_seed_nav,
        'detail': 'Seed navigation buttons found' if has_seed_nav else 'Seed navigation incomplete'
    })
    
    # Check for self-contained structure
    is_self_contained = '<script>' in html_content and 'setup()' in html_content and 'draw()' in html_content
    checks.append({
        'name': 'self_contained_artifact',
        'passed': is_self_contained,
        'detail': 'Self-contained p5.js code found' if is_self_contained else 'p5.js code structure missing'
    })
    
    # Check philosophy content quality (basic)
    philosophy_quality = False
    if philosophy_files:
        with open(os.path.join(workspace_dir, philosophy_files[0]), 'r', encoding='utf-8') as f:
            philosophy_content = f.read()
            # Look for algorithmic/computational terms
            key_terms = ['algorithm', 'particle', 'noise', 'flow', 'emergent', 'generative']
            philosophy_quality = sum(1 for term in key_terms if term.lower() in philosophy_content.lower()) >= 3
    
    checks.append({
        'name': 'philosophy_quality',
        'passed': philosophy_quality,
        'detail': 'Algorithmic philosophy contains relevant computational concepts' if philosophy_quality else 'Philosophy lacks algorithmic focus'
    })
    
    passed_checks = sum(1 for check in checks if check['passed'])
    score = passed_checks / len(checks)
    
    return {
        'passed': score >= 0.7,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_dir>')
        sys.exit(1)
    
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result, indent=2))