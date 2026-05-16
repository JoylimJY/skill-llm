#!/usr/bin/env python3
"""
Evaluation script for the ResearchVault biotech intelligence task.
Checks: project init, artifact ingestion, synthesis (links), and verification plan.
"""

import sys
import json
import sqlite3
import os
from pathlib import Path

def find_vault_db(project_id: str) -> Path | None:
    """Search for the SQLite database created by vault.py."""
    candidates = [
        Path.home() / ".researchvault" / f"{project_id}.db",
        Path("/root/.researchvault") / f"{project_id}.db",
        Path("/workspace/.researchvault") / f"{project_id}.db",
    ]
    for c in candidates:
        if c.exists():
            return c
    # Broader search
    for p in Path("/").rglob(f"{project_id}.db"):
        return p
    return None

def find_verification_plan(project_id: str) -> dict | None:
    """Search for the verification plan JSON file."""
    candidates = [
        Path.home() / ".researchvault" / f"{project_id}_verification_plan.json",
        Path("/root/.researchvault") / f"{project_id}_verification_plan.json",
    ]
    for c in candidates:
        if c.exists():
            try:
                return json.loads(c.read_text())
            except Exception:
                pass
    # Broader search
    for p in Path("/").rglob(f"{project_id}_verification_plan.json"):
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    # Also check workspace
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    for p in Path(workspace).rglob("*verification_plan*.json"):
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return None

def run_eval():
    PROJECT_ID = "biotech-v1"
    checks = []
    total_score = 0.0

    # ----------------------------------------------------------------
    # CHECK 1: Project was initialized in the vault database
    # ----------------------------------------------------------------
    db_path = find_vault_db(PROJECT_ID)
    check1_passed = False
    check1_detail = ""
    try:
        if db_path is None:
            check1_detail = f"No database file found for project '{PROJECT_ID}'. The vault was never initialized."
        else:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM projects WHERE id=?", (PROJECT_ID,)).fetchone()
            if row is None:
                check1_detail = f"Database exists at {db_path} but project '{PROJECT_ID}' not found in projects table."
            else:
                proj = dict(row)
                if not proj.get("name") or not proj.get("objective"):
                    check1_detail = f"Project '{PROJECT_ID}' found but missing name or objective. Got: {proj}"
                else:
                    check1_passed = True
                    check1_detail = f"Project '{PROJECT_ID}' initialized: name='{proj['name']}', objective='{proj['objective']}'"
            conn.close()
    except Exception as e:
        check1_detail = f"Exception reading project: {e}"

    checks.append({"name": "project_initialized", "passed": check1_passed, "detail": check1_detail})
    if check1_passed:
        total_score += 0.20

    # ----------------------------------------------------------------
    # CHECK 2: At least 2 source files were ingested as artifacts
    # ----------------------------------------------------------------
    check2_passed = False
    check2_detail = ""
    artifact_count = 0
    try:
        if db_path is None:
            check2_detail = "No database found — cannot check artifacts."
        else:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            artifacts = conn.execute(
                "SELECT * FROM artifacts WHERE project_id=?", (PROJECT_ID,)
            ).fetchall()
            artifact_count = len(artifacts)
            sources = [dict(a)["source"] for a in artifacts]
            conn.close()
            if artifact_count >= 2:
                check2_passed = True
                check2_detail = f"{artifact_count} artifacts ingested. Sources: {sources}"
            else:
                check2_detail = f"Only {artifact_count} artifact(s) found. Need at least 2 sources ingested. Found: {sources}"
    except Exception as e:
        check2_detail = f"Exception reading artifacts: {e}"

    checks.append({"name": "artifacts_ingested_min_2", "passed": check2_passed, "detail": check2_detail})
    if check2_passed:
        total_score += 0.20

    # ----------------------------------------------------------------
    # CHECK 3: Findings were extracted from ingested artifacts
    # ----------------------------------------------------------------
    check3_passed = False
    check3_detail = ""
    try:
        if db_path is None:
            check3_detail = "No database found — cannot check findings."
        else:
            conn = sqlite3.connect(db_path)
            findings = conn.execute(
                "SELECT COUNT(*) as cnt FROM findings WHERE project_id=?", (PROJECT_ID,)
            ).fetchone()
            fcount = findings[0] if findings else 0
            conn.close()
            if fcount >= 5:
                check3_passed = True
                check3_detail = f"{fcount} findings recorded for project '{PROJECT_ID}'."
            else:
                check3_detail = f"Only {fcount} findings found. Expected at least 5 after ingesting multiple source files."
    except Exception as e:
        check3_detail = f"Exception reading findings: {e}"

    checks.append({"name": "findings_extracted", "passed": check3_passed, "detail": check3_detail})
    if check3_passed:
        total_score += 0.20

    # ----------------------------------------------------------------
    # CHECK 4: Synthesis was run — links table has entries
    # ----------------------------------------------------------------
    check4_passed = False
    check4_detail = ""
    try:
        if db_path is None:
            check4_detail = "No database found — cannot check links."
        else:
            conn = sqlite3.connect(db_path)
            links = conn.execute(
                "SELECT COUNT(*) as cnt FROM links WHERE project_id=?", (PROJECT_ID,)
            ).fetchone()
            lcount = links[0] if links else 0
            conn.close()
            if lcount >= 1:
                check4_passed = True
                check4_detail = f"{lcount} links discovered by synthesis engine for project '{PROJECT_ID}'."
            else:
                check4_detail = "No links found. The 'synthesize' command was likely not run."
    except Exception as e:
        check4_detail = f"Exception reading links: {e}"

    checks.append({"name": "synthesis_links_created", "passed": check4_passed, "detail": check4_detail})
    if check4_passed:
        total_score += 0.20

    # ----------------------------------------------------------------
    # CHECK 5: Verification plan was generated with missions
    # ----------------------------------------------------------------
    check5_passed = False
    check5_detail = ""
    try:
        plan = find_verification_plan(PROJECT_ID)
        if plan is None:
            # Also try checking the DB directly
            if db_path:
                conn = sqlite3.connect(db_path)
                vms = conn.execute(
                    "SELECT COUNT(*) as cnt FROM verification_missions WHERE project_id=?", (PROJECT_ID,)
                ).fetchone()
                vmcount = vms[0] if vms else 0
                conn.close()
                if vmcount >= 1:
                    check5_passed = True
                    check5_detail = f"Verification plan found in DB: {vmcount} missions. (JSON export not found, but DB records exist.)"
                else:
                    check5_detail = "No verification missions found in DB and no JSON plan file found. Run 'verify plan'."
            else:
                check5_detail = "No verification plan JSON and no database found."
        else:
            missions = plan.get("missions", [])
            total = plan.get("total_missions", len(missions))
            pid = plan.get("project_id", "")
            if pid != PROJECT_ID:
                check5_detail = f"Plan found but project_id mismatch: got '{pid}', expected '{PROJECT_ID}'."
            elif len(missions) >= 1:
                check5_passed = True
                check5_detail = f"Verification plan has {total} missions for project '{PROJECT_ID}'. Priorities: {set(m.get('priority','?') for m in missions)}"
            else:
                check5_detail = f"Verification plan JSON found but contains 0 missions."
    except Exception as e:
        check5_detail = f"Exception reading verification plan: {e}"

    checks.append({"name": "verification_plan_generated", "passed": check5_passed, "detail": check5_detail})
    if check5_passed:
        total_score += 0.20

    # ----------------------------------------------------------------
    # Final output
    # ----------------------------------------------------------------
    passed = all(c["passed"] for c in checks)
    result = {
        "passed": passed,
        "score": round(total_score, 2),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run_eval()