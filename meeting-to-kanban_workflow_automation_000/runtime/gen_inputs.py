import os
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Skill directory structure (simulating an AgentSkills/OpenClaw layout) ──
skill_root = workspace / "skills" / "meeting-to-kanban"
scripts_dir = skill_root / "scripts"
resources_dir = skill_root / "resources"
scripts_dir.mkdir(parents=True, exist_ok=True)
resources_dir.mkdir(parents=True, exist_ok=True)

# ── board-columns.yaml  (the canonical schema the agent must use) ──
board_columns_yaml = textwrap.dedent("""\
columns:
  - id: backlog
    label: Backlog
    description: Items identified but not yet scheduled.
    wip_limit: null
  - id: next
    label: Next
    description: Prioritised items ready to be picked up in the next cycle.
    wip_limit: 5
  - id: doing
    label: Doing
    description: Items actively being worked on right now.
    wip_limit: 3
  - id: waiting
    label: Waiting
    description: Items blocked on an external dependency or approval.
    wip_limit: null
  - id: done
    label: Done
    description: Completed items – may be archived after two sprints.
    wip_limit: null

defaults:
  unresolved_owner: "unresolved"
  unresolved_date: "unresolved"
  assumption_prefix: "[ASSUMPTION]"

output:
  csv_delimiter: ","
  required_csv_columns:
    - task_id
    - title
    - column
    - owner
    - due_date
    - blockers
    - notes
  summary_max_sentences: 5
  open_questions_marker: "OPEN:"
""")
(resources_dir / "board-columns.yaml").write_text(board_columns_yaml)

# ── tasks_to_kanban.py  (the bundled helper script) ──
tasks_to_kanban_py = textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"
tasks_to_kanban.py  –  Meeting-to-Kanban helper script  (v1.1.0)

Usage
-----
python3 tasks_to_kanban.py \\
    --transcript <path>          # raw meeting notes file
    --columns-schema <path>      # board-columns.yaml
    --output-csv <path>          # kanban CSV destination
    --output-summary <path>      # manager summary (.md or .txt)
    --output-owners <path>       # owners + due-dates table (.csv or .md)
    --output-questions <path>    # open questions list (.txt or .md)
    [--project-name <str>]       # optional project label
    [--time-horizon <str>]       # e.g. "2 weeks", "Q3 2025"

The script reads the YAML schema for valid column names and the
defaults/unresolved markers.  It then does a rule-based parse of the
transcript, writing four output artefacts that together satisfy the
output contract defined in SKILL.md.

Exit codes:  0 = success,  1 = usage error,  2 = runtime error.
\"\"\"

import argparse
import csv
import re
import sys
import textwrap
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required.  Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_schema(schema_path: str) -> dict:
    with open(schema_path) as fh:
        return yaml.safe_load(fh)


def valid_column_labels(schema: dict) -> list[str]:
    return [c["label"] for c in schema["columns"]]


def unresolved_owner(schema: dict) -> str:
    return schema.get("defaults", {}).get("unresolved_owner", "unresolved")


def unresolved_date(schema: dict) -> str:
    return schema.get("defaults", {}).get("unresolved_date", "unresolved")


def assumption_prefix(schema: dict) -> str:
    return schema.get("defaults", {}).get("assumption_prefix", "[ASSUMPTION]")


def open_questions_marker(schema: dict) -> str:
    return schema.get("output", {}).get("open_questions_marker", "OPEN:")


def required_csv_columns(schema: dict) -> list[str]:
    return schema["output"]["required_csv_columns"]


# ─────────────────────────────────────────────────────────────────────────────
# Parsing  (rule-based; intentionally heuristic so the transcript format matters)
# ─────────────────────────────────────────────────────────────────────────────

