import sys
import os
import json
import ast
import re

def load_source(workspace):
    candidates = []
    for fname in os.listdir(workspace):
        if fname.endswith('.py') and 'task' in fname.lower() and 'mcp' in fname.lower():
            candidates.append(os.path.join(workspace, fname))
    # Also check direct name
    direct = os.path.join(workspace, 'task_mcp_server.py')
    if direct not in candidates and os.path.exists(direct):
        candidates.insert(0, direct)
    return candidates

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def check_file_exists(workspace):
    path = os.path.join(workspace, 'task_mcp_server.py')
    return os.path.exists(path), path

def run_checks(workspace):
    checks = []

    # Check 1: File exists
    exists, fpath = check_file_exists(workspace)
    checks.append({
        'name': 'File task_mcp_server.py exists',
        'passed': exists,
        'detail': f'File found at {fpath}' if exists else 'task_mcp_server.py not found in workspace'
    })
    if not exists:
        # Try to find any candidate
        candidates = load_source(workspace)
        if candidates:
            fpath = candidates[0]
            checks[-1] = {
                'name': 'File task_mcp_server.py exists',
                'passed': False,
                'detail': f'task_mcp_server.py not found, but found candidate: {os.path.basename(fpath)}'
            }
        else:
            for _ in range(6):
                checks.append({'name': 'placeholder', 'passed': False, 'detail': 'File not found, skipping remaining checks'})
            return checks

    source = read_file(fpath)
    source_lower = source.lower()

    # Check 2: FastMCP import and server named task_mcp
    has_fastmcp_import = 'fastmcp' in source_lower
    has_task_mcp_name = bool(re.search(r'fastmcp\s*\(\s*["\']task_mcp["\']', source, re.IGNORECASE))
    checks.append({
        'name': 'FastMCP imported and server named task_mcp',
        'passed': has_fastmcp_import and has_task_mcp_name,
        'detail': f'FastMCP import: {has_fastmcp_import}, server name task_mcp: {has_task_mcp_name}'
    })

    # Check 3: TASK_API_URL env variable used
    has_env_var = 'task_api_url' in source_lower and ('environ' in source_lower or 'getenv' in source_lower or 'os.environ' in source_lower or 'os.getenv' in source_lower)
    checks.append({
        'name': 'TASK_API_URL environment variable used',
        'passed': has_env_var,
        'detail': 'TASK_API_URL read from environment' if has_env_var else 'TASK_API_URL not found in os.environ/os.getenv calls'
    })

    # Check 4: tool task_list_tasks defined
    has_list_tasks = 'task_list_tasks' in source
    checks.append({
        'name': 'tool task_list_tasks defined',
        'passed': has_list_tasks,
        'detail': 'task_list_tasks tool found' if has_list_tasks else 'task_list_tasks tool not found'
    })

    # Check 5: tool task_get_task defined
    has_get_task = 'task_get_task' in source
    checks.append({
        'name': 'tool task_get_task defined',
        'passed': has_get_task,
        'detail': 'task_get_task tool found' if has_get_task else 'task_get_task tool not found'
    })

    # Check 6: tool task_create_task defined
    has_create_task = 'task_create_task' in source
    checks.append({
        'name': 'tool task_create_task defined',
        'passed': has_create_task,
        'detail': 'task_create_task tool found' if has_create_task else 'task_create_task tool not found'
    })

    # Check 7: httpx used for HTTP requests
    has_httpx = 'httpx' in source_lower
    checks.append({
        'name': 'httpx used for HTTP requests',
        'passed': has_httpx,
        'detail': 'httpx imported/used' if has_httpx else 'httpx not found in source'
    })

    # Check 8: Pydantic BaseModel used for input validation
    has_basemodel = 'basemodel' in source_lower
    has_field = 'field(' in source_lower or 'field (' in source_lower
    checks.append({
        'name': 'Pydantic BaseModel with Field() used for input validation',
        'passed': has_basemodel and has_field,
        'detail': f'BaseModel: {has_basemodel}, Field(): {has_field}'
    })

    # Check 9: async tools
    async_tool_count = len(re.findall(r'async\s+def\s+task_(?:list_tasks|get_task|create_task)', source))
    checks.append({
        'name': 'Tools are async functions',
        'passed': async_tool_count >= 2,
        'detail': f'{async_tool_count} of 3 tools defined as async'
    })

    # Check 10: error handling present
    has_try_except = 'try:' in source and 'except' in source
    has_error_return = bool(re.search(r'["\']error["\']|"error:|error:', source, re.IGNORECASE))
    checks.append({
        'name': 'Error handling implemented',
        'passed': has_try_except or has_error_return,
        'detail': f'try/except: {has_try_except}, error string return: {has_error_return}'
    })

    # Check 11: main guard with mcp.run()
    has_main_guard = '__name__' in source and '__main__' in source
    has_mcp_run = bool(re.search(r'mcp\.run\s*\(', source))
    checks.append({
        'name': 'if __name__ == __main__: mcp.run() present',
        'passed': has_main_guard and has_mcp_run,
        'detail': f'main guard: {has_main_guard}, mcp.run(): {has_mcp_run}'
    })

    # Check 12: syntax validity
    try:
        ast.parse(source)
        syntax_ok = True
        syntax_detail = 'File parses successfully as valid Python'
    except SyntaxError as e:
        syntax_ok = False
        syntax_detail = f'SyntaxError: {e}'
    checks.append({
        'name': 'Python syntax is valid',
        'passed': syntax_ok,
        'detail': syntax_detail
    })

    return checks

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    checks = run_checks(workspace)
    # Remove placeholder checks
    checks = [c for c in checks if c['name'] != 'placeholder']
    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total > 0 else 0.0
    result = {
        'passed': score >= 0.8,
        'score': round(score, 4),
        'checks': checks
    }
    print(json.dumps(result, indent=2))
