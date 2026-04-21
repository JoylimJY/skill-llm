import os
import sys
import json
import zipfile
import yaml
import re
from pathlib import Path

def check_skill_package(workspace_path):
    checks = []
    
    # Find zip files in workspace
    zip_files = list(Path(workspace_path).glob('*.zip'))
    
    if not zip_files:
        checks.append({"name": "skill_package_exists", "passed": False, "detail": "No zip file found in workspace"})
        return checks
    
    # Use the first zip file found
    zip_path = zip_files[0]
    checks.append({"name": "skill_package_exists", "passed": True, "detail": f"Found skill package: {zip_path.name}"})
    
    # Extract and examine zip contents
    extract_dir = Path(workspace_path) / "extracted_skill"
    extract_dir.mkdir(exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    except Exception as e:
        checks.append({"name": "zip_extraction", "passed": False, "detail": f"Failed to extract zip: {str(e)}"})
        return checks
    
    checks.append({"name": "zip_extraction", "passed": True, "detail": "Successfully extracted skill package"})
    
    # Find skill directory (should be api-documentation-generator or similar)
    skill_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
    
    if not skill_dirs:
        checks.append({"name": "skill_directory_structure", "passed": False, "detail": "No skill directory found in package"})
        return checks
    
    skill_dir = skill_dirs[0]
    checks.append({"name": "skill_directory_structure", "passed": True, "detail": f"Found skill directory: {skill_dir.name}"})
    
    # Check for SKILL.md
    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        checks.append({"name": "skill_md_exists", "passed": False, "detail": "SKILL.md file not found"})
        return checks
    
    checks.append({"name": "skill_md_exists", "passed": True, "detail": "SKILL.md file found"})
    
    # Read and validate SKILL.md content
    try:
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        checks.append({"name": "skill_md_readable", "passed": False, "detail": f"Could not read SKILL.md: {str(e)}"})
        return checks
    
    checks.append({"name": "skill_md_readable", "passed": True, "detail": "SKILL.md is readable"})
    
    # Check YAML frontmatter
    if not content.startswith('---'):
        checks.append({"name": "yaml_frontmatter", "passed": False, "detail": "SKILL.md missing YAML frontmatter"})
    else:
        try:
            # Extract frontmatter
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                
                # Check required fields
                if 'name' in frontmatter and 'description' in frontmatter:
                    checks.append({"name": "yaml_frontmatter", "passed": True, "detail": "Valid YAML frontmatter with required fields"})
                    
                    # Check if name relates to API documentation
                    name_check = any(keyword in frontmatter['name'].lower() for keyword in ['api', 'documentation', 'doc'])
                    checks.append({"name": "skill_name_appropriate", "passed": name_check, "detail": f"Skill name: {frontmatter['name']}"})
                    
                    # Check if description mentions OpenAPI or API documentation
                    desc_check = any(keyword in frontmatter['description'].lower() for keyword in ['openapi', 'api documentation', 'swagger', 'api doc'])
                    checks.append({"name": "skill_description_appropriate", "passed": desc_check, "detail": f"Description mentions relevant keywords: {desc_check}"})
                else:
                    checks.append({"name": "yaml_frontmatter", "passed": False, "detail": "Frontmatter missing required 'name' or 'description' fields"})
            else:
                checks.append({"name": "yaml_frontmatter", "passed": False, "detail": "Invalid frontmatter format"})
        except Exception as e:
            checks.append({"name": "yaml_frontmatter", "passed": False, "detail": f"Error parsing frontmatter: {str(e)}"})
    
    # Check main content discusses API documentation generation
    content_lower = content.lower()
    api_content_check = any(keyword in content_lower for keyword in ['openapi', 'swagger', 'api documentation', 'markdown documentation'])
    checks.append({"name": "skill_content_relevant", "passed": api_content_check, "detail": f"Content discusses API documentation: {api_content_check}"})
    
    # Check for bundled resources (scripts, references, or assets)
    has_scripts = (skill_dir / "scripts").exists() and any((skill_dir / "scripts").iterdir())
    has_references = (skill_dir / "references").exists() and any((skill_dir / "references").iterdir())
    has_assets = (skill_dir / "assets").exists() and any((skill_dir / "assets").iterdir())
    
    bundled_resources = has_scripts or has_references or has_assets
    resource_detail = f"Scripts: {has_scripts}, References: {has_references}, Assets: {has_assets}"
    checks.append({"name": "bundled_resources", "passed": bundled_resources, "detail": resource_detail})
    
    # Check content structure and quality (imperative form, clear instructions)
    has_clear_purpose = any(phrase in content_lower for phrase in ['purpose', 'when to use', 'use this skill when'])
    has_instructions = any(phrase in content_lower for phrase in ['to generate', 'to create', 'process', 'workflow'])
    
    structure_check = has_clear_purpose and has_instructions
    checks.append({"name": "content_structure", "passed": structure_check, "detail": f"Clear purpose and instructions: {structure_check}"})
    
    return checks

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Missing workspace path argument"}]}))
        return
    
    workspace_path = sys.argv[1]
    
    if not os.path.exists(workspace_path):
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "workspace", "passed": False, "detail": "Workspace path does not exist"}]}))
        return
    
    checks = check_skill_package(workspace_path)
    
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.8
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()