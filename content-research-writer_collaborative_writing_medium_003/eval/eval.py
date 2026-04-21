#!/usr/bin/env python3
import sys
import os
import glob
import json
import re
from typing import Dict, List, Tuple

def safe_read_file(filepath: str) -> str:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ""

def check_outline_structure(content: str) -> Tuple[bool, str]:
    content_lower = content.lower()
    
    # Check for outline indicators
    has_outline_title = any(marker in content_lower for marker in ['outline', 'structure', 'future of remote', 'remote team collaboration'])
    
    # Count main sections (flexible patterns)
    section_patterns = [
        r'#{1,3}\s*[^#\n]+',  # Markdown headers
        r'^\s*\d+\.\s*[^\n]+',  # Numbered lists
        r'^\s*[-*]\s*[^\n]+.*:',  # Bullet points with colons
        r'^[A-Z][^\n]*:',  # Title case sections with colons
    ]
    
    sections_found = 0
    for pattern in section_patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
        sections_found = max(sections_found, len(matches))
    
    has_enough_sections = sections_found >= 5
    
    # Check for research gaps indicators
    research_indicators = ['research needed', 'research gap', 'to-do', 'find data', 'source needed', 'citation needed', 'needs research']
    has_research_gaps = any(indicator in content_lower for indicator in research_indicators)
    
    details = f"Found {sections_found} sections, research gaps: {has_research_gaps}"
    success = has_outline_title and has_enough_sections and has_research_gaps
    
    return success, details

def check_research_content(content: str) -> Tuple[bool, str]:
    content_lower = content.lower()
    
    # Check for research title/header
    has_research_header = any(marker in content_lower for marker in ['research', 'findings', 'statistics', 'data'])
    
    # Look for statistics/numbers
    number_pattern = r'\d+%|\d+\.\d+%|\d+x|\d+ times|\d+\.\d+ times'
    stats_found = len(re.findall(number_pattern, content, re.IGNORECASE))
    has_enough_stats = stats_found >= 3
    
    # Look for citations/sources
    citation_patterns = [
        r'\[\d+\]',  # [1] style
        r'\([^)]*20\d{2}[^)]*\)',  # (Author, 2024) style
        r'source:|citation:|reference:',  # Explicit source labels
        r'according to',  # Attribution phrases
        r'study shows|research shows|survey finds'
    ]
    
    citations_found = 0
    for pattern in citation_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        citations_found += len(matches)
    
    has_citations = citations_found >= 3
    
    details = f"Found {stats_found} statistics, {citations_found} citation indicators"
    success = has_research_header and has_enough_stats and has_citations
    
    return success, details

def check_hook_improvements(content: str) -> Tuple[bool, str]:
    content_lower = content.lower()
    
    # Check for hook-related content
    has_hook_header = any(marker in content_lower for marker in ['hook', 'introduction', 'opening', 'improved'])
    
    # Count distinct options/alternatives
    option_patterns = [
        r'option\s*\d+',
        r'alternative\s*\d+',
        r'version\s*\d+',
        r'^\s*\d+\.',
        r'\*\*option',
        r'hook\s*\d+'
    ]
    
    options_found = 0
    for pattern in option_patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
        options_found = max(options_found, len(matches))
    
    # Also check for multiple quoted examples
    quote_pattern = r'[>"].*?[>"]'
    quoted_examples = len(re.findall(quote_pattern, content, re.DOTALL))
    options_found = max(options_found, quoted_examples)
    
    has_enough_options = options_found >= 3
    
    # Check for explanations
    explanation_indicators = ['why it works', 'explanation', 'because', 'this works by', 'effective because']
    has_explanations = any(indicator in content_lower for indicator in explanation_indicators)
    
    details = f"Found {options_found} hook options, explanations: {has_explanations}"
    success = has_hook_header and has_enough_options and has_explanations
    
    return success, details

def find_best_file(pattern: str, check_func) -> Tuple[bool, str, str]:
    """Find the best matching file for a given pattern and evaluation function"""
    files = glob.glob(pattern)
    if not files:
        return False, f"No files matching {pattern} found", ""
    
    best_score = False
    best_detail = "No valid content found"
    best_file = ""
    
    for file_path in files:
        content = safe_read_file(file_path)
        if content.strip():
            success, detail = check_func(content)
            if success or not best_score:  # Keep the first success or best attempt
                best_score = success
                best_detail = detail
                best_file = file_path
            if success:
                break  # Found a good match, stop searching
    
    return best_score, best_detail, best_file

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Missing workspace path"}]}))
        return
    
    workspace = sys.argv[1]
    os.chdir(workspace)
    
    checks = []
    
    # Check for outline.md
    outline_success, outline_detail, outline_file = find_best_file("*outline*.md", check_outline_structure)
    checks.append({
        "name": "outline_structure",
        "passed": outline_success,
        "detail": f"Outline check ({outline_file}): {outline_detail}"
    })
    
    # Check for research.md
    research_success, research_detail, research_file = find_best_file("*research*.md", check_research_content)
    checks.append({
        "name": "research_content",
        "passed": research_success,
        "detail": f"Research check ({research_file}): {research_detail}"
    })
    
    # Check for hook_improvements.md
    hook_success, hook_detail, hook_file = find_best_file("*hook*.md", check_hook_improvements)
    checks.append({
        "name": "hook_improvements",
        "passed": hook_success,
        "detail": f"Hook improvements check ({hook_file}): {hook_detail}"
    })
    
    # Check file existence (basic requirement)
    required_files_exist = len([f for f in glob.glob("*.md") if safe_read_file(f).strip()]) >= 3
    checks.append({
        "name": "file_creation",
        "passed": required_files_exist,
        "detail": f"Found {len(glob.glob('*.md'))} markdown files with content"
    })
    
    # Calculate score
    passed_count = sum(1 for c in checks if c['passed'])
    total_count = len(checks)
    score = passed_count / total_count
    overall_passed = score >= 0.75  # Allow partial success for complex multi-file task
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()