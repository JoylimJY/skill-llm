#!/usr/bin/env python3
import sys
import os
import json
from bs4 import BeautifulSoup

def eval_task(workspace_dir):
    checks = []
    passed = True
    score = 0.0
    
    try:
        # Check if bundle.html exists
        bundle_path = os.path.join(workspace_dir, 'bundle.html')
        if not os.path.exists(bundle_path):
            checks.append({
                "name": "bundle_exists",
                "passed": False,
                "detail": "bundle.html file not found"
            })
            passed = False
        else:
            checks.append({
                "name": "bundle_exists",
                "passed": True,
                "detail": "bundle.html file exists"
            })
            score += 0.2
            
            # Parse HTML and check content
            with open(bundle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check for task management related text
            text_content = soup.get_text().lower()
            
            # Check for task-related keywords
            task_keywords = ['task', 'todo', 'add', 'complete', 'delete']
            found_keywords = [kw for kw in task_keywords if kw in text_content]
            
            if len(found_keywords) >= 3:
                checks.append({
                    "name": "task_content",
                    "passed": True,
                    "detail": f"Found task-related content: {found_keywords}"
                })
                score += 0.2
            else:
                checks.append({
                    "name": "task_content",
                    "passed": False,
                    "detail": f"Insufficient task-related keywords found: {found_keywords}"
                })
                passed = False
            
            # Check for React/JavaScript content
            if 'react' in content.lower() or 'function' in content.lower() or 'const' in content.lower():
                checks.append({
                    "name": "react_content",
                    "passed": True,
                    "detail": "Contains React/JavaScript code"
                })
                score += 0.2
            else:
                checks.append({
                    "name": "react_content",
                    "passed": False,
                    "detail": "No React/JavaScript code detected"
                })
                passed = False
            
            # Check for form elements (input, button)
            inputs = soup.find_all('input')
            buttons = soup.find_all('button')
            
            if len(inputs) > 0 and len(buttons) > 0:
                checks.append({
                    "name": "interactive_elements",
                    "passed": True,
                    "detail": f"Found {len(inputs)} input(s) and {len(buttons)} button(s)"
                })
                score += 0.2
            else:
                checks.append({
                    "name": "interactive_elements",
                    "passed": False,
                    "detail": f"Missing interactive elements: {len(inputs)} inputs, {len(buttons)} buttons"
                })
                passed = False
            
            # Check for Tailwind CSS classes
            if 'tailwind' in content.lower() or any(cls in content for cls in ['bg-', 'text-', 'p-', 'mx-', 'my-']):
                checks.append({
                    "name": "styling",
                    "passed": True,
                    "detail": "Contains Tailwind CSS styling"
                })
                score += 0.2
            else:
                checks.append({
                    "name": "styling",
                    "passed": False,
                    "detail": "No Tailwind CSS styling detected"
                })
                passed = False
        
    except Exception as e:
        checks.append({
            "name": "evaluation_error",
            "passed": False,
            "detail": f"Error during evaluation: {str(e)}"
        })
        passed = False
    
    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python eval_script.py <workspace_dir>")
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = eval_task(workspace_dir)
    print(json.dumps(result))