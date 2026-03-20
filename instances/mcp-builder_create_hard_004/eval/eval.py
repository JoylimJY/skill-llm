#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import importlib.util
import asyncio

def check_file_exists(workspace_dir, filename):
    """Check if a file exists in the workspace."""
    filepath = Path(workspace_dir) / filename
    return filepath.exists(), str(filepath)

def check_python_syntax(filepath):
    """Check if Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            compile(f.read(), filepath, 'exec')
        return True, 'Valid Python syntax'
    except SyntaxError as e:
        return False, f'Syntax error: {e}'
    except Exception as e:
        return False, f'Error reading file: {e}'

def check_mcp_imports(filepath):
    """Check if file contains required MCP imports."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        required_imports = [
            'from mcp.server.fastmcp import FastMCP',
            'from pydantic import BaseModel'
        ]
        
        missing = []
        for imp in required_imports:
            if imp not in content:
                missing.append(imp)
        
        if missing:
            return False, f'Missing imports: {missing}'
        
        return True, 'All required imports present'
    except Exception as e:
        return False, f'Error checking imports: {e}'

def check_tool_definitions(filepath):
    """Check if file contains required Reddit tool definitions."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        required_tools = [
            '@mcp.tool',
            'reddit_search_posts',
            'reddit_get_subreddit', 
            'reddit_get_comments'
        ]
        
        missing = []
        for tool in required_tools:
            if tool not in content:
                missing.append(tool)
        
        if missing:
            return False, f'Missing required elements: {missing}'
            
        return True, 'All required tools defined'
    except Exception as e:
        return False, f'Error checking tools: {e}'

def check_pydantic_models(filepath):
    """Check if file contains Pydantic models for input validation."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Look for Pydantic model patterns
        model_indicators = [
            'class.*BaseModel',
            'Field(',
            'model_config',
        ]
        
        found_models = []
        for indicator in model_indicators:
            import re
            if re.search(indicator, content):
                found_models.append(indicator)
        
        if len(found_models) < 2:  # Should have at least class and Field usage
            return False, f'Insufficient Pydantic model usage. Found: {found_models}'
            
        return True, f'Pydantic models properly defined. Found: {found_models}'
    except Exception as e:
        return False, f'Error checking Pydantic models: {e}'

def check_response_formats(filepath):
    """Check if file supports both JSON and markdown response formats."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        format_indicators = [
            'ResponseFormat',
            'MARKDOWN',
            'JSON',
            'response_format'
        ]
        
        missing = []
        for indicator in format_indicators:
            if indicator not in content:
                missing.append(indicator)
                
        if missing:
            return False, f'Missing response format support: {missing}'
            
        return True, 'Both JSON and Markdown formats supported'
    except Exception as e:
        return False, f'Error checking response formats: {e}'

def check_pagination_support(filepath):
    """Check if file implements pagination."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        pagination_indicators = [
            'limit',
            'offset',
            'has_more',
            'next_offset'
        ]
        
        found = 0
        for indicator in pagination_indicators:
            if indicator in content:
                found += 1
                
        if found < 3:  # Should have at least 3 pagination elements
            return False, f'Insufficient pagination support. Found {found}/4 indicators'
            
        return True, f'Pagination properly implemented. Found {found}/4 indicators'
    except Exception as e:
        return False, f'Error checking pagination: {e}'

