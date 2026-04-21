import sys
import os
import zipfile
import yaml
import json
import re
from pathlib import Path

def eval_task(workspace_dir):
    checks = []
    workspace_path = Path(workspace_dir)
    
    # Check 1: Skill zip file exists with correct name
    zip_files = list(workspace_path.glob('*.zip'))
    target_zip = workspace_path / 'react-component-library-builder.zip'
    zip_exists = target_zip.exists()
    checks.append({
        'name': 'skill_zip_exists',
        'passed': zip_exists,
        'detail': f'Found zip file: {zip_exists}'
    })
    
    skill_dir = None
    if zip_exists:
        # Extract and validate zip contents
        try:
            with zipfile.ZipFile(target_zip, 'r') as zf:
                extract_dir = workspace_path / 'extracted_skill'
                zf.extractall(extract_dir)
                skill_dir = extract_dir / 'react-component-library-builder'
                if not skill_dir.exists():
                    # Look for any skill directory
                    skill_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
                    if skill_dirs:
                        skill_dir = skill_dirs[0]
        except Exception as e:
            checks.append({
                'name': 'zip_extraction',
                'passed': False,
                'detail': f'Failed to extract zip: {str(e)}'
            })
            skill_dir = None
    
    if not skill_dir:
        # Look for unzipped skill directory
        potential_dirs = list(workspace_path.glob('*react-component*'))
        if not potential_dirs:
            potential_dirs = [d for d in workspace_path.iterdir() if d.is_dir() and 'skill' in d.name.lower()]
        if potential_dirs:
            skill_dir = potential_dirs[0]
    
    # Check 2: SKILL.md exists and has proper structure
    skill_md_exists = False
    skill_content = ''
    if skill_dir:
        skill_md_path = skill_dir / 'SKILL.md'
        skill_md_exists = skill_md_path.exists()
        if skill_md_exists:
            skill_content = skill_md_path.read_text().lower()
    
    checks.append({
        'name': 'skill_md_exists',
        'passed': skill_md_exists,
        'detail': f'SKILL.md found: {skill_md_exists}'
    })
    
    # Check 3: SKILL.md has proper YAML frontmatter
    yaml_valid = False
    if skill_md_exists:
        try:
            content = (skill_dir / 'SKILL.md').read_text()
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    yaml_content = yaml.safe_load(parts[1])
                    name = yaml_content.get('name', '').lower()
                    desc = yaml_content.get('description', '').lower()
                    yaml_valid = 'react' in name and 'component' in desc and len(desc) > 20
        except:
            yaml_valid = False
    
    checks.append({
        'name': 'yaml_frontmatter_valid',
        'passed': yaml_valid,
        'detail': f'Valid YAML frontmatter with React component description: {yaml_valid}'
    })
    
    # Check 4: Assets directory with React component template
    assets_valid = False
    if skill_dir:
        assets_dir = skill_dir / 'assets'
        if assets_dir.exists():
            # Look for TypeScript React files
            ts_files = list(assets_dir.rglob('*.ts')) + list(assets_dir.rglob('*.tsx'))
            for ts_file in ts_files:
                content = ts_file.read_text().lower()
                if any(keyword in content for keyword in ['react', 'component', 'interface', 'props']):
                    assets_valid = True
                    break
    
    checks.append({
        'name': 'assets_react_template',
        'passed': assets_valid,
        'detail': f'Assets directory contains React TypeScript template: {assets_valid}'
    })
    
    # Check 5: References directory with best practices guide
    references_valid = False
    if skill_dir:
        references_dir = skill_dir / 'references'
        if references_dir.exists():
            for ref_file in references_dir.glob('*.md'):
                content = ref_file.read_text().lower()
                if any(keyword in content for keyword in ['component', 'best practice', 'typescript', 'react']):
                    references_valid = True
                    break
    
    checks.append({
        'name': 'references_best_practices',
        'passed': references_valid,
        'detail': f'References directory contains component best practices: {references_valid}'
    })
    
    # Check 6: Scripts directory with Python scaffolding script
    scripts_valid = False
    if skill_dir:
        scripts_dir = skill_dir / 'scripts'
        if scripts_dir.exists():
            for script_file in scripts_dir.glob('*.py'):
                content = script_file.read_text().lower()
                if any(keyword in content for keyword in ['component', 'scaffold', 'def', 'import']):
                    scripts_valid = True
                    break
    
    checks.append({
        'name': 'scripts_scaffolding',
        'passed': scripts_valid,
        'detail': f'Scripts directory contains Python scaffolding script: {scripts_valid}'
    })
    
    # Check 7: SKILL.md content explains when to use skill
    usage_explained = False
    if skill_content:
        usage_keywords = ['when', 'use', 'skill', 'component', 'library']
        usage_explained = sum(1 for keyword in usage_keywords if keyword in skill_content) >= 3
    
    checks.append({
        'name': 'usage_explanation',
        'passed': usage_explained,
        'detail': f'SKILL.md explains when to use the skill: {usage_explained}'
    })
    
    # Check 8: SKILL.md references bundled resources
    resources_referenced = False
    if skill_content:
        resource_refs = ['assets', 'references', 'scripts']
        resources_referenced = sum(1 for ref in resource_refs if ref in skill_content) >= 2
    
    checks.append({
        'name': 'resources_referenced',
        'passed': resources_referenced,
        'detail': f'SKILL.md references bundled resources: {resources_referenced}'
    })
    
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8
    
    return {
        'passed': passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    result = eval_task(sys.argv[1])
    print(json.dumps(result))