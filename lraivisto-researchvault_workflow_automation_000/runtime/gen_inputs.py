#!/usr/bin/env python3
"""
Generate the initial sandbox workspace for the ResearchVault evaluation task.
This script creates a realistic pharma competitive intelligence workspace with
distractor files, a mock researchvault package, and raw unstructured data
that the agent must ingest.
"""

import os
import random
import json
import sqlite3
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── 1. Create the researchvault package (scripts/vault.py + pyproject.toml) ──

scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

pyproject = WORKSPACE / "pyproject.toml"
pyproject.write_text(textwrap.dedent("""\
    [build-system]
    requires = ["setuptools>=68"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "researchvault"
    version = "0.3.1"
    requires-python = ">=3.13"
    dependencies = [
        "click>=8.1",
        "rich>=13.0",
        "sentence-transformers>=3.0",
        "sqlite-utils>=3.36",
        "httpx>=0.27",
        "beautifulsoup4>=4.12",
        "numpy>=1.26",
    ]

    [tool.setuptools.packages.find]
    where = ["."]
"""))

# The main vault.py script — a fully functional CLI tool
vault_py = scripts_dir / "vault.py"
vault_py.write_text(textwrap.dedent('''\
    #!/usr/bin/env python3
    """ResearchVault CLI — Autonomous State Manager for Agentic Research."""

    import click
    import sqlite3
    import json
    import hashlib
    import time
    import urllib.request
    import urllib.parse
    import re
    import os
    from pathlib import Path
    from datetime import datetime, timezone

    DB_PATH = Path(".vault") / "vault.db"


    def get_db(project_id: str) -> sqlite3.Connection:
        db_dir = Path(".vault")
        db_dir.mkdir(exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn


    def init_schema(conn: sqlite3.Connection):
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                objective TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT \'active\'
            );
            CREATE TABLE IF NOT EXISTS artifacts (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                source_url TEXT,
                raw_content TEXT,
                ingested_at TEXT NOT NULL,
                content_hash TEXT
            );
            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                artifact_id TEXT,
                content TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                created_at TEXT NOT NULL,
                tags TEXT DEFAULT \'[]\'
            );
            CREATE TABLE IF NOT EXISTS links (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                source_finding_id TEXT,
                target_finding_id TEXT,
                link_type TEXT DEFAULT \'related\',
                score REAL DEFAULT 0.0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS verification_missions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                finding_id TEXT,
                mission_type TEXT DEFAULT \'fact_check\',
                status TEXT DEFAULT \'pending\',
                priority REAL DEFAULT 0.5,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS branches (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                hypothesis TEXT,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT \'active\'
            );
        """)
        conn.commit()


    def make_id(prefix: str, content: str) -> str:
        h = hashlib.sha256(content.encode()).hexdigest()[:12]
        return f"{prefix}_{h}"


    @click.group()
    def cli():
        """ResearchVault: High-velocity research orchestration engine."""
        pass


    @cli.command("init")
    @click.option("--id", "project_id", required=True, help="Unique project identifier.")
    @click.option("--name", required=True, help="Human-readable project name.")
    @click.option("--objective", required=True, help="Research objective statement.")
    def init_cmd(project_id: str, name: str, objective: str):
        """Initialize a new research vault project."""
        conn = get_db(project_id)
        init_schema(conn)
        now = datetime.now(timezone.utc).isoformat()
        try:
            conn.execute(
                "INSERT INTO projects (id, name, objective, created_at) VALUES (?, ?, ?, ?)",
                (project_id, name, objective, now)
            )
            conn.commit()
            click.echo(f"[vault] Project \'{project_id}\' initialized: {name}")
            click.echo(f"[vault] Objective: {objective}")
        except sqlite3.IntegrityError:
            click.echo(f"[vault] Project \'{project_id}\' already exists.", err=True)
        finally:
            conn.close()


    @cli.command("scuttle")
    @click.argument("url")
    @click.option("--id", "project_id", required=True, help="Target project ID.")
    def scuttle_cmd(url: str, project_id: str):
        """Ingest a URL or local file as a research artifact."""
        conn = get_db(project_id)
        init_schema(conn)

        # Verify project exists
        row = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            click.echo(f"[vault] ERROR: Project \'{project_id}\' not found. Run init first.", err=True)
            conn.close()
            return

        # Fetch content
        raw_content = ""
        try:
            if url.startswith("file://"):
                local_path = url[7:]
                with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                    raw_content = f.read()
            elif url.startswith("http://") or url.startswith("https://"):
                with urllib.request.urlopen(url, timeout=10) as resp:
                    raw_content = resp.read().decode("utf-8", errors="replace")
            else:
                # Treat as local path
                with open(url, "r", encoding="utf-8", errors="replace") as f:
                    raw_content = f.read()
        except Exception as e:
            click.echo(f"[vault] WARNING: Could not fetch \'{url}\': {e}", err=True)
            raw_content = f"FETCH_ERROR: {e}"

        content_hash = hashlib.sha256(raw_content.encode()).hexdigest()
        artifact_id = make_id("art", f"{project_id}:{url}:{content_hash}")
        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            "INSERT OR REPLACE INTO artifacts (id, project_id, source_url, raw_content, ingested_at, content_hash) VALUES (?, ?, ?, ?, ?, ?)",
            (artifact_id, project_id, url, raw_content, now, content_hash)
        )

        # Extract pseudo-findings from content lines
        findings_created = 0
        lines = [l.strip() for l in raw_content.splitlines() if len(l.strip()) > 40]
        for line in lines[:20]:  # cap at 20 findings per artifact
            confidence = round(random.uniform(0.3, 0.95), 3)
            finding_id = make_id("fnd", f"{artifact_id}:{line}")
            tags = json.dumps(["auto-extracted", "unverified"])
            conn.execute(
                "INSERT OR REPLACE INTO findings (id, project_id, artifact_id, content, confidence, created_at, tags) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (finding_id, project_id, artifact_id, line, confidence, now, tags)
            )
            findings_created += 1

        conn.commit()
        click.echo(f"[vault] Artifact \'{artifact_id}\' ingested from \'{url}\'.")
        click.echo(f"[vault] Extracted {findings_created} findings.")
        conn.close()


    @cli.command("synthesize")
    @click.option("--id", "project_id", required=True, help="Target project ID.")
    def synthesize_cmd(project_id: str):
        """Discover and record semantic links between findings."""
        conn = get_db(project_id)
        init_schema(conn)

        findings = conn.execute(
            "SELECT id, content FROM findings WHERE project_id = ?",
            (project_id,)
        ).fetchall()

        if len(findings) < 2:
            click.echo("[vault] Not enough findings to synthesize (need >= 2).")
            conn.close()
            return

        now = datetime.now(timezone.utc).isoformat()
        links_created = 0

        # Simple keyword-overlap similarity (deterministic, no ML dependency)
        def similarity(a: str, b: str) -> float:
            wa = set(re.findall(r\'\\w+\', a.lower()))
            wb = set(re.findall(r\'\\w+\', b.lower()))
            if not wa or not wb:
                return 0.0
            return len(wa & wb) / len(wa | wb)

        for i in range(len(findings)):
            for j in range(i + 1, len(findings)):
                score = similarity(findings[i]["content"], findings[j]["content"])
                if score > 0.15:
                    link_id = make_id("lnk", f"{findings[i][\'id\']}:{findings[j][\'id\']}")
                    conn.execute(
                        "INSERT OR REPLACE INTO links (id, project_id, source_finding_id, target_finding_id, link_type, score, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (link_id, project_id, findings[i]["id"], findings[j]["id"], "related", round(score, 4), now)
                    )
                    links_created += 1

        conn.commit()
        click.echo(f"[vault] Synthesis complete: {links_created} links discovered for project \'{project_id}\'.")
        conn.close()


    @cli.command("verify")
    @click.argument("action", type=click.Choice(["plan", "run", "status"]))
    @click.option("--id", "project_id", required=True, help="Target project ID.")
    @click.option("--threshold", default=0.6, help="Confidence threshold below which findings get missions.")
    def verify_cmd(action: str, project_id: str, threshold: float):
        """Manage verification missions for low-confidence findings."""
        conn = get_db(project_id)
        init_schema(conn)

        if action == "plan":
            # Find low-confidence findings
            findings = conn.execute(
                "SELECT id, content, confidence FROM findings WHERE project_id = ? AND confidence < ?",
                (project_id, threshold)
            ).fetchall()

            now = datetime.now(timezone.utc).isoformat()
            missions_created = 0
            for f in findings:
                # Avoid duplicate missions
                existing = conn.execute(
                    "SELECT id FROM verification_missions WHERE finding_id = ? AND status = \'pending\'",
                    (f["id"],)
                ).fetchone()
                if not existing:
                    mission_id = make_id("mis", f"{project_id}:{f[\'id\']}:{now}")
                    priority = round(1.0 - f["confidence"], 4)
                    conn.execute(
                        "INSERT INTO verification_missions (id, project_id, finding_id, mission_type, status, priority, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (mission_id, project_id, f["id"], "fact_check", "pending", priority, now)
                    )
                    missions_created += 1

            conn.commit()
            click.echo(f"[vault] Verification plan: {missions_created} missions created for project \'{project_id}\'.")
            conn.close()

        elif action == "status":
            rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM verification_missions WHERE project_id = ? GROUP BY status",
                (project_id,)
            ).fetchall()
            for r in rows:
                click.echo(f"[vault]   {r[\'status\']}: {r[\'cnt\']} missions")
            conn.close()

        elif action == "run":
            click.echo("[vault] Autonomous verification run initiated (stub).")
            conn.close()


    @cli.command("branch")
    @click.option("--id", "project_id", required=True, help="Target project ID.")
    @click.option("--name", required=True, help="Branch name.")
    @click.option("--hypothesis", default="", help="Hypothesis statement for this branch.")
    def branch_cmd(project_id: str, name: str, hypothesis: str):
        """Create a research branch to explore a parallel hypothesis."""
        conn = get_db(project_id)
        init_schema(conn)
        now = datetime.now(timezone.utc).isoformat()
        branch_id = make_id("brn", f"{project_id}:{name}:{now}")
        conn.execute(
            "INSERT INTO branches (id, project_id, name, hypothesis, created_at) VALUES (?, ?, ?, ?, ?)",
            (branch_id, project_id, name, hypothesis, now)
        )
        conn.commit()
        click.echo(f"[vault] Branch \'{name}\' created for project \'{project_id}\'.")
        conn.close()


    @cli.command("mcp")
    @click.option("--transport", default="stdio", type=click.Choice(["stdio", "http"]))
    def mcp_cmd(transport: str):
        """Start the MCP server for cross-agent collaboration."""
        click.echo(f"[vault] MCP server starting (transport={transport})...")
        click.echo("[vault] Press Ctrl+C to stop.")
        # Stub: in production this would start a real MCP server


    if __name__ == "__main__":
        cli()
'''))

