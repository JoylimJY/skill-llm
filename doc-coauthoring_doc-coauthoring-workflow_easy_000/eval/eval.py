#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Check 1: File exists
    doc_path = Path(workspace_dir) / 'graphql-migration-decision.md'
    file_exists = doc_path.exists()
    checks.append({
        'name': 'Output file exists',
        'passed': file_exists,
        'detail': f'File graphql-migration-decision.md found at {doc_path}' if file_exists else 'File not found'
    })
    
    if not file_exists:
        return {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
    
    # Read document
    with open(doc_path, 'r') as f:
        content = f.read().lower()
    
    # Check 2: Document has substantial content
    word_count = len(content.split())
    has_content = word_count >= 300
    checks.append({
        'name': 'Document has substantial content',
        'passed': has_content,
        'detail': f'Word count: {word_count} (minimum 300 required)'
    })
    
    # Check 3: Document addresses the decision topic
    decision_keywords = ['graphql', 'rest', 'migration', 'api']
    has_decision_focus = any(keyword in content for keyword in decision_keywords)
    checks.append({
        'name': 'Document addresses GraphQL/REST decision',
        'passed': has_decision_focus,
        'detail': 'Document discusses GraphQL, REST, migration, or API' if has_decision_focus else 'Missing core topic'
    })
    
    # Check 4: Document includes trade-offs or considerations
    tradeoff_keywords = ['benefit', 'concern', 'trade-off', 'advantage', 'disadvantage', 'risk', 'challenge', 'consideration']
    has_tradeoffs = any(keyword in content for keyword in tradeoff_keywords)
    checks.append({
        'name': 'Document discusses trade-offs',
        'passed': has_tradeoffs,
        'detail': 'Document includes benefits, concerns, or trade-offs' if has_tradeoffs else 'Missing trade-off analysis'
    })
    
    # Check 5: Document has clear structure
    structure_keywords = ['background', 'proposal', 'recommendation', 'conclusion', 'decision', 'rationale', 'approach']
    has_structure = any(keyword in content for keyword in structure_keywords)
    checks.append({
        'name': 'Document has clear structure',
        'passed': has_structure,
        'detail': 'Document includes structured sections' if has_structure else 'Missing clear structure'
    })
    
    # Check 6: Document is readable and well-formatted
    has_headers = '#' in content or '==' in content
    checks.append({
        'name': 'Document uses formatting',
        'passed': has_headers,
        'detail': 'Document includes headers or formatting' if has_headers else 'Missing formatting'
    })
    
    # Check 7: Document mentions stakeholders or audience
    audience_keywords = ['stakeholder', 'team', 'engineer', 'developer', 'audience', 'reader']
    considers_audience = any(keyword in content for keyword in audience_keywords)
    checks.append({
        'name': 'Document considers audience',
        'passed': considers_audience,
        'detail': 'Document references stakeholders or audience' if considers_audience else 'Missing audience consideration'
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
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    result = evaluate(workspace)
    print(json.dumps(result))
