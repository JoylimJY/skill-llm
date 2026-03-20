#!/usr/bin/env python3
import sys
import os
import json
import glob
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_path>"}]}))
        return
    
    workspace = sys.argv[1]
    checks = []
    
    # Check if any document was created (markdown files or similar)
    doc_files = list(Path(workspace).glob('*.md')) + list(Path(workspace).glob('*.txt')) + list(Path(workspace).glob('*design*')) + list(Path(workspace).glob('*spec*')) + list(Path(workspace).glob('*doc*'))
    
    doc_created = len(doc_files) > 0
    checks.append({
        "name": "document_created", 
        "passed": doc_created,
        "detail": f"Found {len(doc_files)} document files: {[f.name for f in doc_files]}"
    })
    
    if not doc_created:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    # Read the main document content
    main_doc = max(doc_files, key=lambda f: f.stat().st_size)
    try:
        content = main_doc.read_text().lower()
    except:
        content = ""
    
    # Check for key sections that should be in a technical design doc
    sections_found = 0
    section_checks = [
        ("overview", any(word in content for word in ["overview", "summary", "introduction", "background"])),
        ("api_endpoint", any(word in content for word in ["endpoint", "api", "/users", "post", "preferences"])),
        ("implementation", any(word in content for word in ["implementation", "design", "approach", "architecture"])),
        ("security", any(word in content for word in ["security", "authentication", "auth", "token"])),
        ("performance", any(word in content for word in ["performance", "response time", "latency"]))
    ]
    
    for section_name, found in section_checks:
        checks.append({
            "name": f"section_{section_name}",
            "passed": found,
            "detail": f"Section {section_name} {'found' if found else 'missing'} in document"
        })
        if found:
            sections_found += 1
    
    # Check document length (should be substantial)
    word_count = len(content.split())
    substantial_content = word_count > 100
    checks.append({
        "name": "substantial_content",
        "passed": substantial_content,
        "detail": f"Document has {word_count} words"
    })
    
    # Check for structured content (headers, sections)
    has_structure = any(marker in content for marker in ['#', '##', '###', '1.', '2.', '*', '-'])
    checks.append({
        "name": "structured_content",
        "passed": has_structure,
        "detail": "Document appears to have structured formatting"
    })
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Overall pass requires: document created, at least 3 sections, substantial content
    overall_pass = doc_created and sections_found >= 3 and substantial_content
    
    print(json.dumps({
        "passed": overall_pass,
        "score": score,
        "checks": checks
    }))

if __name__ == "__main__":
    main()