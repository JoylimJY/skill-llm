#!/usr/bin/env python3
"""
Generate the sandbox workspace for the obsidian-ontology-sync evaluation.
Creates a realistic Obsidian vault with messy notes, distractor files,
and the skill scripts (sync.py, etc.) that the agent must configure and invoke.
"""

import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────
def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content))


# ─────────────────────────────────────────────
# 1.  Obsidian Vault
# ─────────────────────────────────────────────
VAULT = WORKSPACE / "life" / "pkm"

# --- Contacts ---
write(VAULT / "references" / "contacts" / "Alice Johnson.md", """\
    # Alice Johnson

    **Email:** alice@acmecorp.com
    **Company:** Acme Corp
    **Phone:** +1-555-0101
    **Met At:** Tech Conference 2026
    **Projects:** [[Project Alpha]]

    ## Notes
    Great developer, responsive communication. Introduced us to Bob.
""")

write(VAULT / "references" / "contacts" / "Bob Martinez.md", """\
    # Bob Martinez

    **Company:** TechHub
    **Met At:** Startup Summit 2025
    **Projects:** [[Project Beta]], [[Project Gamma]]

    ## Notes
    Bob is the lead architect at TechHub. No email on file yet - need to follow up.
    Met through Alice at TechHub offices.
""")

write(VAULT / "references" / "contacts" / "Carol Lee.md", """\
    # Carol Lee

    **Email:** carol.lee@innovate.io
    **Phone:** +1-555-0303
    **Company:** Innovate IO
    **Met At:** DevDays 2025
    **Projects:** [[Project Alpha]], [[Project Delta]]

    ## Notes
    Carol is a senior PM. Very organized. Referred by Carol's manager.
""")

write(VAULT / "references" / "contacts" / "David Kim.md", """\
    # David Kim

    **Email:** dkim@nexuspartners.com
    **Company:** Nexus Partners
    **Met At:** Tech Conference 2026

    ## Notes
    Investor contact. Interested in Project Gamma. No current project assignment.
""")

# --- Clients ---
write(VAULT / "references" / "clients" / "Acme Corp.md", """\
    # Acme Corp

    **Contract Value:** 520000
    **Primary Contact:** [[Alice Johnson]]
    **Projects:** [[Project Alpha]]
    **Status:** active

    ## Notes
    Long-standing client. Annual renewal due Q3 2026.
""")

write(VAULT / "references" / "clients" / "TechHub.md", """\
    # TechHub

    **Contract Value:** 380000
    **Primary Contact:** [[Bob Martinez]]
    **Projects:** [[Project Beta]], [[Project Gamma]]
    **Status:** warm_lead

    ## Notes
    Potential expansion client. Negotiations ongoing.
""")

# --- Team ---
write(VAULT / "references" / "team" / "Priya Sharma.md", """\
    # Priya Sharma

    **Email:** priya@ourconsulting.com
    **Role:** Senior Consultant
    **Reports To:** [[Marcus Wells]]
    **Assigned Projects:** [[Project Alpha]], [[Project Beta]]
    **Response Pattern:** proactive

    ## Notes
    Top performer. Handles most of Acme Corp deliverables.
""")

write(VAULT / "references" / "team" / "Marcus Wells.md", """\
    # Marcus Wells

    **Email:** marcus@ourconsulting.com
    **Role:** Principal Consultant
    **Assigned Projects:** [[Project Alpha]], [[Project Gamma]], [[Project Delta]]
    **Response Pattern:** proactive

    ## Notes
    Leads engagement with TechHub. Reports to CEO.
""")

write(VAULT / "references" / "team" / "Jin Park.md", """\
    # Jin Park

    **Role:** Junior Consultant
    **Reports To:** [[Priya Sharma]]
    **Assigned Projects:** [[Project Beta]]
    **Response Pattern:** reactive

    ## Notes
    Recently onboarded. Missing email - HR to update records.
    Needs closer supervision during ramp-up period.
""")

# --- Projects ---
write(VAULT / "projects" / "Project Alpha.md", """\
    # Project Alpha

    **Client:** [[Acme Corp]]
    **Value:** 520000
    **Status:** active
    **Deadline:** 2026-09-30
    **Team:** [[Priya Sharma]], [[Marcus Wells]]

    ## Description
    Core platform modernisation for Acme Corp. Phase 2 started March 2026.
""")

