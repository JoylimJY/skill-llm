import os
import sys
import json
import re
from pathlib import Path

def eval_task(workspace_path):
    checks = []
    
    # Check 1: Report file exists
    report_files = list(Path(workspace_path).glob('*report*.md'))
    if not report_files:
        checks.append({
            'name': 'Report file exists',
            'passed': False,
            'detail': 'No report markdown file found'
        })
        # Early return if no file found
        score = 0.0
        return {
            'passed': False,
            'score': score,
            'checks': checks
        }
    
    checks.append({
        'name': 'Report file exists', 
        'passed': True,
        'detail': f'Found report file: {report_files[0].name}'
    })
    
    # Read the report content
    report_content = ''
    best_score = 0
    best_content = ''
    
    for report_file in report_files:
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                # Score this file and keep the best one
                temp_score = 0
                if 'work summary' in content or 'summary' in content:
                    temp_score += 1
                if 'improvement' in content and 'area' in content:
                    temp_score += 1
                if 'typescript' in content or 'error handling' in content:
                    temp_score += 1
                if temp_score > best_score:
                    best_score = temp_score
                    best_content = content
                    report_content = content
        except Exception as e:
            continue
    
    if not report_content:
        checks.append({
            'name': 'Report content readable',
            'passed': False, 
            'detail': 'Could not read report content'
        })
    else:
        checks.append({
            'name': 'Report content readable',
            'passed': True,
            'detail': 'Successfully read report content'
        })
    
    # Check 2: Contains work summary section
    has_summary = any(keyword in report_content for keyword in [
        'work summary', 'summary', 'recent work', 'past 24', 'past 48'
    ])
    checks.append({
        'name': 'Contains work summary',
        'passed': has_summary,
        'detail': 'Found work summary section' if has_summary else 'Missing work summary section'
    })
    
    # Check 3: Identifies improvement areas
    has_improvements = any(keyword in report_content for keyword in [
        'improvement area', 'areas for improvement', 'skill gap', 'growth area'
    ])
    checks.append({
        'name': 'Identifies improvement areas', 
        'passed': has_improvements,
        'detail': 'Found improvement areas section' if has_improvements else 'Missing improvement areas'
    })
    
    # Check 4: References specific technologies from chat history
    tech_mentioned = any(tech in report_content for tech in [
        'typescript', 'react', 'async', 'sql', 'docker', 'express', 'node'
    ])
    checks.append({
        'name': 'References specific technologies',
        'passed': tech_mentioned,
        'detail': 'Found references to technologies from chat history' if tech_mentioned else 'Missing technology references'
    })
    
    # Check 5: Provides evidence-based recommendations
    has_evidence = any(phrase in report_content for phrase in [
        'what i observed', 'in your recent', 'you struggled', 'you worked on', 'evidence', 'pattern'
    ])
    checks.append({
        'name': 'Provides evidence-based recommendations',
        'passed': has_evidence,
        'detail': 'Found evidence-based analysis' if has_evidence else 'Missing evidence or observations'
    })
    
    # Check 6: Contains action items or recommendations
    has_actions = any(keyword in report_content for keyword in [
        'action item', 'recommendation', 'next step', 'focus on', 'priority'
    ])
    checks.append({
        'name': 'Contains actionable recommendations',
        'passed': has_actions,
        'detail': 'Found actionable recommendations' if has_actions else 'Missing action items or recommendations'
    })
    
    # Check 7: Report structure and formatting
    has_structure = (
        report_content.count('#') >= 3 and  # Multiple headings
        ('##' in report_content or '###' in report_content)  # Subsections
    )
    checks.append({
        'name': 'Proper report structure',
        'passed': has_structure,
        'detail': 'Report has proper heading structure' if has_structure else 'Report lacks proper structure'
    })
    
    # Calculate score
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.7  # Pass if at least 70% of checks pass
    
    return {
        'passed': passed,
        'score': score, 
        'checks': checks
    }

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.' 
    result = eval_task(workspace)
    print(json.dumps(result))