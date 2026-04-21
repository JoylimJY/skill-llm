import sys
import os
import json
import re
from pathlib import Path

def evaluate_task(workspace_dir):
    checks = []
    workspace_path = Path(workspace_dir)
    
    # Find markdown report files
    report_files = list(workspace_path.glob('*.md')) + list(workspace_path.glob('*report*')) + list(workspace_path.glob('*growth*'))
    
    if not report_files:
        # Check for any text files that might contain the report
        report_files = [f for f in workspace_path.glob('*.txt') if f.stat().st_size > 1000]
    
    best_score = 0
    best_content = ""
    
    for report_file in report_files:
        try:
            content = report_file.read_text(encoding='utf-8').lower()
            file_score = evaluate_report_content(content, checks)
            if file_score > best_score:
                best_score = file_score
                best_content = content
        except Exception as e:
            continue
    
    if not best_content:
        checks.append({"name": "report_file_exists", "passed": False, "detail": "No report file found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Evaluate the best report content
    evaluate_report_content(best_content, checks)
    
    # Calculate final score
    passed_checks = sum(1 for c in checks if c['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    return {
        "passed": score >= 0.8,
        "score": score,
        "checks": checks
    }

def evaluate_report_content(content, checks):
    # Check for required sections
    required_sections = [
        ('work_summary', ['work summary', 'summary', 'recent work']),
        ('improvement_areas', ['improvement', 'areas', 'skill', 'growth']), 
        ('strengths', ['strength', 'doing well', 'good']),
        ('action_items', ['action', 'priority', 'next step']),
        ('learning_resources', ['learning', 'resource', 'hackernews', 'article'])
    ]
    
    for section_name, keywords in required_sections:
        has_section = any(keyword in content for keyword in keywords)
        checks.append({
            "name": f"has_{section_name}",
            "passed": has_section,
            "detail": f"Report contains {section_name.replace('_', ' ')} section: {has_section}"
        })
    
    # Check for specific improvement areas (at least 3)
    improvement_patterns = [
        r'typescript.*type',
        r'security.*data', 
        r'error.*handling',
        r'async.*await',
        r'react.*component',
        r'css.*layout',
        r'validation.*api'
    ]
    
    found_areas = sum(1 for pattern in improvement_patterns if re.search(pattern, content, re.IGNORECASE))
    checks.append({
        "name": "multiple_improvement_areas",
        "passed": found_areas >= 3,
        "detail": f"Found {found_areas} improvement areas (need >= 3)"
    })
    
    # Check for evidence-based analysis
    evidence_keywords = ['observed', 'noticed', 'chat', 'project', 'recent work', 'struggle', 'challenge']
    has_evidence = sum(1 for keyword in evidence_keywords if keyword in content) >= 2
    checks.append({
        "name": "evidence_based_analysis", 
        "passed": has_evidence,
        "detail": f"Analysis includes evidence from chat history: {has_evidence}"
    })
    
    # Check for specific technologies mentioned
    tech_keywords = ['typescript', 'react', 'node', 'express', 'css', 'api', 'database']
    mentioned_tech = sum(1 for tech in tech_keywords if tech in content)
    checks.append({
        "name": "mentions_technologies",
        "passed": mentioned_tech >= 3,
        "detail": f"Report mentions {mentioned_tech} technologies from chat history"
    })
    
    # Check for learning resources with URLs/links
    has_links = 'http' in content or 'link' in content or 'url' in content or 'hackernews' in content
    checks.append({
        "name": "includes_learning_resources",
        "passed": has_links,
        "detail": f"Report includes learning resource links: {has_links}"
    })
    
    # Check for actionable recommendations
    action_keywords = ['recommend', 'focus', 'study', 'practice', 'implement', 'learn', 'improve']
    actionable_count = sum(1 for keyword in action_keywords if keyword in content)
    checks.append({
        "name": "actionable_recommendations",
        "passed": actionable_count >= 4,
        "detail": f"Report contains {actionable_count} actionable recommendations"
    })
    
    # Check for proper markdown structure  
    has_headers = '#' in content
    has_structure = '##' in content or '###' in content
    checks.append({
        "name": "proper_formatting",
        "passed": has_headers and has_structure,
        "detail": f"Report uses proper markdown formatting: {has_headers and has_structure}"
    })
    
    return sum(1 for c in checks if c['passed']) / len(checks)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Invalid arguments"}]}))
        sys.exit(1)
    
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result))