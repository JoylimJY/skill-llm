import os
import sys
import json
import re
from pathlib import Path

def evaluate_doc_coauthoring(workspace_dir):
    checks = []
    score = 0.0
    
    # Check if a technical design document was created
    doc_files = list(Path(workspace_dir).glob('*.md'))
    doc_files = [f for f in doc_files if 'template_hint' not in f.name and f.stat().st_size > 1000]
    
    if not doc_files:
        checks.append({"name": "document_created", "passed": False, "detail": "No substantial markdown document found"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    main_doc = max(doc_files, key=lambda f: f.stat().st_size)
    content = main_doc.read_text()
    
    checks.append({"name": "document_created", "passed": True, "detail": f"Found document: {main_doc.name}"})
    score += 0.15
    
    # Check for structured sections typical of technical design docs
    required_sections = [
        (r'(?i)(overview|introduction|summary)', 'overview_section'),
        (r'(?i)(architecture|design)', 'architecture_section'), 
        (r'(?i)(implementation|technical details)', 'implementation_section'),
        (r'(?i)(configuration|usage)', 'configuration_section'),
        (r'(?i)(migration|deployment)', 'migration_section')
    ]
    
    sections_found = 0
    for pattern, check_name in required_sections:
        if re.search(pattern, content):
            checks.append({"name": check_name, "passed": True, "detail": "Section found"})
            sections_found += 1
            score += 0.12
        else:
            checks.append({"name": check_name, "passed": False, "detail": "Section missing"})
    
    # Check for Redis-specific content
    redis_indicators = ['redis', 'cluster', 'fallback', 'in-memory']
    redis_mentions = sum(1 for indicator in redis_indicators if indicator.lower() in content.lower())
    
    if redis_mentions >= 3:
        checks.append({"name": "redis_content", "passed": True, "detail": f"Found {redis_mentions} Redis-related terms"})
        score += 0.15
    else:
        checks.append({"name": "redis_content", "passed": False, "detail": f"Only {redis_mentions} Redis-related terms found"})
    
    # Check for rate limiting specifics
    rate_limit_terms = ['rate limit', 'requests per second', 'throttling', 'quota', 'window']
    rate_limit_mentions = sum(1 for term in rate_limit_terms if term.lower() in content.lower())
    
    if rate_limit_mentions >= 2:
        checks.append({"name": "rate_limiting_content", "passed": True, "detail": f"Found {rate_limit_mentions} rate limiting terms"})
        score += 0.1
    else:
        checks.append({"name": "rate_limiting_content", "passed": False, "detail": f"Only {rate_limit_mentions} rate limiting terms"})
    
    # Check document length and structure quality
    word_count = len(content.split())
    header_count = len(re.findall(r'^#+', content, re.MULTILINE))
    
    if word_count >= 800:
        checks.append({"name": "sufficient_detail", "passed": True, "detail": f"Document has {word_count} words"})
        score += 0.1
    else:
        checks.append({"name": "sufficient_detail", "passed": False, "detail": f"Document only has {word_count} words"})
    
    if header_count >= 5:
        checks.append({"name": "well_structured", "passed": True, "detail": f"Document has {header_count} headers"})
        score += 0.08
    else:
        checks.append({"name": "well_structured", "passed": False, "detail": f"Document has only {header_count} headers"})
    
    # Check for technical depth (code examples, configs, etc.)
    technical_indicators = ['```', 'code', 'config', 'yaml', 'json', 'endpoint', 'API']
    tech_score = sum(1 for indicator in technical_indicators if indicator in content)
    
    if tech_score >= 3:
        checks.append({"name": "technical_depth", "passed": True, "detail": f"Found {tech_score} technical elements"})
        score += 0.1
    else:
        checks.append({"name": "technical_depth", "passed": False, "detail": f"Only {tech_score} technical elements found"})
    
    passed = score >= 0.7
    return {"passed": passed, "score": min(1.0, score), "checks": checks}

if __name__ == "__main__":
    result = evaluate_doc_coauthoring(sys.argv[1])
    print(json.dumps(result))