#!/usr/bin/env python3
import os
import sys
import json
import yaml
import zipfile
from pathlib import Path
import re

def check_skill_structure(workspace_dir):
    """Check if skill directory structure is correct"""
    checks = []
    
    # Look for employee-onboarding directory
    skill_dirs = [d for d in os.listdir(workspace_dir) if os.path.isdir(os.path.join(workspace_dir, d)) and 'onboard' in d.lower()]
    
    if not skill_dirs:
        checks.append({"name": "skill_directory_exists", "passed": False, "detail": "No onboarding skill directory found"})
        return checks, None
    
    # Use the first matching directory
    skill_dir = os.path.join(workspace_dir, skill_dirs[0])
    checks.append({"name": "skill_directory_exists", "passed": True, "detail": f"Found skill directory: {skill_dirs[0]}"})
    
    return checks, skill_dir

def check_skill_md(skill_dir):
    """Check SKILL.md file content and structure"""
    checks = []
    
    skill_md_path = os.path.join(skill_dir, 'SKILL.md')
    if not os.path.exists(skill_md_path):
        checks.append({"name": "skill_md_exists", "passed": False, "detail": "SKILL.md file not found"})
        return checks
    
    checks.append({"name": "skill_md_exists", "passed": True, "detail": "SKILL.md file exists"})
    
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check YAML frontmatter
    if content.startswith('---'):
        checks.append({"name": "yaml_frontmatter", "passed": True, "detail": "YAML frontmatter present"})
        
        try:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                
                # Check name field
                if frontmatter.get('name') and 'onboard' in frontmatter['name'].lower():
                    checks.append({"name": "skill_name_correct", "passed": True, "detail": f"Skill name: {frontmatter['name']}"})
                else:
                    checks.append({"name": "skill_name_correct", "passed": False, "detail": "Skill name missing or incorrect"})
                
                # Check description
                description = frontmatter.get('description', '')
                if len(description) >= 20 and any(keyword in description.lower() for keyword in ['onboard', 'employee', 'hire']):
                    checks.append({"name": "skill_description", "passed": True, "detail": "Description adequate and relevant"})
                else:
                    checks.append({"name": "skill_description", "passed": False, "detail": "Description missing, too short, or not relevant"})
                
                body = parts[2].strip()
                if len(body) >= 100:
                    checks.append({"name": "skill_body_content", "passed": True, "detail": f"Body content length: {len(body)} characters"})
                else:
                    checks.append({"name": "skill_body_content", "passed": False, "detail": "Body content too short"})
            else:
                checks.append({"name": "yaml_frontmatter", "passed": False, "detail": "Invalid YAML frontmatter format"})
        except yaml.YAMLError:
            checks.append({"name": "yaml_frontmatter", "passed": False, "detail": "YAML frontmatter parsing error"})
    else:
        checks.append({"name": "yaml_frontmatter", "passed": False, "detail": "No YAML frontmatter found"})
    
    return checks

def check_scripts_directory(skill_dir):
    """Check scripts directory and PDF generation script"""
    checks = []
    
    scripts_dir = os.path.join(skill_dir, 'scripts')
    if not os.path.exists(scripts_dir):
        checks.append({"name": "scripts_directory", "passed": False, "detail": "Scripts directory not found"})
        return checks
    
    checks.append({"name": "scripts_directory", "passed": True, "detail": "Scripts directory exists"})
    
    # Look for PDF generation script
    script_files = [f for f in os.listdir(scripts_dir) if f.endswith('.py')]
    pdf_script_found = False
    
    for script_file in script_files:
        script_path = os.path.join(scripts_dir, script_file)
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            if any(keyword in content for keyword in ['pdf', 'welcome', 'packet']):
                pdf_script_found = True
                break
    
    if pdf_script_found:
        checks.append({"name": "pdf_generation_script", "passed": True, "detail": "PDF generation script found"})
    else:
        checks.append({"name": "pdf_generation_script", "passed": False, "detail": "PDF generation script not found"})
    
    return checks

