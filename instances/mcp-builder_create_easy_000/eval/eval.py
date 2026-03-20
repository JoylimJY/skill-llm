#!/usr/bin/env python3
import sys
import os
import json
import ast
import subprocess
import tempfile
from pathlib import Path

def check_file_exists(filepath, name):
    exists = os.path.isfile(filepath)
    return {
        "name": f"File exists: {name}",
        "passed": exists,
        "detail": f"Expected {filepath} to exist" if not exists else f"Found {filepath}"
    }

def check_python_syntax(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        ast.parse(content)
        return {
            "name": "Python syntax valid",
            "passed": True,
            "detail": "Python file has valid syntax"
        }
    except SyntaxError as e:
        return {
            "name": "Python syntax valid",
            "passed": False,
            "detail": f"Syntax error: {str(e)}"
        }
    except Exception as e:
        return {
            "name": "Python syntax valid",
            "passed": False,
            "detail": f"Error reading file: {str(e)}"
        }

def check_imports(filepath):
    required_imports = ['fastmcp', 'pydantic', 'httpx']
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        found_imports = []
        for imp in required_imports:
            if imp in content:
                found_imports.append(imp)
        
        missing = set(required_imports) - set(found_imports)
        
        return {
            "name": "Required imports present",
            "passed": len(missing) == 0,
            "detail": f"Missing imports: {list(missing)}" if missing else "All required imports found"
        }
    except Exception as e:
        return {
            "name": "Required imports present",
            "passed": False,
            "detail": f"Error checking imports: {str(e)}"
        }

def check_mcp_server_creation(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        has_fastmcp = 'FastMCP' in content
        has_server_name = 'github_mcp' in content or 'github-mcp' in content
        
        return {
            "name": "MCP server initialized",
            "passed": has_fastmcp and has_server_name,
            "detail": "FastMCP server created with appropriate name" if (has_fastmcp and has_server_name) else "Missing FastMCP initialization or server name"
        }
    except Exception as e:
        return {
            "name": "MCP server initialized",
            "passed": False,
            "detail": f"Error checking server creation: {str(e)}"
        }

def check_tools_implemented(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        has_search_repos = 'search_repositories' in content or 'github_search_repositories' in content
        has_get_user = 'get_user' in content or 'github_get_user' in content
        has_tool_decorator = '@mcp.tool' in content
        
        tools_found = sum([has_search_repos, has_get_user])
        
        return {
            "name": "Required tools implemented",
            "passed": tools_found >= 2 and has_tool_decorator,
            "detail": f"Found {tools_found}/2 required tools with @mcp.tool decorator" if has_tool_decorator else "Missing @mcp.tool decorator or tools"
        }
    except Exception as e:
        return {
            "name": "Required tools implemented",
            "passed": False,
            "detail": f"Error checking tools: {str(e)}"
        }

def check_pydantic_models(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        has_basemodel = 'BaseModel' in content
        has_field = 'Field' in content or 'field' in content.lower()
        
        return {
            "name": "Pydantic models defined",
            "passed": has_basemodel,
            "detail": "Pydantic BaseModel used for input validation" if has_basemodel else "Missing Pydantic BaseModel usage"
        }
    except Exception as e:
        return {
            "name": "Pydantic models defined",
            "passed": False,
            "detail": f"Error checking models: {str(e)}"
        }

def check_server_name_convention(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Look for proper naming convention
        has_proper_name = 'github_mcp' in content
        
        return {
            "name": "Server naming convention",
            "passed": has_proper_name,
            "detail": "Server uses proper naming convention 'github_mcp'" if has_proper_name else "Server should be named 'github_mcp' following Python convention"
        }
    except Exception as e:
        return {
            "name": "Server naming convention",
            "passed": False,
            "detail": f"Error checking naming: {str(e)}"
        }

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Usage", "passed": False, "detail": "Expected workspace directory path"}]}))
        return
    
    workspace_dir = sys.argv[1]
    
    # Look for Python MCP server file
    possible_files = [
        os.path.join(workspace_dir, 'github_mcp.py'),
        os.path.join(workspace_dir, 'github_mcp_server.py'),
        os.path.join(workspace_dir, 'server.py'),
        os.path.join(workspace_dir, 'mcp_server.py')
    ]
    
    server_file = None
    for f in possible_files:
        if os.path.isfile(f):
            server_file = f
            break
    
    checks = []
    
    if not server_file:
        # Look for any .py file that might be the server
        py_files = [f for f in os.listdir(workspace_dir) if f.endswith('.py') and not f.startswith('gen_') and not f.startswith('eval_')]
        if py_files:
            server_file = os.path.join(workspace_dir, py_files[0])
        
    if server_file:
        checks.append(check_file_exists(server_file, "MCP server file"))
        checks.append(check_python_syntax(server_file))
        checks.append(check_imports(server_file))
        checks.append(check_mcp_server_creation(server_file))
        checks.append(check_tools_implemented(server_file))
        checks.append(check_pydantic_models(server_file))
        checks.append(check_server_name_convention(server_file))
    else:
        checks.append({
            "name": "MCP server file found",
            "passed": False,
            "detail": "No Python MCP server file found. Expected github_mcp.py or similar."
        })
    
    passed_checks = sum(1 for check in checks if check["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    result = {
        "passed": score >= 0.7,  # Pass if at least 70% of checks pass
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()