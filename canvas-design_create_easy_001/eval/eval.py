import sys
import os
import json
from pathlib import Path

def evaluate_canvas_design(workspace_path):
    workspace = Path(workspace_path)
    checks = []
    
    # Check for philosophy.md file
    philosophy_files = list(workspace.glob('*philosophy*.md')) + list(workspace.glob('*.md'))
    philosophy_exists = len(philosophy_files) > 0
    
    philosophy_content = ''
    if philosophy_exists:
        for file in philosophy_files:
            try:
                content = file.read_text(encoding='utf-8')
                if len(content) > 200:  # Substantial content
                    philosophy_content = content.lower()
                    break
            except:
                continue
    
    checks.append({
        'name': 'Philosophy markdown file exists',
        'passed': philosophy_exists,
        'detail': f'Found {len(philosophy_files)} markdown files' if philosophy_exists else 'No markdown files found'
    })
    
    # Check philosophy content quality
    philosophy_quality = False
    if philosophy_content:
        design_keywords = ['visual', 'design', 'aesthetic', 'composition', 'color', 'form', 'space']
        craft_keywords = ['craft', 'expert', 'master', 'meticulous', 'precision', 'labored']
        
        design_score = sum(1 for kw in design_keywords if kw in philosophy_content)
        craft_score = sum(1 for kw in craft_keywords if kw in philosophy_content)
        
        philosophy_quality = design_score >= 3 and craft_score >= 1 and len(philosophy_content) > 800
    
    checks.append({
        'name': 'Philosophy contains design principles',
        'passed': philosophy_quality,
        'detail': 'Philosophy demonstrates design thinking and craftsmanship emphasis' if philosophy_quality else 'Philosophy lacks depth or design focus'
    })
    
    # Check for poster image file
    image_files = list(workspace.glob('*detox*.png')) + list(workspace.glob('*poster*.png')) + list(workspace.glob('*.png'))
    image_exists = len(image_files) > 0
    
    checks.append({
        'name': 'Poster image file exists',
        'passed': image_exists,
        'detail': f'Found {len(image_files)} PNG files' if image_exists else 'No PNG files found'
    })
    
    # Check image file size (proxy for visual content)
    substantial_image = False
    if image_exists:
        for img_file in image_files:
            try:
                file_size = img_file.stat().st_size
                if file_size > 5000:  # At least 5KB suggests actual visual content
                    substantial_image = True
                    break
            except:
                continue
    
    checks.append({
        'name': 'Image has substantial content',
        'passed': substantial_image,
        'detail': 'Image file size indicates visual content' if substantial_image else 'Image appears to be empty or minimal'
    })
    
    # Check for digital detox conceptual alignment
    detox_alignment = False
    if philosophy_content:
        detox_concepts = ['digital', 'detox', 'minimal', 'quiet', 'silence', 'analog', 'disconnect', 'peaceful', 'meditation']
        alignment_score = sum(1 for concept in detox_concepts if concept in philosophy_content)
        detox_alignment = alignment_score >= 2
    
    checks.append({
        'name': 'Design aligns with digital detox concept',
        'passed': detox_alignment,
        'detail': 'Philosophy reflects digital detox themes' if detox_alignment else 'Philosophy lacks connection to digital detox concept'
    })
    
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8
    
    return {
        'passed': passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    result = evaluate_canvas_design(sys.argv[1])
    print(json.dumps(result, indent=2))