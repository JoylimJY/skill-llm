import sys
import os
import json
import re
from pathlib import Path

def evaluate_task(workspace_dir):
    checks = []
    workspace_path = Path(workspace_dir)
    
    # Check 1: HTML file exists with correct name
    html_files = list(workspace_path.glob('ai_trends_presentation.html'))
    if html_files:
        html_file = html_files[0]
        checks.append({'name': 'HTML file created with correct name', 'passed': True, 'detail': 'Found ai_trends_presentation.html'})
        
        # Read HTML content for further checks
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read().lower()
        except:
            html_content = ''
    else:
        checks.append({'name': 'HTML file created with correct name', 'passed': False, 'detail': 'ai_trends_presentation.html not found'})
        html_content = ''
    
    # Check 2: Contains title slide content
    title_check = 'ai trends 2024' in html_content and 'future of technology conference' in html_content
    checks.append({'name': 'Title slide content present', 'passed': title_check, 'detail': 'Title and subtitle found' if title_check else 'Missing title or subtitle content'})
    
    # Check 3: Contains 5 slides worth of content
    slide_indicators = ['overview', 'machine learning', 'automation', 'conclusion']
    slide_count = sum(1 for indicator in slide_indicators if indicator in html_content) + (1 if 'ai trends 2024' in html_content else 0)
    slide_check = slide_count >= 4  # At least 4 of the 5 slides should have identifiable content
    checks.append({'name': 'Five slides content structure', 'passed': slide_check, 'detail': f'Found content for {slide_count} slides'})
    
    # Check 4: Tech Innovation theme colors applied
    tech_colors = ['#0066cc', '#ff6600', '#00cc66', '#f8f9fa', '#333333']
    color_matches = sum(1 for color in tech_colors if color in html_content or color.upper() in html_content.upper())
    color_check = color_matches >= 2  # At least 2 theme colors should be present
    checks.append({'name': 'Tech Innovation theme colors applied', 'passed': color_check, 'detail': f'Found {color_matches} theme colors in HTML'})
    
    # Check 5: Tech Innovation theme fonts applied
    font_check = 'roboto' in html_content or 'open sans' in html_content
    checks.append({'name': 'Tech Innovation theme fonts applied', 'passed': font_check, 'detail': 'Theme fonts found' if font_check else 'Theme fonts not found'})
    
    # Check 6: HTML structure (basic HTML tags)
    html_structure = '<html' in html_content or '<head' in html_content or '<body' in html_content
    checks.append({'name': 'Valid HTML structure', 'passed': html_structure, 'detail': 'HTML tags found' if html_structure else 'Missing basic HTML structure'})
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    total_count = len(checks)
    score = passed_count / total_count
    overall_passed = score >= 0.8
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace_dir = sys.argv[1]
    result = evaluate_task(workspace_dir)
    print(json.dumps(result))