# ─── 2. Create a realistic distractor directory structure ──────────────────────

# Pharma competitive intelligence context
(WORKSPACE / "reports" / "q1_2024").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "reports" / "q2_2024").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "data" / "raw" / "pubmed").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "data" / "processed").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "data" / "exports").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "configs").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "logs").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "archive" / "2023").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "notebooks").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "assets" / "templates").mkdir(parents=True, exist_ok=True)

# Distractor files
(WORKSPACE / "reports" / "q1_2024" / "pipeline_summary.csv").write_text(
    "company,drug,phase,indication\nAlphaGen Bio,AG-201,Phase II,NASH\nVectaTherapeutics,VT-900,Phase I,GBM\n"
)
(WORKSPACE / "reports" / "q2_2024" / "funding_rounds.json").write_text(
    json.dumps([
        {"company": "NovaSynapse", "amount_musd": 85, "series": "B", "date": "2024-04-12"},
        {"company": "CrisprEdge", "amount_musd": 120, "series": "C", "date": "2024-05-03"},
    ], indent=2)
)
(WORKSPACE / "data" / "raw" / "pubmed" / "abstracts_batch_001.txt").write_text(
    "PMID: 38201234\nTitle: Novel KRAS inhibitor demonstrates synergy with PD-1 blockade\n\n"
    "PMID: 38209876\nTitle: mRNA delivery platforms in rare metabolic disorders\n"
)
(WORKSPACE / "data" / "processed" / "entity_extraction_log.txt").write_text(
    "[2024-06-01 09:12:44] Extracted 342 entities from batch_001\n"
    "[2024-06-01 09:13:02] Confidence filter applied: 287 retained\n"
)
(WORKSPACE / "configs" / "pipeline_config.yaml").write_text(
    "version: 2\nsources:\n  - pubmed\n  - clinicaltrials\noutput_format: jsonl\n"
)
(WORKSPACE / "configs" / "watchdog.toml").write_text(
    "[watchdog]\ninterval_sec = 300\ntargets = [\"https://clinicaltrials.gov/api/query\"]\n"
)
(WORKSPACE / "logs" / "ingestion_2024-06-01.log").write_text(
    "INFO  [09:00:01] Starting ingestion pipeline\n"
    "WARN  [09:00:45] Rate limit on PubMed API, backing off 30s\n"
    "INFO  [09:01:20] 156 records ingested\n"
)
(WORKSPACE / "archive" / "2023" / "old_findings.db").write_text("PLACEHOLDER - old sqlite db")
(WORKSPACE / "notebooks" / "exploratory_analysis.ipynb").write_text(
    json.dumps({"nbformat": 4, "cells": [], "metadata": {}, "nbformat_minor": 5})
)
(WORKSPACE / "assets" / "templates" / "report_template.md").write_text(
    "# Research Report Template\n\n## Executive Summary\n\n## Key Findings\n\n## Next Steps\n"
)
(WORKSPACE / "data" / "exports" / "competitor_snapshot_2024Q1.jsonl").write_text(
    '{"id": "comp_001", "name": "HelixDyne", "focus": "gene editing", "stage": "clinical"}\n'
    '{"id": "comp_002", "name": "PharmaAxis", "focus": "AI drug discovery", "stage": "preclinical"}\n'
)

