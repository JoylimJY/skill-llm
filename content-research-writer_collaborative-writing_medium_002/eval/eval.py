import os
import sys
import re
import json
from pathlib import Path

def main(workspace_dir):
    workspace_path = Path(workspace_dir)
    checks = []
    
    # Check 1: Asks clarifying questions at the start
    draft_files = list(workspace_path.glob('*.md'))
    found_questions = False
    questions_content = ''
    
    for file_path in draft_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                if any(keyword in content for keyword in ['what', 'who', 'how', 'which', 'clarif', 'question', 'angle', 'specific']):
                    found_questions = True
                    questions_content = content
                    break
        except:
            continue
    
    checks.append({
        'name': 'Asks clarifying questions',
        'passed': found_questions,
        'detail': 'Found clarifying questions' if found_questions else 'No clarifying questions found'
    })
    
    # Check 2: Creates a detailed outline
    found_outline = False
    outline_content = ''
    
    for file_path in draft_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if re.search(r'#.*outline', content, re.IGNORECASE) or \
                   (content.count('#') >= 3 and any(word in content.lower() for word in ['introduction', 'conclusion', 'section'])):
                    found_outline = True
                    outline_content = content
                    break
        except:
            continue
    
    checks.append({
        'name': 'Creates detailed outline',
        'passed': found_outline,
        'detail': 'Found structured outline' if found_outline else 'No clear outline structure found'
    })
    
    # Check 3: Includes research with statistics
    found_research = False
    research_content = ''
    
    for file_path in draft_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if re.search(r'\d+%', content) or \
                   any(word in content.lower() for word in ['study', 'survey', 'research', 'data', 'statistics']):
                    found_research = True
                    research_content = content
                    break
        except:
            continue
    
    checks.append({
        'name': 'Conducts research with statistics',
        'passed': found_research,
        'detail': 'Found research data and statistics' if found_research else 'No research statistics found'
    })
    
    # Check 4: Provides numbered citations
    found_citations = False
    citation_content = ''
    
    for file_path in draft_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if re.search(r'\[\d+\]', content) or \
                   re.search(r'citation|reference|source', content, re.IGNORECASE):
                    found_citations = True
                    citation_content = content
                    break
        except:
            continue
    
    checks.append({
        'name': 'Adds numbered citations',
        'passed': found_citations,
        'detail': 'Found numbered citations format' if found_citations else 'No numbered citations found'
    })
    
    # Check 5: Improves the hook/introduction
    found_hook_improvement = False
    hook_content = ''
    
    for file_path in draft_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                # Look for improved hooks - more engaging than generic statements
                if any(pattern in content for pattern in ['hook', 'compelling', 'attention', 'engaging']) or \
                   (content.count('?') > 0 and any(word in content for word in ['imagine', 'what if', 'picture'])):
                    found_hook_improvement = True
                    hook_content = content
                    break
        except:
            continue
    
    checks.append({
        'name': 'Improves introduction hook',
        'passed': found_hook_improvement,
        'detail': 'Found hook improvement suggestions' if found_hook_improvement else 'No hook improvement found'
    })
    
    # Check 6: Saves as blog-post-draft.md
    target_file = workspace_path / 'blog-post-draft.md'
    file_saved_correctly = target_file.exists()
    
    checks.append({
        'name': 'Saves as blog-post-draft.md',
        'passed': file_saved_correctly,
        'detail': 'File saved with correct name' if file_saved_correctly else 'blog-post-draft.md not found'
    })
    
    # Check 7: Focuses on team managers audience
    found_manager_focus = False
    manager_content = ''
    
    for file_path in draft_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                if any(word in content for word in ['manager', 'team lead', 'supervisor', 'leadership', 'manage team']):
                    found_manager_focus = True
                    manager_content = content
                    break
        except:
            continue
    
    checks.append({
        'name': 'Targets team managers audience',
        'passed': found_manager_focus,
        'detail': 'Found content targeted at managers' if found_manager_focus else 'No clear manager focus found'
    })
    
    # Check 8: Provides actionable insights
    found_actionable = False
    actionable_content = ''
    
    for file_path in draft_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
                if any(word in content for word in ['action', 'implement', 'steps', 'how to', 'tip', 'strategy', 'best practice']):
                    found_actionable = True
                    actionable_content = content
                    break
        except:
            continue
    
    checks.append({
        'name': 'Provides actionable insights',
        'passed': found_actionable,
        'detail': 'Found actionable content and strategies' if found_actionable else 'No clear actionable insights found'
    })
    
    # Calculate score
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8  # Allow some flexibility for collaborative writing task
    
    result = {
        'passed': passed,
        'score': score,
        'checks': checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main(sys.argv[1])