def check_error_handling(filepath):
    """Check if file has proper error handling."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        error_indicators = [
            'try:',
            'except',
            'Error:',
            '_handle_api_error'
        ]
        
        found = 0
        for indicator in error_indicators:
            if indicator in content:
                found += 1
                
        if found < 3:
            return False, f'Insufficient error handling. Found {found}/4 indicators'
            
        return True, f'Error handling implemented. Found {found}/4 indicators'
    except Exception as e:
        return False, f'Error checking error handling: {e}'

def check_evaluation_file(workspace_dir):
    """Check if evaluation file exists and has proper structure."""
    eval_path = None
    for filename in ['evaluation.xml', 'reddit_evaluation.xml', 'evaluations.xml']:
        if (Path(workspace_dir) / filename).exists():
            eval_path = Path(workspace_dir) / filename
            break
            
    if not eval_path:
        return False, 'No evaluation XML file found'
        
    try:
        tree = ET.parse(eval_path)
        root = tree.getroot()
        
        if root.tag != 'evaluation':
            return False, f'Root element should be <evaluation>, found <{root.tag}>'
            
        qa_pairs = root.findall('qa_pair')
        if len(qa_pairs) < 5:  # Should have at least 5 questions for complexity
            return False, f'Should have at least 5 questions, found {len(qa_pairs)}'
            
        # Check each qa_pair has question and answer
        for i, qa_pair in enumerate(qa_pairs):
            question = qa_pair.find('question')
            answer = qa_pair.find('answer')
            
            if question is None:
                return False, f'QA pair {i+1} missing <question> element'
            if answer is None:
                return False, f'QA pair {i+1} missing <answer> element'
                
            if not question.text or not question.text.strip():
                return False, f'QA pair {i+1} has empty question'
            if not answer.text or not answer.text.strip():
                return False, f'QA pair {i+1} has empty answer'
                
        return True, f'Evaluation file properly structured with {len(qa_pairs)} questions'
        
    except ET.ParseError as e:
        return False, f'Invalid XML format: {e}'
    except Exception as e:
        return False, f'Error parsing evaluation file: {e}'

def check_evaluation_content_quality(workspace_dir):
    """Check if evaluation questions are complex and realistic."""
    eval_path = None
    for filename in ['evaluation.xml', 'reddit_evaluation.xml', 'evaluations.xml']:
        if (Path(workspace_dir) / filename).exists():
            eval_path = Path(workspace_dir) / filename
            break
            
    if not eval_path:
        return False, 'No evaluation file to check'
        
    try:
        tree = ET.parse(eval_path)
        root = tree.getroot()
        qa_pairs = root.findall('qa_pair')
        
        complex_indicators = [
            'Find', 'Search', 'Which', 'How many', 'What was', 'Among',
            'highest', 'most', 'created in', 'between', 'during'
        ]
        
        reddit_specific = [
            'subreddit', 'post', 'comment', 'score', 'author', 'upvote'
        ]
        
        complex_count = 0
        reddit_count = 0
        
        for qa_pair in qa_pairs:
            question_text = qa_pair.find('question').text.lower()
            
            # Check for complexity indicators
            if any(indicator.lower() in question_text for indicator in complex_indicators):
                complex_count += 1
                
            # Check for Reddit-specific content
            if any(term in question_text for term in reddit_specific):
                reddit_count += 1
                
        if complex_count < 3:
            return False, f'Questions not complex enough. Only {complex_count} questions show complexity'
            
        if reddit_count < 4:
            return False, f'Questions not Reddit-specific enough. Only {reddit_count} mention Reddit concepts'
            
        return True, f'Questions are appropriately complex and Reddit-focused ({complex_count} complex, {reddit_count} Reddit-specific)'
        
    except Exception as e:
        return False, f'Error analyzing evaluation content: {e}'

def check_marker_content_verification(workspace_dir):
    """Check if server implementation can find marker content from mock data."""
    try:
        # Load the mock data that was generated
        mock_data_path = Path(workspace_dir) / 'mock_reddit_data.json'
        if not mock_data_path.exists():
            return False, 'Mock data file not found'
            
        with open(mock_data_path, 'r') as f:
            mock_data = json.load(f)
            
        # Check that mock data contains our verification markers
        markers_found = []
        
        for post in mock_data.get('posts', []):
            if 'MARKER_' in post.get('title', '') or 'VERIFICATION_MARKER_' in post.get('selftext', ''):
                markers_found.append(f"Post: {post.get('id')}")
                
        for comment in mock_data.get('comments', []):
            if 'VERIFICATION_MARKER_' in comment.get('body', ''):
                markers_found.append(f"Comment: {comment.get('id')}")
                
        if len(markers_found) < 3:
            return False, f'Insufficient marker content found. Only {len(markers_found)} items with markers'
            
        return True, f'Mock data properly contains verification markers in {len(markers_found)} items'
        
    except Exception as e:
        return False, f'Error checking marker content: {e}'

def run_evaluation(workspace_dir):
    """Run all evaluation checks."""
    checks = []
    
    # Check for main server file
    server_files = ['reddit_mcp.py', 'reddit_mcp_server.py', 'main.py']
    server_file = None
    for filename in server_files:
        exists, filepath = check_file_exists(workspace_dir, filename)
        if exists:
            server_file = filepath
            break
            
    if server_file:
        checks.append({
            'name': 'Server file exists',
            'passed': True,
            'detail': f'Found server file: {os.path.basename(server_file)}'
        })
        
        # Check Python syntax
        passed, detail = check_python_syntax(server_file)
        checks.append({
            'name': 'Python syntax valid',
            'passed': passed,
            'detail': detail
        })
        
        # Check MCP imports
        passed, detail = check_mcp_imports(server_file)
        checks.append({
            'name': 'MCP imports present',
            'passed': passed,
            'detail': detail
        })
        
        # Check tool definitions
        passed, detail = check_tool_definitions(server_file)
        checks.append({
            'name': 'Reddit tools defined',
            'passed': passed,
            'detail': detail
        })
        
        # Check Pydantic models
        passed, detail = check_pydantic_models(server_file)
        checks.append({
            'name': 'Pydantic models implemented',
            'passed': passed,
            'detail': detail
        })
        
        # Check response formats
        passed, detail = check_response_formats(server_file)
        checks.append({
            'name': 'Response formats supported',
            'passed': passed,
            'detail': detail
        })
        
        # Check pagination
        passed, detail = check_pagination_support(server_file)
        checks.append({
            'name': 'Pagination implemented',
            'passed': passed,
            'detail': detail
        })
        
        # Check error handling
        passed, detail = check_error_handling(server_file)
        checks.append({
            'name': 'Error handling implemented',
            'passed': passed,
            'detail': detail
        })
        
    else:
        checks.append({
            'name': 'Server file exists',
            'passed': False,
            'detail': f'No server file found. Expected one of: {server_files}'
        })
    
    # Check evaluation file
    passed, detail = check_evaluation_file(workspace_dir)
    checks.append({
        'name': 'Evaluation file structure',
        'passed': passed,
        'detail': detail
    })
    
    # Check evaluation content quality
    passed, detail = check_evaluation_content_quality(workspace_dir)
    checks.append({
        'name': 'Evaluation questions quality',
        'passed': passed,
        'detail': detail
    })
    
    # Check marker content
    passed, detail = check_marker_content_verification(workspace_dir)
    checks.append({
        'name': 'Mock data verification markers',
        'passed': passed,
        'detail': detail
    })
    
    # Calculate overall score
    total_checks = len(checks)
    passed_checks = sum(1 for check in checks if check['passed'])
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Overall pass requires most critical checks
    critical_checks = ['Server file exists', 'Python syntax valid', 'MCP imports present', 
                      'Reddit tools defined', 'Evaluation file structure']
    critical_passed = sum(1 for check in checks 
                         if check['name'] in critical_checks and check['passed'])
    
    overall_passed = (critical_passed == len(critical_checks)) and (score >= 0.7)
    
    return {
        'passed': overall_passed,
        'score': score,
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({
            'passed': False,
            'score': 0.0,
            'checks': [{
                'name': 'Argument validation',
                'passed': False,
                'detail': 'Usage: eval_script <workspace_directory>'
            }]
        }))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = run_evaluation(workspace_dir)
    print(json.dumps(result, indent=2))