#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path
import re
from bs4 import BeautifulSoup

def evaluate_task(workspace_dir):
    workspace_path = Path(workspace_dir)
    checks = []
    score = 0.0
    
    # Check if bundle.html exists
    bundle_path = workspace_path / 'bundle.html'
    if not bundle_path.exists():
        checks.append({
            'name': 'bundle_exists',
            'passed': False,
            'detail': 'bundle.html file not found'
        })
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    checks.append({
        'name': 'bundle_exists',
        'passed': True,
        'detail': 'bundle.html file exists'
    })
    score += 10
    
    try:
        # Read and parse the HTML
        with open(bundle_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for React app structure
        has_react = 'React' in html_content or 'react' in html_content.lower()
        checks.append({
            'name': 'react_usage',
            'passed': has_react,
            'detail': 'React framework detected' if has_react else 'No React framework detected'
        })
        if has_react:
            score += 15
        
        # Check for task management related content
        content_lower = html_content.lower()
        has_task_content = any(term in content_lower for term in ['task', 'todo', 'progress', 'done', 'kanban', 'board'])
        checks.append({
            'name': 'task_content',
            'passed': has_task_content,
            'detail': 'Task management content found' if has_task_content else 'No task management content found'
        })
        if has_task_content:
            score += 15
        
        # Check for column structure (To Do, In Progress, Done)
        has_columns = all(col.lower().replace(' ', '') in content_lower.replace(' ', '') for col in ['todo', 'inprogress', 'done'])
        checks.append({
            'name': 'column_structure',
            'passed': has_columns,
            'detail': 'All required columns found' if has_columns else 'Missing required columns (To Do, In Progress, Done)'
        })
        if has_columns:
            score += 20
        
        # Check for drag and drop functionality
        has_dnd = any(term in content_lower for term in ['drag', 'drop', 'sortable', 'draggable', 'droppable'])
        checks.append({
            'name': 'drag_drop',
            'passed': has_dnd,
            'detail': 'Drag and drop functionality detected' if has_dnd else 'No drag and drop functionality found'
        })
        if has_dnd:
            score += 15
        
        # Check for dark mode functionality
        has_dark_mode = any(term in content_lower for term in ['dark', 'theme', 'mode'])
        checks.append({
            'name': 'dark_mode',
            'passed': has_dark_mode,
            'detail': 'Dark mode functionality detected' if has_dark_mode else 'No dark mode functionality found'
        })
        if has_dark_mode:
            score += 10
        
        # Check for date functionality
        has_dates = any(term in content_lower for term in ['date', 'due', 'calendar', 'deadline'])
        checks.append({
            'name': 'date_functionality',
            'passed': has_dates,
            'detail': 'Date functionality detected' if has_dates else 'No date functionality found'
        })
        if has_dates:
            score += 10
        
        # Check for professional styling (no excessive purple, not overly centered)
        has_purple_excess = content_lower.count('purple') > 5 or 'bg-purple' in content_lower
        has_excessive_centering = content_lower.count('center') > 10 or content_lower.count('justify-center') > 8
        is_professional = not (has_purple_excess or has_excessive_centering)
        checks.append({
            'name': 'professional_design',
            'passed': is_professional,
            'detail': 'Professional design detected' if is_professional else 'Design appears to have excessive purple or centering'
        })
        if is_professional:
            score += 5
        
        # Bonus: Check for state management
        has_state_mgmt = any(term in content_lower for term in ['usestate', 'state', 'setstate', 'reducer'])
        if has_state_mgmt:
            score += 10
            checks.append({
                'name': 'state_management',
                'passed': True,
                'detail': 'State management detected'
            })
        
    except Exception as e:
        checks.append({
            'name': 'parse_error',
            'passed': False,
            'detail': f'Error parsing HTML: {str(e)}'
        })
    
    # Normalize score to 0-100
    max_score = 110  # Total possible points
    normalized_score = min(100.0, (score / max_score) * 100)
    passed = normalized_score >= 70
    
    return {
        'passed': passed,
        'score': normalized_score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_directory>')
        sys.exit(1)
    
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result, indent=2))