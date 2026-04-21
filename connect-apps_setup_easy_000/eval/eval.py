import os
import sys
import subprocess
import json

def evaluate_setup(workspace_path):
    os.chdir(workspace_path)
    checks = []
    
    # Check 1: Plugin installation attempt
    plugin_check = False
    try:
        result = subprocess.run(['plugin', 'install', 'composio-toolrouter'], 
                              capture_output=True, text=True, timeout=10)
        if 'installed successfully' in result.stdout.lower():
            plugin_check = True
        checks.append({
            'name': 'Plugin Installation',
            'passed': plugin_check,
            'detail': 'Plugin install command executed successfully' if plugin_check else 'Plugin installation failed'
        })
    except Exception as e:
        checks.append({
            'name': 'Plugin Installation',
            'passed': False,
            'detail': f'Error running plugin install: {str(e)}'
        })
    
    # Check 2: Setup command execution
    setup_check = False
    try:
        result = subprocess.run(['composio-toolrouter', 'setup'], 
                              capture_output=True, text=True, timeout=10)
        if 'setup completed successfully' in result.stdout.lower():
            setup_check = True
        checks.append({
            'name': 'Setup Command',
            'passed': setup_check,
            'detail': 'Setup command executed successfully' if setup_check else 'Setup command failed'
        })
    except Exception as e:
        checks.append({
            'name': 'Setup Command',
            'passed': False,
            'detail': f'Error running setup: {str(e)}'
        })
    
    # Check 3: Verification file creation
    verification_check = False
    verification_detail = 'Verification file not found'
    
    if os.path.exists('setup_verification.txt'):
        try:
            with open('setup_verification.txt', 'r') as f:
                content = f.read().strip().lower()
                if 'composio setup completed successfully' in content:
                    verification_check = True
                    verification_detail = 'Verification file created with correct content'
                else:
                    verification_detail = 'Verification file exists but content is incorrect'
        except Exception as e:
            verification_detail = f'Error reading verification file: {str(e)}'
    
    checks.append({
        'name': 'Verification File',
        'passed': verification_check,
        'detail': verification_detail
    })
    
    # Calculate score
    passed_count = sum(1 for c in checks if c['passed'])
    total_count = len(checks)
    score = passed_count / total_count if total_count > 0 else 0
    
    return {
        'passed': score == 1.0,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace = sys.argv[1]
    result = evaluate_setup(workspace)
    print(json.dumps(result))