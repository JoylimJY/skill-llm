#!/usr/bin/env python3
import sys
import os
import subprocess
import json
from pathlib import Path

def check_presentation(workspace_dir):
    checks = []
    score = 0.0
    
    # Check if output file exists
    pptx_path = Path(workspace_dir) / 'coffee_presentation.pptx'
    if not pptx_path.exists():
        checks.append({"name": "file_exists", "passed": False, "detail": "coffee_presentation.pptx not found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "file_exists", "passed": True, "detail": "Output file created successfully"})
    score += 0.2
    
    try:
        # Extract text content using markitdown
        result = subprocess.run(['python3', '-m', 'markitdown', str(pptx_path)], 
                              capture_output=True, text=True, cwd=workspace_dir)
        
        if result.returncode != 0:
            checks.append({"name": "file_readable", "passed": False, "detail": "Could not read presentation file"})
            return {"passed": False, "score": score, "checks": checks}
        
        content = result.stdout.lower()
        checks.append({"name": "file_readable", "passed": True, "detail": "Presentation file is valid and readable"})
        score += 0.2
        
        # Check for coffee-related content
        coffee_terms = ['coffee', 'brewing', 'french press', 'pour over', 'espresso']
        found_terms = [term for term in coffee_terms if term in content]
        
        if len(found_terms) >= 4:
            checks.append({"name": "coffee_content", "passed": True, "detail": f"Found coffee brewing terms: {', '.join(found_terms)}"})
            score += 0.2
        else:
            checks.append({"name": "coffee_content", "passed": False, "detail": f"Only found {len(found_terms)} coffee terms: {', '.join(found_terms)}"})
        
        # Check slide count by counting slide markers
        slide_count = content.count('slide ')
        if slide_count == 0:
            # Alternative: count common slide patterns
            patterns = ['# ', '## ', 'title', 'conclusion', 'overview']
            slide_indicators = sum(1 for pattern in patterns if pattern in content)
            if slide_indicators >= 4:
                slide_count = 4
        
        if slide_count >= 4:
            checks.append({"name": "slide_count", "passed": True, "detail": f"Presentation has sufficient slides (detected {slide_count})"})
            score += 0.2
        else:
            checks.append({"name": "slide_count", "passed": False, "detail": f"Expected 4+ slides, detected {slide_count}"})
        
        # Check for method-specific content
        methods = ['french press', 'pour over', 'espresso']
        methods_found = [method for method in methods if method in content]
        
        if len(methods_found) >= 3:
            checks.append({"name": "brewing_methods", "passed": True, "detail": f"All brewing methods covered: {', '.join(methods_found)}"})
            score += 0.2
        else:
            checks.append({"name": "brewing_methods", "passed": False, "detail": f"Missing methods. Found: {', '.join(methods_found)}"})
        
    except Exception as e:
        checks.append({"name": "content_analysis", "passed": False, "detail": f"Error analyzing content: {str(e)}"})
        return {"passed": False, "score": score, "checks": checks}
    
    passed = score >= 0.8
    return {"passed": passed, "score": score, "checks": checks}

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = check_presentation(sys.argv[1])
    print(json.dumps(result))
