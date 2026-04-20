import sys
import os
import json
import re

def normalize(text):
    return re.sub(r'[\s\W]+', ' ', text.lower()).strip()

def fuzzy_contains(haystack, needle, threshold=75):
    try:
        from rapidfuzz import fuzz
        hay_norm = normalize(haystack)
        needle_norm = normalize(needle)
        if needle_norm in hay_norm:
            return True
        ratio = fuzz.partial_ratio(needle_norm, hay_norm)
        return ratio >= threshold
    except Exception:
        return normalize(needle) in normalize(haystack)

def run_checks(workspace):
    checks = []

    # Check 1: output file exists
    output_path = os.path.join(workspace, 'revenue_model.md')
    file_exists = os.path.isfile(output_path)
    checks.append({
        'name': 'output_file_exists',
        'passed': file_exists,
        'detail': 'revenue_model.md found' if file_exists else 'revenue_model.md not found in workspace'
    })

    if not file_exists:
        score = 0.0
        return {'passed': False, 'score': score, 'checks': checks}

    try:
        with open(output_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        checks.append({'name': 'file_readable', 'passed': False, 'detail': str(e)})
        return {'passed': False, 'score': 0.0, 'checks': checks}

    # Check 2: mentions subscription as primary model
    sub_terms = ['subscription', 'monthly', 'recurring', 'saas']
    sub_found = any(fuzzy_contains(content, t) for t in sub_terms)
    checks.append({
        'name': 'recommends_subscription_model',
        'passed': sub_found,
        'detail': 'Found subscription/recurring model recommendation' if sub_found else 'No clear subscription model recommendation found'
    })

    # Check 3: three revenue streams present
    stream_terms = ['primary', 'secondary', 'opportunistic']
    streams_found = all(fuzzy_contains(content, t) for t in stream_terms)
    checks.append({
        'name': 'three_stream_stack_present',
        'passed': streams_found,
        'detail': 'All three stream types (primary, secondary, opportunistic) mentioned' if streams_found else 'Missing one or more stream types'
    })

    # Check 4: pricing mentioned (dollar amounts)
    price_pattern = re.search(r'\$\s*\d+', content)
    price_found = price_pattern is not None
    checks.append({
        'name': 'specific_pricing_included',
        'passed': price_found,
        'detail': 'Found at least one dollar-amount price' if price_found else 'No specific pricing (e.g. $19/month) found'
    })

    # Check 5: payment flow template fields present
    flow_fields = ['payment trigger', 'billing tool', 'cancellation', 'free trial']
    flow_hits = [f for f in flow_fields if fuzzy_contains(content, f)]
    flow_ok = len(flow_hits) >= 3
    checks.append({
        'name': 'payment_flow_template_present',
        'passed': flow_ok,
        'detail': f'Found {len(flow_hits)}/4 payment flow fields: {flow_hits}'
    })

    # Check 6: 12-month projection present
    projection_terms = ['month 12', 'month12', '12 month', '12-month', 'year 1', 'annual']
    proj_found = any(fuzzy_contains(content, t) for t in projection_terms)
    checks.append({
        'name': 'twelve_month_projection_present',
        'passed': proj_found,
        'detail': 'Found 12-month or annual projection reference' if proj_found else 'No 12-month projection found'
    })

    # Check 7: references FreelanceCanvas or the business context
    brand_found = fuzzy_contains(content, 'freelancecanvas') or fuzzy_contains(content, 'freelance canvas') or fuzzy_contains(content, 'designer')
    checks.append({
        'name': 'references_business_context',
        'passed': brand_found,
        'detail': 'Content references the specific business context' if brand_found else 'No reference to FreelanceCanvas or designer context found'
    })

    # Check 8: mentions EU VAT or Paddle/Lemon Squeezy (constraint from context)
    tax_terms = ['vat', 'paddle', 'lemon squeezy', 'lemonsqueezy', 'tax']
    tax_found = any(fuzzy_contains(content, t) for t in tax_terms)
    checks.append({
        'name': 'addresses_eu_vat_constraint',
        'passed': tax_found,
        'detail': 'Addresses EU VAT or recommends appropriate billing tool' if tax_found else 'No mention of EU VAT handling or suitable billing tools'
    })

    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 6

    return {'passed': overall_passed, 'score': score, 'checks': checks}

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    try:
        result = run_checks(workspace)
    except Exception as e:
        result = {
            'passed': False,
            'score': 0.0,
            'checks': [{'name': 'eval_crashed', 'passed': False, 'detail': str(e)}]
        }
    print(json.dumps(result, indent=2))
