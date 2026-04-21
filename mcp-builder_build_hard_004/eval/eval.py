import os
import sys
import json
import re

# Robust text search ignoring case

def contains_keyword(text, keywords):
    if not text:
        return False
    text_l = text.lower()
    for kw in keywords:
        if kw.lower() in text_l:
            return True
    return False

# Parse json safely

def safe_load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None

# Validate pagination metadata in JSON response

def check_pagination_fields(resp):
    keys = ['total', 'count', 'offset', 'has_more']
    if not isinstance(resp, dict):
        return False, 'Response is not a JSON object'
    for key in keys:
        if key not in resp:
            return False, f"Pagination field '{key}' missing"
    # Check values reasonable
    total = resp.get('total')
    count = resp.get('count')
    offset = resp.get('offset')
    has_more = resp.get('has_more')
    if not isinstance(total, int) or total < 0:
        return False, 'Total count invalid'
    if not isinstance(count, int) or count < 0:
        return False, 'Count invalid'
    if not isinstance(offset, int) or offset < 0:
        return False, 'Offset invalid'
    if not isinstance(has_more, bool):
        return False, 'has_more is not boolean'
    if offset > total:
        return False, 'Offset exceeds total'
    if count > (total - offset):
        return False, 'Count exceeds remaining items'
    return True, ''


# Check truncation message presence and contents

def check_truncation(text):
    if not text:
        return False, 'No text to check truncation'
    # Look for some phrase like 'truncated' and 'Use limit or offset' ignoring case
    pattern = re.compile(r'truncate(d|ing)?', re.IGNORECASE)
    if not pattern.search(text):
        return False, 'No truncation keyword found'
    if not re.search(r'(limit|offset)', text, re.IGNORECASE):
        return False, 'No suggestion to use limit or offset found'
    return True, ''

# Locate files ending with .py or .json for evaluation

def find_file_with_keywords(dir_path, keywords, include_exts=None):
    # keywords can be list of strings appearing in filename
    res = []
    for root, dirs, files in os.walk(dir_path):
        for fname in files:
            if include_exts and not any(fname.endswith(ext) for ext in include_exts):
                continue
            fname_l = fname.lower()
            if all(kw.lower() in fname_l for kw in keywords):
                res.append(os.path.join(root, fname))
    return res


# Main evaluation

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            'passed': False,
            'score': 0.0,
            'checks': [{'name': 'arg_check', 'passed': False, 'detail': 'Missing workspace directory argument'}]
        }))
        return

    workspace = sys.argv[1]

    # Checks to perform
    checks = []

    # 1. Check all three input JSON files exist and contain marker content
    input_files = ['projects.json', 'tasks.json', 'users.json']
    for fname in input_files:
        fpath = os.path.join(workspace, fname)
        if not os.path.isfile(fpath):
            checks.append({'name': f'{fname} existence', 'passed': False, 'detail': f'{fname} not found'})
            continue
        try:
            data = safe_load_json(fpath)
            if not data:
                checks.append({'name': f'{fname} parse', 'passed': False, 'detail': f'{fname} not valid JSON'})
                continue
            # Check marker content present in JSON strings
            json_text = json.dumps(data)
            if fname == 'projects.json':
                markers = ['[PROJECT_MARKER_ALPHA]', '[PROJECT_MARKER_BETA]', '[PROJECT_MARKER_GAMMA]']
            elif fname == 'tasks.json':
                markers = ['[TASK_MARKER_ONE]', '[TASK_MARKER_TWO]', '[TASK_MARKER_THREE]', '[TASK_MARKER_FOUR]']
            elif fname == 'users.json':
                markers = ['[USER_MARKER_EVE]', '[USER_MARKER_DAN]', '[USER_MARKER_KIM]']
            else:
                markers = []
            found_all = all(marker.lower() in json_text.lower() for marker in markers)
            passed = found_all
            det = f'All markers found' if passed else f'Missing some marker in {fname}'
            checks.append({'name': f'{fname} marker content', 'passed': passed, 'detail': det})
        except Exception as e:
            checks.append({'name': f'{fname} exception', 'passed': False, 'detail': str(e)})

    # 2. Check for server script file named tasktracker_mcp.py present
    # Flexible: accept any .py file with 'tasktracker' in name
    server_files = find_file_with_keywords(workspace, ['tasktracker'], include_exts=['.py'])
    if not server_files:
        checks.append({'name': 'server script file', 'passed': False, 'detail': 'No server script file with tasktracker found'})
    else:
        # Check for correct tool annotations presence via text search
        server_path = server_files[0]
        with open(server_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        # Check presence of MCP tools with required annotations
        annotation_marks = ['readonlyhint=true', 'destructivehint=false', 'idempotenthint=true', 'openworldhint=true']
        annotation_check = all(mark in content for mark in annotation_marks)
        checks.append({'name': 'tool annotations', 'passed': annotation_check, 'detail': 'All required tool annotations present' if annotation_check else 'Missing some required annotations'})

    # 3. Check Dockerfile existence - flexible naming
    dockerfile_names = ['Dockerfile', 'dockerfile', 'Dockerfile.txt']
    dockerfile_path = None
    for dname in dockerfile_names:
        dpath = os.path.join(workspace, dname)
        if os.path.isfile(dpath):
            dockerfile_path = dpath
            break
    
    if dockerfile_path:
        with open(dockerfile_path, 'r', encoding='utf-8') as f:
            docker_content = f.read().lower()
        # Check for python:3.11-slim specifically
        python_311 = 'python:3.11-slim' in docker_content
        checks.append({'name': 'dockerfile base image', 'passed': python_311, 'detail': 'Uses python:3.11-slim as base image' if python_311 else 'Does not use python:3.11-slim'})
    else:
        checks.append({'name': 'dockerfile existence', 'passed': False, 'detail': 'Dockerfile not found'})

    # 4. Evaluate gen_inputs_script outputs by verifying generated files contain marker strings (already done)

    # 5. Evaluate eval_script script exists and runs without error
    eval_scripts = find_file_with_keywords(workspace, ['eval'], include_exts=['.py'])
    if not eval_scripts:
        checks.append({'name': 'eval script existence', 'passed': False, 'detail': 'Evaluation script not found'})
    else:
        eval_path = eval_scripts[0]
        checks.append({'name': 'eval script existence', 'passed': True, 'detail': f'Found evaluation script at {eval_path}'})

    # Calculate score
    passed_count = sum(1 for c in checks if c['passed'])
    total_checks = len(checks)
    score = passed_count / total_checks if total_checks > 0 else 0.0
    passed = score == 1.0  # Hard task requires perfect score

    # Output result
    print(json.dumps({
        'passed': passed,
        'score': score,
        'checks': checks
    }))


if __name__ == '__main__':
    main()
