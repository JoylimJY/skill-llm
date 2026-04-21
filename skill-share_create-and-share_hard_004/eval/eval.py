import os
import sys
import json
import yaml
import zipfile
from pathlib import Path

def check_skill_directory_structure(workspace_dir):
    """Check if skill directory was created with proper structure"""
    skill_dirs = [d for d in os.listdir(workspace_dir) if d.startswith('skill-database-migrator') or d == 'database-migrator']
    
    if not skill_dirs:
        return False, "No skill directory found"
    
    skill_dir = os.path.join(workspace_dir, skill_dirs[0])
    if not os.path.isdir(skill_dir):
        return False, f"Found {skill_dirs[0]} but it's not a directory"
    
    required_dirs = ['scripts', 'references', 'assets']
    for req_dir in required_dirs:
        dir_path = os.path.join(skill_dir, req_dir)
        if not os.path.exists(dir_path):
            return False, f"Missing required directory: {req_dir}"
    
    return True, f"Skill directory {skill_dirs[0]} created with proper structure"

def check_skill_md_file(workspace_dir):
    """Check if SKILL.md exists and has proper format"""
    skill_dirs = [d for d in os.listdir(workspace_dir) if 'database-migrator' in d.lower() and os.path.isdir(os.path.join(workspace_dir, d))]
    
    if not skill_dirs:
        return False, "No skill directory found for SKILL.md check"
    
    skill_dir = os.path.join(workspace_dir, skill_dirs[0])
    skill_md_path = os.path.join(skill_dir, 'SKILL.md')
    
    if not os.path.exists(skill_md_path):
        return False, "SKILL.md file not found"
    
    with open(skill_md_path, 'r') as f:
        content = f.read().lower()
    
    # Check for required elements
    required_elements = [
        'database-migrator',
        'migrate',
        'database',
        'name:',
        'description:'
    ]
    
    missing = [elem for elem in required_elements if elem not in content]
    if missing:
        return False, f"SKILL.md missing required elements: {missing}"
    
    return True, "SKILL.md file created with proper metadata"

def check_migration_scripts(workspace_dir):
    """Check if migration utility scripts were created"""
    skill_dirs = [d for d in os.listdir(workspace_dir) if 'database-migrator' in d.lower() and os.path.isdir(os.path.join(workspace_dir, d))]
    
    if not skill_dirs:
        return False, "No skill directory found for scripts check"
    
    skill_dir = os.path.join(workspace_dir, skill_dirs[0])
    scripts_dir = os.path.join(skill_dir, 'scripts')
    
    if not os.path.exists(scripts_dir):
        return False, "Scripts directory not found"
    
    # Look for Python files in scripts directory
    python_files = [f for f in os.listdir(scripts_dir) if f.endswith('.py')]
    
    if not python_files:
        return False, "No Python migration scripts found in scripts directory"
    
    # Check if at least one script contains migration-related content
    migration_keywords = ['migrate', 'database', 'transfer', 'export', 'import']
    found_migration_content = False
    
    for py_file in python_files:
        try:
            with open(os.path.join(scripts_dir, py_file), 'r') as f:
                content = f.read().lower()
                if any(keyword in content for keyword in migration_keywords):
                    found_migration_content = True
                    break
        except:
            continue
    
    if not found_migration_content:
        return False, "Scripts directory exists but no migration-related content found"
    
    return True, f"Migration scripts created in scripts directory ({len(python_files)} Python files)"

def check_reference_files(workspace_dir):
    """Check if reference files with database schemas were included"""
    skill_dirs = [d for d in os.listdir(workspace_dir) if 'database-migrator' in d.lower() and os.path.isdir(os.path.join(workspace_dir, d))]
    
    if not skill_dirs:
        return False, "No skill directory found for references check"
    
    skill_dir = os.path.join(workspace_dir, skill_dirs[0])
    references_dir = os.path.join(skill_dir, 'references')
    
    if not os.path.exists(references_dir):
        return False, "References directory not found"
    
    # Look for SQL or schema files
    schema_files = [f for f in os.listdir(references_dir) if f.endswith(('.sql', '.md', '.txt'))]
    
    if not schema_files:
        return False, "No schema reference files found in references directory"
    
    # Check content for database-related keywords
    schema_keywords = ['schema', 'table', 'database', 'create', 'mysql', 'postgres']
    found_schema_content = False
    
    for schema_file in schema_files:
        try:
            with open(os.path.join(references_dir, schema_file), 'r') as f:
                content = f.read().lower()
                if any(keyword in content for keyword in schema_keywords):
                    found_schema_content = True
                    break
        except:
            continue
    
    if not found_schema_content:
        return False, "References directory exists but no database schema content found"
    
    return True, f"Database schema references included ({len(schema_files)} files)"

