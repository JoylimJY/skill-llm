import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "lab/projects/quantum_sim/data",
    "lab/projects/quantum_sim/results",
    "lab/projects/neutrino_detect/logs",
    "lab/projects/neutrino_detect/models",
    "lab/team/profiles",
    "lab/team/schedules",
    "lab/configs/hardware",
    "lab/configs/software",
    "lab/archive/2024/papers",
    "lab/archive/2024/reports",
    "lab/archive/2023/data",
    "lab/scratch",
    "lab/notes/meetings",
    "lab/notes/ideas",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but irrelevant to the task
distractor_files = {
    "lab/projects/quantum_sim/data/run_001.csv": "time,energy,momentum\n0.1,2.3,1.1\n0.2,2.4,1.2\n",
    "lab/projects/quantum_sim/results/summary.txt": "Simulation converged after 1200 iterations. Energy error: 0.003%",
    "lab/projects/neutrino_detect/logs/detector.log": "[2026-01-15] Detector initialized. Threshold: 0.5 MeV\n[2026-01-16] 14 events recorded.",
    "lab/projects/neutrino_detect/models/baseline.json": json.dumps({"model": "baseline_v1", "accuracy": 0.87, "threshold": 0.5}),
    "lab/team/profiles/dr_chen.txt": "Dr. Sarah Chen - Lead Physicist - Focus: Quantum Field Theory",
    "lab/team/profiles/dr_okafor.txt": "Dr. Emeka Okafor - Data Scientist - Focus: ML for particle detection",
    "lab/team/schedules/weekly_2026_03.csv": "Mon,Team standup,09:00\nWed,Paper review,14:00\nFri,Compute cluster maintenance,10:00",
    "lab/configs/hardware/cluster_specs.txt": "Nodes: 48\nCPU: AMD EPYC 7763\nRAM: 512GB per node\nStorage: 2PB Lustre",
    "lab/configs/software/python_env.txt": "python==3.11\nnumpy==1.26.4\nscipy==1.12.0\nmatplotlib==3.8.3",
    "lab/archive/2024/papers/qst_preprint.txt": "Title: Quantum Stochastic Transport in Disordered Lattices\nAuthors: Chen, Okafor, Zhang\nAbstract: We present...",
    "lab/archive/2024/reports/annual_report.txt": "FY2024 Lab Report - Total publications: 7, Grant secured: $2.1M",
    "lab/archive/2023/data/experiment_log.txt": "Experiment E-042: Completed. Anomalous reading at t=42s flagged for review.",
    "lab/scratch/temp_analysis.py": "import numpy as np\n# TODO: finalize analysis\ndata = np.random.rand(100)\nprint(data.mean())",
    "lab/notes/meetings/2026_02_15.txt": "Meeting notes: Discussed new grant proposal. Priority: finish simulation by Q2.",
    "lab/notes/ideas/memory_system_notes.txt": "Idea: Use vector search for lab knowledge base. Need to handle CJK text for collaborators.",
}

for path, content in distractor_files.items():
    (workspace / path).write_text(content)

# THE ACTUAL TASK INPUT: A structured list of lab facts that must be loaded into the memory system
# These are raw, untagged facts — the agent must figure out priority tags and classifications
lab_facts = {
    "facts_to_memorize": [
        {
            "id": "F001",
            "content": "Dr. Sarah Chen is the principal investigator and lab director. She prefers LaTeX for all paper drafts and requires double-blind peer review for all submissions.",
            "suggested_importance": "critical",
            "domain": "team_identity"
        },
        {
            "id": "F002", 
            "content": "The compute cluster uses SLURM job scheduler. Max walltime is 72 hours. Use partition 'highmem' for jobs requiring more than 256GB RAM.",
            "suggested_importance": "critical",
            "domain": "tech_config"
        },
        {
            "id": "F003",
            "content": "Project QST-7 is investigating quantum stochastic transport. Current status: data collection phase. Deadline: 2026-06-30.",
            "suggested_importance": "important",
            "domain": "project"
        },
        {
            "id": "F004",
            "content": "The Heisenberg Uncertainty Principle states that the product of position and momentum uncertainties is at least ħ/2.",
            "suggested_importance": "important",
            "domain": "science"
        },
        {
            "id": "F005",
            "content": "Lab coffee machine is on the 3rd floor break room. It runs out of pods by Wednesday most weeks.",
            "suggested_importance": "normal",
            "domain": "general"
        },
        {
            "id": "F006",
            "content": "Dr. Emeka Okafor manages all ML pipelines. He uses PyTorch and prefers GPU-accelerated training on the A100 nodes.",
            "suggested_importance": "important",
            "domain": "team_identity"
        },
        {
            "id": "F007",
            "content": "SSH access to the cluster requires two-factor authentication. VPN must be active. Use 'ssh cluster.lab.internal' as the hostname.",
            "suggested_importance": "critical",
            "domain": "tech_config"
        },
        {
            "id": "F008",
            "content": "Project NEUTRINO-3 uses a water Cherenkov detector array. The detection threshold is 0.5 MeV. Background noise filter: 3-sigma cutoff.",
            "suggested_importance": "important",
            "domain": "project"
        }
    ],
    "search_queries": [
        "cluster configuration SLURM",
        "principal investigator preferences",
        "quantum transport project deadline"
    ],
    "output_file": "memory_audit_report.json"
}

(workspace / "lab_facts.json").write_text(json.dumps(lab_facts, indent=2))

# Also write a task description file (not a hint, just business context)
task_brief = """RESEARCH LAB AI ASSISTANT - MEMORY BOOTSTRAP TASK
===================================================

The QST Research Lab is deploying an AI assistant system that requires pre-loaded 
institutional knowledge to function effectively from day one.

Input data: lab_facts.json (contains 8 facts to be ingested)
Required output: memory_audit_report.json (structured audit of what was stored and retrieved)

The AI assistant system has already been installed at /opt/soul-memory.
All scripts and modules are available there.

Contact: lab-admin@qst-lab.internal
"""
(workspace / "TASK_BRIEF.txt").write_text(task_brief)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files)} distractor files + lab_facts.json + TASK_BRIEF.txt")