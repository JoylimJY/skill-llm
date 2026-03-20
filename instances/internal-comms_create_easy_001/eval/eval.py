#!/usr/bin/env python3
import sys
import os
import re
import json

def check_3p_format(content):
    """Check if content follows 3P update format"""
    lines = content.strip().split('\n')
    if len(lines) < 4:
        return False, "Too few lines for complete 3P format"
    
    # Check for header with emoji and team name
    header_pattern = r'^[^\w]*Mobile Development.*\([^)]+\)'
    if not re.search(header_pattern, lines[0]):
        return False, "Header missing emoji, team name, or date range"
    
    # Check for Progress, Plans, Problems sections
    content_lower = content.lower()
    if 'progress:' not in content_lower:
        return False, "Missing Progress section"
    if 'plans:' not in content_lower:
        return False, "Missing Plans section"
    if 'problems:' not in content_lower:
        return False, "Missing Problems section"
    
    return True, "Proper 3P format detected"

def check_content_accuracy(content):
    """Check if content includes key information from prompt"""
    content_lower = content.lower()
    required_items = [
        ('onboarding', 'user onboarding flow'),
        ('bugs', 'bug fixes'),
        ('notification', 'notification system'),
        ('api', 'backend API blocker')
    ]
    
    missing = []
    for key, desc in required_items:
        if key not in content_lower:
            missing.append(desc)
    
    if missing:
        return False, f"Missing key content: {', '.join(missing)}"
    return True, "All key content included"

def check_conciseness(content):
    """Check if update is appropriately concise"""
    lines = [line for line in content.split('\n') if line.strip()]
    if len(lines) > 6:
        return False, "Update too verbose, should be 4 lines (header + 3 sections)"
    return True, "Appropriately concise"

def evaluate_workspace(workspace_path):
    checks = []
    
    # Look for output files
    possible_files = ['3p_update.txt', 'mobile_3p.txt', 'update.txt', '3p.txt']
    output_file = None
    
    for filename in possible_files:
        filepath = os.path.join(workspace_path, filename)
        if os.path.exists(filepath):
            output_file = filepath
            break
    
    # Also check for any .txt files that might contain the update
    if not output_file:
        for file in os.listdir(workspace_path):
            if file.endswith('.txt') and file not in ['team_context.txt', 'previous_3p_example.txt']:
                filepath = os.path.join(workspace_path, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    if 'mobile development' in content.lower() and ('progress:' in content.lower() or 'plans:' in content.lower()):
                        output_file = filepath
                        break
    
    if not output_file:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "No 3P update output file found"}]
        }
    
    # Read the output file
    with open(output_file, 'r') as f:
        content = f.read()
    
    # File exists check
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found output file: {os.path.basename(output_file)}"})
    
    # Format check
    format_passed, format_detail = check_3p_format(content)
    checks.append({"name": "proper_3p_format", "passed": format_passed, "detail": format_detail})
    
    # Content accuracy check
    content_passed, content_detail = check_content_accuracy(content)
    checks.append({"name": "content_accuracy", "passed": content_passed, "detail": content_detail})
    
    # Conciseness check
    concise_passed, concise_detail = check_conciseness(content)
    checks.append({"name": "appropriate_length", "passed": concise_passed, "detail": concise_detail})
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check["passed"])
    score = passed_checks / len(checks)
    passed = score >= 0.75
    
    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_path = sys.argv[1] if len(sys.argv) > 1 else "."
    result = evaluate_workspace(workspace_path)
    print(json.dumps(result))