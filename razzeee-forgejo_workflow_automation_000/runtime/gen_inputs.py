#!/usr/bin/env python3
import os
import random
import json

random.seed(42)

workspace = "/workspace"

# Create a deeply nested distractor directory structure
dirs = [
    "aerospace/qms/docs/procedures",
    "aerospace/qms/docs/standards",
    "aerospace/qms/audit_logs/2024/Q1",
    "aerospace/qms/audit_logs/2024/Q2",
    "aerospace/software/modules/nav_core",
    "aerospace/software/modules/telemetry",
    "aerospace/software/modules/comm_stack",
    "aerospace/compliance/reports/draft",
    "aerospace/compliance/reports/final",
    "aerospace/ci_pipeline/configs",
    "aerospace/ci_pipeline/logs",
    "tools/scripts",
    "tools/configs",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files with realistic aerospace content
distractor_files = {
    "aerospace/qms/docs/procedures/change_control.md": "# Change Control Procedure\n\nAll software changes must be reviewed by QA prior to merge.\nChange requests must reference a defect ticket.\nApproval threshold: 2 senior engineers.\n",
    "aerospace/qms/docs/standards/DO-178C_compliance.txt": "DO-178C Software Levels:\nLevel A - Catastrophic\nLevel B - Hazardous\nLevel C - Major\nLevel D - Minor\n\nAll nav_core modules are classified Level B.\n",
    "aerospace/qms/audit_logs/2024/Q1/audit_q1.csv": "Date,Auditor,Module,Finding,Severity\n2024-01-15,J.Smith,nav_core,Unchecked return value,HIGH\n2024-02-03,A.Lee,telemetry,Missing unit test,MEDIUM\n2024-03-22,J.Smith,comm_stack,Deprecated API usage,LOW\n",
    "aerospace/qms/audit_logs/2024/Q2/audit_q2.csv": "Date,Auditor,Module,Finding,Severity\n2024-04-10,B.Jones,nav_core,Buffer overflow risk,CRITICAL\n2024-05-18,A.Lee,telemetry,Race condition,HIGH\n",
    "aerospace/software/modules/nav_core/nav_main.c": "/* Navigation Core Module */\n#include <stdint.h>\n\nvoid compute_position(float lat, float lon) {\n    // TODO: implement Kalman filter\n}\n",
    "aerospace/software/modules/telemetry/telem_handler.py": "# Telemetry Handler\nimport socket\n\ndef send_telemetry(data):\n    # FIXME: add retry logic\n    pass\n",
    "aerospace/software/modules/comm_stack/comm.rs": "// Communication Stack\npub fn transmit(payload: &[u8]) -> Result<(), String> {\n    // stub\n    Ok(())\n}\n",
    "aerospace/compliance/reports/draft/q2_draft.txt": "DRAFT - Q2 Software Compliance Report\nStatus: INCOMPLETE\nOpen defects: TBD\nPending review: see repository\n",
    "aerospace/ci_pipeline/configs/pipeline.yaml": "stages:\n  - lint\n  - build\n  - test\n  - deploy\n\nlint:\n  script: cargo clippy\n\nbuild:\n  script: make all\n\ntest:\n  script: pytest tests/\n",
    "aerospace/ci_pipeline/logs/build_20240510.log": "[INFO] Build started\n[INFO] Compiling nav_core... OK\n[WARN] telemetry: 2 deprecation warnings\n[ERROR] comm_stack: linker error on armv7\n[INFO] Build failed\n",
    "tools/scripts/check_deps.sh": "#!/bin/bash\necho 'Checking dependencies...'\ncommand -v git && echo 'git: OK'\ncommand -v python3 && echo 'python3: OK'\n",
    "tools/configs/repo_mirrors.json": '{"primary": "https://internal.aerospace.corp/git", "mirror": "https://backup.aerospace.corp/git"}\n',
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# Write a task brief that describes the business context but gives NO technical hints
task_brief = """AEROSPACE SOFTWARE QA - COMPLIANCE AUDIT REQUEST
=================================================

From: Chief Quality Officer
To: QA Automation Team
Subject: Urgent - Compliance Snapshot Required

We need an automated snapshot of the current state of our internal code repository
for the upcoming DO-178C audit.

Specifically, we need:
1. A list of all OPEN defect tickets (issues) in the 'aeroquality/nav-core' repository.
2. Full metadata for Pull Request #3 in that same repository.

Please produce a file called 'compliance_snapshot.json' with this data.

The internal repository service is running locally. Credentials and connection
details are in /workspace/repo_access.cfg

"""

with open(os.path.join(workspace, "AUDIT_REQUEST.txt"), "w") as f:
    f.write(task_brief)

# Write repo_access.cfg with connection details for the local mock
repo_access = """[forgejo]
url = http://localhost:3000
token = test-token-aerospace-42
owner = aeroquality
repo = nav-core
login_name = local-forgejo
"""

with open(os.path.join(workspace, "repo_access.cfg"), "w") as f:
    f.write(repo_access)

print("Workspace initialized.")
print(f"Files created: {len(distractor_files) + 2}")