write(VAULT / "projects" / "Project Beta.md", """\
    # Project Beta

    **Client:** [[TechHub]]
    **Value:** 200000
    **Status:** active
    **Team:** [[Priya Sharma]], [[Jin Park]]

    ## Description
    API integration project. Deadline not yet confirmed by client.
""")

# Note: Project Gamma and Project Delta are referenced but have NO project files → broken links

# --- Daily Status ---
write(VAULT / "daily-status" / "2026-03-10" / "morning-standup.md", """\
    # Morning Standup - 2026-03-10

    ## Updates
    - Priya: Project Alpha on track. Client review tomorrow.
    - Jin: Project Beta blocked on TechHub API credentials.
    - Marcus: Waiting for Nexus Partners (David Kim) intro call.

    ## Blockers
    - Jin blocked on TechHub API access
    - Project Gamma kickoff delayed (no team assigned yet)

    ## Response Times
    - Alice Johnson: responded within 2h
    - Bob Martinez: no response (3rd attempt)
""")

write(VAULT / "daily-status" / "2026-03-11" / "morning-standup.md", """\
    # Morning Standup - 2026-03-11

    ## Updates
    - Priya: Delivered Project Alpha milestone doc.
    - Jin: Still blocked, escalated to Marcus.

    ## Blockers
    - TechHub API credentials still pending

    ## Response Times
    - Carol Lee: responded same day
    - Bob Martinez: still no response (4th attempt)
""")

# ─────────────────────────────────────────────
# 2. Distractor Files  (noise to test awareness)
# ─────────────────────────────────────────────

# Old backup config the agent must NOT use
write(VAULT / "ontology-sync" / "config.yaml.bak", """\
    # OLD CONFIG - DO NOT USE
    obsidian:
      vault_path: /old/path/pkm
    ontology:
      storage_path: /tmp/ontology_old
""")

# Random orphan notes
write(VAULT / "inbox" / "random-idea.md", """\
    # Random Idea
    Need to set up knowledge graph tooling. Look into ontology extraction.
""")

write(VAULT / "inbox" / "meeting-notes-2026-01.md", """\
    # Meeting Notes Jan 2026
    Discussed quarterly goals. No specific project assignments yet.
""")

write(VAULT / "references" / "books" / "Thinking Fast and Slow.md", """\
    # Thinking Fast and Slow
    **Author:** Daniel Kahneman
    ## Key Takeaways
    - System 1 vs System 2 thinking
""")

write(VAULT / "templates" / "contact-template.md", """\
    # {{Name}}

    **Email:**
    **Company:**
    **Met At:**
    **Projects:**

    ## Notes
""")

write(VAULT / "templates" / "project-template.md", """\
    # {{Project Name}}

    **Client:**
    **Value:**
    **Status:**
    **Deadline:**
    **Team:**

    ## Description
""")

# Partial/broken old ontology data (agent should not be confused by this)
write(VAULT / "memory" / "ontology" / ".gitkeep", "")

old_junk = VAULT / "memory" / "ontology" / "old-graph-backup.jsonl"
old_junk.write_text(
    json.dumps({"entity": {"id": "person_old", "type": "Person", "properties": {"name": "Old Entry"}}, "version": "0.0.1"}) + "\n"
)

# ─────────────────────────────────────────────
# 3. Skill Scripts  (the mock implementation)
# ─────────────────────────────────────────────
SCRIPTS = WORKSPACE / "skills" / "obsidian-ontology-sync" / "scripts"
SCRIPTS.mkdir(parents=True, exist_ok=True)

