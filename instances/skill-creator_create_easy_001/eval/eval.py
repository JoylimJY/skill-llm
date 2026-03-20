#!/usr/bin/env python3
import sys
import os
import json
import glob

def check_skill_exists(workspace_dir):
    """Check if a skill was created"""
    skill_files = glob.glob(os.path.join(workspace_dir, '*/SKILL.md'))
    if not skill_files:
        skill_files = glob.glob(os.path.join(workspace_dir, 'SKILL.md'))
    return len(skill_files) > 0, skill_files

def check_skill_content(skill_files):
    """Check if the skill contains PDF extraction related content"""
    checks = []
    
    if not skill_files:
        return checks
    
    skill_path = skill_files[0]
    try:
        with open(skill_path, 'r') as f:
            content = f.read().lower()
        
        # Check for PDF-related keywords
        pdf_keywords = ['pdf', 'extract', 'text', 'ocr']
        found_keywords = [kw for kw in pdf_keywords if kw in content]
        
        checks.append({
            'name': 'contains_pdf_keywords',
            'passed': len(found_keywords) >= 2,
            'detail': f'Found keywords: {", ".join(found_keywords)}'
        })
        
        # Check for OCR/tesseract mentions
        ocr_mentioned = any(term in content for term in ['tesseract', 'pytesseract', 'ocr', 'image'])
        checks.append({
            'name': 'mentions_ocr',
            'passed': ocr_mentioned,
            'detail': 'OCR capabilities mentioned' if ocr_mentioned else 'No OCR capabilities mentioned'
        })
        
        # Check for multiple PDF libraries
        pdf_libs = ['pypdf', 'pdfplumber', 'pdf2image', 'pymupdf']
        found_libs = [lib for lib in pdf_libs if lib in content]
        checks.append({
            'name': 'mentions_pdf_libraries',
            'passed': len(found_libs) > 0,
            'detail': f'PDF libraries mentioned: {", ".join(found_libs)}' if found_libs else 'No PDF libraries mentioned'
        })
        
    except Exception as e:
        checks.append({
            'name': 'skill_content_readable',
            'passed': False,
            'detail': f'Error reading skill file: {str(e)}'
        })
    
    return checks

def check_test_cases(workspace_dir):
    """Check if test cases were created"""
    checks = []
    
    # Look for evals.json or test cases
    eval_files = glob.glob(os.path.join(workspace_dir, '**/evals.json'), recursive=True)
    test_files = glob.glob(os.path.join(workspace_dir, '**/test*'), recursive=True)
    
    has_tests = len(eval_files) > 0 or len(test_files) > 0
    checks.append({
        'name': 'has_test_cases',
        'passed': has_tests,
        'detail': f'Found {len(eval_files)} eval files and {len(test_files)} test files'
    })
    
    return checks

def check_scripts_directory(workspace_dir):
    """Check if scripts were created for the skill"""
    checks = []
    
    script_dirs = glob.glob(os.path.join(workspace_dir, '*/scripts'), recursive=True)
    script_files = glob.glob(os.path.join(workspace_dir, '**/*.py'), recursive=True)
    
    has_scripts = len(script_dirs) > 0 or len(script_files) > 2  # More than just our eval/gen scripts
    checks.append({
        'name': 'includes_helper_scripts',
        'passed': has_scripts,
        'detail': f'Found {len(script_dirs)} script directories and {len(script_files)} Python files'
    })
    
    return checks

def main():
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'usage', 'passed': False, 'detail': 'Usage: eval_script.py <workspace_dir>'}]}))
        return
    
    workspace_dir = sys.argv[1]
    
    if not os.path.exists(workspace_dir):
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'workspace_exists', 'passed': False, 'detail': 'Workspace directory does not exist'}]}))
        return
    
    all_checks = []
    
    # Check if skill was created
    skill_exists, skill_files = check_skill_exists(workspace_dir)
    all_checks.append({
        'name': 'skill_created',
        'passed': skill_exists,
        'detail': f'Found SKILL.md files: {", ".join(skill_files)}' if skill_files else 'No SKILL.md found'
    })
    
    if skill_exists:
        all_checks.extend(check_skill_content(skill_files))
    
    all_checks.extend(check_test_cases(workspace_dir))
    all_checks.extend(check_scripts_directory(workspace_dir))
    
    # Calculate score
    passed_checks = sum(1 for check in all_checks if check['passed'])
    total_checks = len(all_checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    overall_passed = skill_exists and score >= 0.6
    
    result = {
        'passed': overall_passed,
        'score': score,
        'checks': all_checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()