# ─── 3. Create the PRIMARY data source: a messy, realistic intelligence report ─
# This is what the agent must ingest using the tool's scuttle command

intel_report = WORKSPACE / "data" / "raw" / "biotech_intelligence_report_june2024.txt"
intel_report.write_text(textwrap.dedent("""\
    BIOTECH COMPETITIVE INTELLIGENCE REPORT — JUNE 2024
    Source: Internal synthesis from SEC filings, conference abstracts, LinkedIn signals
    Classification: INTERNAL USE ONLY

    === SECTION 1: EMERGING GENE THERAPY PLAYERS ===

    HelixDyne Therapeutics (San Diego) has disclosed a proprietary AAV capsid engineering platform
    targeting Duchenne Muscular Dystrophy with an IND filing expected Q4 2024. Their Series B of
    $95M closed in March 2024 with Flagship Pioneering leading. Key differentiator: tissue-specific
    tropism improvements reducing off-target hepatic expression by reportedly 40%.

    VectorBridge Bio (Cambridge, MA) is pursuing a next-generation lentiviral vector for ex-vivo
    CAR-T manufacturing. The company recently poached the Head of CMC from Bluebird Bio, signaling
    imminent scale-up. They filed 3 new patents in Q1 2024 covering novel pseudotyping strategies.

    NovaSynapse Genomics (Basel) combines CRISPR base-editing with targeted liposomal delivery.
    Their lead program SNP-701 targets a point mutation prevalent in Wilson disease. Phase I expected
    to initiate H2 2025. Partnered with Novartis for co-development in rare CNS disorders.

    === SECTION 2: AI-DRIVEN DRUG DISCOVERY ===

    PharmaAxis AI (London) claims a generative chemistry model (AxGen-v3) capable of designing
    molecules with predicted ADMET profiles in under 72 hours. Raised $60M Series A in February 2024.
    Their pipeline includes 5 preclinical candidates in oncology and metabolic disease.

    AlphaGen Bio (South San Francisco) uses multi-modal deep learning integrating proteomics and
    cryo-EM structural data. Lead asset AG-201 (NASH) entered Phase II with interim readout in Q3 2024.
    CEO previously led R&D at Genentech. Board includes two former FDA division directors.

    === SECTION 3: FINANCING & DEAL ACTIVITY ===

    CrisprEdge announced a $120M Series C on May 3, 2024, led by OrbiMed with participation from
    ARCH Venture Partners. Proceeds earmarked for GBM (glioblastoma multiforme) Phase I dose
    escalation and manufacturing buildout in Research Triangle Park, NC.

    Undisclosed Asian strategic investor made a $45M minority stake in VectorBridge Bio per SEC
    Form D filing dated April 29, 2024. Deal terms include right-of-first-negotiation for Asia-Pacific
    commercialization rights.

    === SECTION 4: REGULATORY & CLINICAL SIGNALS ===

    FDA granted Regenerative Medicine Advanced Therapy (RMAT) designation to HelixDyne's DMD program
    on June 7, 2024, following precedent set by Sarepta Therapeutics. This accelerates the IND pathway.

    NovaSynapse received EMA orphan designation for SNP-701 in Wilson disease on May 14, 2024.
    The designation provides 10-year market exclusivity in the EU upon approval.

    VectorBridge Bio's IND for VB-320 (CAR-T for relapsed/refractory AML) cleared FDA review
    on June 3, 2024, with first patient dosing anticipated Q3 2024.

    === SECTION 5: TALENT & LEADERSHIP SIGNALS ===

    PharmaAxis AI hired Dr. Elena Markov (ex-DeepMind Health) as Chief Scientific Officer in May 2024.
    Her expertise in protein structure prediction is expected to strengthen their structural biology pipeline.

    AlphaGen Bio promoted Dr. Kenji Watanabe to COO, consolidating operations ahead of anticipated
    Phase II readout and potential partnership discussions with big pharma.

    HelixDyne expanded their scientific advisory board with three KOLs specializing in
    neuromuscular diseases from Johns Hopkins, Mayo Clinic, and UCL.
"""))

