import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# Create deeply nested distractor structure simulating a real platform-engineering repo
distractor_dirs = [
    "platform/infra/terraform/modules/vpc",
    "platform/infra/terraform/modules/eks",
    "platform/ci/pipelines/build",
    "platform/ci/pipelines/deploy",
    "platform/skills/legacy/file-scanner",
    "platform/skills/legacy/log-rotator",
    "platform/docs/runbooks",
    "platform/docs/architecture",
    "catalog/drafts/old-submissions",
    "catalog/published/v1/data-fetcher",
    "catalog/published/v1/slack-notifier",
    "tools/validators",
    "tools/linters",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files
distractors = {
    "platform/infra/terraform/modules/vpc/main.tf": 'resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }',
    "platform/infra/terraform/modules/eks/cluster.tf": 'module "eks" { source = "terraform-aws-modules/eks/aws" }',
    "platform/ci/pipelines/build/Jenkinsfile": 'pipeline { agent any; stages { stage("Build") { steps { sh "make build" } } } }',
    "platform/ci/pipelines/deploy/deploy.sh": '#!/bin/bash\necho "Deploying to prod"\nkubectl apply -f k8s/',
    "platform/skills/legacy/file-scanner/SKILL.md": "---\nname: file-scanner\ndescription: Old scanner\n---\n# File Scanner\nLegacy skill.",
    "platform/skills/legacy/log-rotator/index.js": "// Legacy log rotator\nconsole.log('rotating logs');",
    "platform/docs/runbooks/incident-response.md": "# Incident Response\n1. Page on-call\n2. Assess severity\n3. Mitigate",
    "platform/docs/architecture/system-design.md": "# System Design\nMicroservices architecture with event bus.",
    "catalog/drafts/old-submissions/draft-skill.yaml": "name: draft-x\nversion: 0.9.0\nstatus: draft",
    "catalog/published/v1/data-fetcher/manifest.json": '{"name":"data-fetcher","version":"1.0.0","author":"team-a"}',
    "catalog/published/v1/slack-notifier/manifest.json": '{"name":"slack-notifier","version":"2.1.0","author":"team-b"}',
    "tools/validators/check_schema.py": "import yaml\n# Schema validator placeholder\nprint('Validating...')",
    "tools/linters/md_lint.sh": "#!/bin/bash\necho 'Linting markdown files...'",
}

for path, content in distractors.items():
    full_path = os.path.join(WORKSPACE, path)
    with open(full_path, "w") as f:
        f.write(content)

# The BRIEF (the business request context file — NOT a hint or README, just raw spec notes)
brief_content = """\
INTERNAL TICKET #PLT-4821
Title: Package the "csv-transformer" skill for catalog submission

Assigned to: Platform Automation Team
Priority: HIGH

Background:
The data engineering team has written a Node.js utility called csv-transformer that
converts CSV files into JSON. They want it packaged as an official catalog skill so
other teams can discover and use it via the internal automation platform.

Raw notes from the data-eng team:
  - The tool is a Node.js script
  - Binary name exposed: csv-transform
  - npm package name: @dataeng/csv-transformer
  - Author: data-eng-team
  - Version to publish: 2.3.0
  - Short description: Converts CSV files to JSON format using configurable column mappings.
  - The skill should include a usage example showing how to invoke it on a file called data.csv
  - The error handling section should document what to do if the input file is missing
  - There should be a validation helper script in the scripts/ folder

Catalog submission target slug: csv-transformer
Changelog note for this release: "Initial catalog submission of csv-transformer skill"
"""

with open(os.path.join(WORKSPACE, "PLT-4821-brief.txt"), "w") as f:
    f.write(brief_content)

# Also drop an incomplete/broken attempt at the skill that the agent should NOT just copy
broken_attempt_dir = os.path.join(WORKSPACE, "workspace-scratch", "csv-transformer-attempt")
os.makedirs(broken_attempt_dir, exist_ok=True)

broken_skill_md = """\
---
name: csv-transformer
description: CSV to JSON
author: data-eng-team
version: 2.3.0
---

# csv-transformer

Does stuff with CSV.

## Notes
- nodejs required
"""

with open(os.path.join(broken_attempt_dir, "SKILL.md"), "w") as f:
    f.write(broken_skill_md)

with open(os.path.join(broken_attempt_dir, "notes.txt"), "w") as f:
    f.write("This attempt is incomplete. Frontmatter is wrong, missing sections, wrong structure.")

print("Workspace generated successfully.")
print(f"Key input file: {WORKSPACE}/PLT-4821-brief.txt")