#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path

def check_skill_creation(workspace_path):
    workspace = Path(workspace_path)
    checks = []
    score = 0.0
    
    # Check if SKILL.md exists
    skill_md = workspace / 'SKILL.md'
    if skill_md.exists():
        checks.append({
            'name': 'SKILL.md exists',
            'passed': True,
            'detail': 'Found SKILL.md file'
        })
        score += 0.3
        
        # Check SKILL.md content
        content = skill_md.read_text()
        
        # Check for YAML frontmatter
        if content.startswith('---'):
            checks.append({
                'name': 'YAML frontmatter present',
                'passed': True,
                'detail': 'SKILL.md has proper frontmatter'
            })
            score += 0.2
            
            # Check for required fields
            if 'name:' in content and 'description:' in content:
                checks.append({
                    'name': 'Required frontmatter fields',
                    'passed': True,
                    'detail': 'Has name and description fields'
                })
                score += 0.2
            else:
                checks.append({
                    'name': 'Required frontmatter fields',
                    'passed': False,
                    'detail': 'Missing name or description in frontmatter'
                })
        else:
            checks.append({
                'name': 'YAML frontmatter present',
                'passed': False,
                'detail': 'SKILL.md missing frontmatter'
            })
        
        # Check for PDF/text extraction related content
        content_lower = content.lower()
        pdf_keywords = ['pdf', 'text', 'extract', 'ocr']
        found_keywords = [kw for kw in pdf_keywords if kw in content_lower]
        
        if len(found_keywords) >= 2:
            checks.append({
                'name': 'PDF extraction content',
                'passed': True,
                'detail': f'Found relevant keywords: {found_keywords}'
            })
            score += 0.2
        else:
            checks.append({
                'name': 'PDF extraction content',
                'passed': False,
                'detail': f'Limited PDF-related content (found: {found_keywords})'
            })
            
    else:
        checks.append({
            'name': 'SKILL.md exists',
            'passed': False,
            'detail': 'SKILL.md file not found'
        })
    
    # Check if test cases were run (look for workspace evidence)
    eval_evidence = [
        workspace / 'iteration-1',
        workspace / 'benchmark.json',
        workspace / 'evals',
        workspace.glob('*eval*'),
        workspace.glob('*test*')
    ]
    
    found_eval_evidence = any([
        path.exists() if hasattr(path, 'exists') else any(path)
        for path in eval_evidence
    ])
    
    if found_eval_evidence:
        checks.append({
            'name': 'Evaluation evidence',
            'passed': True,
            'detail': 'Found evidence of skill testing/evaluation'
        })
        score += 0.1
    else:
        checks.append({
            'name': 'Evaluation evidence',
            'passed': False,
            'detail': 'No clear evidence of skill evaluation'
        })
    
    # Bonus: Check for .skill package file
    skill_files = list(workspace.glob('*.skill'))
    if skill_files:
        checks.append({
            'name': 'Packaged skill file',
            'passed': True,
            'detail': f'Found packaged skill: {skill_files[0].name}'
        })
        score += 0.1
    
    passed = score >= 0.7  # Need 70% to pass
    
    return {
        'passed': passed,
        'score': min(score, 1.0),
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'error': 'Usage: eval_script.py <workspace_path>'}))
        sys.exit(1)
    
    result = check_skill_creation(sys.argv[1])
    print(json.dumps(result, indent=2))