#!/usr/bin/env python3
import sys
import os
import json
import subprocess
from pathlib import Path

def check_task_completion(workspace_dir):
    checks = []
    score = 0.0
    
    workspace_path = Path(workspace_dir)
    
    # Check if requirements file exists with marker
    req_file = workspace_path / 'task_requirements.json'
    if req_file.exists():
        with open(req_file) as f:
            reqs = json.load(f)
            if reqs.get('validation_marker') == 'FINANCE_DASHBOARD_TASK_2024':
                checks.append({"name": "Task marker validation", "passed": True, "detail": "Correct task marker found"})
                score += 0.1
            else:
                checks.append({"name": "Task marker validation", "passed": False, "detail": "Invalid task marker"})
    else:
        checks.append({"name": "Task marker validation", "passed": False, "detail": "Requirements file not found"})
    
    # Check if bundle.html was created
    bundle_file = workspace_path / 'bundle.html'
    if bundle_file.exists():
        checks.append({"name": "Bundle file creation", "passed": True, "detail": "bundle.html created successfully"})
        score += 0.15
        
        # Read and analyze bundle content
        try:
            with open(bundle_file, 'r', encoding='utf-8') as f:
                bundle_content = f.read()
                
            # Check for React and modern patterns
            if 'React' in bundle_content or 'useState' in bundle_content:
                checks.append({"name": "React framework usage", "passed": True, "detail": "React patterns detected"})
                score += 0.1
            else:
                checks.append({"name": "React framework usage", "passed": False, "detail": "No React patterns found"})
            
            # Check for expense tracking features
            expense_keywords = ['expense', 'spending', 'category', 'filter', 'monthly', 'yearly']
            if any(keyword.lower() in bundle_content.lower() for keyword in expense_keywords):
                checks.append({"name": "Expense tracking features", "passed": True, "detail": "Expense tracking elements found"})
                score += 0.15
            else:
                checks.append({"name": "Expense tracking features", "passed": False, "detail": "No expense tracking features detected"})
            
            # Check for budget comparison features
            budget_keywords = ['budget', 'actual', 'progress', 'comparison']
            if any(keyword.lower() in bundle_content.lower() for keyword in budget_keywords):
                checks.append({"name": "Budget comparison features", "passed": True, "detail": "Budget tracking elements found"})
                score += 0.15
            else:
                checks.append({"name": "Budget comparison features", "passed": False, "detail": "No budget comparison features detected"})
            
            # Check for investment portfolio features  
            investment_keywords = ['portfolio', 'investment', 'allocation', 'chart', 'performance']
            if any(keyword.lower() in bundle_content.lower() for keyword in investment_keywords):
                checks.append({"name": "Investment portfolio features", "passed": True, "detail": "Investment portfolio elements found"})
                score += 0.15
            else:
                checks.append({"name": "Investment portfolio features", "passed": False, "detail": "No investment portfolio features detected"})
            
            # Check for financial goals tracking
            goals_keywords = ['goals', 'target', 'achievement', 'milestone']
            if any(keyword.lower() in bundle_content.lower() for keyword in goals_keywords):
                checks.append({"name": "Financial goals tracking", "passed": True, "detail": "Goals tracking elements found"})
                score += 0.1
            else:
                checks.append({"name": "Financial goals tracking", "passed": False, "detail": "No goals tracking features detected"})
            
            # Check for theme toggle functionality
            theme_keywords = ['theme', 'dark', 'light', 'toggle', 'mode']
            if any(keyword.lower() in bundle_content.lower() for keyword in theme_keywords):
                checks.append({"name": "Theme toggle functionality", "passed": True, "detail": "Theme switching elements found"})
                score += 0.1
            else:
                checks.append({"name": "Theme toggle functionality", "passed": False, "detail": "No theme toggle functionality detected"})
            
            # Check for responsive design patterns
            responsive_keywords = ['responsive', 'mobile', 'sm:', 'md:', 'lg:', 'xl:', 'grid', 'flex']
            if any(keyword.lower() in bundle_content.lower() for keyword in responsive_keywords):
                checks.append({"name": "Responsive design patterns", "passed": True, "detail": "Responsive design elements found"})
                score += 0.1
            else:
                checks.append({"name": "Responsive design patterns", "passed": False, "detail": "No responsive design patterns detected"})
            
            # Check bundle size (should be substantial for complex app)
            bundle_size = len(bundle_content)
            if bundle_size > 50000:  # At least 50KB for a complex dashboard
                checks.append({"name": "Bundle complexity", "passed": True, "detail": f"Bundle size indicates complex application ({bundle_size} bytes)"})
                score += 0.05
            else:
                checks.append({"name": "Bundle complexity", "passed": False, "detail": f"Bundle too small for complex dashboard ({bundle_size} bytes)"})
                
        except Exception as e:
            checks.append({"name": "Bundle content analysis", "passed": False, "detail": f"Error reading bundle: {str(e)}"})
            
    else:
        checks.append({"name": "Bundle file creation", "passed": False, "detail": "bundle.html not found"})
    
    # Check if project structure was created properly
    expected_files = ['package.json', 'tsconfig.json', 'tailwind.config.js', 'vite.config.ts']
    structure_score = 0
    for file in expected_files:
        if (workspace_path / file).exists():
            structure_score += 1
    
    if structure_score == len(expected_files):
        checks.append({"name": "Project structure", "passed": True, "detail": "All config files created properly"})
        score += 0.05
    else:
        checks.append({"name": "Project structure", "passed": False, "detail": f"Missing config files ({structure_score}/{len(expected_files)} found)"})
    
    passed = score >= 0.7  # Require 70% to pass
    return {"passed": passed, "score": score, "checks": checks}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Usage", "passed": False, "detail": "Workspace directory argument required"}]}))
        sys.exit(1)
    
    result = check_task_completion(sys.argv[1])
    print(json.dumps(result))