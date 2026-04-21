import sys
import os
import json

def evaluate_skill_creation(workspace_path):
    checks = []
    
    # Check if pdf-extractor folder exists
    skill_folder = os.path.join(workspace_path, 'pdf-extractor')
    folder_exists = os.path.isdir(skill_folder)
    checks.append({
        'name': 'Skill folder created',
        'passed': folder_exists,
        'detail': f'pdf-extractor folder exists: {folder_exists}'
    })
    
    if not folder_exists:
        score = 0.0
        return {
            'passed': False,
            'score': score,
            'checks': checks
        }
    
    # Check SKILL.md exists and has correct frontmatter
    skill_md_path = os.path.join(skill_folder, 'SKILL.md')
    skill_md_exists = os.path.isfile(skill_md_path)
    checks.append({
        'name': 'SKILL.md file exists',
        'passed': skill_md_exists,
        'detail': f'SKILL.md exists: {skill_md_exists}'
    })
    
    # Check frontmatter content
    frontmatter_valid = False
    if skill_md_exists:
        try:
            with open(skill_md_path, 'r') as f:
                content = f.read().lower()
                has_name = 'pdf-extractor' in content
                has_description = 'description' in content and 'pdf' in content
                frontmatter_valid = has_name and has_description
        except:
            pass
    
    checks.append({
        'name': 'SKILL.md has proper frontmatter',
        'passed': frontmatter_valid,
        'detail': f'Frontmatter with name and description: {frontmatter_valid}'
    })
    
    # Check scripts folder and extract_pdf_data.py
    scripts_folder = os.path.join(skill_folder, 'scripts')
    scripts_exists = os.path.isdir(scripts_folder)
    checks.append({
        'name': 'Scripts folder exists',
        'passed': scripts_exists,
        'detail': f'scripts/ folder exists: {scripts_exists}'
    })
    
    script_file = os.path.join(scripts_folder, 'extract_pdf_data.py')
    script_exists = os.path.isfile(script_file)
    checks.append({
        'name': 'PDF extraction script exists',
        'passed': script_exists,
        'detail': f'extract_pdf_data.py exists: {script_exists}'
    })
    
    # Check evals.json
    evals_folder = os.path.join(skill_folder, 'evals')
    evals_json_path = os.path.join(evals_folder, 'evals.json')
    evals_exists = os.path.isfile(evals_json_path)
    checks.append({
        'name': 'Evals file exists',
        'passed': evals_exists,
        'detail': f'evals/evals.json exists: {evals_exists}'
    })
    
    # Check evals content
    evals_valid = False
    if evals_exists:
        try:
            with open(evals_json_path, 'r') as f:
                evals_data = json.load(f)
                has_skill_name = evals_data.get('skill_name') == 'pdf-extractor'
                has_evals = len(evals_data.get('evals', [])) >= 2
                evals_valid = has_skill_name and has_evals
        except:
            pass
    
    checks.append({
        'name': 'Evals content is valid',
        'passed': evals_valid,
        'detail': f'Valid evals.json with 2+ test cases: {evals_valid}'
    })
    
    score = sum(1 for c in checks if c['passed']) / len(checks)
    
    return {
        'passed': score == 1.0,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_path>')
        sys.exit(1)
    
    result = evaluate_skill_creation(sys.argv[1])
    print(json.dumps(result))