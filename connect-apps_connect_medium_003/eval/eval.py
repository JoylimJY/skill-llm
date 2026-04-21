import os
import sys
import json
import re

def check_setup_report(workspace_dir):
    """Check if setup report was created and contains required information"""
    report_files = [f for f in os.listdir(workspace_dir) if f.lower().endswith('.md') and 'report' in f.lower()]
    
    if not report_files:
        return False, "No report file found"
    
    # Check all potential report files
    for report_file in report_files:
        try:
            with open(os.path.join(workspace_dir, report_file), 'r', encoding='utf-8') as f:
                content = f.read().lower()
                
            # Check for key elements with flexible matching
            has_install_step = any(keyword in content for keyword in ['install', 'plugin', 'composio-toolrouter'])
            has_setup_step = any(keyword in content for keyword in ['setup', 'configure', 'config'])
            has_email_step = any(keyword in content for keyword in ['email', 'test@example.com', 'send'])
            
            if has_install_step and has_setup_step and has_email_step:
                return True, f"Valid report found in {report_file}"
        except Exception as e:
            continue
    
    return False, "Report file exists but missing required steps"

def check_plugin_installation(workspace_dir):
    """Check if plugin installation was documented or simulated"""
    # Look for any files that might indicate plugin installation
    files = os.listdir(workspace_dir)
    
    # Check for command outputs or documentation
    for filename in files:
        if filename.lower().endswith(('.md', '.txt', '.log')):
            try:
                with open(os.path.join(workspace_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if 'composio-toolrouter' in content and any(word in content for word in ['install', 'installed', 'add']):
                        return True, "Plugin installation documented"
            except:
                continue
    
    return False, "No evidence of plugin installation"

def check_setup_configuration(workspace_dir):
    """Check if setup/configuration was documented"""
    files = os.listdir(workspace_dir)
    
    for filename in files:
        if filename.lower().endswith(('.md', '.txt', '.log', '.json')):
            try:
                with open(os.path.join(workspace_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if any(keyword in content for keyword in ['setup', 'configure', 'api key', 'platform.composio']):
                        return True, "Setup configuration documented"
            except:
                continue
    
    return False, "No evidence of setup configuration"

def check_email_sending(workspace_dir):
    """Check if email sending was attempted and documented"""
    files = os.listdir(workspace_dir)
    
    for filename in files:
        if filename.lower().endswith(('.md', '.txt', '.log')):
            try:
                with open(os.path.join(workspace_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    
                has_email_address = 'test@example.com' in content
                has_subject = 'plugin test' in content
                has_send_action = any(word in content for word in ['send', 'sent', 'email'])
                
                if has_email_address and has_subject and has_send_action:
                    return True, "Email sending documented with correct details"
            except:
                continue
    
    return False, "Email sending not properly documented"

def check_step_documentation(workspace_dir):
    """Check if steps were properly documented"""
    files = os.listdir(workspace_dir)
    
    for filename in files:
        if filename.lower().endswith(('.md', '.txt')):
            try:
                with open(os.path.join(workspace_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    
                # Look for structured documentation
                has_steps = any(marker in content for marker in ['1.', '2.', '3.', 'step', 'first', 'second', 'third'])
                has_success_status = any(word in content for word in ['success', 'successful', 'complete', 'done', 'working'])
                
                if has_steps and has_success_status:
                    return True, "Steps documented with status information"
            except:
                continue
    
    return False, "Steps not properly documented"

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Missing workspace directory argument"}]}))
        return
    
    workspace_dir = sys.argv[1]
    
    checks = []
    
    # Check 1: Setup report exists
    report_passed, report_detail = check_setup_report(workspace_dir)
    checks.append({"name": "setup_report_created", "passed": report_passed, "detail": report_detail})
    
    # Check 2: Plugin installation documented
    install_passed, install_detail = check_plugin_installation(workspace_dir)
    checks.append({"name": "plugin_installation", "passed": install_passed, "detail": install_detail})
    
    # Check 3: Setup configuration documented
    config_passed, config_detail = check_setup_configuration(workspace_dir)
    checks.append({"name": "setup_configuration", "passed": config_passed, "detail": config_detail})
    
    # Check 4: Email sending documented
    email_passed, email_detail = check_email_sending(workspace_dir)
    checks.append({"name": "email_sending", "passed": email_passed, "detail": email_detail})
    
    # Check 5: Step documentation quality
    steps_passed, steps_detail = check_step_documentation(workspace_dir)
    checks.append({"name": "step_documentation", "passed": steps_passed, "detail": steps_detail})
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_count / total_checks
    
    overall_passed = score >= 0.8
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()