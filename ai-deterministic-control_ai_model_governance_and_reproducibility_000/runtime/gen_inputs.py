import os
import json
import random
import pathlib

random.seed(42)

workspace = pathlib.Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create deeply nested distractor directory structure ---
dirs = [
    "src/models/glm",
    "src/models/gpt",
    "src/pipeline/preprocessing",
    "src/pipeline/postprocessing",
    "config/environments/prod",
    "config/environments/dev",
    "logs/2024/Q1",
    "logs/2024/Q2",
    "reports/quarterly/risk",
    "reports/quarterly/compliance",
    "data/raw/financials",
    "data/processed/financials",
    "scripts/automation",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "src/models/glm/architecture.py": """
# GLM-5 Architecture stub
class GLM5:
    def __init__(self, temperature=0.7, top_p=0.9):
        self.temperature = temperature
        self.top_p = top_p
""",
    "src/models/gpt/config.py": """
GPT_DEFAULTS = {"temperature": 0.5, "top_p": 0.95, "seed": None}
""",
    "src/pipeline/preprocessing/cleaner.py": """
def clean_text(text):
    return text.strip().lower()
""",
    "src/pipeline/postprocessing/formatter.py": """
def format_output(data):
    return json.dumps(data, indent=2)
""",
    "config/environments/prod/app.yaml": """
environment: production
log_level: WARNING
retry_limit: 3
""",
    "config/environments/dev/app.yaml": """
environment: development
log_level: DEBUG
retry_limit: 1
""",
    "logs/2024/Q1/access.log": "\n".join(
        [f"2024-01-{i:02d} INFO Request processed in {random.randint(100,500)}ms" for i in range(1, 32)]
    ),
    "logs/2024/Q2/access.log": "\n".join(
        [f"2024-04-{i:02d} INFO Request processed in {random.randint(100,500)}ms" for i in range(1, 31)]
    ),
    "reports/quarterly/risk/template.txt": """
QUARTERLY RISK REPORT TEMPLATE
================================
Model: {model}
Date: {date}
Risk Score: {score}
""",
    "reports/quarterly/compliance/checklist.json": json.dumps({
        "items": [
            {"id": 1, "check": "Model parameters locked", "status": "PENDING"},
            {"id": 2, "check": "Output consistency verified", "status": "PENDING"},
            {"id": 3, "check": "Audit trail generated", "status": "PENDING"},
        ]
    }, indent=2),
    "data/raw/financials/transactions_2024.csv": "date,amount,category\n2024-01-01,1500.00,EQUITY\n2024-01-02,2300.50,BOND\n",
    "data/processed/financials/summary.json": json.dumps({"total": 3800.50, "categories": ["EQUITY", "BOND"]}, indent=2),
    "scripts/automation/deploy.sh": "#!/bin/bash\necho 'Deploying model pipeline...'\n",
    "tests/unit/test_cleaner.py": "def test_clean_text(): assert True\n",
    "tests/integration/test_pipeline.py": "def test_pipeline_end_to_end(): assert True\n",
}

for path, content in distractor_files.items():
    full_path = workspace / path
    full_path.write_text(content)

# --- Create the openclaw.json that the inject command will modify ---
openclaw_dir = pathlib.Path.home() / ".openclaw"
openclaw_dir.mkdir(parents=True, exist_ok=True)

# The openclaw.json starts with stale/wrong parameters for glm-5
openclaw_config = {
    "version": "1.0",
    "models": {
        "glm-5": {
            "temperature": 0.7,
            "top_p": 0.9,
            "seed": None,
            "description": "GLM-5 default config"
        },
        "gpt-4": {
            "temperature": 0.5,
            "top_p": 0.95,
            "seed": 100,
            "description": "GPT-4 default config"
        }
    },
    "global": {
        "timeout": 30,
        "retry_limit": 3
    }
}

openclaw_json_path = openclaw_dir / "openclaw.json"
openclaw_json_path.write_text(json.dumps(openclaw_config, indent=2))

# --- Create workspace dir for signal file (must exist) ---
openclaw_workspace = openclaw_dir / "workspace"
openclaw_workspace.mkdir(parents=True, exist_ok=True)

# --- Create a stale/wrong signal file to make sure agent overwrites it ---
stale_signal = {
    "preset": "creative_writing",
    "temperature": 0.8,
    "top_p": 0.95,
    "applied_at": "2024-01-01T00:00:00"
}
signal_path = openclaw_workspace / ".detcontrol_signal.json"
signal_path.write_text(json.dumps(stale_signal, indent=2))

# --- Task instruction file (business context only, no technical hints) ---
task_brief = """TASK BRIEF - Financial AI Platform Stability Audit
===================================================

Context:
Our data analysis pipeline uses the glm-5 model to generate quarterly risk summaries.
Compliance requires that all AI outputs are reproducible and consistent.

Required Actions:
1. Configure the AI control system for data analysis workloads using the appropriate
   stability profile designed for that use case.

2. Push these stability settings into the platform model configuration for glm-5.

3. Run a consistency audit on the following prompt (use 5 samples):
   "Analyze the quarterly risk factors for a mid-cap equity portfolio"
   
   Save the full consistency audit results to a file named: consistency_audit_report.json
   (place it in the /workspace/reports/quarterly/risk/ directory)

The compliance team needs to verify that all three steps were completed correctly.
"""
(workspace / "TASK_BRIEF.txt").write_text(task_brief)

print("Workspace generated successfully.")
print(f"openclaw.json created at: {openclaw_dir / 'openclaw.json'}")
print(f"Signal file (stale) at: {openclaw_dir / 'workspace' / '.detcontrol_signal.json'}")