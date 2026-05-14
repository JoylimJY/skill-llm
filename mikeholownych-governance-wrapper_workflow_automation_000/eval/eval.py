import json
import sys
import hashlib
from pathlib import Path

def sha256_of(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def hash_record(record: dict) -> str:
    serialized = json.dumps(record, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode()).hexdigest()

def run_eval(workspace: str):
    checks = []
    workspace = Path(workspace)
    evidence_log_path = workspace / "evidence" / "execution-evidence.log"
    
    # ── Check 1: analysis_result.json was created ────────────────────────────
    result_files = list(workspace.rglob("analysis_result.json"))
    result_file_found = len(result_files) > 0
    result_data = None
    if result_file_found:
        try:
            result_data = json.loads(result_files[0].read_text())
            checks.append({
                "name": "analysis_result.json exists and is valid JSON",
                "passed": True,
                "detail": f"Found at {result_files[0]}"
            })
        except Exception as e:
            checks.append({
                "name": "analysis_result.json exists and is valid JSON",
                "passed": False,
                "detail": f"File found but JSON parse failed: {e}"
            })
            result_data = None
    else:
        checks.append({
            "name": "analysis_result.json exists and is valid JSON",
            "passed": False,
            "detail": "No analysis_result.json found anywhere in workspace"
        })

    # ── Check 2: result has status=SUCCESS ───────────────────────────────────
    if result_data:
        status_ok = result_data.get("status") == "SUCCESS"
        checks.append({
            "name": "analysis_result.json reports SUCCESS status",
            "passed": status_ok,
            "detail": f"status={result_data.get('status')}"
        })
    else:
        checks.append({
            "name": "analysis_result.json reports SUCCESS status",
            "passed": False,
            "detail": "No result data to check"
        })

    # ── Check 3: correct skill (contract.analysis or clause.extraction) ──────
    ALLOWED_SKILLS = {
        "contract.analysis", "legal.research", "clause.extraction",
        "risk.scoring", "precedent.lookup"
    }
    if result_data:
        used_skill = result_data.get("skill", "")
        skill_ok = used_skill in ALLOWED_SKILLS
        checks.append({
            "name": "Correct allowlisted skill was used",
            "passed": skill_ok,
            "detail": f"skill='{used_skill}'. Allowed: {sorted(ALLOWED_SKILLS)}"
        })
    else:
        checks.append({
            "name": "Correct allowlisted skill was used",
            "passed": False,
            "detail": "No result data to check skill"
        })

    # ── Check 4: model lock is opencode/big-pickle ───────────────────────────
    if result_data:
        model_used = result_data.get("model", "")
        model_ok = model_used == "opencode/big-pickle"
        checks.append({
            "name": "Model lock is opencode/big-pickle",
            "passed": model_ok,
            "detail": f"model='{model_used}'"
        })
    else:
        checks.append({
            "name": "Model lock is opencode/big-pickle",
            "passed": False,
            "detail": "No result data to check model"
        })

    # ── Check 5: temperature is 0.0 ──────────────────────────────────────────
    if result_data:
        temp_used = result_data.get("temperature", None)
        temp_ok = temp_used == 0.0
        checks.append({
            "name": "Temperature lock is 0.0",
            "passed": temp_ok,
            "detail": f"temperature={temp_used}"
        })
    else:
        checks.append({
            "name": "Temperature lock is 0.0",
            "passed": False,
            "detail": "No result data to check temperature"
        })

    # ── Check 6: schema is execution-evidence.v1 ─────────────────────────────
    if result_data:
        schema_used = result_data.get("schema", "")
        schema_ok = schema_used == "execution-evidence.v1"
        checks.append({
            "name": "Schema is execution-evidence.v1",
            "passed": schema_ok,
            "detail": f"schema='{schema_used}'"
        })
    else:
        checks.append({
            "name": "Schema is execution-evidence.v1",
            "passed": False,
            "detail": "No result data to check schema"
        })

    # ── Check 7: evidence log exists and has at least one SUCCESS entry ───────
    evidence_ok = False
    evidence_entry = None
    try:
        if evidence_log_path.exists():
            lines = [l.strip() for l in evidence_log_path.read_text().splitlines() if l.strip()]
            for line in lines:
                try:
                    entry = json.loads(line)
                    if entry.get("status") == "SUCCESS" and entry.get("schema") == "execution-evidence.v1":
                        evidence_entry = entry
                        evidence_ok = True
                        break
                except Exception:
                    continue
        checks.append({
            "name": "Evidence log contains a SUCCESS execution-evidence.v1 entry",
            "passed": evidence_ok,
            "detail": f"Log path: {evidence_log_path}. Entry found: {evidence_entry is not None}"
        })
    except Exception as e:
        checks.append({
            "name": "Evidence log contains a SUCCESS execution-evidence.v1 entry",
            "passed": False,
            "detail": f"Error reading evidence log: {e}"
        })

    # ── Check 8: hash chain integrity ─────────────────────────────────────────
    chain_ok = False
    chain_detail = "Evidence log not readable"
    try:
        if evidence_log_path.exists():
            lines = [l.strip() for l in evidence_log_path.read_text().splitlines() if l.strip()]
            records = []
            for line in lines:
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
            
            # Verify each record's evidence_hash is correct
            if records:
                chain_broken = False
                for i, rec in enumerate(records):
                    stored_hash = rec.get("evidence_hash", "")
                    # Reconstruct the record without evidence_hash for re-hashing
                    rec_copy = {k: v for k, v in rec.items() if k != "evidence_hash"}
                    computed_hash = hash_record(rec_copy)
                    if stored_hash != computed_hash:
                        chain_broken = True
                        chain_detail = f"Hash mismatch at record {i}: stored={stored_hash[:16]}... computed={computed_hash[:16]}..."
                        break
                    # Verify prev_hash chain
                    if i > 0:
                        expected_prev = records[i-1].get("evidence_hash", "")
                        actual_prev = rec.get("prev_hash", "")
                        if actual_prev != expected_prev:
                            chain_broken = True
                            chain_detail = f"Chain break at record {i}: prev_hash={actual_prev[:16]}... expected={expected_prev[:16]}..."
                            break
                if not chain_broken:
                    chain_ok = True
                    chain_detail = f"Hash chain verified across {len(records)} record(s)"
            else:
                chain_detail = "No parseable records in evidence log"
    except Exception as e:
        chain_detail = f"Error verifying hash chain: {e}"
    
    checks.append({
        "name": "Evidence log hash chain is intact",
        "passed": chain_ok,
        "detail": chain_detail
    })

    # ── Check 9: evidence_hash in result matches what's in the log ───────────
    if result_data and evidence_entry:
        result_hash = result_data.get("evidence_hash", "")
        log_hash = evidence_entry.get("evidence_hash", "")
        hash_match = result_hash == log_hash and result_hash != ""
        checks.append({
            "name": "evidence_hash in result file matches the evidence log entry",
            "passed": hash_match,
            "detail": f"result_hash={result_hash[:16]}... log_hash={log_hash[:16]}..."
        })
    else:
        checks.append({
            "name": "evidence_hash in result file matches the evidence log entry",
            "passed": False,
            "detail": "Missing result data or evidence entry to compare"
        })

    # ── Final scoring ────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    output = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "workspace arg", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    run_eval(sys.argv[1])