def check_configuration_templates(workspace_dir):
    """Check if configuration templates were created in assets"""
    skill_dirs = [d for d in os.listdir(workspace_dir) if 'database-migrator' in d.lower() and os.path.isdir(os.path.join(workspace_dir, d))]
    
    if not skill_dirs:
        return False, "No skill directory found for assets check"
    
    skill_dir = os.path.join(workspace_dir, skill_dirs[0])
    assets_dir = os.path.join(skill_dir, 'assets')
    
    if not os.path.exists(assets_dir):
        return False, "Assets directory not found"
    
    # Look for configuration files
    config_files = [f for f in os.listdir(assets_dir) if f.endswith(('.yaml', '.yml', '.json', '.conf', '.cfg'))]
    
    if not config_files:
        return False, "No configuration template files found in assets directory"
    
    # Check content for configuration-related keywords
    config_keywords = ['config', 'database', 'connection', 'host', 'port', 'migration']
    found_config_content = False
    
    for config_file in config_files:
        try:
            with open(os.path.join(assets_dir, config_file), 'r') as f:
                content = f.read().lower()
                if any(keyword in content for keyword in config_keywords):
                    found_config_content = True
                    break
        except:
            continue
    
    if not found_config_content:
        return False, "Assets directory exists but no configuration content found"
    
    return True, f"Configuration templates created in assets ({len(config_files)} files)"

def check_slack_integration(workspace_dir):
    """Check if Slack integration was attempted"""
    # Look for evidence of Slack integration attempts
    slack_indicators = []
    
    # Check for Python files that might contain Slack code
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            if file.endswith('.py'):
                try:
                    with open(os.path.join(root, file), 'r') as f:
                        content = f.read().lower()
                        if any(keyword in content for keyword in ['slack', 'rube', 'webhook', 'channel', 'dev-tools']):
                            slack_indicators.append(f"Slack integration found in {file}")
                except:
                    continue
    
    # Check for log files or output that mentions Slack
    log_files = [f for f in os.listdir(workspace_dir) if f.endswith(('.log', '.txt', '.out'))]
    for log_file in log_files:
        try:
            with open(os.path.join(workspace_dir, log_file), 'r') as f:
                content = f.read().lower()
                if any(keyword in content for keyword in ['slack', 'channel', 'dev-tools', 'posted', 'sent']):
                    slack_indicators.append(f"Slack activity found in {log_file}")
        except:
            continue
    
    if not slack_indicators:
        return False, "No evidence of Slack integration or sharing attempt found"
    
    return True, f"Slack integration detected: {'; '.join(slack_indicators[:3])}"

def check_skill_packaging(workspace_dir):
    """Check if skill was packaged properly"""
    # Look for zip files or packaging evidence
    zip_files = [f for f in os.listdir(workspace_dir) if f.endswith('.zip')]
    
    if zip_files:
        # Check if zip contains the skill
        for zip_file in zip_files:
            try:
                with zipfile.ZipFile(os.path.join(workspace_dir, zip_file), 'r') as zf:
                    files_in_zip = zf.namelist()
                    if any('skill.md' in f.lower() or 'database-migrator' in f.lower() for f in files_in_zip):
                        return True, f"Skill packaged in {zip_file} with {len(files_in_zip)} files"
            except:
                continue
    
    # Alternative: Check for evidence of packaging commands or output
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            if file.endswith(('.py', '.sh', '.log', '.txt')):
                try:
                    with open(os.path.join(root, file), 'r') as f:
                        content = f.read().lower()
                        if any(keyword in content for keyword in ['zip', 'package', 'distribute', 'bundle']):
                            return True, f"Packaging activity detected in {file}"
                except:
                    continue
    
    return False, "No evidence of skill packaging found"

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Invalid arguments"}]}))
        return
    
    workspace_dir = sys.argv[1]
    
    checks = []
    
    # Check 1: Skill directory structure
    passed, detail = check_skill_directory_structure(workspace_dir)
    checks.append({"name": "skill_directory_structure", "passed": passed, "detail": detail})
    
    # Check 2: SKILL.md file
    passed, detail = check_skill_md_file(workspace_dir)
    checks.append({"name": "skill_md_file", "passed": passed, "detail": detail})
    
    # Check 3: Migration scripts
    passed, detail = check_migration_scripts(workspace_dir)
    checks.append({"name": "migration_scripts", "passed": passed, "detail": detail})
    
    # Check 4: Reference files
    passed, detail = check_reference_files(workspace_dir)
    checks.append({"name": "reference_files", "passed": passed, "detail": detail})
    
    # Check 5: Configuration templates
    passed, detail = check_configuration_templates(workspace_dir)
    checks.append({"name": "configuration_templates", "passed": passed, "detail": detail})
    
    # Check 6: Slack integration
    passed, detail = check_slack_integration(workspace_dir)
    checks.append({"name": "slack_integration", "passed": passed, "detail": detail})
    
    # Check 7: Skill packaging
    passed, detail = check_skill_packaging(workspace_dir)
    checks.append({"name": "skill_packaging", "passed": passed, "detail": detail})
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_count / total_checks
    overall_passed = score >= 0.8  # Allow for some flexibility
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()