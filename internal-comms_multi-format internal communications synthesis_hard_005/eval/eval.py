#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    output_file = Path(workspace_dir) / 'platform-infrastructure-3p.md'
    
    # Check 1: File exists
    file_exists = output_file.exists()
    checks.append({
        "name": "Output file exists",
        "passed": file_exists,
        "detail": f"File 'platform-infrastructure-3p.md' {'found' if file_exists else 'not found'}"
    })
    
    if not file_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    
    # Read the file
    with open(output_file, 'r') as f:
        content = f.read()
    
    content_lower = content.lower()
    
    # Check 2: Contains emoji at start
    has_emoji = len(content) > 0 and ord(content[0]) > 127
    checks.append({
        "name": "Starts with emoji",
        "passed": has_emoji,
        "detail": "First character is an emoji" if has_emoji else "No emoji found at start"
    })
    
    # Check 3: Contains team name
    has_team_name = 'platform infrastructure' in content_lower
    checks.append({
        "name": "Contains team name",
        "passed": has_team_name,
        "detail": "'Platform Infrastructure' found" if has_team_name else "Team name not found"
    })
    
    # Check 4: Contains date range
    has_date_range = 'january 15-19' in content_lower or 'january 15' in content_lower
    checks.append({
        "name": "Contains date range",
        "passed": has_date_range,
        "detail": "Date range found" if has_date_range else "Date range not found"
    })
    
    # Check 5: Has Progress section
    has_progress = 'progress:' in content_lower
    checks.append({
        "name": "Has Progress section",
        "passed": has_progress,
        "detail": "Progress section found" if has_progress else "Progress section missing"
    })
    
    # Check 6: Has Plans section
    has_plans = 'plans:' in content_lower
    checks.append({
        "name": "Has Plans section",
        "passed": has_plans,
        "detail": "Plans section found" if has_plans else "Plans section missing"
    })
    
    # Check 7: Has Problems section
    has_problems = 'problems:' in content_lower
    checks.append({
        "name": "Has Problems section",
        "passed": has_problems,
        "detail": "Problems section found" if has_problems else "Problems section missing"
    })
    
    # Check 8: Contains key progress metrics
    has_progress_content = any(keyword in content_lower for keyword in ['23%', 'latency', '2-hour', 'bugs', 'onboarded'])
    checks.append({
        "name": "Progress section has substantive content",
        "passed": has_progress_content,
        "detail": "Key progress metrics found" if has_progress_content else "Progress content appears incomplete"
    })
    
    # Check 9: Contains key plans
    has_plans_content = any(keyword in content_lower for keyword in ['caching', 'architecture', 'documentation', 'message queue'])
    checks.append({
        "name": "Plans section has substantive content",
        "passed": has_plans_content,
        "detail": "Key plans found" if has_plans_content else "Plans content appears incomplete"
    })
    
    # Check 10: Contains key problems
    has_problems_content = any(keyword in content_lower for keyword in ['medical leave', 'dependency', 'staging', 'unstable'])
    checks.append({
        "name": "Problems section has substantive content",
        "passed": has_problems_content,
        "detail": "Key problems found" if has_problems_content else "Problems content appears incomplete"
    })
    
    # Check 11: Reasonable length (not too verbose)
    lines = content.strip().split('\n')
    is_concise = len(lines) <= 10
    checks.append({
        "name": "Concise format (30-60 second read)",
        "passed": is_concise,
        "detail": f"Content is {len(lines)} lines (target: <=10)" if is_concise else f"Content is {len(lines)} lines (too verbose)"
    })
    
    # Check 12: Proper section structure
    has_proper_structure = content_lower.count('progress:') == 1 and content_lower.count('plans:') == 1 and content_lower.count('problems:') == 1
    checks.append({
        "name": "Proper section structure",
        "passed": has_proper_structure,
        "detail": "All three sections present exactly once" if has_proper_structure else "Section structure incorrect"
    })
    
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks)
    
    return {
        "passed": score >= 0.9,
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '/workspace'
    result = evaluate(workspace)
    print(json.dumps(result))
