#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import time
from pathlib import Path

def check_task_completion(workspace_dir):
    checks = []
    total_score = 0
    max_score = 100
    
    workspace_path = Path(workspace_dir)
    
    # Check 1: Automation script exists (10 points)
    automation_files = list(workspace_path.glob('*automation*.py')) + list(workspace_path.glob('*test*.py')) + list(workspace_path.glob('*checkout*.py'))
    if automation_files:
        checks.append({
            'name': 'automation_script_exists',
            'passed': True,
            'detail': f'Found automation script: {automation_files[0].name}'
        })
        total_score += 10
    else:
        checks.append({
            'name': 'automation_script_exists',
            'passed': False,
            'detail': 'No automation script found'
        })
    
    # Check 2: Screenshots directory exists (15 points)
    screenshot_files = list(workspace_path.glob('*.png')) + list(workspace_path.glob('screenshots/*.png')) + list(workspace_path.glob('**/screenshots/*.png'))
    if screenshot_files:
        checks.append({
            'name': 'screenshots_captured',
            'passed': True,
            'detail': f'Found {len(screenshot_files)} screenshot(s)'
        })
        total_score += 15
        
        # Check if screenshots show key steps
        screenshot_names = [f.name.lower() for f in screenshot_files]
        key_steps = ['product', 'cart', 'checkout', 'confirm']
        found_steps = [step for step in key_steps if any(step in name for name in screenshot_names)]
        if len(found_steps) >= 2:
            total_score += 10
            checks.append({
                'name': 'key_screenshots_captured',
                'passed': True,
                'detail': f'Screenshots captured for key steps: {", ".join(found_steps)}'
            })
        else:
            checks.append({
                'name': 'key_screenshots_captured',
                'passed': False,
                'detail': 'Missing screenshots for key checkout steps'
            })
    else:
        checks.append({
            'name': 'screenshots_captured',
            'passed': False,
            'detail': 'No screenshots found'
        })
        checks.append({
            'name': 'key_screenshots_captured',
            'passed': False,
            'detail': 'No screenshots found'
        })
    
    # Check 3: Playwright usage verification (15 points)
    if automation_files:
        automation_content = automation_files[0].read_text()
        playwright_indicators = [
            'playwright' in automation_content.lower(),
            'browser' in automation_content,
            'page.goto' in automation_content,
            'wait_for_load_state' in automation_content or 'networkidle' in automation_content
        ]
        
        if sum(playwright_indicators) >= 3:
            checks.append({
                'name': 'proper_playwright_usage',
                'passed': True,
                'detail': 'Script uses Playwright correctly with proper waits'
            })
            total_score += 15
        else:
            checks.append({
                'name': 'proper_playwright_usage',
                'passed': False,
                'detail': 'Script missing proper Playwright usage or waits'
            })
    else:
        checks.append({
            'name': 'proper_playwright_usage',
            'passed': False,
            'detail': 'No automation script to evaluate'
        })
    
    # Check 4: Multi-server setup usage (20 points)
    if automation_files:
        # Look for evidence of with_server.py usage or multiple server handling
        script_files = list(workspace_path.glob('*.py')) + list(workspace_path.glob('*.sh'))
        server_setup_found = False
        
        for script_file in script_files:
            content = script_file.read_text()
            if ('with_server.py' in content or 
                ('3001' in content and '3002' in content and '3000' in content) or
                ('multiple' in content.lower() and 'server' in content.lower())):
                server_setup_found = True
                break
        
        if server_setup_found:
            checks.append({
                'name': 'multi_server_setup',
                'passed': True,
                'detail': 'Evidence of multi-server setup found'
            })
            total_score += 20
        else:
            checks.append({
                'name': 'multi_server_setup',
                'passed': False,
                'detail': 'No evidence of proper multi-server setup'
            })
    else:
        checks.append({
            'name': 'multi_server_setup',
            'passed': False,
            'detail': 'No automation script to evaluate server setup'
        })
    
    # Check 5: Payment flow verification (15 points)
    log_files = list(workspace_path.glob('*.log')) + list(workspace_path.glob('*.txt'))
    payment_verification = False
    
    if automation_files:
        automation_content = automation_files[0].read_text()
        payment_indicators = [
            'payment' in automation_content.lower(),
            'checkout' in automation_content.lower(),
            'card' in automation_content.lower() or 'MARKER_CARDHOLDER' in automation_content,
            '3002' in automation_content  # Payment service port
        ]
        
        if sum(payment_indicators) >= 3:
            payment_verification = True
    
    # Also check log files for payment markers
    for log_file in log_files:
        try:
            content = log_file.read_text()
            if ('MARKER_PAYMENT_SUCCESS' in content or 'MARKER_TXN_' in content or 'PAYMENT_LOG' in content):
                payment_verification = True
                break
        except:
            pass
    
    if payment_verification:
        checks.append({
            'name': 'payment_flow_verification',
            'passed': True,
            'detail': 'Payment processing flow properly tested'
        })
        total_score += 15
    else:
        checks.append({
            'name': 'payment_flow_verification',
            'passed': False,
            'detail': 'Payment flow verification not found'
        })
    
    # Check 6: Async handling and loading states (15 points)
    if automation_files:
        automation_content = automation_files[0].read_text()
        async_indicators = [
            'loading' in automation_content.lower(),
            'wait_for_selector' in automation_content,
            'wait_for_timeout' in automation_content,
            'MARKER_PROCESSING_PAYMENT' in automation_content,
            'time.sleep' in automation_content or 'page.wait_for' in automation_content
        ]
        
        if sum(async_indicators) >= 2:
            checks.append({
                'name': 'async_handling',
                'passed': True,
                'detail': 'Proper handling of async operations and loading states'
            })
            total_score += 15
        else:
            checks.append({
                'name': 'async_handling',
                'passed': False,
                'detail': 'Missing proper async/loading state handling'
            })
    else:
        checks.append({
            'name': 'async_handling',
            'passed': False,
            'detail': 'No automation script to evaluate async handling'
        })
    
    passed = total_score >= 60  # Pass threshold: 60% of total points
    score = total_score / max_score
    
    return {
        'passed': passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python eval_script.py <workspace_directory>')
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = check_task_completion(workspace_dir)
    print(json.dumps(result, indent=2))