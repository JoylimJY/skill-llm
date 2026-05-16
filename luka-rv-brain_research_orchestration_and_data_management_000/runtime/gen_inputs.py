import os
import random
import json
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Clone the actual researchvault package from a public repo ─────────────────
# We simulate the project existing via git clone in setup_script.
# Here we create the messy research context files the agent must work with.

# ── Distractor directory structure ────────────────────────────────────────────
dirs = [
    "data/raw/pubmed",
    "data/raw/clinical_trials",
    "data/processed/candidates",
    "data/processed/rejected",
    "notes/hypotheses",
    "notes/meetings",
    "reports/q1",
    "reports/q2",
    "scripts/legacy",
    "config/environments",
    "config/pipelines",
    "archive/2023",
    "archive/2022",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files ─────────────────────────────────────────────────────────────
distractor_files = {
    "data/raw/pubmed/batch_001.csv": textwrap.dedent("""\
        pmid,title,abstract,year
        38291044,"Metformin in glioblastoma","Retrospective cohort showing 12% OS improvement",2024
        38102938,"Ivermectin antiviral claims","Meta-analysis of 8 RCTs; inconclusive",2023
        37984211,"Aspirin colorectal prevention","Large RCT confirms chemopreventive effect",2024
    """),
    "data/raw/pubmed/batch_002.csv": textwrap.dedent("""\
        pmid,title,abstract,year
        38401022,"Doxycycline anti-glioma","In vitro synergy with TMZ observed",2024
        38205819,"Mebendazole repurposing review","Broad spectrum anti-cancer activity",2023
    """),
    "data/raw/clinical_trials/active_trials.json": json.dumps([
        {"nct_id": "NCT05112345", "drug": "Metformin", "condition": "Glioblastoma", "phase": "II", "status": "Recruiting"},
        {"nct_id": "NCT05209876", "drug": "Mebendazole", "condition": "Colon Cancer", "phase": "I/II", "status": "Active"},
        {"nct_id": "NCT04891234", "drug": "Ivermectin", "condition": "NSCLC", "phase": "II", "status": "Terminated"},
    ], indent=2),
    "data/processed/candidates/shortlist.txt": textwrap.dedent("""\
        # Candidate drugs for repurposing - Q1 2024
        1. Metformin (AMPK activation, autophagy)
        2. Mebendazole (tubulin disruption)
        3. Doxycycline (mitochondrial inhibition)
        4. Itraconazole (Hedgehog pathway)
    """),
    "data/processed/rejected/exclusion_log.csv": textwrap.dedent("""\
        drug,reason,date
        Ivermectin,insufficient human evidence,2024-01-15
        Hydroxychloroquine,failed Phase III,2024-02-01
    """),
    "notes/hypotheses/metformin_glio.md": textwrap.dedent("""\
        # Hypothesis: Metformin + TMZ Synergy in GBM
        
        Mechanism: AMPK activation suppresses mTORC1, sensitizing GBM to TMZ.
        Evidence level: Preclinical (strong), Clinical (weak - single-arm Phase II)
        Confidence: 0.55
        
        Open questions:
        - BBB penetration at therapeutic doses?
        - Optimal dosing schedule?
    """),
    "notes/hypotheses/mebendazole_broad.md": textwrap.dedent("""\
        # Hypothesis: Mebendazole as Broad-Spectrum Anti-Cancer Agent
        
        Mechanism: Beta-tubulin polymerization inhibition
        Evidence: Multiple xenograft models, 2 case reports
        Confidence: 0.40 (very low - mostly preclinical)
        
        Needs: Prospective clinical data urgently
    """),
    "notes/meetings/2024_03_12_kickoff.txt": textwrap.dedent("""\
        Meeting notes - Drug Repurposing Task Force
        Date: 2024-03-12
        
        Agenda:
        - Review Q4 2023 findings
        - Prioritize verification targets
        - Assign literature review tasks
        
        Action items:
        - Set up centralized tracking system (owner: data team)
        - Flag low-confidence findings for independent verification
    """),
    "reports/q1/summary_draft.txt": textwrap.dedent("""\
        Q1 2024 Drug Repurposing Report - DRAFT
        
        Top candidates: Metformin, Mebendazole, Doxycycline
        Key risk: Several findings lack clinical validation.
        Recommendation: Initiate verification workflow for confidence < 0.5 items.
    """),
    "reports/q2/placeholder.txt": "Q2 report not yet started.\n",
    "config/environments/dev.env": textwrap.dedent("""\
        VAULT_DB_PATH=./dev_vault.db
        EMBEDDING_MODEL=all-MiniLM-L6-v2
        LOG_LEVEL=DEBUG
    """),
    "config/pipelines/ingestion.yaml": textwrap.dedent("""\
        pipeline:
          name: pubmed-ingestion
          sources:
            - type: url
              value: https://pubmed.ncbi.nlm.nih.gov/search/?term=drug+repurposing+glioblastoma
            - type: url
              value: https://clinicaltrials.gov/search?cond=Glioblastoma&intr=repurposing
          schedule: weekly
    """),
    "config/pipelines/synthesis.yaml": textwrap.dedent("""\
        synthesis:
          similarity_threshold: 0.72
          max_links_per_artifact: 10
          embedding_batch_size: 32
    """),
    "scripts/legacy/old_tracker.py": textwrap.dedent("""\
        #!/usr/bin/env python3
        # DEPRECATED - replaced by new vault system
        import sqlite3
        
        def init_old_db(path):
            conn = sqlite3.connect(path)
            conn.execute("CREATE TABLE IF NOT EXISTS findings (id TEXT, content TEXT)")
            conn.commit()
            return conn
        
        if __name__ == "__main__":
            print("This script is deprecated. Use the new vault system.")
    """),
    "scripts/legacy/migrate_v1.sh": textwrap.dedent("""\
        #!/bin/bash
        # Migration script from v1 flat-file system
        echo "Migrating legacy data..."
        # TODO: implement migration logic
        echo "Migration complete (stub)"
    """),
    "archive/2023/findings_export.jsonl": "\n".join([
        json.dumps({"id": f"arc-{i:04d}", "finding": f"Legacy finding {i}", "confidence": round(random.uniform(0.3, 0.9), 2)})
        for i in range(20)
    ]),
    "archive/2022/old_notes.txt": "Pre-systematic-review notes. Not validated. Do not use.\n",
}

for rel_path, content in distractor_files.items():
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# ── Task specification file ───────────────────────────────────────────────────
# This is the business brief the agent receives as context.
# It does NOT hint at CLI commands.
task_brief = textwrap.dedent("""\
    DRUG REPURPOSING RESEARCH BRIEF
    ================================
    Project: Oncology Drug Repurposing Initiative
    Team: Computational Pharmacology Group
    Date: 2024-03-15

    We are launching a systematic tracking effort for our drug repurposing research.
    The focus is on identifying off-label oncology drug candidates with emerging evidence.

    REQUIREMENTS:
    1. Initialize a persistent research project with:
       - Project ID: "pharma-repurpose-v1"
       - Project Name: "Oncology Drug Repurposing"
       - Objective: "Identify off-label drug candidates with emerging clinical evidence for oncology indications"

    2. Ingest the following two public sources into the project:
       - https://pubmed.ncbi.nlm.nih.gov/search/?term=drug+repurposing+glioblastoma
       - https://clinicaltrials.gov/search?cond=Glioblastoma&intr=repurposing

    3. Run the automated relationship-discovery process to link related findings.

    4. Run the verification planning step to flag low-confidence data for follow-up.

    The system must persist all state locally. After completion, please confirm what
    the vault's SQLite database path is and that the above steps were executed.
""")
(workspace / "RESEARCH_BRIEF.txt").write_text(task_brief)

print("Workspace initialized successfully.")
print(f"Files created: {len(distractor_files)} distractor files + 1 task brief")