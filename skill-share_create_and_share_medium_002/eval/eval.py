import os
import sys
import json
import yaml
import zipfile
import re
from pathlib import Path

def find_skill_directory(workspace_dir):
    """Search for skill directory in workspace and common subdirectories"""
    # Search in workspace root
    for d in os.listdir(workspace_dir):
        if d.startswith('skill-text-summarizer') or d == 'text-summarizer':
            path = os.path.join(workspace_dir, d)
            if os.path.isdir(path) and os.path.exists(os.path.join(path, 'SKILL.md')):
                return path
    
    # Search in common subdirectories
    for subdir in ['skills', 'skill', 'src']:
        subdir_path = os.path.join(workspace_dir, subdir)
        if os.path.isdir(subdir_path):
            for d in os.listdir(subdir_path):
                if d.startswith('skill-text-summarizer') or d == 'text-summarizer':
                    path = os.path.join(subdir_path, d)
                    if os.path.isdir(path) and os.path.exists(os.path.join(path, 'SKILL.md')):
                        return path
    
    return None

def check_skill_directory_structure(workspace_dir):
    """Check if skill directory was created with proper structure"""
    skill_dir = find_skill_directory(workspace_dir)
    if not skill_dir:
        return False, 'No skill directory found'
    
    # Check for SKILL.md
    skill_md = os.path.join(skill_dir, 'SKILL.md')
    if not os.path.exists(skill_md):
        return False, 'SKILL.md not found'
    
    return True, skill_dir

def check_skill_metadata(skill_dir):
    """Check SKILL.md content and metadata"""
    skill_md = os.path.join(skill_dir, 'SKILL.md')
    
    with open(skill_md, 'r') as f:
        content = f.read().lower()
    
    # Check for YAML frontmatter
    if not content.startswith('---'):
        return False, 'No YAML frontmatter found'
    
    # Extract YAML frontmatter
    yaml_match = re.search(r'^---(.*?)^---', content, re.MULTILINE | re.DOTALL)
    if not yaml_match:
        return False, 'Invalid YAML frontmatter structure'
    
    try:
        yaml_content = yaml.safe_load(yaml_match.group(1))
    except:
        return False, 'Invalid YAML syntax'
    
    # Check required fields
    if 'name' not in yaml_content:
        return False, 'Missing name field in metadata'
    
    if 'description' not in yaml_content:
        return False, 'Missing description field in metadata'
    
    # Check name format (should be hyphen-case)
    name = str(yaml_content['name']).lower()
    if 'text' not in name and 'summarizer' not in name:
        return False, 'Name does not contain expected keywords'
    
    # Check description content
    description = str(yaml_content['description']).lower()
    if not any(keyword in description for keyword in ['summary', 'summariz', 'document', 'text']):
        return False, 'Description does not mention summarization capabilities'
    
    return True, 'Metadata validation passed'

def find_skill_zip(workspace_dir):
    """Search for skill zip file in workspace and common subdirectories"""
    # Search in workspace root
    for f in os.listdir(workspace_dir):
        if f.endswith('.zip') and 'text-summarizer' in f.lower():
            return os.path.join(workspace_dir, f)
    
    # Search in common subdirectories
    for subdir in ['skills', 'skill', 'src']:
        subdir_path = os.path.join(workspace_dir, subdir)
        if os.path.isdir(subdir_path):
            for f in os.listdir(subdir_path):
                if f.endswith('.zip') and 'text-summarizer' in f.lower():
                    return os.path.join(subdir_path, f)
    
    return None

def check_skill_package(workspace_dir):
    """Check if skill was packaged as zip file"""
    zip_path = find_skill_zip(workspace_dir)
    if not zip_path:
        return False, 'No skill package zip file found'
    
    zip_files = [os.path.basename(zip_path)]
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            file_list = zf.namelist()
            if not any('SKILL.md' in f for f in file_list):
                return False, 'SKILL.md not found in package'
            if not any('scripts/' in f for f in file_list):
                return False, 'scripts directory not found in package'
    except:
        return False, 'Invalid or corrupted zip file'
    
    return True, 'Skill package created successfully'

def check_slack_notification(workspace_dir):
    """Check if Slack notification was prepared/sent"""
    # Look for evidence of Slack integration
    files = os.listdir(workspace_dir)
    
    # Check for slack-related files, logs, or output
    slack_indicators = [
        any('slack' in f.lower() for f in files),
        any('notification' in f.lower() for f in files),
        any('message' in f.lower() for f in files)
    ]
    
    # Also check for any files that might contain slack channel references
    for file in files:
        if file.endswith(('.txt', '.log', '.json', '.md')):
            try:
                with open(os.path.join(workspace_dir, file), 'r') as f:
                    content = f.read().lower()
                    if any(keyword in content for keyword in ['#skills-updates', 'slack', 'channel', 'text-summarizer']):
                        return True, 'Slack notification evidence found'
            except:
                continue
    
    if any(slack_indicators):
        return True, 'Slack notification prepared'
    
    return False, 'No evidence of Slack notification'

def main():
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'args', 'passed': False, 'detail': 'Missing workspace directory argument'}]}))
        return
    
    workspace_dir = sys.argv[1]
    checks = []
    
    # Check 1: Skill directory structure
    structure_passed, structure_detail = check_skill_directory_structure(workspace_dir)
    checks.append({
        'name': 'skill_directory_structure',
        'passed': structure_passed,
        'detail': structure_detail
    })
    
    if structure_passed:
        skill_dir = structure_detail
        
        # Check 2: Skill metadata
        metadata_passed, metadata_detail = check_skill_metadata(skill_dir)
        checks.append({
            'name': 'skill_metadata',
            'passed': metadata_passed,
            'detail': metadata_detail
        })
    else:
        checks.append({
            'name': 'skill_metadata',
            'passed': False,
            'detail': 'Cannot check metadata - skill directory not found'
        })
    
    # Check 3: Skill packaging
    package_passed, package_detail = check_skill_package(workspace_dir)
    checks.append({
        'name': 'skill_packaging',
        'passed': package_passed,
        'detail': package_detail
    })
    
    # Check 4: Slack notification
    slack_passed, slack_detail = check_slack_notification(workspace_dir)
    checks.append({
        'name': 'slack_notification',
        'passed': slack_passed,
        'detail': slack_detail
    })
    
    # Calculate score
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score == 1.0
    
    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()