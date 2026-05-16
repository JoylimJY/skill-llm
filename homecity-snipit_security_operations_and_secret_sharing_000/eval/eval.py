import sys
import json
import os
from pathlib import Path

def load_jsonl(path):
    records = []
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return records

def load_snippets_store(path="/tmp/snipit_snippets.json"):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    # ---- Check 1: snippet_ids.txt exists and is well-formed ----
    ids_file = Path(workspace) / "snippet_ids.txt"
    creds_id = None
    script_id = None
    
    try:
        content = ids_file.read_text().strip()
        lines = {line.split("=", 1)[0].strip(): line.split("=", 1)[1].strip()
                 for line in content.splitlines() if "=" in line}
        creds_id = lines.get("CREDS_SNIPPET_ID")
        script_id = lines.get("SCRIPT_SNIPPET_ID")
        
        if creds_id and script_id:
            checks.append({"name": "snippet_ids_file_format", "passed": True,
                           "detail": f"Found CREDS_SNIPPET_ID={creds_id}, SCRIPT_SNIPPET_ID={script_id}"})
        else:
            checks.append({"name": "snippet_ids_file_format", "passed": False,
                           "detail": f"Missing required keys. Found keys: {list(lines.keys())}"})
    except Exception as e:
        checks.append({"name": "snippet_ids_file_format", "passed": False,
                       "detail": f"Could not read snippet_ids.txt: {e}"})

    # Load all request logs and snippet store
    request_logs = load_jsonl("/tmp/snipit_requests.jsonl")
    snippets_store = load_snippets_store()
    
    create_events = [r for r in request_logs if r.get("event") == "create"]
    
    # ---- Check 2: Credentials snippet was created with correct flags ----
    creds_snippet = None
    if creds_id:
        creds_snippet = snippets_store.get(creds_id)
    
    if not creds_snippet and create_events:
        # Try to find it by content or properties
        for ev in create_events:
            body = ev.get("body", {})
            if (body.get("password") == "DrillP@ss2024!" or 
                body.get("burnAfterRead") == True):
                candidate = snippets_store.get(ev.get("id", ""))
                if candidate:
                    creds_snippet = candidate
                    creds_id = ev.get("id")
                    break
    
    # Check password on creds snippet
    try:
        has_password = (
            creds_snippet is not None and 
            creds_snippet.get("password") == "DrillP@ss2024!"
        )
        checks.append({
            "name": "creds_snippet_password_protected",
            "passed": has_password,
            "detail": (f"password field: {creds_snippet.get('password') if creds_snippet else 'N/A'}"
                      f" (expected: DrillP@ss2024!)")
        })
    except Exception as e:
        checks.append({"name": "creds_snippet_password_protected", "passed": False,
                       "detail": f"Error: {e}"})

    # Check burn-after-read on creds snippet
    try:
        has_burn = (
            creds_snippet is not None and 
            creds_snippet.get("burnAfterRead") == True
        )
        checks.append({
            "name": "creds_snippet_burn_after_read",
            "passed": has_burn,
            "detail": f"burnAfterRead: {creds_snippet.get('burnAfterRead') if creds_snippet else 'N/A'}"
        })
    except Exception as e:
        checks.append({"name": "creds_snippet_burn_after_read", "passed": False,
                       "detail": f"Error: {e}"})

    # Check expiry = "1w" (proprietary trap: must be exactly "1w", not "7d", "168h", etc.)
    try:
        expires_val = creds_snippet.get("expires") if creds_snippet else None
        has_correct_expiry = expires_val == "1w"
        checks.append({
            "name": "creds_snippet_expires_1w",
            "passed": has_correct_expiry,
            "detail": (f"expires field: '{expires_val}' "
                      f"(must be exactly '1w' per snipit's allowed values: 1h,6h,1d,3d,1w,2w,never)")
        })
    except Exception as e:
        checks.append({"name": "creds_snippet_expires_1w", "passed": False,
                       "detail": f"Error: {e}"})

    # Check title of creds snippet
    try:
        title_val = creds_snippet.get("title", "") if creds_snippet else ""
        has_title = "Prod DB Creds" in title_val and "Incident Drill" in title_val
        checks.append({
            "name": "creds_snippet_title",
            "passed": has_title,
            "detail": f"title: '{title_val}' (must contain 'Prod DB Creds' and 'Incident Drill')"
        })
    except Exception as e:
        checks.append({"name": "creds_snippet_title", "passed": False,
                       "detail": f"Error: {e}"})

    # Check content of creds snippet (must have actual file content)
    try:
        creds_content = creds_snippet.get("content", "") if creds_snippet else ""
        has_content = "DB_HOST" in creds_content and "payments_db" in creds_content
        checks.append({
            "name": "creds_snippet_has_file_content",
            "passed": has_content,
            "detail": f"content preview: '{creds_content[:80]}...'" if len(creds_content) > 80 else f"content: '{creds_content}'"
        })
    except Exception as e:
        checks.append({"name": "creds_snippet_has_file_content", "passed": False,
                       "detail": f"Error: {e}"})

    # ---- Check 3: Script snippet created via curl API fallback ----
    script_snippet = None
    if script_id:
        script_snippet = snippets_store.get(script_id)
    
    # Verify it's different from creds snippet
    try:
        are_different = (creds_id != script_id) and (creds_id is not None) and (script_id is not None)
        checks.append({
            "name": "two_distinct_snippets_created",
            "passed": are_different,
            "detail": f"creds_id={creds_id}, script_id={script_id}"
        })
    except Exception as e:
        checks.append({"name": "two_distinct_snippets_created", "passed": False,
                       "detail": f"Error: {e}"})

    # Check script snippet language = python
    try:
        lang_val = script_snippet.get("language", "") if script_snippet else ""
        has_python_lang = lang_val == "python"
        checks.append({
            "name": "script_snippet_language_python",
            "passed": has_python_lang,
            "detail": f"language: '{lang_val}' (expected: 'python')"
        })
    except Exception as e:
        checks.append({"name": "script_snippet_language_python", "passed": False,
                       "detail": f"Error: {e}"})

    # Check script snippet burn-after-read
    try:
        script_burn = script_snippet.get("burnAfterRead") if script_snippet else None
        has_script_burn = script_burn == True
        checks.append({
            "name": "script_snippet_burn_after_read",
            "passed": has_script_burn,
            "detail": f"burnAfterRead: {script_burn}"
        })
    except Exception as e:
        checks.append({"name": "script_snippet_burn_after_read", "passed": False,
                       "detail": f"Error: {e}"})

    # Check script snippet content
    try:
        script_content = script_snippet.get("content", "") if script_snippet else ""
        has_script_content = "reset_connection_pool" in script_content or "pg_terminate_backend" in script_content
        checks.append({
            "name": "script_snippet_has_file_content",
            "passed": has_script_content,
            "detail": f"content preview: '{script_content[:80]}...'" if len(script_content) > 80 else f"content: '{script_content}'"
        })
    except Exception as e:
        checks.append({"name": "script_snippet_has_file_content", "passed": False,
                       "detail": f"Error: {e}"})

    # ---- Check 4: Verify script snippet was created via curl (no password set) ----
    try:
        no_password = (
            script_snippet is not None and 
            not script_snippet.get("password")
        )
        checks.append({
            "name": "script_snippet_no_password",
            "passed": no_password,
            "detail": f"password field: {script_snippet.get('password') if script_snippet else 'N/A'} (should be absent/null)"
        })
    except Exception as e:
        checks.append({"name": "script_snippet_no_password", "passed": False,
                       "detail": f"Error: {e}"})

    # ---- Compute score ----
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    overall_passed = passed_count == total

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()