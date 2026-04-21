import sys
import os
import json
import re

def evaluate_setup_instructions(workspace_dir):
    checks = []
    
    # Look for any text files that might contain setup instructions
    instruction_files = []
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            if file.endswith(('.txt', '.md', '.rst')):
                instruction_files.append(os.path.join(root, file))
    
    content = ''
    for file_path in instruction_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content += f.read().lower() + '\n'
        except:
            continue
    
    # Check 1: Installation command mentioned
    install_keywords = ['plugin install', 'composio-toolrouter', '/plugin install']
    install_found = any(keyword.lower() in content for keyword in install_keywords)
    checks.append({
        'name': 'Installation Command',
        'passed': install_found,
        'detail': f'Found plugin installation instructions: {install_found}'
    })
    
    # Check 2: Setup command mentioned
    setup_keywords = ['setup', '/composio-toolrouter:setup', 'configure']
    setup_found = any(keyword.lower() in content for keyword in setup_keywords)
    checks.append({
        'name': 'Setup Command',
        'passed': setup_found,
        'detail': f'Found setup instructions: {setup_found}'
    })
    
    # Check 3: API key mentioned
    api_keywords = ['api key', 'platform.composio.dev', 'authentication']
    api_found = any(keyword.lower() in content for keyword in api_keywords)
    checks.append({
        'name': 'API Key Reference',
        'passed': api_found,
        'detail': f'Found API key instructions: {api_found}'
    })
    
    # Check 4: Step-by-step format
    step_keywords = ['step 1', 'step 2', 'first', 'then', 'next']
    steps_found = any(keyword.lower() in content for keyword in step_keywords)
    checks.append({
        'name': 'Step-by-Step Format',
        'passed': steps_found,
        'detail': f'Found step-by-step instructions: {steps_found}'
    })
    
    # Check 5: Testing mentioned
    test_keywords = ['test', 'try', 'verify', 'example']
    test_found = any(keyword.lower() in content for keyword in test_keywords)
    checks.append({
        'name': 'Testing Instructions',
        'passed': test_found,
        'detail': f'Found testing/verification steps: {test_found}'
    })
    
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.8
    
    return {
        'passed': passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace_dir = sys.argv[1]
    result = evaluate_setup_instructions(workspace_dir)
    print(json.dumps(result))