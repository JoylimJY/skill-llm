#!/usr/bin/env python3

import sys
import os
import json
import subprocess
import tempfile
import importlib.util
from pathlib import Path

def check_file_exists(filepath, name):
    """Check if a file exists."""
    exists = os.path.exists(filepath)
    return {
        "name": name,
        "passed": exists,
        "detail": f"File {'found' if exists else 'not found'}: {filepath}"
    }

def check_file_contains_marker(filepath, marker, name):
    """Check if file contains a specific marker."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            contains = marker in content
            return {
                "name": name,
                "passed": contains,
                "detail": f"Marker {'found' if contains else 'not found'} in {filepath}"
            }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "detail": f"Error reading {filepath}: {str(e)}"
        }

def check_python_imports(filepath, required_imports, name):
    """Check if Python file contains required imports."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            missing_imports = []
            for imp in required_imports:
                if imp not in content:
                    missing_imports.append(imp)
            
            passed = len(missing_imports) == 0
            detail = "All required imports found" if passed else f"Missing imports: {missing_imports}"
            return {
                "name": name,
                "passed": passed,
                "detail": detail
            }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "detail": f"Error checking imports in {filepath}: {str(e)}"
        }

def check_mcp_tool_registration(filepath, expected_tools, name):
    """Check if MCP server contains expected tool registrations."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            found_tools = []
            missing_tools = []
            
            for tool in expected_tools:
                if f'@mcp.tool' in content and tool in content:
                    found_tools.append(tool)
                else:
                    missing_tools.append(tool)
            
            passed = len(missing_tools) == 0
            detail = f"Found tools: {found_tools}" if passed else f"Missing tools: {missing_tools}"
            return {
                "name": name,
                "passed": passed,
                "detail": detail
            }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "detail": f"Error checking tool registration: {str(e)}"
        }

def check_pydantic_models(filepath, name):
    """Check if file contains proper Pydantic model definitions."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
            has_basemodel = 'BaseModel' in content
            has_field = 'Field(' in content
            has_model_config = 'model_config' in content or 'ConfigDict' in content
            
            passed = has_basemodel and has_field
            details = []
            if has_basemodel:
                details.append("BaseModel found")
            if has_field:
                details.append("Field() usage found")
            if has_model_config:
                details.append("Model config found")
                
            return {
                "name": name,
                "passed": passed,
                "detail": "; ".join(details) if details else "No Pydantic patterns found"
            }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "detail": f"Error checking Pydantic models: {str(e)}"
        }

def check_server_naming(filepath, name):
    """Check if server follows Python MCP naming convention."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
            # Look for FastMCP initialization with proper naming
            has_fastmcp = 'FastMCP(' in content
            has_weather_name = 'weather_mcp' in content or '"weather_mcp"' in content
            
            passed = has_fastmcp and has_weather_name
            detail = "Proper server naming found" if passed else "Server naming doesn't follow convention"
            
            return {
                "name": name,
                "passed": passed,
                "detail": detail
            }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "detail": f"Error checking server naming: {str(e)}"
        }

def main():
    if len(sys.argv) != 2:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "arg_check", "passed": False, "detail": "Expected workspace directory argument"}]
        }))
        return
    
    workspace_dir = sys.argv[1]
    os.chdir(workspace_dir)
    
    checks = []
    
    # Check for required input files (should exist from gen_inputs_script)
    checks.append(check_file_exists('test_api_data.json', 'test_data_exists'))
    checks.append(check_file_contains_marker('weather_requirements.txt', 'MARKER_WEATHER_REQ_12345', 'requirements_marker'))
    
    # Look for Python MCP server file
    python_files = list(Path('.').glob('*.py'))
    mcp_server_files = []
    
    for py_file in python_files:
        if py_file.name not in ['gen_inputs_script.py', 'eval_script.py']:
            with open(py_file, 'r') as f:
                content = f.read()
                if 'FastMCP' in content and '@mcp.tool' in content:
                    mcp_server_files.append(str(py_file))
    
    if mcp_server_files:
        server_file = mcp_server_files[0]
        checks.append({
            "name": "mcp_server_found",
            "passed": True,
            "detail": f"Found MCP server: {server_file}"
        })
        
        # Check server structure and content
        required_imports = ['FastMCP', 'BaseModel', 'Field', 'httpx']
        checks.append(check_python_imports(server_file, required_imports, 'required_imports'))
        
        # Check for expected weather tools
        expected_tools = ['weather_get_current', 'weather_list_cities']
        checks.append(check_mcp_tool_registration(server_file, expected_tools, 'tool_registration'))
        
        # Check Pydantic model usage
        checks.append(check_pydantic_models(server_file, 'pydantic_models'))
        
        # Check server naming convention
        checks.append(check_server_naming(server_file, 'server_naming'))
        
        # Check if file is executable Python
        try:
            result = subprocess.run([sys.executable, '-m', 'py_compile', server_file], 
                                  capture_output=True, text=True)
            checks.append({
                "name": "python_syntax",
                "passed": result.returncode == 0,
                "detail": "Python syntax valid" if result.returncode == 0 else f"Syntax error: {result.stderr}"
            })
        except Exception as e:
            checks.append({
                "name": "python_syntax",
                "passed": False,
                "detail": f"Error checking syntax: {str(e)}"
            })
    else:
        checks.append({
            "name": "mcp_server_found",
            "passed": False,
            "detail": "No MCP server file found (should contain FastMCP and @mcp.tool)"
        })
    
    # Calculate score
    passed_checks = sum(1 for check in checks if check["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    result = {
        "passed": score >= 0.7,  # Need at least 70% of checks to pass
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()