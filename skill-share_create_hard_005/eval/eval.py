import os
import sys
import json
import zipfile
import yaml
from pathlib import Path

def check_skill_directory_structure(workspace_path):
    """Check if skill directory was created with proper structure."""
    skill_dirs = [d for d in os.listdir(workspace_path) if d.startswith('skill-') or d.startswith('code-quality-analyzer')]
    
    if not skill_dirs:
        return False, "No skill directory found"
    
    # Use the first skill directory found
    skill_dir = os.path.join(workspace_path, skill_dirs[0])
    
    required_files = ['SKILL.md']
    required_dirs = ['scripts', 'references']
    
    for file in required_files:
        if not os.path.exists(os.path.join(skill_dir, file)):
            return False, f"Missing required file: {file}"
    
    for dir in required_dirs:
        if not os.path.exists(os.path.join(skill_dir, dir)):
            return False, f"Missing required directory: {dir}"
    
    return True, "Skill directory structure is correct"

def check_skill_metadata(workspace_path):
    """Check SKILL.md has proper metadata."""
    skill_dirs = [d for d in os.listdir(workspace_path) if d.startswith('skill-') or d.startswith('code-quality-analyzer')]
    
    if not skill_dirs:
        return False, "No skill directory found"
    
    skill_md_path = os.path.join(workspace_path, skill_dirs[0], 'SKILL.md')
    
    if not os.path.exists(skill_md_path):
        return False, "SKILL.md not found"
    
    with open(skill_md_path, 'r') as f:
        content = f.read().lower()
    
    required_fields = ['name:', 'description:', 'license:']
    for field in required_fields:
        if field not in content:
            return False, f"Missing required field: {field}"
    
    if 'code-quality-analyzer' not in content:
        return False, "Skill name not found in metadata"
    
    if 'python' not in content and 'quality' not in content:
        return False, "Description doesn't mention key functionality"
    
    return True, "SKILL.md metadata is complete"

def check_analysis_script(workspace_path):
    """Check if Python analysis script was created."""
    skill_dirs = [d for d in os.listdir(workspace_path) if d.startswith('skill-') or d.startswith('code-quality-analyzer')]
    
    if not skill_dirs:
        return False, "No skill directory found"
    
    scripts_dir = os.path.join(workspace_path, skill_dirs[0], 'scripts')
    
    if not os.path.exists(scripts_dir):
        return False, "Scripts directory not found"
    
    py_files = [f for f in os.listdir(scripts_dir) if f.endswith('.py')]
    
    if not py_files:
        return False, "No Python script found in scripts directory"
    
    # Check content of first Python file
    script_path = os.path.join(scripts_dir, py_files[0])
    with open(script_path, 'r') as f:
        content = f.read().lower()
    
    quality_keywords = ['complexity', 'pep', 'style', 'quality', 'analyze', 'json']
    found_keywords = sum(1 for keyword in quality_keywords if keyword in content)
    
    if found_keywords < 3:
        return False, "Script doesn't appear to contain quality analysis functionality"
    
    return True, "Analysis script created successfully"

def check_documentation(workspace_path):
    """Check if proper documentation was created."""
    skill_dirs = [d for d in os.listdir(workspace_path) if d.startswith('skill-') or d.startswith('code-quality-analyzer')]
    
    if not skill_dirs:
        return False, "No skill directory found"
    
    references_dir = os.path.join(workspace_path, skill_dirs[0], 'references')
    
    if not os.path.exists(references_dir):
        return False, "References directory not found"
    
    md_files = [f for f in os.listdir(references_dir) if f.endswith('.md')]
    
    if len(md_files) < 2:
        return False, "Insufficient documentation files (need at least 2)"
    
    # Check for README.md
    readme_found = any('readme' in f.lower() for f in md_files)
    if not readme_found:
        return False, "README.md not found in references"
    
    # Check for quality-metrics.md or similar
    metrics_found = any('quality' in f.lower() or 'metric' in f.lower() for f in md_files)
    if not metrics_found:
        return False, "Quality metrics documentation not found"
    
    return True, "Documentation files created successfully"

def check_packaged_skill(workspace_path):
    """Check if skill was packaged as a zip file."""
    zip_files = [f for f in os.listdir(workspace_path) if f.endswith('.zip')]
    
    if not zip_files:
        return False, "No zip package found"
    
    # Check for properly named zip file
    expected_patterns = ['code-quality-analyzer', 'v1.0']
    valid_zip = None
    
    for zip_file in zip_files:
        if all(pattern.lower() in zip_file.lower() for pattern in expected_patterns):
            valid_zip = zip_file
            break
    
    if not valid_zip:
        return False, "Zip file doesn't follow expected naming convention"
    
    # Check zip contents
    try:
        with zipfile.ZipFile(os.path.join(workspace_path, valid_zip), 'r') as zf:
            files = zf.namelist()
            if not any('SKILL.md' in f for f in files):
                return False, "Zip package missing SKILL.md"
            if not any('scripts/' in f for f in files):
                return False, "Zip package missing scripts directory"
    except Exception as e:
        return False, f"Error reading zip file: {str(e)}"
    
    return True, "Skill packaged successfully"

def check_slack_notification(workspace_path):
    """Check if Slack notification was attempted."""
    # Look for log files, output files, or any indication of Slack interaction
    all_files = []
    for root, dirs, files in os.walk(workspace_path):
        all_files.extend([os.path.join(root, f) for f in files])
    
    slack_indicators = []
    
    # Check for files that might contain Slack-related content
    for file_path in all_files:
        if file_path.endswith(('.txt', '.log', '.json', '.md')):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    if any(term in content for term in ['slack', '#dev-tools', 'notification', 'webhook']):
                        slack_indicators.append(file_path)
            except:
                continue
    
    # Also check if any Python files contain Slack-related code
    py_files = [f for f in all_files if f.endswith('.py')]
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                if any(term in content for term in ['slack', 'webhook', 'post_message', 'send_message']):
                    slack_indicators.append(py_file)
        except:
            continue
    
    if slack_indicators:
        return True, "Slack notification functionality detected"
    
    return False, "No evidence of Slack notification attempt found"

def evaluate_task(workspace_path):
    """Evaluate the complete task."""
    checks = []
    
    # Check 1: Skill directory structure
    passed, detail = check_skill_directory_structure(workspace_path)
    checks.append({"name": "skill_directory_structure", "passed": passed, "detail": detail})
    
    # Check 2: SKILL.md metadata
    passed, detail = check_skill_metadata(workspace_path)
    checks.append({"name": "skill_metadata", "passed": passed, "detail": detail})
    
    # Check 3: Analysis script
    passed, detail = check_analysis_script(workspace_path)
    checks.append({"name": "analysis_script", "passed": passed, "detail": detail})
    
    # Check 4: Documentation
    passed, detail = check_documentation(workspace_path)
    checks.append({"name": "documentation", "passed": passed, "detail": detail})
    
    # Check 5: Packaged skill
    passed, detail = check_packaged_skill(workspace_path)
    checks.append({"name": "packaged_skill", "passed": passed, "detail": detail})
    
    # Check 6: Slack notification
    passed, detail = check_slack_notification(workspace_path)
    checks.append({"name": "slack_notification", "passed": passed, "detail": detail})
    
    # Calculate score
    score = sum(1 for c in checks if c['passed']) / len(checks)
    
    result = {
        "passed": score >= 0.8,
        "score": score,
        "checks": checks
    }
    
    return result

if __name__ == "__main__":
    workspace_path = sys.argv[1]
    result = evaluate_task(workspace_path)
    print(json.dumps(result))