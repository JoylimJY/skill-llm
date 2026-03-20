#!/usr/bin/env python3
import os
import sys
import json
import re
from pathlib import Path

def check_doc_exists_and_structured(workspace_dir):
    """Check if a well-structured decision document was created"""
    doc_files = list(Path(workspace_dir).glob('*.md'))
    doc_files.extend(list(Path(workspace_dir).glob('decision-doc*')))
    doc_files.extend(list(Path(workspace_dir).glob('*decision*')))
    doc_files.extend(list(Path(workspace_dir).glob('*migration*')))
    
    if not doc_files:
        return False, 'No decision document found', ''
    
    # Find the most likely decision doc (largest .md file)
    main_doc = max(doc_files, key=lambda f: f.stat().st_size if f.suffix == '.md' else 0)
    
    try:
        content = main_doc.read_text()
        if len(content) < 1000:  # Too short for a comprehensive doc
            return False, f'Document too short: {len(content)} chars', content
        return True, f'Found document: {main_doc.name}', content
    except:
        return False, 'Could not read document', ''

def check_context_integration(content):
    """Verify the document integrates context from input files"""
    markers_found = []
    context_markers = [
        ('MARKER_INCIDENT_DB_CONNECTIONS', 'database connection incidents'),
        ('MARKER_INCIDENT_DEPLOYMENT_COUPLING', 'deployment coupling issues'),
        ('MARKER_INCIDENT_SCALABILITY_WALL', 'scalability problems'),
        ('MARKER_TEAM_CAPACITY_DATA', 'team capacity constraints'),
        ('MARKER_COMPLIANCE_CONSTRAINTS', 'compliance requirements'),
        ('MARKER_BUSINESS_CONSTRAINTS', 'business limitations')
    ]
    
    # Check for references to context (not literal markers)
    context_integration_score = 0
    details = []
    
    if 'database connection' in content.lower() or 'connection pool' in content.lower():
        context_integration_score += 1
        details.append('References database scaling issues')
    
    if 'deployment' in content.lower() and ('rollback' in content.lower() or 'coupling' in content.lower()):
        context_integration_score += 1
        details.append('Addresses deployment coupling problems')
        
    if 'team' in content.lower() and ('capacity' in content.lower() or 'experience' in content.lower()):
        context_integration_score += 1
        details.append('Considers team constraints')
        
    if 'pci' in content.lower() or 'compliance' in content.lower():
        context_integration_score += 1
        details.append('Addresses compliance requirements')
        
    if 'budget' in content.lower() or '$500k' in content or 'cost' in content.lower():
        context_integration_score += 1
        details.append('Considers budget constraints')
    
    passed = context_integration_score >= 3
    detail = f'Integrated {context_integration_score}/5 context areas: {details}'
    return passed, detail

def check_decision_doc_structure(content):
    """Check if document follows decision doc best practices"""
    required_sections = [
        (r'(problem|context|background)', 'Problem/Context section'),
        (r'(decision|proposal|approach|solution)', 'Decision/Proposal section'),
        (r'(alternative|option|consideration)', 'Alternatives section'),
        (r'(risk|concern|challenge)', 'Risks/Concerns section'),
        (r'(timeline|plan|phase|implementation)', 'Implementation plan')
    ]
    
    sections_found = []
    for pattern, description in required_sections:
        if re.search(pattern, content, re.IGNORECASE):
            sections_found.append(description)
    
    passed = len(sections_found) >= 4
    detail = f'Found {len(sections_found)}/5 expected sections: {sections_found}'
    return passed, detail

def check_technical_depth(content):
    """Verify document has appropriate technical depth for architecture decision"""
    technical_elements = [
        ('microservice', 'microservices architecture'),
        ('service', 'service boundaries'),
        ('database', 'data architecture'),
        ('api', 'API design'),
        ('migration', 'migration strategy'),
        ('scalability', 'scalability considerations'),
        ('infrastructure', 'infrastructure planning')
    ]
    
    elements_found = []
    for term, description in technical_elements:
        if term in content.lower():
            elements_found.append(description)
    
    # Check for specific technical details
    has_specifics = any([
        'phase' in content.lower(),
        'service' in content.lower() and 'boundary' in content.lower(),
        'q1' in content.lower() or 'q2' in content.lower(),
        'order' in content.lower() and 'service' in content.lower()
    ])
    
    passed = len(elements_found) >= 5 and has_specifics
    detail = f'Technical elements: {len(elements_found)}/7, Has specifics: {has_specifics}'
    return passed, detail

def check_stakeholder_focus(content):
    """Check if document is appropriately focused for engineering leadership"""
    leadership_elements = [
        'impact' in content.lower(),
        'risk' in content.lower(),
        'timeline' in content.lower(),
        'resource' in content.lower() or 'team' in content.lower(),
        'cost' in content.lower() or 'budget' in content.lower(),
        'business' in content.lower(),
    ]
    
    elements_count = sum(leadership_elements)
    
    # Check for decision-oriented language
    has_decision_language = any([
        'recommend' in content.lower(),
        'propose' in content.lower(),
        'decision' in content.lower(),
        'approach' in content.lower()
    ])
    
    passed = elements_count >= 4 and has_decision_language
    detail = f'Leadership focus elements: {elements_count}/6, Has decision language: {has_decision_language}'
    return passed, detail

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script <workspace_dir>"}]}))
        return
    
    workspace_dir = sys.argv[1]
    checks = []
    
    # Check 1: Document exists and is substantial
    doc_exists, doc_detail, content = check_doc_exists_and_structured(workspace_dir)
    checks.append({
        "name": "document_creation",
        "passed": doc_exists,
        "detail": doc_detail
    })
    
    if not doc_exists:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return
    
    # Check 2: Context integration
    context_passed, context_detail = check_context_integration(content)
    checks.append({
        "name": "context_integration",
        "passed": context_passed,
        "detail": context_detail
    })
    
    # Check 3: Decision document structure
    structure_passed, structure_detail = check_decision_doc_structure(content)
    checks.append({
        "name": "decision_doc_structure",
        "passed": structure_passed,
        "detail": structure_detail
    })
    
    # Check 4: Technical depth appropriate for architecture decision
    tech_passed, tech_detail = check_technical_depth(content)
    checks.append({
        "name": "technical_depth",
        "passed": tech_passed,
        "detail": tech_detail
    })
    
    # Check 5: Stakeholder-appropriate content
    stakeholder_passed, stakeholder_detail = check_stakeholder_focus(content)
    checks.append({
        "name": "stakeholder_focus",
        "passed": stakeholder_passed,
        "detail": stakeholder_detail
    })
    
    # Calculate overall score
    passed_count = sum(1 for check in checks if check["passed"])
    total_checks = len(checks)
    score = passed_count / total_checks
    overall_passed = score >= 0.8  # Need 4/5 checks to pass
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()