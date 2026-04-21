#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Check 1: Document file exists
    doc_files = list(Path(workspace_dir).glob('*.md')) + list(Path(workspace_dir).glob('*.txt'))
    doc_exists = len(doc_files) > 0
    checks.append({
        "name": "Document file created",
        "passed": doc_exists,
        "detail": f"Found {len(doc_files)} document file(s)" if doc_exists else "No document file found"
    })
    
    if not doc_exists:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Read the best document found
    doc_content = ""
    for doc_file in doc_files:
        try:
            with open(doc_file, 'r') as f:
                content = f.read()
                if len(content) > len(doc_content):
                    doc_content = content
        except:
            pass
    
    # Check 2: Document has required sections for decision doc
    required_sections = ['problem', 'option', 'recommend', 'rationale', 'risk']
    sections_found = sum(1 for section in required_sections if section.lower() in doc_content.lower())
    checks.append({
        "name": "Required sections present",
        "passed": sections_found >= 4,
        "detail": f"Found {sections_found}/5 key sections (problem, options, recommendation, rationale, risks)"
    })
    
    # Check 3: Document addresses microservices migration topic
    microservices_mentioned = 'microservice' in doc_content.lower()
    monolith_mentioned = 'monolith' in doc_content.lower()
    checks.append({
        "name": "Topic-specific content",
        "passed": microservices_mentioned and monolith_mentioned,
        "detail": "Document discusses both microservices and monolith approaches" if (microservices_mentioned and monolith_mentioned) else "Missing discussion of key approaches"
    })
    
    # Check 4: Document has meaningful length (not just template)
    has_substance = len(doc_content) > 500 and doc_content.count('\n') > 10
    checks.append({
        "name": "Document has substantive content",
        "passed": has_substance,
        "detail": f"Document length: {len(doc_content)} chars, {doc_content.count(chr(10))} lines" if has_substance else "Document appears to be mostly template"
    })
    
    # Check 5: Document includes decision rationale
    has_rationale = any(keyword in doc_content.lower() for keyword in ['because', 'reason', 'rationale', 'justify', 'why'])
    checks.append({
        "name": "Decision rationale explained",
        "passed": has_rationale,
        "detail": "Document explains reasoning behind the decision" if has_rationale else "Missing explanation of decision rationale"
    })
    
    # Check 6: Document addresses constraints/risks
    has_constraints = any(keyword in doc_content.lower() for keyword in ['risk', 'constraint', 'timeline', 'resource', 'cost', 'complexity'])
    checks.append({
        "name": "Constraints and risks addressed",
        "passed": has_constraints,
        "detail": "Document discusses constraints, risks, or implementation challenges" if has_constraints else "Missing discussion of constraints or risks"
    })
    
    # Check 7: Document is structured (has headers/sections)
    has_structure = doc_content.count('#') >= 3 or doc_content.count('\n\n') >= 5
    checks.append({
        "name": "Document is well-structured",
        "passed": has_structure,
        "detail": "Document uses headers and clear sections" if has_structure else "Document lacks clear structure"
    })
    
    # Calculate score
    passed_count = sum(1 for check in checks if check['passed'])
    score = passed_count / len(checks)
    
    return {
        "passed": score >= 0.8,
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '/workspace'
    result = evaluate(workspace)
    print(json.dumps(result))
