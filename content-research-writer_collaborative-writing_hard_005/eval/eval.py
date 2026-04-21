import os
import sys
import json
import re
from pathlib import Path

def evaluate_task(workspace_dir):
    workspace_path = Path(workspace_dir)
    checks = []
    
    # Check 1: Final article file exists
    final_article_path = None
    for file_path in workspace_path.glob('*.md'):
        if 'final' in file_path.name.lower() and 'article' in file_path.name.lower():
            final_article_path = file_path
            break
    
    if final_article_path and final_article_path.exists():
        checks.append({"name": "final_article_exists", "passed": True, "detail": f"Found final article: {final_article_path.name}"})
        article_content = final_article_path.read_text().lower()
    else:
        checks.append({"name": "final_article_exists", "passed": False, "detail": "No final-article.md or similar file found"})
        article_content = ""
    
    # Check 2: Research notes file exists
    research_file_found = False
    research_content = ""
    for file_path in workspace_path.glob('*.md'):
        if 'research' in file_path.name.lower() and ('note' in file_path.name.lower() or 'finding' in file_path.name.lower()):
            research_file_found = True
            research_content = file_path.read_text().lower()
            break
    
    checks.append({"name": "research_notes_exists", "passed": research_file_found, "detail": "Research notes file found" if research_file_found else "No research-notes.md or similar file found"})
    
    # Check 3: Article has compelling hook with data or story
    hook_found = False
    hook_patterns = [
        r'\d+%',  # percentage
        r'\$[\d,]+',  # dollar amounts
        r'\d+[kmb]\+?',  # numbers with k/m/b
        r'study shows?',
        r'survey found',
        r'research reveals?',
        r'according to',
        r'imagine if',
        r'what if',
        r'last (week|month|year)',
        r'story of',
        r'meet [a-z]+'
    ]
    
    for pattern in hook_patterns:
        if re.search(pattern, article_content, re.IGNORECASE):
            hook_found = True
            break
    
    checks.append({"name": "compelling_hook", "passed": hook_found, "detail": "Hook contains data or story elements" if hook_found else "Hook lacks compelling data or story elements"})
    
    # Check 4: Article has at least 3 main sections
    section_count = 0
    section_patterns = [
        r'^#{1,3}\s+[^#]',  # markdown headers
        r'\*\*[^*]+\*\*',  # bold section titles
        r'^[\d]+\.',  # numbered sections
    ]
    
    lines = article_content.split('\n')
    for line in lines:
        for pattern in section_patterns:
            if re.search(pattern, line, re.MULTILINE | re.IGNORECASE):
                section_count += 1
                break
    
    checks.append({"name": "three_main_sections", "passed": section_count >= 3, "detail": f"Found {section_count} sections (need 3+)"})
    
    # Check 5: Citations in [Author, Year] format
    citation_patterns = [
        r'\[[^\]]+,\s*\d{4}\]',  # [Author, 2023]
        r'\([^\)]+,\s*\d{4}\)',  # (Author, 2023)
        r'\[[^\]]*\d{4}[^\]]*\]'  # [study 2023] or similar
    ]
    
    citations_found = False
    for pattern in citation_patterns:
        if re.search(pattern, article_content, re.IGNORECASE):
            citations_found = True
            break
    
    checks.append({"name": "proper_citations", "passed": citations_found, "detail": "Citations found in proper format" if citations_found else "No proper citations found"})
    
    # Check 6: Conclusion with actionable insights
    conclusion_found = False
    actionable_found = False
    
    conclusion_indicators = ['conclusion', 'summary', 'takeaway', 'final', 'wrap']
    actionable_indicators = ['should', 'can', 'recommend', 'suggest', 'consider', 'try', 'implement', 'action', 'step', 'tip']
    
    for indicator in conclusion_indicators:
        if indicator in article_content:
            conclusion_found = True
            break
    
    for indicator in actionable_indicators:
        if indicator in article_content:
            actionable_found = True
            break
    
    conclusion_with_actions = conclusion_found and actionable_found
    checks.append({"name": "actionable_conclusion", "passed": conclusion_with_actions, "detail": "Conclusion with actionable insights found" if conclusion_with_actions else "Missing conclusion with actionable insights"})
    
    # Check 7: Research demonstrates evidence gathering
    research_quality = False
    if research_content:
        research_indicators = ['study', 'survey', 'research', 'data', 'statistic', 'report', 'finding', 'evidence']
        research_score = sum(1 for indicator in research_indicators if indicator in research_content)
        research_quality = research_score >= 3
    
    checks.append({"name": "research_quality", "passed": research_quality, "detail": "Research demonstrates thorough evidence gathering" if research_quality else "Research lacks sufficient evidence gathering"})
    
    # Check 8: Business audience appropriate tone
    business_tone_found = False
    business_terms = ['productivity', 'efficiency', 'performance', 'roi', 'business', 'organization', 'company', 'team', 'management', 'strategy']
    business_score = sum(1 for term in business_terms if term in article_content)
    business_tone_found = business_score >= 4
    
    checks.append({"name": "business_audience_tone", "passed": business_tone_found, "detail": "Appropriate business tone maintained" if business_tone_found else "Tone not suitable for business audience"})
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    overall_passed = score >= 0.8
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))
    return result

if __name__ == '__main__':
    evaluate_task(sys.argv[1])