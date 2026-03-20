import sys
import os
import json
import re
from pathlib import Path

def main(workspace_dir):
    workspace_path = Path(workspace_dir)
    checks = []
    
    # Load expected output configuration
    expected_file = workspace_path / 'expected_output.json'
    if not expected_file.exists():
        return {"passed": False, "score": 0.0, "checks": [{"name": "config_exists", "passed": False, "detail": "Expected output config missing"}]}
    
    with open(expected_file) as f:
        expected = json.load(f)
    
    # Check if main.py exists and has proper structure
    main_py = workspace_path / 'main.py'
    main_py_check = {
        "name": "main_py_exists",
        "passed": main_py.exists(),
        "detail": "main.py file exists" if main_py.exists() else "main.py file missing"
    }
    checks.append(main_py_check)
    
    if main_py.exists():
        with open(main_py) as f:
            main_content = f.read()
            
        # Check for Claude API usage
        anthropic_import = "import anthropic" in main_content or "from anthropic" in main_content
        anthropic_check = {
            "name": "uses_anthropic",
            "passed": anthropic_import,
            "detail": "Uses anthropic SDK" if anthropic_import else "Missing anthropic SDK usage"
        }
        checks.append(anthropic_check)
        
        # Check for adaptive thinking usage
        adaptive_thinking = 'thinking.*adaptive' in main_content or 'type.*adaptive' in main_content
        thinking_check = {
            "name": "uses_adaptive_thinking", 
            "passed": adaptive_thinking,
            "detail": "Uses adaptive thinking" if adaptive_thinking else "Missing adaptive thinking configuration"
        }
        checks.append(thinking_check)
        
        # Check for tool definitions (web_search, web_fetch, code_execution)
        has_web_search = 'web_search' in main_content
        has_web_fetch = 'web_fetch' in main_content  
        has_code_exec = 'code_execution' in main_content
        
        tools_check = {
            "name": "defines_required_tools",
            "passed": has_web_search and has_web_fetch and has_code_exec,
            "detail": f"Tools found - web_search: {has_web_search}, web_fetch: {has_web_fetch}, code_execution: {has_code_exec}"
        }
        checks.append(tools_check)
        
        # Check for proper model usage (claude-opus-4-6)
        correct_model = 'claude-opus-4-6' in main_content
        model_check = {
            "name": "uses_correct_model",
            "passed": correct_model,
            "detail": "Uses claude-opus-4-6 model" if correct_model else "Missing or incorrect model specification"
        }
        checks.append(model_check)
        
        # Check for error handling
        has_try_except = 'try:' in main_content and 'except' in main_content
        error_handling_check = {
            "name": "has_error_handling",
            "passed": has_try_except,
            "detail": "Has try/except error handling" if has_try_except else "Missing error handling"
        }
        checks.append(error_handling_check)
        
        # Check for async/await usage
        has_async = 'async def' in main_content or 'await' in main_content
        async_check = {
            "name": "uses_async",
            "passed": has_async,
            "detail": "Uses async/await patterns" if has_async else "Missing async implementation"
        }
        checks.append(async_check)
    
    # Check for proper config file reading
    config_file = workspace_path / 'research_config.json'
    config_check = {
        "name": "config_file_exists",
        "passed": config_file.exists(),
        "detail": "Research config file exists" if config_file.exists() else "Research config file missing"
    }
    checks.append(config_check)
    
    # Check if code handles multiple output formats (markdown + docx)
    docx_handling = 'python-docx' in str(workspace_path / 'requirements.txt').replace('-', '_') if (workspace_path / 'requirements.txt').exists() else False
    markdown_handling = 'markdown' in str(workspace_path / 'requirements.txt') if (workspace_path / 'requirements.txt').exists() else False
    
    format_check = {
        "name": "supports_multiple_formats",
        "passed": docx_handling and markdown_handling,
        "detail": f"Output format support - DOCX: {docx_handling}, Markdown: {markdown_handling}"
    }
    checks.append(format_check)
    
    # Check for streaming usage (recommended for large outputs)
    if main_py.exists():
        with open(main_py) as f:
            main_content = f.read()
        has_streaming = '.stream(' in main_content or 'stream=' in main_content
        streaming_check = {
            "name": "uses_streaming",
            "passed": has_streaming,
            "detail": "Uses streaming for responses" if has_streaming else "Missing streaming implementation"
        }
        checks.append(streaming_check)
    
    # Check for proper file organization
    has_proper_structure = True
    structure_details = []
    
    # Should have separate modules/classes for different concerns
    if main_py.exists():
        with open(main_py) as f:
            content = f.read()
        if len(content.split('\n')) > 200:  # If main.py is too long, should be modularized
            has_proper_structure = False
            structure_details.append("main.py is too monolithic")
    
    structure_check = {
        "name": "proper_code_structure", 
        "passed": has_proper_structure,
        "detail": "Code is well structured" if has_proper_structure else "; ".join(structure_details)
    }
    checks.append(structure_check)
    
    # Check for marker content in config
    marker_check = {
        "name": "marker_content_present",
        "passed": False,
        "detail": "Marker content not found"
    }
    
    if config_file.exists():
        with open(config_file) as f:
            config_data = json.load(f)
        if expected['marker_validation'] in str(config_data):
            marker_check['passed'] = True
            marker_check['detail'] = "Marker content found in config"
    
    checks.append(marker_check)
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Overall pass requires most critical checks
    critical_checks = ['main_py_exists', 'uses_anthropic', 'defines_required_tools', 'uses_correct_model', 'marker_content_present']
    critical_passed = sum(1 for check in checks if check['name'] in critical_checks and check['passed'])
    
    passed = critical_passed >= len(critical_checks) * 0.8 and score >= 0.7
    
    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = main(sys.argv[1])
    print(json.dumps(result))