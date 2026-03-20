#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Any

def check_file_exists(workspace_dir: str, filename: str) -> Dict[str, Any]:
    """Check if a file exists in the workspace."""
    filepath = Path(workspace_dir) / filename
    return {
        "name": f"File exists: {filename}",
        "passed": filepath.exists(),
        "detail": f"Expected {filename} to exist" + ("" if filepath.exists() else " but it was not found")
    }

def check_typescript_compilation(workspace_dir: str) -> Dict[str, Any]:
    """Check if TypeScript code compiles successfully."""
    try:
        os.chdir(workspace_dir)
        result = subprocess.run(["npm", "run", "build"], 
                              capture_output=True, text=True, timeout=60)
        passed = result.returncode == 0
        detail = "TypeScript compilation successful" if passed else f"Compilation failed: {result.stderr}"
        return {
            "name": "TypeScript compilation",
            "passed": passed,
            "detail": detail
        }
    except Exception as e:
        return {
            "name": "TypeScript compilation",
            "passed": False,
            "detail": f"Error during compilation: {str(e)}"
        }

def check_server_naming(workspace_dir: str) -> Dict[str, Any]:
    """Check if server follows naming convention."""
    package_json_path = Path(workspace_dir) / "package.json"
    if not package_json_path.exists():
        return {
            "name": "Server naming convention",
            "passed": False,
            "detail": "package.json not found"
        }
    
    with open(package_json_path, 'r') as f:
        package_data = json.load(f)
    
    name = package_data.get('name', '')
    expected_pattern = r'^todoist-mcp-server$|^[a-z0-9-]+-mcp-server$'
    passed = bool(re.match(expected_pattern, name))
    
    return {
        "name": "Server naming convention",
        "passed": passed,
        "detail": f"Server name '{name}' {'follows' if passed else 'does not follow'} convention {expected_pattern}"
    }

def check_mcp_server_structure(workspace_dir: str) -> Dict[str, Any]:
    """Check if the MCP server has proper structure and imports."""
    index_path = Path(workspace_dir) / "src" / "index.ts"
    if not index_path.exists():
        return {
            "name": "MCP server structure",
            "passed": False,
            "detail": "src/index.ts not found"
        }
    
    with open(index_path, 'r') as f:
        content = f.read()
    
    required_imports = [
        "@modelcontextprotocol/sdk/server/mcp",
        "zod"
    ]
    
    required_patterns = [
        r"McpServer",
        r"registerTool",
        r"server\.connect"
    ]
    
    missing_imports = [imp for imp in required_imports if imp not in content]
    missing_patterns = [pat for pat in required_patterns if not re.search(pat, content)]
    
    passed = len(missing_imports) == 0 and len(missing_patterns) == 0
    detail_parts = []
    if missing_imports:
        detail_parts.append(f"Missing imports: {missing_imports}")
    if missing_patterns:
        detail_parts.append(f"Missing patterns: {missing_patterns}")
    
    detail = "MCP server structure correct" if passed else "; ".join(detail_parts)
    
    return {
        "name": "MCP server structure",
        "passed": passed,
        "detail": detail
    }

def check_tool_implementations(workspace_dir: str) -> Dict[str, Any]:
    """Check if required Todoist tools are implemented."""
    src_files = []
    src_dir = Path(workspace_dir) / "src"
    if src_dir.exists():
        for file_path in src_dir.rglob("*.ts"):
            with open(file_path, 'r') as f:
                src_files.append(f.read())
    
    all_content = "\n".join(src_files)
    
    required_tools = [
        r"todoist_.*search.*task",
        r"todoist_.*create.*task",
        r"todoist_.*update.*task",
        r"todoist_.*list.*project",
        r"todoist_.*get.*project"
    ]
    
    found_tools = []
    for tool_pattern in required_tools:
        if re.search(tool_pattern, all_content, re.IGNORECASE):
            found_tools.append(tool_pattern)
    
    passed = len(found_tools) >= 4  # At least 4 of 5 expected tools
    detail = f"Found {len(found_tools)}/{len(required_tools)} expected tool patterns"
    
    return {
        "name": "Todoist tool implementations",
        "passed": passed,
        "detail": detail
    }