# ── sync.py ──────────────────────────────────
sync_py = r'''#!/usr/bin/env python3
"""
Mock implementation of obsidian-ontology-sync sync.py
Parses Obsidian markdown vault → writes JSONL ontology → generates feedback.
"""
import sys, re, json, argparse, logging
from pathlib import Path
from datetime import date, datetime

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed", file=sys.stderr)
    sys.exit(1)

LOG = logging.getLogger("sync")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# ── Config loading ───────────────────────────────────────────────────────────
CONFIG_SEARCH_PATHS = [
    "/root/life/pkm/ontology-sync/config.yaml",
    str(Path(__file__).parent.parent.parent.parent / "life/pkm/ontology-sync/config.yaml"),
]

def load_config(config_path=None):
    candidates = ([config_path] if config_path else []) + CONFIG_SEARCH_PATHS
    for p in candidates:
        if p and Path(p).exists():
            with open(p) as f:
                cfg = yaml.safe_load(f)
            LOG.info(f"Loaded config from {p}")
            return cfg
    print("ERROR: config.yaml not found. Expected at /root/life/pkm/ontology-sync/config.yaml", file=sys.stderr)
    sys.exit(1)

# ── Markdown parsers ─────────────────────────────────────────────────────────
_PROP = re.compile(r"^\*\*([^*]+)\*\*:\s*(.+)", re.MULTILINE)
_WIKI = re.compile(r"\[\[([^\]]+)\]\]")

def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

def parse_properties(text):
    return {m.group(1).strip(): m.group(2).strip() for m in _PROP.finditer(text)}

def parse_wiki_links(value):
    return _WIKI.findall(value)

def extract_notes_section(text):
    m = re.search(r"^## Notes\s*(.+?)(?=^##|\Z)", text, re.MULTILINE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""

# ── Entity builders ──────────────────────────────────────────────────────────
def build_person_entity(name, props, notes, role=None):
    eid = "person_" + slug(name)
    p = {"name": name}
    if "Email" in props:
        p["email"] = props["Email"]
    if "Phone" in props:
        p["phone"] = props["Phone"]
    if notes:
        p["notes"] = notes
    if role:
        p["role"] = role
    if "Response Pattern" in props:
        p["response_pattern"] = props["Response Pattern"]
    if "Status" in props:
        p["status"] = props["Status"]
    return {"id": eid, "type": "Person", "properties": p}

def build_org_entity(name, props, notes):
    eid = "org_" + slug(name)
    p = {"name": name}
    if "Contract Value" in props:
        try:
            p["contract_value"] = int(re.sub(r"[^\d]", "", props["Contract Value"]))
        except Exception:
            pass
    if "Status" in props:
        p["status"] = props["Status"]
    if notes:
        p["notes"] = notes
    return {"id": eid, "type": "Organization", "properties": p}

def build_project_entity(name, props, notes):
    eid = "project_" + slug(name)
    p = {"name": name}
    if "Status" in props:
        p["status"] = props["Status"]
    if "Value" in props:
        try:
            p["value"] = int(re.sub(r"[^\d]", "", props["Value"]))
        except Exception:
            pass
    if "Deadline" in props:
        p["deadline"] = props["Deadline"]
    if notes:
        p["notes"] = notes
    return {"id": eid, "type": "Project", "properties": p}

def build_event_entity(name):
    eid = "event_" + slug(name)
    return {"id": eid, "type": "Event", "properties": {"name": name}}

# ── Relation builder ─────────────────────────────────────────────────────────
def rel(frm, r, to):
    return {"from": frm, "rel": r, "to": to}

# ── Phase 1: Extract ─────────────────────────────────────────────────────────
def cmd_extract(cfg, dry_run=False, verbose=False):
    vault = Path(cfg["obsidian"]["vault_path"])
    storage = Path(cfg["ontology"]["storage_path"])
    sources = cfg["obsidian"].get("sources", {})
    
    records = []  # list of {"entity": {...}, "relations": [...]}
    seen_entities = set()
    seen_events = set()

    def add_event(name):
        eid = "event_" + slug(name)
        if eid not in seen_events:
            seen_events.add(eid)
            records.append({"entity": build_event_entity(name), "relations": []})
        return eid

    # ── contacts ────────────────────────────────────────────────────────────
    contacts_cfg = sources.get("contacts", {})
    contacts_path = vault / contacts_cfg.get("path", "references/contacts")
    if contacts_path.exists():
        for md in contacts_path.glob("*.md"):
            text = md.read_text()
            name = md.stem
            props = parse_properties(text)
            notes = extract_notes_section(text)
            entity = build_person_entity(name, props, notes)
            eid = entity["id"]
            seen_entities.add(eid)
            rels = []
            # works_at
            if "Company" in props:
                org_eid = "org_" + slug(props["Company"])
                rels.append(rel(eid, "works_at", org_eid))
            # met_at
            if "Met At" in props:
                ev_eid = add_event(props["Met At"])
                rels.append(rel(eid, "met_at", ev_eid))
            # assigned_to projects
            if "Projects" in props:
                for proj in parse_wiki_links(props["Projects"]):
                    rels.append(rel(eid, "assigned_to", "project_" + slug(proj)))
            records.append({"entity": entity, "relations": rels})

    # ── clients ──────────────────────────────────────────────────────────────
    clients_cfg = sources.get("clients", {})
    clients_path = vault / clients_cfg.get("path", "references/clients")
    if clients_path.exists():
        for md in clients_path.glob("*.md"):
            text = md.read_text()
            name = md.stem
            props = parse_properties(text)
            notes = extract_notes_section(text)
            entity = build_org_entity(name, props, notes)
            eid = entity["id"]
            rels = []
            # primary_contact
            if "Primary Contact" in props:
                links = parse_wiki_links(props["Primary Contact"])
                for person in links:
                    rels.append(rel(eid, "has_primary_contact", "person_" + slug(person)))
            # projects
            if "Projects" in props:
                for proj in parse_wiki_links(props["Projects"]):
                    proj_eid = "project_" + slug(proj)
                    rels.append(rel(eid, "has_project", proj_eid))
                    # reverse: project for_client
                    records.append({"entity": None, "relations": [rel(proj_eid, "for_client", eid)]})
            records.append({"entity": entity, "relations": rels})

    # ── team ─────────────────────────────────────────────────────────────────
    team_cfg = sources.get("team", {})
    team_path = vault / team_cfg.get("path", "references/team")
    if team_path.exists():
        for md in team_path.glob("*.md"):
            text = md.read_text()
            name = md.stem
            props = parse_properties(text)
            notes = extract_notes_section(text)
            entity = build_person_entity(name, props, notes, role="team_member")
            eid = entity["id"]
            seen_entities.add(eid)
            rels = []
            # reports_to
            if "Reports To" in props:
                links = parse_wiki_links(props["Reports To"])
                for mgr in links:
                    rels.append(rel(eid, "reports_to", "person_" + slug(mgr)))
            # assigned_to
            if "Assigned Projects" in props:
                for proj in parse_wiki_links(props["Assigned Projects"]):
                    rels.append(rel(eid, "assigned_to", "project_" + slug(proj)))
            records.append({"entity": entity, "relations": rels})

    # ── projects ─────────────────────────────────────────────────────────────
    projects_path = vault / "projects"
    if projects_path.exists():
        for md in projects_path.glob("*.md"):
            text = md.read_text()
            name = md.stem
            props = parse_properties(text)
            notes = extract_notes_section(text)
            entity = build_project_entity(name, props, notes)
            eid = entity["id"]
            rels = []
            if "Client" in props:
                links = parse_wiki_links(props["Client"])
                for c in links:
                    rels.append(rel(eid, "for_client", "org_" + slug(c)))
            if "Team" in props:
                for person in parse_wiki_links(props["Team"]):
                    rels.append(rel("person_" + slug(person), "assigned_to", eid))
            records.append({"entity": entity, "relations": rels})

    # ── daily status ─────────────────────────────────────────────────────────
    ds_cfg = sources.get("daily_status", {})
    ds_path = vault / ds_cfg.get("path", "daily-status")
    if ds_path.exists():
        for md in ds_path.rglob("*.md"):
            text = md.read_text()
            # Extract blocker issues
            blocker_section = re.search(r"## Blockers(.+?)(?=^##|\Z)", text, re.MULTILINE | re.DOTALL)
            if blocker_section:
                for line in blocker_section.group(1).strip().splitlines():
                    line = line.strip("- ").strip()
                    if line:
                        issue_id = "issue_" + slug(line)[:40]
                        records.append({
                            "entity": {"id": issue_id, "type": "Issue", "properties": {"description": line}},
                            "relations": []
                        })
            # Response time tracking
            rt_section = re.search(r"## Response Times(.+?)(?=^##|\Z)", text, re.MULTILINE | re.DOTALL)
            if rt_section:
                for line in rt_section.group(1).strip().splitlines():
                    m = re.match(r"-\s*(.+?):\s*(.+)", line.strip())
                    if m:
                        person_name = m.group(1).strip()
                        response = m.group(2).strip()
                        pid = "person_" + slug(person_name)
                        records.append({
                            "entity": None,
                            "relations": [],
                            "meta": {"update": {"id": pid, "response_time": response}}
                        })

    if verbose:
        LOG.info(f"Total records to write: {len(records)}")

    if dry_run:
        print(f"[DRY RUN] Would write {len(records)} records to {storage / 'graph.jsonl'}")
        for r in records[:5]:
            print(json.dumps(r, indent=2))
        return

    # Write ontology
    storage.mkdir(parents=True, exist_ok=True)
    graph_file = storage / "graph.jsonl"
    with open(graph_file, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    LOG.info(f"Wrote {len(records)} records to {graph_file}")

    # Write schema
    schema = {
        "entities": ["Person", "Organization", "Project", "Event", "Task", "Issue"],
        "relationships": ["works_at", "assigned_to", "met_at", "for_client", "reports_to", "has_task", "blocks", "has_primary_contact", "has_project"],
        "generated": str(datetime.now().isoformat())
    }
    with open(storage / "schema.yaml", "w") as f:
        yaml.dump(schema, f)

    # Write log
    log_dir = vault / "ontology-sync" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"sync-{date.today()}.log"
    with open(log_file, "w") as f:
        f.write(f"Sync extract completed at {datetime.now().isoformat()}\n")
        f.write(f"Records written: {len(records)}\n")
    (log_dir / "sync-latest.log").write_text(log_file.read_text())
    print(f"Extraction complete. {len(records)} records written to {graph_file}")

# ── Phase 2: Analyze ──────────────────────────────────────────────────────────
def cmd_analyze(cfg):
    vault = Path(cfg["obsidian"]["vault_path"])
    storage = Path(cfg["ontology"]["storage_path"])
    graph_file = storage / "graph.jsonl"
    if not graph_file.exists():
        print("ERROR: graph.jsonl not found. Run 'extract' first.", file=sys.stderr)
        sys.exit(1)

    records = []
    with open(graph_file) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    people = {}
    projects = {}
    orgs = {}
    all_relations = []

    for rec in records:
        ent = rec.get("entity")
        if ent:
            t = ent.get("type")
            if t == "Person":
                people[ent["id"]] = ent
            elif t == "Project":
                projects[ent["id"]] = ent
            elif t == "Organization":
                orgs[ent["id"]] = ent
        for r in rec.get("relations", []):
            all_relations.append(r)

    # Build sets
    assigned_people = set(r["from"] for r in all_relations if r["rel"] == "assigned_to")
    project_refs = set(r["to"] for r in all_relations if r["rel"] == "assigned_to")
    missing_emails = [p for p in people.values() if "email" not in p.get("properties", {})]
    unassigned_team = [p for p in people.values()
                       if p.get("properties", {}).get("role") == "team_member"
                       and p["id"] not in assigned_people]
    broken_project_refs = project_refs - set(projects.keys())

    insights = {
        "total_people": len(people),
        "total_projects": len(projects),
        "total_orgs": len(orgs),
        "missing_email_count": len(missing_emails),
        "missing_email_names": [p["properties"]["name"] for p in missing_emails],
        "unassigned_team_count": len(unassigned_team),
        "broken_project_refs": list(broken_project_refs),
        "generated": str(datetime.now().isoformat())
    }

    feedback_dir = Path(cfg["feedback"]["output_path"])
    feedback_dir.mkdir(parents=True, exist_ok=True)
    insights_file = feedback_dir / "daily-insights.md"
    with open(insights_file, "w") as f:
        f.write(f"# Daily Insights - {date.today()}\n\n")
        f.write(f"## Summary\n")
        f.write(f"- People tracked: {insights['total_people']}\n")
        f.write(f"- Projects tracked: {insights['total_projects']}\n")
        f.write(f"- Organizations tracked: {insights['total_orgs']}\n\n")
        f.write(f"## Issues Found\n")
        if missing_emails:
            f.write(f"- **{len(missing_emails)} contact(s) missing email address:**\n")
            for n in insights["missing_email_names"]:
                f.write(f"  - {n}\n")
        if unassigned_team:
            f.write(f"- **{len(unassigned_team)} team member(s) with no project assignments**\n")
        if broken_project_refs:
            f.write(f"- **Broken project references:** {', '.join(broken_project_refs)}\n")

    print(f"Analysis complete. Insights written to {insights_file}")
    return insights

# ── Phase 3: Feedback ─────────────────────────────────────────────────────────
def cmd_feedback(cfg):
    insights = cmd_analyze(cfg)
    feedback_dir = Path(cfg["feedback"]["output_path"])
    feedback_dir.mkdir(parents=True, exist_ok=True)

    report_file = feedback_dir / "weekly-feedback.md"
    with open(report_file, "w") as f:
        f.write(f"# Sync Feedback - {date.today()}\n\n")
        f.write("## Missing Information\n")
        if insights["missing_email_names"]:
            for name in insights["missing_email_names"]:
                f.write(f"- [ ] `{name}` missing email address\n")
        else:
            f.write("- No missing email addresses found.\n")
        if insights["unassigned_team_count"] > 0:
            f.write(f"\n- [ ] {insights['unassigned_team_count']} team member(s) have no assigned projects\n")
        f.write("\n## Broken References\n")
        if insights["broken_project_refs"]:
            for ref in insights["broken_project_refs"]:
                f.write(f"- [ ] Project `{ref}` referenced but no project file found\n")
        else:
            f.write("- No broken references.\n")
        f.write("\n## Relationship Insights\n")
        f.write(f"- Total entities: {insights['total_people']} people, {insights['total_projects']} projects, {insights['total_orgs']} orgs\n")
        f.write("\n## Template Suggestions\n")
        f.write("- Add `Projects: [[]]` field to contact template\n")
        f.write("- Add `Response Pattern:` field to team template\n")

    suggestions_file = feedback_dir / "suggestions.md"
    with open(suggestions_file, "w") as f:
        f.write(f"# Suggestions - {date.today()}\n\n")
        if insights["broken_project_refs"]:
            f.write("## Create Missing Project Files\n")
            for ref in insights["broken_project_refs"]:
                proj_name = ref.replace("project_", "").replace("_", " ").title()
                f.write(f"- Create `projects/{proj_name}.md` using project template\n")
        f.write("\n## Add Missing Email Addresses\n")
        for name in insights["missing_email_names"]:
            f.write(f"- Update contact/team file for `{name}` with email field\n")

    print(f"Feedback report written to {report_file}")
    print(f"Suggestions written to {suggestions_file}")

# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Obsidian → Ontology Sync")
    parser.add_argument("command", choices=["extract", "analyze", "feedback", "apply-feedback"])
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.command == "extract":
        cmd_extract(cfg, dry_run=args.dry_run, verbose=args.verbose)
    elif args.command == "analyze":
        cmd_analyze(cfg)
    elif args.command == "feedback":
        cmd_feedback(cfg)
    elif args.command == "apply-feedback":
        print("apply-feedback: not yet implemented in this version.")

if __name__ == "__main__":
    main()
'''
(SCRIPTS / "sync.py").write_text(sync_py)

