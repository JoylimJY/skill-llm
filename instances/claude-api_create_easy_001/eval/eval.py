#!/usr/bin/env python3
import sys
import os
import json

def main(workspace_dir):
    checks = []
    passed = True
    score = 0.0
    
    # Check if script was created
    script_files = [f for f in os.listdir(workspace_dir) if f.endswith('.py') and 'summarize' in f.lower() or 'claude' in f.lower() or 'summary' in f.lower()]
    if not script_files:
        script_files = [f for f in os.listdir(workspace_dir) if f.endswith('.py') and f != 'eval_script.py' and f != 'gen_inputs_script.py']
    
    script_check = len(script_files) > 0
    checks.append({
        'name': 'Python script created',
        'passed': script_check,
        'detail': f'Found Python script: {script_files[0] if script_files else "None"}'
    })
    
    if script_check:
        score += 0.3
        script_path = os.path.join(workspace_dir, script_files[0])
        
        # Check if script imports anthropic
        try:
            with open(script_path, 'r') as f:
                script_content = f.read()
            
            anthropic_import = 'import anthropic' in script_content or 'from anthropic' in script_content
            checks.append({
                'name': 'Uses anthropic library',
                'passed': anthropic_import,
                'detail': 'Script imports anthropic library' if anthropic_import else 'Script missing anthropic import'
            })
            if anthropic_import:
                score += 0.2
            
            # Check for Claude Opus 4.6 model
            opus_model = 'claude-opus-4-6' in script_content
            checks.append({
                'name': 'Uses Claude Opus 4.6 model',
                'passed': opus_model,
                'detail': 'Script uses claude-opus-4-6 model' if opus_model else 'Script does not specify claude-opus-4-6 model'
            })
            if opus_model:
                score += 0.2
            
            # Check for file reading
            file_read = 'input_text.txt' in script_content and ('open(' in script_content or 'read' in script_content)
            checks.append({
                'name': 'Reads input file',
                'passed': file_read,
                'detail': 'Script reads from input_text.txt' if file_read else 'Script does not read input_text.txt'
            })
            if file_read:
                score += 0.15
            
            # Check for file writing
            file_write = 'summary.txt' in script_content and ('open(' in script_content or 'write' in script_content)
            checks.append({
                'name': 'Writes output file',
                'passed': file_write,
                'detail': 'Script writes to summary.txt' if file_write else 'Script does not write to summary.txt'
            })
            if file_write:
                score += 0.15
            
        except Exception as e:
            checks.append({
                'name': 'Script readable',
                'passed': False,
                'detail': f'Error reading script: {str(e)}'
            })
            passed = False
    else:
        passed = False
    
    if score >= 0.7:
        passed = True
    else:
        passed = False
    
    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_dir>')
        sys.exit(1)
    main(sys.argv[1])