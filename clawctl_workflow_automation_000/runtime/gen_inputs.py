import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create realistic distractor directory structure ---
dirs = [
    "pipeline/screening",
    "pipeline/docking",
    "pipeline/admet",
    "pipeline/reporting",
    "data/compounds/batch_001",
    "data/compounds/batch_002",
    "data/results/docking_scores",
    "data/results/admet_flags",
    "logs/agents",
    "logs/errors",
    "configs",
    "scripts",
    "artifacts/reports",
    "artifacts/models",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "pipeline/screening/run_config.yaml": "batch: batch_001\nthreshold: 0.75\nmethod: vina\n",
    "pipeline/docking/receptor_prep.log": "[INFO] Receptor grid generated\n[INFO] 142 conformers sampled\n",
    "pipeline/admet/filter_rules.json": json.dumps({"lipinski": True, "hERG": True, "ames": True}, indent=2),
    "pipeline/reporting/template.md": "# Compound Report\n\n## Summary\n\n## Results\n",
    "data/compounds/batch_001/smiles.csv": "compound_id,smiles\nCPD001,CC(=O)OC1=CC=CC=C1C(=O)O\nCPD002,CN1C=NC2=C1C(=O)N(C(=O)N2C)C\n",
    "data/compounds/batch_002/smiles.csv": "compound_id,smiles\nCPD003,CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C\nCPD004,C1CCCCC1\n",
    "data/results/docking_scores/batch_001_scores.csv": "compound_id,score\nCPD001,-8.2\nCPD002,-6.5\n",
    "data/results/admet_flags/batch_001_flags.json": json.dumps({"CPD001": {"hERG": False, "ames": False}, "CPD002": {"hERG": True, "ames": False}}, indent=2),
    "logs/agents/screener.log": "[2024-01-10 09:00:00] screener: started batch_001\n[2024-01-10 09:45:00] screener: 42 hits found\n",
    "logs/errors/admet_warnings.log": "WARNING: CPD002 failed hERG filter\nWARNING: CPD003 low solubility predicted\n",
    "configs/agent_roles.yaml": "agents:\n  - name: screener\n    role: screening-agent\n  - name: docker_agent\n    role: docking-agent\n  - name: admet_agent\n    role: admet-agent\n  - name: reporter\n    role: reporting-agent\n",
    "scripts/preprocess.py": "#!/usr/bin/env python3\n# Placeholder preprocessing script\nimport sys\nprint('Preprocessing', sys.argv[1:])\n",
    "artifacts/reports/preliminary_findings.txt": "Preliminary: 42 hits from batch_001, 3 top candidates forwarded to docking.\n",
    "artifacts/models/scoring_model_v2.pkl.info": "model: RF_v2\ntrained_on: ChEMBL30\nauc: 0.91\n",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# --- Task specification file (the "business brief" the agent must read and act on) ---
# This describes the scenario in plain English — the agent must translate this into clawctl operations
brief = {
    "pipeline_name": "Project Phoenix - Lead Optimization Sprint 3",
    "coordinator": "lead_coord",
    "agents": [
        {"name": "screener",    "role": "screening-agent"},
        {"name": "docker_agent","role": "docking-agent"},
        {"name": "admet_agent", "role": "admet-agent"},
        {"name": "reporter",    "role": "reporting-agent"},
    ],
    "tasks_to_create": [
        {
            "ref": "TASK_A",
            "subject": "Screen batch_002 compounds against target EGFR",
            "description": "Run virtual screening on batch_002 using EGFR receptor grid v3",
            "priority": 2,
            "assigned_to": "screener"
        },
        {
            "ref": "TASK_B",
            "subject": "Dock top hits from batch_002 into EGFR binding pocket",
            "description": "Molecular docking of screening hits with AutoDock Vina, output scores to results/docking_scores/",
            "priority": 1,
            "assigned_to": "docker_agent",
            "parent_ref": "TASK_A"
        },
        {
            "ref": "TASK_C",
            "subject": "Run ADMET profiling on docked compounds",
            "description": "Apply ADMET filters (hERG, Ames, Lipinski) to docking hits",
            "priority": 1,
            "assigned_to": "admet_agent",
            "parent_ref": "TASK_B"
        },
        {
            "ref": "TASK_D",
            "subject": "Compile lead optimization report for Sprint 3",
            "description": "Aggregate screening, docking, and ADMET results into final report",
            "priority": 0,
            "assigned_to": "reporter",
            "parent_ref": "TASK_C"
        }
    ],
    "workflow_actions": [
        # screener claims and starts TASK_A
        {"action": "claim_and_start", "agent": "screener", "task_ref": "TASK_A"},
        # docker_agent is blocked waiting for screener: TASK_B blocked by TASK_A
        {"action": "block", "agent": "docker_agent", "task_ref": "TASK_B", "blocked_by_ref": "TASK_A"},
        # screener finishes TASK_A with a note and artifact metadata
        {
            "action": "done",
            "agent": "screener",
            "task_ref": "TASK_A",
            "note": "Completed screening: 18 hits above threshold 0.75",
            "meta": {"artifact": "data/results/docking_scores/batch_002_hits.csv"}
        },
        # screener sends a handoff message to docker_agent about TASK_B
        {
            "action": "msg",
            "from_agent": "screener",
            "to_agent": "docker_agent",
            "body": "Batch_002 screening done. 18 hits ready for docking. Results in data/results/docking_scores/batch_002_hits.csv",
            "task_ref": "TASK_B",
            "msg_type": "handoff"
        },
        # docker_agent claims and starts TASK_B
        {"action": "claim_and_start", "agent": "docker_agent", "task_ref": "TASK_B"},
        # docker_agent marks TASK_B for review before done
        {"action": "review", "agent": "docker_agent", "task_ref": "TASK_B"},
        # docker_agent completes TASK_B
        {
            "action": "done",
            "agent": "docker_agent",
            "task_ref": "TASK_B",
            "note": "Docking complete: top 5 compounds scored below -8.0 kcal/mol",
            "meta": {"artifact": "data/results/docking_scores/batch_002_docked.csv"}
        },
        # lead_coord broadcasts a status update to all agents
        {
            "action": "broadcast",
            "agent": "lead_coord",
            "body": "Sprint 3 docking phase complete. ADMET team please proceed."
        },
        # admet_agent claims and starts TASK_C
        {"action": "claim_and_start", "agent": "admet_agent", "task_ref": "TASK_C"},
        # admet_agent completes TASK_C
        {
            "action": "done",
            "agent": "admet_agent",
            "task_ref": "TASK_C",
            "note": "ADMET: 3 compounds passed all filters. 2 flagged for hERG liability.",
            "meta": {"artifact": "data/results/admet_flags/batch_002_flags.json"}
        },
        # admet_agent sends handoff to reporter for TASK_D
        {
            "action": "msg",
            "from_agent": "admet_agent",
            "to_agent": "reporter",
            "body": "ADMET profiling complete. 3 clean leads ready for report compilation.",
            "task_ref": "TASK_D",
            "msg_type": "handoff"
        },
        # reporter claims and starts TASK_D
        {"action": "claim_and_start", "agent": "reporter", "task_ref": "TASK_D"},
        # reporter completes TASK_D
        {
            "action": "done",
            "agent": "reporter",
            "task_ref": "TASK_D",
            "note": "Sprint 3 report compiled: 3 lead candidates identified for wet-lab validation.",
            "meta": {"artifact": "artifacts/reports/sprint3_leads.pdf"}
        },
    ]
}

(workspace / "configs" / "sprint3_brief.json").write_text(json.dumps(brief, indent=2))

# Also write a plain-english scenario description for the agent
scenario_text = """
PROJECT PHOENIX — SPRINT 3 COORDINATION BRIEF
==============================================

You are the pipeline coordinator for Project Phoenix, a computational drug discovery effort.
Your job is to set up the coordination system and orchestrate a four-agent pipeline using the
agent fleet management tooling available on this system.

The details of what needs to be done are in: configs/sprint3_brief.json

The agent roles, task hierarchy, blocking dependencies, completion notes, artifact references,
and inter-agent communication requirements are all specified there.

Your deliverable: a fully executed pipeline coordination state recorded in the system,
matching the workflow described in the brief.

The tool you need is already installed. Initialize it, register the agents, create the tasks
in the correct hierarchy, drive them through their lifecycle states, record blockers,
send the right types of messages, and attach artifact references where specified.
"""

(workspace / "MISSION.txt").write_text(scenario_text)

print("Workspace generated successfully.")