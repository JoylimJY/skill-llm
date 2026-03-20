#!/usr/bin/env python3
import sys
import os
import json

def main():
    workspace_dir = sys.argv[1]
    os.chdir(workspace_dir)
    
    checks = []
    
    # Check if Python script was created
    python_files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'gen_inputs_script.py']
    script_exists = len(python_files) > 0
    checks.append({
        'name': 'python_script_created',
        'passed': script_exists,
        'detail': f'Found {len(python_files)} Python files: {python_files}' if script_exists else 'No Python script found'
    })
    
    # Check if chat_log.txt was created
    chat_log_exists = os.path.exists('chat_log.txt')
    checks.append({
        'name': 'chat_log_created',
        'passed': chat_log_exists,
        'detail': 'chat_log.txt file exists' if chat_log_exists else 'chat_log.txt file missing'
    })
    
    # Check content of chat_log.txt
    haiku_content = False
    question_content = False
    if chat_log_exists:
        try:
            with open('chat_log.txt', 'r') as f:
                content = f.read().lower()
                haiku_content = 'haiku' in content or 'poetry' in content
                question_content = 'coding' in content or 'code' in content or 'programming' in content
        except Exception as e:
            pass
    
    checks.append({
        'name': 'haiku_request_logged',
        'passed': haiku_content,
        'detail': 'Chat log contains haiku-related content' if haiku_content else 'No haiku content found in log'
    })
    
    checks.append({
        'name': 'coding_topic_logged',
        'passed': question_content,
        'detail': 'Chat log contains coding-related content' if question_content else 'No coding topic found in log'
    })
    
    # Check if script imports anthropic
    anthropic_import = False
    if python_files:
        try:
            with open(python_files[0], 'r') as f:
                content = f.read()
                anthropic_import = 'import anthropic' in content or 'from anthropic' in content
        except Exception as e:
            pass
    
    checks.append({
        'name': 'anthropic_import_used',
        'passed': anthropic_import,
        'detail': 'Script imports anthropic library' if anthropic_import else 'No anthropic import found'
    })
    
    passed_count = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_count / total_checks
    
    result = {
        'passed': score >= 0.6,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()