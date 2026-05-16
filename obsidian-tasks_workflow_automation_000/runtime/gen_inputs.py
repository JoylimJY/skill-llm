#!/usr/bin/env python3
"""
Generate the sandbox workspace for the obsidian-tasks evaluation.
Creates a realistic vault structure with distractors and the setup script,
but leaves the agent to do ALL the real configuration work.
"""

import os
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── 1. Create the obsidian-tasks skill scripts ─────────────────────────────

scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

setup_py = scripts_dir / "setup.py"
setup_py.write_text(textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"Setup script for obsidian-tasks vault initialization.\"\"\"
    import argparse
    import os
    from pathlib import Path

    def setup_vault(vault_path, folder="Tasks", columns=None):
        if columns is None:
            columns = ["Backlog", "Todo", "In Progress", "Review", "Done"]

        vault = Path(vault_path)
        vault.mkdir(parents=True, exist_ok=True)

        tasks_dir = vault / folder
        tasks_dir.mkdir(parents=True, exist_ok=True)

        # Build kanban board
        board_lines = [
            "---",
            "kanban-plugin: basic",
            "---",
            "",
        ]
        for col in columns:
            board_lines.append(f"## {col}")
            board_lines.append("")

        board_lines.append("%% kanban:settings")
        board_lines.append('```')
        board_lines.append('{"kanban-plugin":"basic"}')
        board_lines.append('```')
        board_lines.append("%%")

        board_path = tasks_dir / "Board.md"
        board_path.write_text("\\n".join(board_lines))

        # Build dataview dashboard
        col_list = ", ".join(f'"{c}"' for c in columns)
        tasks_folder = f"{folder}"

        dashboard_content = f\"\"\"# Task Dashboard

## P1 – Urgent Tasks
```dataview
TABLE status, category, due
FROM "{tasks_folder}"
WHERE priority = "P1" AND status != "done"
SORT due ASC
```

## Overdue Tasks
```dataview
TABLE priority, category
FROM "{tasks_folder}"
WHERE due AND due < date(today) AND status != "done"
SORT due ASC
```

## Recently Completed
```dataview
TABLE category
FROM "{tasks_folder}"
WHERE status = "done"
SORT file.mtime DESC
LIMIT 10
```
\"\"\"
        dashboard_path = tasks_dir / "Dashboard.md"
        dashboard_path.write_text(dashboard_content)

        print(f"[setup] Vault initialized at: {vault_path}")
        print(f"[setup] Tasks folder: {tasks_dir}")
        print(f"[setup] Board.md columns: {columns}")
        print(f"[setup] Board.md: {board_path}")
        print(f"[setup] Dashboard.md: {dashboard_path}")
        print("[setup] Install Kanban and Dataview community plugins in Obsidian.")
        return board_path, dashboard_path

    if __name__ == "__main__":
        parser = argparse.ArgumentParser(description="Setup obsidian-tasks vault")
        parser.add_argument("vault_path", help="Path to Obsidian vault root")
        parser.add_argument("--folder", default="Tasks", help="Subfolder name")
        parser.add_argument("--columns", default="Backlog,Todo,In Progress,Review,Done",
                            help="Comma-separated column names")
        args = parser.parse_args()
        cols = [c.strip() for c in args.columns.split(",")]
        setup_vault(args.vault_path, folder=args.folder, columns=cols)
"""))
setup_py.chmod(0o755)

# ─── 2. Create the target Obsidian vault root (empty, no Tasks folder yet) ──

vault_dir = WORKSPACE / "PharmaVault"
vault_dir.mkdir(parents=True, exist_ok=True)

# Obsidian config stub (distractor)
obsidian_cfg = vault_dir / ".obsidian"
obsidian_cfg.mkdir(parents=True, exist_ok=True)
(obsidian_cfg / "app.json").write_text('{"alwaysUpdateLinks": true}\n')
(obsidian_cfg / "community-plugins.json").write_text('["kanban","dataview"]\n')
(obsidian_cfg / "plugins").mkdir(exist_ok=True)

# ─── 3. Research folder – distractor reference notes ────────────────────────

research_dir = vault_dir / "Research"
research_dir.mkdir(parents=True, exist_ok=True)

(research_dir / "compound-X47-assay-results.md").write_text(textwrap.dedent("""\
    # Compound X47 Assay Results

    IC50: 3.2 nM
    Selectivity index: 42
    Cytotoxicity: low

    ## Notes
    Results from March batch look promising.
"""))

(research_dir / "toxicology-prelim-2026-01.md").write_text(textwrap.dedent("""\
    # Toxicology Preliminary Report – Jan 2026

    NOAEL: 50 mg/kg
    Species: Sprague-Dawley rat
    Duration: 28 days

    No significant adverse effects observed at therapeutic doses.
"""))

(research_dir / "competitor-landscape.md").write_text(textwrap.dedent("""\
    # Competitor Landscape Analysis

    - CompoundorA (Pharma Inc): Phase II
    - MoleculeB (BioGen): Preclinical
    - X47 analog (us): Lead optimization
"""))

(research_dir / "regulatory-pathway-notes.md").write_text(textwrap.dedent("""\
    # Regulatory Pathway Notes

    IND application target: Q3 2026
    FDA pre-IND meeting: scheduled
"""))

(research_dir / "meeting-notes-feb-2026.md").write_text(textwrap.dedent("""\
    # Team Meeting – Feb 2026

    Attendees: Alice (CSO), Bob (CMC), Carol (Regulatory)

    Action items:
    - Finalize synthesis protocol for X47
    - Submit toxicology data for review
    - Update IND timeline
"""))

# ─── 4. Additional distractor folders ────────────────────────────────────────

templates_dir = vault_dir / "Templates"
templates_dir.mkdir(exist_ok=True)
(templates_dir / "weekly-review.md").write_text("# Weekly Review Template\n\n- What went well?\n- What needs attention?\n")
(templates_dir / "experiment-log.md").write_text("# Experiment Log\n\nDate:\nExperimenter:\nProtocol:\n")

archive_dir = vault_dir / "Archive" / "2025"
archive_dir.mkdir(parents=True, exist_ok=True)
(archive_dir / "Q4-2025-summary.md").write_text("# Q4 2025 Summary\n\nAll milestones met.\n")
(archive_dir / "old-board.md").write_text("# Old Board\n\n## Done\n- [x] [[Phase1-prep]]\n")

people_dir = vault_dir / "People"
people_dir.mkdir(exist_ok=True)
(people_dir / "alice-profile.md").write_text("# Alice\n\nRole: CSO\nFocus: Lead optimization\n")
(people_dir / "bob-profile.md").write_text("# Bob\n\nRole: CMC Lead\nFocus: Synthesis scale-up\n")

# ─── 5. Write a MESSY, WRONG task note the agent must NOT use as a template ──
# (This is a distractor showing WRONG frontmatter format)

messy_dir = vault_dir / "Inbox"
messy_dir.mkdir(exist_ok=True)
(messy_dir / "rough-ideas.md").write_text(textwrap.dedent("""\
    # Rough Ideas (not formatted)

    status: in_progress   <-- WRONG format, underscores not hyphens
    priority: high        <-- WRONG, should be P1/P2/P3
    due: 07-02-2026       <-- WRONG date format

    - run more assays
    - talk to regulatory
    - check competitor IP
"""))

# ─── 6. Scenario description file (business context only, no hints) ──────────

(WORKSPACE / "project-brief.md").write_text(textwrap.dedent("""\
    # PharmaVault Project Brief

    Vault location: /workspace/PharmaVault
    Scripts location: /workspace/scripts/

    ## Pipeline Tasks to Track

    ### Task A: "Synthesize-X47-Batch2"
    - Category: research
    - Priority: P1 (urgent)
    - Created: 2026-02-10
    - Due: 2026-02-20
    - Current stage: In Progress
    - Linked reference: compound-X47-assay-results (in Research folder)

    ### Task B: "Toxicology-Report-Review"
    - Category: research
    - Priority: P2
    - Created: 2026-02-05
    - Due: 2026-02-28
    - Current stage: Review
    - Linked reference: toxicology-prelim-2026-01 (in Research folder)

    ### Task C: "IND-Application-Draft"
    - Category: revenue
    - Priority: P1 (urgent)
    - Created: 2026-01-15
    - Due: 2026-03-01
    - Current stage: Backlog
    - No linked reference yet

    ### Task D: "Competitor-IP-Landscape"
    - Category: research
    - Priority: P3
    - Created: 2026-02-01
    - No due date
    - Current stage: Todo
    - Linked reference: competitor-landscape (in Research folder)

    ## Workflow Instructions (business language)
    1. Initialize the project tracking board in the vault using a custom
       folder called "Pipeline" with stages:
       Backlog, Todo, In Progress, Review, Done
    2. Create properly formatted tracking cards for all four tasks above.
    3. "Toxicology-Report-Review" has just been approved — move it from
       Review to Done and mark it as completed (completion date: 2026-02-12).
    4. "Synthesize-X47-Batch2" has been pulled back for rework — move it
       from In Progress back to Todo.
"""))

print("Workspace generated successfully.")
print(f"Vault: {vault_dir}")
print(f"Scripts: {scripts_dir}")