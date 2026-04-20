import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None


def normalize(s):
    if not isinstance(s, str):
        return ''
    return re.sub(r'[^a-z0-9]+', '', s.lower())


def check_file_exists(path, name):
    """Check if a file exists with fuzzy matching"""
    if path.exists():
        return True, f"{name} exists"
    return False, f"{name} is missing"


def check_file_contains(path, patterns, name):
    """Check if file contains required patterns"""
    content = safe_read(path)
    if not content:
        return False, f"{name} could not be read"
    
    missing = []
    for pattern in patterns:
        if not re.search(pattern, content, re.IGNORECASE):
            missing.append(pattern)
    
    if missing:
        return False, f"{name} missing patterns: {missing}"
    return True, f"{name} contains required patterns"


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check for task.yaml
    task_yaml_path = workspace / 'task.yaml'
    passed, detail = check_file_exists(task_yaml_path, 'task.yaml')
    checks.append({'name': 'task_yaml_exists', 'passed': passed, 'detail': detail})
    
    if passed:
        content = safe_read(task_yaml_path)
        if content:
            # Check for required task.yaml fields
            required_fields = ['skill:', 'difficulty:', 'description:', 'inputs:', 'outputs:']
            missing_fields = [f for f in required_fields if not re.search(re.escape(f), content, re.IGNORECASE)]
            checks.append({
                'name': 'task_yaml_structure', 
                'passed': len(missing_fields) == 0, 
                'detail': f"Missing fields: {missing_fields}" if missing_fields else "All required fields present"
            })
            
            # Check for dr-frankenstein skill
            checks.append({
                'name': 'task_yaml_skill', 
                'passed': re.search(r'skill:\s*dr-frankenstein', content, re.IGNORECASE) is not None, 
                'detail': 'task.yaml should specify dr-frankenstein skill'
            })
            
            # Check for hard difficulty
            checks.append({
                'name': 'task_yaml_difficulty', 
                'passed': re.search(r'difficulty:\s*hard', content, re.IGNORECASE) is not None, 
                'detail': 'task.yaml should specify hard difficulty'
            })

    # Check for gen_inputs.py
    gen_inputs_path = workspace / 'gen_inputs.py'
    passed, detail = check_file_exists(gen_inputs_path, 'gen_inputs.py')
    checks.append({'name': 'gen_inputs_exists', 'passed': passed, 'detail': detail})
    
    if passed:
        content = safe_read(gen_inputs_path)
        if content:
            # Check for deterministic seed
            checks.append({
                'name': 'gen_inputs_seed', 
                'passed': re.search(r'seed', content, re.IGNORECASE) is not None, 
                'detail': 'gen_inputs.py should use a seed for determinism'
            })
            
            # Check for marker generation
            checks.append({
                'name': 'gen_inputs_markers', 
                'passed': re.search(r'marker', content, re.IGNORECASE) is not None, 
                'detail': 'gen_inputs.py should generate marker text'
            })

    # Check for evaluator.py
    evaluator_path = workspace / 'evaluator.py'
    passed, detail = check_file_exists(evaluator_path, 'evaluator.py')
    checks.append({'name': 'evaluator_exists', 'passed': passed, 'detail': detail})
    
    if passed:
        content = safe_read(evaluator_path)
        if content:
            # Check for basic evaluation structure
            checks.append({
                'name': 'evaluator_structure', 
                'passed': re.search(r'def\s+evaluate', content, re.IGNORECASE) is not None or 
                          re.search(r'def\s+main', content, re.IGNORECASE) is not None, 
                'detail': 'evaluator.py should have evaluation function'
            })
            
            # Check for output validation
            checks.append({
                'name': 'evaluator_validation', 
                'passed': re.search(r'output', content, re.IGNORECASE) is not None, 
                'detail': 'evaluator.py should validate outputs'
            })

    # Check for supporting files (optional but recommended)
    dockerfile_path = workspace / 'Dockerfile'
    passed, detail = check_file_exists(dockerfile_path, 'Dockerfile')
    checks.append({'name': 'dockerfile_exists', 'passed': passed, 'detail': detail})
    
    setup_path = workspace / 'setup.sh'
    passed, detail = check_file_exists(setup_path, 'setup.sh')
    checks.append({'name': 'setup_exists', 'passed': passed, 'detail': detail})

    # Calculate score
    total = len(checks) if checks else 1
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total
    
    # Pass if at least 80% of checks pass
    result = {
        'passed': score >= 0.8, 
        'score': round(score, 2), 
        'checks': checks
    }
    print(json.dumps(result))


if __name__ == '__main__':
    main()