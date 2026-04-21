import os
import sys
import json
import re
from pathlib import Path

def evaluate_communication_analysis(workspace_dir):
    checks = []
    
    # Find the analysis file
    analysis_file = None
    for file in Path(workspace_dir).glob('*.md'):
        if 'communication' in file.name.lower() and 'analysis' in file.name.lower():
            analysis_file = file
            break
    
    if not analysis_file:
        checks.append({
            'name': 'Analysis file exists',
            'passed': False,
            'detail': 'No markdown file with communication analysis found'
        })
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    checks.append({
        'name': 'Analysis file exists',
        'passed': True,
        'detail': f'Found analysis file: {analysis_file.name}'
    })
    
    # Read the analysis content
    try:
        with open(analysis_file, 'r', encoding='utf-8') as f:
            content = f.read().lower()
    except Exception as e:
        checks.append({
            'name': 'File readable',
            'passed': False,
            'detail': f'Could not read analysis file: {str(e)}'
        })
        return {'passed': False, 'score': len([c for c in checks if c['passed']]) / len(checks), 'checks': checks}
    
    checks.append({
        'name': 'File readable',
        'passed': True,
        'detail': 'Analysis file successfully read'
    })
    
    # Check for conflict avoidance analysis
    conflict_patterns = ['conflict', 'avoid', 'hedging', 'maybe', 'potentially', 'indirect']
    has_conflict_analysis = any(pattern in content for pattern in conflict_patterns)
    
    checks.append({
        'name': 'Conflict avoidance analysis',
        'passed': has_conflict_analysis,
        'detail': 'Found conflict avoidance patterns analysis' if has_conflict_analysis else 'Missing conflict avoidance analysis'
    })
    
    # Check for speaking ratio analysis
    ratio_patterns = ['speaking', 'ratio', 'percentage', 'talk', 'listen']
    has_ratio_analysis = any(pattern in content for pattern in ratio_patterns)
    
    checks.append({
        'name': 'Speaking ratio analysis',
        'passed': has_ratio_analysis,
        'detail': 'Found speaking ratio analysis' if has_ratio_analysis else 'Missing speaking ratio analysis'
    })
    
    # Check for filler words analysis  
    filler_patterns = ['filler', 'um', 'uh', 'like', 'you know', 'actually']
    has_filler_analysis = any(pattern in content for pattern in filler_patterns)
    
    checks.append({
        'name': 'Filler words analysis',
        'passed': has_filler_analysis,
        'detail': 'Found filler words analysis' if has_filler_analysis else 'Missing filler words analysis'
    })
    
    # Check for active listening analysis
    listening_patterns = ['listen', 'question', 'clarify', 'paraphras', 'hearing', 'understand']
    has_listening_analysis = any(pattern in content for pattern in listening_patterns)
    
    checks.append({
        'name': 'Active listening analysis',
        'passed': has_listening_analysis,
        'detail': 'Found active listening analysis' if has_listening_analysis else 'Missing active listening analysis'
    })
    
    # Check for timestamped examples
    timestamp_patterns = [r'\d{2}:\d{2}:\d{2}', r'\d{1,2}:\d{2}', 'timestamp']
    has_timestamps = any(re.search(pattern, content, re.IGNORECASE) for pattern in timestamp_patterns)
    
    checks.append({
        'name': 'Timestamped examples',
        'passed': has_timestamps,
        'detail': 'Found timestamped examples' if has_timestamps else 'Missing timestamped examples'
    })
    
    # Check for specific meeting references
    meeting_patterns = ['standup', 'review', 'client', 'feedback', 'retrospective']
    has_meeting_refs = any(pattern in content for pattern in meeting_patterns)
    
    checks.append({
        'name': 'Specific meeting references',
        'passed': has_meeting_refs,
        'detail': 'Found specific meeting references' if has_meeting_refs else 'Missing specific meeting references'
    })
    
    # Check for structured sections
    section_patterns = ['#', '##', '###', 'pattern', 'finding', 'example']
    has_structure = any(pattern in content for pattern in section_patterns)
    
    checks.append({
        'name': 'Structured analysis format',
        'passed': has_structure,
        'detail': 'Found structured sections' if has_structure else 'Missing structured format'
    })
    
    # Check for actionable insights/recommendations
    insight_patterns = ['recommend', 'improve', 'better', 'suggest', 'next', 'action']
    has_insights = any(pattern in content for pattern in insight_patterns)
    
    checks.append({
        'name': 'Actionable insights',
        'passed': has_insights,
        'detail': 'Found actionable insights' if has_insights else 'Missing actionable insights'
    })
    
    # Calculate final score
    passed_checks = len([c for c in checks if c['passed']])
    total_checks = len(checks)
    score = passed_checks / total_checks
    overall_passed = score >= 0.8
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace_dir = sys.argv[1]
    result = evaluate_communication_analysis(workspace_dir)
    print(json.dumps(result))