import sys
import os
import re
import json
from pathlib import Path

def check_philosophy_file(workspace_path):
    """Check if philosophy markdown file exists and contains required elements"""
    philosophy_files = list(Path(workspace_path).glob('*philosophy*.md'))
    
    if not philosophy_files:
        return False, "No philosophy markdown file found"
    
    # Check the most likely candidate
    for philosophy_file in philosophy_files:
        try:
            content = philosophy_file.read_text(encoding='utf-8').lower()
            
            # Check for philosophy structure
            has_movement_name = any(keyword in content for keyword in ['digital archaeology', 'movement', 'philosophy', 'aesthetic'])
            has_visual_elements = any(keyword in content for keyword in ['visual', 'space', 'form', 'color', 'composition'])
            has_craftsmanship = any(keyword in content for keyword in ['craft', 'expertise', 'master', 'meticulous', 'painstaking'])
            
            if has_movement_name and has_visual_elements and has_craftsmanship:
                return True, f"Philosophy file found with proper structure: {philosophy_file.name}"
        except:
            continue
    
    return False, "Philosophy file exists but lacks required elements"

def check_artwork_file(workspace_path):
    """Check if PDF artwork file exists"""
    pdf_files = list(Path(workspace_path).glob('*.pdf'))
    
    if not pdf_files:
        return False, "No PDF artwork file found"
    
    # Look for files with 'artwork' or 'digital_archaeology' in name
    for pdf_file in pdf_files:
        if any(keyword in pdf_file.name.lower() for keyword in ['artwork', 'digital', 'archaeology']):
            # Basic file size check (should be substantial for a designed piece)
            if pdf_file.stat().st_size > 5000:  # At least 5KB
                return True, f"Artwork PDF found: {pdf_file.name}"
    
    # Check any PDF file as fallback
    for pdf_file in pdf_files:
        if pdf_file.stat().st_size > 5000:
            return True, f"PDF artwork file found: {pdf_file.name}"
    
    return False, "PDF file exists but appears too small or incomplete"

def check_digital_archaeology_theme(workspace_path):
    """Check if the theme of digital archaeology is present"""
    all_files = list(Path(workspace_path).glob('*'))
    combined_content = ""
    
    for file_path in all_files:
        if file_path.is_file() and file_path.suffix in ['.md', '.txt']:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                combined_content += content.lower() + " "
            except:
                continue
    
    # Check for digital archaeology related concepts
    digital_terms = any(term in combined_content for term in ['digital', 'data', 'binary', 'file', 'format', 'system'])
    archaeology_terms = any(term in combined_content for term in ['archaeology', 'excavation', 'artifact', 'preservation', 'documentation'])
    
    if digital_terms and archaeology_terms:
        return True, "Digital archaeology theme clearly present"
    elif digital_terms or archaeology_terms:
        return True, "Theme partially present with relevant concepts"
    else:
        return False, "Digital archaeology theme not clearly expressed"

def check_sophisticated_execution(workspace_path):
    """Check for indicators of sophisticated, museum-quality execution"""
    all_files = list(Path(workspace_path).glob('*'))
    
    # Check for multiple output files (shows thoroughness)
    has_multiple_outputs = len([f for f in all_files if f.suffix in ['.pdf', '.png', '.md']]) >= 2
    
    # Check file sizes suggest substantial content
    substantial_files = sum(1 for f in all_files if f.is_file() and f.stat().st_size > 1000)
    
    # Check for sophisticated language in text files
    sophistication_indicators = False
    for file_path in all_files:
        if file_path.is_file() and file_path.suffix in ['.md', '.txt']:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore').lower()
                if any(term in content for term in ['sophisticated', 'museum', 'masterpiece', 'systematic', 'methodology', 'precision']):
                    sophistication_indicators = True
                    break
            except:
                continue
    
    if has_multiple_outputs and substantial_files >= 2 and sophistication_indicators:
        return True, "Evidence of sophisticated, museum-quality execution"
    elif has_multiple_outputs and substantial_files >= 1:
        return True, "Good execution with proper file structure"
    else:
        return False, "Execution appears rushed or incomplete"

def main(workspace_path):
    checks = []
    
    # Check 1: Philosophy file exists and is well-structured
    philosophy_passed, philosophy_detail = check_philosophy_file(workspace_path)
    checks.append({
        "name": "Philosophy Document",
        "passed": philosophy_passed,
        "detail": philosophy_detail
    })
    
    # Check 2: Artwork PDF file exists
    artwork_passed, artwork_detail = check_artwork_file(workspace_path)
    checks.append({
        "name": "Artwork File",
        "passed": artwork_passed,
        "detail": artwork_detail
    })
    
    # Check 3: Digital archaeology theme is present
    theme_passed, theme_detail = check_digital_archaeology_theme(workspace_path)
    checks.append({
        "name": "Digital Archaeology Theme",
        "passed": theme_passed,
        "detail": theme_detail
    })
    
    # Check 4: Sophisticated execution
    execution_passed, execution_detail = check_sophisticated_execution(workspace_path)
    checks.append({
        "name": "Sophisticated Execution",
        "passed": execution_passed,
        "detail": execution_detail
    })
    
    # Calculate score
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.75  # Allow for some flexibility given the creative nature
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Setup", "passed": False, "detail": "Invalid arguments"}]}))
        sys.exit(1)
    
    main(sys.argv[1])