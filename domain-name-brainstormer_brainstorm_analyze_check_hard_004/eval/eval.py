import os
import sys
import re
import json

def evaluate_domain_analysis(workspace_dir):
    checks = []
    
    # Check if domain_analysis.md file exists
    analysis_file = os.path.join(workspace_dir, 'domain_analysis.md')
    file_exists = os.path.exists(analysis_file)
    checks.append({
        'name': 'domain_analysis.md file created',
        'passed': file_exists,
        'detail': 'Found domain_analysis.md file' if file_exists else 'Missing domain_analysis.md file'
    })
    
    if not file_exists:
        return {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
    
    # Read the analysis file
    try:
        with open(analysis_file, 'r', encoding='utf-8') as f:
            content = f.read().lower()
    except Exception as e:
        checks.append({
            'name': 'file readable',
            'passed': False,
            'detail': f'Error reading file: {str(e)}'
        })
        return {
            'passed': False,
            'score': len([c for c in checks if c['passed']]) / len(checks),
            'checks': checks
        }
    
    # Check for markdown structure
    has_headers = bool(re.search(r'#{1,6}\s+', content))
    checks.append({
        'name': 'markdown format with headers',
        'passed': has_headers,
        'detail': 'Contains markdown headers' if has_headers else 'Missing markdown headers'
    })
    
    # Check for minimum number of domain suggestions (at least 12)
    domain_pattern = r'([a-z0-9-]+\.(com|io|dev|ai|eco))'
    domains_found = re.findall(domain_pattern, content)
    has_enough_domains = len(domains_found) >= 12
    checks.append({
        'name': 'minimum 12 domain suggestions',
        'passed': has_enough_domains,
        'detail': f'Found {len(domains_found)} domain suggestions' if has_enough_domains else f'Only found {len(domains_found)} domains, need at least 12'
    })
    
    # Check for required TLD extensions
    required_tlds = ['com', 'io', 'dev', 'ai', 'eco']
    found_tlds = set()
    for domain, tld in domains_found:
        found_tlds.add(tld)
    
    has_all_tlds = all(tld in found_tlds for tld in required_tlds)
    checks.append({
        'name': 'covers all required TLD extensions',
        'passed': has_all_tlds,
        'detail': f'Found TLDs: {", ".join(sorted(found_tlds))}' if has_all_tlds else f'Missing TLDs: {", ".join(set(required_tlds) - found_tlds)}'
    })
    
    # Check for availability status mentions
    availability_keywords = ['available', 'taken', 'registered', 'unavailable']
    has_availability = any(keyword in content for keyword in availability_keywords)
    checks.append({
        'name': 'includes availability information',
        'passed': has_availability,
        'detail': 'Contains availability status information' if has_availability else 'Missing availability status information'
    })
    
    # Check for sustainability/tech relevance
    sustainability_keywords = ['sustainable', 'sustainability', 'green', 'eco', 'waste', 'zero waste', 'environment']
    tech_keywords = ['ai', 'tech', 'smart', 'digital', 'data', 'machine learning', 'predict']
    
    has_sustainability = any(keyword in content for keyword in sustainability_keywords)
    has_tech = any(keyword in content for keyword in tech_keywords)
    
    checks.append({
        'name': 'addresses sustainability theme',
        'passed': has_sustainability,
        'detail': 'Contains sustainability-related terms' if has_sustainability else 'Missing sustainability focus'
    })
    
    checks.append({
        'name': 'addresses technology theme', 
        'passed': has_tech,
        'detail': 'Contains technology-related terms' if has_tech else 'Missing technology focus'
    })
    
    # Check for restaurant/food industry relevance
    restaurant_keywords = ['restaurant', 'food', 'kitchen', 'menu', 'plate', 'dining', 'culinary', 'chef']
    has_restaurant_focus = any(keyword in content for keyword in restaurant_keywords)
    checks.append({
        'name': 'addresses restaurant/food industry',
        'passed': has_restaurant_focus,
        'detail': 'Contains restaurant/food industry terms' if has_restaurant_focus else 'Missing restaurant industry focus'
    })
    
    # Check for explanations/reasoning
    explanation_keywords = ['why', 'because', 'reason', 'memorable', 'brandable', 'conveys', 'suggests', 'implies']
    has_explanations = any(keyword in content for keyword in explanation_keywords)
    checks.append({
        'name': 'includes explanations for domain choices',
        'passed': has_explanations,
        'detail': 'Contains explanations for domain suggestions' if has_explanations else 'Missing explanations for domain choices'
    })
    
    # Check for top recommendations section
    recommendation_keywords = ['top', 'recommend', 'best', 'favorite', 'pick', 'choice']
    has_recommendations = any(keyword in content for keyword in recommendation_keywords)
    checks.append({
        'name': 'provides top recommendations',
        'passed': has_recommendations,
        'detail': 'Contains recommendation section' if has_recommendations else 'Missing top recommendations'
    })
    
    # Check for professional tone and structure
    section_keywords = ['available', 'taken', 'recommendations', 'analysis', 'suggestions']
    has_sections = sum(1 for keyword in section_keywords if keyword in content) >= 3
    checks.append({
        'name': 'well-structured with clear sections',
        'passed': has_sections,
        'detail': 'Contains multiple organized sections' if has_sections else 'Lacks clear section organization'
    })
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    score = passed_count / len(checks)
    
    return {
        'passed': score >= 0.8,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace_dir = sys.argv[1]
    result = evaluate_domain_analysis(workspace_dir)
    print(json.dumps(result))