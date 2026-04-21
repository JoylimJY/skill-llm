import os
import sys
import json
import re
from pathlib import Path

def evaluate_domain_suggestions(workspace_dir):
    checks = []
    
    # Find markdown file
    md_files = list(Path(workspace_dir).glob('*.md'))
    domain_file = None
    for f in md_files:
        if 'domain' in f.name.lower():
            domain_file = f
            break
    
    if not domain_file:
        domain_file = md_files[0] if md_files else None
    
    if not domain_file:
        checks.append({"name": "Output file exists", "passed": False, "detail": "No markdown file found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "Output file exists", "passed": True, "detail": f"Found {domain_file.name}"})
    
    try:
        content = domain_file.read_text().lower()
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": f"Error reading file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "File readable", "passed": True, "detail": "File content loaded successfully"})
    
    # Check for AI/chatbot/support related domain suggestions
    ai_keywords = ['chatbot', 'support', 'assist', 'help', 'auto', 'smart', 'ai', 'bot', 'care', 'service']
    has_relevant_domains = any(keyword in content for keyword in ai_keywords)
    checks.append({"name": "Contains relevant domain names", "passed": has_relevant_domains, "detail": "Found AI/support related domain suggestions" if has_relevant_domains else "No relevant domain names found"})
    
    # Check for multiple TLD coverage
    tlds = ['.com', '.io', '.ai', '.app']
    tld_count = sum(1 for tld in tlds if tld in content)
    checks.append({"name": "Covers multiple TLDs", "passed": tld_count >= 3, "detail": f"Found {tld_count}/4 requested TLDs"})
    
    # Check for availability indicators
    availability_indicators = ['available', 'taken', 'registered', 'free', 'unavailable']
    has_availability = any(indicator in content for indicator in availability_indicators)
    checks.append({"name": "Shows availability status", "passed": has_availability, "detail": "Includes availability information" if has_availability else "Missing availability status"})
    
    # Check for organized sections
    section_headers = ['available', 'taken', 'recommend', 'suggestion']
    section_count = sum(1 for header in section_headers if header in content)
    checks.append({"name": "Well-organized sections", "passed": section_count >= 2, "detail": f"Found {section_count} relevant sections"})
    
    # Check for explanations/reasoning
    explanation_keywords = ['why', 'because', 'reason', 'professional', 'memorable', 'trust']
    has_explanations = any(keyword in content for keyword in explanation_keywords)
    checks.append({"name": "Includes explanations", "passed": has_explanations, "detail": "Contains reasoning for suggestions" if has_explanations else "Missing explanations for domain choices"})
    
    # Check for multiple domain suggestions (at least 5)
    domain_pattern = r'\b\w+\.(com|io|ai|app)\b'
    domain_matches = re.findall(domain_pattern, content, re.IGNORECASE)
    domain_count = len(domain_matches)
    checks.append({"name": "Sufficient domain quantity", "passed": domain_count >= 5, "detail": f"Found {domain_count} domain suggestions"})
    
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.8
    
    return {"passed": passed, "score": score, "checks": checks}

if __name__ == '__main__':
    result = evaluate_domain_suggestions(sys.argv[1])
    print(json.dumps(result))