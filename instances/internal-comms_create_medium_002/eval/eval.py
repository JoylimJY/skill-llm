import sys
import os
import re
import json

def check_3p_format(content):
    """Check if content follows 3P update format"""
    checks = []
    
    # Check for emoji and team name in header
    emoji_header = bool(re.search(r'^[^\w\s]+.*Mobile.*Engineering.*\(.*Jan.*8.*12.*2024.*\)', content, re.MULTILINE | re.IGNORECASE))
    checks.append({
        "name": "emoji_and_header_format",
        "passed": emoji_header,
        "detail": "Header should have emoji, team name, and date range"
    })
    
    # Check for all three P sections
    has_progress = bool(re.search(r'Progress:', content, re.IGNORECASE))
    has_plans = bool(re.search(r'Plans:', content, re.IGNORECASE))
    has_problems = bool(re.search(r'Problems:', content, re.IGNORECASE))
    
    checks.append({
        "name": "progress_section",
        "passed": has_progress,
        "detail": "Must include Progress: section"
    })
    
    checks.append({
        "name": "plans_section", 
        "passed": has_plans,
        "detail": "Must include Plans: section"
    })
    
    checks.append({
        "name": "problems_section",
        "passed": has_problems,
        "detail": "Must include Problems: section"
    })
    
    # Check for key content mentions
    mentions_notifications = bool(re.search(r'push.*notification|notification.*system', content, re.IGNORECASE))
    mentions_bugs = bool(re.search(r'15.*bug|bug.*15|fixed.*bug', content, re.IGNORECASE))
    mentions_payment = bool(re.search(r'payment.*redesign|redesign.*payment', content, re.IGNORECASE))
    mentions_api_blocker = bool(re.search(r'backend.*API|API.*backend|platform.*team.*delay|delay.*platform', content, re.IGNORECASE))
    
    checks.append({
        "name": "key_progress_items",
        "passed": mentions_notifications and mentions_bugs,
        "detail": "Should mention push notifications and bug fixes in progress"
    })
    
    checks.append({
        "name": "key_plans_items",
        "passed": mentions_payment,
        "detail": "Should mention payment redesign in plans"
    })
    
    checks.append({
        "name": "key_problems_items",
        "passed": mentions_api_blocker,
        "detail": "Should mention API/platform team blocker in problems"
    })
    
    # Check length (should be concise)
    line_count = len([line for line in content.split('\n') if line.strip()])
    appropriate_length = 4 <= line_count <= 12  # Header + 3 sections, each 1-3 sentences
    
    checks.append({
        "name": "appropriate_length",
        "passed": appropriate_length,
        "detail": f"Should be concise (4-12 lines), found {line_count} lines"
    })
    
    return checks

def main(workspace_path):
    checks = []
    passed = False
    score = 0.0
    
    # Look for output file
    possible_files = ['3p_update.txt', '3p_update.md', 'update.txt', 'mobile_3p.txt', 'output.txt']
    output_file = None
    
    for filename in possible_files:
        filepath = os.path.join(workspace_path, filename)
        if os.path.exists(filepath):
            output_file = filepath
            break
    
    if not output_file:
        # Check if content was written to stdout or any .txt/.md file
        for file in os.listdir(workspace_path):
            if file.endswith(('.txt', '.md')) and file not in ['team_context.txt', 'recent_updates.txt']:
                output_file = os.path.join(workspace_path, file)
                break
    
    if not output_file:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "No 3P update output file found"
        })
    else:
        checks.append({
            "name": "output_file_exists", 
            "passed": True,
            "detail": f"Found output file: {os.path.basename(output_file)}"
        })
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        if len(content.strip()) < 50:
            checks.append({
                "name": "sufficient_content",
                "passed": False,
                "detail": "Output file appears to be empty or too short"
            })
        else:
            checks.append({
                "name": "sufficient_content",
                "passed": True, 
                "detail": "Output contains substantial content"
            })
            
            # Run 3P format checks
            format_checks = check_3p_format(content)
            checks.extend(format_checks)
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_count / total_checks if total_checks > 0 else 0.0
    passed = score >= 0.7
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_path>"}]}))
        sys.exit(1)
    
    main(sys.argv[1])