#!/usr/bin/env python3
import json
import os
import sys
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Check 1: src/index.ts exists
    index_ts_path = os.path.join(workspace_dir, 'src', 'index.ts')
    check1 = {
        "name": "src/index.ts exists",
        "passed": os.path.isfile(index_ts_path),
        "detail": "File src/index.ts must exist"
    }
    checks.append(check1)
    
    if not check1["passed"]:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    with open(index_ts_path, 'r') as f:
        content = f.read()
    
    # Check 2: McpServer import
    check2 = {
        "name": "McpServer import present",
        "passed": 'McpServer' in content and '@modelcontextprotocol/sdk' in content,
        "detail": "Must import McpServer from MCP SDK"
    }
    checks.append(check2)
    
    # Check 3: Zod import
    check3 = {
        "name": "Zod import present",
        "passed": 'import { z }' in content or 'from "zod"' in content,
        "detail": "Must import Zod for schema validation"
    }
    checks.append(check3)
    
    # Check 4: Server name is 'tasks-mcp-server'
    check4 = {
        "name": "Server name is tasks-mcp-server",
        "passed": 'tasks-mcp-server' in content,
        "detail": "Server name must be 'tasks-mcp-server'"
    }
    checks.append(check4)
    
    # Check 5: search_tasks tool registered
    check5 = {
        "name": "search_tasks tool registered",
        "passed": 'search_tasks' in content and 'registerTool' in content,
        "detail": "Must register search_tasks tool"
    }
    checks.append(check5)
    
    # Check 6: list_tasks tool registered
    check6 = {
        "name": "list_tasks tool registered",
        "passed": 'list_tasks' in content,
        "detail": "Must register list_tasks tool"
    }
    checks.append(check6)
    
    # Check 7: get_task_details tool registered
    check7 = {
        "name": "get_task_details tool registered",
        "passed": 'get_task_details' in content,
        "detail": "Must register get_task_details tool"
    }
    checks.append(check7)
    
    # Check 8: Zod schema for input validation
    check8 = {
        "name": "Zod schemas for validation",
        "passed": 'z.object' in content and 'z.string' in content,
        "detail": "Must use Zod schemas for input validation"
    }
    checks.append(check8)
    
    # Check 9: Response format support (markdown/json)
    check9 = {
        "name": "Response format support",
        "passed": ('markdown' in content.lower() or 'json' in content.lower()) and 'response_format' in content,
        "detail": "Must support markdown and JSON response formats"
    }
    checks.append(check9)
    
    # Check 10: Tool annotations present
    check10 = {
        "name": "Tool annotations present",
        "passed": 'readOnlyHint' in content or 'destructiveHint' in content or 'annotations' in content,
        "detail": "Must include tool annotations"
    }
    checks.append(check10)
    
    # Check 11: Error handling
    check11 = {
        "name": "Error handling implemented",
        "passed": 'catch' in content or 'try' in content or 'Error' in content,
        "detail": "Must implement error handling"
    }
    checks.append(check11)
    
    # Check 12: Pagination support
    check12 = {
        "name": "Pagination support",
        "passed": ('limit' in content or 'offset' in content or 'pagination' in content.lower()),
        "detail": "Must support pagination with limit/offset"
    }
    checks.append(check12)
    
    # Check 13: package.json exists and valid
    package_json_path = os.path.join(workspace_dir, 'package.json')
    check13 = {
        "name": "package.json exists and valid",
        "passed": False,
        "detail": "package.json must exist and be valid JSON"
    }
    if os.path.isfile(package_json_path):
        try:
            with open(package_json_path, 'r') as f:
                pkg = json.load(f)
            check13["passed"] = pkg.get('name') == 'tasks-mcp-server'
        except:
            pass
    checks.append(check13)
    
    # Check 14: tsconfig.json exists
    tsconfig_path = os.path.join(workspace_dir, 'tsconfig.json')
    check14 = {
        "name": "tsconfig.json exists",
        "passed": os.path.isfile(tsconfig_path),
        "detail": "tsconfig.json must exist"
    }
    checks.append(check14)
    
    # Check 15: Tool descriptions are comprehensive
    check15 = {
        "name": "Tool descriptions comprehensive",
        "passed": content.count('description') >= 3,
        "detail": "Each tool must have a description"
    }
    checks.append(check15)
    
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks)
    
    return {
        "passed": score >= 0.8,
        "score": score,
        "checks": checks
    }

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '/workspace'
    result = evaluate(workspace)
    print(json.dumps(result))
