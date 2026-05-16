import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Deep distractor directory structure ---
dirs = [
    workspace / "research" / "quantum" / "papers" / "2024",
    workspace / "research" / "quantum" / "papers" / "2023",
    workspace / "research" / "biology" / "genomics",
    workspace / "obsidian_vault" / "Physics" / "Classical",
    workspace / "obsidian_vault" / "Physics" / "Quantum",
    workspace / "obsidian_vault" / "Math" / "LinearAlgebra",
    workspace / "obsidian_vault" / "Templates",
    workspace / "obsidian_vault" / "Archive" / "2023",
    workspace / "logs" / "nlm_sessions",
    workspace / "exports" / "raw",
    workspace / "tmp" / "scratch",
    workspace / "config",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    workspace / "research" / "quantum" / "papers" / "2024" / "surface_codes.txt":
        "Surface codes are a leading approach to quantum error correction...",
    workspace / "research" / "quantum" / "papers" / "2023" / "shor_algorithm.txt":
        "Shor's algorithm demonstrates exponential speedup for factoring...",
    workspace / "research" / "biology" / "genomics" / "crispr_notes.txt":
        "CRISPR-Cas9 enables precise gene editing at targeted loci...",
    workspace / "obsidian_vault" / "Physics" / "Classical" / "Newtonian_QA.md":
        "---\ntitle: Newtonian Mechanics | Deep Q&A\ndate: 2024-01-10\n---\n# Newton\n",
    workspace / "obsidian_vault" / "Physics" / "Quantum" / "Superposition_Summary.md":
        "# Superposition\nOld distracted notes about superposition states...",
    workspace / "obsidian_vault" / "Math" / "LinearAlgebra" / "Matrices_Glossary.md":
        "---\ntitle: Matrices Glossary\n---\n**Eigenvalue**: ...",
    workspace / "obsidian_vault" / "Templates" / "note_template.md":
        "# Template\nUse this for new notes.\n{{title}}\n{{date}}\n",
    workspace / "obsidian_vault" / "Archive" / "2023" / "old_meeting.md":
        "Meeting from 2023-05-12: discussed quantum hardware roadmap.",
    workspace / "logs" / "nlm_sessions" / "session_2024_01.json":
        json.dumps({"session_id": "abc123", "notebook": "Quantum Error Correction", "ts": "2024-01-15"}),
    workspace / "logs" / "nlm_sessions" / "session_2024_02.json":
        json.dumps({"session_id": "def456", "notebook": "Quantum Cryptography", "ts": "2024-02-10"}),
    workspace / "exports" / "raw" / "raw_nlm_export.txt":
        "Raw export from NotebookLM session. Contains unstructured notes on stabilizer codes.",
    workspace / "config" / "obsidian_config.json":
        json.dumps({"vault_name": "ResearchVault", "vault_path": "/workspace/obsidian_vault", "plugins": ["dataview", "templater"]}),
    workspace / "tmp" / "scratch" / "draft_questions.txt":
        "1. What is a stabilizer code?\n2. How does fault-tolerance threshold work?\n",
}
for path, content in distractor_files.items():
    path.write_text(content, encoding="utf-8")

# --- The task context file: tells the agent what notebook exists and what vault to use ---
task_brief = workspace / "task_brief.txt"
task_brief.write_text(
    "Project: Quantum Error Correction Knowledge Base\n"
    "Existing NotebookLM notebook: 'Quantum Error Correction'\n"
    "Obsidian vault location: /workspace/obsidian_vault\n"
    "Topic folder: QuantumComputing\n"
    "Language requirement: Chinese\n"
    "Output type: Structured summary (not Q&A, not glossary)\n"
    "Audit requirement: The distillation log must be written back into the source notebook for traceability.\n",
    encoding="utf-8"
)

print("Workspace initialized successfully.")
print(f"Total distractor files: {len(distractor_files)}")
print(f"Vault path: {workspace / 'obsidian_vault'}")