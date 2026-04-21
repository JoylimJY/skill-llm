import sys
import os
import json
import yaml
import re
from pathlib import Path

def main(workspace_dir):
    checks = []
    
    # Check 1: Skill directory created with correct naming convention
    skill_dir = None
    for item in os.listdir(workspace_dir):
        if item.startswith('skill-text-formatter') or item == 'text-formatter':
            skill_dir = os.path.join(workspace_dir, item)
            break
    
    if skill_dir and os.path.isdir(skill_dir):
        checks.append({"name": "skill_directory_created", "passed": True, "detail": "Skill directory found"})
    else:
        checks.append({"name": "skill_directory_created", "passed": False, "detail": "Skill directory not found"})
        skill_dir = None
    
    # Check 2: SKILL.md file exists
    skill_md_exists = False
    skill_md_path = None
    if skill_dir:
        skill_md_path = os.path.join(skill_dir, 'SKILL.md')
        skill_md_exists = os.path.exists(skill_md_path)
    
    if skill_md_exists:
        checks.append({"name": "skill_md_exists", "passed": True, "detail": "SKILL.md file found"})
    else:
        checks.append({"name": "skill_md_exists", "passed": False, "detail": "SKILL.md file not found"})
    
    # Check 3: SKILL.md has proper YAML frontmatter
    yaml_valid = False
    skill_content = ""
    if skill_md_exists:
        try:
            with open(skill_md_path, 'r') as f:
                skill_content = f.read().lower()
            
            # Check for YAML frontmatter markers
            if skill_content.startswith('---') and '---' in skill_content[3:]:
                yaml_section = skill_content.split('---')[1]
                yaml_data = yaml.safe_load(yaml_section)
                if isinstance(yaml_data, dict) and 'name' in yaml_data and 'description' in yaml_data:
                    yaml_valid = True
        except Exception as e:
            pass
    
    if yaml_valid:
        checks.append({"name": "yaml_frontmatter_valid", "passed": True, "detail": "YAML frontmatter is properly formatted"})
    else:
        checks.append({"name": "yaml_frontmatter_valid", "passed": False, "detail": "YAML frontmatter missing or invalid"})
    
    # Check 4: Skill name matches expected
    name_correct = False
    if yaml_valid and skill_content:
        if 'text-formatter' in skill_content or 'text_formatter' in skill_content:
            name_correct = True
    
    if name_correct:
        checks.append({"name": "skill_name_correct", "passed": True, "detail": "Skill name matches expected"})
    else:
        checks.append({"name": "skill_name_correct", "passed": False, "detail": "Skill name does not match expected"})
    
    # Check 5: Description contains formatting-related content
    description_valid = False
    if skill_content:
        format_keywords = ['format', 'text', 'case', 'transform', 'utility']
        if any(keyword in skill_content for keyword in format_keywords):
            description_valid = True
    
    if description_valid:
        checks.append({"name": "description_relevant", "passed": True, "detail": "Description contains relevant formatting content"})
    else:
        checks.append({"name": "description_relevant", "passed": False, "detail": "Description does not mention formatting functionality"})
    
    # Check 6: Standard directories created
    standard_dirs = ['scripts', 'references', 'assets']
    dirs_created = 0
    if skill_dir:
        for dir_name in standard_dirs:
            dir_path = os.path.join(skill_dir, dir_name)
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                dirs_created += 1
    
    if dirs_created >= 2:  # Allow some flexibility
        checks.append({"name": "standard_directories", "passed": True, "detail": f"{dirs_created} standard directories created"})
    else:
        checks.append({"name": "standard_directories", "passed": False, "detail": f"Only {dirs_created} standard directories found"})
    
    # Check 7: Evidence of Slack integration attempt
    slack_attempted = False
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    if any(keyword in content for keyword in ['slack', 'webhook', 'channel', '#general', 'post', 'message']):
                        slack_attempted = True
                        break
            except:
                continue
        if slack_attempted:
            break
    
    if slack_attempted:
        checks.append({"name": "slack_integration_attempted", "passed": True, "detail": "Evidence of Slack integration found"})
    else:
        checks.append({"name": "slack_integration_attempted", "passed": False, "detail": "No evidence of Slack integration attempt"})
    
    # Calculate score and overall pass
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.8
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main(sys.argv[1])