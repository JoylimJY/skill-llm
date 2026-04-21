import sys
import os
import json
import yaml
from pathlib import Path

def main(workspace_path):
    workspace = Path(workspace_path)
    checks = []
    
    # Check 1: Skill directory exists with correct naming convention
    skill_dirs = list(workspace.glob('skill-*'))
    skill_dir_exists = False
    skill_dir_path = None
    
    for skill_dir in skill_dirs:
        if 'text-formatter' in skill_dir.name.lower():
            skill_dir_exists = True
            skill_dir_path = skill_dir
            break
    
    checks.append({
        'name': 'skill_directory_created',
        'passed': skill_dir_exists,
        'detail': f'Found skill directory: {skill_dir_path.name if skill_dir_path else "None"}'
    })
    
    # Check 2: SKILL.md file exists and has proper structure
    skill_md_exists = False
    skill_md_valid = False
    skill_name_correct = False
    skill_desc_correct = False
    
    if skill_dir_path and skill_dir_path.exists():
        skill_md_file = skill_dir_path / 'SKILL.md'
        if skill_md_file.exists():
            skill_md_exists = True
            try:
                content = skill_md_file.read_text()
                # Check for YAML frontmatter
                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        yaml_content = parts[1]
                        metadata = yaml.safe_load(yaml_content)
                        if isinstance(metadata, dict):
                            skill_md_valid = True
                            if 'name' in metadata and 'text-formatter' in metadata['name'].lower():
                                skill_name_correct = True
                            if 'description' in metadata and any(word in metadata['description'].lower() for word in ['format', 'text', 'styling']):
                                skill_desc_correct = True
            except Exception as e:
                pass
    
    checks.append({
        'name': 'skill_md_exists',
        'passed': skill_md_exists,
        'detail': 'SKILL.md file found in skill directory'
    })
    
    checks.append({
        'name': 'skill_md_structure',
        'passed': skill_md_valid,
        'detail': 'SKILL.md has valid YAML frontmatter structure'
    })
    
    checks.append({
        'name': 'skill_name_correct',
        'passed': skill_name_correct,
        'detail': 'Skill name contains text-formatter'
    })
    
    checks.append({
        'name': 'skill_description_correct',
        'passed': skill_desc_correct,
        'detail': 'Skill description mentions formatting/text/styling'
    })
    
    # Check 3: Required directories exist
    required_dirs = ['scripts', 'references', 'assets']
    dirs_created = 0
    
    if skill_dir_path and skill_dir_path.exists():
        for req_dir in required_dirs:
            if (skill_dir_path / req_dir).exists():
                dirs_created += 1
    
    checks.append({
        'name': 'required_directories',
        'passed': dirs_created >= 2,  # At least 2 out of 3 directories
        'detail': f'Created {dirs_created} out of {len(required_dirs)} required directories'
    })
    
    # Check 4: Slack sharing indication (look for any evidence of Slack integration)
    slack_shared = False
    
    # Check for any files or outputs that indicate Slack sharing
    all_files = list(workspace.rglob('*'))
    for file_path in all_files:
        if file_path.is_file():
            try:
                content = file_path.read_text().lower()
                if any(keyword in content for keyword in ['slack', 'general', 'channel', 'message']):
                    slack_shared = True
                    break
            except:
                pass
    
    # Also check for any output or log files that might contain Slack references
    output_files = list(workspace.glob('*.txt')) + list(workspace.glob('*.log')) + list(workspace.glob('*.out'))
    for output_file in output_files:
        try:
            content = output_file.read_text().lower()
            if 'slack' in content or 'general' in content or 'text-formatter' in content:
                slack_shared = True
                break
        except:
            pass
    
    checks.append({
        'name': 'slack_sharing_attempted',
        'passed': slack_shared,
        'detail': 'Evidence of Slack integration or sharing found'
    })
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_count / total_checks
    overall_passed = score >= 0.8
    
    result = {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main(sys.argv[1])