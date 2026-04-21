#!/usr/bin/env python3
import os
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Create init_skill.py script
with open('init_skill.py', 'w') as f:
    f.write('''#!/usr/bin/env python3
import os
import sys
import argparse

def create_skill_template(skill_name, output_path):
    skill_dir = os.path.join(output_path, skill_name)
    os.makedirs(skill_dir, exist_ok=True)
    
    # Create SKILL.md template
    skill_md = f"""---
name: {skill_name}
description: TODO: Add description
license: Complete terms in LICENSE.txt
---

# {skill_name.replace('-', ' ').title()}

TODO: Add skill content

## Usage

TODO: Add usage instructions
"""
    
    with open(os.path.join(skill_dir, 'SKILL.md'), 'w') as f:
        f.write(skill_md)
    
    # Create example directories
    for subdir in ['scripts', 'references', 'assets']:
        subdir_path = os.path.join(skill_dir, subdir)
        os.makedirs(subdir_path, exist_ok=True)
        
        # Create example files
        if subdir == 'scripts':
            with open(os.path.join(subdir_path, 'example.py'), 'w') as f:
                f.write('# Example script\nprint("Hello from script")\n')
        elif subdir == 'references':
            with open(os.path.join(subdir_path, 'example.md'), 'w') as f:
                f.write('# Example Reference\nThis is example reference documentation.\n')
        elif subdir == 'assets':
            with open(os.path.join(subdir_path, 'example.txt'), 'w') as f:
                f.write('Example asset file\n')
    
    print(f"Created skill template at {skill_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Initialize a new skill')
    parser.add_argument('skill_name', help='Name of the skill')
    parser.add_argument('--path', default='.', help='Output directory path')
    args = parser.parse_args()
    
    create_skill_template(args.skill_name, args.path)
''')

# Create package_skill.py script
with open('package_skill.py', 'w') as f:
    f.write('''#!/usr/bin/env python3
import os
import sys
import yaml
import zipfile
import argparse
from pathlib import Path

def validate_skill(skill_path):
    """Validate skill structure and content"""
    errors = []
    
    skill_md_path = os.path.join(skill_path, 'SKILL.md')
    if not os.path.exists(skill_md_path):
        errors.append("Missing SKILL.md file")
        return errors
    
    with open(skill_md_path, 'r') as f:
        content = f.read()
    
    # Check for YAML frontmatter
    if not content.startswith('---'):
        errors.append("Missing YAML frontmatter")
        return errors
    
    try:
        parts = content.split('---', 2)
        if len(parts) < 3:
            errors.append("Invalid YAML frontmatter format")
            return errors
        
        frontmatter = yaml.safe_load(parts[1])
        
        # Validate required fields
        if 'name' not in frontmatter:
            errors.append("Missing 'name' in frontmatter")
        elif not isinstance(frontmatter['name'], str) or not frontmatter['name'].strip():
            errors.append("'name' must be a non-empty string")
        
        if 'description' not in frontmatter:
            errors.append("Missing 'description' in frontmatter")
        elif not isinstance(frontmatter['description'], str) or len(frontmatter['description'].strip()) < 20:
            errors.append("'description' must be at least 20 characters")
        
        # Validate skill naming convention
        skill_name = frontmatter.get('name', '')
        if skill_name and not skill_name.replace('-', '').replace('_', '').isalnum():
            errors.append("Skill name should only contain alphanumeric characters, hyphens, and underscores")
        
        # Check body content
        body = parts[2].strip()
        if len(body) < 100:
            errors.append("SKILL.md body content too short (minimum 100 characters)")
        
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML frontmatter: {e}")
    
    return errors

def package_skill(skill_path, output_dir=None):
    """Package skill into zip file after validation"""
    skill_path = Path(skill_path).resolve()
    
    if not skill_path.exists():
        print(f"Error: Skill directory {skill_path} does not exist")
        return False
    
    # Validate skill
    errors = validate_skill(skill_path)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    # Determine output directory and filename
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = skill_path.parent
    
    skill_name = skill_path.name
    zip_filename = f"{skill_name}.zip"
    zip_path = output_dir / zip_filename
    
    # Create zip file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(skill_path):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(skill_path.parent)
                zipf.write(file_path, arcname)
    
    print(f"Successfully packaged skill to {zip_path}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Package a skill into a zip file')
    parser.add_argument('skill_path', help='Path to the skill directory')
    parser.add_argument('output_dir', nargs='?', help='Output directory for the zip file')
    args = parser.parse_args()
    
    success = package_skill(args.skill_path, args.output_dir)
    sys.exit(0 if success else 1)
''')

# Make scripts executable
os.chmod('init_skill.py', 0o755)
os.chmod('package_skill.py', 0o755)

# Create sample company policy document
with open('company_policies.md', 'w') as f:
    f.write('''# Company Policies

## IT Security Policies
- MARKER_IT_SECURITY: All devices must have encryption enabled
- Password requirements: minimum 12 characters
- Two-factor authentication mandatory

## HR Policies
- MARKER_HR_POLICY: New employees have 90-day probation period
- Vacation accrual starts after 30 days
- Remote work policy allows 2 days per week

## Training Requirements
- MARKER_TRAINING: Security awareness training within first week
- Department-specific training within first month
- Compliance training quarterly
''')

# Create sample IT procedures document
with open('it_procedures.md', 'w') as f:
    f.write('''# IT Setup Procedures

## Hardware Setup
- MARKER_HARDWARE: Laptop configuration and imaging
- Monitor and peripherals assignment
- Network access provisioning

## Software Installation
- MARKER_SOFTWARE: Standard software package deployment
- Role-specific application installation
- License assignment and tracking

## Account Creation
- MARKER_ACCOUNTS: Active Directory account creation
- Email account setup
- Application access provisioning
''')

print("Generated input files successfully")