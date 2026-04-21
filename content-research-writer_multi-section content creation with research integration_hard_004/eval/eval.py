import os
import sys
import json
import re
from pathlib import Path

def evaluate_task(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)
    
    # Check 1: Final article file exists
    final_article_path = workspace / 'final_article.md'
    if final_article_path.exists():
        checks.append({'name': 'final_article_file_exists', 'passed': True, 'detail': 'final_article.md found'})
        final_content = final_article_path.read_text().lower()
    else:
        checks.append({'name': 'final_article_file_exists', 'passed': False, 'detail': 'final_article.md not found'})
        final_content = ''
    
    # If no final article, check for other markdown files
    if not final_content:
        md_files = list(workspace.glob('*.md'))
        for md_file in md_files:
            if 'article' in md_file.name.lower() or 'final' in md_file.name.lower():
                final_content = md_file.read_text().lower()
                break
    
    # Check 2: Article has compelling hook/introduction
    hook_patterns = [
        r'imagine\s+', r'what\s+if\s+', r'last\s+(week|month|year)\s+', 
        r'in\s+\d+\s+(seconds|minutes|hours)\s+', r'while\s+most\s+teams\s+',
        r'the\s+traditional\s+', r'\d+%\s+of\s+(teams|companies|workers)\s+'
    ]
    has_compelling_hook = any(re.search(pattern, final_content) for pattern in hook_patterns)
    if has_compelling_hook:
        checks.append({'name': 'compelling_hook', 'passed': True, 'detail': 'Article contains engaging opening'})
    else:
        checks.append({'name': 'compelling_hook', 'passed': False, 'detail': 'No compelling hook detected'})
    
    # Check 3: Word count in range (2000-2500)
    word_count = len(final_content.split())
    if 1800 <= word_count <= 2800:  # Allow some flexibility
        checks.append({'name': 'word_count', 'passed': True, 'detail': f'Word count: {word_count} (within range)'})
    else:
        checks.append({'name': 'word_count', 'passed': False, 'detail': f'Word count: {word_count} (outside target range)'})
    
    # Check 4: Clear section structure
    section_patterns = [
        r'##\s+[^#\n]+', r'###\s+[^#\n]+',  # Markdown headers
        r'\n[A-Z][^\n]*:\s*\n', r'\n\*\*[^*]+\*\*\s*\n'  # Alternative section markers
    ]
    section_count = sum(len(re.findall(pattern, final_content)) for pattern in section_patterns)
    if section_count >= 4:
        checks.append({'name': 'clear_sections', 'passed': True, 'detail': f'Found {section_count} sections/subsections'})
    else:
        checks.append({'name': 'clear_sections', 'passed': False, 'detail': f'Only {section_count} sections found, expected at least 4'})
    
    # Check 5: Citations present (numbered references)
    citation_patterns = [
        r'\[\d+\]',  # [1], [2], etc.
        r'\(\d+\)',   # (1), (2), etc.
        r'\^\d+',     # ^1, ^2, etc.
        r'\d+\.',     # 1. Author... reference format
    ]
    citation_matches = []
    for pattern in citation_patterns:
        citation_matches.extend(re.findall(pattern, final_content))
    
    unique_citations = len(set(citation_matches))
    if unique_citations >= 5:
        checks.append({'name': 'sufficient_citations', 'passed': True, 'detail': f'Found {unique_citations} unique citations'})
    else:
        checks.append({'name': 'sufficient_citations', 'passed': False, 'detail': f'Only {unique_citations} citations found, expected at least 5'})
    
    # Check 6: References section exists
    references_patterns = [
        r'##\s*references', r'##\s*bibliography', r'##\s*sources',
        r'###\s*references', r'references:', r'sources:', r'bibliography:'
    ]
    has_references = any(re.search(pattern, final_content) for pattern in references_patterns)
    if has_references:
        checks.append({'name': 'references_section', 'passed': True, 'detail': 'References section found'})
    else:
        checks.append({'name': 'references_section', 'passed': False, 'detail': 'No references section detected'})
    
    # Check 7: Target audience appropriate (tech leaders/CTOs)
    tech_leadership_terms = [
        'cto', 'chief technology officer', 'tech leader', 'technology leader',
        'engineering manager', 'technical decision', 'technology stack',
        'digital transformation', 'platform', 'architecture', 'scalability',
        'enterprise', 'organization', 'strategic', 'roi', 'productivity metrics'
    ]
    tech_term_count = sum(1 for term in tech_leadership_terms if term in final_content)
    if tech_term_count >= 3:
        checks.append({'name': 'tech_audience_appropriate', 'passed': True, 'detail': f'Found {tech_term_count} tech leadership terms'})
    else:
        checks.append({'name': 'tech_audience_appropriate', 'passed': False, 'detail': f'Only {tech_term_count} tech leadership terms, content may not target tech leaders'})
    
    # Check 8: Beyond video calls theme
    collaboration_themes = [
        'beyond video', 'async', 'asynchronous', 'collaboration tools',
        'digital workspace', 'remote collaboration', 'distributed team',
        'virtual collaboration', 'online collaboration', 'team productivity'
    ]
    theme_matches = sum(1 for theme in collaboration_themes if theme in final_content)
    if theme_matches >= 3:
        checks.append({'name': 'collaboration_theme', 'passed': True, 'detail': f'Found {theme_matches} collaboration theme references'})
    else:
        checks.append({'name': 'collaboration_theme', 'passed': False, 'detail': f'Only {theme_matches} collaboration themes found'})
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    score = passed_checks / len(checks)
    overall_passed = score >= 0.8  # Allow some flexibility for hard task
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result))