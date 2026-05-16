#!/usr/bin/env python3
"""
Evaluation script for the genome-qc macro pipeline task.
Usage: python3 eval_script.py <workspace_dir>
"""
import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    home = Path(workspace)

    # ── Derived paths ──────────────────────────────────────────────────────────
    pipeline_path = home / "Documents" / "proyectos" / "genome-qc" / "PIPELINE.md"
    heartbeat_path = home / ".openclaw" / "workspace-agent-bio-01" / "HEARTBEAT.md"

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION A: PIPELINE.md checks
    # ══════════════════════════════════════════════════════════════════════════

    # A1: File exists at the correct location
    pipeline_exists = pipeline_path.exists()
    checks.append({
        "name": "A1_pipeline_correct_location",
        "passed": pipeline_exists,
        "detail": f"PIPELINE.md at {pipeline_path}: {'found' if pipeline_exists else 'MISSING'}"
    })

    pipeline_content = ""
    if pipeline_exists:
        try:
            pipeline_content = pipeline_path.read_text()
        except Exception as e:
            checks.append({"name": "A1_pipeline_read", "passed": False, "detail": str(e)})

    # A2: Header block — must have # PIPELINE —, # Proyecto:, # Objetivo:, # Creado:
    has_pipeline_header = bool(re.search(r'^# PIPELINE\s*[—–-]', pipeline_content, re.MULTILINE))
    checks.append({
        "name": "A2_pipeline_header",
        "passed": has_pipeline_header,
        "detail": f"Has '# PIPELINE —' header: {has_pipeline_header}"
    })

    has_proyecto = bool(re.search(r'^# Proyecto:\s*.+genome-qc', pipeline_content, re.MULTILINE))
    checks.append({
        "name": "A2_pipeline_proyecto_line",
        "passed": has_proyecto,
        "detail": f"Has '# Proyecto:' line referencing genome-qc: {has_proyecto}"
    })

    has_objetivo = bool(re.search(r'^# Objetivo:\s*.+', pipeline_content, re.MULTILINE))
    checks.append({
        "name": "A2_pipeline_objetivo_line",
        "passed": has_objetivo,
        "detail": f"Has '# Objetivo:' line: {has_objetivo}"
    })

    has_creado = bool(re.search(r'^# Creado:\s*\d{4}-\d{2}-\d{2}', pipeline_content, re.MULTILINE))
    checks.append({
        "name": "A2_pipeline_creado_date",
        "passed": has_creado,
        "detail": f"Has '# Creado: YYYY-MM-DD': {has_creado}"
    })

    # A3: At least 5 steps defined
    step_headers = re.findall(r'^## Step \d+:', pipeline_content, re.MULTILINE)
    has_min_steps = len(step_headers) >= 5
    checks.append({
        "name": "A3_minimum_five_steps",
        "passed": has_min_steps,
        "detail": f"Found {len(step_headers)} steps (need ≥5)"
    })

    # A4: All steps have [PENDING] status
    steps_with_status = re.findall(r'^## Step \d+:.*?\[(PENDING|RUNNING|COMPLETED|FAILED|BLOCKED|✅[^\]]*)\]', pipeline_content, re.MULTILINE)
    all_pending = all(s.strip() == 'PENDING' for s in steps_with_status)
    checks.append({
        "name": "A4_all_steps_pending",
        "passed": all_pending and len(steps_with_status) >= 5,
        "detail": f"Step statuses found: {steps_with_status}"
    })

    # A5: Every step must have a 'verify:' field
    # Count steps and verify: fields — they should match
    step_blocks = re.split(r'^## Step \d+:', pipeline_content, flags=re.MULTILINE)
    step_blocks = [b for b in step_blocks if b.strip()]  # remove empty
    verify_count = sum(1 for b in step_blocks if re.search(r'^\s*-\s*verify:', b, re.MULTILINE))
    all_have_verify = (verify_count == len(step_blocks)) and len(step_blocks) >= 5
    checks.append({
        "name": "A5_all_steps_have_verify",
        "passed": all_have_verify,
        "detail": f"{verify_count}/{len(step_blocks)} steps have 'verify:' field"
    })

    # A6: Every step must have 'engine:' field
    engine_count = sum(1 for b in step_blocks if re.search(r'^\s*-\s*engine:', b, re.MULTILINE))
    all_have_engine = (engine_count == len(step_blocks)) and len(step_blocks) >= 5
    checks.append({
        "name": "A6_all_steps_have_engine",
        "passed": all_have_engine,
        "detail": f"{engine_count}/{len(step_blocks)} steps have 'engine:' field"
    })

    # A7: At least one step uses depends_on:
    has_depends_on = bool(re.search(r'^\s*-\s*depends_on:', pipeline_content, re.MULTILINE))
    checks.append({
        "name": "A7_has_depends_on",
        "passed": has_depends_on,
        "detail": f"Has at least one 'depends_on:' field: {has_depends_on}"
    })

    # A8: At least one step uses parallel:
    has_parallel = bool(re.search(r'^\s*-\s*parallel:', pipeline_content, re.MULTILINE))
    checks.append({
        "name": "A8_has_parallel_field",
        "passed": has_parallel,
        "detail": f"Has at least one 'parallel:' field: {has_parallel}"
    })

    # A9: parallel: field contains a list of step numbers (e.g., [2, 3] or [1, 3])
    parallel_values = re.findall(r'^\s*-\s*parallel:\s*(\[[\d,\s]+\])', pipeline_content, re.MULTILINE)
    valid_parallel_list = len(parallel_values) > 0
    checks.append({
        "name": "A9_parallel_is_list_of_numbers",
        "passed": valid_parallel_list,
        "detail": f"parallel: values found: {parallel_values}"
    })

    # A10: PIPELINE.md must NOT be in workspace (should be in repo only)
    wrong_location_pipeline = (home / ".openclaw" / "workspace-agent-bio-01" / "PIPELINE.md").exists()
    checks.append({
        "name": "A10_pipeline_not_in_workspace",
        "passed": not wrong_location_pipeline,
        "detail": f"PIPELINE.md incorrectly placed in workspace: {wrong_location_pipeline}"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION B: HEARTBEAT.md checks
    # ══════════════════════════════════════════════════════════════════════════

    # B1: File exists at the correct location
    heartbeat_exists = heartbeat_path.exists()
    checks.append({
        "name": "B1_heartbeat_correct_location",
        "passed": heartbeat_exists,
        "detail": f"HEARTBEAT.md at {heartbeat_path}: {'found' if heartbeat_exists else 'MISSING'}"
    })

    heartbeat_content = ""
    if heartbeat_exists:
        try:
            heartbeat_content = heartbeat_path.read_text()
        except Exception as e:
            checks.append({"name": "B1_heartbeat_read", "passed": False, "detail": str(e)})

    # B2: Has # HEARTBEAT — <Agent Name> header
    has_heartbeat_header = bool(re.search(r'^# HEARTBEAT\s*[—–-]', heartbeat_content, re.MULTILINE))
    checks.append({
        "name": "B2_heartbeat_header",
        "passed": has_heartbeat_header,
        "detail": f"Has '# HEARTBEAT —' header: {has_heartbeat_header}"
    })

    # B3: Contains the NUNCA modifiques warning
    has_nunca_warning = bool(re.search(r'NUNCA\s+modifiques', heartbeat_content, re.IGNORECASE))
    checks.append({
        "name": "B3_heartbeat_nunca_warning",
        "passed": has_nunca_warning,
        "detail": f"Has 'NUNCA modifiques' immutability warning: {has_nunca_warning}"
    })

    # B4: References the pipeline with an absolute path containing genome-qc
    # Must reference ~/Documents/proyectos/genome-qc/PIPELINE.md or absolute equivalent
    has_absolute_pipeline_ref = bool(re.search(
        r'(~/Documents/proyectos/genome-qc/PIPELINE\.md|/home/[^/]+/Documents/proyectos/genome-qc/PIPELINE\.md)',
        heartbeat_content
    ))
    checks.append({
        "name": "B4_heartbeat_absolute_pipeline_path",
        "passed": has_absolute_pipeline_ref,
        "detail": f"References pipeline with absolute path: {has_absolute_pipeline_ref}"
    })

    # B5: Contains heartbeat protocol section (numbered steps)
    has_protocol = bool(re.search(r'Protocolo|protocolo|heartbeat', heartbeat_content, re.IGNORECASE))
    checks.append({
        "name": "B5_heartbeat_protocol_section",
        "passed": has_protocol,
        "detail": f"Has protocol/heartbeat section: {has_protocol}"
    })

    # B6: Contains Zombie Detection section
    has_zombie = bool(re.search(r'[Zz]ombie', heartbeat_content))
    checks.append({
        "name": "B6_heartbeat_zombie_detection",
        "passed": has_zombie,
        "detail": f"Has Zombie Detection section: {has_zombie}"
    })

    # B7: HEARTBEAT.md must NOT be inside the project repo
    wrong_location_heartbeat = (home / "Documents" / "proyectos" / "genome-qc" / "HEARTBEAT.md").exists()
    checks.append({
        "name": "B7_heartbeat_not_in_repo",
        "passed": not wrong_location_heartbeat,
        "detail": f"HEARTBEAT.md incorrectly placed in project repo: {wrong_location_heartbeat}"
    })

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION C: Git commit with correct format
    # ══════════════════════════════════════════════════════════════════════════

    # C1: Check git log in genome-qc for a pipeline-style commit
    import subprocess
    git_commit_ok = False
    git_detail = "Could not read git log"
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--all"],
            cwd=str(home / "Documents" / "proyectos" / "genome-qc"),
            capture_output=True, text=True, timeout=10
        )
        git_log = result.stdout
        # Look for commit matching pipeline/<project>/step-N: <title> format
        git_commit_ok = bool(re.search(r'pipeline/genome-qc/step-\d+:', git_log))
        git_detail = f"Git log excerpt: {git_log[:300]}"
    except Exception as e:
        git_detail = f"Exception reading git log: {e}"

    checks.append({
        "name": "C1_git_pipeline_commit_format",
        "passed": git_commit_ok,
        "detail": git_detail
    })

    # ══════════════════════════════════════════════════════════════════════════
    # SCORING
    # ══════════════════════════════════════════════════════════════════════════

    # Weighted scoring: critical checks worth more
    critical_checks = {
        "A1_pipeline_correct_location": 3,
        "A5_all_steps_have_verify": 3,
        "A8_has_parallel_field": 2,
        "A9_parallel_is_list_of_numbers": 2,
        "A7_has_depends_on": 2,
        "B1_heartbeat_correct_location": 3,
        "B3_heartbeat_nunca_warning": 2,
        "B4_heartbeat_absolute_pipeline_path": 3,
        "B7_heartbeat_not_in_repo": 2,
        "A10_pipeline_not_in_workspace": 2,
        "C1_git_pipeline_commit_format": 2,
    }
    default_weight = 1

    total_weight = 0
    earned_weight = 0
    for c in checks:
        w = critical_checks.get(c["name"], default_weight)
        total_weight += w
        if c["passed"]:
            earned_weight += w

    score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0

    # Must pass all critical checks to be considered "passed"
    critical_passed = all(
        c["passed"] for c in checks
        if c["name"] in critical_checks
    )
    passed = critical_passed and score >= 0.80

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/bioagent"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))