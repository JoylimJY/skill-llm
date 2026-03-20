#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any

def run_command(cmd: List[str], cwd: str = None) -> tuple[bool, str, str]:
    """Run a command and return success, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_file_exists(filepath: str, workspace_dir: str) -> Dict[str, Any]:
    """Check if a file exists and return check result."""
    full_path = os.path.join(workspace_dir, filepath)
    exists = os.path.isfile(full_path)
    return {
        "name": f"File exists: {filepath}",
        "passed": exists,
        "detail": f"File {'found' if exists else 'not found'} at {filepath}"
    }

def check_file_contains(filepath: str, workspace_dir: str, content: str, description: str = None) -> Dict[str, Any]:
    """Check if a file contains specific content."""
    full_path = os.path.join(workspace_dir, filepath)
    desc = description or f"contains '{content[:50]}...'"
    
    if not os.path.isfile(full_path):
        return {
            "name": f"File {filepath} {desc}",
            "passed": False,
            "detail": f"File {filepath} not found"
        }
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        contains = content in file_content
        return {
            "name": f"File {filepath} {desc}",
            "passed": contains,
            "detail": f"Content {'found' if contains else 'not found'} in {filepath}"
        }
    except Exception as e:
        return {
            "name": f"File {filepath} {desc}",
            "passed": False,
            "detail": f"Error reading {filepath}: {str(e)}"
        }

def check_typescript_builds(workspace_dir: str) -> Dict[str, Any]:
    """Check if TypeScript code compiles successfully."""
    success, stdout, stderr = run_command(['npm', 'run', 'build'], cwd=workspace_dir)
    
    return {
        "name": "TypeScript compilation",
        "passed": success,
        "detail": f"Build {'succeeded' if success else 'failed'}. Stderr: {stderr[:200]}..."
    }

def check_mcp_server_structure(workspace_dir: str) -> List[Dict[str, Any]]:
    """Check MCP server implementation structure."""
    checks = []
    
    # Check main index.ts file exists and has proper imports
    main_file = os.path.join(workspace_dir, 'src', 'index.ts')
    if os.path.exists(main_file):
        with open(main_file, 'r') as f:
            content = f.read()
            
        # Check for required MCP SDK imports
        has_mcp_import = '@modelcontextprotocol/sdk' in content
        has_server_init = 'McpServer' in content or 'new McpServer' in content
        has_tool_registration = 'registerTool' in content
        has_todoist_tools = ('todoist_create_task' in content or 
                            'todoist_search_tasks' in content or 
                            'todoist_list_projects' in content)
        
        checks.append({
            "name": "MCP SDK imports",
            "passed": has_mcp_import,
            "detail": "MCP SDK imported" if has_mcp_import else "Missing MCP SDK import"
        })
        
        checks.append({
            "name": "Server initialization",
            "passed": has_server_init,
            "detail": "McpServer initialized" if has_server_init else "Missing McpServer initialization"
        })
        
        checks.append({
            "name": "Tool registration",
            "passed": has_tool_registration,
            "detail": "Tools registered" if has_tool_registration else "No tool registration found"
        })
        
        checks.append({
            "name": "Todoist-specific tools",
            "passed": has_todoist_tools,
            "detail": "Todoist tools implemented" if has_todoist_tools else "Missing Todoist tool implementations"
        })
        
    else:
        checks.append({
            "name": "Main server file",
            "passed": False,
            "detail": "src/index.ts not found"
        })
    
    return checks

def check_evaluation_file(workspace_dir: str) -> Dict[str, Any]:
    """Check if evaluation.xml file was created with proper structure."""
    eval_file = os.path.join(workspace_dir, 'evaluation.xml')
    
    if not os.path.exists(eval_file):
        return {
            "name": "Evaluation file exists",
            "passed": False,
            "detail": "evaluation.xml not found"
        }
    
    try:
        with open(eval_file, 'r') as f:
            content = f.read()
        
        # Check for XML structure
        has_evaluation_tag = '<evaluation>' in content and '</evaluation>' in content
        has_qa_pairs = '<qa_pair>' in content and '</qa_pair>' in content
        has_questions = '<question>' in content and '</question>' in content
        has_answers = '<answer>' in content and '</answer>' in content
        
        # Count qa_pairs
        qa_pair_count = content.count('<qa_pair>')
        has_ten_questions = qa_pair_count >= 10
        
        # Check for Todoist-specific content in questions
        has_todoist_questions = ('task' in content.lower() and 
                               ('project' in content.lower() or 
                                'create' in content.lower() or 
                                'search' in content.lower()))
        
        all_checks_pass = all([has_evaluation_tag, has_qa_pairs, has_questions, has_answers, has_ten_questions, has_todoist_questions])
        
        return {
            "name": "Evaluation file structure",
            "passed": all_checks_pass,
            "detail": f"XML structure: {has_evaluation_tag}, QA pairs: {qa_pair_count}, Todoist content: {has_todoist_questions}"
        }
        
    except Exception as e:
        return {
            "name": "Evaluation file structure",
            "passed": False,
            "detail": f"Error reading evaluation.xml: {str(e)}"
        }

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: eval_script.py <workspace_directory>"}))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    
    if not os.path.isdir(workspace_dir):
        print(json.dumps({"error": f"Workspace directory {workspace_dir} does not exist"}))
        sys.exit(1)
    
    checks = []
    
    # Basic file structure checks
    checks.append(check_file_exists('package.json', workspace_dir))
    checks.append(check_file_exists('tsconfig.json', workspace_dir))
    checks.append(check_file_exists('src/index.ts', workspace_dir))
    
    # Content checks for key files
    checks.append(check_file_contains('package.json', workspace_dir, 'todoist-mcp-server', 'contains todoist server name'))
    checks.append(check_file_contains('package.json', workspace_dir, '@modelcontextprotocol/sdk', 'includes MCP SDK dependency'))
    checks.append(check_file_contains('package.json', workspace_dir, 'zod', 'includes Zod for validation'))
    
    # TypeScript compilation check
    checks.append(check_typescript_builds(workspace_dir))
    
    # MCP server structure checks
    checks.extend(check_mcp_server_structure(workspace_dir))
    
    # Check for required Todoist tools implementation
    index_content_checks = [
        ('todoist_create_task', 'Create task tool'),
        ('todoist_search_tasks', 'Search tasks tool'),
        ('todoist_list_projects', 'List projects tool'),
        ('todoist_complete_task', 'Complete task tool'),
        ('ResponseFormat', 'Response format enum'),
        ('z.object', 'Zod validation schemas'),
        ('async function', 'Async functions'),
        ('error handling', 'Error handling')
    ]
    
    for search_term, description in index_content_checks:
        checks.append(check_file_contains('src/index.ts', workspace_dir, search_term, f'implements {description}'))
    
    # Check for evaluation file
    checks.append(check_evaluation_file(workspace_dir))
    
    # Check for marker content that should be preserved
    checks.append(check_file_contains('README.md', workspace_dir, 'EVAL_MARKER_README_TODOIST', 'contains evaluation marker'))
    
    # Calculate overall score
    passed_checks = sum(1 for check in checks if check['passed'])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Determine overall pass/fail
    # Must have: basic files, TypeScript compilation, MCP structure, and evaluation
    critical_checks = [
        'File exists: src/index.ts',
        'TypeScript compilation', 
        'MCP SDK imports',
        'Server initialization',
        'Tool registration',
        'Evaluation file structure'
    ]
    
    critical_passed = all(check['passed'] for check in checks if check['name'] in critical_checks)
    overall_passed = critical_passed and score >= 0.75
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()