# ── init.py ──────────────────────────────────
init_py = r'''#!/usr/bin/env python3
"""Creates default config.yaml and directory structure."""
import sys
from pathlib import Path
try:
    import yaml
except ImportError:
    print("pyyaml not installed"); sys.exit(1)

DEFAULT_CONFIG = {
    "obsidian": {
        "vault_path": "/root/life/pkm",
        "sources": {
            "contacts": {"path": "references/contacts", "entity_type": "Person",
                         "extract": ["email_from_content","company_from_property","projects_from_links"]},
            "clients": {"path": "references/clients", "entity_type": "Organization",
                        "extract": ["contract_value","projects","contacts"]},
            "team": {"path": "references/team", "entity_type": "Person", "role": "team_member",
                     "extract": ["assignments","response_patterns","reports_to"]},
            "daily_status": {"path": "daily-status",
                             "extract": ["response_times","behavioral_patterns","blockers"]}
        }
    },
    "ontology": {
        "storage_path": "/root/life/pkm/memory/ontology",
        "format": "jsonl",
        "entities": ["Person","Organization","Project","Event","Task"],
        "relationships": ["works_at","assigned_to","met_at","for_client","reports_to","has_task","blocks"]
    },
    "feedback": {
        "output_path": "/root/life/pkm/ontology-sync/feedback",
        "generate_reports": True,
        "suggest_templates": True,
        "highlight_missing": True
    },
    "schedule": {
        "sync_interval": "0 */3 * * *",
        "analyze_daily": "0 9 * * *",
        "feedback_weekly": "0 10 * * MON"
    }
}

config_path = Path("/root/life/pkm/ontology-sync/config.yaml")
config_path.parent.mkdir(parents=True, exist_ok=True)
if config_path.exists():
    print(f"Config already exists at {config_path}")
else:
    with open(config_path, "w") as f:
        yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
    print(f"Created config at {config_path}")
'''
(SCRIPTS / "init.py").write_text(init_py)

