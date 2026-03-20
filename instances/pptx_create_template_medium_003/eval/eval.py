#!/usr/bin/env python3
import sys
import os
import json
import subprocess
from pathlib import Path

def main(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    
    # Check if output PPTX exists
    pptx_files = list(workspace.glob('*.pptx'))
    if not pptx_files:
        checks.append({"name": "output_exists", "passed": False, "detail": "No .pptx file found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    pptx_file = pptx_files[0]
    checks.append({"name": "output_exists", "passed": True, "detail": f"Found {pptx_file.name}"})
    
    try:
        # Extract text content
        result = subprocess.run(['python3', '-m', 'markitdown', str(pptx_file)], 
                              capture_output=True, text=True, check=True)
        content = result.stdout.lower()
        
        # Check for required content
        required_terms = [
            'paystream',
            'fintech', 
            'payment processing',
            'small business',
            '300%',
            '2.1b',
            'market',
            'competitive',
            'funding'
        ]
        
        content_score = 0
        for term in required_terms:
            if term in content:
                content_score += 1
                checks.append({"name": f"content_{term}", "passed": True, "detail": f"Found '{term}' in content"})
            else:
                checks.append({"name": f"content_{term}", "passed": False, "detail": f"Missing '{term}' in content"})
        
        # Count slides by counting slide separators
        slide_count = content.count('---') + 1 if '---' in content else len([line for line in content.split('\n') if line.strip() and not line.startswith(' ')][:15])
        
        slide_check = 8 <= slide_count <= 12
        checks.append({"name": "slide_count", "passed": slide_check, "detail": f"Found {slide_count} slides (target: 8-10)"})
        
        # Check file size (should be substantial for a well-designed presentation)
        file_size = pptx_file.stat().st_size
        size_check = file_size > 50000  # At least 50KB indicates substantial content
        checks.append({"name": "file_size", "passed": size_check, "detail": f"File size: {file_size} bytes"})
        
        # Calculate final score
        passed_checks = sum(1 for check in checks if check['passed'])
        total_checks = len(checks)
        score = passed_checks / total_checks
        
        # Must have core elements to pass
        core_passed = (
            any('paystream' in content for _ in [1]) and
            any('payment' in content for _ in [1]) and
            slide_count >= 8 and
            size_check
        )
        
        return {
            "passed": core_passed and score >= 0.7,
            "score": score,
            "checks": checks
        }
        
    except subprocess.CalledProcessError as e:
        checks.append({"name": "content_extraction", "passed": False, "detail": f"Failed to extract content: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    except Exception as e:
        checks.append({"name": "evaluation_error", "passed": False, "detail": f"Error during evaluation: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

if __name__ == '__main__':
    result = main(sys.argv[1])
    print(json.dumps(result))