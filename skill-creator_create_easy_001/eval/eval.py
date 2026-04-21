#!/usr/bin/env python3
import sys
import os
import json
import yaml
import glob

def check_skill_structure(workspace_dir):
    checks = []
    
    # Find skill directory
    skill_dirs = [d for d in os.listdir(workspace_dir) if os.path.isdir(os.path.join(workspace_dir, d)) and 'skill' in d.lower()]
    if not skill_dirs:
        checks.append({"name": "skill_directory_exists", "passed": False, "detail": "No skill directory found"})
        return checks, None
    
    skill_dir = os.path.join(workspace_dir, skill_dirs[0])
    checks.append({"name": "skill_directory_exists", "passed": True, "detail": f"Found skill directory: {skill_dirs[0]}"})
    
    # Check SKILL.md exists
    skill_md_path = os.path.join(skill_dir, 'SKILL.md')
    if not os.path.exists(skill_md_path):
        checks.append({"name": "skill_md_exists", "passed": False, "detail": "SKILL.md file not found"})
        return checks, skill_dir
    
    checks.append({"name": "skill_md_exists", "passed": True, "detail": "SKILL.md file found"})
    return checks, skill_dir

def check_skill_md_content(skill_dir):
    checks = []
    skill_md_path = os.path.join(skill_dir, 'SKILL.md')
    
    try:
        with open(skill_md_path, 'r') as f:
            content = f.read()
        
        # Check for YAML frontmatter
        if content.startswith('---'):
            try:
                yaml_end = content.find('---', 3)
                if yaml_end > 0:
                    yaml_content = content[3:yaml_end]
                    metadata = yaml.safe_load(yaml_content)
                    
                    # Check required fields
                    if metadata and isinstance(metadata, dict):
                        if 'name' in metadata:
                            checks.append({"name": "yaml_name_field", "passed": True, "detail": f"Name field present: {metadata['name']}"})
                        else:
                            checks.append({"name": "yaml_name_field", "passed": False, "detail": "Missing required 'name' field in YAML frontmatter"})
                        
                        if 'description' in metadata:
                            checks.append({"name": "yaml_description_field", "passed": True, "detail": "Description field present"})
                        else:
                            checks.append({"name": "yaml_description_field", "passed": False, "detail": "Missing required 'description' field in YAML frontmatter"})
                    else:
                        checks.append({"name": "yaml_parsing", "passed": False, "detail": "Could not parse YAML frontmatter"})
                else:
                    checks.append({"name": "yaml_structure", "passed": False, "detail": "YAML frontmatter not properly closed"})
            except Exception as e:
                checks.append({"name": "yaml_parsing", "passed": False, "detail": f"Error parsing YAML: {str(e)}"})
        else:
            checks.append({"name": "yaml_frontmatter", "passed": False, "detail": "No YAML frontmatter found"})
        
        # Check for markdown content related to markdown processing
        content_lower = content.lower()
        markdown_keywords = ['markdown', 'md', 'table of contents', 'toc', 'syntax', 'format']
        if any(keyword in content_lower for keyword in markdown_keywords):
            checks.append({"name": "relevant_content", "passed": True, "detail": "Content appears relevant to markdown processing"})
        else:
            checks.append({"name": "relevant_content", "passed": False, "detail": "Content does not appear related to markdown processing"})
            
    except Exception as e:
        checks.append({"name": "skill_md_readable", "passed": False, "detail": f"Could not read SKILL.md: {str(e)}"})
    
    return checks

def check_bundled_resources(skill_dir):
    checks = []
    
    # Check for scripts directory
    scripts_dir = os.path.join(skill_dir, 'scripts')
    if os.path.exists(scripts_dir):
        scripts = [f for f in os.listdir(scripts_dir) if f.endswith('.py') or f.endswith('.sh')]
        if scripts:
            checks.append({"name": "scripts_present", "passed": True, "detail": f"Found {len(scripts)} script(s): {', '.join(scripts)}"})
        else:
            checks.append({"name": "scripts_present", "passed": False, "detail": "Scripts directory exists but contains no scripts"})
    else:
        checks.append({"name": "scripts_present", "passed": False, "detail": "No scripts directory found"})
    
    # Check for at least one additional resource directory (references or assets)
    references_dir = os.path.join(skill_dir, 'references')
    assets_dir = os.path.join(skill_dir, 'assets')
    
    additional_resources = False
    if os.path.exists(references_dir) and os.listdir(references_dir):
        additional_resources = True
        checks.append({"name": "references_present", "passed": True, "detail": "References directory with content found"})
    
    if os.path.exists(assets_dir) and os.listdir(assets_dir):
        additional_resources = True
        checks.append({"name": "assets_present", "passed": True, "detail": "Assets directory with content found"})
    
    if not additional_resources:
        checks.append({"name": "additional_resources", "passed": False, "detail": "No references or assets directories with content found"})
    else:
        checks.append({"name": "additional_resources", "passed": True, "detail": "Additional resource directories found"})
    
    return checks

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        return
    
    workspace_dir = sys.argv[1]
    all_checks = []
    
    # Check skill structure
    structure_checks, skill_dir = check_skill_structure(workspace_dir)
    all_checks.extend(structure_checks)
    
    if skill_dir:
        # Check SKILL.md content
        content_checks = check_skill_md_content(skill_dir)
        all_checks.extend(content_checks)
        
        # Check bundled resources
        resource_checks = check_bundled_resources(skill_dir)
        all_checks.extend(resource_checks)
    
    # Calculate score
    passed_checks = sum(1 for check in all_checks if check['passed'])
    total_checks = len(all_checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    overall_passed = score >= 0.8
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": all_checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()