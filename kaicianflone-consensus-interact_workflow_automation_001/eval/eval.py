import sys
import json
import os
import subprocess
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    overall_passed = True

    def add_check(name, passed, detail):
        nonlocal overall_passed
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            overall_passed = False

    # ---- Check 1: consensus-tools init was run (`.consensus/` directory exists) ----
    consensus_dir = None
    # Search for .consensus directory anywhere in workspace
    for root, dirs, files in os.walk(workspace):
        if '.consensus' in dirs:
            consensus_dir = os.path.join(root, '.consensus')
            break
    
    if consensus_dir:
        add_check("consensus_init_ran", True, f"Found .consensus directory at {consensus_dir}")
    else:
        add_check("consensus_init_ran", False, "No .consensus directory found; `consensus-tools init` was likely not run")

    # ---- Check 2: SQLite storage backend used ----
    # Look for consensus-tools storage config or SQLite files
    sqlite_found = False
    sqlite_detail = "No SQLite database file found"
    
    # Check for .db or .sqlite files related to consensus
    for root, dirs, files in os.walk(workspace):
        for f in files:
            if f.endswith('.db') or f.endswith('.sqlite') or f.endswith('.sqlite3'):
                if 'consensus' in f.lower() or 'consensus' in root.lower():
                    sqlite_found = True
                    sqlite_detail = f"Found SQLite file: {os.path.join(root, f)}"
                    break
            # Also check for JSON config that specifies sqlite
            if f.endswith('.json') and ('consensus' in f.lower() or 'openclaw' in root.lower()):
                try:
                    with open(os.path.join(root, f)) as fh:
                        data = json.load(fh)
                    # Check nested config for sqlite kind
                    config_str = json.dumps(data)
                    if '"sqlite"' in config_str or "'sqlite'" in config_str:
                        sqlite_found = True
                        sqlite_detail = f"Found sqlite config in {os.path.join(root, f)}"
                        break
                except Exception:
                    pass
        if sqlite_found:
            break
    
    # Also look in ~/.openclaw if it exists
    openclaw_home = Path.home() / ".openclaw"
    if openclaw_home.exists():
        for f in openclaw_home.rglob("*"):
            if f.suffix in ('.db', '.sqlite', '.sqlite3'):
                sqlite_found = True
                sqlite_detail = f"Found SQLite file: {f}"
                break
            if f.suffix == '.json' and 'consensus' in str(f).lower():
                try:
                    data = json.loads(f.read_text())
                    if 'sqlite' in json.dumps(data):
                        sqlite_found = True
                        sqlite_detail = f"Found sqlite config in {f}"
                        break
                except Exception:
                    pass

    add_check("sqlite_storage_backend", sqlite_found, sqlite_detail)

    # ---- Check 3: Output file `consensus_verdict.json` exists ----
    verdict_files = list(Path(workspace).rglob("consensus_verdict.json"))
    
    if not verdict_files:
        add_check("output_file_exists", False, "consensus_verdict.json not found anywhere in workspace")
        add_check("output_has_job_result", False, "Cannot check content - file not found")
        add_check("approval_vote_policy_used", False, "Cannot check policy - file not found")
        add_check("winning_submission_identified", False, "Cannot check winner - file not found")
        add_check("votes_recorded", False, "Cannot check votes - file not found")
    else:
        verdict_path = verdict_files[0]
        add_check("output_file_exists", True, f"Found consensus_verdict.json at {verdict_path}")
        
        try:
            with open(verdict_path) as f:
                verdict = json.load(f)
            
            verdict_str = json.dumps(verdict).lower()

            # Check 4: File contains a job result (has jobId or id or result fields)
            has_result_structure = any(
                k in verdict for k in ['jobId', 'job_id', 'id', 'result', 'winner', 'winningSubmission', 'submission']
            )
            # Also accept if it's a nested object that has these
            if not has_result_structure:
                for v in verdict.values() if isinstance(verdict, dict) else []:
                    if isinstance(v, dict) and any(k in v for k in ['jobId', 'id', 'result', 'winner']):
                        has_result_structure = True
                        break
            
            add_check(
                "output_has_job_result",
                has_result_structure,
                f"Result structure check: keys found = {list(verdict.keys()) if isinstance(verdict, dict) else 'non-dict'}"
            )

            # Check 5: APPROVAL_VOTE policy was used
            approval_vote_present = (
                'approval_vote' in verdict_str or 
                'approvalvote' in verdict_str or
                'approval' in verdict_str
            )
            add_check(
                "approval_vote_policy_used",
                approval_vote_present,
                f"APPROVAL_VOTE policy reference found in verdict: {approval_vote_present}"
            )

            # Check 6: There is a winning submission identified
            winner_present = any(
                kw in verdict_str for kw in ['winner', 'winning', 'resolved', 'selected', 'result']
            )
            add_check(
                "winning_submission_identified",
                winner_present,
                f"Winner/result reference found in verdict: {winner_present}"
            )

            # Check 7: Votes appear to have been cast (yes/no votes recorded in some way)
            # Check for vote counts or vote data in verdict
            votes_present = any(
                kw in verdict_str for kw in ['vote', 'yes', 'score', 'tally', 'ballot']
            )
            add_check(
                "votes_recorded",
                votes_present,
                f"Vote-related data found in verdict: {votes_present}"
            )

        except json.JSONDecodeError as e:
            add_check("output_has_job_result", False, f"consensus_verdict.json is not valid JSON: {e}")
            add_check("approval_vote_policy_used", False, "Cannot parse file")
            add_check("winning_submission_identified", False, "Cannot parse file")
            add_check("votes_recorded", False, "Cannot parse file")
        except Exception as e:
            add_check("output_has_job_result", False, f"Unexpected error reading file: {e}")
            add_check("approval_vote_policy_used", False, f"Error: {e}")
            add_check("winning_submission_identified", False, f"Error: {e}")
            add_check("votes_recorded", False, f"Error: {e}")

    # ---- Check 8: Verify that two submissions were created (for the two agents) ----
    # Look for any evidence of submissions (could be in storage file, sqlite, or logs)
    submissions_evidence = False
    submissions_detail = "No evidence of two submissions found"
    
    # Check workspace for any consensus storage files
    storage_paths = []
    for root, dirs, files in os.walk(workspace):
        for f in files:
            if 'consensus' in f.lower() and f.endswith('.json'):
                storage_paths.append(os.path.join(root, f))
    
    # Also check home dir
    for f in Path.home().rglob("consensus*.json"):
        storage_paths.append(str(f))
    for f in Path.home().rglob("*.json"):
        if 'openclaw' in str(f) or 'consensus' in str(f):
            storage_paths.append(str(f))
    
    for sp in storage_paths:
        try:
            with open(sp) as fh:
                data = json.load(fh)
            data_str = json.dumps(data)
            # If we see submissions array with 2+ entries
            if '"submissions"' in data_str:
                # Try to count submissions
                if isinstance(data, dict):
                    subs = data.get('submissions', [])
                    if isinstance(subs, list) and len(subs) >= 2:
                        submissions_evidence = True
                        submissions_detail = f"Found {len(subs)} submissions in {sp}"
                        break
                    elif isinstance(subs, dict) and len(subs) >= 2:
                        submissions_evidence = True
                        submissions_detail = f"Found {len(subs)} submissions in {sp}"
                        break
        except Exception:
            pass
    
    # Also check SQLite files
    if not submissions_evidence:
        for root, dirs, files in os.walk(workspace):
            for f in files:
                if f.endswith('.db') or f.endswith('.sqlite') or f.endswith('.sqlite3'):
                    db_path = os.path.join(root, f)
                    try:
                        result = subprocess.run(
                            ['sqlite3', db_path, 'SELECT COUNT(*) FROM submissions;'],
                            capture_output=True, text=True, timeout=5
                        )
                        count = int(result.stdout.strip())
                        if count >= 2:
                            submissions_evidence = True
                            submissions_detail = f"Found {count} submissions in SQLite DB {db_path}"
                            break
                    except Exception:
                        pass
            if submissions_evidence:
                break
        
        # Also check home dir for sqlite
        if not submissions_evidence:
            for f in Path.home().rglob("*.db"):
                try:
                    result = subprocess.run(
                        ['sqlite3', str(f), 'SELECT COUNT(*) FROM submissions;'],
                        capture_output=True, text=True, timeout=5
                    )
                    count = int(result.stdout.strip())
                    if count >= 2:
                        submissions_evidence = True
                        submissions_detail = f"Found {count} submissions in SQLite DB {f}"
                        break
                except Exception:
                    pass

    add_check("two_submissions_created", submissions_evidence, submissions_detail)

    # ---- Check 9: Votes were cast (3 votes expected from task spec) ----
    votes_count_ok = False
    votes_count_detail = "Could not verify vote count"
    
    for sp in storage_paths:
        try:
            with open(sp) as fh:
                data = json.load(fh)
            data_str = json.dumps(data)
            if '"votes"' in data_str:
                if isinstance(data, dict):
                    votes = data.get('votes', [])
                    if isinstance(votes, list) and len(votes) >= 3:
                        votes_count_ok = True
                        votes_count_detail = f"Found {len(votes)} votes in storage"
                        break
                    elif isinstance(votes, dict) and len(votes) >= 3:
                        votes_count_ok = True
                        votes_count_detail = f"Found {len(votes)} votes in storage"
                        break
        except Exception:
            pass
    
    if not votes_count_ok:
        for root, dirs, files in os.walk(workspace):
            for f in files:
                if f.endswith('.db') or f.endswith('.sqlite') or f.endswith('.sqlite3'):
                    db_path = os.path.join(root, f)
                    try:
                        result = subprocess.run(
                            ['sqlite3', db_path, 'SELECT COUNT(*) FROM votes;'],
                            capture_output=True, text=True, timeout=5
                        )
                        count = int(result.stdout.strip())
                        if count >= 3:
                            votes_count_ok = True
                            votes_count_detail = f"Found {count} votes in SQLite DB"
                            break
                    except Exception:
                        pass
            if votes_count_ok:
                break
        
        if not votes_count_ok:
            for f in Path.home().rglob("*.db"):
                try:
                    result = subprocess.run(
                        ['sqlite3', str(f), 'SELECT COUNT(*) FROM votes;'],
                        capture_output=True, text=True, timeout=5
                    )
                    count = int(result.stdout.strip())
                    if count >= 3:
                        votes_count_ok = True
                        votes_count_detail = f"Found {count} votes in SQLite DB"
                        break
                except Exception:
                    pass

    add_check("three_votes_cast", votes_count_ok, votes_count_detail)

    # Calculate score
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))