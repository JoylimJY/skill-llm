import sys
import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

def evaluate_expense_tracker(workspace_dir):
    checks = []
    workspace_path = Path(workspace_dir)
    
    # Check if bundle.html exists
    bundle_path = workspace_path / 'bundle.html'
    bundle_exists = bundle_path.exists()
    checks.append({
        'name': 'bundle_html_exists',
        'passed': bundle_exists,
        'detail': f'Bundle.html file exists: {bundle_exists}'
    })
    
    if not bundle_exists:
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    # Parse the HTML bundle
    with open(bundle_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check for React app structure
    react_root = soup.find('div', id='root') is not None
    checks.append({
        'name': 'react_root_exists',
        'passed': react_root,
        'detail': f'React root div found: {react_root}'
    })
    
    # Check for expense-related components in the bundled JavaScript
    has_expense_logic = any([
        'expense' in html_content.lower(),
        'category' in html_content.lower(),
        'dashboard' in html_content.lower()
    ])
    checks.append({
        'name': 'expense_logic_present',
        'passed': has_expense_logic,
        'detail': f'Expense-related logic found in bundle: {has_expense_logic}'
    })
    
    # Check for form elements (input, select, button)
    form_elements = len(soup.find_all(['input', 'select', 'button'])) > 0
    checks.append({
        'name': 'form_elements_present',
        'passed': form_elements,
        'detail': f'Form elements (input/select/button) found: {form_elements}'
    })
    
    # Check for Tailwind CSS classes
    tailwind_present = any([
        'class=' in html_content and any(tw_class in html_content for tw_class in ['flex', 'grid', 'p-', 'm-', 'bg-', 'text-']),
        'tailwindcss' in html_content.lower()
    ])
    checks.append({
        'name': 'tailwind_styling',
        'passed': tailwind_present,
        'detail': f'Tailwind CSS styling detected: {tailwind_present}'
    })
    
    # Check for shadcn/ui component usage patterns
    shadcn_patterns = any([
        'ui/' in html_content,
        'components/ui' in html_content,
        'Card' in html_content and 'CardContent' in html_content,
        'Button' in html_content,
        'Dialog' in html_content
    ])
    checks.append({
        'name': 'shadcn_components',
        'passed': shadcn_patterns,
        'detail': f'shadcn/ui component patterns found: {shadcn_patterns}'
    })
    
    # Check project structure was created
    project_dirs = list(workspace_path.glob('*/src'))
    project_structure = len(project_dirs) > 0
    checks.append({
        'name': 'project_structure',
        'passed': project_structure,
        'detail': f'React project structure created: {project_structure}'
    })
    
    # Check for package.json in project
    package_json_exists = len(list(workspace_path.glob('*/package.json'))) > 0
    checks.append({
        'name': 'package_json_exists',
        'passed': package_json_exists,
        'detail': f'package.json found in project: {package_json_exists}'
    })
    
    # Check bundle size is reasonable (should be substantial for a full React app)
    bundle_size_kb = bundle_path.stat().st_size / 1024
    reasonable_size = 50 < bundle_size_kb < 5000  # Between 50KB and 5MB
    checks.append({
        'name': 'bundle_size_reasonable',
        'passed': reasonable_size,
        'detail': f'Bundle size reasonable ({bundle_size_kb:.1f}KB): {reasonable_size}'
    })
    
    # Check for expense dashboard features in content
    dashboard_features = any([
        'total' in html_content.lower() and 'expense' in html_content.lower(),
        'chart' in html_content.lower() or 'graph' in html_content.lower(),
        'category' in html_content.lower() and 'amount' in html_content.lower()
    ])
    checks.append({
        'name': 'dashboard_features',
        'passed': dashboard_features,
        'detail': f'Dashboard features detected in bundle: {dashboard_features}'
    })
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    # Overall pass condition: most critical checks pass
    critical_passed = bundle_exists and react_root and has_expense_logic and project_structure
    overall_passed = critical_passed and score >= 0.7
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'args', 'passed': False, 'detail': 'Invalid arguments'}]}))
        sys.exit(1)
    
    result = evaluate_expense_tracker(sys.argv[1])
    print(json.dumps(result))