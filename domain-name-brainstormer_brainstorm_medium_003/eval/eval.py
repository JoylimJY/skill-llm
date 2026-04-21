import sys
import os
import re

def check_file_exists(workspace_dir):
    filepath = os.path.join(workspace_dir, 'domain_suggestions.md')
    return os.path.isfile(filepath), filepath

def check_content_structure(content):
    checks = []
    content_lower = content.lower()
    
    # Check for main sections
    has_available = any(keyword in content_lower for keyword in ['available', 'free', 'open'])
    checks.append(('has_available_section', has_available, 'Contains available domains section'))
    
    has_taken = any(keyword in content_lower for keyword in ['taken', 'unavailable', 'registered'])
    checks.append(('has_taken_section', has_taken, 'Contains taken/unavailable domains section'))
    
    has_recommendations = any(keyword in content_lower for keyword in ['recommend', 'top pick', 'best', 'suggestion'])
    checks.append(('has_recommendations', has_recommendations, 'Contains recommendations section'))
    
    return checks

def check_domain_suggestions(content):
    checks = []
    content_lower = content.lower()
    
    # Check for business/CRM related terms
    business_terms = ['crm', 'lead', 'sales', 'client', 'customer', 'business', 'growth', 'connect', 'manage', 'track']
    has_relevant_terms = any(term in content_lower for term in business_terms)
    checks.append(('relevant_domain_terms', has_relevant_terms, 'Contains business/CRM related domain terms'))
    
    # Check for multiple TLD mentions
    tlds = ['.com', '.io', '.dev', '.app', '.co']
    mentioned_tlds = sum(1 for tld in tlds if tld in content_lower)
    has_multiple_tlds = mentioned_tlds >= 3
    checks.append(('multiple_tlds', has_multiple_tlds, f'Mentions multiple TLDs ({mentioned_tlds}/5 found)'))
    
    # Check for domain count (should suggest multiple options)
    domain_pattern = r'\w+\.(com|io|dev|app|co)'
    domain_matches = re.findall(domain_pattern, content_lower, re.IGNORECASE)
    has_sufficient_domains = len(domain_matches) >= 5
    checks.append(('sufficient_domains', has_sufficient_domains, f'Contains sufficient domain suggestions ({len(domain_matches)} found)'))
    
    return checks

def check_explanations(content):
    checks = []
    content_lower = content.lower()
    
    # Check for explanatory content
    explanation_keywords = ['why', 'because', 'reason', 'convey', 'professional', 'trust', 'memorable', 'brandable']
    has_explanations = any(keyword in content_lower for keyword in explanation_keywords)
    checks.append(('has_explanations', has_explanations, 'Contains explanations for domain suggestions'))
    
    # Check for target audience consideration
    audience_keywords = ['small business', 'entrepreneur', 'affordable', 'professional', 'growth']
    considers_audience = any(keyword in content_lower for keyword in audience_keywords)
    checks.append(('considers_audience', considers_audience, 'Considers target audience in suggestions'))
    
    return checks

def main():
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'usage', 'passed': False, 'detail': 'Invalid usage'}]}))
        return
    
    workspace_dir = sys.argv[1]
    all_checks = []
    
    # Check if file exists
    file_exists, filepath = check_file_exists(workspace_dir)
    all_checks.append({'name': 'file_exists', 'passed': file_exists, 'detail': 'domain_suggestions.md file exists'})
    
    if not file_exists:
        score = sum(1 for c in all_checks if c['passed']) / len(all_checks)
        result = {'passed': score == 1.0, 'score': score, 'checks': all_checks}
        print(json.dumps(result))
        return
    
    # Read and analyze content
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        all_checks.append({'name': 'file_readable', 'passed': False, 'detail': f'Could not read file: {str(e)}'})
        score = sum(1 for c in all_checks if c['passed']) / len(all_checks)
        result = {'passed': score == 1.0, 'score': score, 'checks': all_checks}
        print(json.dumps(result))
        return
    
    all_checks.append({'name': 'file_readable', 'passed': True, 'detail': 'File is readable'})
    
    # Run content checks
    structure_checks = check_content_structure(content)
    domain_checks = check_domain_suggestions(content)
    explanation_checks = check_explanations(content)
    
    # Convert to required format
    for name, passed, detail in structure_checks + domain_checks + explanation_checks:
        all_checks.append({'name': name, 'passed': passed, 'detail': detail})
    
    # Calculate final score
    score = sum(1 for c in all_checks if c['passed']) / len(all_checks)
    passed = score >= 0.8
    
    result = {'passed': passed, 'score': score, 'checks': all_checks}
    print(json.dumps(result))

if __name__ == '__main__':
    import json
    main()