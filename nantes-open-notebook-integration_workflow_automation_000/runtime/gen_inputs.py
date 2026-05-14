import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic deeply nested directory structure with distractor files
dirs = [
    "project/docs/papers",
    "project/docs/notes",
    "project/src/analysis",
    "project/src/data_ingest",
    "project/config",
    "project/logs",
    "project/notebooks_backup",
    "project/experiments/run_001",
    "project/experiments/run_002",
    "project/references",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "project/docs/papers/crispr_review.txt": "CRISPR-Cas9 systems enable precise genome editing by leveraging guide RNA specificity.",
    "project/docs/papers/rna_seq_methods.txt": "RNA-seq quantification methods include STAR, HISAT2, and kallisto for transcript abundance.",
    "project/docs/notes/meeting_2024_03.txt": "Discussed off-target effects in gene editing; need to review literature.",
    "project/docs/notes/TODO.txt": "- Finish analysis pipeline\n- Update notebook IDs\n- Review model outputs",
    "project/src/analysis/stats.py": "import scipy\nimport numpy as np\n# placeholder analysis script",
    "project/src/data_ingest/loader.py": "# data loader stub\ndef load_csv(path): pass",
    "project/config/settings.ini": "[DEFAULT]\nmodel=qwen3-4b\napi_host=localhost\napi_port=5055",
    "project/config/docker-compose-host-ollama.yml": "version: '3'\nservices:\n  app:\n    image: open-notebook\n    ports:\n      - '5055:5055'",
    "project/logs/ingest_2024_03_01.log": "[INFO] Loaded 42 records\n[WARN] 3 duplicates skipped",
    "project/logs/search_errors.log": "[ERROR] Connection refused at localhost:5055\n[ERROR] Retry 1/3...",
    "project/notebooks_backup/old_notebook_ids.txt": "# OUTDATED - do not use\nSIMULATION=notebook:aabbcc\nRESEARCH=notebook:ddeeff",
    "project/experiments/run_001/params.json": json.dumps({"lr": 0.001, "epochs": 50, "batch_size": 32}, indent=2),
    "project/experiments/run_002/params.json": json.dumps({"lr": 0.0005, "epochs": 100, "batch_size": 64}, indent=2),
    "project/references/bibliography.bib": "@article{test2024,\n  title={Test},\n  author={Author},\n  year={2024}\n}",
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# The actual input: a set of research snippets to be ingested
# These are the observations the agent must add to the notebook
research_snippets = [
    "Proteomics analysis revealed elevated expression of HSP70 chaperone proteins under heat stress conditions in HeLa cells.",
    "Mass spectrometry data indicates a 3.2-fold upregulation of mitochondrial complex I subunits following hypoxia treatment.",
    "Single-cell RNA sequencing of 10,000 neurons identified 7 distinct transcriptional clusters correlated with synaptic plasticity markers.",
    "ATAC-seq chromatin accessibility profiling shows increased open chromatin at AP-1 motif regions in stimulated macrophages.",
    "Metabolomics screening detected accumulation of succinate and itaconate, confirming TCA cycle rewiring in LPS-activated monocytes.",
]

with open(os.path.join(workspace, "project/docs/research_observations.json"), "w") as f:
    json.dump({"observations": research_snippets, "project": "cell_stress_response", "model_id": "qwen3-4b"}, f, indent=2)

# The query the agent must use for the final search
with open(os.path.join(workspace, "project/docs/search_query.txt"), "w") as f:
    f.write("What metabolic and proteomic changes occur during cellular stress response?")

print("Workspace initialized successfully.")
print(f"Research snippets: {len(research_snippets)}")
print(f"Files created: {len(distractors) + 2}")