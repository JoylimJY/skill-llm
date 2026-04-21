import os
import sys
import json
import re
from pathlib import Path

def evaluate_task(workspace_dir):
    checks = []
    
    # Check 1: Report file exists
    report_path = os.path.join(workspace_dir, 'meeting_insights.md')
    if os.path.exists(report_path):
        checks.append({"name": "Report file created", "passed": True, "detail": "meeting_insights.md found"})
    else:
        checks.append({"name": "Report file created", "passed": False, "detail": "meeting_insights.md not found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Read the report content
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read().lower()
    
    # Check 2: Filler word analysis present
    filler_keywords = ['filler word', 'um', 'uh', 'like', 'you know', 'actually']
    filler_found = any(keyword in content for keyword in filler_keywords)
    checks.append({"name": "Filler word analysis included", "passed": filler_found, "detail": "Found filler word analysis" if filler_found else "No filler word analysis detected"})
    
    # Check 3: Speaking time/ratio analysis
    speaking_keywords = ['speaking', 'ratio', 'time', 'percentage', 'talking']
    speaking_found = any(keyword in content for keyword in speaking_keywords)
    checks.append({"name": "Speaking time analysis included", "passed": speaking_found, "detail": "Found speaking time analysis" if speaking_found else "No speaking time analysis detected"})
    
    # Check 4: Conflict avoidance analysis
    conflict_keywords = ['conflict', 'avoid', 'hedging', 'indirect', 'maybe', 'perhaps', 'kind of']
    conflict_found = any(keyword in content for keyword in conflict_keywords)
    checks.append({"name": "Conflict avoidance analysis included", "passed": conflict_found, "detail": "Found conflict avoidance analysis" if conflict_found else "No conflict avoidance analysis detected"})
    
    # Check 5: Specific examples with timestamps
    timestamp_pattern = r'\[?\d{2}:\d{2}:\d{2}\]?|\d{2}:\d{2}'
    timestamps_found = bool(re.search(timestamp_pattern, content))
    checks.append({"name": "Examples with timestamps provided", "passed": timestamps_found, "detail": "Found timestamped examples" if timestamps_found else "No timestamped examples found"})
    
    # Check 6: Actionable recommendations
    recommendation_keywords = ['recommend', 'suggest', 'improve', 'better', 'next steps', 'action']
    recommendations_found = any(keyword in content for keyword in recommendation_keywords)
    checks.append({"name": "Actionable recommendations included", "passed": recommendations_found, "detail": "Found actionable recommendations" if recommendations_found else "No actionable recommendations detected"})
    
    # Check 7: Multiple meetings analyzed
    meeting_indicators = ['team meeting', 'client call', 'one-on-one', '2024-01', '2024-02', 'sarah', 'jessica']
    multiple_meetings = sum(1 for indicator in meeting_indicators if indicator in content) >= 3
    checks.append({"name": "Multiple meetings analyzed", "passed": multiple_meetings, "detail": "Evidence of analyzing multiple meetings" if multiple_meetings else "Appears to analyze only one meeting or missing meeting references"})
    
    # Calculate score
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.8
    
    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python eval_script.py <workspace_directory>")
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = evaluate_task(workspace_dir)
    print(json.dumps(result))