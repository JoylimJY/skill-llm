#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)
    
    # Check 1: File exists
    pptx_file = workspace / 'climate_presentation.pptx'
    file_exists = pptx_file.exists()
    checks.append({
        'name': 'File exists',
        'passed': file_exists,
        'detail': f'climate_presentation.pptx found: {file_exists}'
    })
    
    if not file_exists:
        result = {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
        print(json.dumps(result))
        return
    
    # Check 2: File is valid PPTX (has correct magic bytes)
    try:
        with open(pptx_file, 'rb') as f:
            magic = f.read(4)
        is_zip = magic == b'PK\x03\x04'
        checks.append({
            'name': 'Valid PPTX format',
            'passed': is_zip,
            'detail': f'File has ZIP magic bytes: {is_zip}'
        })
    except Exception as e:
        checks.append({
            'name': 'Valid PPTX format',
            'passed': False,
            'detail': f'Error reading file: {str(e)}'
        })
        is_zip = False
    
    if not is_zip:
        result = {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
        print(json.dumps(result))
        return
    
    # Check 3: Extract and verify content using markitdown
    try:
        import subprocess
        result_text = subprocess.run(
            ['python3', '-m', 'markitdown', str(pptx_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        content = result_text.stdout.lower()
        
        # Check for title slide content
        has_title = 'climate change overview' in content
        checks.append({
            'name': 'Slide 1: Title present',
            'passed': has_title,
            'detail': f'Title "Climate Change Overview" found: {has_title}'
        })
        
        has_subtitle = 'global challenge' in content
        checks.append({
            'name': 'Slide 1: Subtitle present',
            'passed': has_subtitle,
            'detail': f'Subtitle "A Global Challenge" found: {has_subtitle}'
        })
        
        # Check for content slide
        has_key_facts = 'key facts' in content
        checks.append({
            'name': 'Slide 2: Title present',
            'passed': has_key_facts,
            'detail': f'Title "Key Facts" found: {has_key_facts}'
        })
        
        has_bullet1 = 'global temperatures' in content and 'rising' in content
        checks.append({
            'name': 'Slide 2: Bullet 1 present',
            'passed': has_bullet1,
            'detail': f'Bullet "Global temperatures rising" found: {has_bullet1}'
        })
        
        has_bullet2 = 'sea levels' in content and 'increasing' in content
        checks.append({
            'name': 'Slide 2: Bullet 2 present',
            'passed': has_bullet2,
            'detail': f'Bullet "Sea levels increasing" found: {has_bullet2}'
        })
        
        has_bullet3 = 'extreme weather' in content and 'events' in content
        checks.append({
            'name': 'Slide 2: Bullet 3 present',
            'passed': has_bullet3,
            'detail': f'Bullet "Extreme weather events" found: {has_bullet3}'
        })
        
        # Check for conclusion slide
        has_take_action = 'take action' in content
        checks.append({
            'name': 'Slide 3: Title present',
            'passed': has_take_action,
            'detail': f'Title "Take Action" found: {has_take_action}'
        })
        
        has_action_text = 'every action counts' in content
        checks.append({
            'name': 'Slide 3: Content present',
            'passed': has_action_text,
            'detail': f'Text "Every action counts" found: {has_action_text}'
        })
        
    except Exception as e:
        checks.append({
            'name': 'Content extraction',
            'passed': False,
            'detail': f'Error extracting content: {str(e)}'
        })
    
    passed_count = sum(1 for c in checks if c['passed'])
    total_count = len(checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    
    result = {
        'passed': score >= 0.9,
        'score': score,
        'checks': checks
    }
    print(json.dumps(result))

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    evaluate(workspace)
