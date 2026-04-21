#!/usr/bin/env python3
import json
import os
import sys

def evaluate(workspace_dir):
    checks = []
    
    # Check 1: theme-showcase.pdf exists and contains theme names
    check1_passed = False
    check1_detail = ""
    try:
        showcase_path = os.path.join(workspace_dir, 'theme-showcase.pdf')
        if os.path.exists(showcase_path):
            with open(showcase_path, 'r') as f:
                content = f.read().lower()
                if 'ocean depths' in content and 'sunset boulevard' in content:
                    check1_passed = True
                    check1_detail = "Theme showcase file exists and contains theme information"
                else:
                    check1_detail = "Theme showcase file missing required theme names"
        else:
            check1_detail = "theme-showcase.pdf not found"
    except Exception as e:
        check1_detail = f"Error reading theme showcase: {str(e)}"
    
    checks.append({"name": "Theme showcase displayed", "passed": check1_passed, "detail": check1_detail})
    
    # Check 2: presentation_themed.md exists
    check2_passed = False
    check2_detail = ""
    try:
        themed_path = os.path.join(workspace_dir, 'presentation_themed.md')
        if os.path.exists(themed_path):
            with open(themed_path, 'r') as f:
                content = f.read()
                if len(content) > 0:
                    check2_passed = True
                    check2_detail = "Themed presentation file created"
                else:
                    check2_detail = "Themed presentation file is empty"
        else:
            check2_detail = "presentation_themed.md not found"
    except Exception as e:
        check2_detail = f"Error reading themed presentation: {str(e)}"
    
    checks.append({"name": "Themed presentation created", "passed": check2_passed, "detail": check2_detail})
    
    # Check 3: Ocean Depths theme applied (colors present in output)
    check3_passed = False
    check3_detail = ""
    try:
        themed_path = os.path.join(workspace_dir, 'presentation_themed.md')
        if os.path.exists(themed_path):
            with open(themed_path, 'r') as f:
                content = f.read().lower()
                ocean_colors = ['#1a5f7a', '#2e8b9e', '#87ceeb']
                if any(color.lower() in content for color in ocean_colors):
                    check3_passed = True
                    check3_detail = "Ocean Depths theme colors applied"
                else:
                    check3_detail = "Ocean Depths theme colors not found in output"
        else:
            check3_detail = "presentation_themed.md not found"
    except Exception as e:
        check3_detail = f"Error checking theme application: {str(e)}"
    
    checks.append({"name": "Ocean Depths theme applied", "passed": check3_passed, "detail": check3_detail})
    
    # Check 4: Custom theme file created
    check4_passed = False
    check4_detail = ""
    try:
        custom_theme_path = os.path.join(workspace_dir, 'themes', 'corporate_steel.json')
        if os.path.exists(custom_theme_path):
            with open(custom_theme_path, 'r') as f:
                theme_data = json.load(f)
                check4_passed = True
                check4_detail = "Custom theme file created"
        else:
            check4_detail = "themes/corporate_steel.json not found"
    except Exception as e:
        check4_detail = f"Error reading custom theme: {str(e)}"
    
    checks.append({"name": "Custom theme file created", "passed": check4_passed, "detail": check4_detail})
    
    # Check 5: Custom theme has correct colors
    check5_passed = False
    check5_detail = ""
    try:
        custom_theme_path = os.path.join(workspace_dir, 'themes', 'corporate_steel.json')
        if os.path.exists(custom_theme_path):
            with open(custom_theme_path, 'r') as f:
                theme_data = json.load(f)
                colors = theme_data.get('colors', {})
                required_colors = {
                    'primary': '#2C3E50',
                    'secondary': '#34495E',
                    'accent': '#3498DB',
                    'text': '#2C3E50',
                    'background': '#ECF0F1'
                }
                all_match = all(
                    colors.get(key, '').upper() == value.upper()
                    for key, value in required_colors.items()
                )
                if all_match:
                    check5_passed = True
                    check5_detail = "Custom theme colors match specification"
                else:
                    check5_detail = f"Custom theme colors mismatch. Got: {colors}"
        else:
            check5_detail = "Custom theme file not found"
    except Exception as e:
        check5_detail = f"Error validating custom theme colors: {str(e)}"
    
    checks.append({"name": "Custom theme colors correct", "passed": check5_passed, "detail": check5_detail})
    
    # Check 6: Custom theme has correct fonts
    check6_passed = False
    check6_detail = ""
    try:
        custom_theme_path = os.path.join(workspace_dir, 'themes', 'corporate_steel.json')
        if os.path.exists(custom_theme_path):
            with open(custom_theme_path, 'r') as f:
                theme_data = json.load(f)
                fonts = theme_data.get('fonts', {})
                if fonts.get('headers', '').lower() == 'segoe ui' and fonts.get('body', '').lower() == 'calibri':
                    check6_passed = True
                    check6_detail = "Custom theme fonts match specification"
                else:
                    check6_detail = f"Custom theme fonts mismatch. Got: {fonts}"
        else:
            check6_detail = "Custom theme file not found"
    except Exception as e:
        check6_detail = f"Error validating custom theme fonts: {str(e)}"
    
    checks.append({"name": "Custom theme fonts correct", "passed": check6_passed, "detail": check6_detail})
    
    # Check 7: Custom theme has name and description
    check7_passed = False
    check7_detail = ""
    try:
        custom_theme_path = os.path.join(workspace_dir, 'themes', 'corporate_steel.json')
        if os.path.exists(custom_theme_path):
            with open(custom_theme_path, 'r') as f:
                theme_data = json.load(f)
                name = theme_data.get('name', '').lower()
                if 'corporate' in name and 'steel' in name:
                    check7_passed = True
                    check7_detail = "Custom theme has correct name"
                else:
                    check7_detail = f"Custom theme name incorrect: {theme_data.get('name', 'N/A')}"
        else:
            check7_detail = "Custom theme file not found"
    except Exception as e:
        check7_detail = f"Error validating custom theme name: {str(e)}"
    
    checks.append({"name": "Custom theme metadata correct", "passed": check7_passed, "detail": check7_detail})
    
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks)
    overall_passed = score >= 0.8
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '/workspace'
    result = evaluate(workspace)
    print(json.dumps(result))
