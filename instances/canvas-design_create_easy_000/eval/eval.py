#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path

def main(workspace_dir):
    checks = []
    passed = True
    score = 0.0
    
    workspace = Path(workspace_dir)
    
    # Check for design philosophy markdown file
    md_files = list(workspace.glob('*.md'))
    if md_files:
        checks.append({"name": "Design philosophy file created", "passed": True, "detail": f"Found {len(md_files)} .md file(s)"})
        score += 0.3
        
        # Check content of markdown file
        md_content = md_files[0].read_text()
        if len(md_content) > 500 and 'philosophy' in md_content.lower():
            checks.append({"name": "Philosophy content substantial", "passed": True, "detail": f"Content length: {len(md_content)} characters"})
            score += 0.2
        else:
            checks.append({"name": "Philosophy content substantial", "passed": False, "detail": "Content too brief or missing philosophy elements"})
            passed = False
    else:
        checks.append({"name": "Design philosophy file created", "passed": False, "detail": "No .md files found"})
        passed = False
    
    # Check for visual output (PDF or PNG)
    pdf_files = list(workspace.glob('*.pdf'))
    png_files = list(workspace.glob('*.png'))
    
    if pdf_files or png_files:
        visual_files = pdf_files + png_files
        checks.append({"name": "Visual output created", "passed": True, "detail": f"Found {len(visual_files)} visual file(s)"})
        score += 0.3
        
        # Check file size (should be substantial for a proper design)
        largest_file = max(visual_files, key=lambda f: f.stat().st_size)
        file_size = largest_file.stat().st_size
        if file_size > 10000:  # At least 10KB
            checks.append({"name": "Visual file substantial", "passed": True, "detail": f"Largest file: {file_size} bytes"})
            score += 0.2
        else:
            checks.append({"name": "Visual file substantial", "passed": False, "detail": f"File too small: {file_size} bytes"})
            passed = False
    else:
        checks.append({"name": "Visual output created", "passed": False, "detail": "No .pdf or .png files found"})
        checks.append({"name": "Visual file substantial", "passed": False, "detail": "No visual files to check"})
        passed = False
    
    # Bonus check: both philosophy and visual created
    if md_files and (pdf_files or png_files):
        checks.append({"name": "Complete workflow executed", "passed": True, "detail": "Both design philosophy and visual output created"})
        score = min(1.0, score)
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_dir>')
        sys.exit(1)
    main(sys.argv[1])