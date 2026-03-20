import sys
import os
import json
import re
from pathlib import Path

def check_dashboard_implementation(workspace_dir):
    checks = []
    workspace_path = Path(workspace_dir)
    
    # Check for main HTML/React files
    html_files = list(workspace_path.glob('**/*.html')) + list(workspace_path.glob('**/*.jsx')) + list(workspace_path.glob('**/*.tsx'))
    main_files = [f for f in html_files if any(keyword in f.name.lower() for keyword in ['index', 'app', 'dashboard', 'main'])]
    
    if not main_files:
        checks.append({'name': 'Main file exists', 'passed': False, 'detail': 'No main HTML/React files found'})
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    checks.append({'name': 'Main file exists', 'passed': True, 'detail': f'Found main file: {main_files[0].name}'})
    
    # Read main file content
    main_file = main_files[0]
    try:
        content = main_file.read_text(encoding='utf-8')
    except:
        checks.append({'name': 'File readable', 'passed': False, 'detail': 'Could not read main file'})
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    checks.append({'name': 'File readable', 'passed': True, 'detail': 'Main file is readable'})
    
    # Check for marker content
    marker_found = 'CRYPTO_DASHBOARD_FINTECH_2024' in content
    checks.append({'name': 'Marker content present', 'passed': marker_found, 'detail': 'Required marker found in code' if marker_found else 'Marker content missing'})
    
    # Check for cryptocurrency-related content
    crypto_keywords = ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'portfolio', 'price', 'solana', 'sol']
    crypto_content = any(keyword.lower() in content.lower() for keyword in crypto_keywords)
    checks.append({'name': 'Cryptocurrency content', 'passed': crypto_content, 'detail': 'Crypto-related content found' if crypto_content else 'No crypto content detected'})
    
    # Check for dashboard/fintech UI elements
    ui_keywords = ['dashboard', 'chart', 'portfolio', 'balance', 'holdings', 'performance', 'value', 'usd']
    ui_content = sum(1 for keyword in ui_keywords if keyword.lower() in content.lower())
    ui_check = ui_content >= 3
    checks.append({'name': 'Dashboard UI elements', 'passed': ui_check, 'detail': f'Found {ui_content} dashboard-related terms'})
    
    # Check for premium styling indicators
    style_indicators = ['gradient', 'shadow', 'animation', 'transition', 'font-weight', 'opacity', 'transform', 'backdrop', 'blur']
    style_content = sum(1 for indicator in style_indicators if indicator.lower() in content.lower())
    style_check = style_content >= 3
    checks.append({'name': 'Premium styling', 'passed': style_check, 'detail': f'Found {style_content} styling techniques'})
    
    # Check for interactivity
    interactive_keywords = ['onclick', 'onhover', 'usestate', 'useeffect', 'event', 'handler', ':hover', 'click']
    interactive_content = any(keyword.lower() in content.lower() for keyword in interactive_keywords)
    checks.append({'name': 'Interactive elements', 'passed': interactive_content, 'detail': 'Interactive features found' if interactive_content else 'No interactivity detected'})
    
    # Check for data visualization elements
    chart_keywords = ['chart', 'graph', 'canvas', 'svg', 'line', 'path', 'recharts', 'chartjs', 'd3']
    chart_content = any(keyword.lower() in content.lower() for keyword in chart_keywords)
    checks.append({'name': 'Data visualization', 'passed': chart_content, 'detail': 'Chart/visualization elements found' if chart_content else 'No data visualization detected'})
    
    # Check for responsive design
    responsive_keywords = ['@media', 'responsive', 'mobile', 'flex', 'grid', 'viewport', 'breakpoint']
    responsive_content = any(keyword.lower() in content.lower() for keyword in responsive_keywords)
    checks.append({'name': 'Responsive design', 'passed': responsive_content, 'detail': 'Responsive design elements found' if responsive_content else 'No responsive design detected'})
    
    # Check for professional color scheme (avoid generic purple gradients)
    color_patterns = re.findall(r'#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|rgb\([^)]+\)|rgba\([^)]+\)', content)
    professional_colors = len(color_patterns) >= 5
    checks.append({'name': 'Professional color scheme', 'passed': professional_colors, 'detail': f'Found {len(color_patterns)} color definitions'})
    
    # Check for premium typography
    font_keywords = ['font-family', 'font-weight', 'letter-spacing', 'line-height', 'typography']
    font_content = sum(1 for keyword in font_keywords if keyword.lower() in content.lower())
    typography_check = font_content >= 2
    checks.append({'name': 'Premium typography', 'passed': typography_check, 'detail': f'Found {font_content} typography properties'})
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    # Overall pass requires most critical checks
    critical_passes = [
        checks[0]['passed'],  # Main file exists
        checks[1]['passed'],  # File readable  
        checks[2]['passed'],  # Marker content
        checks[3]['passed'],  # Crypto content
        checks[4]['passed']   # Dashboard UI
    ]
    
    overall_passed = sum(critical_passes) >= 4 and score >= 0.6
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_directory>')
        sys.exit(1)
    
    result = check_dashboard_implementation(sys.argv[1])
    print(json.dumps(result))