#!/usr/bin/env python3
import sys
import os
import json
import re

def evaluate_newsletter(workspace_dir):
    checks = []
    score = 0.0
    
    # Look for newsletter output file
    newsletter_files = []
    for file in os.listdir(workspace_dir):
        if 'newsletter' in file.lower() or 'update' in file.lower():
            if file.endswith(('.txt', '.md')):
                newsletter_files.append(file)
    
    if not newsletter_files:
        checks.append({
            'name': 'Newsletter file exists',
            'passed': False,
            'detail': 'No newsletter file found (.txt or .md with "newsletter" or "update" in name)'
        })
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    newsletter_file = newsletter_files[0]
    with open(os.path.join(workspace_dir, newsletter_file), 'r') as f:
        content = f.read()
    
    checks.append({
        'name': 'Newsletter file exists',
        'passed': True,
        'detail': f'Found newsletter file: {newsletter_file}'
    })
    score += 10
    
    # Check for proper newsletter structure with sections
    has_sections = bool(re.search(r'[:🎯📈💼🚀📢]|#{1,3}\s+\w+', content))
    checks.append({
        'name': 'Has organized sections',
        'passed': has_sections,
        'detail': 'Newsletter should have clear sections with headers or emoji markers'
    })
    if has_sections:
        score += 15
    
    # Check for bullet points (newsletter format)
    bullet_count = len(re.findall(r'^\s*[-*]\s+', content, re.MULTILINE))
    has_bullets = bullet_count >= 8
    checks.append({
        'name': 'Uses bullet point format',
        'passed': has_bullets,
        'detail': f'Found {bullet_count} bullet points (need at least 8 for newsletter format)'
    })
    if has_bullets:
        score += 15
    
    # Check for key company announcements mentioned
    funding_mentioned = 'series b' in content.lower() or '25m' in content.lower() or 'accel' in content.lower()
    checks.append({
        'name': 'Mentions Series B funding',
        'passed': funding_mentioned,
        'detail': 'Should mention the Series B funding announcement'
    })
    if funding_mentioned:
        score += 15
    
    # Check for product/engineering updates
    product_mentioned = 'onboarding' in content.lower() or 'api' in content.lower() or 'conversion' in content.lower()
    checks.append({
        'name': 'Includes product/engineering updates',
        'passed': product_mentioned,
        'detail': 'Should mention onboarding flow or API rewrite'
    })
    if product_mentioned:
        score += 10
    
    # Check for sales/business updates
    sales_mentioned = 'deal' in content.lower() or 'sales' in content.lower() or 'salesforce' in content.lower()
    checks.append({
        'name': 'Includes sales updates',
        'passed': sales_mentioned,
        'detail': 'Should mention enterprise deals or sales achievements'
    })
    if sales_mentioned:
        score += 10
    
    # Check for hiring updates
    hiring_mentioned = 'hiring' in content.lower() or 'new hire' in content.lower() or 'vp of product' in content.lower() or 'started' in content.lower()
    checks.append({
        'name': 'Mentions hiring activity',
        'passed': hiring_mentioned,
        'detail': 'Should mention new hires or hiring progress'
    })
    if hiring_mentioned:
        score += 10
    
    # Check for external press mention
    press_mentioned = 'techcrunch' in content.lower() or 'press' in content.lower() or 'article' in content.lower()
    checks.append({
        'name': 'References external press',
        'passed': press_mentioned,
        'detail': 'Should mention TechCrunch article or press coverage'
    })
    if press_mentioned:
        score += 5
    
    # Check for appropriate "we" tone (company voice)
    we_usage = len(re.findall(r'\bwe\b', content.lower()))
    appropriate_tone = we_usage >= 3
    checks.append({
        'name': 'Uses appropriate company voice',
        'passed': appropriate_tone,
        'detail': f'Uses "we" {we_usage} times (should be at least 3 for company voice)'
    })
    if appropriate_tone:
        score += 10
    
    # Check length (should be substantial but not too long)
    word_count = len(content.split())
    appropriate_length = 150 <= word_count <= 800
    checks.append({
        'name': 'Appropriate length',
        'passed': appropriate_length,
        'detail': f'Newsletter is {word_count} words (should be 150-800 words)'
    })
    if appropriate_length:
        score += 10
    
    passed = score >= 70
    return {
        'passed': passed,
        'score': min(100.0, score),
        'checks': checks
    }

if __name__ == '__main__':
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    result = evaluate_newsletter(workspace_dir)
    print(json.dumps(result))