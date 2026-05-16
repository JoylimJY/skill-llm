import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "projects/fintech-rebrand/assets",
    "projects/fintech-rebrand/contracts",
    "projects/old-client-xyz/notes",
    "invoices/2025-Q1",
    "invoices/2025-Q2",
    "crm",
    "inbox",
    "templates",
    "meetings",          # meetings root exists but is otherwise empty
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
(workspace / "projects" / "fintech-rebrand" / "assets" / "logo_v1.svg").write_text(
    "<svg><!-- placeholder logo --></svg>"
)
(workspace / "projects" / "fintech-rebrand" / "contracts" / "draft_contract_v2.md").write_text(
    "# Draft Contract\n\nParties: Studio Novo (you) & Paxo Financial Inc.\n\nScope TBD.\n"
)
(workspace / "projects" / "old-client-xyz" / "notes" / "discovery_raw.txt").write_text(
    "Old call notes from 2024. Budget ~$8k. Contact: Jim B.\n"
)
(workspace / "invoices" / "2025-Q1" / "INV-001.md").write_text(
    "# Invoice 001\nAmount: $3,500\nClient: Acme Corp\n"
)
(workspace / "invoices" / "2025-Q2" / "INV-004.md").write_text(
    "# Invoice 004\nAmount: $5,000\nClient: Generic Brand LLC\n"
)
(workspace / "crm" / "crm-records.md").write_text(
    "# CRM Records\n\n## Paxo Financial Inc.\n- First contact: 2025-11-10\n- Contact: Dana Yuen (Head of Product)\n- Warm intro via LinkedIn\n- Interested in full brand identity refresh\n- No prior work delivered\n"
)
(workspace / "inbox" / "inbox-triage.md").write_text(
    "# Inbox\n\n- Email from Dana Yuen re: discovery call scheduling\n- Proposal request attached\n"
)
(workspace / "templates" / "brief_template.md").write_text(
    "# Generic Brief\n\nPurpose: ...\nGoals: ...\n"
)
(workspace / "templates" / "invoice_template.md").write_text(
    "# Invoice Template\nBill To: ...\nAmount: ...\n"
)
(workspace / "projects" / "fintech-rebrand" / "README_internal.txt").write_text(
    "Internal tracking for Paxo Financial brand project.\nKickoff pending discovery call outcome.\n"
)

# ── Pre-seeded (but EMPTY/stub) meetings state files ──────────────────────
# meeting-log.md exists as stub — agent must ADD the entry
(workspace / "meetings" / "meeting-log.md").write_text(
    "# Meeting Log\n\n| Date | Meeting | Type | Key Decision | File |\n|------|---------|------|--------------|------|\n"
)

# open-actions.md exists as stub — agent must ADD rows
(workspace / "meetings" / "open-actions.md").write_text(
    "# Open Action Items\n\nLast reviewed: 2025-11-10\n\n| # | Action | Owner | Due | Meeting | Status |\n|---|--------|-------|-----|---------|--------|\n"
)

# A stale open-actions entry from a completely different old meeting (distractor)
# We inject one existing row so the agent must preserve it AND add new ones
old_row = "| 1 | Send revised invoice | You | 2025-11-15 | 2025-11-10-acme-checkin.md | Open |\n"
(workspace / "meetings" / "open-actions.md").write_text(
    "# Open Action Items\n\nLast reviewed: 2025-11-10\n\n"
    "| # | Action | Owner | Due | Meeting | Status |\n"
    "|---|--------|-------|-----|---------|--------|\n"
    + old_row
)

print("Workspace generated successfully.")
print("Directory tree:")
for p in sorted(workspace.rglob("*")):
    print(" ", p.relative_to(workspace))