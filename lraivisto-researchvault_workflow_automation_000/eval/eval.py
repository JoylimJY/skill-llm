#!/usr/bin/env python3
"""
Evaluation script for the ResearchVault pharma intelligence task.

Checks:
1. Project initialized with correct id, name, and objective in the SQLite vault
2. At least one artifact ingested from the intelligence report (scuttle)
3. At least one finding was extracted and stored
4. Synthesis was run: at least one semantic link exists in the vault
5. Verification missions were planned: at least one pending mission exists
6. (Bonus) A second source was scuttled (multi-source ingestion)
"""

import sys
import json
import sqlite3
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    workspace = Path(workspace)
    db_path = workspace / ".vault" / "vault.db"

    def add_check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── CHECK 0: Database file exists ─────────────────────────────────────────
    if not db_path.exists():
        add_check("vault_db_exists", False, f"Database not found at {db_path}. Did the agent run 'init'?")
        return {"passed": False, "score": 0.0, "checks": checks}
    add_check("vault_db_exists", True, f"Database found at {db_path}")

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
    except Exception as e:
        add_check("vault_db_readable", False, f"Cannot open database: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    add_check("vault_db_readable", True, "Database opened successfully")

    # ── CHECK 1: Project initialized with expected fields ─────────────────────
    try:
        projects = conn.execute("SELECT * FROM projects").fetchall()
        if not projects:
            add_check("project_initialized", False, "No projects found in the vault.")
        else:
            # We check that at least one project has all three required fields non-empty
            valid_projects = [
                p for p in projects
                if p["id"] and p["name"] and p["objective"]
                and len(p["id"].strip()) > 0
                and len(p["name"].strip()) > 0
                and len(p["objective"].strip()) > 0
            ]
            if valid_projects:
                p = valid_projects[0]
                add_check(
                    "project_initialized",
                    True,
                    f"Project '{p['id']}' created: name='{p['name']}', objective='{p['objective'][:60]}...'"
                )
            else:
                add_check("project_initialized", False,
                          f"Found {len(projects)} project(s) but none have all required fields (id, name, objective).")
    except Exception as e:
        add_check("project_initialized", False, f"Error querying projects table: {e}")

    # ── CHECK 2: At least one artifact ingested via scuttle ───────────────────
    try:
        artifacts = conn.execute("SELECT * FROM artifacts").fetchall()
        if not artifacts:
            add_check("artifact_ingested", False, "No artifacts found. The agent must run the scuttle command.")
        else:
            # Check that at least one artifact references the intelligence report
            report_artifacts = [
                a for a in artifacts
                if a["source_url"] and (
                    "biotech_intelligence_report" in (a["source_url"] or "")
                    or "intelligence_report" in (a["source_url"] or "")
                    or "june2024" in (a["source_url"] or "").lower()
                    or (a["raw_content"] and "HelixDyne" in (a["raw_content"] or ""))
                    or (a["raw_content"] and "PharmaAxis" in (a["raw_content"] or ""))
                    or (a["raw_content"] and "GENE THERAPY" in (a["raw_content"] or "").upper())
                )
            ]
            if report_artifacts:
                add_check(
                    "artifact_ingested",
                    True,
                    f"Found {len(report_artifacts)} artifact(s) from the intelligence report. "
                    f"Source: {report_artifacts[0]['source_url']}"
                )
            else:
                add_check(
                    "artifact_ingested",
                    False,
                    f"Found {len(artifacts)} artifact(s) but none appear to be from the pharma intelligence report. "
                    f"Sources: {[a['source_url'] for a in artifacts[:3]]}"
                )
    except Exception as e:
        add_check("artifact_ingested", False, f"Error querying artifacts table: {e}")

    # ── CHECK 3: Findings were extracted ──────────────────────────────────────
    try:
        findings = conn.execute("SELECT COUNT(*) as cnt FROM findings").fetchone()
        cnt = findings["cnt"] if findings else 0
        if cnt >= 3:
            add_check("findings_extracted", True, f"{cnt} findings extracted from ingested artifacts.")
        else:
            add_check("findings_extracted", False,
                      f"Only {cnt} findings found. Expected at least 3 after scuttling the intelligence report.")
    except Exception as e:
        add_check("findings_extracted", False, f"Error querying findings table: {e}")

    # ── CHECK 4: Synthesis was run (links table populated) ────────────────────
    try:
        links = conn.execute("SELECT COUNT(*) as cnt FROM links").fetchone()
        cnt = links["cnt"] if links else 0
        if cnt >= 1:
            add_check("synthesis_run", True, f"{cnt} semantic link(s) discovered by synthesis engine.")
        else:
            add_check("synthesis_run", False,
                      "No links found. The agent must run the 'synthesize' command after ingestion.")
    except Exception as e:
        add_check("synthesis_run", False, f"Error querying links table: {e}")

    # ── CHECK 5: Verification missions were planned ────────────────────────────
    try:
        missions = conn.execute(
            "SELECT COUNT(*) as cnt FROM verification_missions WHERE status = 'pending'"
        ).fetchone()
        cnt = missions["cnt"] if missions else 0
        if cnt >= 1:
            add_check("verification_planned", True,
                      f"{cnt} pending verification mission(s) created for low-confidence findings.")
        else:
            # Check if any missions exist at all
            all_missions = conn.execute("SELECT COUNT(*) as cnt FROM verification_missions").fetchone()
            all_cnt = all_missions["cnt"] if all_missions else 0
            add_check("verification_planned", False,
                      f"No pending verification missions found (total missions: {all_cnt}). "
                      "The agent must run 'verify plan' after synthesis.")
    except Exception as e:
        add_check("verification_planned", False, f"Error querying verification_missions table: {e}")

    # ── CHECK 6 (bonus): Multi-source ingestion ───────────────────────────────
    try:
        artifact_count = conn.execute("SELECT COUNT(DISTINCT source_url) as cnt FROM artifacts").fetchone()
        source_count = artifact_count["cnt"] if artifact_count else 0
        if source_count >= 2:
            add_check("multi_source_ingestion", True,
                      f"{source_count} distinct sources ingested (multi-source pipeline complete).")
        else:
            add_check("multi_source_ingestion", False,
                      f"Only {source_count} unique source(s) ingested. "
                      "For full marks, ingest both intelligence data files.")
    except Exception as e:
        add_check("multi_source_ingestion", False, f"Error checking source diversity: {e}")

    conn.close()

    # ── Scoring ────────────────────────────────────────────────────────────────
    # Weights: core checks are required; bonus check is extra credit
    core_checks = [
        "vault_db_exists",
        "vault_db_readable",
        "project_initialized",
        "artifact_ingested",
        "findings_extracted",
        "synthesis_run",
        "verification_planned",
    ]
    bonus_checks = ["multi_source_ingestion"]

    core_passed = sum(1 for c in checks if c["name"] in core_checks and c["passed"])
    bonus_passed = sum(1 for c in checks if c["name"] in bonus_checks and c["passed"])

    core_score = core_passed / len(core_checks)
    bonus_score = bonus_passed / len(bonus_checks) * 0.15  # bonus worth 15%

    final_score = min(1.0, core_score * 0.85 + bonus_score + (0.15 if core_score == 1.0 else 0.0))

    all_core_passed = core_passed == len(core_checks)

    return {
        "passed": all_core_passed,
        "score": round(final_score, 3),
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [], "error": "Usage: eval.py <workspace_dir>"}))
        sys.exit(1)

    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))