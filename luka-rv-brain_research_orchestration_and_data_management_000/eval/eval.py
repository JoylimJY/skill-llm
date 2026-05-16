#!/usr/bin/env python3
"""
Evaluation script for ResearchVault drug-repurposing task.
Checks that the agent correctly used the vault CLI to:
1. Initialize a project (pharma-repurpose-v1)
2. Scuttle two URLs
3. Run synthesize
4. Run verify plan
"""

import sys
import json
import sqlite3
import subprocess
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    weight_sum = 0.0

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        nonlocal total_score, weight_sum
        checks.append({"name": name, "passed": passed, "detail": detail})
        weight_sum += weight
        if passed:
            total_score += weight

    # ── Locate the SQLite vault database ──────────────────────────────────────
    # The vault typically creates a .db file; search common locations
    db_candidates = list(workspace.rglob("*.db")) + list(workspace.rglob("*.sqlite")) + list(workspace.rglob("*.sqlite3"))
    # Also check researchvault subdirectory specifically
    rv_dir = workspace / "researchvault"
    if rv_dir.exists():
        db_candidates += list(rv_dir.rglob("*.db")) + list(rv_dir.rglob("*.sqlite"))

    vault_db = None
    project_row = None

    for db_path in db_candidates:
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Try to find the projects table (could be named 'projects' or 'vaults')
            tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            if not tables:
                conn.close()
                continue

            # Look for a table that might hold project/vault metadata
            for tname in ["projects", "vaults", "research_projects", "vault_projects"]:
                if tname in tables:
                    rows = cursor.execute(f"SELECT * FROM {tname}").fetchall()
                    for row in rows:
                        row_dict = dict(row)
                        vals = [str(v).lower() for v in row_dict.values()]
                        if any("pharma-repurpose-v1" in v for v in vals):
                            vault_db = db_path
                            project_row = row_dict
                            break
                if vault_db:
                    break

            # Also try scanning all tables for the project ID
            if not vault_db:
                for tname in tables:
                    try:
                        rows = cursor.execute(f"SELECT * FROM {tname}").fetchall()
                        for row in rows:
                            vals = [str(v).lower() for v in dict(row).values()]
                            if any("pharma-repurpose-v1" in v for v in vals):
                                vault_db = db_path
                                project_row = dict(row)
                                break
                    except Exception:
                        pass
                    if vault_db:
                        break
            conn.close()
        except Exception as e:
            continue

    # ── CHECK 1: Database exists with project ID ───────────────────────────────
    if vault_db and project_row:
        add_check(
            "vault_db_initialized",
            True,
            f"Found vault DB at '{vault_db}' containing project 'pharma-repurpose-v1'. Row: {project_row}",
            weight=2.0,
        )
    else:
        add_check(
            "vault_db_initialized",
            False,
            f"No SQLite DB found containing project ID 'pharma-repurpose-v1'. Searched {len(db_candidates)} DB files: {[str(p) for p in db_candidates[:5]]}",
            weight=2.0,
        )

    # ── CHECK 2: Project metadata correctness ─────────────────────────────────
    if project_row:
        vals_lower = {k: str(v).lower() for k, v in project_row.items()}
        all_vals = " ".join(vals_lower.values())
        has_name = "oncology drug repurposing" in all_vals
        has_objective_keywords = ("off-label" in all_vals or "off_label" in all_vals or
                                   "clinical evidence" in all_vals or "emerging" in all_vals or
                                   "oncology" in all_vals)
        add_check(
            "project_metadata_correct",
            has_name and has_objective_keywords,
            f"Name present: {has_name}, Objective keywords present: {has_objective_keywords}. Row values: {all_vals[:300]}",
            weight=1.5,
        )
    else:
        add_check(
            "project_metadata_correct",
            False,
            "Cannot check metadata — project row not found.",
            weight=1.5,
        )

    # ── CHECK 3: Artifacts/findings ingested (scuttle ran) ────────────────────
    ingested = False
    ingested_detail = ""
    if vault_db:
        try:
            conn = sqlite3.connect(str(vault_db))
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            artifact_tables = [t for t in tables if any(kw in t.lower() for kw in ["artifact", "finding", "source", "document", "page", "result"])]
            for tname in artifact_tables:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
                    if count > 0:
                        # Check for URL-related content
                        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({tname})").fetchall()]
                        url_cols = [c for c in cols if any(kw in c.lower() for kw in ["url", "source", "uri", "link", "origin"])]
                        if url_cols:
                            sample = conn.execute(f"SELECT {url_cols[0]} FROM {tname} LIMIT 5").fetchall()
                            ingested_detail = f"Table '{tname}' has {count} rows. URL samples: {[r[0] for r in sample]}"
                        else:
                            ingested_detail = f"Table '{tname}' has {count} rows (no explicit URL column found)."
                        ingested = True
                        break
                except Exception as e:
                    ingested_detail += f" Error reading {tname}: {e}"
            if not ingested:
                # Check if tables exist but are empty — scuttle may have been called but returned nothing
                all_table_counts = {}
                for tname in tables:
                    try:
                        c = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
                        all_table_counts[tname] = c
                    except Exception:
                        pass
                ingested_detail = f"All table counts: {all_table_counts}"
            conn.close()
        except Exception as e:
            ingested_detail = f"DB read error: {e}"
    else:
        ingested_detail = "No vault DB found."

    # We also check shell history / logs for evidence of 'scuttle' being called
    scuttle_called = False
    scuttle_sources = []
    history_files = [
        Path("/root/.bash_history"),
        Path("/root/.zsh_history"),
        workspace / ".agent_history",
        workspace / "vault_run.log",
        workspace / "agent.log",
    ]
    for hf in history_files:
        if hf.exists():
            try:
                content = hf.read_text(errors="replace")
                if "scuttle" in content:
                    scuttle_called = True
                    # Try to extract URLs
                    import re
                    urls = re.findall(r'scuttle\s+(https?://[^\s"\']+)', content)
                    scuttle_sources.extend(urls)
            except Exception:
                pass

    # Check for log files in researchvault dir
    for log_f in (workspace / "researchvault").rglob("*.log") if (workspace / "researchvault").exists() else []:
        try:
            content = log_f.read_text(errors="replace")
            if "scuttle" in content or "pubmed" in content.lower() or "clinicaltrials" in content.lower():
                scuttle_called = True
        except Exception:
            pass

    add_check(
        "scuttle_ingestion_ran",
        ingested or scuttle_called,
        f"DB ingestion evidence: {ingested}. Shell history evidence: {scuttle_called}. Sources found: {scuttle_sources}. DB detail: {ingested_detail}",
        weight=2.0,
    )

    # ── CHECK 4: Both URLs were scuttled ──────────────────────────────────────
    pubmed_url = "pubmed.ncbi.nlm.nih.gov"
    ctgov_url = "clinicaltrials.gov"

    urls_ingested = {"pubmed": False, "clinicaltrials": False}
    if vault_db:
        try:
            conn = sqlite3.connect(str(vault_db))
            # Dump entire DB text to search for URLs
            dump = ""
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            for tname in tables:
                try:
                    rows = conn.execute(f"SELECT * FROM {tname}").fetchall()
                    for row in rows:
                        dump += " ".join(str(v) for v in row) + " "
                except Exception:
                    pass
            conn.close()
            if pubmed_url in dump:
                urls_ingested["pubmed"] = True
            if ctgov_url in dump:
                urls_ingested["clinicaltrials"] = True
        except Exception as e:
            pass

    # Also check history
    if scuttle_sources:
        for url in scuttle_sources:
            if pubmed_url in url:
                urls_ingested["pubmed"] = True
            if ctgov_url in url:
                urls_ingested["clinicaltrials"] = True

    both_urls = urls_ingested["pubmed"] and urls_ingested["clinicaltrials"]
    add_check(
        "both_urls_scuttled",
        both_urls,
        f"PubMed URL ingested: {urls_ingested['pubmed']}, ClinicalTrials URL ingested: {urls_ingested['clinicaltrials']}",
        weight=2.0,
    )

    # ── CHECK 5: Synthesize was run ────────────────────────────────────────────
    synthesize_ran = False
    links_exist = False
    synth_detail = ""

    # Check DB for links table
    if vault_db:
        try:
            conn = sqlite3.connect(str(vault_db))
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            link_tables = [t for t in tables if any(kw in t.lower() for kw in ["link", "relation", "edge", "connection", "synthesis"])]
            for tname in link_tables:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
                    synth_detail += f"Table '{tname}': {count} rows. "
                    if count > 0:
                        links_exist = True
                except Exception as e:
                    synth_detail += f"Error on {tname}: {e}. "
            conn.close()
        except Exception as e:
            synth_detail = f"DB error: {e}"

    # Check history for synthesize command
    for hf in history_files:
        if hf.exists():
            try:
                content = hf.read_text(errors="replace")
                if "synthesize" in content and "pharma-repurpose-v1" in content:
                    synthesize_ran = True
            except Exception:
                pass

    add_check(
        "synthesize_ran",
        links_exist or synthesize_ran,
        f"Links/synthesis table evidence: {links_exist}. History evidence: {synthesize_ran}. Detail: {synth_detail}",
        weight=1.5,
    )

    # ── CHECK 6: Verify plan was run ───────────────────────────────────────────
    verify_ran = False
    missions_exist = False
    verify_detail = ""

    if vault_db:
        try:
            conn = sqlite3.connect(str(vault_db))
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            mission_tables = [t for t in tables if any(kw in t.lower() for kw in ["mission", "verification", "verify", "task", "todo", "queue"])]
            for tname in mission_tables:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
                    verify_detail += f"Table '{tname}': {count} rows. "
                    if count > 0:
                        missions_exist = True
                except Exception as e:
                    verify_detail += f"Error on {tname}: {e}. "
            conn.close()
        except Exception as e:
            verify_detail = f"DB error: {e}"

    # Check history for "verify plan"
    for hf in history_files:
        if hf.exists():
            try:
                content = hf.read_text(errors="replace")
                if ("verify" in content and "plan" in content and "pharma-repurpose-v1" in content):
                    verify_ran = True
            except Exception:
                pass

    add_check(
        "verify_plan_ran",
        missions_exist or verify_ran,
        f"Verification missions table evidence: {missions_exist}. History evidence: {verify_ran}. Detail: {verify_detail}",
        weight=1.5,
    )

    # ── CHECK 7: Used correct CLI pattern (uv run python scripts/vault.py) ────
    correct_cli_used = False
    cli_detail = "No shell history found."
    for hf in history_files:
        if hf.exists():
            try:
                content = hf.read_text(errors="replace")
                if "scripts/vault.py" in content or "vault.py" in content:
                    if "uv run" in content:
                        correct_cli_used = True
                        cli_detail = "Found 'uv run' + 'vault.py' in shell history."
                    else:
                        cli_detail = "Found 'vault.py' but NOT via 'uv run' — may have used wrong invocation."
            except Exception:
                pass

    # Also check if researchvault dir and vault.py exist (means agent found the right place)
    vault_script_exists = (workspace / "researchvault" / "scripts" / "vault.py").exists()
    add_check(
        "correct_cli_invocation",
        correct_cli_used or vault_script_exists,
        f"Correct CLI: {correct_cli_used}. vault.py script present at expected path: {vault_script_exists}. Detail: {cli_detail}",
        weight=1.0,
    )

    # ── Compute final score ────────────────────────────────────────────────────
    score = round(total_score / weight_sum, 4) if weight_sum > 0 else 0.0
    passed = score >= 0.60  # Must pass at least 60% weighted checks

    # Override: vault must exist and have correct project
    critical_checks = ["vault_db_initialized", "scuttle_ingestion_ran", "synthesize_ran", "verify_plan_ran"]
    critical_passed = [c for c in checks if c["name"] in critical_checks and c["passed"]]
    if len(critical_passed) < 3:
        passed = False

    return {
        "passed": passed,
        "score": score,
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg_error", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))