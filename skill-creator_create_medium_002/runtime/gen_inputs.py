import os

# Create the scripts directory and init_skill.py
os.makedirs('scripts', exist_ok=True)

# Create init_skill.py script
init_skill_content = '''#!/usr/bin/env python3
import os
import sys
import argparse

def create_skill_template(skill_name, output_path):
    skill_dir = os.path.join(output_path, skill_name)
    os.makedirs(skill_dir, exist_ok=True)
    
    # Create SKILL.md template
    skill_md_content = f"""---
name: {skill_name}
description: TODO: Add description
---

# {skill_name.replace('-', ' ').title()}

TODO: Add skill content

## Usage

TODO: Describe when and how to use this skill
"""
    
    with open(os.path.join(skill_dir, 'SKILL.md'), 'w') as f:
        f.write(skill_md_content)
    
    # Create example directories
    os.makedirs(os.path.join(skill_dir, 'scripts'), exist_ok=True)
    os.makedirs(os.path.join(skill_dir, 'references'), exist_ok=True)
    os.makedirs(os.path.join(skill_dir, 'assets'), exist_ok=True)
    
    # Create example files
    with open(os.path.join(skill_dir, 'scripts', 'example.py'), 'w') as f:
        f.write('# Example script file\\nprint("Hello from example script!")')
    
    with open(os.path.join(skill_dir, 'references', 'example.md'), 'w') as f:
        f.write('# Example Reference\\n\\nThis is an example reference file.')
    
    with open(os.path.join(skill_dir, 'assets', 'example.txt'), 'w') as f:
        f.write('Example asset file')
    
    print(f"Skill '{skill_name}' created at {skill_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Initialize a new skill')
    parser.add_argument('skill_name', help='Name of the skill to create')
    parser.add_argument('--path', default='.', help='Output directory path')
    
    args = parser.parse_args()
    create_skill_template(args.skill_name, args.path)
'''

with open('scripts/init_skill.py', 'w') as f:
    f.write(init_skill_content)

os.chmod('scripts/init_skill.py', 0o755)

# Create package_skill.py script
package_skill_content = '''#!/usr/bin/env python3
import os
import sys
import yaml
import zipfile
import argparse

def validate_skill(skill_path):
    errors = []
    
    # Check if SKILL.md exists
    skill_md_path = os.path.join(skill_path, 'SKILL.md')
    if not os.path.exists(skill_md_path):
        errors.append('SKILL.md file is missing')
        return errors
    
    # Read and validate SKILL.md
    with open(skill_md_path, 'r') as f:
        content = f.read()
    
    # Check for YAML frontmatter
    if not content.startswith('---\\n'):
        errors.append('SKILL.md must start with YAML frontmatter')
        return errors
    
    try:
        # Extract YAML frontmatter
        yaml_end = content.find('\\n---\\n', 4)
        if yaml_end == -1:
            errors.append('Invalid YAML frontmatter format')
            return errors
        
        yaml_content = content[4:yaml_end]
        metadata = yaml.safe_load(yaml_content)
        
        # Check required fields
        if not metadata.get('name'):
            errors.append('name field is required in YAML frontmatter')
        if not metadata.get('description'):
            errors.append('description field is required in YAML frontmatter')
        
        # Check description quality
        desc = metadata.get('description', '')
        if len(desc) < 20:
            errors.append('description should be more detailed (at least 20 characters)')
            
    except yaml.YAMLError:
        errors.append('Invalid YAML frontmatter syntax')
    
    return errors

def package_skill(skill_path, output_dir='.'):
    # Validate first
    errors = validate_skill(skill_path)
    if errors:
        print('Validation errors:')
        for error in errors:
            print(f'  - {error}')
        sys.exit(1)
    
    # Get skill name from directory
    skill_name = os.path.basename(skill_path.rstrip('/'))
    zip_filename = f'{skill_name}.zip'
    zip_path = os.path.join(output_dir, zip_filename)
    
    # Create zip file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(skill_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, skill_path)
                zipf.write(file_path, arcname)
    
    print(f'Skill packaged successfully: {zip_path}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Package a skill into a zip file')
    parser.add_argument('skill_path', help='Path to the skill directory')
    parser.add_argument('output_dir', nargs='?', default='.', help='Output directory for the zip file')
    
    args = parser.parse_args()
    package_skill(args.skill_path, args.output_dir)
'''

with open('scripts/package_skill.py', 'w') as f:
    f.write(package_skill_content)

os.chmod('scripts/package_skill.py', 0o755)

print('Generated init_skill.py and package_skill.py scripts')