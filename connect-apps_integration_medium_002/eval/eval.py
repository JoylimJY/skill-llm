import sys
import os
import json
import re

def check_file_exists(workspace_dir, filename):
    filepath = os.path.join(workspace_dir, filename)
    return os.path.exists(filepath), filepath

def check_email_script(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read().lower()
        
        checks = []
        
        # Check for email subject
        subject_found = 'project status update' in content
        checks.append({
            "name": "email_subject_check",
            "passed": subject_found,
            "detail": "Found 'Project Status Update' subject" if subject_found else "Missing required email subject"
        })
        
        # Check for email body content
        body_content = 'deployment is complete' in content and 'tests are passing' in content
        checks.append({
            "name": "email_body_check",
            "passed": body_content,
            "detail": "Found required email body content" if body_content else "Missing deployment and testing message in body"
        })
        
        # Check for recipient
        recipient_found = 'test@example.com' in content
        checks.append({
            "name": "email_recipient_check",
            "passed": recipient_found,
            "detail": "Found correct recipient email" if recipient_found else "Missing test@example.com recipient"
        })
        
        # Check for error handling
        error_handling = any(keyword in content for keyword in ['try:', 'except:', 'error', 'exception'])
        checks.append({
            "name": "error_handling_check",
            "passed": error_handling,
            "detail": "Found error handling code" if error_handling else "Missing error handling implementation"
        })
        
        return checks
    except Exception as e:
        return [{
            "name": "email_script_read_error",
            "passed": False,
            "detail": f"Error reading email script: {str(e)}"
        }]

def check_config_file(filepath):
    try:
        with open(filepath, 'r') as f:
            config_data = json.load(f)
        
        checks = []
        
        # Check for required fields
        required_fields = ['api_key', 'base_url', 'enabled_apps']
        for field in required_fields:
            field_exists = field in config_data
            checks.append({
                "name": f"config_{field}_check",
                "passed": field_exists,
                "detail": f"Found {field} in config" if field_exists else f"Missing {field} field in config"
            })
        
        # Check if gmail is in enabled_apps
        gmail_enabled = False
        if 'enabled_apps' in config_data:
            enabled_apps = config_data.get('enabled_apps', [])
            if isinstance(enabled_apps, list):
                gmail_enabled = any('gmail' in str(app).lower() for app in enabled_apps)
        
        checks.append({
            "name": "gmail_enabled_check",
            "passed": gmail_enabled,
            "detail": "Gmail found in enabled apps" if gmail_enabled else "Gmail not found in enabled_apps"
        })
        
        return checks
    except json.JSONDecodeError:
        return [{
            "name": "config_json_parse_error",
            "passed": False,
            "detail": "Invalid JSON format in config file"
        }]
    except Exception as e:
        return [{
            "name": "config_file_read_error",
            "passed": False,
            "detail": f"Error reading config file: {str(e)}"
        }]

def main():
    workspace_dir = sys.argv[1]
    all_checks = []
    
    # Check if email automation script exists
    email_script_exists, email_script_path = check_file_exists(workspace_dir, 'email_automation.py')
    all_checks.append({
        "name": "email_script_exists",
        "passed": email_script_exists,
        "detail": "Found email_automation.py" if email_script_exists else "Missing email_automation.py file"
    })
    
    # Check email script content if it exists
    if email_script_exists:
        all_checks.extend(check_email_script(email_script_path))
    
    # Check if config file exists
    config_exists, config_path = check_file_exists(workspace_dir, 'composio_config.json')
    all_checks.append({
        "name": "config_file_exists",
        "passed": config_exists,
        "detail": "Found composio_config.json" if config_exists else "Missing composio_config.json file"
    })
    
    # Check config file content if it exists
    if config_exists:
        all_checks.extend(check_config_file(config_path))
    
    # Calculate score
    passed_checks = sum(1 for check in all_checks if check['passed'])
    total_checks = len(all_checks)
    score = passed_checks / total_checks
    
    result = {
        "passed": score == 1.0,
        "score": score,
        "checks": all_checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()