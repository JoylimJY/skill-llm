import os
import sys
import json
import re
from pathlib import Path

def evaluate_task(workspace_dir):
    checks = []
    workspace_path = Path(workspace_dir)
    
    # Check 1: Design philosophy MD file exists and has content
    philosophy_files = list(workspace_path.glob('*.md'))
    philosophy_found = False
    philosophy_content = ""
    
    for md_file in philosophy_files:
        try:
            content = md_file.read_text(encoding='utf-8').lower()
            if any(keyword in content for keyword in ['philosophy', 'aesthetic', 'visual', 'design', 'movement']):
                philosophy_found = True
                philosophy_content = content
                break
        except:
            continue
    
    checks.append({
        "name": "Design Philosophy File Created",
        "passed": philosophy_found,
        "detail": f"Found design philosophy in MD file: {philosophy_found}"
    })
    
    # Check 2: Philosophy mentions spatial/architectural concepts
    spatial_concepts = philosophy_found and any(keyword in philosophy_content for keyword in ['space', 'spatial', 'architecture', 'structure', 'geometric', 'form'])
    
    checks.append({
        "name": "Philosophy Contains Spatial Concepts",
        "passed": spatial_concepts,
        "detail": f"Philosophy discusses spatial/architectural elements: {spatial_concepts}"
    })
    
    # Check 3: Philosophy emphasizes visual expression over text
    visual_emphasis = philosophy_found and any(phrase in philosophy_content for phrase in ['minimal text', 'visual', 'express', 'design', 'craftsmanship', 'expert'])
    
    checks.append({
        "name": "Philosophy Emphasizes Visual Expression",
        "passed": visual_emphasis,
        "detail": f"Philosophy prioritizes visual over textual communication: {visual_emphasis}"
    })
    
    # Check 4: PDF poster file exists
    pdf_files = list(workspace_path.glob('*.pdf'))
    poster_found = len(pdf_files) > 0
    target_filename = any('synaptic' in str(pdf_file).lower() and 'architecture' in str(pdf_file).lower() for pdf_file in pdf_files)
    
    checks.append({
        "name": "PDF Poster File Created",
        "passed": poster_found,
        "detail": f"PDF file created: {poster_found}, target filename used: {target_filename}"
    })
    
    # Check 5: PDF file is substantial (not empty)
    pdf_substantial = False
    if pdf_files:
        try:
            largest_pdf = max(pdf_files, key=lambda f: f.stat().st_size)
            pdf_substantial = largest_pdf.stat().st_size > 5000  # At least 5KB
        except:
            pass
    
    checks.append({
        "name": "PDF Contains Substantial Content",
        "passed": pdf_substantial,
        "detail": f"PDF file has substantial content (>5KB): {pdf_substantial}"
    })
    
    # Check 6: Neural/synaptic concept integration (check for related terms in philosophy)
    neural_integration = philosophy_found and any(keyword in philosophy_content for keyword in ['neural', 'synaptic', 'connection', 'network', 'brain', 'mind', 'cognitive'])
    
    checks.append({
        "name": "Neural Concepts Integrated",
        "passed": neural_integration,
        "detail": f"Philosophy integrates neural/synaptic concepts: {neural_integration}"
    })
    
    # Check 7: Professional craftsmanship language present
    craftsmanship_language = philosophy_found and any(phrase in philosophy_content for phrase in ['meticulously', 'crafted', 'expert', 'master', 'precision', 'painstaking', 'countless hours'])
    
    checks.append({
        "name": "Craftsmanship Emphasis Present",
        "passed": craftsmanship_language,
        "detail": f"Philosophy emphasizes expert craftsmanship: {craftsmanship_language}"
    })
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    return {
        "passed": score >= 0.8,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python eval_script.py <workspace_dir>"}))
        sys.exit(1)
    
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result))