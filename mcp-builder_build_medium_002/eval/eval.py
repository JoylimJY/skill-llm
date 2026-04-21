import json
import os
import re
import sys
from typing import List, Dict, Any


def read_all_text_files(workspace: str) -> List[str]:
    texts = []
    for root, _, files in os.walk(workspace):
        for fname in files:
            if fname.lower().endswith('.md') or fname.lower().endswith('.txt') or fname.lower().endswith('.json') or fname.lower().endswith('.py'):
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        texts.append(f.read())
                except Exception:
                    continue
    return texts


def check_presence_of_docstring_and_annotations(workspace: str) -> Dict[str, Any]:
    '''Check if example_search_mcp.py defines the tool with docstring and annotations.'''
    target_file = None
    for root, _, files in os.walk(workspace):
        for fname in files:
            if fname == 'example_search_mcp.py':
                target_file = os.path.join(root, fname)
                break
        if target_file:
            break

    if not target_file:
        return {"name": "File exists: example_search_mcp.py", "passed": False, "detail": "File example_search_mcp.py not found."}

    passed_docstring = False
    passed_annotations = False

    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"name": "Read example_search_mcp.py", "passed": False, "detail": f"Failed to read file: {e}"}

    # Check that docstring exists for tool function
    # Look for triple-quoted string immediately after 'async def example_search_users'
    func_match = re.search(r'async def example_search_users\s*\(.*?\):', content, flags=re.IGNORECASE | re.DOTALL)
    if func_match:
        # Find starting position after the function declaration
        start_pos = func_match.end()
        # Check if a triple-quoted string appears starting near here
        triple_quote_match = re.search(r'\"\"\"(.*?)\"\"\"', content[start_pos:start_pos+1000], flags=re.IGNORECASE | re.DOTALL)
        if triple_quote_match:
            passed_docstring = True
    
    # Check annotations in decorator @mcp.tool(...annotations={...})
    # Look for '@mcp.tool' decorator containing annotations with keys: readOnlyHint, destructiveHint, idempotentHint, openWorldHint
    annotations_pattern = re.compile(
        r'@mcp\.tool\s*\(.*?annotations\s*=\s*\{([^}]*)\}',
        flags=re.IGNORECASE | re.DOTALL
    )
    annotations_match = annotations_pattern.search(content)
    if annotations_match:
        annotations_text = annotations_match.group(1).lower()
        needed_keys = [
            'readonlyhint', 'destructivehint', 'idempotenthint', 'openworldhint'
        ]
        if all(key in annotations_text for key in needed_keys):
            passed_annotations = True

    detail_msg = ''
    if not passed_docstring:
        detail_msg += 'Missing or incomplete docstring for example_search_users. '
    if not passed_annotations:
        detail_msg += 'Missing or incomplete annotations in @mcp.tool decorator. '

    passed = passed_docstring and passed_annotations
    return {"name": "Docstring and annotation presence", "passed": passed, "detail": detail_msg.strip() if detail_msg else "Present and complete."}


def check_character_limit_and_truncation(response_text: str) -> Dict[str, Any]:
    '''Check if response respects CHARACTER_LIMIT and truncation message is present if needed.'''
    CHARACTER_LIMIT = 25000
    chars_len = len(response_text)
    if chars_len <= CHARACTER_LIMIT:
        # If not exceeding limit, perfect.
        return {"name": "Character limit compliance", "passed": True, "detail": "Response within character limit."}

    # If over limit, expect truncation message (case-insensitive search)
    truncation_indicators = [
        'truncated', 'response truncated', 'use', 'offset', 'filter', 'see more'
    ]
    lower_resp = response_text.lower()
    found = any(kw in lower_resp for kw in truncation_indicators)
    if found:
        return {"name": "Character limit compliance", "passed": True, "detail": "Response truncated with guidance message."}
    else:
        return {"name": "Character limit compliance", "passed": False, "detail": "Response exceeds character limit but no truncation notice found."}


def check_pagination_metadata(json_data: Dict[str, Any]) -> Dict[str, Any]:
    '''Verify pagination metadata is correct and consistent.''' 
    total = json_data.get('total')
    count = json_data.get('count')
    offset = json_data.get('offset')
    users = json_data.get('users')
    has_more = json_data.get('has_more')
    next_offset = json_data.get('next_offset')

    if total is None or count is None or offset is None or users is None:
        return {"name": "Pagination metadata completeness", "passed": False, "detail": "Missing required pagination properties."}
    if not isinstance(users, list):
        return {"name": "Pagination users list", "passed": False, "detail": "'users' field is not a list."}

    # Count consistency
    if count != len(users):
        return {"name": "Pagination count correctness", "passed": False, "detail": f"Count {count} does not match number of users {len(users)}."}

    # has_more and next_offset logic
    expected_has_more = total > offset + count
    if has_more != expected_has_more:
        return {"name": "Pagination has_more correctness", "passed": False, "detail": f"has_more value {has_more} incorrect; expected {expected_has_more}."}

    if expected_has_more and next_offset != offset + count:
        return {"name": "Pagination next_offset correctness", "passed": False, "detail": f"next_offset {next_offset} incorrect; expected {offset + count}."}

    if not expected_has_more and next_offset is not None:
        return {"name": "Pagination next_offset correctness", "passed": False, "detail": "next_offset should be None when no more results."}

    return {"name": "Pagination metadata correctness", "passed": True, "detail": "Pagination metadata is consistent."}


