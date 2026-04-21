import sys
import os
import re
import json

def evaluate_outline(workspace_dir):
    checks = []
    
    # Check 1: File exists and is named correctly
    outline_file = os.path.join(workspace_dir, 'blog_outline.md')
    file_exists = os.path.exists(outline_file)
    checks.append({
        'name': 'Outline file exists with correct name',
        'passed': file_exists,
        'detail': 'Found blog_outline.md' if file_exists else 'blog_outline.md not found'
    })
    
    if not file_exists:
        # If file doesn't exist, add failing checks for remaining criteria
        checks.extend([
            {'name': 'Contains introduction with hook', 'passed': False, 'detail': 'File not found'},
            {'name': 'Has 3-4 main sections', 'passed': False, 'detail': 'File not found'},
            {'name': 'Includes conclusion with call to action', 'passed': False, 'detail': 'File not found'},
            {'name': 'Uses proper markdown formatting', 'passed': False, 'detail': 'File not found'}
        ])
        score = 0.0
        return {'passed': False, 'score': score, 'checks': checks}
    
    # Read the outline content
    with open(outline_file, 'r', encoding='utf-8') as f:
        content = f.read().lower()
    
    # Check 2: Contains introduction with hook
    intro_keywords = ['introduction', 'intro', 'hook']
    has_intro = any(keyword in content for keyword in intro_keywords)
    checks.append({
        'name': 'Contains introduction with hook',
        'passed': has_intro,
        'detail': 'Found introduction section' if has_intro else 'No clear introduction section found'
    })
    
    # Check 3: Has 3-4 main sections (count headings that look like main sections)
    heading_pattern = r'^#+\s+(?!introduction|intro|conclusion).*remote.*work|^#+\s+(?!introduction|intro|conclusion).*benefit|^#+\s+(?!introduction|intro|conclusion).*advantage|^#+\s+(?!introduction|intro|conclusion).*productivity|^#+\s+(?!introduction|intro|conclusion).*balance|^#+\s+(?!introduction|intro|conclusion).*career|^#+\s+(?!introduction|intro|conclusion).*cost|^#+\s+(?!introduction|intro|conclusion).*flexibility'
    main_sections = re.findall(heading_pattern, content, re.MULTILINE | re.IGNORECASE)
    
    # Alternative approach: count ## level headings that aren't intro/conclusion
    all_headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
    main_headings = [h for h in all_headings if not any(word in h.lower() for word in ['introduction', 'intro', 'conclusion', 'summary'])]
    
    section_count = max(len(main_sections), len(main_headings))
    has_main_sections = 3 <= section_count <= 6  # Allow some flexibility
    checks.append({
        'name': 'Has 3-4 main sections',
        'passed': has_main_sections,
        'detail': f'Found {section_count} main sections' if has_main_sections else f'Found {section_count} main sections, expected 3-4'
    })
    
    # Check 4: Includes conclusion with call to action
    conclusion_keywords = ['conclusion', 'summary', 'call to action', 'action', 'next steps']
    has_conclusion = any(keyword in content for keyword in conclusion_keywords)
    checks.append({
        'name': 'Includes conclusion with call to action',
        'passed': has_conclusion,
        'detail': 'Found conclusion section' if has_conclusion else 'No conclusion section found'
    })
    
    # Check 5: Uses proper markdown formatting (has headings)
    has_headings = bool(re.search(r'^#+\s+', content, re.MULTILINE))
    checks.append({
        'name': 'Uses proper markdown formatting',
        'passed': has_headings,
        'detail': 'Contains markdown headings' if has_headings else 'No markdown headings found'
    })
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    score = passed_count / len(checks)
    overall_passed = score >= 0.8
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace_dir = sys.argv[1]
    result = evaluate_outline(workspace_dir)
    print(json.dumps(result))