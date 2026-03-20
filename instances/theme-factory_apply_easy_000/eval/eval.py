import sys
import os
import json
from pptx import Presentation

def check_task_completion(workspace_dir):
    checks = []
    passed_count = 0
    total_checks = 4
    
    # Check if original presentation exists
    pptx_path = os.path.join(workspace_dir, 'quarterly_sales.pptx')
    if os.path.exists(pptx_path):
        checks.append({
            "name": "Original presentation exists",
            "passed": True,
            "detail": "quarterly_sales.pptx found"
        })
        passed_count += 1
    else:
        checks.append({
            "name": "Original presentation exists",
            "passed": False,
            "detail": "quarterly_sales.pptx not found"
        })
    
    # Check if theme showcase was displayed (file exists)
    showcase_path = os.path.join(workspace_dir, 'theme-showcase.pdf')
    if os.path.exists(showcase_path):
        checks.append({
            "name": "Theme showcase available",
            "passed": True,
            "detail": "theme-showcase.pdf found"
        })
        passed_count += 1
    else:
        checks.append({
            "name": "Theme showcase available",
            "passed": False,
            "detail": "theme-showcase.pdf not found"
        })
    
    # Check if themes directory exists with theme files
    themes_dir = os.path.join(workspace_dir, 'themes')
    if os.path.exists(themes_dir) and os.path.isdir(themes_dir):
        theme_files = [f for f in os.listdir(themes_dir) if f.endswith('.txt')]
        if len(theme_files) >= 2:
            checks.append({
                "name": "Theme files available",
                "passed": True,
                "detail": f"Found {len(theme_files)} theme files"
            })
            passed_count += 1
        else:
            checks.append({
                "name": "Theme files available",
                "passed": False,
                "detail": f"Only {len(theme_files)} theme files found"
            })
    else:
        checks.append({
            "name": "Theme files available",
            "passed": False,
            "detail": "themes directory not found"
        })
    
    # Check if presentation has been modified/styled (basic check)
    try:
        prs = Presentation(pptx_path)
        slide_count = len(prs.slides)
        if slide_count >= 3:
            checks.append({
                "name": "Presentation structure maintained",
                "passed": True,
                "detail": f"Found {slide_count} slides as expected"
            })
            passed_count += 1
        else:
            checks.append({
                "name": "Presentation structure maintained",
                "passed": False,
                "detail": f"Expected 3+ slides, found {slide_count}"
            })
    except Exception as e:
        checks.append({
            "name": "Presentation structure maintained",
            "passed": False,
            "detail": f"Error reading presentation: {str(e)}"
        })
    
    score = passed_count / total_checks
    overall_passed = score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: eval_script.py <workspace_dir>"}))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = check_task_completion(workspace_dir)
    print(json.dumps(result, indent=2))