# Patterns that signal an action item line
_ACTION_RE = re.compile(
    r"(?:action|todo|task|follow[- ]?up|ai|→|->|•|-\\s)\\s*[:\\-]?\\s*(.+)",
    re.IGNORECASE,
)
_OWNER_RE   = re.compile(r"\\(([A-Z][a-z]+(?:\\s[A-Z][a-z]+)?)\\)|owner[:\\s]+([A-Za-z ]+?)(?:,|;|\\.|$)", re.IGNORECASE)
_DATE_RE    = re.compile(
    r"\\bby\\s+(\\d{4}-\\d{2}-\\d{2}|\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}|"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\\s+\\d{1,2}(?:st|nd|rd|th)?(?:,?\\s+\\d{4})?)\\b",
    re.IGNORECASE,
)
_BLOCKER_RE = re.compile(r"block(?:ed|er)[:\\s]+([^.\\n]+)", re.IGNORECASE)
_DONE_RE    = re.compile(r"\\b(?:completed?|done|finished?|closed?)\\b", re.IGNORECASE)
_WAIT_RE    = re.compile(r"\\b(?:waiting|pending|blocked|on hold)\\b", re.IGNORECASE)
_DOING_RE   = re.compile(r"\\b(?:in[- ]?progress|ongoing|currently|underway|wip)\\b", re.IGNORECASE)
_NEXT_RE    = re.compile(r"\\b(?:next sprint|next cycle|next week|soon|upcoming|prioriti[sz]ed)\\b", re.IGNORECASE)
_RISK_RE    = re.compile(r"\\b(?:risk|concern|issue|problem|blocker|depend)\\b", re.IGNORECASE)
_QUESTION_RE = re.compile(r"^[^.!]*\\?\\s*$|\\b(?:unclear|unknown|TBD|TBC|who will|should we|need to decide|open question)\\b", re.IGNORECASE)
_DECISION_RE = re.compile(r"\\b(?:decided?|agreed?|confirmed?|resolved?|approved?)\\b", re.IGNORECASE)


def classify_column(line: str, valid_labels: list[str]) -> str:
    \"\"\"Map a line to the most appropriate column label.\"\"\"
    if _DONE_RE.search(line):
        return "Done"
    if _WAIT_RE.search(line):
        return "Waiting"
    if _DOING_RE.search(line):
        return "Doing"
    if _NEXT_RE.search(line):
        return "Next"
    return "Backlog"


def extract_owner(line: str, fallback: str) -> str:
    m = _OWNER_RE.search(line)
    if m:
        return (m.group(1) or m.group(2) or fallback).strip()
    return fallback


def extract_date(line: str, fallback: str) -> str:
    m = _DATE_RE.search(line)
    if m:
        return m.group(1).strip()
    return fallback


def extract_blocker(line: str) -> str:
    m = _BLOCKER_RE.search(line)
    if m:
        return m.group(1).strip()
    return ""


def parse_transcript(text: str, schema: dict) -> tuple[list[dict], list[str], list[str]]:
    \"\"\"
    Returns (tasks, decisions, open_questions).
    \"\"\"
    valid_labels = valid_column_labels(schema)
    uo = unresolved_owner(schema)
    ud = unresolved_date(schema)
    oq_marker = open_questions_marker(schema)
    ap = assumption_prefix(schema)

    tasks: list[dict] = []
    decisions: list[str] = []
    open_questions: list[str] = []
    task_counter = 0

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Decisions
        if _DECISION_RE.search(line):
            decisions.append(line)

        # Open questions
        if _QUESTION_RE.search(line):
            open_questions.append(f"{oq_marker} {line}")

        # Action items
        m = _ACTION_RE.search(line)
        if m:
            task_counter += 1
            title = m.group(1).strip().rstrip(".")
            owner = extract_owner(line, uo)
            due   = extract_date(line, ud)
            col   = classify_column(line, valid_labels)
            blk   = extract_blocker(line)

            notes = ""
            if owner == uo:
                notes += f"{ap} Owner not specified in transcript. "
            if due == ud:
                notes += f"{ap} Due date not specified in transcript."
            notes = notes.strip()

            tasks.append({
                "task_id":  f"T{task_counter:03d}",
                "title":    title,
                "column":   col,
                "owner":    owner,
                "due_date": due,
                "blockers": blk,
                "notes":    notes,
            })

    return tasks, decisions, open_questions


# ─────────────────────────────────────────────────────────────────────────────
# Writers
# ─────────────────────────────────────────────────────────────────────────────

def write_csv(tasks: list[dict], req_cols: list[str], dest: str) -> None:
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=req_cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(tasks)


