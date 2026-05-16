import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Project directory structure (distractors) ──────────────────────────────
dirs = [
    "project/src/core",
    "project/src/utils",
    "project/src/api",
    "project/tests/unit",
    "project/tests/integration",
    "project/docs/drafts",
    "project/docs/specs",
    "project/infra/terraform",
    "project/infra/kubernetes",
    "project/scripts",
    "internal/hr/hiring",
    "internal/finance/q3",
    "internal/legal/contracts",
    "deliverables",
    "tool_logs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ────────────────────────────────────────────────────────
distractor_files = {
    "project/src/core/engine.py": "# Core engine placeholder\nclass Engine:\n    pass\n",
    "project/src/utils/helpers.py": "# Utility helpers\ndef format_date(d): return str(d)\n",
    "project/src/api/routes.py": "# API routes - stub\nROUTES = []\n",
    "project/tests/unit/test_engine.py": "import pytest\ndef test_placeholder(): assert True\n",
    "project/tests/integration/test_api.py": "# Integration tests pending\n",
    "project/docs/drafts/outline_v1.txt": "Architecture outline - very rough draft\n1. Introduction\n2. ???\n3. Profit\n",
    "project/docs/specs/data_model_draft.json": json.dumps({"entities": ["User", "Order", "Product"], "relations": "TBD"}, indent=2),
    "project/infra/terraform/main.tf": '# Terraform config stub\nprovider "aws" { region = "us-east-1" }\n',
    "project/infra/kubernetes/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: app\n",
    "project/scripts/build.sh": "#!/bin/bash\necho 'build not yet configured'\n",
    "internal/hr/hiring/open_roles.txt": "Software Engineer x3\nDevOps Lead x1\n",
    "internal/finance/q3/budget_notes.txt": "Q3 budget under review. Awaiting CTO sign-off.\n",
    "internal/legal/contracts/nda_template.txt": "NON-DISCLOSURE AGREEMENT TEMPLATE v2.1\n[PARTY A] agrees to...\n",
    "project/docs/drafts/tech_stack_notes.txt": "Possible stack: FastAPI + PostgreSQL + Redis + React\nNeeds formal writeup for investor deck.\n",
    "project/src/core/config.py": "# Configuration module\nDEBUG = False\nDATABASE_URL = 'postgresql://localhost/app'\n",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# ── The actual task brief (given to agent as context) ──────────────────────
task_brief = {
    "request_id": "DUE-DILIGENCE-2024-Q4-007",
    "requestor": "Mei Zhang, Chief of Staff",
    "priority": "HIGH",
    "deadline": "2024-12-15",
    "description": (
        "We are preparing for our Series A investor due diligence. "
        "We need a comprehensive Technical Architecture Document (TAD) "
        "covering: system overview, component interactions, data flow, "
        "scalability strategy, and security posture. "
        "The document must be at least 1500 words, professionally formatted in Markdown. "
        "After it is written, it must be independently reviewed for completeness, "
        "technical accuracy, and investor-readiness before submission."
    ),
    "output_file": "deliverables/technical_architecture_document.md",
    "notes": "This is a writing + review task. Coordination and quality assurance are critical.",
}

(workspace / "task_brief.json").write_text(json.dumps(task_brief, indent=2))

# ── Seed tool_logs directory with an empty invocations log ─────────────────
(workspace / "tool_logs" / "invocations.jsonl").write_text("")

print("Workspace initialized successfully.")
print(f"Task brief written to: {workspace / 'task_brief.json'}")