def parse_json_response_from_text(text: str) -> Dict[str, Any]:
    '''Attempt to extract JSON from anywhere in the text'''
    try:
        # Attempt to parse whole text
        return json.loads(text)
    except Exception:
        # Try to find a JSON substring
        matches = re.findall(r'\{.*?\}', text, re.DOTALL)
        for candidate in matches:
            try:
                parsed = json.loads(candidate)
                return parsed
            except Exception:
                continue
    return {}


def check_response_formats(workspace: str) -> List[Dict[str, Any]]:
    '''Check that both markdown and JSON response formats work and are correct.'''
    results = []

    # Find all markdown or text files and JSON output files
    all_texts = read_all_text_files(workspace)

    markdown_found = False
    json_found = False

    for text in all_texts:
        if 'user search results' in text.lower():
            markdown_found = True
            # Check for presence of user names and emails
            passes = all(
                (u in text.lower()) for u in ['alice', 'email', 'bob', 'carol']
            )
            results.append({
                "name": "Markdown response content",
                "passed": passes,
                "detail": "Markdown output includes expected user info." if passes else "Missing some expected user info in markdown."
            })

        # Try to parse json to check structure
        parsed = parse_json_response_from_text(text)
        if parsed:
            # Check keys expected in json
            keys = parsed.keys()
            if all(k in keys for k in ['total', 'count', 'offset', 'users']):
                json_found = True
                # pagination metadata correctness
                results.append(check_pagination_metadata(parsed))

                # Check users list type
                if isinstance(parsed.get('users'), list) and len(parsed['users']) > 0:
                    # Check each user has required fields
                    all_good = True
                    for user in parsed['users']:
                        if not isinstance(user, dict):
                            all_good = False
                            break
                        required = ['id', 'name', 'email']
                        if not all(r in user for r in required):
                            all_good = False
                            break
                    results.append({
                        "name": "Users list fields",
                        "passed": all_good,
                        "detail": "All users have required fields." if all_good else "Some users missing required fields."
                    })
                else:
                    results.append({
                        "name": "Users list type and length",
                        "passed": False,
                        "detail": "Users field is not a non-empty list."
                    })

    if not markdown_found:
        results.append({"name": "Markdown response presence", "passed": False, "detail": "No user search markdown response found."})
    else:
        results.append({"name": "Markdown response presence", "passed": True, "detail": "Found markdown response."})

    if not json_found:
        results.append({"name": "JSON response presence", "passed": False, "detail": "No valid JSON user search response found."})
    else:
        results.append({"name": "JSON response presence", "passed": True, "detail": "Found valid JSON response."})

    return results


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Args", "passed": False, "detail": "Workspace directory argument missing."}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    checks = []

    # Check docstring and annotations
    checks.append(check_presence_of_docstring_and_annotations(workspace))

    # Load all text to find large response (simulate large text test via generated inputs unlikely but we check all files)
    all_texts = read_all_text_files(workspace)
    char_limit_checks = []

    for text in all_texts:
        if 'user search results' in text.lower() or text.strip().startswith('{'):
            # Check character limit and truncation on this snippet
            char_limit_checks.append(check_character_limit_and_truncation(text))

    if char_limit_checks:
        # Combine results: pass if any check is passed as these represent samples
        passed = any(c['passed'] for c in char_limit_checks)
        detail = 'At least one response respects character limit or truncation.' if passed else 'No responses respect character limit or truncation.'
        checks.append({"name": "Character limit checks", "passed": passed, "detail": detail})
    else:
        checks.append({"name": "Character limit checks", "passed": False, "detail": "No candidate response texts found for character limit check."})

    # Check response formats
    checks.extend(check_response_formats(workspace))

    # Calculate final score
    total = len(checks)
    passed_count = sum(1 for check in checks if check['passed'])
    score = passed_count / total if total > 0 else 0.0

    # Overall pass threshold is 0.8 (80%) due to medium difficulty
    overall_pass = score >= 0.8

    output = {
        "passed": overall_pass,
        "score": score,
        "checks": checks
    }

    print(json.dumps(output))


if __name__ == '__main__':
    main()
