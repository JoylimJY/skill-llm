import sys
import os
import json
from pathlib import Path

def evaluate_canvas_design(workspace_dir):
    workspace_path = Path(workspace_dir)
    checks = []
    score = 0.0
    
    # Check if marker file exists (input validation)
    marker_file = workspace_path / 'task_markers.json'
    if not marker_file.exists():
        checks.append({"name": "marker_file", "passed": False, "detail": "Task marker file missing"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Load marker data
    with open(marker_file) as f:
        markers = json.load(f)
    
    # Check for design philosophy markdown file
    md_files = list(workspace_path.glob('*.md'))
    philosophy_found = len(md_files) > 0
    checks.append({"name": "design_philosophy", "passed": philosophy_found, 
                  "detail": f"Found {len(md_files)} .md files (design philosophy)"})
    if philosophy_found:
        score += 0.25
        
        # Check philosophy content quality
        for md_file in md_files:
            content = md_file.read_text().lower()
            philosophy_quality = (
                len(content.split()) > 200 and  # Substantial content
                any(word in content for word in ['visual', 'form', 'space', 'color', 'composition']) and
                any(word in content for word in ['craftsmanship', 'meticulously', 'expertise', 'master'])
            )
            if philosophy_quality:
                score += 0.15
                checks.append({"name": "philosophy_quality", "passed": True, 
                              "detail": "Philosophy contains required design and craftsmanship elements"})
                break
    
    # Check for visual output files (PDF or PNG)
    pdf_files = list(workspace_path.glob('*.pdf'))
    png_files = list(workspace_path.glob('*.png'))
    visual_files = pdf_files + png_files
    
    visual_output_found = len(visual_files) > 0
    checks.append({"name": "visual_output", "passed": visual_output_found,
                  "detail": f"Found {len(pdf_files)} PDF and {len(png_files)} PNG files"})
    
    if visual_output_found:
        score += 0.35
        
        # Check for multi-page requirement
        multi_page_satisfied = False
        total_pages = 0
        
        # Count PDF pages
        for pdf_file in pdf_files:
            try:
                import PyPDF2
                with open(pdf_file, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    total_pages += len(reader.pages)
            except:
                total_pages += 1  # Assume at least 1 page if can't read
        
        # Count PNG files as individual pages
        total_pages += len(png_files)
        
        multi_page_satisfied = total_pages > 1
        checks.append({"name": "multi_page_series", "passed": multi_page_satisfied,
                      "detail": f"Total pages/images: {total_pages} (requirement: >1)"})
        
        if multi_page_satisfied:
            score += 0.25
    
    # Check file sizes (indicator of substantial content)
    substantial_files = 0
    for vfile in visual_files:
        if vfile.stat().st_size > 10000:  # At least 10KB
            substantial_files += 1
    
    size_check = substantial_files > 0
    checks.append({"name": "substantial_content", "passed": size_check,
                  "detail": f"{substantial_files} files with substantial size (>10KB)"})
    
    if size_check:
        score += 0.1
    
    # Final score calculation
    passed = score >= 0.7  # Need at least 70% to pass
    
    return {
        "passed": passed,
        "score": min(1.0, score),
        "checks": checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Invalid arguments"}]}))
        sys.exit(1)
    
    result = evaluate_canvas_design(sys.argv[1])
    print(json.dumps(result, indent=2))