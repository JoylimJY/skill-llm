#!/usr/bin/env python3
import sys
import os
import subprocess
import json
from pathlib import Path

def check_file_exists(workspace_dir):
    docx_path = Path(workspace_dir) / 'cloud_migration_proposal.docx'
    return {'name': 'file_exists', 'passed': docx_path.exists(), 'detail': f'Expected file at {docx_path}'}

def extract_text_content(workspace_dir):
    docx_path = Path(workspace_dir) / 'cloud_migration_proposal.docx'
    if not docx_path.exists():
        return {'name': 'content_extraction', 'passed': False, 'detail': 'File does not exist'}
    
    try:
        result = subprocess.run(['pandoc', str(docx_path), '-t', 'plain'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.lower()
    except Exception as e:
        return {'name': 'content_extraction', 'passed': False, 'detail': f'Failed to extract text: {e}'}

def check_required_content(workspace_dir):
    content = extract_text_content(workspace_dir)
    if isinstance(content, dict):  # Error case
        return content
    
    checks = []
    required_phrases = [
        'cloud infrastructure migration proposal',
        'prepared for techcorp inc',
        'table of contents',
        'executive summary', 
        'technical requirements',
        'timeline',
        'budget overview',
        'planning',
        'migration', 
        'testing',
        'phase',
        'duration'
    ]
    
    for phrase in required_phrases:
        found = phrase in content
        checks.append({
            'name': f'contains_{phrase.replace(" ", "_")}',
            'passed': found,
            'detail': f'Found required phrase: {phrase}' if found else f'Missing required phrase: {phrase}'
        })
    
    return checks

def check_structure(workspace_dir):
    # Use pandoc to get structured output
    docx_path = Path(workspace_dir) / 'cloud_migration_proposal.docx'
    if not docx_path.exists():
        return [{'name': 'structure_check', 'passed': False, 'detail': 'File does not exist'}]
    
    try:
        # Extract as markdown to see headings
        result = subprocess.run(['pandoc', str(docx_path), '-t', 'markdown'], 
                              capture_output=True, text=True, check=True)
        markdown_content = result.stdout
        
        # Check for heading structure
        has_headings = '# ' in markdown_content or '## ' in markdown_content
        has_table = '|' in markdown_content  # Tables contain pipe characters in markdown
        has_list = ('- ' in markdown_content or '* ' in markdown_content or 
                   '1. ' in markdown_content or '2. ' in markdown_content)
        
        return [
            {'name': 'has_headings', 'passed': has_headings, 'detail': 'Document contains proper heading structure'},
            {'name': 'has_table', 'passed': has_table, 'detail': 'Document contains table structure'},
            {'name': 'has_list', 'passed': has_list, 'detail': 'Document contains bulleted/numbered lists'}
        ]
    except Exception as e:
        return [{'name': 'structure_check', 'passed': False, 'detail': f'Failed to check structure: {e}'}]

def main():
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'usage', 'passed': False, 'detail': 'Usage: eval_script.py <workspace_dir>'}]}))
        return
    
    workspace_dir = sys.argv[1]
    checks = []
    
    # Check file exists
    file_check = check_file_exists(workspace_dir)
    checks.append(file_check)
    
    if file_check['passed']:
        # Check content
        content_checks = check_required_content(workspace_dir)
        if isinstance(content_checks, list):
            checks.extend(content_checks)
        else:
            checks.append(content_checks)
        
        # Check structure  
        structure_checks = check_structure(workspace_dir)
        checks.extend(structure_checks)
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    passed = score >= 0.7  # Pass if 70% of checks pass
    
    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()