import os
import sys
import json
import re
from pathlib import Path

def check_workflow_summary(workspace_dir):
    """Check if workflow summary JSON file exists and contains required data"""
    summary_files = list(Path(workspace_dir).glob('**/workflow_summary.json'))
    if not summary_files:
        summary_files = [f for f in Path(workspace_dir).rglob('*.json') if 'workflow' in f.name.lower() or 'summary' in f.name.lower()]
    
    if not summary_files:
        return False, 'No workflow summary JSON file found'
    
    for summary_file in summary_files:
        try:
            with open(summary_file, 'r') as f:
                data = json.load(f)
            
            required_keys = ['email_sent', 'github_issue_created', 'slack_posted']
            id_keys = ['email_id', 'issue_id', 'message_id']
            
            has_status_keys = all(key in data for key in required_keys)
            has_id_keys = any(key in data for key in id_keys)
            
            if has_status_keys and has_id_keys:
                return True, f'Valid workflow summary found in {summary_file.name}'
        except (json.JSONDecodeError, Exception):
            continue
    
    return False, 'No valid workflow summary JSON structure found'

def check_email_setup(workspace_dir):
    """Check if email sending is mentioned with correct details"""
    all_files = list(Path(workspace_dir).rglob('*'))
    text_content = ''
    
    for file_path in all_files:
        if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.json', '.log', '.py']:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content += f.read().lower()
            except:
                continue
    
    has_welcome_email = 'welcome to the team' in text_content or 'newuser@company.com' in text_content
    has_welcome_marker = 'welcome_marker_2024' in text_content
    
    if has_welcome_email and has_welcome_marker:
        return True, 'Email setup with correct recipient and marker found'
    elif has_welcome_email:
        return True, 'Email setup with correct recipient found (marker tolerance)'
    else:
        return False, 'Email setup details not found'

def check_github_integration(workspace_dir):
    """Check if GitHub issue creation is mentioned"""
    all_files = list(Path(workspace_dir).rglob('*'))
    text_content = ''
    
    for file_path in all_files:
        if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.json', '.log', '.py']:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content += f.read().lower()
            except:
                continue
    
    has_github_issue = 'setup new employee access' in text_content or 'github issue' in text_content
    has_github_marker = 'github_issue_marker_2024' in text_content
    
    if has_github_issue and has_github_marker:
        return True, 'GitHub issue creation with correct title and marker found'
    elif has_github_issue:
        return True, 'GitHub issue creation found (marker tolerance)'
    else:
        return False, 'GitHub issue creation not found'

def check_slack_integration(workspace_dir):
    """Check if Slack message posting is mentioned"""
    all_files = list(Path(workspace_dir).rglob('*'))
    text_content = ''
    
    for file_path in all_files:
        if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.json', '.log', '.py']:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content += f.read().lower()
            except:
                continue
    
    has_slack_post = 'new team member onboarded' in text_content or ('#general' in text_content and 'slack' in text_content)
    has_slack_marker = 'slack_notification_marker_2024' in text_content
    
    if has_slack_post and has_slack_marker:
        return True, 'Slack message posting with correct content and marker found'
    elif has_slack_post:
        return True, 'Slack message posting found (marker tolerance)'
    else:
        return False, 'Slack message posting not found'

def check_plugin_installation(workspace_dir):
    """Check if composio plugin installation is mentioned"""
    all_files = list(Path(workspace_dir).rglob('*'))
    text_content = ''
    
    for file_path in all_files:
        if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.json', '.log', '.py']:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content += f.read().lower()
            except:
                continue
    
    has_plugin_install = 'composio-toolrouter' in text_content or 'plugin install' in text_content
    has_setup_command = 'setup' in text_content and 'composio' in text_content
    
    if has_plugin_install and has_setup_command:
        return True, 'Plugin installation and setup commands found'
    elif has_plugin_install:
        return True, 'Plugin installation mentioned'
    else:
        return False, 'Plugin installation steps not found'

def check_workflow_orchestration(workspace_dir):
    """Check if all three integrations are coordinated in a workflow"""
    all_files = list(Path(workspace_dir).rglob('*'))
    text_content = ''
    
    for file_path in all_files:
        if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.json', '.log', '.py']:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content += f.read().lower()
            except:
                continue
    
    has_email_ref = 'email' in text_content or 'gmail' in text_content
    has_github_ref = 'github' in text_content or 'issue' in text_content
    has_slack_ref = 'slack' in text_content
    
    integration_count = sum([has_email_ref, has_github_ref, has_slack_ref])
    
    if integration_count >= 3:
        return True, 'All three integrations (email, github, slack) referenced'
    elif integration_count >= 2:
        return True, 'Multiple integrations found'
    else:
        return False, 'Insufficient integration coverage'

def main():
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'args', 'passed': False, 'detail': 'Invalid arguments'}]}))
        return
    
    workspace_dir = sys.argv[1]
    
    checks = []
    
    # Check 1: Plugin installation
    plugin_passed, plugin_detail = check_plugin_installation(workspace_dir)
    checks.append({
        'name': 'plugin_installation',
        'passed': plugin_passed,
        'detail': plugin_detail
    })
    
    # Check 2: Email integration
    email_passed, email_detail = check_email_setup(workspace_dir)
    checks.append({
        'name': 'email_integration',
        'passed': email_passed,
        'detail': email_detail
    })
    
    # Check 3: GitHub integration
    github_passed, github_detail = check_github_integration(workspace_dir)
    checks.append({
        'name': 'github_integration',
        'passed': github_passed,
        'detail': github_detail
    })
    
    # Check 4: Slack integration
    slack_passed, slack_detail = check_slack_integration(workspace_dir)
    checks.append({
        'name': 'slack_integration',
        'passed': slack_passed,
        'detail': slack_detail
    })
    
    # Check 5: Workflow orchestration
    workflow_passed, workflow_detail = check_workflow_orchestration(workspace_dir)
    checks.append({
        'name': 'workflow_orchestration',
        'passed': workflow_passed,
        'detail': workflow_detail
    })
    
    # Check 6: Summary output
    summary_passed, summary_detail = check_workflow_summary(workspace_dir)
    checks.append({
        'name': 'workflow_summary',
        'passed': summary_passed,
        'detail': summary_detail
    })
    
    passed_count = sum(1 for check in checks if check['passed'])
    score = passed_count / len(checks)
    overall_passed = score >= 0.8
    
    result = {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()