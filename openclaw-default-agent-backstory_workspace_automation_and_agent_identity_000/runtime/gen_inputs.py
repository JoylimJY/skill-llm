import os
import random

random.seed(42)

workspace = "/workspace"

# --- Create distractor directory structure ---
distractor_dirs = [
    "experiments/trial_001",
    "experiments/trial_002",
    "data/raw/genomics",
    "data/processed/proteomics",
    "reports/q1",
    "reports/q2",
    "scripts/analysis",
    "scripts/preprocessing",
    "notebooks/exploratory",
    "pipelines/ingestion",
    "pipelines/validation",
    "references",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "experiments/trial_001/params.json": '{"lr": 0.001, "epochs": 50, "batch_size": 32}',
    "experiments/trial_002/params.json": '{"lr": 0.0005, "epochs": 100, "batch_size": 64}',
    "data/raw/genomics/sample_ids.txt": "\n".join(f"SAMPLE_{i:04d}" for i in range(20)),
    "data/processed/proteomics/metadata.csv": "sample_id,condition,replicate\nS001,control,1\nS002,treated,1\nS003,control,2",
    "reports/q1/summary.txt": "Q1 results: 12 experiments completed, 3 hits identified.",
    "reports/q2/summary.txt": "Q2 results: 18 experiments completed, 7 leads advanced.",
    "scripts/analysis/run_deseq.sh": "#!/bin/bash\nRscript deseq2_pipeline.R $1 $2",
    "scripts/preprocessing/normalize.py": "import pandas as pd\ndf = pd.read_csv('input.csv')\ndf = (df - df.mean()) / df.std()\ndf.to_csv('output.csv', index=False)",
    "notebooks/exploratory/eda.ipynb": '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}',
    "pipelines/ingestion/config.yaml": "source: s3://biotech-data\ndest: /data/raw\nschedule: daily",
    "pipelines/validation/schema.json": '{"type": "object", "properties": {"sample_id": {"type": "string"}}}',
    "references/gene_ontology_terms.txt": "GO:0008150 biological_process\nGO:0003674 molecular_function\nGO:0005575 cellular_component",
}
for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- Placeholder / stub versions of core context files (the "messy input") ---
# These simulate an existing but broken workspace that needs bootstrap mode

stub_agents = """# AGENTS.md
<!-- TODO: fill this in -->
"""

stub_soul = """# SOUL.md
TBD
"""

stub_identity = """# IDENTITY.md
name: (not set)
role: (not set)
"""

stub_tools = """# TOOLS.md
## Tools
- (list tools here)
"""

stub_user = """# USER.md
## User Profile
Name: Dr. Yuki Tanaka
Role: Principal Investigator, Oncology Research
(rest TBD)
"""

stub_heartbeat = """# HEARTBEAT.md
cadence: TBD
"""

stub_bootstrap = """# BOOTSTRAP.md
Status: Not started
"""

# Write stubs at workspace root
stubs = {
    "AGENTS.md": stub_agents,
    "SOUL.md": stub_soul,
    "IDENTITY.md": stub_identity,
    "TOOLS.md": stub_tools,
    "USER.md": stub_user,
    "HEARTBEAT.md": stub_heartbeat,
    "BOOTSTRAP.md": stub_bootstrap,
}
for filename, content in stubs.items():
    with open(os.path.join(workspace, filename), "w") as f:
        f.write(content)

# --- Pre-answered interview responses file ---
# The agent should use these to synthesize content into core files
interview_answers = """# Bootstrap Interview — Pre-Answered Responses
# Use these answers to complete the agent workspace configuration.

Q1: What is the agent's primary purpose and domain?
A: This agent supports a biotech oncology research team led by Dr. Yuki Tanaka.
   It should help with literature synthesis, experimental design suggestions,
   data interpretation, and lab meeting preparation. The team works on targeted
   cancer therapies, primarily KRAS and TP53 mutations.

Q2: What tools and integrations does the team use daily?
A: The team uses Python (pandas, scanpy, DESeq2 via R), Jupyter notebooks,
   a shared S3 bucket for raw data, Slack for communication, and Notion for
   lab documentation. The agent should prioritize CLI-friendly responses.

Q3: What should the agent's personality and communication style be?
A: Professional but approachable. Precise and evidence-based. Should cite
   uncertainty explicitly. Should never guess at clinical outcomes. Prefers
   bullet points and structured summaries. Avoid jargon unless the user is
   clearly technical.

Q4: What are the most important behavioral guardrails for this agent?
A: Must not fabricate citations or experimental results. Must flag when a
   question is outside oncology/bioinformatics scope. Must escalate ambiguous
   clinical implications to Dr. Tanaka rather than self-resolve. Confidentiality
   of patient-derived sample data is paramount — never log or repeat sample IDs
   in memory files.

Q5: What does a successful daily session look like, and what should be remembered across sessions?
A: Each session starts with a brief status check of ongoing experiments.
   The agent should remember active project names, pending literature reviews,
   and team member names across sessions. Daily notes should capture decisions
   made, not raw data. Memory should NOT store sample IDs or raw genomic data.
"""
with open(os.path.join(workspace, "interview_answers.md"), "w") as f:
    f.write(interview_answers)

print("Workspace initialized successfully.")
print(f"Core stub files: {list(stubs.keys())}")
print("Interview answers written to interview_answers.md")