import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Skills directory structure (mimics the real gws skill layout) ---
skills_root = workspace / "skills"

# gws-shared skill (prerequisite)
gws_shared_dir = skills_root / "gws-shared"
gws_shared_dir.mkdir(parents=True, exist_ok=True)

shared_skill_content = """---
name: gws-shared
description: "Shared auth, global flags, and security rules for all gws commands."
metadata:
  version: 0.22.5
---

# gws-shared

Global flags and authentication rules for all `gws` commands.

## Authentication

All `gws` commands require an authenticated session. Authentication is provided
via a credentials file located at `~/.gws/credentials.json`.

You must ensure this file exists before running any `gws` command.

## Global Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--account` | ✓ | — | The Google account email to use (must match credentials file) |
| `--json` | — | false | Output results as JSON |

## Security Rules

- Never share your credentials file.
- All write commands require explicit user confirmation before execution.
- The `--account` flag must be passed on every command invocation.

## Credentials File Format

The credentials file at `~/.gws/credentials.json` must contain:

```json
{
  "account": "user@example.com",
  "token": "mock-token-value"
}
```

## Example Auth Usage

```bash
gws drive +upload ./file.pdf --account user@example.com
```
"""

(gws_shared_dir / "SKILL.md").write_text(shared_skill_content)

# gws-drive-upload skill
gws_drive_upload_dir = skills_root / "gws-drive-upload"
gws_drive_upload_dir.mkdir(parents=True, exist_ok=True)

drive_upload_skill_content = """---
name: gws-drive-upload
description: "Google Drive: Upload a file with automatic metadata."
metadata:
  version: 0.22.5
  openclaw:
    category: "productivity"
    requires:
      bins:
        - gws
    cliHelp: "gws drive +upload --help"
---

# drive +upload

> **PREREQUISITE:** Read `../gws-shared/SKILL.md` for auth, global flags, and security rules. If missing, run `gws generate-skills` to create it.

Upload a file with automatic metadata

## Usage

```bash
gws drive +upload <file>
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `<file>` | ✓ | — | Path to file to upload |
| `--parent` | — | — | Parent folder ID |
| `--name` | — | — | Target filename (defaults to source filename) |

## Examples

```bash
gws drive +upload ./report.pdf
gws drive +upload ./report.pdf --parent FOLDER_ID
gws drive +upload ./data.csv --name 'Sales Data.csv'
```

## Tips

- MIME type is detected automatically.
- Filename is inferred from the local path unless --name is given.

> [!CAUTION]
> This is a **write** command — confirm with the user before executing.

## See Also

- [gws-shared](../gws-shared/SKILL.md) — Global flags and auth
- [gws-drive](../gws-drive/SKILL.md) — All manage files, folders, and shared drives commands
"""

(gws_drive_upload_dir / "SKILL.md").write_text(drive_upload_skill_content)

# --- Distractor files: a realistic finance department file tree ---
finance_dirs = [
    workspace / "finance" / "q1_2024" / "raw",
    workspace / "finance" / "q1_2024" / "processed",
    workspace / "finance" / "q2_2024" / "raw",
    workspace / "finance" / "q2_2024" / "processed",
    workspace / "finance" / "q3_2024" / "drafts",
    workspace / "finance" / "q3_2024" / "approved",
    workspace / "finance" / "archive" / "2023",
    workspace / "finance" / "templates",
    workspace / "ops" / "infrastructure",
    workspace / "ops" / "deployments",
    workspace / "hr" / "onboarding",
]

for d in finance_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = [
    (workspace / "finance" / "q1_2024" / "raw" / "transactions_jan.csv",
     "date,amount,category\n2024-01-15,5200.00,OPEX\n2024-01-22,18000.00,CAPEX\n"),
    (workspace / "finance" / "q1_2024" / "raw" / "transactions_feb.csv",
     "date,amount,category\n2024-02-10,3100.00,OPEX\n"),
    (workspace / "finance" / "q1_2024" / "processed" / "q1_summary.xlsx.placeholder",
     "placeholder for excel file"),
    (workspace / "finance" / "q2_2024" / "raw" / "transactions_apr.csv",
     "date,amount,category\n2024-04-01,9900.00,REVENUE\n"),
    (workspace / "finance" / "q2_2024" / "processed" / "q2_report_DRAFT.pdf.placeholder",
     "Draft Q2 report placeholder"),
    (workspace / "finance" / "q3_2024" / "drafts" / "q3_earnings_v1.pptx.placeholder",
     "Version 1 draft"),
    (workspace / "finance" / "q3_2024" / "drafts" / "q3_earnings_v2.pptx.placeholder",
     "Version 2 draft"),
    (workspace / "finance" / "q3_2024" / "approved" / "q3_earnings_FINAL.pptx",
     "FINAL Q3 2024 Earnings Presentation - Approved by CFO\nRevenue: $142M\nEBITDA: $31M\n"),
    (workspace / "finance" / "archive" / "2023" / "q4_2023_earnings.pdf.placeholder",
     "Archived Q4 2023 earnings"),
    (workspace / "finance" / "templates" / "quarterly_template.pptx.placeholder",
     "Standard quarterly template"),
    (workspace / "ops" / "infrastructure" / "network_topology.yaml",
     "nodes:\n  - id: web-01\n  - id: db-01\n"),
    (workspace / "ops" / "deployments" / "k8s_config.yaml",
     "apiVersion: v1\nkind: Pod\n"),
    (workspace / "hr" / "onboarding" / "new_hire_checklist.txt",
     "1. Complete I-9\n2. Setup workstation\n3. Meet your manager\n"),
]

for fpath, content in distractor_files:
    fpath.write_text(content)

# --- The ACTUAL target file the agent needs to upload ---
# This is the approved Q3 earnings presentation that should be uploaded
target_file = workspace / "finance" / "q3_2024" / "approved" / "q3_earnings_FINAL.pptx"
# Already created above

# --- Config file with upload job details (deliberately structured like a work ticket) ---
upload_ticket = {
    "ticket_id": "FIN-2024-Q3-ARCH-007",
    "requested_by": "Sarah Chen, CFO",
    "description": "Archive the approved Q3 2024 earnings presentation to the Finance Archive folder on shared drive.",
    "source_file": "finance/q3_2024/approved/q3_earnings_FINAL.pptx",
    "destination": {
        "drive_folder_id": "1XkZpQ9mRtYvN3wBcDfGhJ2sLpOuEa4K",
        "archive_filename": "FY2024_Q3_Earnings_Presentation_ARCHIVE.pptx"
    },
    "account": "finance-bot@acmecorp.com",
    "status": "PENDING"
}

(workspace / "finance" / "upload_ticket.json").write_text(
    json.dumps(upload_ticket, indent=2)
)

# --- Credentials file (required by gws-shared auth) ---
gws_config_dir = Path.home() / ".gws"
gws_config_dir.mkdir(exist_ok=True)
credentials = {
    "account": "finance-bot@acmecorp.com",
    "token": "mock-token-abc123xyz"
}
(gws_config_dir / "credentials.json").write_text(json.dumps(credentials, indent=2))

print("Workspace generated successfully.")
print(f"Target file: {target_file}")
print(f"Upload ticket: {workspace / 'finance' / 'upload_ticket.json'}")