def write_summary(
    tasks: list[dict],
    decisions: list[str],
    project_name: str,
    time_horizon: str,
    max_sentences: int,
    dest: str,
) -> None:
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    doing  = [t for t in tasks if t["column"] == "Doing"]
    waiting = [t for t in tasks if t["column"] == "Waiting"]
    unresolved_owners = [t for t in tasks if t["owner"] == "unresolved"]
    unresolved_dates  = [t for t in tasks if t["due_date"] == "unresolved"]

    lines = [
        f"# Manager Summary – {project_name}",
        f"**Time horizon:** {time_horizon}",
        "",
        f"A total of **{len(tasks)} action items** were extracted from the meeting transcript.",
        f"{len(doing)} item(s) are currently **in progress**; "
        f"{len(waiting)} item(s) are **blocked or waiting**.",
    ]
    if decisions:
        lines.append(f"Key decisions recorded: {len(decisions)}.")
    if unresolved_owners:
        lines.append(
            f"⚠️  {len(unresolved_owners)} task(s) have **no assigned owner** and are marked `unresolved`."
        )
    if unresolved_dates:
        lines.append(
            f"⚠️  {len(unresolved_dates)} task(s) have **no due date** and are marked `unresolved`."
        )
    # Trim to max_sentences (rough)
    summary_body = [l for l in lines if l and not l.startswith("#") and not l.startswith("**")]
    trimmed = summary_body[:max_sentences]
    with open(dest, "w") as fh:
        fh.write("\\n".join(lines[:3]) + "\\n\\n")
        fh.write("\\n".join(trimmed) + "\\n")


def write_owners_table(tasks: list[dict], dest: str) -> None:
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Owners & Due Dates\\n"]
    lines.append("| task_id | title | owner | due_date |")
    lines.append("|---------|-------|-------|----------|")
    for t in tasks:
        lines.append(f"| {t['task_id']} | {t['title'][:60]} | {t['owner']} | {t['due_date']} |")
    with open(dest, "w") as fh:
        fh.write("\\n".join(lines) + "\\n")


