import sys
import os
import json
import re

def check_rfc_document(workspace_path):
    checks = []
    score = 0.0
    
    # Look for RFC document files
    rfc_files = []
    for file in os.listdir(workspace_path):
        if file.endswith(('.md', '.txt')) and any(keyword in file.lower() for keyword in ['rfc', 'proposal', 'auth', 'migration']):
            rfc_files.append(file)
    
    if not rfc_files:
        checks.append({"name": "RFC document exists", "passed": False, "detail": "No RFC document found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Read the main RFC document
    rfc_file = rfc_files[0]
    try:
        with open(os.path.join(workspace_path, rfc_file), 'r') as f:
            content = f.read().lower()
    except Exception as e:
        checks.append({"name": "RFC document readable", "passed": False, "detail": f"Could not read {rfc_file}: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "RFC document exists", "passed": True, "detail": f"Found RFC document: {rfc_file}"})
    score += 0.15
    
    # Check for essential RFC sections
    required_sections = [
        (r'(problem|background|motivation|current)', 'Problem/Background section'),
        (r'(proposal|solution|approach)', 'Proposal/Solution section'),
        (r'(implementation|migration|plan)', 'Implementation section'),
        (r'(security|risk)', 'Security considerations'),
        (r'(timeline|schedule)', 'Timeline section')
    ]
    
    for pattern, section_name in required_sections:
        if re.search(pattern, content):
            checks.append({"name": f"{section_name} present", "passed": True, "detail": f"Found {section_name.lower()}"})
            score += 0.1
        else:
            checks.append({"name": f"{section_name} present", "passed": False, "detail": f"Missing {section_name.lower()}"})
    
    # Check for key technical concepts
    technical_concepts = [
        ('jwt', 'JWT mentioned'),
        ('session', 'Session-based auth mentioned'),
        ('redis', 'Redis discussed'),
        ('token', 'Token concepts addressed'),
        ('expir', 'Token expiration issues addressed')
    ]
    
    for concept, description in technical_concepts:
        if concept in content:
            checks.append({"name": description, "passed": True, "detail": f"Document addresses {concept}"})
            score += 0.05
        else:
            checks.append({"name": description, "passed": False, "detail": f"Missing discussion of {concept}"})
    
    # Check for audience considerations
    audience_terms = ['engineer', 'security', 'lead', 'team', 'mobile', 'frontend']
    audience_found = any(term in content for term in audience_terms)
    if audience_found:
        checks.append({"name": "Audience awareness", "passed": True, "detail": "Document shows awareness of target audience"})
        score += 0.1
    else:
        checks.append({"name": "Audience awareness", "passed": False, "detail": "Document lacks audience considerations"})
    
    # Check document length (should be substantial)
    word_count = len(content.split())
    if word_count >= 300:
        checks.append({"name": "Sufficient detail", "passed": True, "detail": f"Document has {word_count} words"})
        score += 0.1
    else:
        checks.append({"name": "Sufficient detail", "passed": False, "detail": f"Document too brief: {word_count} words"})
    
    # Check for structured formatting
    has_structure = bool(re.search(r'(#|\*|1\.|\-)', content))
    if has_structure:
        checks.append({"name": "Structured formatting", "passed": True, "detail": "Document uses structured formatting"})
        score += 0.05
    else:
        checks.append({"name": "Structured formatting", "passed": False, "detail": "Document lacks structured formatting"})
    
    # Overall pass threshold
    passed = score >= 0.6
    
    return {"passed": passed, "score": min(1.0, score), "checks": checks}

if __name__ == "__main__":
    workspace_path = sys.argv[1]
    result = check_rfc_document(workspace_path)
    print(json.dumps(result))