def check_zod_schemas(workspace_dir: str) -> Dict[str, Any]:
    """Check if Zod schemas are properly used for input validation."""
    src_files = []
    src_dir = Path(workspace_dir) / "src"
    if src_dir.exists():
        for file_path in src_dir.rglob("*.ts"):
            with open(file_path, 'r') as f:
                src_files.append(f.read())
    
    all_content = "\n".join(src_files)
    
    zod_patterns = [
        r"z\.object\(",
        r"z\.string\(",
        r"z\.number\(",
        r"inputSchema.*:",
        r"\.describe\("
    ]
    
    found_patterns = sum(1 for pattern in zod_patterns if re.search(pattern, all_content))
    passed = found_patterns >= 3
    
    return {
        "name": "Zod schema validation",
        "passed": passed,
        "detail": f"Found {found_patterns}/{len(zod_patterns)} Zod validation patterns"
    }

def check_evaluation_file(workspace_dir: str) -> Dict[str, Any]:
    """Check if proper evaluation file is created."""
    eval_files = list(Path(workspace_dir).glob("*evaluation*.xml")) + list(Path(workspace_dir).glob("evaluation.xml"))
    if not eval_files:
        return {
            "name": "Evaluation file creation",
            "passed": False,
            "detail": "No evaluation.xml file found"
        }
    
    eval_file = eval_files[0]
    with open(eval_file, 'r') as f:
        content = f.read()
    
    # Check for required XML structure
    xml_patterns = [
        r"<evaluation>",
        r"<qa_pair>",
        r"<question>",
        r"<answer>",
        r"</evaluation>"
    ]
    
    found_xml = sum(1 for pattern in xml_patterns if re.search(pattern, content))
    
    # Count questions
    qa_pairs = len(re.findall(r"<qa_pair>", content))
    
    # Check for complexity indicators
    complexity_indicators = [
        r"find.*project.*task",
        r"search.*label",
        r"completed.*date",
        r"priority.*high",
        r"most.*recent"
    ]
    
    found_complexity = sum(1 for pattern in complexity_indicators 
                          if re.search(pattern, content, re.IGNORECASE))
    
    passed = (found_xml >= 4 and qa_pairs >= 8 and found_complexity >= 2)
    detail = f"XML structure: {found_xml}/5, Questions: {qa_pairs}/10, Complexity: {found_complexity}/5"
    
    return {
        "name": "Evaluation file creation",
        "passed": passed,
        "detail": detail
    }

def check_error_handling(workspace_dir: str) -> Dict[str, Any]:
    """Check if proper error handling is implemented."""
    src_files = []
    src_dir = Path(workspace_dir) / "src"
    if src_dir.exists():
        for file_path in src_dir.rglob("*.ts"):
            with open(file_path, 'r') as f:
                src_files.append(f.read())
    
    all_content = "\n".join(src_files)
    
    error_patterns = [
        r"try\s*\{",
        r"catch\s*\(",
        r"AxiosError",
        r"Error:",
        r"handleApiError|handle.*error"
    ]
    
    found_patterns = sum(1 for pattern in error_patterns if re.search(pattern, all_content, re.IGNORECASE))
    passed = found_patterns >= 3
    
    return {
        "name": "Error handling implementation",
        "passed": passed,
        "detail": f"Found {found_patterns}/{len(error_patterns)} error handling patterns"
    }

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Args", "passed": False, "detail": "Usage: eval_script <workspace_dir>"}]}))
        return
    
    workspace_dir = sys.argv[1]
    
    checks = [
        check_file_exists(workspace_dir, "package.json"),
        check_file_exists(workspace_dir, "tsconfig.json"),
        check_file_exists(workspace_dir, "src/index.ts"),
        check_typescript_compilation(workspace_dir),
        check_server_naming(workspace_dir),
        check_mcp_server_structure(workspace_dir),
        check_tool_implementations(workspace_dir),
        check_zod_schemas(workspace_dir),
        check_evaluation_file(workspace_dir),
        check_error_handling(workspace_dir)
    ]
    
    passed_count = sum(1 for check in checks if check["passed"])
    total_count = len(checks)
    score = passed_count / total_count
    overall_passed = score >= 0.7
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()