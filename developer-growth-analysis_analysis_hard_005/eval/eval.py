import os
import sys
import json
import re
from pathlib import Path

def check_file_exists(workspace_dir, filename):
    """Check if the specified file exists"""
    file_path = Path(workspace_dir) / filename
    return file_path.exists(), str(file_path)

def check_report_structure(file_content):
    """Check if report has required sections with flexible matching"""
    content_lower = file_content.lower()
    
    required_sections = [
        (['work summary', 'summary'], 'Work Summary section'),
        (['improvement areas', 'improvement'], 'Improvement Areas section'),
        (['strengths', 'strength'], 'Strengths section'),
        (['action items', 'actions'], 'Action Items section'),
        (['learning resources', 'resources'], 'Learning Resources section')
    ]
    
    checks = []
    for keywords, description in required_sections:
        found = any(keyword in content_lower for keyword in keywords)
        checks.append((description, found))
    
    return checks

def check_improvement_areas_quality(file_content):
    """Check if improvement areas are specific and evidence-based"""
    content_lower = file_content.lower()
    
    # Look for evidence of specific technology mentions
    tech_keywords = ['typescript', 'react', 'css', 'database', 'auth', 'error', 'async']
    tech_mentioned = any(keyword in content_lower for keyword in tech_keywords)
    
    # Look for evidence-based language
    evidence_phrases = ['observed', 'noticed', 'struggled', 'your work shows', 'in your recent', 'what i saw']
    evidence_based = any(phrase in content_lower for phrase in evidence_phrases)
    
    # Look for specific recommendations
    recommendation_phrases = ['recommendation', 'study', 'learn', 'practice', 'apply', 'focus on']
    has_recommendations = any(phrase in content_lower for phrase in recommendation_phrases)
    
    return [
        ('Technology-specific areas identified', tech_mentioned),
        ('Evidence-based observations', evidence_based),
        ('Specific recommendations provided', has_recommendations)
    ]

def check_time_period_analysis(file_content):
    """Check if report analyzes recent time period (24-48 hours)"""
    content_lower = file_content.lower()
    
    time_indicators = ['24 hours', '48 hours', 'past day', 'past two days', 'recent', 'yesterday', 'today']
    has_time_reference = any(indicator in content_lower for indicator in time_indicators)
    
    return has_time_reference

def check_prioritization(file_content):
    """Check if improvement areas are prioritized"""
    content_lower = file_content.lower()
    
    # Look for numbering or priority indicators
    priority_patterns = [
        r'###?\s*1\.',  # ### 1. or ## 1.
        r'priority',
        r'most important',
        r'first',
        r'\b1\b.*\b2\b.*\b3\b'  # Sequential numbering
    ]
    
    has_prioritization = any(re.search(pattern, content_lower, re.IGNORECASE) for pattern in priority_patterns)
    return has_prioritization

def check_actionable_items(file_content):
    """Check for specific, actionable next steps"""
    content_lower = file_content.lower()
    
    action_indicators = ['spend', 'hours', 'study', 'practice', 'apply', 'document', 'set up', 'review']
    has_actions = any(indicator in content_lower for indicator in action_indicators)
    
    return has_actions

def main(workspace_dir):
    checks = []
    
    # Check 1: Report file exists
    file_exists, file_path = check_file_exists(workspace_dir, 'growth_report.md')
    checks.append({
        'name': 'Growth report file created',
        'passed': file_exists,
        'detail': f'Expected growth_report.md at {file_path}'
    })
    
    if not file_exists:
        return {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
    
    # Read the report content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        checks.append({
            'name': 'Report file readable',
            'passed': False,
            'detail': f'Error reading file: {str(e)}'
        })
        return {
            'passed': False,
            'score': len([c for c in checks if c['passed']]) / len(checks),
            'checks': checks
        }
    
    # Check 2-6: Report structure
    structure_checks = check_report_structure(content)
    for description, passed in structure_checks:
        checks.append({
            'name': description,
            'passed': passed,
            'detail': f'Section {"found" if passed else "missing"} in report'
        })
    
    # Check 7-9: Improvement areas quality
    quality_checks = check_improvement_areas_quality(content)
    for description, passed in quality_checks:
        checks.append({
            'name': description,
            'passed': passed,
            'detail': f'Quality check {"passed" if passed else "failed"}'
        })
    
    # Check 10: Time period analysis
    time_check = check_time_period_analysis(content)
    checks.append({
        'name': 'Recent time period analyzed',
        'passed': time_check,
        'detail': 'Report references recent work period (24-48 hours)'
    })
    
    # Check 11: Prioritization
    priority_check = check_prioritization(content)
    checks.append({
        'name': 'Improvement areas prioritized',
        'passed': priority_check,
        'detail': 'Areas are numbered or prioritized'
    })
    
    # Check 12: Actionable items
    action_check = check_actionable_items(content)
    checks.append({
        'name': 'Specific action items provided',
        'passed': action_check,
        'detail': 'Report includes concrete next steps'
    })
    
    # Calculate final score
    passed_count = len([c for c in checks if c['passed']])
    total_count = len(checks)
    score = passed_count / total_count
    
    return {
        'passed': score >= 0.8,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_dir>')
        sys.exit(1)
    
    result = main(sys.argv[1])
    print(json.dumps(result))