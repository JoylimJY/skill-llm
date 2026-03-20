#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def check_skill_improvement(workspace_path):
    """Check if the skill has been improved through the iterative process."""
    workspace = Path(workspace_path)
    checks = []
    total_score = 0
    
    # Check 1: Verify skill directory exists
    skill_path = workspace / 'analytics-helper'
    skill_exists = skill_path.exists() and (skill_path / 'SKILL.md').exists()
    checks.append({
        'name': 'skill_structure',
        'passed': skill_exists,
        'detail': f'Skill directory and SKILL.md found: {skill_exists}'
    })
    if skill_exists:
        total_score += 15
    
    # Check 2: Look for iteration workspace directories
    iteration_dirs = [d for d in workspace.iterdir() if d.is_dir() and 'iteration' in d.name.lower()]
    has_iterations = len(iteration_dirs) >= 1
    checks.append({
        'name': 'iteration_evidence', 
        'passed': has_iterations,
        'detail': f'Found {len(iteration_dirs)} iteration directories: {[d.name for d in iteration_dirs]}'
    })
    if has_iterations:
        total_score += 20
    
    # Check 3: Look for test execution evidence
    test_outputs_found = False
    eval_runs_found = 0
    for iter_dir in iteration_dirs:
        eval_dirs = [d for d in iter_dir.iterdir() if d.is_dir() and 'eval' in d.name.lower()]
        eval_runs_found += len(eval_dirs)
        for eval_dir in eval_dirs:
            if (eval_dir / 'outputs').exists():
                test_outputs_found = True
    
    checks.append({
        'name': 'test_execution',
        'passed': test_outputs_found and eval_runs_found >= 3,
        'detail': f'Found {eval_runs_found} eval runs with outputs: {test_outputs_found}'
    })
    if test_outputs_found and eval_runs_found >= 3:
        total_score += 20
    
    # Check 4: Look for evaluation/grading evidence  
    grading_found = False
    viewer_evidence = False
    for iter_dir in iteration_dirs:
        if (iter_dir / 'benchmark.json').exists():
            grading_found = True
        grading_files = list(iter_dir.rglob('grading.json'))
        if grading_files:
            grading_found = True
        if (iter_dir / 'feedback.json').exists():
            viewer_evidence = True
    
    checks.append({
        'name': 'evaluation_process',
        'passed': grading_found,
        'detail': f'Grading/benchmark evidence found: {grading_found}, viewer feedback: {viewer_evidence}'
    })
    if grading_found:
        total_score += 20
    
    # Check 5: Look for skill modifications/improvements
    skill_improved = False
    original_skill_path = skill_path / 'SKILL.md'
    if original_skill_path.exists():
        skill_content = original_skill_path.read_text()
        # Look for signs of improvement: more detailed instructions, scripts, examples
        improvement_indicators = [
            len(skill_content) > 1000,  # More detailed content
            'script' in skill_content.lower(),
            'example' in skill_content.lower(),
            'step' in skill_content.lower() and skill_content.lower().count('step') > 2,
            'import pandas' in skill_content or 'matplotlib' in skill_content
        ]
        skill_improved = sum(improvement_indicators) >= 2
    
    checks.append({
        'name': 'skill_improvement',
        'passed': skill_improved,
        'detail': f'Skill shows signs of improvement (detailed instructions, scripts, examples): {skill_improved}'
    })
    if skill_improved:
        total_score += 15
    
    # Check 6: Multiple iterations indicate iterative improvement
    multiple_iterations = len(iteration_dirs) >= 2
    checks.append({
        'name': 'iterative_process',
        'passed': multiple_iterations,
        'detail': f'Multiple iterations found indicating iterative improvement: {len(iteration_dirs)} >= 2'
    })
    if multiple_iterations:
        total_score += 10
    
    # Overall pass if we have evidence of the core skill improvement workflow
    workflow_complete = skill_exists and has_iterations and test_outputs_found and grading_found
    
    return {
        'passed': workflow_complete,
        'score': min(total_score / 100.0, 1.0),
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_path>')
        sys.exit(1)
    
    result = check_skill_improvement(sys.argv[1])
    print(json.dumps(result, indent=2))