def write_open_questions(questions: list[str], dest: str) -> None:
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w") as fh:
        if questions:
            fh.write("\\n".join(questions) + "\\n")
        else:
            fh.write("No open questions identified.\\n")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Convert meeting transcript to Kanban artefacts.")
    ap.add_argument("--transcript",        required=True)
    ap.add_argument("--columns-schema",    required=True)
    ap.add_argument("--output-csv",        required=True)
    ap.add_argument("--output-summary",    required=True)
    ap.add_argument("--output-owners",     required=True)
    ap.add_argument("--output-questions",  required=True)
    ap.add_argument("--project-name",      default="Unnamed Project")
    ap.add_argument("--time-horizon",      default="unspecified")
    args = ap.parse_args()

    try:
        schema = load_schema(args.columns_schema)
    except Exception as exc:
        print(f"ERROR loading schema: {exc}", file=sys.stderr)
        return 2

    try:
        transcript_text = Path(args.transcript).read_text()
    except Exception as exc:
        print(f"ERROR reading transcript: {exc}", file=sys.stderr)
        return 2

    tasks, decisions, open_questions = parse_transcript(transcript_text, schema)

    if not tasks:
        print("WARNING: No action items extracted from transcript.", file=sys.stderr)

    req_cols = required_csv_columns(schema)
    write_csv(tasks, req_cols, args.output_csv)
    write_summary(
        tasks, decisions,
        project_name=args.project_name,
        time_horizon=args.time_horizon,
        max_sentences=schema["output"].get("summary_max_sentences", 5),
        dest=args.output_summary,
    )
    write_owners_table(tasks, args.output_owners)
    write_open_questions(open_questions, args.output_questions)

    print(f"✓ Kanban CSV       → {args.output_csv}")
    print(f"✓ Manager summary  → {args.output_summary}")
    print(f"✓ Owners table     → {args.output_owners}")
    print(f"✓ Open questions   → {args.output_questions}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
""")
(scripts_dir / "tasks_to_kanban.py").write_text(tasks_to_kanban_py)

# ── Messy meeting transcript (the raw input) ──
meetings_dir = workspace / "projects" / "nucleotrack" / "meetings"
meetings_dir.mkdir(parents=True, exist_ok=True)

transcript = textwrap.dedent("""\
    NucleoTrack Clinical Data Platform – Sprint Planning & Risk Review
    Date: 2025-06-10  |  Facilitator: Dr. Priya Mehta  |  Scribe: Leo Fontaine

    Attendees: Dr. Priya Mehta (PM), Chen Wei (Backend Lead), Aisha Okonkwo (QA),
               Fatima Reza (Regulatory), Marcus Aldridge (DevOps), Soo-Jin Park (Data Science)

    --- AGENDA ---

    1. Review of last sprint
    2. Blockers & risks
    3. Upcoming deliverables for FDA pre-submission package
    4. Infrastructure readiness
    5. Open items / parking lot

    =============================================================
    MINUTES
    =============================================================

    [09:02] Dr. Priya Mehta opened the meeting. Confirmed that the de-identification
    pipeline passed internal audit (COMPLETED last Thursday). This is now Done.

    [09:08] Chen Wei: Action: migrate the audit-log service to Postgres 15 by 2025-06-20.
    Currently in progress (WIP). Blocker: waiting on DBA approval from IT.

    [09:15] Aisha Okonkwo: Todo – write regression test suite for the new HL7 parser.
    No deadline set yet. Owner: Aisha Okonkwo.

    [09:19] Fatima Reza raised a risk: the FDA guidance document for eCTD 4.0 is still
    unclear on section 5.3 tagging requirements. We need to decide how to handle this.
    Open question: Do we need outside regulatory counsel before submitting? 
    Action: Fatima Reza to draft a one-page gap analysis for eCTD compliance by June 30 2025.

    [09:27] Marcus Aldridge: Follow-up – harden container image (pin all base image
    digests). Prioritised for next sprint. Owner: Marcus Aldridge. Due: 2025-06-17.

    [09:33] Soo-Jin Park mentioned the anomaly-detection model retraining is underway.
    Action → retrain anomaly model on the Q2 dataset. Owner: Soo-Jin Park. In-progress.
    Blocker: labelled dataset still being reviewed by Aisha.

    [09:40] Dr. Priya Mehta: Action – schedule architecture review with external consultant.
    No owner assigned yet. No date confirmed. Should we bring in Dr. Haruto Yamada?

    [09:47] Chen Wei: Todo – add distributed tracing (OpenTelemetry) to API gateway.
    Next sprint. No owner beyond Chen Wei implied. Due: 2025-06-24.

    [09:52] Aisha Okonkwo: Decided that test environment will be promoted to staging by
    end of this week. Owner: Aisha Okonkwo. Done criteria: smoke tests green.

    [09:58] PARKING LOT / OPEN ITEMS:
    - Who will own the GDPR data-residency review? TBD.
    - Should we include synthetic data generation in scope for Q3? Unclear.
    - Dependency on third-party genomics API – contract renewal date unknown.

    [10:05] Meeting adjourned.
""")
(meetings_dir / "sprint_planning_2025-06-10.txt").write_text(transcript)

# ── Distractor files ──
(workspace / "projects" / "nucleotrack" / "README_INTERNAL.md").write_text(
    "# NucleoTrack Internal Docs\nThis folder contains project artefacts.\n"
)
(workspace / "projects" / "nucleotrack" / "budget_q2.csv").write_text(
    "category,amount\nCloud,12400\nLicenses,3200\nConsulting,8000\n"
)
(workspace / "projects" / "nucleotrack" / "risk_register.xlsx.placeholder").write_text(
    "placeholder – binary file not included\n"
)
(workspace / "projects" / "nucleotrack" / "team_contacts.txt").write_text(
    "Chen Wei: cwei@nucleotrack.io\nAisha Okonkwo: aokonkwo@nucleotrack.io\nFatima Reza: freza@nucleotrack.io\n"
)

design_dir = workspace / "projects" / "nucleotrack" / "design"
design_dir.mkdir(parents=True, exist_ok=True)
(design_dir / "architecture_v2.drawio.placeholder").write_text("placeholder\n")
(design_dir / "data_flow_diagram.txt").write_text(
    "Ingest → De-ID → Store → Query → Export\n"
)
(design_dir / "api_spec_draft.yaml").write_text(
    "openapi: 3.0.0\ninfo:\n  title: NucleoTrack API\n  version: 0.9.0\n"
)

infra_dir = workspace / "projects" / "nucleotrack" / "infra"
infra_dir.mkdir(parents=True, exist_ok=True)
(infra_dir / "terraform_plan.txt").write_text(
    "Plan: 12 to add, 0 to change, 0 to destroy.\n"
)
(infra_dir / "container_registry.txt").write_text(
    "registry: ghcr.io/nucleotrack\nimages: api, worker, scheduler\n"
)
(infra_dir / "k8s_namespace_config.yaml").write_text(
    "apiVersion: v1\nkind: Namespace\nmetadata:\n  name: nucleotrack-prod\n"
)

(workspace / "notes_scratch.txt").write_text(
    "random scratch notes – not meeting minutes\nlunch order: pizza\n"
)
(workspace / "old_kanban_attempt.csv").write_text(
    "task,status\nfix bug,todo\nwrite docs,done\n"
    "# THIS FILE IS STALE – DO NOT USE\n"
)

print("Workspace generated successfully.")
print(f"Skill root: {skill_root}")
print(f"Transcript: {meetings_dir / 'sprint_planning_2025-06-10.txt'}")