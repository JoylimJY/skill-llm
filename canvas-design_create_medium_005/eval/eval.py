import sys
import os
import json
from pathlib import Path

def check_philosophy_file(workspace_dir):
    """Check for design philosophy markdown file"""
    philosophy_files = list(Path(workspace_dir).glob('*philosophy*.md'))
    if not philosophy_files:
        return False, "No philosophy markdown file found"
    
    for file_path in philosophy_files:
        try:
            content = file_path.read_text().lower()
            # Check for key philosophy elements
            has_movement_name = any(keyword in content for keyword in ['movement', 'philosophy', 'aesthetic', 'visual'])
            has_visual_focus = any(keyword in content for keyword in ['color', 'form', 'space', 'composition', 'visual'])
            has_craftsmanship = any(keyword in content for keyword in ['craft', 'expert', 'master', 'meticulous', 'precision'])
            has_math_concepts = any(keyword in content for keyword in ['mathematical', 'geometry', 'proportion', 'pattern', 'ratio', 'symmetry', 'golden', 'fibonacci'])
            
            if has_movement_name and has_visual_focus and has_craftsmanship and len(content) > 500:
                return True, f"Found comprehensive design philosophy in {file_path.name}"
        except Exception as e:
            continue
    
    return False, "Philosophy file found but lacks required elements"

def check_poster_file(workspace_dir):
    """Check for poster PDF file"""
    pdf_files = list(Path(workspace_dir).glob('*.pdf'))
    if not pdf_files:
        return False, "No PDF poster file found"
    
    for file_path in pdf_files:
        # Check if file exists and has reasonable size (indicating content)
        if file_path.stat().st_size > 1000:  # At least 1KB
            return True, f"Found poster file: {file_path.name}"
    
    return False, "PDF file found but appears to be empty or corrupted"

def check_file_naming(workspace_dir):
    """Check if files follow requested naming convention"""
    has_philosophy = any(Path(workspace_dir).glob('*philosophy*.md'))
    has_poster = any(Path(workspace_dir).glob('*poster*.pdf')) or any(Path(workspace_dir).glob('*mathematical*.pdf')) or any(Path(workspace_dir).glob('*beauty*.pdf'))
    
    if has_philosophy and has_poster:
        return True, "Files follow appropriate naming conventions"
    elif has_philosophy:
        return True, "Philosophy file properly named, poster file present"
    else:
        return False, "Files do not follow requested naming conventions"

def check_mathematical_theme(workspace_dir):
    """Check if the philosophy addresses mathematical beauty theme"""
    philosophy_files = list(Path(workspace_dir).glob('*.md'))
    
    for file_path in philosophy_files:
        try:
            content = file_path.read_text().lower()
            math_indicators = ['mathematical', 'mathematics', 'geometric', 'geometry', 'proportion', 'ratio', 'symmetry', 'pattern', 'golden', 'fibonacci', 'formula', 'equation']
            
            math_count = sum(1 for indicator in math_indicators if indicator in content)
            if math_count >= 2:  # At least 2 mathematical concepts mentioned
                return True, f"Philosophy properly addresses mathematical beauty theme ({math_count} mathematical concepts found)"
        except Exception:
            continue
    
    return False, "Philosophy does not adequately address mathematical beauty theme"

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "argument_check", "passed": False, "detail": "Script requires workspace directory argument"}]}))
        return
    
    workspace_dir = sys.argv[1]
    
    checks = []
    
    # Check 1: Philosophy file exists and has content
    philosophy_passed, philosophy_detail = check_philosophy_file(workspace_dir)
    checks.append({"name": "philosophy_file", "passed": philosophy_passed, "detail": philosophy_detail})
    
    # Check 2: Poster PDF file exists
    poster_passed, poster_detail = check_poster_file(workspace_dir)
    checks.append({"name": "poster_file", "passed": poster_passed, "detail": poster_detail})
    
    # Check 3: File naming conventions
    naming_passed, naming_detail = check_file_naming(workspace_dir)
    checks.append({"name": "file_naming", "passed": naming_passed, "detail": naming_detail})
    
    # Check 4: Mathematical theme addressed
    theme_passed, theme_detail = check_mathematical_theme(workspace_dir)
    checks.append({"name": "mathematical_theme", "passed": theme_passed, "detail": theme_detail})
    
    # Calculate score
    score = sum(1 for check in checks if check['passed']) / len(checks)
    passed = score >= 0.75  # Pass if at least 3 out of 4 checks pass
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()

    