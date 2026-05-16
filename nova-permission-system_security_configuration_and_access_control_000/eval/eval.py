import sys
import json
import os
from pathlib import Path

def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return None, str(e)

def check_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"
    except Exception as e:
        return None, str(e)

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    data_dir = workspace / "data"
    agents_md_path = workspace / "AGENTS.md"

    checks = []
    total_score = 0.0
    max_checks = 0

    # -----------------------------------------------------------------------
    # CHECK 1: users.json exists in /workspace/data/ and has correct structure
    # -----------------------------------------------------------------------
    max_checks += 1
    users_path = data_dir / "users.json"
    users_data, users_err = check_json(users_path)
    
    if users_data is None:
        checks.append({
            "name": "users.json: exists and valid JSON",
            "passed": False,
            "detail": users_err or "File missing or invalid"
        })
    else:
        checks.append({
            "name": "users.json: exists and valid JSON",
            "passed": True,
            "detail": f"Found at {users_path}"
        })
        total_score += 1

    # CHECK 2: users.json is a list with at least one user with correct owner fields
    max_checks += 1
    if users_data is not None and isinstance(users_data, list) and len(users_data) > 0:
        owner = None
        for u in users_data:
            if isinstance(u, dict) and u.get("role") == "owner":
                owner = u
                break
        if owner is None:
            checks.append({
                "name": "users.json: contains owner role user with correct schema",
                "passed": False,
                "detail": f"No user with role='owner' found. Data: {users_data}"
            })
        else:
            required_keys = {"user_id", "name", "role", "created_at", "verified"}
            missing_keys = required_keys - set(owner.keys())
            wrong_role = owner.get("role") != "owner"
            verified_wrong = owner.get("verified") is not True
            
            if missing_keys:
                checks.append({
                    "name": "users.json: contains owner role user with correct schema",
                    "passed": False,
                    "detail": f"Owner user missing keys: {missing_keys}. Found: {owner}"
                })
            elif wrong_role:
                checks.append({
                    "name": "users.json: contains owner role user with correct schema",
                    "passed": False,
                    "detail": f"Owner role incorrect: {owner.get('role')}"
                })
            elif verified_wrong:
                checks.append({
                    "name": "users.json: contains owner role user with correct schema",
                    "passed": False,
                    "detail": f"Owner verified should be true, got: {owner.get('verified')}"
                })
            else:
                checks.append({
                    "name": "users.json: contains owner role user with correct schema",
                    "passed": True,
                    "detail": f"Owner user found: user_id={owner.get('user_id')}, verified=true"
                })
                total_score += 1
    else:
        checks.append({
            "name": "users.json: contains owner role user with correct schema",
            "passed": False,
            "detail": f"users.json is not a non-empty list. Got: {type(users_data)}"
        })

    # -----------------------------------------------------------------------
    # CHECK 3: accounts.json exists in /workspace/data/ and is a LIST
    # -----------------------------------------------------------------------
    max_checks += 1
    accounts_path = data_dir / "accounts.json"
    accounts_data, accounts_err = check_json(accounts_path)
    
    if accounts_data is None:
        checks.append({
            "name": "accounts.json: exists, valid JSON, and is a list",
            "passed": False,
            "detail": accounts_err or "File missing"
        })
    elif not isinstance(accounts_data, list):
        checks.append({
            "name": "accounts.json: exists, valid JSON, and is a list",
            "passed": False,
            "detail": f"accounts.json must be a JSON array (list), got {type(accounts_data).__name__}"
        })
    else:
        checks.append({
            "name": "accounts.json: exists, valid JSON, and is a list",
            "passed": True,
            "detail": f"accounts.json is a valid list with {len(accounts_data)} entries"
        })
        total_score += 1

    # CHECK 4: accounts.json has at least one entry with correct fields
    max_checks += 1
    if accounts_data is not None and isinstance(accounts_data, list) and len(accounts_data) > 0:
        account = accounts_data[0]
        required_acct_keys = {"account_id", "platform", "open_id", "user_id"}
        missing_acct_keys = required_acct_keys - set(account.keys())
        if missing_acct_keys:
            checks.append({
                "name": "accounts.json: first entry has required fields",
                "passed": False,
                "detail": f"Missing keys: {missing_acct_keys}. Found: {account}"
            })
        else:
            # user_id must match a user in users.json
            if users_data and isinstance(users_data, list):
                user_ids = {u.get("user_id") for u in users_data if isinstance(u, dict)}
                if account.get("user_id") not in user_ids:
                    checks.append({
                        "name": "accounts.json: first entry has required fields",
                        "passed": False,
                        "detail": f"account user_id '{account.get('user_id')}' not found in users.json (known: {user_ids})"
                    })
                else:
                    checks.append({
                        "name": "accounts.json: first entry has required fields",
                        "passed": True,
                        "detail": f"Account entry valid: {account}"
                    })
                    total_score += 1
            else:
                checks.append({
                    "name": "accounts.json: first entry has required fields",
                    "passed": True,
                    "detail": f"Account entry has required fields: {account}"
                })
                total_score += 1
    else:
        checks.append({
            "name": "accounts.json: first entry has required fields",
            "passed": False,
            "detail": "accounts.json empty or not a list"
        })

    # -----------------------------------------------------------------------
    # CHECK 5: permissions.json exists and has correct role structure
    # -----------------------------------------------------------------------
    max_checks += 1
    perms_path = data_dir / "permissions.json"
    perms_data, perms_err = check_json(perms_path)
    
    if perms_data is None:
        checks.append({
            "name": "permissions.json: exists and valid JSON",
            "passed": False,
            "detail": perms_err or "File missing"
        })
    else:
        checks.append({
            "name": "permissions.json: exists and valid JSON",
            "passed": True,
            "detail": f"Found at {perms_path}"
        })
        total_score += 1

    # CHECK 6: permissions.json has correct role permission values (the proprietary trap)
    max_checks += 1
    if perms_data is not None and isinstance(perms_data, dict):
        roles = perms_data.get("roles", {})
        errors = []
        
        # owner: all true
        owner_perms = roles.get("owner", {})
        for perm in ["read", "write", "admin", "execute"]:
            if owner_perms.get(perm) is not True:
                errors.append(f"owner.{perm} should be true, got {owner_perms.get(perm)}")
        
        # friend: read=true, write=false, admin=false, execute=true
        friend_perms = roles.get("friend", {})
        expected_friend = {"read": True, "write": False, "admin": False, "execute": True}
        for perm, expected_val in expected_friend.items():
            if friend_perms.get(perm) is not expected_val:
                errors.append(f"friend.{perm} should be {expected_val}, got {friend_perms.get(perm)}")
        
        # stranger: all false
        stranger_perms = roles.get("stranger", {})
        for perm in ["read", "write", "admin", "execute"]:
            if stranger_perms.get(perm) is not False:
                errors.append(f"stranger.{perm} should be false, got {stranger_perms.get(perm)}")
        
        if errors:
            checks.append({
                "name": "permissions.json: role permission values are correct",
                "passed": False,
                "detail": "Errors: " + "; ".join(errors)
            })
        else:
            checks.append({
                "name": "permissions.json: role permission values are correct",
                "passed": True,
                "detail": "All role permissions match specification"
            })
            total_score += 1
    else:
        checks.append({
            "name": "permissions.json: role permission values are correct",
            "passed": False,
            "detail": f"permissions.json invalid or missing roles. Got: {perms_data}"
        })

    # CHECK 7: permissions.json has test_mode field (boolean)
    max_checks += 1
    if perms_data is not None and isinstance(perms_data, dict):
        if "test_mode" not in perms_data:
            checks.append({
                "name": "permissions.json: has test_mode field",
                "passed": False,
                "detail": f"'test_mode' key missing from permissions.json. Keys found: {list(perms_data.keys())}"
            })
        elif not isinstance(perms_data.get("test_mode"), bool):
            checks.append({
                "name": "permissions.json: has test_mode field",
                "passed": False,
                "detail": f"test_mode must be boolean, got {type(perms_data.get('test_mode')).__name__}: {perms_data.get('test_mode')}"
            })
        else:
            checks.append({
                "name": "permissions.json: has test_mode field",
                "passed": True,
                "detail": f"test_mode={perms_data.get('test_mode')}"
            })
            total_score += 1
    else:
        checks.append({
            "name": "permissions.json: has test_mode field",
            "passed": False,
            "detail": "permissions.json invalid or missing"
        })

    # CHECK 8: permissions.json has whitelist field (list)
    max_checks += 1
    if perms_data is not None and isinstance(perms_data, dict):
        if "whitelist" not in perms_data:
            checks.append({
                "name": "permissions.json: has whitelist field (list)",
                "passed": False,
                "detail": f"'whitelist' key missing. Keys found: {list(perms_data.keys())}"
            })
        elif not isinstance(perms_data.get("whitelist"), list):
            checks.append({
                "name": "permissions.json: has whitelist field (list)",
                "passed": False,
                "detail": f"whitelist must be a list, got {type(perms_data.get('whitelist')).__name__}"
            })
        else:
            checks.append({
                "name": "permissions.json: has whitelist field (list)",
                "passed": True,
                "detail": f"whitelist={perms_data.get('whitelist')}"
            })
            total_score += 1
    else:
        checks.append({
            "name": "permissions.json: has whitelist field (list)",
            "passed": False,
            "detail": "permissions.json invalid or missing"
        })

    # -----------------------------------------------------------------------
    # CHECK 9: approvals.json exists and is an empty list []
    # -----------------------------------------------------------------------
    max_checks += 1
    approvals_path = data_dir / "approvals.json"
    approvals_data, approvals_err = check_json(approvals_path)
    
    if approvals_data is None:
        checks.append({
            "name": "approvals.json: exists and is an empty list []",
            "passed": False,
            "detail": approvals_err or "File missing"
        })
    elif not isinstance(approvals_data, list):
        checks.append({
            "name": "approvals.json: exists and is an empty list []",
            "passed": False,
            "detail": f"approvals.json must be a JSON array [], got {type(approvals_data).__name__}: {approvals_data}"
        })
    else:
        checks.append({
            "name": "approvals.json: exists and is an empty list []",
            "passed": True,
            "detail": f"approvals.json is a valid list with {len(approvals_data)} entries (empty init is correct)"
        })
        total_score += 1

    # -----------------------------------------------------------------------
    # CHECK 10: AGENTS.md contains the security-rules-start/end block
    # -----------------------------------------------------------------------
    max_checks += 1
    try:
        agents_md_content = agents_md_path.read_text(encoding="utf-8")
        has_start = "<!-- security-rules-start -->" in agents_md_content
        has_end = "<!-- security-rules-end -->" in agents_md_content
        
        if not has_start or not has_end:
            checks.append({
                "name": "AGENTS.md: contains security-rules comment markers",
                "passed": False,
                "detail": f"Missing markers. has_start={has_start}, has_end={has_end}"
            })
        else:
            checks.append({
                "name": "AGENTS.md: contains security-rules comment markers",
                "passed": True,
                "detail": "Both <!-- security-rules-start --> and <!-- security-rules-end --> found"
            })
            total_score += 1
    except FileNotFoundError:
        checks.append({
            "name": "AGENTS.md: contains security-rules comment markers",
            "passed": False,
            "detail": f"AGENTS.md not found at {agents_md_path}"
        })
    except Exception as e:
        checks.append({
            "name": "AGENTS.md: contains security-rules comment markers",
            "passed": False,
            "detail": f"Error reading AGENTS.md: {e}"
        })

    # CHECK 11: AGENTS.md security block contains permission-gate mention and identity-management mention
    max_checks += 1
    try:
        agents_md_content = agents_md_path.read_text(encoding="utf-8")
        # Extract the content between the markers
        start_marker = "<!-- security-rules-start -->"
        end_marker = "<!-- security-rules-end -->"
        
        if start_marker in agents_md_content and end_marker in agents_md_content:
            start_idx = agents_md_content.index(start_marker)
            end_idx = agents_md_content.index(end_marker)
            security_block = agents_md_content[start_idx:end_idx + len(end_marker)]
            
            has_permission_gate = "permission-gate" in security_block
            has_identity_mgmt = "identity-management" in security_block
            has_security_heading = "Security Rules" in security_block
            
            if has_permission_gate and has_identity_mgmt and has_security_heading:
                checks.append({
                    "name": "AGENTS.md: security block contains required content",
                    "passed": True,
                    "detail": "Security block has permission-gate, identity-management, and Security Rules heading"
                })
                total_score += 1
            else:
                checks.append({
                    "name": "AGENTS.md: security block contains required content",
                    "passed": False,
                    "detail": f"Missing content: has_permission_gate={has_permission_gate}, has_identity_mgmt={has_identity_mgmt}, has_security_heading={has_security_heading}"
                })
        else:
            checks.append({
                "name": "AGENTS.md: security block contains required content",
                "passed": False,
                "detail": "Security markers not found in AGENTS.md"
            })
    except FileNotFoundError:
        checks.append({
            "name": "AGENTS.md: security block contains required content",
            "passed": False,
            "detail": "AGENTS.md not found"
        })
    except Exception as e:
        checks.append({
            "name": "AGENTS.md: security block contains required content",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 12: End-to-end functional test - authenticate() works with correct data
    # -----------------------------------------------------------------------
    max_checks += 1
    try:
        import sys as _sys
        _sys.path.insert(0, str(workspace / "nova-permission-system"))
        os.environ["NOVA_DATA_DIR"] = str(data_dir)
        
        # Only run if all data files seem valid
        if (users_data is not None and isinstance(users_data, list) and 
            accounts_data is not None and isinstance(accounts_data, list) and len(accounts_data) > 0 and
            perms_data is not None):
            
            from permission_check.main import authenticate
            
            # Get the owner's open_id from accounts
            owner_account = None
            if users_data and accounts_data:
                owner_user_ids = {u.get("user_id") for u in users_data if isinstance(u, dict) and u.get("role") == "owner"}
                for acct in accounts_data:
                    if isinstance(acct, dict) and acct.get("user_id") in owner_user_ids:
                        owner_account = acct
                        break
            
            if owner_account is None:
                checks.append({
                    "name": "Functional test: authenticate() correctly allows owner write permission",
                    "passed": False,
                    "detail": "Could not find owner account in accounts.json to run functional test"
                })
            else:
                result = authenticate({
                    "open_id": owner_account.get("open_id"),
                    "platform": owner_account.get("platform"),
                    "permission": "write"
                })
                
                if result.get("allowed") is True and result.get("role") == "owner":
                    checks.append({
                        "name": "Functional test: authenticate() correctly allows owner write permission",
                        "passed": True,
                        "detail": f"authenticate() returned allowed=True for owner with write permission. Result: {result}"
                    })
                    total_score += 1
                else:
                    checks.append({
                        "name": "Functional test: authenticate() correctly allows owner write permission",
                        "passed": False,
                        "detail": f"Expected allowed=True, role=owner. Got: {result}"
                    })
        else:
            checks.append({
                "name": "Functional test: authenticate() correctly allows owner write permission",
                "passed": False,
                "detail": "Skipped: prerequisite data files are invalid or missing"
            })
    except Exception as e:
        checks.append({
            "name": "Functional test: authenticate() correctly allows owner write permission",
            "passed": False,
            "detail": f"Exception during functional test: {type(e).__name__}: {e}"
        })

    # CHECK 13: Functional test - stranger is denied read permission
    max_checks += 1
    try:
        if perms_data is not None and isinstance(perms_data, dict):
            from permission_check.main import authenticate
            result_stranger = authenticate({
                "open_id": "nonexistent_stranger_xyz_999",
                "platform": "feishu",
                "permission": "read"
            })
            # A stranger (unknown account) should be denied
            if result_stranger.get("allowed") is False:
                checks.append({
                    "name": "Functional test: authenticate() correctly denies unknown user",
                    "passed": True,
                    "detail": f"Correctly denied unknown user. Result: {result_stranger}"
                })
                total_score += 1
            else:
                checks.append({
                    "name": "Functional test: authenticate() correctly denies unknown user",
                    "passed": False,
                    "detail": f"Expected allowed=False for unknown user, got: {result_stranger}"
                })
        else:
            checks.append({
                "name": "Functional test: authenticate() correctly denies unknown user",
                "passed": False,
                "detail": "Skipped: permissions.json invalid"
            })
    except Exception as e:
        checks.append({
            "name": "Functional test: authenticate() correctly denies unknown user",
            "passed": False,
            "detail": f"Exception: {type(e).__name__}: {e}"
        })

    # -----------------------------------------------------------------------
    # Final scoring
    # -----------------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    score = total_score / max_checks if max_checks > 0 else 0.0
    overall_passed = passed_checks >= 10  # Must pass at least 10/13 checks

    result = {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()