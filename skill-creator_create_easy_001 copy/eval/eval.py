import sys
import os
import json
import re

def evaluate_skill_creation(workspace_path):
    checks = []
    
    # Check if SKILL.md exists
    skill_file = os.path.join(workspace_path, 'SKILL.md')
    skill_exists = os.path.exists(skill_file)
    checks.append({
        'name': 'SKILL.md file exists',
        'passed': skill_exists,
        'detail': f'Found SKILL.md: {skill_exists}'
    })
    
    if not skill_exists:
        # Early exit if no skill file
        score = 0.0
        return {
            'passed': False,
            'score': score,
            'checks': checks
        }
    
    # Read the skill content
    try:
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read().lower()
    except Exception as e:
        checks.append({
            'name': 'SKILL.md readable',
            'passed': False,
            'detail': f'Error reading file: {e}'
        })
        score = len([c for c in checks if c['passed']]) / len(checks)
        return {
            'passed': score >= 0.8,
            'score': score,
            'checks': checks
        }
    
    # Check for YAML frontmatter with skill name
    has_frontmatter = '---' in content and 'name:' in content
    has_pdf_extractor_name = 'pdf-extractor' in content or 'pdf_extractor' in content
    checks.append({
        'name': 'Contains YAML frontmatter',
        'passed': has_frontmatter,
        'detail': f'Found frontmatter: {has_frontmatter}'
    })
    checks.append({
        'name': 'Skill named pdf-extractor',
        'passed': has_pdf_extractor_name,
        'detail': f'Found pdf-extractor name: {has_pdf_extractor_name}'
    })
    
    # Check for PDF-related content
    pdf_keywords = ['pdf', 'pypdf2', 'pdfplumber', 'extract', 'text']
    pdf_content_found = any(keyword in content for keyword in pdf_keywords)
    checks.append({
        'name': 'Contains PDF extraction content',
        'passed': pdf_content_found,
        'detail': f'Found PDF-related keywords: {pdf_content_found}'
    })
    
    # Check for Python library mentions
    python_libs = ['pypdf2' in content, 'pdfplumber' in content]
    has_python_libs = any(python_libs)
    checks.append({
        'name': 'Mentions Python PDF libraries',
        'passed': has_python_libs,
        'detail': f'Found PyPDF2 or pdfplumber: {has_python_libs}'
    })
    
    # Check for error handling mention
    error_keywords = ['error', 'exception', 'corrupted', 'password', 'protected', 'try', 'except']
    has_error_handling = any(keyword in content for keyword in error_keywords)
    checks.append({
        'name': 'Mentions error handling',
        'passed': has_error_handling,
        'detail': f'Found error handling concepts: {has_error_handling}'
    })
    
    # Check for description field
    has_description = 'description:' in content
    checks.append({
        'name': 'Contains description field',
        'passed': has_description,
        'detail': f'Found description field: {has_description}'
    })
    
    # Calculate final score
    score = sum(1 for c in checks if c['passed']) / len(checks)
    
    return {
        'passed': score >= 0.8,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_path>')
        sys.exit(1)
    
    result = evaluate_skill_creation(sys.argv[1])
    print(json.dumps(result))