#!/usr/bin/env python3

import os
import sys
import json
import yaml
import zipfile
from pathlib import Path

def check_skill_structure(workspace_dir):
    """Check if skill directory structure was created correctly"""
    skill_dir = None
    for item in os.listdir(workspace_dir):
        if item.startswith('skill-json-validator') or item == 'json-validator':
            skill_dir = os.path.join(workspace_dir, item)
            break
    
    if not skill_dir or not os.path.isdir(skill_dir):
        return False, "Skill directory not found"
    
    required_files = ['SKILL.md']
    required_dirs = ['scripts', 'references', 'assets']
    
    for file in required_files:
        if not os.path.exists(os.path.join(skill_dir, file)):
            return False, f"Missing required file: {file}"
    
    for dir in required_dirs:
        if not os.path.exists(os.path.join(skill_dir, dir)):
            return False, f"Missing required directory: {dir}"
    
    return True, "Skill structure created correctly"

def check_skill_metadata(workspace_dir):
    """Check SKILL.md content and metadata"""
    skill_dirs = [d for d in os.listdir(workspace_dir) if d.startswith('skill-') or d == 'json-validator']
    if not skill_dirs:
        return False, "No skill directory found"
    
    skill_dir = os.path.join(workspace_dir, skill_dirs[0])
    skill_md_path = os.path.join(skill_dir, 'SKILL.md')
    
    if not os.path.exists(skill_md_path):
        return False, "SKILL.md not found"
    
    with open(skill_md_path, 'r') as f:
        content = f.read().lower()
    
    # Check for required metadata fields
    required_fields = ['name:', 'description:', 'license:']
    for field in required_fields:
        if field not in content:
            return False, f"Missing metadata field: {field}"
    
    # Check for skill name and json validation content
    if 'json' not in content and 'validator' not in content:
        return False, "Skill content doesn't mention JSON validation"
    
    return True, "SKILL.md contains proper metadata and content"

def check_skill_package(workspace_dir):
    """Check if skill was packaged as zip file"""
    zip_files = [f for f in os.listdir(workspace_dir) if f.endswith('.zip')]
    
    target_zip = None
    for zip_file in zip_files:
        if 'json-validator' in zip_file.lower() or 'skill' in zip_file.lower():
            target_zip = zip_file
            break
    
    if not target_zip:
        return False, "No skill zip package found"
    
    zip_path = os.path.join(workspace_dir, target_zip)
    
    # Verify zip contains skill files
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            if not any('SKILL.md' in f for f in file_list):
                return False, "Zip package doesn't contain SKILL.md"
            if not any('scripts/' in f for f in file_list):
                return False, "Zip package doesn't contain scripts directory"
    except zipfile.BadZipFile:
        return False, "Invalid zip file created"
    
    return True, f"Skill packaged successfully as {target_zip}"

def check_slack_integration(workspace_dir):
    """Check for evidence of Slack integration attempt"""
    # Look for any files or logs that indicate Slack integration was attempted
    files_to_check = []
    
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            if file.endswith(('.py', '.sh', '.log', '.txt', '.md')):
                files_to_check.append(os.path.join(root, file))
    
    slack_indicators = ['slack', 'rube', '#dev-tools', 'channel', 'message']
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                if any(indicator in content for indicator in slack_indicators):
                    return True, "Slack integration functionality detected"
        except:
            continue
    
    return False, "No evidence of Slack integration found"

def check_naming_convention(workspace_dir):
    """Check if skill follows proper naming conventions"""
    skill_dirs = [d for d in os.listdir(workspace_dir) if os.path.isdir(os.path.join(workspace_dir, d))]
    
    valid_names = ['skill-json-validator', 'json-validator', 'json_validator']
    
    for skill_dir in skill_dirs:
        if any(name in skill_dir.lower() for name in ['json', 'validator']):
            if os.path.exists(os.path.join(workspace_dir, skill_dir, 'SKILL.md')):
                return True, f"Skill directory follows naming convention: {skill_dir}"
    
    return False, "Skill directory doesn't follow proper naming convention"

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Invalid arguments"}]}))
        return
    
    workspace_dir = sys.argv[1]
    
    if not os.path.exists(workspace_dir):
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "workspace", "passed": False, "detail": "Workspace directory not found"}]}))
        return
    
    checks = []
    
    # Check 1: Skill structure
    passed, detail = check_skill_structure(workspace_dir)
    checks.append({"name": "skill_structure", "passed": passed, "detail": detail})
    
    # Check 2: Skill metadata
    passed, detail = check_skill_metadata(workspace_dir)
    checks.append({"name": "skill_metadata", "passed": passed, "detail": detail})
    
    # Check 3: Skill packaging
    passed, detail = check_skill_package(workspace_dir)
    checks.append({"name": "skill_package", "passed": passed, "detail": detail})
    
    # Check 4: Slack integration
    passed, detail = check_slack_integration(workspace_dir)
    checks.append({"name": "slack_integration", "passed": passed, "detail": detail})
    
    # Check 5: Naming convention
    passed, detail = check_naming_convention(workspace_dir)
    checks.append({"name": "naming_convention", "passed": passed, "detail": detail})
    
    # Calculate score
    score = sum(1 for c in checks if c['passed']) / len(checks)
    
    # skill_package is a critical requirement - must pass all checks
    skill_package_passed = any(c['passed'] for c in checks if c['name'] == 'skill_package')
    overall_passed = (score == 1.0) or (score >= 0.8 and skill_package_passed)
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()