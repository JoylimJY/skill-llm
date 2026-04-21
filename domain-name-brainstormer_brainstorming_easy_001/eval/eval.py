import os
import sys
import re
import json

def main(workspace_path):
    checks = []
    
    # Check if domain_suggestions.txt exists
    domain_file = os.path.join(workspace_path, 'domain_suggestions.txt')
    if not os.path.exists(domain_file):
        checks.append({"name": "domain_suggestions_file_exists", "passed": False, "detail": "File 'domain_suggestions.txt' not found"})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return
    
    checks.append({"name": "domain_suggestions_file_exists", "passed": True, "detail": "File 'domain_suggestions.txt' found"})
    
    try:
        with open(domain_file, 'r', encoding='utf-8') as f:
            content = f.read().lower()
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"})
        result = {"passed": False, "score": len([c for c in checks if c['passed']]) / len(checks), "checks": checks}
        print(json.dumps(result))
        return
    
    checks.append({"name": "file_readable", "passed": True, "detail": "File is readable"})
    
    # Check for task management related domain names
    task_keywords = ['task', 'project', 'team', 'manage', 'track', 'deadline', 'assign', 'work', 'plan', 'todo', 'schedule']
    has_relevant_names = any(keyword in content for keyword in task_keywords)
    checks.append({"name": "relevant_domain_names", "passed": has_relevant_names, "detail": "Contains task management related domain names" if has_relevant_names else "Missing task management related domain names"})
    
    # Check for multiple TLD extensions
    tld_patterns = ['.com', '.io', '.dev', '.app']
    found_tlds = [tld for tld in tld_patterns if tld in content]
    has_multiple_tlds = len(found_tlds) >= 3
    checks.append({"name": "multiple_tlds_checked", "passed": has_multiple_tlds, "detail": f"Found {len(found_tlds)} different TLDs: {found_tlds}" if has_multiple_tlds else f"Only found {len(found_tlds)} TLDs: {found_tlds}"})
    
    # Check for availability status indicators
    availability_indicators = ['available', 'taken', 'unavailable', 'registered', 'free', '✓', '✗', 'yes', 'no']
    has_availability_info = any(indicator in content for indicator in availability_indicators)
    checks.append({"name": "availability_status_included", "passed": has_availability_info, "detail": "Includes availability status for domain names" if has_availability_info else "Missing availability status information"})
    
    # Check for minimum number of domain suggestions (at least 5)
    # Count potential domain names by looking for TLD patterns
    domain_count = len(re.findall(r'\w+\.(com|io|dev|app|co|net|org)', content))
    has_enough_suggestions = domain_count >= 5
    checks.append({"name": "sufficient_domain_suggestions", "passed": has_enough_suggestions, "detail": f"Found {domain_count} domain suggestions" if has_enough_suggestions else f"Only found {domain_count} domain suggestions, need at least 5"})
    
    # Check for creative/explanatory content
    explanation_keywords = ['why', 'because', 'reason', 'memorable', 'brandable', 'short', 'clear', 'perfect', 'great']
    has_explanations = any(keyword in content for keyword in explanation_keywords)
    checks.append({"name": "includes_explanations", "passed": has_explanations, "detail": "Includes explanations or reasoning for domain suggestions" if has_explanations else "Missing explanations for domain choices"})
    
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    passed = score >= 0.8
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main(sys.argv[1])