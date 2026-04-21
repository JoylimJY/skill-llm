#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Check 1: decision-doc.md exists
    doc_path = Path(workspace_dir) / 'decision-doc.md'
    doc_exists = doc_path.exists()
    checks.append({
        'name': 'decision-doc.md file exists',
        'passed': doc_exists,
        'detail': f'File found at {doc_path}' if doc_exists else 'File not found'
    })
    
    if not doc_exists:
        return {
            'passed': False,
            'score': 0.0,
            'checks': checks
        }
    
    # Read the document
    with open(doc_path, 'r') as f:
        content = f.read().lower()
    
    # Check 2: Document has Problem Statement section
    has_problem = any(keyword in content for keyword in ['problem', 'issue', 'challenge', 'pain'])
    checks.append({
        'name': 'Problem Statement section present',
        'passed': has_problem,
        'detail': 'Document addresses the problem/challenge' if has_problem else 'No problem statement found'
    })
    
    # Check 3: Document has Proposed Solution section
    has_solution = any(keyword in content for keyword in ['proposed', 'solution', 'approach', 'architecture'])
    checks.append({
        'name': 'Proposed Solution section present',
        'passed': has_solution,
        'detail': 'Document describes proposed solution' if has_solution else 'No solution section found'
    })
    
    # Check 4: Document has Alternatives Considered section
    has_alternatives = any(keyword in content for keyword in ['alternative', 'rejected', 'considered', 'why not'])
    checks.append({
        'name': 'Alternatives Considered section present',
        'passed': has_alternatives,
        'detail': 'Document discusses alternatives' if has_alternatives else 'No alternatives section found'
    })
    
    # Check 5: Document has Implementation Plan section
    has_timeline = any(keyword in content for keyword in ['implementation', 'timeline', 'phase', 'plan', 'schedule'])
    checks.append({
        'name': 'Implementation Plan section present',
        'passed': has_timeline,
        'detail': 'Document includes implementation timeline' if has_timeline else 'No implementation plan found'
    })
    
    # Check 6: Document has Risks section
    has_risks = any(keyword in content for keyword in ['risk', 'mitigation', 'challenge', 'concern'])
    checks.append({
        'name': 'Risks and Mitigations section present',
        'passed': has_risks,
        'detail': 'Document addresses risks' if has_risks else 'No risks section found'
    })
    
    # Check 7: Document contains substantive content (not just placeholders)
    placeholder_count = content.count('[to be written]')
    has_content = placeholder_count == 0 and len(content) > 500
    checks.append({
        'name': 'Document contains substantive content',
        'passed': has_content,
        'detail': f'Document has {len(content)} characters with {placeholder_count} placeholders' if has_content else f'Document appears incomplete ({placeholder_count} placeholders, {len(content)} chars)'
    })
    
    # Check 8: Document references microservices or migration context
    has_context = any(keyword in content for keyword in ['microservice', 'monolith', 'migration', 'api', 'service'])
    checks.append({
        'name': 'Document addresses microservices migration context',
        'passed': has_context,
        'detail': 'Document discusses microservices/migration' if has_context else 'Missing migration context'
    })
    
    # Check 9: Document has clear structure with headers
    has_structure = content.count('#') >= 4
    checks.append({
        'name': 'Document has clear section structure',
        'passed': has_structure,
        'detail': f'Document has {content.count("#")} section headers' if has_structure else 'Document lacks clear structure'
    })
    
    # Check 10: Document is readable and coherent
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    avg_line_length = sum(len(line) for line in lines) / max(len(lines), 1) if lines else 0
    is_coherent = avg_line_length > 20 and len(lines) > 15
    checks.append({
        'name': 'Document is coherent and well-formed',
        'passed': is_coherent,
        'detail': f'Document has {len(lines)} lines with avg length {avg_line_length:.1f}' if is_coherent else 'Document appears fragmented or too short'
    })
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    score = passed_count / len(checks)
    
    return {
        'passed': score >= 0.8,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '/workspace'
    result = evaluate(workspace)
    print(json.dumps(result))
