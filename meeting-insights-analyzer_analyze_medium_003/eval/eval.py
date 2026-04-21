import os
import sys
import json
import re

def check_communication_analysis(workspace_path):
    checks = []
    
    # Check if the analysis file exists
    analysis_file = None
    for file in os.listdir(workspace_path):
        if file.lower() == 'communication_analysis.md' or 'communication' in file.lower() and file.endswith('.md'):
            analysis_file = os.path.join(workspace_path, file)
            break
    
    if not analysis_file:
        checks.append({
            'name': 'Analysis file exists',
            'passed': False, 
            'detail': 'No communication analysis markdown file found'
        })
        # Return early if no file found
        return {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
    
    checks.append({
        'name': 'Analysis file exists',
        'passed': True,
        'detail': f'Found analysis file: {os.path.basename(analysis_file)}'
    })
    
    # Read the analysis content
    try:
        with open(analysis_file, 'r', encoding='utf-8') as f:
            content = f.read().lower()
    except Exception as e:
        checks.append({
            'name': 'File readable',
            'passed': False,
            'detail': f'Could not read analysis file: {e}'
        })
        return {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
    
    checks.append({
        'name': 'File readable', 
        'passed': True,
        'detail': 'Analysis file successfully read'
    })
    
    # Check for conflict avoidance analysis
    conflict_keywords = ['conflict', 'avoid', 'indirect', 'hedging', 'maybe', 'kind of', 'i think']
    found_conflict_analysis = any(keyword in content for keyword in conflict_keywords)
    checks.append({
        'name': 'Conflict avoidance analysis',
        'passed': found_conflict_analysis,
        'detail': f'Found conflict avoidance analysis: {found_conflict_analysis}'
    })
    
    # Check for specific examples with timestamps
    timestamp_pattern = r'\[?\d{2}:\d{2}:\d{2}\]?|\d{2}:\d{2}'
    has_timestamps = bool(re.search(timestamp_pattern, content))
    checks.append({
        'name': 'Includes timestamps',
        'passed': has_timestamps,
        'detail': f'Found timestamp references: {has_timestamps}'
    })
    
    # Check for speaking patterns analysis
    speaking_keywords = ['speaking', 'filler', 'um', 'uh', 'pattern', 'communication']
    found_speaking_analysis = sum(1 for keyword in speaking_keywords if keyword in content) >= 3
    checks.append({
        'name': 'Speaking patterns analysis',
        'passed': found_speaking_analysis,
        'detail': f'Found speaking patterns analysis: {found_speaking_analysis}'
    })
    
    # Check for actionable recommendations
    recommendation_keywords = ['recommend', 'improve', 'suggestion', 'better', 'action', 'next steps']
    found_recommendations = sum(1 for keyword in recommendation_keywords if keyword in content) >= 2
    checks.append({
        'name': 'Actionable recommendations',
        'passed': found_recommendations, 
        'detail': f'Found actionable recommendations: {found_recommendations}'
    })
    
    # Check for specific meeting references
    meeting_refs = ['standup', 'project review', 'client call', 'performance review', 'january', 'february']
    found_meeting_refs = sum(1 for ref in meeting_refs if ref in content) >= 3
    checks.append({
        'name': 'References specific meetings',
        'passed': found_meeting_refs,
        'detail': f'Found specific meeting references: {found_meeting_refs}'
    })
    
    # Check for examples of indirect language from transcripts
    indirect_examples = ['maybe we could', 'if you think', 'kind of thinking', 'i guess', 'whatever you think']
    found_indirect_examples = any(example in content for example in indirect_examples)
    checks.append({
        'name': 'Identifies indirect language examples',
        'passed': found_indirect_examples,
        'detail': f'Found indirect language examples: {found_indirect_examples}'
    })
    
    # Check document structure (headings)
    heading_pattern = r'#+\s*\w+|^\w+\s*\n=+|^\w+\s*\n-+'
    has_structure = bool(re.search(heading_pattern, content, re.MULTILINE))
    checks.append({
        'name': 'Well-structured document',
        'passed': has_structure,
        'detail': f'Found document structure/headings: {has_structure}'
    })
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_count / total_checks
    overall_passed = score >= 0.8
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace_path = sys.argv[1]
    result = check_communication_analysis(workspace_path)
    print(json.dumps(result))