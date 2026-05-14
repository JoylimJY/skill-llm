import sys
import json
import os
from pathlib import Path

def find_storage_file(workspace: Path):
    """Search for the consensus-tools local storage JSON file."""
    candidates = [
        workspace / ".openclaw" / "consensus-tools.json",
        workspace / ".consensus" / "state.json",
        workspace / ".consensus" / "board.json",
    ]
    # Also search recursively for any consensus storage file
    for c in candidates:
        if c.exists():
            return c
    # Broader search
    for p in workspace.rglob("*.json"):
        try:
            data = json.loads(p.read_text())
            if "jobs" in data and isinstance(data["jobs"], (dict, list)):
                return p
        except Exception:
            continue
    return None

def evaluate(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0
    max_score = 0.0

    # ---------------------------------------------------------------
    # CHECK 1: pipeline_result.json exists at workspace root
    # ---------------------------------------------------------------
    max_score += 20
    result_file = workspace / "pipeline_result.json"
    # Also search recursively if not at root
    if not result_file.exists():
        found = list(workspace.rglob("pipeline_result.json"))
        if found:
            result_file = found[0]

    if result_file.exists():
        checks.append({
            "name": "pipeline_result.json exists",
            "passed": True,
            "detail": f"Found at {result_file}"
        })
        total_score += 20
    else:
        checks.append({
            "name": "pipeline_result.json exists",
            "passed": False,
            "detail": "pipeline_result.json not found anywhere in workspace"
        })

    # ---------------------------------------------------------------
    # CHECK 2: pipeline_result.json is valid JSON
    # ---------------------------------------------------------------
    max_score += 10
    result_data = None
    if result_file.exists():
        try:
            result_data = json.loads(result_file.read_text())
            checks.append({
                "name": "pipeline_result.json is valid JSON",
                "passed": True,
                "detail": f"Parsed successfully, keys: {list(result_data.keys()) if isinstance(result_data, dict) else 'array'}"
            })
            total_score += 10
        except Exception as e:
            checks.append({
                "name": "pipeline_result.json is valid JSON",
                "passed": False,
                "detail": f"JSON parse error: {e}"
            })
    else:
        checks.append({
            "name": "pipeline_result.json is valid JSON",
            "passed": False,
            "detail": "File does not exist, skipping parse check"
        })

    # ---------------------------------------------------------------
    # CHECK 3: consensus-tools was initialized (look for .consensus dir or storage)
    # ---------------------------------------------------------------
    max_score += 15
    consensus_dir = workspace / ".consensus"
    openclaw_dir = workspace / ".openclaw"
    storage_found = consensus_dir.exists() or openclaw_dir.exists() or find_storage_file(workspace) is not None

    if storage_found:
        detail_parts = []
        if consensus_dir.exists():
            detail_parts.append(f".consensus/ exists with: {[f.name for f in consensus_dir.rglob('*') if f.is_file()][:5]}")
        if openclaw_dir.exists():
            detail_parts.append(f".openclaw/ exists with: {[f.name for f in openclaw_dir.rglob('*') if f.is_file()][:5]}")
        checks.append({
            "name": "consensus-tools initialized (storage/dir present)",
            "passed": True,
            "detail": "; ".join(detail_parts) if detail_parts else "Storage file found"
        })
        total_score += 15
    else:
        checks.append({
            "name": "consensus-tools initialized (storage/dir present)",
            "passed": False,
            "detail": "Neither .consensus/ nor .openclaw/ directory found, and no storage JSON found"
        })

    # ---------------------------------------------------------------
    # CHECK 4: Find and parse local storage to verify job was posted
    # ---------------------------------------------------------------
    max_score += 20
    storage_file = find_storage_file(workspace)
    storage_data = None
    job_data = None

    if storage_file:
        try:
            storage_data = json.loads(storage_file.read_text())
        except Exception as e:
            storage_data = None
            checks.append({
                "name": "Local storage readable",
                "passed": False,
                "detail": f"Could not parse storage file {storage_file}: {e}"
            })

    # Try to find a job with HIGHEST_CONFIDENCE_SINGLE policy
    if storage_data:
        jobs = storage_data.get("jobs", {})
        if isinstance(jobs, list):
            jobs = {j.get("id", str(i)): j for i, j in enumerate(jobs)}
        
        for job_id, job in jobs.items():
            policy = ""
            if isinstance(job.get("policy"), str):
                policy = job["policy"]
            elif isinstance(job.get("policy"), dict):
                policy = job["policy"].get("type", "")
            elif isinstance(job.get("consensusPolicy"), dict):
                policy = job["consensusPolicy"].get("type", "")
            
            if "HIGHEST_CONFIDENCE" in policy.upper() or "HIGHEST_CONFIDENCE_SINGLE" in str(job).upper():
                job_data = job
                job_data["_id"] = job_id
                break
            # Fallback: look for title match
            if "Lead Compound" in str(job.get("title", "")) or "Phase I" in str(job.get("title", "")):
                job_data = job
                job_data["_id"] = job_id
                break

        if job_data:
            checks.append({
                "name": "Job posted with HIGHEST_CONFIDENCE_SINGLE policy",
                "passed": True,
                "detail": f"Job found: id={job_data.get('_id')}, policy={job_data.get('policy', job_data.get('consensusPolicy', 'unknown'))}"
            })
            total_score += 20
        else:
            # Check if any job was posted at all
            if jobs:
                checks.append({
                    "name": "Job posted with HIGHEST_CONFIDENCE_SINGLE policy",
                    "passed": False,
                    "detail": f"Jobs found but none with HIGHEST_CONFIDENCE_SINGLE policy. Found policies: {[j.get('policy', j.get('consensusPolicy', '?')) for j in list(jobs.values())[:3]]}"
                })
            else:
                checks.append({
                    "name": "Job posted with HIGHEST_CONFIDENCE_SINGLE policy",
                    "passed": False,
                    "detail": "No jobs found in storage"
                })
    else:
        checks.append({
            "name": "Job posted with HIGHEST_CONFIDENCE_SINGLE policy",
            "passed": False,
            "detail": "Storage data not available"
        })

    # ---------------------------------------------------------------
    # CHECK 5: Three submissions were created
    # ---------------------------------------------------------------
    max_score += 15
    submissions = []
    if storage_data and job_data:
        job_id = job_data.get("_id", "")
        # Submissions may be stored under the job or at top level
        subs_top = storage_data.get("submissions", {})
        if isinstance(subs_top, list):
            submissions = [s for s in subs_top if str(s.get("jobId", "")) == str(job_id)]
        elif isinstance(subs_top, dict):
            submissions = [s for s in subs_top.values() if str(s.get("jobId", "")) == str(job_id)]
        
        # Also check under job itself
        if not submissions:
            submissions = job_data.get("submissions", [])
            if isinstance(submissions, dict):
                submissions = list(submissions.values())

    if len(submissions) >= 3:
        checks.append({
            "name": "Three submissions created",
            "passed": True,
            "detail": f"Found {len(submissions)} submissions for the job"
        })
        total_score += 15
    elif len(submissions) > 0:
        checks.append({
            "name": "Three submissions created",
            "passed": False,
            "detail": f"Found only {len(submissions)} submission(s), expected at least 3"
        })
    else:
        checks.append({
            "name": "Three submissions created",
            "passed": False,
            "detail": "No submissions found for the job"
        })

    # ---------------------------------------------------------------
    # CHECK 6: Job was resolved
    # ---------------------------------------------------------------
    max_score += 10
    job_resolved = False
    if job_data:
        status = str(job_data.get("status", "")).upper()
        if status in ("RESOLVED", "CLOSED", "COMPLETE", "DONE", "FINISHED"):
            job_resolved = True
        # Also check for result field
        if job_data.get("result") or job_data.get("winner") or job_data.get("winnerSubmissionId"):
            job_resolved = True

    if job_resolved:
        checks.append({
            "name": "Job was resolved",
            "passed": True,
            "detail": f"Job status: {job_data.get('status', 'unknown')}, winner: {job_data.get('winner', job_data.get('winnerSubmissionId', 'see result field'))}"
        })
        total_score += 10
    else:
        checks.append({
            "name": "Job was resolved",
            "passed": False,
            "detail": f"Job status: {job_data.get('status', 'unknown') if job_data else 'job not found'}"
        })

    # ---------------------------------------------------------------
    # CHECK 7: pipeline_result.json references CPD-1002 as winner
    # (highest confidence 0.91 should win with HIGHEST_CONFIDENCE_SINGLE)
    # ---------------------------------------------------------------
    max_score += 10
    if result_data:
        result_str = json.dumps(result_data).lower()
        cpd1002_mentioned = "cpd-1002" in result_str or "cpd1002" in result_str
        if cpd1002_mentioned:
            checks.append({
                "name": "pipeline_result.json identifies CPD-1002 as winner",
                "passed": True,
                "detail": "CPD-1002 (highest confidence 0.91) correctly identified as winner in result"
            })
            total_score += 10
        else:
            checks.append({
                "name": "pipeline_result.json identifies CPD-1002 as winner",
                "passed": False,
                "detail": f"CPD-1002 not found in pipeline_result.json. Content snippet: {result_str[:300]}"
            })
    else:
        checks.append({
            "name": "pipeline_result.json identifies CPD-1002 as winner",
            "passed": False,
            "detail": "pipeline_result.json not available for winner check"
        })

    # ---------------------------------------------------------------
    # FINAL SCORING
    # ---------------------------------------------------------------
    all_passed = all(c["passed"] for c in checks)
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0

    output = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))
    return output

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)