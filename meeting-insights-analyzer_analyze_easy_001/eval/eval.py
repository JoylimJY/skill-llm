import os
import sys
import json
import re

def evaluate_task(workspace_dir):
    checks = []
    
    # Check if conflict_analysis.md file exists
    report_file = None
    for filename in os.listdir(workspace_dir):
        if filename.lower() == 'conflict_analysis.md':
            report_file = os.path.join(workspace_dir, filename)
            break
    
    if not report_file:
        checks.append({"name": "Report file exists", "passed": False, "detail": "conflict_analysis.md file not found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "Report file exists", "passed": True, "detail": "conflict_analysis.md file found"})
    
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read().lower()
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": f"Could not read file: {e}"})
        return {"passed": False, "score": len([c for c in checks if c['passed']]) / len(checks), "checks": checks}
    
    checks.append({"name": "File readable", "passed": True, "detail": "File successfully read"})
    
    # Check for conflict avoidance patterns identification
    conflict_keywords = ['conflict', 'avoid', 'indirect', 'hedging', 'maybe', 'potentially', 'perhaps']
    has_conflict_analysis = any(keyword in content for keyword in conflict_keywords)
    checks.append({"name": "Identifies conflict avoidance patterns", "passed": has_conflict_analysis, "detail": "Found conflict avoidance analysis" if has_conflict_analysis else "No conflict avoidance analysis found"})
    
    # Check for specific examples with timestamps
    timestamp_pattern = r'\[?\d{2}:\d{2}[:\d{2}]?\]?|\d{2}:\d{2}'
    has_timestamps = bool(re.search(timestamp_pattern, content))
    checks.append({"name": "Includes specific examples with timestamps", "passed": has_timestamps, "detail": "Found timestamp references" if has_timestamps else "No timestamp examples found"})
    
    # Check for hedging language examples
    hedging_examples = ['maybe', 'potentially', 'i think', 'sort of', 'kind of', 'perhaps']
    has_hedging_analysis = any(hedge in content for hedge in hedging_examples)
    checks.append({"name": "Analyzes hedging language", "passed": has_hedging_analysis, "detail": "Found hedging language analysis" if has_hedging_analysis else "No hedging language analysis found"})
    
    # Check for recommendations
    recommendation_keywords = ['recommend', 'suggestion', 'improve', 'better', 'direct', 'clear', 'specific']
    has_recommendations = any(keyword in content for keyword in recommendation_keywords)
    checks.append({"name": "Provides recommendations", "passed": has_recommendations, "detail": "Found recommendations" if has_recommendations else "No recommendations found"})
    
    # Check for meeting-specific analysis (references to the actual meetings)
    meeting_refs = ['team meeting', 'sarah', 'client', '2024-01']
    has_meeting_refs = any(ref in content for ref in meeting_refs)
    checks.append({"name": "References actual meeting content", "passed": has_meeting_refs, "detail": "Found references to actual meetings" if has_meeting_refs else "No specific meeting references found"})
    
    # Check for structured format
    structure_indicators = ['#', '*', '-', '1.', '2.', 'example']
    has_structure = any(indicator in content for indicator in structure_indicators)
    checks.append({"name": "Uses structured format", "passed": has_structure, "detail": "Found structured formatting" if has_structure else "No clear structure found"})
    
    passed_count = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_count / total_checks
    overall_passed = score >= 0.8
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    workspace_dir = sys.argv[1]
    result = evaluate_task(workspace_dir)
    print(json.dumps(result))