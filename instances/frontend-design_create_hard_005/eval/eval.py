#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path
try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system('pip3 install beautifulsoup4')
    from bs4 import BeautifulSoup

def evaluate_dashboard(workspace_dir):
    checks = []
    score = 0.0
    
    workspace_path = Path(workspace_dir)
    
    # Check for HTML files
    html_files = list(workspace_path.glob('**/*.html')) + list(workspace_path.glob('**/*.jsx')) + list(workspace_path.glob('**/*.js'))
    if not html_files:
        checks.append({'name': 'html_files_exist', 'passed': False, 'detail': 'No HTML, JSX, or JS files found'})
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    checks.append({'name': 'html_files_exist', 'passed': True, 'detail': f'Found {len(html_files)} implementation files'})
    score += 10
    
    # Check for CSS files or styled components
    css_files = list(workspace_path.glob('**/*.css')) + list(workspace_path.glob('**/*.scss'))
    has_styling = len(css_files) > 0
    
    # Read all implementation files to check content
    all_content = ''
    for file_path in html_files + css_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                all_content += f.read().lower()
        except:
            continue
    
    # Check for portfolio section
    portfolio_indicators = ['portfolio', 'total', 'value', 'balance']
    has_portfolio = any(indicator in all_content for indicator in portfolio_indicators)
    checks.append({'name': 'portfolio_section', 'passed': has_portfolio, 'detail': 'Portfolio overview section implemented' if has_portfolio else 'Portfolio section missing'})
    if has_portfolio:
        score += 15
    
    # Check for chart/visualization elements
    chart_indicators = ['chart', 'graph', 'visualization', 'canvas', 'svg', 'pie', 'donut', 'arc']
    has_charts = any(indicator in all_content for indicator in chart_indicators)
    checks.append({'name': 'chart_visualization', 'passed': has_charts, 'detail': 'Chart visualizations implemented' if has_charts else 'No chart visualizations found'})
    if has_charts:
        score += 20
    
    # Check for cryptocurrency data usage
    crypto_indicators = ['btc', 'bitcoin', 'eth', 'ethereum', 'sol', 'solana', 'ada', 'cardano']
    uses_crypto_data = any(indicator in all_content for indicator in crypto_indicators)
    checks.append({'name': 'crypto_data_usage', 'passed': uses_crypto_data, 'detail': 'Uses cryptocurrency data' if uses_crypto_data else 'Cryptocurrency data not utilized'})
    if uses_crypto_data:
        score += 15
    
    # Check for transaction history
    transaction_indicators = ['transaction', 'history', 'buy', 'sell', 'trade']
    has_transactions = any(indicator in all_content for indicator in transaction_indicators)
    checks.append({'name': 'transaction_history', 'passed': has_transactions, 'detail': 'Transaction history implemented' if has_transactions else 'Transaction history missing'})
    if has_transactions:
        score += 15
    
    # Check for animations/interactions
    animation_indicators = ['animation', 'transition', 'hover', 'keyframes', '@keyframes', 'transform', 'opacity']
    has_animations = any(indicator in all_content for indicator in animation_indicators)
    checks.append({'name': 'animations_interactions', 'passed': has_animations, 'detail': 'Animations and interactions implemented' if has_animations else 'No animations or interactions found'})
    if has_animations:
        score += 15
    
    # Check for distinctive styling (avoiding generic choices)
    generic_indicators = ['inter', 'roboto', 'arial', 'system']
    distinctive_indicators = ['font-family', 'custom', 'gradient', 'shadow', 'border-radius']
    avoids_generic = not any(generic in all_content for generic in generic_indicators)
    has_distinctive = any(distinctive in all_content for distinctive in distinctive_indicators)
    is_distinctive = avoids_generic and has_distinctive
    checks.append({'name': 'distinctive_design', 'passed': is_distinctive, 'detail': 'Distinctive design aesthetic' if is_distinctive else 'Generic or basic styling'})
    if is_distinctive:
        score += 10
    
    # Check for responsive design indicators
    responsive_indicators = ['@media', 'responsive', 'flex', 'grid', 'mobile']
    is_responsive = any(indicator in all_content for indicator in responsive_indicators)
    checks.append({'name': 'responsive_design', 'passed': is_responsive, 'detail': 'Responsive design implemented' if is_responsive else 'No responsive design indicators'})
    if is_responsive:
        score += 10
    
    passed = score >= 60  # Require at least 60% score to pass
    final_score = min(score / 100, 1.0)  # Normalize to 0-1
    
    return {
        'passed': passed,
        'score': final_score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python eval_script.py <workspace_directory>')
        sys.exit(1)
    
    result = evaluate_dashboard(sys.argv[1])
    print(json.dumps(result, indent=2))