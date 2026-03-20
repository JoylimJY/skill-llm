#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Missing workspace directory argument"}]}))
        return
    
    workspace = Path(sys.argv[1])
    checks = []
    
    # Load validation markers
    try:
        with open(workspace / 'validation_markers.json') as f:
            markers = json.load(f)['expected_markers']
    except:
        checks.append({"name": "markers_load", "passed": False, "detail": "Could not load validation markers"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    # Check if bundle.html exists
    bundle_path = workspace / 'bundle.html'
    if bundle_path.exists():
        checks.append({"name": "bundle_exists", "passed": True, "detail": "bundle.html file created"})
        
        try:
            with open(bundle_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check file size (should be substantial for a complex app)
            file_size = len(content)
            if file_size > 50000:  # At least 50KB for a complex dashboard
                checks.append({"name": "bundle_size", "passed": True, "detail": f"Bundle size adequate: {file_size} bytes"})
            else:
                checks.append({"name": "bundle_size", "passed": False, "detail": f"Bundle too small: {file_size} bytes"})
            
            # Check for React and modern web technologies
            react_found = 'react' in content.lower() or 'usestate' in content.lower() or 'useeffect' in content.lower()
            checks.append({"name": "react_usage", "passed": react_found, "detail": "React components detected" if react_found else "No React usage found"})
            
            # Check for Tailwind CSS classes
            tailwind_patterns = ['class="', 'className="', 'bg-', 'text-', 'flex', 'grid']
            tailwind_found = any(pattern in content for pattern in tailwind_patterns)
            checks.append({"name": "tailwind_styling", "passed": tailwind_found, "detail": "Tailwind CSS classes found" if tailwind_found else "No Tailwind CSS styling detected"})
            
            # Check for shadcn/ui components
            shadcn_patterns = ['ui/button', 'ui/card', 'ui/dialog', 'radix', 'lucide']
            shadcn_found = any(pattern in content for pattern in shadcn_patterns)
            checks.append({"name": "shadcn_components", "passed": shadcn_found, "detail": "shadcn/ui components detected" if shadcn_found else "No shadcn/ui components found"})
            
            # Check for required features
            features_checks = [
                ('kanban_board', ['kanban', 'drag', 'drop', 'column'], "Kanban board functionality"),
                ('team_management', ['team', 'member', 'avatar'], "Team member management"),
                ('calendar_planning', ['calendar', 'date', 'sprint'], "Calendar/sprint planning"),
                ('analytics_charts', ['chart', 'analytic', 'velocity', 'burndown'], "Analytics charts"),
                ('theme_toggle', ['theme', 'dark', 'light'], "Theme toggle functionality")
            ]
            
            for check_name, keywords, description in features_checks:
                found = any(keyword in content.lower() for keyword in keywords)
                checks.append({"name": check_name, "passed": found, "detail": f"{description} {'found' if found else 'missing'}"})
            
            # Check for validation markers in content
            markers_found = 0
            for marker in markers:
                if marker in content:
                    markers_found += 1
            
            markers_check = markers_found >= 3  # At least 3 out of 5 markers
            checks.append({"name": "validation_markers", "passed": markers_check, "detail": f"Found {markers_found}/{len(markers)} validation markers"})
            
            # Check against AI slop patterns (should avoid these)
            ai_slop_patterns = ['text-center', 'justify-center', 'items-center', 'purple-', 'gradient']
            excessive_centering = sum(content.count(pattern) for pattern in ai_slop_patterns[:3]) > 20
            purple_gradients = any(pattern in content for pattern in ai_slop_patterns[3:])
            
            avoids_ai_slop = not (excessive_centering or purple_gradients)
            checks.append({"name": "avoids_ai_slop", "passed": avoids_ai_slop, "detail": "Good design practices" if avoids_ai_slop else "Contains typical AI-generated patterns"})
            
            # Check for responsive design
            responsive_patterns = ['sm:', 'md:', 'lg:', 'xl:', '@media', 'responsive']
            responsive_found = any(pattern in content for pattern in responsive_patterns)
            checks.append({"name": "responsive_design", "passed": responsive_found, "detail": "Responsive design detected" if responsive_found else "No responsive design patterns found"})
            
        except Exception as e:
            checks.append({"name": "bundle_analysis", "passed": False, "detail": f"Error analyzing bundle: {str(e)}"})
    
    else:
        checks.append({"name": "bundle_exists", "passed": False, "detail": "bundle.html file not found"})
    
    # Check if project structure was created
    project_dirs = ['DevTracker Pro', 'devtracker-pro', 'project', 'dashboard']
    project_found = any((workspace / dirname).exists() for dirname in project_dirs)
    if project_found:
        checks.append({"name": "project_structure", "passed": True, "detail": "Project directory structure created"})
    else:
        checks.append({"name": "project_structure", "passed": False, "detail": "No project directory found"})
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Overall pass requires bundle.html + most features working
    overall_passed = (
        any(check['name'] == 'bundle_exists' and check['passed'] for check in checks) and
        score >= 0.7
    )
    
    result = {
        "passed": overall_passed,
        "score": round(score, 2),
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()