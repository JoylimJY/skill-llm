import os
import sys
import json
import re
from pathlib import Path

def check_file_exists(workspace_path):
    """Check if the output file exists"""
    report_path = Path(workspace_path) / 'meeting_insights_report.md'
    return report_path.exists(), str(report_path)

def check_conflict_avoidance_analysis(content):
    """Check for conflict avoidance pattern analysis"""
    conflict_keywords = ['conflict', 'avoidance', 'hedging', 'indirect', 'maybe', 'kind of', 'i think']
    has_analysis = any(keyword.lower() in content.lower() for keyword in conflict_keywords)
    
    # Look for specific examples with timestamps
    timestamp_pattern = r'\d{2}:\d{2}:\d{2}'
    has_timestamps = bool(re.search(timestamp_pattern, content))
    
    # Look for quoted examples
    has_quotes = '>' in content or '"' in content
    
    return has_analysis and has_timestamps and has_quotes

def check_speaking_ratio_analysis(content):
    """Check for speaking ratio analysis"""
    ratio_keywords = ['speaking', 'ratio', 'percentage', '%', 'time', 'duration']
    has_ratio_analysis = any(keyword.lower() in content.lower() for keyword in ratio_keywords)
    
    # Look for numerical analysis
    has_numbers = bool(re.search(r'\d+%', content))
    
    return has_ratio_analysis and has_numbers

def check_filler_words_analysis(content):
    """Check for filler words and hedging language analysis"""
    filler_keywords = ['filler', 'um', 'uh', 'like', 'you know', 'hedging', 'frequency']
    has_filler_analysis = any(keyword.lower() in content.lower() for keyword in filler_keywords)
    
    # Look for specific filler word examples
    filler_examples = bool(re.search(r'("um"|"uh"|"like"|"you know")', content, re.IGNORECASE))
    
    return has_filler_analysis or filler_examples

def check_active_listening_analysis(content):
    """Check for active listening behavior analysis"""
    listening_keywords = ['listening', 'questions', 'clarifying', 'paraphrasing', 'building']
    has_listening_analysis = any(keyword.lower() in content.lower() for keyword in listening_keywords)
    
    # Look for examples of good listening behaviors mentioned
    listening_examples = bool(re.search(r'(paraphrasing|building on|clarifying)', content, re.IGNORECASE))
    
    return has_listening_analysis or listening_examples

def check_leadership_facilitation_analysis(content):
    """Check for leadership and facilitation effectiveness analysis"""
    leadership_keywords = ['leadership', 'facilitation', 'decision', 'decisive', 'team', 'meeting']
    has_leadership_analysis = any(keyword.lower() in content.lower() for keyword in leadership_keywords)
    
    # Look for decision-making analysis
    decision_analysis = bool(re.search(r'(decision|decisive|indecisive)', content, re.IGNORECASE))
    
    return has_leadership_analysis and decision_analysis

def check_actionable_recommendations(content):
    """Check for actionable recommendations"""
    recommendation_keywords = ['recommendation', 'improve', 'better', 'action', 'next steps']
    has_recommendations = any(keyword.lower() in content.lower() for keyword in recommendation_keywords)
    
    # Look for structured recommendations (numbered lists, bullet points)
    has_structure = bool(re.search(r'(\n\d+\.|\n-|\n\*)', content))
    
    return has_recommendations and has_structure

def check_frequency_counts(content):
    """Check for frequency counts and quantitative analysis"""
    frequency_indicators = ['times', 'instances', 'frequency', 'count', 'across']
    has_frequency = any(indicator.lower() in content.lower() for indicator in frequency_indicators)
    
    # Look for numbers indicating frequency
    has_counts = bool(re.search(r'\d+\s+(times|instances|meetings)', content, re.IGNORECASE))
    
    return has_frequency or has_counts

def check_specific_quotes(content):
    """Check for specific quotes from transcripts"""
    # Look for quoted content that matches patterns from our transcripts
    transcript_quotes = [
        'maybe we could',
        'i was thinking',
        'if that makes sense',
        'whatever you think',
        'you know'
    ]
    
    has_specific_quotes = any(quote.lower() in content.lower() for quote in transcript_quotes)
    
    # Also check for quote formatting
    has_quote_formatting = bool(re.search(r'(>\s|"[^"]{20,}")', content))
    
    return has_specific_quotes or has_quote_formatting

def main(workspace_path):
    checks = []
    
    # Check if file exists
    file_exists, file_path = check_file_exists(workspace_path)
    checks.append({
        'name': 'Output file exists',
        'passed': file_exists,
        'detail': f'Expected meeting_insights_report.md at {file_path}'
    })
    
    if not file_exists:
        return {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
    
    # Read the content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        checks.append({
            'name': 'File readable',
            'passed': False,
            'detail': f'Error reading file: {str(e)}'
        })
        return {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
    
    # Check conflict avoidance analysis
    checks.append({
        'name': 'Conflict avoidance analysis',
        'passed': check_conflict_avoidance_analysis(content),
        'detail': 'Should identify conflict avoidance patterns with timestamped examples'
    })
    
    # Check speaking ratio analysis
    checks.append({
        'name': 'Speaking ratio analysis',
        'passed': check_speaking_ratio_analysis(content),
        'detail': 'Should analyze speaking ratios with percentages or numerical data'
    })
    
    # Check filler words analysis
    checks.append({
        'name': 'Filler words analysis',
        'passed': check_filler_words_analysis(content),
        'detail': 'Should identify filler words and hedging language usage'
    })
    
    # Check active listening analysis
    checks.append({
        'name': 'Active listening analysis',
        'passed': check_active_listening_analysis(content),
        'detail': 'Should analyze active listening behaviors and examples'
    })
    
    # Check leadership facilitation analysis
    checks.append({
        'name': 'Leadership facilitation analysis', 
        'passed': check_leadership_facilitation_analysis(content),
        'detail': 'Should evaluate leadership and decision-making effectiveness'
    })
    
    # Check actionable recommendations
    checks.append({
        'name': 'Actionable recommendations',
        'passed': check_actionable_recommendations(content),
        'detail': 'Should provide specific, actionable improvement recommendations'
    })
    
    # Check frequency counts
    checks.append({
        'name': 'Frequency counts',
        'passed': check_frequency_counts(content),
        'detail': 'Should include quantitative frequency analysis of behaviors'
    })
    
    # Check specific quotes
    checks.append({
        'name': 'Specific transcript quotes',
        'passed': check_specific_quotes(content),
        'detail': 'Should include specific quotes from the provided transcripts'
    })
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    return {
        'passed': score == 1.0,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'error': 'Usage: eval_script.py <workspace_path>'}))
        sys.exit(1)
    
    result = main(sys.argv[1])
    print(json.dumps(result))