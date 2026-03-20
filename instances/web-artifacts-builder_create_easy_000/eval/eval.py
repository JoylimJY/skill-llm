#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Expected workspace directory argument"}]}))
        return
    
    workspace_dir = Path(sys.argv[1])
    checks = []
    total_points = 0
    earned_points = 0
    
    # Check 1: bundle.html exists
    total_points += 3
    bundle_path = workspace_dir / "bundle.html"
    if bundle_path.exists():
        checks.append({"name": "bundle_exists", "passed": True, "detail": "bundle.html file was created"})
        earned_points += 3
    else:
        checks.append({"name": "bundle_exists", "passed": False, "detail": "bundle.html file not found"})
    
    # Check 2: bundle.html contains marker comment
    total_points += 2
    if bundle_path.exists():
        try:
            content = bundle_path.read_text()
            if "TASK_MANAGER_BUNDLED" in content:
                checks.append({"name": "bundle_marker", "passed": True, "detail": "Bundle marker found in HTML"})
                earned_points += 2
            else:
                checks.append({"name": "bundle_marker", "passed": False, "detail": "Bundle marker not found - script may not have completed"})
        except Exception as e:
            checks.append({"name": "bundle_marker", "passed": False, "detail": f"Error reading bundle.html: {e}"})
    else:
        checks.append({"name": "bundle_marker", "passed": False, "detail": "Cannot check marker - bundle.html missing"})
    
    # Check 3: HTML contains React and task manager elements
    total_points += 3
    if bundle_path.exists():
        try:
            content = bundle_path.read_text()
            react_indicators = ["react", "React", "useState", "jsx"]
            task_indicators = ["task", "Task", "todo", "Todo"]
            
            has_react = any(indicator in content for indicator in react_indicators)
            has_task_content = any(indicator in content for indicator in task_indicators)
            
            if has_react and has_task_content:
                checks.append({"name": "app_content", "passed": True, "detail": "Bundle contains React task manager content"})
                earned_points += 3
            elif has_react:
                checks.append({"name": "app_content", "passed": False, "detail": "Bundle contains React but missing task manager content"})
                earned_points += 1
            else:
                checks.append({"name": "app_content", "passed": False, "detail": "Bundle missing React and task manager content"})
        except Exception as e:
            checks.append({"name": "app_content", "passed": False, "detail": f"Error analyzing bundle content: {e}"})
    else:
        checks.append({"name": "app_content", "passed": False, "detail": "Cannot check content - bundle.html missing"})
    
    # Check 4: HTML contains shadcn/ui CSS variables
    total_points += 2
    if bundle_path.exists():
        try:
            content = bundle_path.read_text()
            css_indicators = ["--background", "--foreground", "--primary", "--border"]
            
            has_shadcn_css = any(indicator in content for indicator in css_indicators)
            
            if has_shadcn_css:
                checks.append({"name": "shadcn_styling", "passed": True, "detail": "Bundle contains shadcn/ui CSS variables"})
                earned_points += 2
            else:
                checks.append({"name": "shadcn_styling", "passed": False, "detail": "Bundle missing shadcn/ui CSS variables"})
        except Exception as e:
            checks.append({"name": "shadcn_styling", "passed": False, "detail": f"Error checking CSS content: {e}"})
    else:
        checks.append({"name": "shadcn_styling", "passed": False, "detail": "Cannot check styling - bundle.html missing"})
    
    score = earned_points / total_points if total_points > 0 else 0.0
    passed = score >= 0.7
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()