import os
import sys
import json
import re
from pathlib import Path

def eval_task(workspace_dir):
    checks = []
    workspace_path = Path(workspace_dir)
    
    # Check 1: Look for integration report file
    report_files = list(workspace_path.glob('*integration*report*.md')) + list(workspace_path.glob('*report*.md'))
    report_found = len(report_files) > 0
    
    if report_found:
        checks.append({
            'name': 'Integration report file created',
            'passed': True,
            'detail': f'Found report file: {report_files[0].name}'
        })
        
        # Read the best report file (longest content)
        report_content = ''
        for report_file in report_files:
            try:
                content = report_file.read_text(encoding='utf-8').lower()
                if len(content) > len(report_content):
                    report_content = content
            except:
                continue
    else:
        checks.append({
            'name': 'Integration report file created',
            'passed': False,
            'detail': 'No integration report file found'
        })
        report_content = ''
    
    # Check 2: Report mentions plugin installation
    plugin_keywords = ['composio-toolrouter', 'plugin install', 'setup']
    plugin_mentioned = any(keyword in report_content for keyword in plugin_keywords)
    checks.append({
        'name': 'Report documents plugin installation',
        'passed': plugin_mentioned,
        'detail': 'Plugin installation process documented' if plugin_mentioned else 'Plugin installation not documented'
    })
    
    # Check 3: Report mentions email sending
    email_keywords = ['email', 'dev-notifications@example.com', 'setup test']
    email_mentioned = any(keyword in report_content for keyword in email_keywords)
    checks.append({
        'name': 'Report documents email sending',
        'passed': email_mentioned,
        'detail': 'Email sending process documented' if email_mentioned else 'Email sending not documented'
    })
    
    # Check 4: Report mentions GitHub issue creation
    github_keywords = ['github', 'issue', 'myorg/test-repo', 'automated notification']
    github_mentioned = any(keyword in report_content for keyword in github_keywords)
    checks.append({
        'name': 'Report documents GitHub issue creation',
        'passed': github_mentioned,
        'detail': 'GitHub issue creation documented' if github_mentioned else 'GitHub issue creation not documented'
    })
    
    # Check 5: Report mentions Slack posting
    slack_keywords = ['slack', '#dev-updates', 'integration is now live']
    slack_mentioned = any(keyword in report_content for keyword in slack_keywords)
    checks.append({
        'name': 'Report documents Slack posting',
        'passed': slack_mentioned,
        'detail': 'Slack posting process documented' if slack_mentioned else 'Slack posting not documented'
    })
    
    # Check 6: Report includes authorization steps
    auth_keywords = ['authorization', 'oauth', 'authenticate', 'permissions']
    auth_mentioned = any(keyword in report_content for keyword in auth_keywords)
    checks.append({
        'name': 'Report mentions authorization steps',
        'passed': auth_mentioned,
        'detail': 'Authorization process documented' if auth_mentioned else 'Authorization steps not documented'
    })
    
    # Check 7: Report includes success confirmations
    success_keywords = ['success', 'completed', 'working', 'confirmed']
    success_mentioned = any(keyword in report_content for keyword in success_keywords)
    checks.append({
        'name': 'Report includes success confirmations',
        'passed': success_mentioned,
        'detail': 'Success confirmations documented' if success_mentioned else 'Success confirmations not documented'
    })
    
    # Check 8: Report includes next steps
    next_steps_keywords = ['next steps', 'future', 'recommendations', 'usage']
    next_steps_mentioned = any(keyword in report_content for keyword in next_steps_keywords)
    checks.append({
        'name': 'Report includes next steps',
        'passed': next_steps_mentioned,
        'detail': 'Next steps documented' if next_steps_mentioned else 'Next steps not documented'
    })
    
    # Check 9: Report has reasonable structure (headings, sections)
    structure_indicators = ['#', '##', '###', '1.', '2.', '3.', '*', '-']
    has_structure = any(indicator in report_content for indicator in structure_indicators)
    checks.append({
        'name': 'Report has proper structure',
        'passed': has_structure,
        'detail': 'Report shows structured formatting' if has_structure else 'Report lacks clear structure'
    })
    
    # Check 10: Report mentions specific service details
    service_details = ['dev-notifications@example.com', 'setup test', 'myorg/test-repo', '#dev-updates']
    details_count = sum(1 for detail in service_details if detail in report_content)
    details_sufficient = details_count >= 2
    checks.append({
        'name': 'Report includes specific service details',
        'passed': details_sufficient,
        'detail': f'Found {details_count}/4 specific service details' 
    })
    
    # Calculate final score
    passed_checks = sum(1 for check in checks if check['passed'])
    score = passed_checks / len(checks)
    overall_passed = score >= 0.7
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python eval_script.py <workspace_dir>')
        sys.exit(1)
    
    result = eval_task(sys.argv[1])
    print(json.dumps(result))