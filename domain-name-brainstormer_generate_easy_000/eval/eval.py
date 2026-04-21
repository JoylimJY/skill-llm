import os
import sys
import json
import re

def eval_domain_suggestions(workspace_path):
    checks = []
    
    # Check if domain_suggestions.md file exists
    md_file = os.path.join(workspace_path, 'domain_suggestions.md')
    if not os.path.exists(md_file):
        checks.append({"name": "file_exists", "passed": False, "detail": "domain_suggestions.md file not found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "file_exists", "passed": True, "detail": "domain_suggestions.md file found"})
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read().lower()
    
    # Check for fitness/running related keywords
    fitness_keywords = ['run', 'fit', 'track', 'pace', 'mile', 'exercise', 'workout', 'athletic', 'sport', 'train']
    has_fitness_context = any(keyword in content for keyword in fitness_keywords)
    checks.append({"name": "fitness_context", "passed": has_fitness_context, "detail": f"Contains fitness/running context: {has_fitness_context}"})
    
    # Check for multiple TLD mentions
    tld_pattern = r'\.(com|io|app|fit|dev|ai)'
    tlds_found = len(set(re.findall(tld_pattern, content)))
    has_multiple_tlds = tlds_found >= 3
    checks.append({"name": "multiple_tlds", "passed": has_multiple_tlds, "detail": f"Found {tlds_found} different TLDs"})
    
    # Check for domain name suggestions (look for domain-like patterns)
    domain_pattern = r'[a-z]+\.(com|io|app|fit|dev|ai)'
    domain_suggestions = re.findall(domain_pattern, content)
    has_domain_suggestions = len(domain_suggestions) >= 3
    checks.append({"name": "domain_suggestions", "passed": has_domain_suggestions, "detail": f"Found {len(domain_suggestions)} domain suggestions"})
    
    # Check for availability information
    availability_keywords = ['available', 'taken', 'check', 'register']
    has_availability_info = any(keyword in content for keyword in availability_keywords)
    checks.append({"name": "availability_info", "passed": has_availability_info, "detail": f"Contains availability information: {has_availability_info}"})
    
    # Check for top recommendations
    recommendation_keywords = ['recommend', 'top', 'best', 'favorite', 'pick']
    has_recommendations = any(keyword in content for keyword in recommendation_keywords)
    checks.append({"name": "recommendations", "passed": has_recommendations, "detail": f"Contains recommendations: {has_recommendations}"})
    
    # Check for explanations/reasoning
    explanation_keywords = ['why', 'because', 'reason', 'perfect', 'memorable', 'short', 'brand']
    has_explanations = any(keyword in content for keyword in explanation_keywords)
    checks.append({"name": "explanations", "passed": has_explanations, "detail": f"Contains explanations: {has_explanations}"})
    
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.8
    
    return {"passed": passed, "score": score, "checks": checks}

if __name__ == "__main__":
    workspace = sys.argv[1]
    result = eval_domain_suggestions(workspace)
    print(json.dumps(result))