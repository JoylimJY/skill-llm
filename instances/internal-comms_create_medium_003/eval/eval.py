#!/usr/bin/env python3
import sys
import os
import json
import re

def check_3p_update(workspace_dir):
    checks = []
    score = 0.0
    
    # Look for any text files that might contain the 3P update
    output_files = []
    for file in os.listdir(workspace_dir):
        if file.endswith('.txt') or file.endswith('.md'):
            output_files.append(file)
    
    # Also check if output was written to stdout (check for any text files or assume console output)
    if not output_files:
        # Look for common output file names
        possible_names = ['3p_update.txt', 'update.txt', 'mobile_3p.txt', 'output.txt']
        for name in possible_names:
            if os.path.exists(os.path.join(workspace_dir, name)):
                output_files.append(name)
    
    content = ""
    if output_files:
        # Read the first output file found
        with open(os.path.join(workspace_dir, output_files[0]), 'r') as f:
            content = f.read()
    else:
        # Check if there's a response file or assume content was provided in stdout
        if os.path.exists(os.path.join(workspace_dir, 'response.txt')):
            with open(os.path.join(workspace_dir, 'response.txt'), 'r') as f:
                content = f.read()
    
    # For this eval, we'll assume the 3P update content might be in any generated text
    # Let's look for key patterns in any .txt or .md files
    all_content = ""
    for root, dirs, files in os.walk(workspace_dir):
        for file in files:
            if file.endswith(('.txt', '.md')):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        all_content += file_content + "\n"
                except:
                    continue
    
    if all_content:
        content = all_content
    
    # Check 1: Has emoji and team name format
    emoji_team_pattern = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]\s+\w+.*\(.*\)'
    has_format = bool(re.search(emoji_team_pattern, content, re.UNICODE))
    if has_format:
        score += 25
        checks.append({"name": "emoji_team_format", "passed": True, "detail": "Found emoji + team name + date format"})
    else:
        checks.append({"name": "emoji_team_format", "passed": False, "detail": "Missing emoji + team name + date format"})
    
    # Check 2: Has Progress section with key details
    progress_found = 'Progress:' in content or 'progress:' in content
    has_push_notif = 'push notification' in content.lower() or 'notification' in content.lower()
    has_engagement_metric = '12%' in content or 'engagement' in content.lower()
    has_bugs = 'bug' in content.lower() and ('8' in content or 'eight' in content.lower())
    has_crash_rate = 'crash' in content.lower() and ('0.8' in content or '2.1' in content)
    
    progress_score = sum([progress_found, has_push_notif, has_engagement_metric, has_bugs, has_crash_rate])
    if progress_score >= 3:
        score += 25
        checks.append({"name": "progress_content", "passed": True, "detail": f"Found {progress_score}/5 progress elements"})
    else:
        checks.append({"name": "progress_content", "passed": False, "detail": f"Only found {progress_score}/5 progress elements"})
    
    # Check 3: Has Plans section with key details  
    plans_found = 'Plans:' in content or 'plans:' in content
    has_redesign = 'redesign' in content.lower() or 'profile' in content.lower()
    has_analytics = 'analytics' in content.lower() or 'sdk' in content.lower()
    
    plans_score = sum([plans_found, has_redesign, has_analytics])
    if plans_score >= 2:
        score += 25
        checks.append({"name": "plans_content", "passed": True, "detail": f"Found {plans_score}/3 plans elements"})
    else:
        checks.append({"name": "plans_content", "passed": False, "detail": f"Only found {plans_score}/3 plans elements"})
    
    # Check 4: Has Problems section with blocking issue
    problems_found = 'Problems:' in content or 'problems:' in content
    has_backend_blocking = 'backend' in content.lower() and ('delay' in content.lower() or 'block' in content.lower() or 'waiting' in content.lower())
    has_api_mention = 'api' in content.lower() or 'preferences' in content.lower()
    
    problems_score = sum([problems_found, has_backend_blocking, has_api_mention])
    if problems_score >= 2:
        score += 25
        checks.append({"name": "problems_content", "passed": True, "detail": f"Found {problems_score}/3 problems elements"})
    else:
        checks.append({"name": "problems_content", "passed": False, "detail": f"Only found {problems_score}/3 problems elements"})
    
    return {
        "passed": score >= 75,
        "score": score / 100.0,
        "checks": checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Invalid arguments"}]}))
        sys.exit(1)
    
    result = check_3p_update(sys.argv[1])
    print(json.dumps(result))