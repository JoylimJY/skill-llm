import sys
import os
import json
import re
from pathlib import Path

def main():
    workspace = sys.argv[1]
    workspace_path = Path(workspace)
    
    checks = []
    
    # Check 1: data-visualization skill directory exists
    skill_dir = workspace_path / 'data-visualization'
    skill_exists = skill_dir.exists() and skill_dir.is_dir()
    checks.append({
        'name': 'Skill directory created',
        'passed': skill_exists,
        'detail': f'Found data-visualization directory: {skill_exists}'
    })
    
    # Check 2: SKILL.md with proper frontmatter
    skill_md_valid = False
    skill_md_path = skill_dir / 'SKILL.md' if skill_exists else None
    if skill_md_path and skill_md_path.exists():
        content = skill_md_path.read_text().lower()
        has_name = 'name:' in content and 'data-visualization' in content
        has_desc = 'description:' in content and any(word in content for word in ['chart', 'dashboard', 'csv', 'visualization'])
        has_frontmatter = content.strip().startswith('---')
        skill_md_valid = has_name and has_desc and has_frontmatter
    
    checks.append({
        'name': 'SKILL.md with valid frontmatter',
        'passed': skill_md_valid,
        'detail': f'SKILL.md exists with proper name and description: {skill_md_valid}'
    })
    
    # Check 3: chart_generator.py script exists
    script_exists = False
    scripts_dir = skill_dir / 'scripts' if skill_exists else None
    if scripts_dir and scripts_dir.exists():
        chart_script = scripts_dir / 'chart_generator.py'
        if chart_script.exists():
            script_content = chart_script.read_text().lower()
            has_plotly = 'plotly' in script_content
            has_csv = 'csv' in script_content or 'pandas' in script_content
            script_exists = has_plotly and has_csv
    
    checks.append({
        'name': 'Chart generator script created',
        'passed': script_exists,
        'detail': f'scripts/chart_generator.py with plotly and CSV handling: {script_exists}'
    })
    
    # Check 4: chart_types.md reference document
    ref_exists = False
    ref_dir = skill_dir / 'references' if skill_exists else None
    if ref_dir and ref_dir.exists():
        chart_types = ref_dir / 'chart_types.md'
        if chart_types.exists():
            ref_content = chart_types.read_text().lower()
            has_chart_info = any(word in ref_content for word in ['bar', 'line', 'pie', 'scatter', 'histogram'])
            ref_exists = has_chart_info and len(ref_content) > 100
    
    checks.append({
        'name': 'Chart types reference document',
        'passed': ref_exists,
        'detail': f'references/chart_types.md with visualization guidance: {ref_exists}'
    })
    
    # Check 5: evals.json with test cases
    evals_valid = False
    evals_dir = skill_dir / 'evals' if skill_exists else None
    if evals_dir and evals_dir.exists():
        evals_file = evals_dir / 'evals.json'
        if evals_file.exists():
            try:
                evals_data = json.loads(evals_file.read_text())
                has_skill_name = evals_data.get('skill_name') == 'data-visualization'
                evals_list = evals_data.get('evals', [])
                has_three_evals = len(evals_list) >= 3
                all_have_prompts = all('prompt' in eval_item for eval_item in evals_list)
                evals_valid = has_skill_name and has_three_evals and all_have_prompts
            except (json.JSONDecodeError, AttributeError):
                pass
    
    checks.append({
        'name': 'Evaluation test cases created',
        'passed': evals_valid,
        'detail': f'evals/evals.json with 3+ test cases: {evals_valid}'
    })
    
    # Check 6: Workspace directory with evaluation results
    workspace_created = False
    workspace_dirs = list(workspace_path.glob('*-workspace'))
    if workspace_dirs:
        for ws_dir in workspace_dirs:
            if any((ws_dir / subdir).exists() for subdir in ['iteration-1', 'eval-0', 'eval-1']):
                workspace_created = True
                break
    
    checks.append({
        'name': 'Evaluation workspace created',
        'passed': workspace_created,
        'detail': f'Found evaluation workspace with results: {workspace_created}'
    })
    
    # Check 7: HTML viewer files or static output
    viewer_created = False
    html_files = list(workspace_path.glob('**/*.html'))
    viewer_created = len(html_files) > 0
    
    checks.append({
        'name': 'Evaluation viewer generated',
        'passed': viewer_created,
        'detail': f'Found HTML viewer files: {viewer_created}'
    })
    
    # Check 8: Packaged skill file
    skill_packaged = False
    skill_files = list(workspace_path.glob('**/*.skill'))
    for skill_file in skill_files:
        if 'data-visualization' in skill_file.name:
            skill_packaged = True
            break
    
    checks.append({
        'name': 'Skill packaged as .skill file',
        'passed': skill_packaged,
        'detail': f'Found data-visualization.skill package: {skill_packaged}'
    })
    
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8
    
    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()