# ── setup-cron.py ─────────────────────────────
setup_cron_py = r'''#!/usr/bin/env python3
"""Sets up cron jobs for the sync pipeline."""
import sys, subprocess, tempfile, os

JOBS = [
    ("0 */3 * * *", "python3 skills/obsidian-ontology-sync/scripts/sync.py extract", "Obsidian → Ontology Sync"),
    ("0 9 * * *",   "python3 skills/obsidian-ontology-sync/scripts/sync.py analyze", "Daily Analysis"),
    ("0 10 * * MON","python3 skills/obsidian-ontology-sync/scripts/sync.py feedback","Weekly Feedback"),
]

try:
    current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    lines = current.stdout.splitlines() if current.returncode == 0 else []
except Exception:
    lines = []

for sched, cmd, label in JOBS:
    entry = f"{sched} {cmd}  # {label}"
    if entry not in lines:
        lines.append(entry)

with tempfile.NamedTemporaryFile("w", suffix=".cron", delete=False) as f:
    f.write("\n".join(lines) + "\n")
    tmp = f.name

os.system(f"crontab {tmp}")
os.unlink(tmp)
print("Cron jobs installed:")
for sched, cmd, label in JOBS:
    print(f"  ✓ {label}: {sched}")
'''
(SCRIPTS / "setup-cron.py").write_text(setup_cron_py)

