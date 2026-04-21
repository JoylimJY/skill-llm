import os
import sys
import json
import re
from pathlib import Path

def evaluate_communication_analysis(workspace_dir):
    checks = []
    workspace_path = Path(workspace_dir)
    
    # Check if the analysis file exists with correct name
    analysis_files = list(workspace_path.glob('communication_analysis.md'))
    if not analysis_files:
        # Check for similar filenames
        md_files = list(workspace_path.glob('*.md'))
        if md_files:
            # Use the first markdown file found
            analysis_file = md_files[0]
            checks.append({
                'name': 'Output file exists (flexible naming)',
                'passed': True,
                'detail': f'Found analysis file: {analysis_file.name}'
            })
        else:
            checks.append({
                'name': 'Output file exists',
                'passed': False,
                'detail': 'No communication_analysis.md or similar markdown file found'
            })
            return {'passed': False, 'score': 0.0, 'checks': checks}
    else:
        analysis_file = analysis_files[0]
        checks.append({
            'name': 'Correct output filename',
            'passed': True,
            'detail': 'Found communication_analysis.md as requested'
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
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    # Check for conflict avoidance analysis
    conflict_indicators = [
        'conflict', 'avoidance', 'avoiding', 'hedging', 'indirect',
        'maybe', 'kind of', 'sort of', 'potentially', 'i guess'
    ]
    conflict_found = any(indicator in content for indicator in conflict_indicators)
    checks.append({
        'name': 'Conflict avoidance pattern analysis',
        'passed': conflict_found,
        'detail': 'Found conflict avoidance analysis' if conflict_found else 'No conflict avoidance analysis detected'
    })
    
    # Check for timestamped quotes
    timestamp_pattern = r'\[?\d{2}:\d{2}:\d{2}\]?|\d{2}:\d{2}'
    has_timestamps = bool(re.search(timestamp_pattern, content))
    checks.append({
        'name': 'Timestamped quotes included',
        'passed': has_timestamps,
        'detail': 'Found timestamped examples from transcripts' if has_timestamps else 'No timestamped quotes found'
    })
    
    # Check for speaking ratio analysis
    speaking_indicators = [
        'speaking ratio', 'percentage', 'speaking time', 'talk time',
        'ratio', '%', 'percent', 'speaking turns', 'dominated'
    ]
    speaking_found = any(indicator in content for indicator in speaking_indicators)
    checks.append({
        'name': 'Speaking ratio analysis',
        'passed': speaking_found,
        'detail': 'Found speaking ratio analysis' if speaking_found else 'No speaking ratio analysis detected'
    })
    
    # Check for filler word analysis
    filler_indicators = [
        'filler', 'um', 'uh', 'like', 'you know', 'actually',
        'filler words', 'verbal tics', 'speech patterns'
    ]
    filler_found = any(indicator in content for indicator in filler_indicators)
    checks.append({
        'name': 'Filler word frequency analysis',
        'passed': filler_found,
        'detail': 'Found filler word analysis' if filler_found else 'No filler word analysis detected'
    })
    
    # Check for active listening analysis
    listening_indicators = [
        'active listening', 'listening', 'questions', 'clarifying',
        'paraphrasing', 'building on', 'references', 'asking'
    ]
    listening_found = any(indicator in content for indicator in listening_indicators)
    checks.append({
        'name': 'Active listening indicators',
        'passed': listening_found,
        'detail': 'Found active listening analysis' if listening_found else 'No active listening analysis detected'
    })
    
    # Check for leadership facilitation analysis
    leadership_indicators = [
        'leadership', 'facilitation', 'facilitating', 'meeting control',
        'decision making', 'inclusion', 'directive', 'collaborative'
    ]
    leadership_found = any(indicator in content for indicator in leadership_indicators)
    checks.append({
        'name': 'Leadership facilitation effectiveness',
        'passed': leadership_found,
        'detail': 'Found leadership analysis' if leadership_found else 'No leadership facilitation analysis detected'
    })
    
    # Check for actionable recommendations (looking for numbered lists or bullet points)
    recommendation_indicators = [
        'recommendation', 'improve', 'better', 'next steps',
        'action', 'growth', 'development', 'should'
    ]
    rec_found = any(indicator in content for indicator in recommendation_indicators)
    
    # Count recommendations by looking for numbered lists or structured advice
    rec_patterns = [
        r'\d+\.',  # Numbered lists
        r'\*\s',   # Bullet points with asterisk
        r'-\s',    # Bullet points with dash
        r'##.*recommendation',  # Headers containing recommendation
        r'##.*improve',  # Headers about improvement
        r'##.*next'      # Next steps sections
    ]
    rec_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in rec_patterns)
    
    checks.append({
        'name': 'Actionable recommendations (at least 3)',
        'passed': rec_found and rec_count >= 3,
        'detail': f'Found {rec_count} recommendation indicators' if rec_found else 'No clear recommendations found'
    })
    
    # Check for quotes from transcripts (Alex Chen mentioned)
    alex_quotes = 'alex chen' in content
    checks.append({
        'name': 'Specific examples with quotes',
        'passed': alex_quotes,
        'detail': 'Found quotes attributed to Alex Chen' if alex_quotes else 'No specific attributed quotes found'
    })
    
    # Check for explanation of why behaviors matter
    explanation_indicators = [
        'why this matters', 'impact', 'because', 'affects',
        'important', 'matters', 'consequence', 'result'
    ]
    explanation_found = any(indicator in content for indicator in explanation_indicators)
    checks.append({
        'name': 'Explanations of why behaviors matter',
        'passed': explanation_found,
        'detail': 'Found explanations of behavioral impact' if explanation_found else 'No behavioral impact explanations found'
    })
    
    # Check content length (should be comprehensive)
    word_count = len(content.split())
    checks.append({
        'name': 'Comprehensive analysis (sufficient detail)',
        'passed': word_count >= 500,
        'detail': f'Analysis contains {word_count} words' + (' (comprehensive)' if word_count >= 500 else ' (may be too brief)')
    })
    
    # Calculate final score
    passed_checks = sum(1 for check in checks if check['passed'])
    score = passed_checks / len(checks)
    overall_passed = score >= 0.8
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'Script usage', 'passed': False, 'detail': 'Workspace directory argument required'}]}))
        sys.exit(1)
    
    result = evaluate_communication_analysis(sys.argv[1])
    print(json.dumps(result))