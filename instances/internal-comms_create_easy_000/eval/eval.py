import sys
import os
import re
import json

def check_3p_update(workspace_dir):
    checks = []
    score = 0.0
    
    # Look for generated 3P update file
    possible_files = ['3p_update.txt', '3p_update.md', 'mobile_3p.txt', 'update.txt', 'mobile_team_update.txt']
    update_file = None
    
    for filename in os.listdir(workspace_dir):
        if any(keyword in filename.lower() for keyword in ['3p', 'update', 'mobile']):
            update_file = os.path.join(workspace_dir, filename)
            break
    
    if not update_file:
        # Check if content was written to stdout or any text file
        for filename in os.listdir(workspace_dir):
            if filename.endswith('.txt') or filename.endswith('.md'):
                potential_file = os.path.join(workspace_dir, filename)
                with open(potential_file, 'r') as f:
                    content = f.read()
                    if 'progress' in content.lower() and 'plans' in content.lower():
                        update_file = potential_file
                        break
    
    if not update_file:
        checks.append({"name": "file_exists", "passed": False, "detail": "No 3P update file found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found update file: {os.path.basename(update_file)}"})
    score += 0.2
    
    with open(update_file, 'r') as f:
        content = f.read()
    
    # Check for proper 3P structure
    has_progress = bool(re.search(r'progress:', content, re.IGNORECASE))
    has_plans = bool(re.search(r'plans:', content, re.IGNORECASE))
    has_problems = bool(re.search(r'problems:', content, re.IGNORECASE))
    
    if has_progress and has_plans and has_problems:
        checks.append({"name": "3p_structure", "passed": True, "detail": "Contains Progress, Plans, and Problems sections"})
        score += 0.3
    else:
        checks.append({"name": "3p_structure", "passed": False, "detail": f"Missing sections - Progress: {has_progress}, Plans: {has_plans}, Problems: {has_problems}"})
    
    # Check for team name and emoji
    has_team_name = 'mobile' in content.lower()
    has_emoji = bool(re.search(r'[📱🚀💻🔧⚡]', content))
    
    if has_team_name:
        checks.append({"name": "team_identification", "passed": True, "detail": "Contains team name (mobile)"})
        score += 0.15
    else:
        checks.append({"name": "team_identification", "passed": False, "detail": "Missing team name"})
    
    if has_emoji:
        checks.append({"name": "emoji_formatting", "passed": True, "detail": "Includes emoji in header"})
        score += 0.1
    else:
        checks.append({"name": "emoji_formatting", "passed": False, "detail": "Missing emoji in header"})
    
    # Check for specific content mentioned in prompt
    content_checks = {
        'push_notification': 'push notification' in content.lower(),
        'bugs_fixed': any(word in content.lower() for word in ['bug', '12', 'twelve']),
        'dark_mode': 'dark mode' in content.lower(),
        'api_blocker': any(word in content.lower() for word in ['api', 'backend', 'platform']),
        'developer_shortage': any(phrase in content.lower() for phrase in ['sarah', 'maternity', 'short', 'ios developer'])
    }
    
    content_score = sum(content_checks.values()) / len(content_checks)
    if content_score >= 0.6:
        checks.append({"name": "content_accuracy", "passed": True, "detail": f"Contains {sum(content_checks.values())}/{len(content_checks)} key details from prompt"})
        score += 0.25
    else:
        checks.append({"name": "content_accuracy", "passed": False, "detail": f"Missing key details: {[k for k, v in content_checks.items() if not v]}"})
    
    passed = score >= 0.6
    return {"passed": passed, "score": min(score, 1.0), "checks": checks}

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: python eval_script.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = check_3p_update(sys.argv[1])
    print(json.dumps(result))