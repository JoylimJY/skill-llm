#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import re
from pathlib import Path

def run_check(name, check_func):
    try:
        result = check_func()
        return {"name": name, "passed": result[0], "detail": result[1]}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Error: {str(e)}"}

def check_project_structure():
    """Check if the project has proper TypeScript MCP structure"""
    required_files = [
        'src/index.ts',
        'package.json',
        'tsconfig.json'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        return False, f"Missing required files: {', '.join(missing_files)}"
    return True, "Project structure is correct"

def check_typescript_compilation():
    """Check if TypeScript code compiles successfully"""
    try:
        result = subprocess.run(['npx', 'tsc'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"TypeScript compilation failed: {result.stderr}"
        
        if not os.path.exists('dist/index.js'):
            return False, "Compiled JavaScript file not found at dist/index.js"
        
        return True, "TypeScript compilation successful"
    except Exception as e:
        return False, f"Compilation check failed: {str(e)}"

def check_mcp_server_implementation():
    """Check if the MCP server is properly implemented"""
    index_file = 'src/index.ts'
    if not os.path.exists(index_file):
        return False, "src/index.ts not found"
    
    with open(index_file, 'r') as f:
        content = f.read()
    
    required_imports = [
        '@modelcontextprotocol/sdk',
        'axios',
        'zod'
    ]
    
    missing_imports = []
    for imp in required_imports:
        if imp not in content:
            missing_imports.append(imp)
    
    if missing_imports:
        return False, f"Missing required imports: {', '.join(missing_imports)}"
    
    # Check for McpServer usage
    if 'McpServer' not in content:
        return False, "McpServer not found in implementation"
    
    # Check for server name following convention
    if 'hackernews-mcp-server' not in content and 'hackernews_mcp' not in content:
        return False, "Server name doesn't follow naming convention"
    
    return True, "MCP server implementation structure is correct"

def check_hackernews_tools():
    """Check if Hacker News specific tools are implemented"""
    index_file = 'src/index.ts'
    with open(index_file, 'r') as f:
        content = f.read()
    
    # Check for tool registration patterns
    if 'registerTool' not in content:
        return False, "No tool registration found"
    
    # Check for HN API related functionality
    hn_indicators = [
        'hacker', 'news', 'story', 'comment', 'search'
    ]
    
    found_indicators = []
    for indicator in hn_indicators:
        if indicator.lower() in content.lower():
            found_indicators.append(indicator)
    
    if len(found_indicators) < 3:
        return False, f"Insufficient HackerNews functionality. Found: {', '.join(found_indicators)}"
    
    # Check for proper tool naming with service prefix
    if 'hackernews_' not in content and 'hn_' not in content:
        return False, "Tools don't follow naming convention with service prefix"
    
    return True, f"HackerNews tools implemented with indicators: {', '.join(found_indicators)}"

def check_pagination_support():
    """Check if pagination is properly implemented"""
    index_file = 'src/index.ts'
    with open(index_file, 'r') as f:
        content = f.read()
    
    pagination_indicators = [
        'limit', 'offset', 'has_more', 'next_offset', 'total'
    ]
    
    found_pagination = []
    for indicator in pagination_indicators:
        if indicator in content:
            found_pagination.append(indicator)
    
    if len(found_pagination) < 3:
        return False, f"Insufficient pagination support. Found: {', '.join(found_pagination)}"
    
    return True, f"Pagination implemented with: {', '.join(found_pagination)}"

def check_zod_schemas():
    """Check if Zod schemas are used for input validation"""
    index_file = 'src/index.ts'
    with open(index_file, 'r') as f:
        content = f.read()
    
    zod_indicators = [
        'z.object', 'z.string', 'z.number', '.describe('
    ]
    
    found_zod = []
    for indicator in zod_indicators:
        if indicator in content:
            found_zod.append(indicator)
    
    if len(found_zod) < 2:
        return False, f"Insufficient Zod usage for input validation. Found: {', '.join(found_zod)}"
    
    return True, f"Zod schemas properly used: {', '.join(found_zod)}"

def check_evaluation_file():
    """Check if evaluation XML file is created"""
    xml_files = list(Path('.').glob('*.xml'))
    
    if not xml_files:
        return False, "No evaluation XML file found"
    
    eval_file = xml_files[0]
    with open(eval_file, 'r') as f:
        content = f.read()
    
    # Check for proper evaluation structure
    if '<evaluation>' not in content or '<qa_pair>' not in content:
        return False, "Evaluation file doesn't have proper XML structure"
    
    # Count qa_pairs
    qa_count = content.count('<qa_pair>')
    if qa_count < 5:
        return False, f"Insufficient evaluation questions. Found: {qa_count}, expected at least 5"
    
    # Check for HN-specific questions
    hn_terms = ['story', 'comment', 'hacker', 'news', 'score', 'author']
    found_terms = sum(1 for term in hn_terms if term.lower() in content.lower())
    
    if found_terms < 3:
        return False, f"Evaluation questions don't seem HackerNews-specific. Found terms: {found_terms}/6"
    
    return True, f"Evaluation file created with {qa_count} questions and HN-specific content"

def main(workspace_dir):
    os.chdir(workspace_dir)
    
    checks = [
        ("Project Structure", check_project_structure),
        ("TypeScript Compilation", check_typescript_compilation),
        ("MCP Server Implementation", check_mcp_server_implementation),
        ("HackerNews Tools", check_hackernews_tools),
        ("Pagination Support", check_pagination_support),
        ("Zod Input Validation", check_zod_schemas),
        ("Evaluation File", check_evaluation_file)
    ]
    
    results = []
    passed_count = 0
    
    for name, check_func in checks:
        result = run_check(name, check_func)
        results.append(result)
        if result['passed']:
            passed_count += 1
    
    score = passed_count / len(checks)
    passed = score >= 0.7  # Need to pass at least 70% of checks
    
    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": results
    }))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: eval_script.py <workspace_directory>")
        sys.exit(1)
    
    main(sys.argv[1])