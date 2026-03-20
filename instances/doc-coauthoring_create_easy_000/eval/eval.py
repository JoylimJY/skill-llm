#!/usr/bin/env python3

import sys
import os
import json
import re
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Need workspace path"}]}))
        return
    
    workspace = Path(sys.argv[1])
    checks = []
    score = 0.0
    
    # Load expected markers
    markers_file = workspace / 'expected_markers.json'
    if markers_file.exists():
        with open(markers_file) as f:
            markers = json.load(f)
    else:
        checks.append({"name": "markers_file", "passed": False, "detail": "Expected markers file not found"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    # Look for decision document file
    doc_files = list(workspace.glob('*.md'))
    decision_doc = None
    
    for doc_file in doc_files:
        if 'decision' in doc_file.name.lower() or 'graphql' in doc_file.name.lower():
            decision_doc = doc_file
            break
    
    if not decision_doc:
        decision_doc = next((f for f in doc_files if f.name != 'decision_doc_template.md'), None)
    
    if decision_doc:
        checks.append({"name": "document_created", "passed": True, "detail": f"Found document: {decision_doc.name}"})
        score += 0.3
        
        # Read document content
        with open(decision_doc) as f:
            content = f.read()
        
        # Check for topic keywords
        topic_found = 0
        for keyword in markers['topic_keywords']:
            if keyword.lower() in content.lower():
                topic_found += 1
        
        if topic_found >= 3:
            checks.append({"name": "topic_content", "passed": True, "detail": f"Found {topic_found}/4 expected keywords"})
            score += 0.2
        else:
            checks.append({"name": "topic_content", "passed": False, "detail": f"Only found {topic_found}/4 expected keywords"})
        
        # Check for structured sections
        sections_found = 0
        for section in markers['expected_sections']:
            if section.lower() in content.lower() or section.replace(' ', '').lower() in content.lower():
                sections_found += 1
        
        if sections_found >= 6:
            checks.append({"name": "document_structure", "passed": True, "detail": f"Found {sections_found}/8 expected sections"})
            score += 0.2
        else:
            checks.append({"name": "document_structure", "passed": False, "detail": f"Only found {sections_found}/8 expected sections"})
        
        # Check for substantial content (not just placeholders)
        non_placeholder_content = content.replace('[', '').replace(']', '')
        substantial_paragraphs = len([p for p in non_placeholder_content.split('\n\n') if len(p.strip()) > 50])
        
        if substantial_paragraphs >= 4:
            checks.append({"name": "content_depth", "passed": True, "detail": f"Found {substantial_paragraphs} substantial content paragraphs"})
            score += 0.2
        else:
            checks.append({"name": "content_depth", "passed": False, "detail": f"Only {substantial_paragraphs} substantial content paragraphs"})
        
        # Check for decision-specific content
        decision_indicators = ['decision', 'recommend', 'propose', 'choose', 'select']
        decision_content = any(indicator in content.lower() for indicator in decision_indicators)
        
        if decision_content:
            checks.append({"name": "decision_content", "passed": True, "detail": "Document contains decision-making language"})
            score += 0.1
        else:
            checks.append({"name": "decision_content", "passed": False, "detail": "Document lacks clear decision-making language"})
        
    else:
        checks.append({"name": "document_created", "passed": False, "detail": "No decision document found"})
    
    passed = score >= 0.6
    
    result = {
        "passed": passed,
        "score": min(1.0, score),
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()