def check_references_directory(skill_dir):
    """Check references directory and policy documents"""
    checks = []
    
    references_dir = os.path.join(skill_dir, 'references')
    if not os.path.exists(references_dir):
        checks.append({"name": "references_directory", "passed": False, "detail": "References directory not found"})
        return checks
    
    checks.append({"name": "references_directory", "passed": True, "detail": "References directory exists"})
    
    # Look for policy and IT procedure documents
    ref_files = [f for f in os.listdir(references_dir) if f.endswith('.md')]
    policy_found = False
    it_found = False
    
    for ref_file in ref_files:
        ref_path = os.path.join(references_dir, ref_file)
        with open(ref_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            if any(keyword in content for keyword in ['policy', 'policies', 'hr']):
                policy_found = True
            if any(keyword in content for keyword in ['it', 'setup', 'procedure']):
                it_found = True
    
    if policy_found:
        checks.append({"name": "policy_documentation", "passed": True, "detail": "Policy documentation found"})
    else:
        checks.append({"name": "policy_documentation", "passed": False, "detail": "Policy documentation not found"})
    
    if it_found:
        checks.append({"name": "it_procedures", "passed": True, "detail": "IT procedures documentation found"})
    else:
        checks.append({"name": "it_procedures", "passed": False, "detail": "IT procedures documentation not found"})
    
    return checks

def check_assets_directory(skill_dir):
    """Check assets directory and template files"""
    checks = []
    
    assets_dir = os.path.join(skill_dir, 'assets')
    if not os.path.exists(assets_dir):
        checks.append({"name": "assets_directory", "passed": False, "detail": "Assets directory not found"})
        return checks
    
    checks.append({"name": "assets_directory", "passed": True, "detail": "Assets directory exists"})
    
    # Check for template files
    asset_files = os.listdir(assets_dir)
    template_found = any(
        any(keyword in f.lower() for keyword in ['template', 'checklist', 'schedule'])
        for f in asset_files
    )
    
    if template_found or len(asset_files) > 0:
        checks.append({"name": "template_assets", "passed": True, "detail": f"Template assets found: {len(asset_files)} files"})
    else:
        checks.append({"name": "template_assets", "passed": False, "detail": "No template assets found"})
    
    return checks

def check_packaging(workspace_dir):
    """Check if skill is properly packaged as zip file"""
    checks = []
    
    # Look for zip files
    zip_files = [f for f in os.listdir(workspace_dir) if f.endswith('.zip') and 'onboard' in f.lower()]
    
    if not zip_files:
        checks.append({"name": "skill_packaging", "passed": False, "detail": "No onboarding skill zip file found"})
        return checks
    
    zip_path = os.path.join(workspace_dir, zip_files[0])
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            file_list = zipf.namelist()
            
            # Check for required structure
            has_skill_md = any('SKILL.md' in f for f in file_list)
            has_scripts = any('scripts/' in f for f in file_list)
            has_references = any('references/' in f for f in file_list)
            has_assets = any('assets/' in f for f in file_list)
            
            structure_score = sum([has_skill_md, has_scripts, has_references, has_assets])
            
            if structure_score >= 3:  # At least 3 out of 4 components
                checks.append({"name": "skill_packaging", "passed": True, "detail": f"Skill properly packaged with {structure_score}/4 components"})
            else:
                checks.append({"name": "skill_packaging", "passed": False, "detail": f"Incomplete packaging: {structure_score}/4 components found"})
                
    except zipfile.BadZipFile:
        checks.append({"name": "skill_packaging", "passed": False, "detail": "Invalid zip file format"})
    
    return checks

def main(workspace_dir):
    all_checks = []
    
    # Check skill directory structure
    structure_checks, skill_dir = check_skill_structure(workspace_dir)
    all_checks.extend(structure_checks)
    
    if skill_dir:
        # Check SKILL.md file
        all_checks.extend(check_skill_md(skill_dir))
        
        # Check scripts directory
        all_checks.extend(check_scripts_directory(skill_dir))
        
        # Check references directory
        all_checks.extend(check_references_directory(skill_dir))
        
        # Check assets directory
        all_checks.extend(check_assets_directory(skill_dir))
    
    # Check packaging
    all_checks.extend(check_packaging(workspace_dir))
    
    # Calculate score
    passed_count = sum(1 for check in all_checks if check['passed'])
    total_count = len(all_checks)
    score = passed_count / total_count if total_count > 0 else 0.0
    
    result = {
        "passed": score >= 0.8,
        "score": score,
        "checks": all_checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: eval_script.py <workspace_dir>")
        sys.exit(1)
    
    main(sys.argv[1])