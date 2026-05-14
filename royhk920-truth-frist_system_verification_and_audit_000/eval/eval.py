import sys
import json
import re
from pathlib import Path

def main(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    score = 0.0

    # Locate audit_findings.md
    findings_files = list(workspace.rglob("audit_findings.md"))
    if not findings_files:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "audit_findings.md not found anywhere in workspace."}]
        }))
        return

    findings_path = findings_files[0]
    try:
        content = findings_path.read_text(encoding="utf-8")
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read audit_findings.md: {e}"}]
        }))
        return

    content_lower = content.lower()

    # -----------------------------------------------------------------------
    # CHECK 1: File exists and is non-trivial
    # -----------------------------------------------------------------------
    c1_passed = len(content.strip()) > 100
    checks.append({
        "name": "file_exists_and_non_trivial",
        "passed": c1_passed,
        "detail": f"audit_findings.md found at {findings_path}. Length: {len(content)} chars."
    })
    if c1_passed:
        score += 0.5

    # -----------------------------------------------------------------------
    # CHECK 2: Uses classification labels Verified / Inferred / Unknown
    # The SKILL.md mandates exactly these three labels.
    # -----------------------------------------------------------------------
    has_verified = bool(re.search(r'\bverified\b', content_lower))
    has_inferred = bool(re.search(r'\binferred\b', content_lower))
    has_unknown  = bool(re.search(r'\bunknown\b', content_lower))
    c2_passed = has_verified and has_inferred and has_unknown
    checks.append({
        "name": "uses_required_classification_labels",
        "passed": c2_passed,
        "detail": (
            f"Verified present: {has_verified}, Inferred present: {has_inferred}, "
            f"Unknown present: {has_unknown}. All three required by SKILL.md framework."
        )
    })
    if c2_passed:
        score += 1.0

    # -----------------------------------------------------------------------
    # CHECK 3: Claim 1 — PID file missing → service running status is Unknown
    # The PID file /workspace/pipeline/ingestor/ingestor.pid does NOT exist.
    # Agent must not claim the service is verified as running.
    # -----------------------------------------------------------------------
    pid_section = re.search(
        r'(claim\s*1|pid|ingestor\.pid|service.*running|running.*service).{0,600}',
        content_lower, re.DOTALL
    )
    # Must mention ingestor.pid and classify as Unknown (or at most Inferred, not Verified)
    mentions_pid = 'ingestor.pid' in content_lower
    # Should NOT say "verified" in close proximity to pid/claim 1 saying it IS running
    pid_not_wrongly_verified = not bool(re.search(
        r'(claim\s*1|ingestor\.pid).{0,200}verified.{0,50}(running|healthy)',
        content_lower, re.DOTALL
    ))
    c3_passed = mentions_pid and pid_not_wrongly_verified
    checks.append({
        "name": "claim1_pid_file_missing_not_verified_running",
        "passed": c3_passed,
        "detail": (
            f"Mentions ingestor.pid: {mentions_pid}. "
            f"Does NOT falsely verify service as running: {pid_not_wrongly_verified}. "
            "PID file is absent; service status must be Unknown or Inferred, never Verified."
        )
    })
    if c3_passed:
        score += 1.5

    # -----------------------------------------------------------------------
    # CHECK 4: Claim 2 — model in config is 'hl7-classifier-v1', NOT v2
    # Agent must cite the actual config file and identify the discrepancy.
    # -----------------------------------------------------------------------
    mentions_v1 = 'hl7-classifier-v1' in content_lower
    mentions_v2_discrepancy = bool(re.search(
        r'(hl7-classifier-v2|v2).{0,300}(mismatch|incorrect|wrong|discrepan|actual|but|found|differ|instead|not\s+v2|v1)',
        content_lower, re.DOTALL
    )) or bool(re.search(
        r'(mismatch|incorrect|wrong|discrepan|actual|differ|instead).{0,300}(hl7-classifier-v2|v2)',
        content_lower, re.DOTALL
    ))
    mentions_config_path = 'ingestor.yaml' in content_lower
    c4_passed = mentions_v1 and mentions_config_path and (mentions_v2_discrepancy or 'hl7-classifier-v1' in content_lower)
    checks.append({
        "name": "claim2_model_discrepancy_identified",
        "passed": c4_passed,
        "detail": (
            f"Mentions hl7-classifier-v1: {mentions_v1}. "
            f"Cites ingestor.yaml: {mentions_config_path}. "
            f"Identifies v2 discrepancy: {mentions_v2_discrepancy}. "
            "Config actually contains v1, not v2 as claimed in memo."
        )
    })
    if c4_passed:
        score += 1.5

    # -----------------------------------------------------------------------
    # CHECK 5: Claim 4 — Last run did NOT complete successfully (ERROR in log)
    # Agent must cite the log and note the ERROR/failure.
    # -----------------------------------------------------------------------
    mentions_log = 'ingestor.log' in content_lower
    mentions_error = bool(re.search(r'\berror\b', content_lower))
    mentions_permission = bool(re.search(r'(permission denied|exit code|aborted|failed)', content_lower))
    c5_passed = mentions_log and mentions_error and mentions_permission
    checks.append({
        "name": "claim4_last_run_failure_identified",
        "passed": c5_passed,
        "detail": (
            f"Mentions ingestor.log: {mentions_log}. "
            f"Mentions error: {mentions_error}. "
            f"Mentions permission/failure detail: {mentions_permission}. "
            "Log shows ERROR with Permission Denied — last run was NOT successful."
        )
    })
    if c5_passed:
        score += 1.5

    # -----------------------------------------------------------------------
    # CHECK 6: Claim 5 — INGESTOR_API_KEY not in env.conf (should be Unknown or Inferred missing)
    # Agent must cite env.conf and note the key is absent.
    # -----------------------------------------------------------------------
    mentions_env_conf = 'env.conf' in content_lower
    mentions_api_key  = 'ingestor_api_key' in content_lower
    api_key_not_found = bool(re.search(
        r'(ingestor_api_key).{0,300}(not\s+(?:found|present|set|in)|absent|missing|unknown|not\s+configured)',
        content_lower, re.DOTALL
    )) or bool(re.search(
        r'(missing|absent|not\s+(?:found|present|set)|unknown).{0,300}ingestor_api_key',
        content_lower, re.DOTALL
    ))
    c6_passed = mentions_env_conf and mentions_api_key and api_key_not_found
    checks.append({
        "name": "claim5_api_key_absent_from_env_conf",
        "passed": c6_passed,
        "detail": (
            f"Mentions env.conf: {mentions_env_conf}. "
            f"Mentions INGESTOR_API_KEY: {mentions_api_key}. "
            f"Identifies key as absent/unknown: {api_key_not_found}. "
            "env.conf does not contain INGESTOR_API_KEY."
        )
    })
    if c6_passed:
        score += 1.5

    # -----------------------------------------------------------------------
    # CHECK 7: Claim 6 — incoming directory has data (batch_001.hl7 present)
    # Memo claims "no data arrived" but a file exists. Agent must contradict this.
    # -----------------------------------------------------------------------
    mentions_incoming = bool(re.search(r'(incoming|batch_001\.hl7)', content_lower))
    contradicts_no_data = bool(re.search(
        r'(batch_001\.hl7|incoming).{0,300}(found|present|exists|arrived|contradicts|incorrect|not\s+empty)',
        content_lower, re.DOTALL
    )) or bool(re.search(
        r'(not\s+empty|file\s+found|data\s+(?:present|found|exists)).{0,300}(incoming|batch)',
        content_lower, re.DOTALL
    ))
    c7_passed = mentions_incoming and contradicts_no_data
    checks.append({
        "name": "claim6_incoming_data_present_contradicts_memo",
        "passed": c7_passed,
        "detail": (
            f"Mentions incoming/batch_001.hl7: {mentions_incoming}. "
            f"Contradicts 'no data' claim: {contradicts_no_data}. "
            "batch_001.hl7 is present in incoming dir — memo claim is false."
        )
    })
    if c7_passed:
        score += 1.5

    # -----------------------------------------------------------------------
    # CHECK 8: For Unknown claims, next-step commands are provided
    # At least one concrete shell command must be present for unverifiable claims.
    # -----------------------------------------------------------------------
    has_next_step_commands = bool(re.search(
        r'(ps\s+aux|systemctl\s+status|cat\s+.*\.pid|ls\s+-|stat\s+|rg\s+|grep\s+|env\s+|printenv)',
        content, re.IGNORECASE
    ))
    c8_passed = has_next_step_commands
    checks.append({
        "name": "unknown_claims_have_next_step_commands",
        "passed": c8_passed,
        "detail": (
            f"Contains next-step shell command(s) for Unknown claims: {has_next_step_commands}. "
            "SKILL.md requires providing actionable next-step commands for Unknown classifications."
        )
    })
    if c8_passed:
        score += 1.0

    # -----------------------------------------------------------------------
    # CHECK 9: Evidence is cited (paths and/or key log lines referenced)
    # -----------------------------------------------------------------------
    cites_paths = bool(re.search(
        r'(/workspace/pipeline/ingestor|pipeline/ingestor/config|pipeline/ingestor/logs)',
        content
    ))
    c9_passed = cites_paths
    checks.append({
        "name": "evidence_cited_with_paths",
        "passed": c9_passed,
        "detail": (
            f"Cites actual file paths as evidence: {cites_paths}. "
            "SKILL.md requires citing paths and key lines as primary evidence."
        )
    })
    if c9_passed:
        score += 0.5

    # Normalize score to 0-10
    max_raw = 0.5 + 1.0 + 1.5 + 1.5 + 1.5 + 1.5 + 1.5 + 1.0 + 0.5
    normalized = round((score / max_raw) * 10.0, 2)
    passed = normalized >= 7.0

    print(json.dumps({
        "passed": passed,
        "score": normalized,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace_dir)