#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path
try:
    import PyPDF2
except ImportError:
    os.system('pip install PyPDF2==3.0.1')
    import PyPDF2

def check_pdf_form(pdf_path, expected_fields):
    """Check if PDF has fillable form fields matching the schema"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            if '/AcroForm' not in reader.trailer['/Root']:
                return False, "PDF does not contain form fields"
            
            form = reader.trailer['/Root']['/AcroForm']
            if '/Fields' not in form:
                return False, "PDF form has no fields"
            
            fields = form['/Fields']
            field_names = []
            
            for field_ref in fields:
                field = field_ref.get_object()
                if '/T' in field:
                    field_names.append(field['/T'])
            
            return True, field_names
    except Exception as e:
        return False, f"Error reading PDF: {str(e)}"

def evaluate_skill_creation(workspace_path):
    workspace = Path(workspace_path)
    checks = []
    total_score = 0
    
    # Check 1: Skill directory was created
    skill_dirs = list(workspace.glob('*-skill')) + list(workspace.glob('skill-*')) + list(workspace.glob('*pdf*form*')) + list(workspace.glob('form*generator*'))
    if skill_dirs:
        skill_dir = skill_dirs[0]
        checks.append({"name": "skill_directory_created", "passed": True, "detail": f"Found skill directory: {skill_dir.name}"})
        total_score += 20
    else:
        checks.append({"name": "skill_directory_created", "passed": False, "detail": "No skill directory found"})
        skill_dir = None
    
    # Check 2: SKILL.md exists and has proper structure
    if skill_dir and (skill_dir / 'SKILL.md').exists():
        skill_md = (skill_dir / 'SKILL.md').read_text()
        has_frontmatter = skill_md.strip().startswith('---')
        has_pdf_content = 'pdf' in skill_md.lower() or 'form' in skill_md.lower()
        
        if has_frontmatter and has_pdf_content:
            checks.append({"name": "skill_md_structure", "passed": True, "detail": "SKILL.md has proper frontmatter and PDF form content"})
            total_score += 25
        else:
            checks.append({"name": "skill_md_structure", "passed": False, "detail": "SKILL.md missing frontmatter or PDF form instructions"})
    else:
        checks.append({"name": "skill_md_structure", "passed": False, "detail": "SKILL.md not found"})
    
    # Check 3: Test cases were created and run
    eval_files = list(workspace.glob('**/evals.json')) + list(workspace.glob('**/eval*.json'))
    if eval_files:
        checks.append({"name": "test_cases_created", "passed": True, "detail": f"Found evaluation files: {len(eval_files)}"})
        total_score += 15
    else:
        checks.append({"name": "test_cases_created", "passed": False, "detail": "No evaluation files found"})
    
    # Check 4: Generated PDF forms exist
    pdf_files = list(workspace.glob('**/*.pdf'))
    if pdf_files:
        checks.append({"name": "pdf_forms_generated", "passed": True, "detail": f"Found {len(pdf_files)} PDF files"})
        total_score += 20
        
        # Check 5: PDF forms are actually fillable
        fillable_count = 0
        for pdf_file in pdf_files:
            has_form, details = check_pdf_form(pdf_file, [])
            if has_form:
                fillable_count += 1
        
        if fillable_count > 0:
            checks.append({"name": "pdf_forms_fillable", "passed": True, "detail": f"{fillable_count} PDFs have fillable form fields"})
            total_score += 20
        else:
            checks.append({"name": "pdf_forms_fillable", "passed": False, "detail": "PDFs found but none have fillable form fields"})
    else:
        checks.append({"name": "pdf_forms_generated", "passed": False, "detail": "No PDF files generated"})
        checks.append({"name": "pdf_forms_fillable", "passed": False, "detail": "No PDFs to check for form fields"})
    
    # Bonus checks
    # Check for scripts directory (indicates bundled tools)
    if skill_dir and (skill_dir / 'scripts').exists():
        script_files = list((skill_dir / 'scripts').glob('*.py'))
        if script_files:
            total_score += 5
            checks.append({"name": "bundled_scripts", "passed": True, "detail": f"Found {len(script_files)} Python scripts in skill"})
    
    # Check for evaluation viewer usage
    if list(workspace.glob('**/feedback.json')) or list(workspace.glob('**/benchmark.json')):
        total_score += 5
        checks.append({"name": "evaluation_feedback", "passed": True, "detail": "Evidence of evaluation viewer usage found"})
    
    # Final score calculation (out of 100 possible points)
    final_score = min(total_score / 100.0, 1.0)
    passed = len([c for c in checks if c['passed']]) >= 3  # At least 3 core checks must pass
    
    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_path>"}]}))
        sys.exit(1)
    
    result = evaluate_skill_creation(sys.argv[1])
    print(json.dumps(result))