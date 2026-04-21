import json
import os
import re
import sys
from typing import Dict, List

def load_file_content(workspace: str, extensions: List[str]) -> Dict[str, str]:
    """Load all files matching extensions in workspace, return dict filename->content."""
    result = {}
    for root, _, files in os.walk(workspace):
        for fname in files:
            if any(fname.lower().endswith(ext) for ext in extensions):
                path = os.path.join(root, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        result[fname] = content
                except Exception:
                    continue
    return result

def check_markdown_output(text: str, known_users: List[Dict[str, str]], query: str, limit: int, offset: int) -> bool:
    text = text.lower()
    if len(text) > 25000:
        return False
    if "found" not in text and "no users found" not in text:
        return False
    matched = False
    lcquery = query.lower()
    for user in known_users:
        name = user.get('name','').lower()
        email = user.get('email','').lower()
        if lcquery in name or lcquery in email:
            if re.search(re.escape(user['name'].lower()), text) and re.search(re.escape(user['email'].lower()), text):
                matched = True
                break
    if not matched and re.search(r'no users found', text, re.I):
        matched = True
    return matched

def check_json_output(text: str, known_users: List[Dict[str, str]], query: str, limit: int, offset: int) -> bool:
    try:
        data = json.loads(text)
    except Exception:
        return False
    total = data.get('total')
    count = data.get('count')
    offset_val = data.get('offset')
    users_list = data.get('users', [])
    if not isinstance(users_list, list):
        return False
    if total != len(known_users):
        return False
    if count != len(users_list):
        return False
    if offset_val != offset:
        return False
    for u in users_list:
        if not isinstance(u, dict):
            return False
        if not all(k in u for k in ['id','name','email']):
            return False
    lcquery = query.lower()
    found = any(lcquery in u.get('name', '').lower() or lcquery in u.get('email','').lower() for u in users_list)
    if not found and len(users_list) > 0:
        return False
    return True

def find_best_pass_score(file_contents: Dict[str,str], known_users: List[Dict[str,str]], query: str, limit: int, offset: int) -> float:
    passed_checks = 0
    total_checks = 2
    passed_checks += any(check_markdown_output(content, known_users, query, limit, offset) for content in file_contents.values())
    passed_checks += any(check_json_output(content, known_users, query, limit, offset) for content in file_contents.values())
    return passed_checks / total_checks

def check_server_py(workspace: str) -> Dict[str, any]:
    """Check server.py content for required components as fallback."""
    server_path = os.path.join(workspace, 'server.py')
    checks = []
    
    if not os.path.isfile(server_path):
        return {"passed": False, "checks": [{"name": "server.py exists", "passed": False, "detail": "server.py not found"}]}
    
    try:
        with open(server_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"passed": False, "checks": [{"name": "server.py readable", "passed": False, "detail": f"Error reading server.py: {str(e)}"}]}
    
    # Check for required components
    has_tool_name = 'example_search_users' in content
    checks.append({"name": "Tool name present", "passed": has_tool_name, "detail": "Tool 'example_search_users' defined"})
    
    has_pydantic = 'BaseModel' in content or 'pydantic' in content.lower()
    checks.append({"name": "Pydantic validation", "passed": has_pydantic, "detail": "Pydantic models for input validation"})
    
    has_character_limit = '25000' in content or 'CHARACTER_LIMIT' in content
    checks.append({"name": "Character limit", "passed": has_character_limit, "detail": "CHARACTER_LIMIT constant defined"})
    
    has_markdown_support = 'markdown' in content.lower()
    has_json_support = '"json"' in content.lower() or "'json'" in content.lower()
    checks.append({"name": "Output formats", "passed": has_markdown_support and has_json_support, "detail": "Supports both markdown and json formats"})
    
    has_annotations = all(a in content for a in ['readOnlyHint', 'destructiveHint', 'idempotentHint', 'openWorldHint'])
    checks.append({"name": "Tool annotations", "passed": has_annotations, "detail": "All required tool annotations present"})
    
    has_async = 'async' in content and 'await' in content
    checks.append({"name": "Async/await", "passed": has_async, "detail": "Tool uses async/await"})
    
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / len(checks) if checks else 0.0
    
    return {"passed": score == 1.0, "score": score, "checks": checks}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "argument check", "passed": False, "detail": "workspace path argument missing"}]}))
        return
    workspace = sys.argv[1]

    users_path = os.path.join(workspace, 'users.json')
    try:
        with open(users_path, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
            known_users = users_data.get('users', [])
    except Exception:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "load users.json", "passed": False, "detail": "users.json missing or invalid JSON"}]}))
        return

    query = "a"
    limit = 5
    offset = 0

    # Try output files first (if agent ran the server and generated outputs)
    file_contents = load_file_content(workspace, [".md", ".markdown", ".json", ".txt", ".out"])

    if file_contents:
        # Use output-based evaluation
        score = find_best_pass_score(file_contents, known_users, query, limit, offset)
        passed = (score == 1.0)

        checks = []
        markdown_pass = any(check_markdown_output(content, known_users, query, limit, offset) for content in file_contents.values())
        checks.append({
            "name": "markdown output format",
            "passed": markdown_pass,
            "detail": "Checks if markdown output contains user info matching query and follow expected structure"
        })
        json_pass = any(check_json_output(content, known_users, query, limit, offset) for content in file_contents.values())
        checks.append({
            "name": "json output format",
            "passed": json_pass,
            "detail": "Checks if json output has structured fields and users matching query"
        })

        print(json.dumps({
            "passed": passed,
            "score": score,
            "checks": checks
        }))
    else:
        # Fallback: check server.py content directly
        result = check_server_py(workspace)
        print(json.dumps(result))

if __name__ == "__main__":
    main()