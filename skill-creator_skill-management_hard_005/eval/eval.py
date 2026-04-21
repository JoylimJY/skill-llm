import os
import sys
import json
import re
from pathlib import Path

def evaluate_skill_creation(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    
    # Check 1: Skill directory exists with correct name
    skill_dirs = list(workspace.glob('dashboard-builder*'))
    skill_dir = None
    for candidate in skill_dirs:
        if candidate.is_dir() and 'dashboard-builder' in candidate.name.lower():
            skill_dir = candidate
            break
    
    if skill_dir:
        checks.append({'name': 'skill_directory_created', 'passed': True, 'detail': f'Found skill directory: {skill_dir.name}'})
    else:
        checks.append({'name': 'skill_directory_created', 'passed': False, 'detail': 'No dashboard-builder skill directory found'})
        # Early return if no skill directory
        score = 0.0
        return {'passed': False, 'score': score, 'checks': checks}
    
    # Check 2: SKILL.md exists with proper frontmatter
    skill_md = skill_dir / 'SKILL.md'
    if skill_md.exists():
        content = skill_md.read_text(encoding='utf-8')
        # Check for YAML frontmatter
        if content.startswith('---') and '---' in content[3:]:
            frontmatter_end = content.find('---', 3) + 3
            frontmatter = content[:frontmatter_end]
            if any(keyword in frontmatter.lower() for keyword in ['name:', 'dashboard-builder']):
                checks.append({'name': 'skill_frontmatter', 'passed': True, 'detail': 'SKILL.md has proper frontmatter with name'})
            else:
                checks.append({'name': 'skill_frontmatter', 'passed': False, 'detail': 'SKILL.md frontmatter missing name field'})
        else:
            checks.append({'name': 'skill_frontmatter', 'passed': False, 'detail': 'SKILL.md missing YAML frontmatter'})
    else:
        checks.append({'name': 'skill_frontmatter', 'passed': False, 'detail': 'SKILL.md file not found'})
    
    # Check 3: Skill content covers CSV data handling
    if skill_md.exists():
        content = skill_md.read_text(encoding='utf-8').lower()
        csv_keywords = ['csv', 'data', 'read', 'parse', 'pandas']
        if any(keyword in content for keyword in csv_keywords):
            checks.append({'name': 'csv_handling_instructions', 'passed': True, 'detail': 'Skill includes CSV data handling instructions'})
        else:
            checks.append({'name': 'csv_handling_instructions', 'passed': False, 'detail': 'Skill missing CSV data handling instructions'})
    else:
        checks.append({'name': 'csv_handling_instructions', 'passed': False, 'detail': 'Cannot check - SKILL.md not found'})
    
    # Check 4: Skill content covers chart generation
    if skill_md.exists():
        content = skill_md.read_text(encoding='utf-8').lower()
        chart_keywords = ['chart', 'graph', 'visualization', 'plot', 'bar', 'line', 'pie']
        if any(keyword in content for keyword in chart_keywords):
            checks.append({'name': 'chart_generation_instructions', 'passed': True, 'detail': 'Skill includes chart generation instructions'})
        else:
            checks.append({'name': 'chart_generation_instructions', 'passed': False, 'detail': 'Skill missing chart generation instructions'})
    else:
        checks.append({'name': 'chart_generation_instructions', 'passed': False, 'detail': 'Cannot check - SKILL.md not found'})
    
    # Check 5: Skill content covers HTML/dashboard creation
    if skill_md.exists():
        content = skill_md.read_text(encoding='utf-8').lower()
        html_keywords = ['html', 'dashboard', 'web', 'interactive', 'javascript', 'css']
        if any(keyword in content for keyword in html_keywords):
            checks.append({'name': 'html_dashboard_instructions', 'passed': True, 'detail': 'Skill includes HTML dashboard creation instructions'})
        else:
            checks.append({'name': 'html_dashboard_instructions', 'passed': False, 'detail': 'Skill missing HTML dashboard instructions'})
    else:
        checks.append({'name': 'html_dashboard_instructions', 'passed': False, 'detail': 'Cannot check - SKILL.md not found'})
    
    # Check 6: Scripts directory with helper scripts
    scripts_dir = skill_dir / 'scripts'
    if scripts_dir.exists() and scripts_dir.is_dir():
        script_files = list(scripts_dir.glob('*.py'))
        if script_files:
            checks.append({'name': 'helper_scripts_provided', 'passed': True, 'detail': f'Found {len(script_files)} helper scripts'})
        else:
            checks.append({'name': 'helper_scripts_provided', 'passed': False, 'detail': 'Scripts directory exists but no Python scripts found'})
    else:
        checks.append({'name': 'helper_scripts_provided', 'passed': False, 'detail': 'No scripts directory found'})
    
    # Check 7: Examples or references directory
    has_examples = False
    for subdir in ['examples', 'references', 'assets']:
        if (skill_dir / subdir).exists():
            has_examples = True
            break
    
    if has_examples:
        checks.append({'name': 'examples_or_references', 'passed': True, 'detail': 'Skill includes examples or reference materials'})
    else:
        checks.append({'name': 'examples_or_references', 'passed': False, 'detail': 'No examples or reference directories found'})
    
    # Check 8: Skill includes error handling guidance
    if skill_md.exists():
        content = skill_md.read_text(encoding='utf-8').lower()
        error_keywords = ['error', 'exception', 'validation', 'handle', 'try', 'catch']
        if any(keyword in content for keyword in error_keywords):
            checks.append({'name': 'error_handling_guidance', 'passed': True, 'detail': 'Skill includes error handling guidance'})
        else:
            checks.append({'name': 'error_handling_guidance', 'passed': False, 'detail': 'Skill missing error handling guidance'})
    else:
        checks.append({'name': 'error_handling_guidance', 'passed': False, 'detail': 'Cannot check - SKILL.md not found'})
    
    # Check 9: .skill package file created
    skill_files = list(workspace.glob('*.skill'))
    dashboard_skill_files = [f for f in skill_files if 'dashboard' in f.name.lower()]
    
    if dashboard_skill_files:
        checks.append({'name': 'skill_package_created', 'passed': True, 'detail': f'Found .skill package: {dashboard_skill_files[0].name}'})
    else:
        checks.append({'name': 'skill_package_created', 'passed': False, 'detail': 'No .skill package file found'})
    
    # Check 10: Skill description mentions triggering contexts
    if skill_md.exists():
        content = skill_md.read_text(encoding='utf-8')
        # Look in frontmatter description
        if content.startswith('---'):
            frontmatter_end = content.find('---', 3)
            if frontmatter_end > 0:
                frontmatter = content[3:frontmatter_end]
                desc_match = re.search(r'description:\s*(.+?)(?=\n\w+:|$)', frontmatter, re.DOTALL)
                if desc_match:
                    description = desc_match.group(1).lower()
                    trigger_keywords = ['dashboard', 'visualization', 'csv', 'chart', 'data']
                    if any(keyword in description for keyword in trigger_keywords):
                        checks.append({'name': 'skill_description_triggers', 'passed': True, 'detail': 'Skill description includes triggering contexts'})
                    else:
                        checks.append({'name': 'skill_description_triggers', 'passed': False, 'detail': 'Skill description lacks clear triggering contexts'})
                else:
                    checks.append({'name': 'skill_description_triggers', 'passed': False, 'detail': 'No description field found in frontmatter'})
            else:
                checks.append({'name': 'skill_description_triggers', 'passed': False, 'detail': 'Malformed frontmatter'})
        else:
            checks.append({'name': 'skill_description_triggers', 'passed': False, 'detail': 'No frontmatter found'})
    else:
        checks.append({'name': 'skill_description_triggers', 'passed': False, 'detail': 'Cannot check - SKILL.md not found'})
    
    # Calculate final score
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.8
    
    return {'passed': passed, 'score': score, 'checks': checks}

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python eval_script.py <workspace_dir>')
        sys.exit(1)
    
    result = evaluate_skill_creation(sys.argv[1])
    print(json.dumps(result, indent=2))