import sys
import os
import re
import json


def check_markdown_content(text: str, query: str) -> bool:
    # Case-insensitive checks for markdown content
    lower = text.lower()
    checks = []

    # Header with query present
    checks.append(query.lower() in lower)

    # Header or first line contains 'found' and a number
    found_matches = re.findall(r'found\s+(\d+)', lower)
    checks.append(len(found_matches) > 0)

    # At least one user heading format: name and id
    user_heading_match = re.search(r'#+\s+.+\s*\(.*\)', text, re.IGNORECASE)
    checks.append(user_heading_match is not None)

    # Email line
    email_line_match = re.search(r'[-*]\s*\*\*email\*\*\s*:\s*\S+@\S+', text, re.IGNORECASE)
    checks.append(email_line_match is not None)

    return all(checks)


def check_json_content(data: dict) -> bool:
    # Required keys
    required_keys = ['total', 'count', 'offset', 'users']
    if not all(k in data for k in required_keys):
        return False

    users = data.get('users', [])
    if not isinstance(users, list) or len(users) == 0:
        return False

    # Check sample user keys
    sample = users[0]
    user_keys = ['id', 'name', 'email']
    if not all(k in sample for k in user_keys):
        return False

    # team is optional
    if 'team' in sample and not isinstance(sample['team'], str):
        return False

    # total, count, offset should be int
    for k in ['total', 'count', 'offset']:
        if not isinstance(data.get(k), int):
            return False

    return True


def flexible_file_discovery(dir_path: str, extensions: list[str]) -> list[str]:
    # Return list of files with matching extensions in any case
    files = []
    for fname in os.listdir(dir_path):
        for ext in extensions:
            if fname.lower().endswith(ext.lower()):
                files.append(os.path.join(dir_path, fname))
    return files


def safe_read_file(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""


def evaluate(workspace: str) -> dict:
    checks = []

    # Discover candidate output files (.py is not expected output, but .md and .json expected in output)
    candidate_files = flexible_file_discovery(workspace, ['.md', '.json', '.txt', '.out', '.result'])

    if not candidate_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_presence", "passed": False, "detail": "No output file with extensions .md, .json, .txt, .out, or .result found."}]
        }

    best_score = 0
    best_detail = ""

    for filepath in candidate_files:
        content = safe_read_file(filepath)
        # Skip empty files
        if not content.strip():
            continue

        # Try JSON parse if file ends with .json or .out or .result
        if filepath.lower().endswith(('.json', '.out', '.result')):
            try:
                data = json.loads(content)
            except Exception:
                continue
            if check_json_content(data):
                return {
                    "passed": True,
                    "score": 1.0,
                    "checks": [
                        {
                            "name": "json_output_structure",
                            "passed": True,
                            "detail": f"Valid JSON output with required keys in file {os.path.basename(filepath)}."
                        }
                    ]
                }
        else:
            # Assume markdown or text output
            # Try to find query string in content (prompt query: example search users uses deterministic query "john")
            # We'll accept any user query with min length 2, so test presence of typical user fields: name, id, email as markers
            # Check for typical markdown patterns
            if check_markdown_content(content, "search") or check_markdown_content(content, "user") or check_markdown_content(content, "email"):
                # Mark passed
                return {
                    "passed": True,
                    "score": 1.0,
                    "checks": [
                        {
                            "name": "markdown_output_structure",
                            "passed": True,
                            "detail": f"Valid markdown output structure found in file {os.path.basename(filepath)}."
                        }
                    ]
                }
    # If no file passed
    return {
        "passed": False,
        "score": 0.0,
        "checks": [{"name": "output_validation", "passed": False, "detail": "No valid markdown or JSON output file with expected structure found."}]
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "argument_presence", "passed": False, "detail": "Workspace directory argument missing."}]
        }))
        sys.exit(1)

    workspace_dir = sys.argv[1]
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))
