import os
import json
import stat

workspace = "/workspace"

# ─────────────────────────────────────────────────────────────────────────────
# 1.  Directory skeleton
# ─────────────────────────────────────────────────────────────────────────────
dirs = [
    # PKM vault
    "root/life/pkm/references/contacts",
    "root/life/pkm/references/clients",
    "root/life/pkm/references/team",
    "root/life/pkm/projects",
    "root/life/pkm/daily-status/2026-02-27",
    "root/life/pkm/daily-status/2026-02-26",
    # Distractor directories
    "root/life/pkm/journal",
    "root/life/pkm/areas/finance",
    "root/life/pkm/areas/health",
    "root/life/pkm/resources/books",
    "root/life/pkm/resources/articles",
    "root/life/pkm/templates",
    # Skill scripts
    "skills/obsidian-ontology-sync/scripts",
    "skills/obsidian-ontology-sync/tests",
    "skills/ontology/scripts",
    # Cron state dir
    "var/cron",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

def write(path, content):
    full = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

# ─────────────────────────────────────────────────────────────────────────────
# 2.  Vault source notes (messy, realistic)
# ─────────────────────────────────────────────────────────────────────────────

# -- Contacts --
write("root/life/pkm/references/contacts/Alice_Johnson.md", """\
# Alice Johnson

**Email:** alice@acmecorp.com
**Company:** Acme Corp
**Met At:** Tech Conference 2026
**Projects:** [[Project Alpha]]

## Notes
Great developer, very responsive. Always delivers on time.
Looking to expand collaboration next quarter.
""")

write("root/life/pkm/references/contacts/Bob_Smith.md", """\
# Bob Smith

**Company:** TechHub
**Met At:** AI Summit 2025

## Notes
No email on file yet. Met briefly at the summit.
Potential lead for Project Beta.
**Projects:** [[Project Beta]]
""")

write("root/life/pkm/references/contacts/Carol_White.md", """\
# Carol White

**Email:** carol@synergyllc.com
**Company:** Synergy LLC
**Met At:** Tech Conference 2026
**Projects:** [[Project Alpha]], [[Project Gamma]]

## Notes
Senior architect. Handles enterprise integrations.
""")

write("root/life/pkm/references/contacts/David_Park.md", """\
# David Park

**Email:** dpark@acmecorp.com
**Company:** Acme Corp
**Met At:** Tech Conference 2026

## Notes
Junior engineer. Strong Python skills. No projects assigned yet.
""")

# -- Clients --
write("root/life/pkm/references/clients/Acme_Corp.md", """\
# Acme Corp

**Contract Value:** 550000
**Primary Contact:** [[Alice Johnson]]
**Projects:** [[Project Alpha]]

## Notes
Long-term client. Renewal expected Q3 2026.
""")

write("root/life/pkm/references/clients/TechHub.md", """\
# TechHub

**Contract Value:** 320000
**Primary Contact:** [[Bob Smith]]
**Projects:** [[Project Beta]]

## Notes
Newer client, growing relationship.
""")

# -- Team --
write("root/life/pkm/references/team/Eve_Torres.md", """\
# Eve Torres

**Email:** eve@internal.com
**Role:** Lead Engineer
**Reports To:** [[Frank]]
**Projects:** [[Project Alpha]], [[Project Beta]]
**Response Pattern:** proactive

## Notes
Top performer. Handles two major projects simultaneously.
""")

write("root/life/pkm/references/team/Frank_Lee.md", """\
# Frank Lee

**Email:** frank@internal.com
**Role:** Engineering Manager
**Projects:** [[Project Alpha]], [[Project Beta]], [[Project Gamma]]
**Response Pattern:** proactive

## Notes
Manages all active projects. Reports to CTO.
""")

write("root/life/pkm/references/team/Grace_Kim.md", """\
# Grace Kim

**Role:** Junior Developer
**Reports To:** [[Frank]]
**Projects:** [[Project Gamma]]
**Response Pattern:** reactive

## Notes
Missing email address. Recently joined the team.
""")

# -- Projects --
write("root/life/pkm/projects/Project_Alpha.md", """\
# Project Alpha

**Client:** [[Acme Corp]]
**Status:** active
**Value:** 550000
**Deadline:** 2026-06-30
**Team:** [[Eve Torres]], [[Frank Lee]], [[Alice Johnson]]

## Notes
Core platform build. Phase 2 starting March.
""")

write("root/life/pkm/projects/Project_Beta.md", """\
# Project Beta

**Client:** [[TechHub]]
**Status:** active
**Value:** 320000
**Deadline:** 2026-09-15
**Team:** [[Eve Torres]], [[Frank Lee]], [[Bob Smith]]

## Notes
Data pipeline integration. On track.
""")

# -- Daily status --
write("root/life/pkm/daily-status/2026-02-27/status.md", """\
# Daily Status 2026-02-27

## Eve Torres
- Submitted API integration for Project Alpha
- Response time: 2h
- Blocker: waiting on Acme Corp credentials

## Frank Lee
- Reviewed Project Beta sprint plan
- Response time: 1h
- No blockers

## Grace Kim
- Working on Project Gamma UI
- Response time: 8h
- Blocker: unclear requirements from client
""")

write("root/life/pkm/daily-status/2026-02-26/status.md", """\
# Daily Status 2026-02-26

## Eve Torres
- Completed data model review
- Response time: 1h

## Frank Lee
- Client call with TechHub
- Response time: 30m
""")

# ─────────────────────────────────────────────────────────────────────────────
# 3.  Distractor files (noise)
# ─────────────────────────────────────────────────────────────────────────────
write("root/life/pkm/journal/2026-02-27.md", """\
# Personal Journal

Today was productive. Gym at 7am. Need to call mom.
Reading: 'Thinking Fast and Slow' - chapter 12.
""")

write("root/life/pkm/areas/finance/Q1-budget.md", """\
# Q1 Budget

Total: $1.2M
Engineering: $800k
Marketing: $400k
""")

write("root/life/pkm/areas/health/workout-log.md", """\
# Workout Log
- 2026-02-27: 5km run, 30min weights
""")

write("root/life/pkm/resources/books/reading-list.md", """\
# Reading List
- [ ] Deep Work - Cal Newport
- [x] Atomic Habits - James Clear
""")

write("root/life/pkm/resources/articles/ai-trends-2026.md", """\
# AI Trends 2026
Notes from various articles about LLMs, agents, etc.
""")

write("root/life/pkm/templates/contact-template.md", """\
# {{Name}}

**Email:** 
**Company:** 
**Met At:** 
**Projects:** 

## Notes
""")

write("root/life/pkm/templates/project-template.md", """\
# {{Project Name}}

**Client:** 
**Status:** 
**Value:** 
**Deadline:** 
**Team:** 

## Notes
""")

write("skills/obsidian-ontology-sync/tests/test_extraction.py", """\
# Placeholder test file - do not run directly
import unittest
class TestExtraction(unittest.TestCase):
    pass
""")

# ─────────────────────────────────────────────────────────────────────────────
# 4.  The actual skill scripts (pre-existing per SKILL.md)
# ─────────────────────────────────────────────────────────────────────────────

# ---------- sync.py ----------
sync_py = r'''#!/usr/bin/env python3
"""
obsidian-ontology-sync :: sync.py
Extracts entities from Obsidian vault → writes graph.jsonl
"""

import sys, os, re, json, yaml, datetime
from pathlib import Path

# ── locate config ──────────────────────────────────────────────────────────
DEFAULT_CONFIG = "/root/life/pkm/ontology-sync/config.yaml"

def load_config(cfg_path=DEFAULT_CONFIG):
    with open(cfg_path) as f:
        return yaml.safe_load(f)

def slugify(text):
    t = text.lower().strip()
    t = re.sub(r"[^a-z0-9]+", "_", t)
    return t.strip("_")

def entity_id(etype, name):
    return f"{etype.lower()}_{slugify(name)}"

# ── parsers ────────────────────────────────────────────────────────────────

def parse_contacts(vault, sources_cfg):
    path = Path(vault) / sources_cfg["contacts"]["path"]
    entities, relations = [], []
    for md in path.glob("*.md"):
        text = md.read_text()
        name = md.stem.replace("_", " ")
        eid = entity_id("person", name)

        email_m = re.search(r"\*\*Email:\*\*\s*(.+)", text)
        company_m = re.search(r"\*\*Company:\*\*\s*(.+)", text)
        metat_m = re.search(r"\*\*Met At:\*\*\s*(.+)", text)
        proj_m = re.findall(r"\[\[([^\]]+)\]\]", text)
        notes_m = re.search(r"## Notes\n([\s\S]+?)(?:\n##|$)", text)

        props = {"name": name}
        if email_m:
            props["email"] = email_m.group(1).strip()
        if notes_m:
            props["notes"] = notes_m.group(1).strip()

        entities.append({"id": eid, "type": "Person", "properties": props})

        if company_m:
            org = company_m.group(1).strip()
            oid = entity_id("org", org)
            entities.append({"id": oid, "type": "Organization",
                              "properties": {"name": org}})
            relations.append({"from": eid, "rel": "works_at", "to": oid})

        if metat_m:
            evt = metat_m.group(1).strip()
            evid = entity_id("event", evt)
            entities.append({"id": evid, "type": "Event",
                              "properties": {"name": evt}})
            relations.append({"from": eid, "rel": "met_at", "to": evid})

        for proj in proj_m:
            if proj not in ["Alice Johnson", "Bob Smith", "Carol White",
                            "David Park", "Eve Torres", "Frank Lee",
                            "Frank", "Grace Kim",
                            "Acme Corp", "TechHub", "Synergy LLC"]:
                pid = entity_id("project", proj)
                relations.append({"from": eid, "rel": "assigned_to", "to": pid})

    return entities, relations


def parse_clients(vault, sources_cfg):
    path = Path(vault) / sources_cfg["clients"]["path"]
    entities, relations = [], []
    for md in path.glob("*.md"):
        text = md.read_text()
        name = md.stem.replace("_", " ")
        oid = entity_id("org", name)

        val_m = re.search(r"\*\*Contract Value:\*\*\s*(\d+)", text)
        contact_m = re.search(r"\*\*Primary Contact:\*\*\s*\[\[([^\]]+)\]\]", text)
        proj_m = re.findall(r"\[\[([^\]]+)\]\]", text)

        props = {"name": name}
        if val_m:
            props["contract_value"] = int(val_m.group(1))

        entities.append({"id": oid, "type": "Organization", "properties": props})

        if contact_m:
            pid = entity_id("person", contact_m.group(1).strip())
            relations.append({"from": oid, "rel": "has_primary_contact", "to": pid})

        for proj in proj_m:
            if "Contact" not in proj and proj not in [name]:
                pid = entity_id("project", proj)
                relations.append({"from": pid, "rel": "for_client", "to": oid})

    return entities, relations


def parse_team(vault, sources_cfg):
    path = Path(vault) / sources_cfg["team"]["path"]
    entities, relations = [], []
    for md in path.glob("*.md"):
        text = md.read_text()
        name = md.stem.replace("_", " ")
        eid = entity_id("person", name)

        email_m = re.search(r"\*\*Email:\*\*\s*(.+)", text)
        rp_m = re.search(r"\*\*Response Pattern:\*\*\s*(.+)", text)
        reports_m = re.search(r"\*\*Reports To:\*\*\s*\[\[([^\]]+)\]\]", text)
        proj_m = re.findall(r"\[\[([^\]]+)\]\]", text)
        notes_m = re.search(r"## Notes\n([\s\S]+?)(?:\n##|$)", text)

        props = {"name": name, "role": "team_member"}
        if email_m:
            props["email"] = email_m.group(1).strip()
        if rp_m:
            props["response_pattern"] = rp_m.group(1).strip()
        if notes_m:
            props["notes"] = notes_m.group(1).strip()

        entities.append({"id": eid, "type": "Person", "properties": props})

        if reports_m:
            mgr = reports_m.group(1).strip()
            mid = entity_id("person", mgr)
            relations.append({"from": eid, "rel": "reports_to", "to": mid})

        for proj in proj_m:
            if proj not in ["Frank", "Frank Lee"]:
                pid = entity_id("project", proj)
                relations.append({"from": eid, "rel": "assigned_to", "to": pid})

    return entities, relations


def parse_projects(vault):
    path = Path(vault) / "projects"
    entities, relations = [], []
    for md in path.glob("*.md"):
        text = md.read_text()
        name = md.stem.replace("_", " ")
        pid = entity_id("project", name)

        client_m = re.search(r"\*\*Client:\*\*\s*\[\[([^\]]+)\]\]", text)
        status_m = re.search(r"\*\*Status:\*\*\s*(.+)", text)
        val_m = re.search(r"\*\*Value:\*\*\s*(\d+)", text)
        deadline_m = re.search(r"\*\*Deadline:\*\*\s*(.+)", text)
        team_m = re.findall(r"\[\[([^\]]+)\]\]", text)

        props = {"name": name}
        if status_m:
            props["status"] = status_m.group(1).strip()
        if val_m:
            props["value"] = int(val_m.group(1))
        if deadline_m:
            props["deadline"] = deadline_m.group(1).strip()

        entities.append({"id": pid, "type": "Project", "properties": props})

        if client_m:
            oid = entity_id("org", client_m.group(1).strip())
            relations.append({"from": pid, "rel": "for_client", "to": oid})

        for member in team_m:
            if member not in [client_m.group(1).strip() if client_m else ""]:
                mid = entity_id("person", member)
                relations.append({"from": pid, "rel": "has_team_member", "to": mid})

    return entities, relations


def parse_daily_status(vault):
    path = Path(vault) / "daily-status"
    entities, relations = [], []
    for day_dir in path.iterdir():
        if not day_dir.is_dir():
            continue
        for md in day_dir.glob("*.md"):
            text = md.read_text()
            date_str = day_dir.name
            # extract response times
            blocks = re.split(r"\n## ", text)
            for block in blocks[1:]:
                lines = block.strip().split("\n")
                person_name = lines[0].strip()
                pid = entity_id("person", person_name)
                rt_m = re.search(r"Response time:\s*(.+)", block)
                blocker_m = re.search(r"Blocker:\s*(.+)", block)
                evid = entity_id("event", f"status_{slugify(person_name)}_{date_str}")
                eprops = {"name": f"Status {person_name} {date_str}", "date": date_str}
                if rt_m:
                    eprops["response_time"] = rt_m.group(1).strip()
                if blocker_m:
                    eprops["blocker"] = blocker_m.group(1).strip()
                entities.append({"id": evid, "type": "Event", "properties": eprops})
                relations.append({"from": pid, "rel": "has_status_event", "to": evid})
    return entities, relations


# ── dedup + write ──────────────────────────────────────────────────────────

def dedup_entities(ents):
    seen = {}
    for e in ents:
        eid = e["id"]
        if eid not in seen:
            seen[eid] = e
        else:
            # merge properties
            seen[eid]["properties"].update(e["properties"])
    return list(seen.values())


def write_graph(cfg, entities, relations):
    storage = Path(cfg["ontology"]["storage_path"])
    storage.mkdir(parents=True, exist_ok=True)
    graph_file = storage / "graph.jsonl"
    with open(graph_file, "w") as f:
        for e in entities:
            f.write(json.dumps({"record_type": "entity", **e}) + "\n")
        for r in relations:
            f.write(json.dumps({"record_type": "relation", **r}) + "\n")
    print(f"[sync] Wrote {len(entities)} entities and {len(relations)} relations → {graph_file}")

    # schema
    schema = {"entity_types": ["Person","Organization","Project","Event","Task"],
              "relationship_types": ["works_at","assigned_to","met_at","for_client",
                                     "reports_to","has_task","blocks","has_team_member",
                                     "has_primary_contact","has_status_event"]}
    with open(storage / "schema.yaml", "w") as f:
        yaml.dump(schema, f)


# ── analysis ───────────────────────────────────────────────────────────────

def load_graph(cfg):
    graph_file = Path(cfg["ontology"]["storage_path"]) / "graph.jsonl"
    entities, relations = [], []
    if not graph_file.exists():
        return entities, relations
    with open(graph_file) as f:
        for line in f:
            rec = json.loads(line)
            if rec["record_type"] == "entity":
                entities.append(rec)
            else:
                relations.append(rec)
    return entities, relations


def run_analyze(cfg):
    entities, relations = load_graph(cfg)
    insights = []

    persons = [e for e in entities if e["type"] == "Person"]
    projects = [e for e in entities if e["type"] == "Project"]

    # Missing emails
    missing_email = [p for p in persons if "email" not in p["properties"]]
    for p in missing_email:
        insights.append(f"Contact '{p['properties']['name']}' missing email address")

    # People with no project
    assigned_ids = set(r["from"] for r in relations if r["rel"] == "assigned_to")
    unassigned = [p for p in persons if p["id"] not in assigned_ids
                  and p["properties"].get("role") == "team_member"]
    if unassigned:
        insights.append(f"{len(unassigned)} team members have no assigned projects")

    # Projects with no client
    proj_with_client = set(r["from"] for r in relations if r["rel"] == "for_client")
    no_client = [p for p in projects if p["id"] not in proj_with_client]
    for p in no_client:
        insights.append(f"Project '{p['properties']['name']}' has no client linked")

    print("[analyze] Insights:")
    for i in insights:
        print(f"  - {i}")

    # Write daily insights
    feedback_path = Path(cfg["feedback"]["output_path"])
    feedback_path.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    insight_file = feedback_path / "daily-insights.md"
    with open(insight_file, "w") as f:
        f.write(f"# Daily Insights - {today}\n\n")
        f.write("## Analysis Results\n\n")
        for i in insights:
            f.write(f"- {i}\n")
    print(f"[analyze] Wrote insights → {insight_file}")
    return insights


# ── feedback ───────────────────────────────────────────────────────────────

def run_feedback(cfg):
    entities, relations = load_graph(cfg)
    feedback_path = Path(cfg["feedback"]["output_path"])
    feedback_path.mkdir(parents=True, exist_ok=True)

    persons = [e for e in entities if e["type"] == "Person"]
    projects = [e for e in entities if e["type"] == "Project"]

    today = datetime.date.today().isoformat()

    # weekly-feedback.md
    wf = feedback_path / "weekly-feedback.md"
    missing_info = []
    for p in persons:
        if "email" not in p["properties"]:
            missing_info.append(f"- [ ] `{p['properties']['name']}` missing email address")
        if "phone" not in p["properties"]:
            missing_info.append(f"- [ ] `{p['properties']['name']}` missing phone number")

    proj_missing = []
    for p in projects:
        if "deadline" not in p["properties"]:
            proj_missing.append(f"- [ ] Project `{p['properties']['name']}` missing deadline")

    with open(wf, "w") as f:
        f.write(f"# Sync Feedback - {today}\n\n")
        f.write(f"## Missing Information ({len(missing_info)} items)\n\n")
        for item in missing_info:
            f.write(item + "\n")
        f.write(f"\n## Project Issues ({len(proj_missing)} items)\n\n")
        for item in proj_missing:
            f.write(item + "\n")
        f.write("\n## Template Suggestions\n\n")
        f.write("- Add `Projects: [[]]` field to contact template\n")
        f.write("- Add `Response Pattern:` field to team template\n")
    print(f"[feedback] Wrote weekly feedback → {wf}")

    # suggestions.md
    sf = feedback_path / "suggestions.md"
    with open(sf, "w") as f:
        f.write(f"# Suggestions - {today}\n\n")
        f.write("## Relationship Suggestions\n\n")
        # Group persons by org
        org_people = {}
        for r in relations:
            if r["rel"] == "works_at":
                org_people.setdefault(r["to"], []).append(r["from"])
        for org_id, people_ids in org_people.items():
            if len(people_ids) >= 2:
                names = []
                for pid in people_ids:
                    match = next((e for e in entities if e["id"] == pid), None)
                    if match:
                        names.append(match["properties"]["name"])
                f.write(f"- Found {len(people_ids)} contacts at `{org_id}`: {', '.join(names)}\n")
    print(f"[feedback] Wrote suggestions → {sf}")


# ── main ───────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    verbose = "--verbose" in args
    command = [a for a in args if not a.startswith("--")]
    cmd = command[0] if command else "extract"

    cfg = load_config()
    vault = cfg["obsidian"]["vault_path"]
    sources = cfg["obsidian"]["sources"]

    if cmd == "extract":
        all_ents, all_rels = [], []
        ce, cr = parse_contacts(vault, sources)
        all_ents.extend(ce); all_rels.extend(cr)
        cle, clr = parse_clients(vault, sources)
        all_ents.extend(cle); all_rels.extend(clr)
        te, tr = parse_team(vault, sources)
        all_ents.extend(te); all_rels.extend(tr)
        pe, pr = parse_projects(vault)
        all_ents.extend(pe); all_rels.extend(pr)
        de, dr = parse_daily_status(vault)
        all_ents.extend(de); all_rels.extend(dr)

        all_ents = dedup_entities(all_ents)

        if dry_run:
            print(f"[dry-run] Would write {len(all_ents)} entities, {len(all_rels)} relations")
            if verbose:
                for e in all_ents:
                    print(" ", e)
        else:
            write_graph(cfg, all_ents, all_rels)
            # write log
            log_dir = Path(vault) / "ontology-sync" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            today = datetime.date.today().isoformat()
            with open(log_dir / f"sync-{today}.log", "w") as lf:
                lf.write(f"Sync completed at {datetime.datetime.now().isoformat()}\n")
                lf.write(f"Entities: {len(all_ents)}\n")
                lf.write(f"Relations: {len(all_rels)}\n")
            with open(log_dir / "sync-latest.log", "w") as lf:
                lf.write(f"Sync completed at {datetime.datetime.now().isoformat()}\n")
                lf.write(f"Entities: {len(all_ents)}\n")
                lf.write(f"Relations: {len(all_rels)}\n")

    elif cmd == "analyze":
        run_analyze(cfg)

    elif cmd == "feedback":
        run_feedback(cfg)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

write("skills/obsidian-ontology-sync/scripts/sync.py", sync_py)

# ---------- init.py ----------
init_py = r'''#!/usr/bin/env python3
"""
obsidian-ontology-sync :: init.py
Creates config.yaml, ontology directories, and cron jobs.
"""
import os, yaml
from pathlib import Path

VAULT = "/root/life/pkm"
CONFIG_PATH = f"{VAULT}/ontology-sync/config.yaml"

DEFAULT_CONFIG = {
    "obsidian": {
        "vault_path": VAULT,
        "sources": {
            "contacts": {
                "path": "references/contacts",
                "entity_type": "Person",
                "extract": ["email_from_content", "company_from_property", "projects_from_links"]
            },
            "clients": {
                "path": "references/clients",
                "entity_type": "Organization",
                "extract": ["contract_value", "projects", "contacts"]
            },
            "team": {
                "path": "references/team",
                "entity_type": "Person",
                "role": "team_member",
                "extract": ["assignments", "response_patterns", "reports_to"]
            },
            "daily_status": {
                "path": "daily-status",
                "extract": ["response_times", "behavioral_patterns", "blockers"]
            }
        }
    },
    "ontology": {
        "storage_path": f"{VAULT}/memory/ontology",
        "format": "jsonl",
        "entities": ["Person", "Organization", "Project", "Event", "Task"],
        "relationships": ["works_at", "assigned_to", "met_at", "for_client",
                          "reports_to", "has_task", "blocks"]
    },
    "feedback": {
        "output_path": f"{VAULT}/ontology-sync/feedback",
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

def main():
    # Create config
    cfg_path = Path(CONFIG_PATH)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cfg_path, "w") as f:
        yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)
    print(f"[init] Created config → {cfg_path}")

    # Create ontology dir structure
    ontology_path = Path(f"{VAULT}/memory/ontology")
    ontology_path.mkdir(parents=True, exist_ok=True)
    print(f"[init] Created ontology directory → {ontology_path}")

    # Create feedback dir
    feedback_path = Path(f"{VAULT}/ontology-sync/feedback")
    feedback_path.mkdir(parents=True, exist_ok=True)
    print(f"[init] Created feedback directory → {feedback_path}")

    # Create logs dir
    logs_path = Path(f"{VAULT}/ontology-sync/logs")
    logs_path.mkdir(parents=True, exist_ok=True)
    print(f"[init] Created logs directory → {logs_path}")

    print("[init] Initialization complete.")
    print("[init] Next steps:")
    print("  1. Run: python3 skills/obsidian-ontology-sync/scripts/sync.py extract --dry-run")
    print("  2. Run: python3 skills/obsidian-ontology-sync/scripts/sync.py extract")
    print("  3. Run: python3 skills/obsidian-ontology-sync/scripts/setup-cron.py")

if __name__ == "__main__":
    main()
'''
write("skills/obsidian-ontology-sync/scripts/init.py", init_py)

# ---------- setup-cron.py ----------
setup_cron_py = r'''#!/usr/bin/env python3
"""
obsidian-ontology-sync :: setup-cron.py
Registers the three required cron jobs using the schedule defined in config.yaml.
"""
import yaml, json, os
from pathlib import Path

CONFIG_PATH = "/root/life/pkm/ontology-sync/config.yaml"
CRON_STATE_FILE = "/workspace/var/cron/jobs.json"

def main():
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)

    sched = cfg["schedule"]

    jobs = [
        {
            "label": "Obsidian → Ontology Sync",
            "schedule": sched["sync_interval"],
            "task": "python3 skills/obsidian-ontology-sync/scripts/sync.py extract"
        },
        {
            "label": "Daily Ontology Analysis",
            "schedule": sched["analyze_daily"],
            "task": "python3 skills/obsidian-ontology-sync/scripts/sync.py analyze"
        },
        {
            "label": "Weekly Feedback Report",
            "schedule": sched["feedback_weekly"],
            "task": "python3 skills/obsidian-ontology-sync/scripts/sync.py feedback"
        }
    ]

    Path(CRON_STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(CRON_STATE_FILE, "w") as f:
        json.dump(jobs, f, indent=2)

    print("[setup-cron] Registered cron jobs:")
    for j in jobs:
        print(f"  ✓ [{j['schedule']}] {j['label']}")

if __name__ == "__main__":
    main()
'''
write("skills/obsidian-ontology-sync/scripts/setup-cron.py", setup_cron_py)

# ---------- debug.py ----------
debug_py = r'''#!/usr/bin/env python3
"""Debug a single vault file."""
import sys, re

def main():
    args = sys.argv[1:]
    f_idx = args.index("--file") if "--file" in args else None
    if f_idx is None:
        print("Usage: debug.py --file <path>")
        sys.exit(1)
    fpath = args[f_idx + 1]
    text = open(fpath).read()
    print(f"=== {fpath} ===")
    print(text)

if __name__ == "__main__":
    main()
'''
write("skills/obsidian-ontology-sync/scripts/debug.py", debug_py)

# ---------- query.py ----------
query_py = r'''#!/usr/bin/env python3
"""Natural language query wrapper."""
import sys, json
from pathlib import Path

def main():
    query = " ".join(sys.argv[1:])
    graph_file = Path("/root/life/pkm/memory/ontology/graph.jsonl")
    if not graph_file.exists():
        print("No ontology data found. Run sync first.")
        sys.exit(1)
    entities = []
    with open(graph_file) as f:
        for line in f:
            rec = json.loads(line)
            if rec["record_type"] == "entity":
                entities.append(rec)
    print(f"Query: {query}")
    print(f"Found {len(entities)} entities in ontology.")
    persons = [e for e in entities if e["type"] == "Person"]
    print(f"  Persons: {len(persons)}")
    print(f"  Projects: {len([e for e in entities if e['type'] == 'Project'])}")
    print(f"  Organizations: {len([e for e in entities if e['type'] == 'Organization'])}")

if __name__ == "__main__":
    main()
'''
write("skills/obsidian-ontology-sync/scripts/query.py", query_py)

# ---------- ontology.py (skills/ontology/scripts/) ----------
ontology_py = r'''#!/usr/bin/env python3
"""Ontology query tool."""
import sys, json, argparse
from pathlib import Path

GRAPH = Path("/root/life/pkm/memory/ontology/graph.jsonl")

def load():
    ents, rels = [], []
    if not GRAPH.exists():
        return ents, rels
    for line in GRAPH.read_text().splitlines():
        r = json.loads(line)
        if r["record_type"] == "entity":
            ents.append(r)
        else:
            rels.append(r)
    return ents, rels

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_cmd", nargs="?", default="query")
    parser.add_argument("--type")
    parser.add_argument("--where")
    parser.add_argument("--related")
    parser.add_argument("--filter")
    parser.add_argument("--missing")
    parser.add_argument("--aggregate")
    parser.add_argument("--group-by")
    parser.add_argument("--count", action="store_true")
    args = parser.parse_args()

    ents, rels = load()
    results = [e for e in ents if not args.type or e["type"] == args.type]
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
'''
write("skills/ontology/scripts/ontology.py", ontology_py)

print("Workspace generation complete.")
print(f"Vault: /root/life/pkm/")
print(f"Scripts: /workspace/skills/obsidian-ontology-sync/scripts/")