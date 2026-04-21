import sys
import os
import re
import json
from pathlib import Path

def evaluate_domain_analysis(workspace_dir):
    checks = []
    workspace_path = Path(workspace_dir)
    
    # Check 1: Required output file exists
    target_files = list(workspace_path.glob('*domain*analysis*.md')) + list(workspace_path.glob('domain_analysis.md'))
    if not target_files:
        checks.append({'name': 'output_file_exists', 'passed': False, 'detail': 'No domain_analysis.md file found'})
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    analysis_file = target_files[0]
    checks.append({'name': 'output_file_exists', 'passed': True, 'detail': f'Found analysis file: {analysis_file.name}'})
    
    try:
        content = analysis_file.read_text(encoding='utf-8').lower()
    except Exception as e:
        checks.append({'name': 'file_readable', 'passed': False, 'detail': f'Could not read file: {e}'})
        return {'passed': False, 'score': len([c for c in checks if c['passed']]) / (len(checks) + 1), 'checks': checks}
    
    checks.append({'name': 'file_readable', 'passed': True, 'detail': 'File is readable'})
    
    # Check 2: Contains at least 15 domain suggestions
    domain_patterns = [
        r'\b\w+\.(com|io|ai|finance|crypto)\b',
        r'[a-z]+\.[a-z]+',
        r'\d+\.\s+[a-z]+\.[a-z]+'
    ]
    
    all_domains = set()
    for pattern in domain_patterns:
        domains = re.findall(pattern, content)
        all_domains.update(domains if isinstance(domains[0] if domains else '', str) else [d[0] if isinstance(d, tuple) else d for d in domains])
    
    # Also check for domain-like patterns in lists
    list_domains = re.findall(r'[-*]\s*([a-z]+\.[a-z]+)', content)
    all_domains.update(list_domains)
    
    unique_domains = len(all_domains)
    domain_count_passed = unique_domains >= 10  # Allow some flexibility
    checks.append({'name': 'minimum_domain_count', 'passed': domain_count_passed, 'detail': f'Found {unique_domains} unique domains (need ≥10)'})
    
    # Check 3: Includes required TLD extensions
    required_tlds = ['.com', '.io', '.ai', '.finance', '.crypto']
    found_tlds = []
    for tld in required_tlds:
        if tld in content or tld.replace('.', '') in content:
            found_tlds.append(tld)
    
    tld_coverage = len(found_tlds) / len(required_tlds)
    tld_passed = tld_coverage >= 0.6  # At least 3 out of 5 TLDs
    checks.append({'name': 'tld_coverage', 'passed': tld_passed, 'detail': f'Covers {len(found_tlds)}/5 required TLDs: {found_tlds}'})
    
    # Check 4: Shows availability status
    availability_keywords = ['available', 'taken', 'registered', 'unavailable', '✓', '✗', 'status']
    has_availability = any(keyword in content for keyword in availability_keywords)
    checks.append({'name': 'availability_status', 'passed': has_availability, 'detail': 'Contains availability status indicators'})
    
    # Check 5: Includes pricing information
    pricing_keywords = ['price', 'pricing', 'cost', '$', 'usd', 'year', 'annual', 'registration']
    has_pricing = any(keyword in content for keyword in pricing_keywords)
    checks.append({'name': 'pricing_information', 'passed': has_pricing, 'detail': 'Contains pricing information'})
    
    # Check 6: Contains branding recommendations
    branding_keywords = ['brand', 'recommend', 'suggestion', 'why', 'because', 'memorable', 'professional', 'catchy', 'perfect']
    has_branding = any(keyword in content for keyword in branding_keywords)
    checks.append({'name': 'branding_recommendations', 'passed': has_branding, 'detail': 'Contains branding insights/recommendations'})
    
    # Check 7: Fintech/crypto relevance
    fintech_keywords = ['fintech', 'crypto', 'defi', 'yield', 'portfolio', 'trading', 'blockchain', 'bitcoin', 'ethereum', 'investment']
    relevant_count = sum(1 for keyword in fintech_keywords if keyword in content)
    is_relevant = relevant_count >= 3
    checks.append({'name': 'domain_relevance', 'passed': is_relevant, 'detail': f'Domain suggestions are relevant to fintech/crypto ({relevant_count} relevant keywords found)'})
    
    # Check 8: Proper markdown formatting
    markdown_indicators = ['#', '##', '###', '*', '-', '1.', '2.', '**', '__']
    has_markdown = any(indicator in content for indicator in markdown_indicators)
    checks.append({'name': 'markdown_formatting', 'passed': has_markdown, 'detail': 'Uses proper markdown formatting'})
    
    # Calculate final score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    overall_passed = score >= 0.75  # Allow some flexibility for hard task
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'script_args', 'passed': False, 'detail': 'Invalid arguments'}]}))
        sys.exit(1)
    
    result = evaluate_domain_analysis(sys.argv[1])
    print(json.dumps(result))