# ─── 4. Create a second data source for multi-source ingestion test ──────────
intel_report2 = WORKSPACE / "data" / "raw" / "regulatory_pipeline_june2024.txt"
intel_report2.write_text(textwrap.dedent("""\
    REGULATORY PIPELINE TRACKER — GENE THERAPY FOCUS — JUNE 2024

    HelixDyne DMD Program: RMAT designation confirmed June 7 2024, Type B meeting with FDA scheduled Q3 2024.
    Regulatory strategy targets accelerated approval pathway using surrogate endpoint (dystrophin expression).
    Clinical hold risk: low based on preclinical package completeness per KOL interviews.

    VectorBridge VB-320 IND cleared June 3 2024. Phase I open-label dose escalation at 3 US sites.
    Safety monitoring committee includes independent hematologists from MD Anderson and Memorial Sloan Kettering.
    Primary endpoint: dose-limiting toxicity rate; secondary: minimal residual disease response at Day 28.

    NovaSynapse SNP-701 EMA orphan designation May 14 2024. EU clinical trial application planned Q1 2025.
    Swiss regulatory authority Swissmedic alignment meeting completed April 2024 with positive outcome.
    The rare disease designation means priority review and reduced regulatory fees in multiple jurisdictions.

    CrisprEdge GBM Phase I protocol incorporates tumor-infiltrating lymphocyte co-administration,
    a novel combination approach not previously tested in CRISPR-based CNS interventions.
    Data Safety Monitoring Board constituted with three external neuro-oncologists.

    PharmaAxis AI has no active INDs but is progressing two candidates toward IND-enabling studies:
    PAX-101 (oncology) and PAX-203 (metabolic disease). Both expected to enter IND-enabling studies H2 2024.

    AlphaGen AG-201 Phase II interim data expected September 2024. Primary endpoint is NASH resolution
    without worsening of fibrosis (FDA-accepted composite endpoint). Enrollment completed March 2024.
"""))

print("Workspace initialized successfully.")
print(f"Key files created:")
print(f"  - {intel_report}")
print(f"  - {intel_report2}")
print(f"  - {vault_py}")
print(f"  - {pyproject}")