# ── query.py ─────────────────────────────────
query_py = r'''#!/usr/bin/env python3
"""Natural language query interface over ontology graph."""
import sys, json
from pathlib import Path
try:
    import yaml
except ImportError:
    sys.exit(1)

CONFIG_PATH = "/root/life/pkm/ontology-sync/config.yaml"
if not Path(CONFIG_PATH).exists():
    print("Config not found. Run init.py first."); sys.exit(1)

with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)

graph_file = Path(cfg["ontology"]["storage_path"]) / "graph.jsonl"
if not graph_file.exists():
    print("Ontology not found. Run sync.py extract first."); sys.exit(1)

records = []
with open(graph_file) as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

print(f"Ontology loaded: {len(records)} records")
query = " ".join(sys.argv[1:])
print(f"Query: {query}")
people = [r["entity"] for r in records if r.get("entity") and r["entity"].get("type") == "Person"]
print(f"Found {len(people)} Person entities")
'''
(SCRIPTS / "query.py").write_text(query_py)

# ── debug.py ─────────────────────────────────
debug_py = r'''#!/usr/bin/env python3
"""Debug extraction for a specific file."""
import sys, argparse, re, json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--file", required=True)
args = parser.parse_args()

p = Path("/root/life/pkm") / args.file
if not p.exists():
    print(f"File not found: {p}"); sys.exit(1)

text = p.read_text()
print(f"=== {p} ===")
print(text[:500])
props = {m.group(1): m.group(2) for m in re.finditer(r"\*\*([^*]+)\*\*:\s*(.+)", text)}
print("Extracted properties:", json.dumps(props, indent=2))
'''
(SCRIPTS / "debug.py").write_text(debug_py)

print("Workspace generated successfully.")
print(f"Vault: {VAULT}")
print(f"Scripts: {SCRIPTS}")