import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── Skill script stubs (simulating pre-installed skill) ────────────────────
skill_dir = WORKSPACE / "skills" / "obsidian-ontology-sync" / "scripts"
skill_dir.mkdir(parents=True, exist_ok=True)

ontology_script_dir = WORKSPACE / "skills" / "ontology" / "scripts"
ontology_script_dir.mkdir(parents=True, exist_ok=True)

# ── sync.py ──────────────────────────────────────────────────────────────────
sync_py = skill_dir / "sync.py"
sync_py.write_text(r'''#!/usr/bin/env python3
"""
Obsidian-Ontology Sync Tool
Usage:
  sync.py extract [--dry-run] [--verbose]
  sync.py analyze
  sync.py feedback
  sync.py apply-feedback
"""
import sys
import os
import re
import json
import yaml
import datetime
from pathlib import Path

CONFIG_SEARCH_PATHS = [
    "/workspace/pkm_vault/ontology-sync/config.yaml",
    "/root/life/pkm/ontology-sync/config.yaml",
    "config.yaml",
]

def load_config():
    for p in CONFIG_SEARCH_PATHS:
        if Path(p).exists():
            with open(p) as f:
                return yaml.safe_load(f), p
    raise FileNotFoundError(
        f"config.yaml not found. Searched: {CONFIG_SEARCH_PATHS}\n"
        "Create it at /workspace/pkm_vault/ontology-sync/config.yaml"
    )

def slugify(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')

def extract_frontmatter_and_body(text):
    fm = {}
    body = text
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1]) or {}
            except Exception:
                fm = {}
            body = parts[2]
    return fm, body

def extract_inline_property(body, key):
    """Extract value from `**Key:** value` style markdown."""
    pattern = rf'\*\*{re.escape(key)}:\*\*\s*(.+)'
    m = re.search(pattern, body)
    if m:
        return m.group(1).strip()
    # Also try bare `Key: value`
    pattern2 = rf'^{re.escape(key)}:\s*(.+)'
    m2 = re.search(pattern2, body, re.MULTILINE)
    if m2:
        return m2.group(1).strip()
    return None

def extract_wikilinks(text):
    return re.findall(r'\[\[([^\]]+)\]\]', text)

def parse_contact(filepath, vault_path):
    text = Path(filepath).read_text()
    fm, body = extract_frontmatter_and_body(text)
    name = Path(filepath).stem.replace('-', ' ').replace('_', ' ')
    entity_id = "person_" + slugify(name)
    props = {"name": name}
    email = extract_inline_property(body, "Email") or fm.get("email")
    if email:
        props["email"] = email
    phone = extract_inline_property(body, "Phone") or fm.get("phone")
    if phone:
        props["phone"] = phone
    # Notes (content after stripping headers/properties)
    notes_match = re.search(r'## Notes\s*\n(.+)', body, re.DOTALL)
    if notes_match:
        props["notes"] = notes_match.group(1).strip()[:200]
    relations = []
    company = extract_inline_property(body, "Company") or fm.get("company")
    if company:
        org_id = "org_" + slugify(company)
        relations.append({"from": entity_id, "rel": "works_at", "to": org_id})
        # also emit org entity
    met_at = extract_inline_property(body, "Met At") or fm.get("met_at")
    if met_at:
        event_id = "event_" + slugify(met_at)
        relations.append({"from": entity_id, "rel": "met_at", "to": event_id})
    projects_raw = extract_inline_property(body, "Projects") or fm.get("projects", "")
    links = extract_wikilinks(body)
    all_projects = []
    if projects_raw:
        # comma separated or wikilinks
        for p in re.split(r'[,;]', projects_raw):
            p = p.strip().strip('[]')
            if p:
                all_projects.append(p)
    for lnk in links:
        if lnk not in all_projects:
            all_projects.append(lnk)
    for proj in all_projects:
        proj_id = "project_" + slugify(proj)
        relations.append({"from": entity_id, "rel": "assigned_to", "to": proj_id})
    return {"entity": {"id": entity_id, "type": "Person", "properties": props}, "relations": relations}, company

def parse_client(filepath, vault_path):
    text = Path(filepath).read_text()
    fm, body = extract_frontmatter_and_body(text)
    name = Path(filepath).stem.replace('-', ' ').replace('_', ' ')
    entity_id = "org_" + slugify(name)
    props = {"name": name}
    cv_raw = extract_inline_property(body, "Contract Value") or fm.get("contract_value")
    if cv_raw:
        nums = re.findall(r'[\d,]+', str(cv_raw))
        if nums:
            props["contract_value"] = int(nums[0].replace(',',''))
    relations = []
    projects_raw = extract_inline_property(body, "Projects") or fm.get("projects", "")
    if projects_raw:
        for p in re.split(r'[,;]', projects_raw):
            p = p.strip().strip('[]')
            if p:
                proj_id = "project_" + slugify(p)
                relations.append({"from": entity_id, "rel": "has_project", "to": proj_id})
    contact_raw = extract_inline_property(body, "Primary Contact") or fm.get("primary_contact")
    if contact_raw:
        contact_id = "person_" + slugify(contact_raw)
        relations.append({"from": entity_id, "rel": "primary_contact", "to": contact_id})
    return {"entity": {"id": entity_id, "type": "Organization", "properties": props}, "relations": relations}

def parse_team(filepath, vault_path):
    text = Path(filepath).read_text()
    fm, body = extract_frontmatter_and_body(text)
    name = Path(filepath).stem.replace('-', ' ').replace('_', ' ')
    entity_id = "person_" + slugify(name)
    props = {"name": name, "role": "team_member"}
    email = extract_inline_property(body, "Email") or fm.get("email")
    if email:
        props["email"] = email
    phone = extract_inline_property(body, "Phone") or fm.get("phone")
    if phone:
        props["phone"] = phone
    rp = extract_inline_property(body, "Response Pattern") or fm.get("response_pattern")
    if rp:
        props["response_pattern"] = rp
    relations = []
    reports_to_raw = extract_inline_property(body, "Reports To") or fm.get("reports_to")
    if reports_to_raw:
        mgr_id = "person_" + slugify(reports_to_raw)
        relations.append({"from": entity_id, "rel": "reports_to", "to": mgr_id})
    assignments_raw = extract_inline_property(body, "Assignments") or fm.get("assignments", "")
    if assignments_raw:
        for p in re.split(r'[,;]', assignments_raw):
            p = p.strip().strip('[]')
            if p:
                proj_id = "project_" + slugify(p)
                relations.append({"from": entity_id, "rel": "assigned_to", "to": proj_id})
    return {"entity": {"id": entity_id, "type": "Person", "properties": props}, "relations": relations}

def parse_project(filepath, vault_path):
    text = Path(filepath).read_text()
    fm, body = extract_frontmatter_and_body(text)
    name = Path(filepath).stem.replace('-', ' ').replace('_', ' ')
    entity_id = "project_" + slugify(name)
    props = {"name": name}
    status = extract_inline_property(body, "Status") or fm.get("status")
    if status:
        props["status"] = status
    deadline = extract_inline_property(body, "Deadline") or fm.get("deadline")
    if deadline:
        props["deadline"] = deadline
    value_raw = extract_inline_property(body, "Value") or fm.get("value")
    if value_raw:
        nums = re.findall(r'[\d,]+', str(value_raw))
        if nums:
            props["value"] = int(nums[0].replace(',',''))
    relations = []
    client_raw = extract_inline_property(body, "Client") or fm.get("client")
    if client_raw:
        org_id = "org_" + slugify(client_raw)
        relations.append({"from": entity_id, "rel": "for_client", "to": org_id})
    team_raw = extract_inline_property(body, "Team") or fm.get("team", "")
    if team_raw:
        for m in re.split(r'[,;]', team_raw):
            m = m.strip().strip('[]')
            if m:
                person_id = "person_" + slugify(m)
                relations.append({"from": entity_id, "rel": "has_team_member", "to": person_id})
    return {"entity": {"id": entity_id, "type": "Project", "properties": props}, "relations": relations}

def run_extract(dry_run=False, verbose=False):
    config, config_path = load_config()
    vault_path = Path(config["obsidian"]["vault_path"])
    storage_path = Path(config["ontology"]["storage_path"])
    sources = config["obsidian"]["sources"]
    records = []
    org_entities = {}

    def process_dir(src_key, parser_fn):
        src_cfg = sources.get(src_key, {})
        rel_path = src_cfg.get("path", src_key)
        src_dir = vault_path / rel_path
        if not src_dir.exists():
            if verbose:
                print(f"[WARN] Source dir not found: {src_dir}")
            return
        for md_file in sorted(src_dir.rglob("*.md")):
            if verbose:
                print(f"[EXTRACT] {md_file}")
            try:
                result = parser_fn(md_file, vault_path)
                if isinstance(result, tuple):
                    rec, extra = result
                    if extra:  # company name from contact
                        org_id = "org_" + slugify(extra)
                        if org_id not in org_entities:
                            org_entities[org_id] = {"entity": {"id": org_id, "type": "Organization", "properties": {"name": extra}}, "relations": []}
                else:
                    rec = result
                records.append(rec)
            except Exception as e:
                print(f"[ERROR] {md_file}: {e}")

    process_dir("contacts", parse_contact)
    process_dir("clients", parse_client)
    process_dir("team", parse_team)
    process_dir("projects", parse_project)

    all_records = list(org_entities.values()) + records

    if dry_run:
        print("[DRY-RUN] Would write the following to ontology:")
        for r in all_records:
            print(json.dumps(r))
        return

    storage_path.mkdir(parents=True, exist_ok=True)
    graph_file = storage_path / "graph.jsonl"
    with open(graph_file, "w") as f:
        for r in all_records:
            f.write(json.dumps(r) + "\n")
    print(f"[OK] Wrote {len(all_records)} records to {graph_file}")

    # write schema
    schema = {
        "entities": ["Person", "Organization", "Project", "Event", "Task"],
        "relationships": ["works_at", "assigned_to", "met_at", "for_client", "reports_to", "has_task", "blocks", "has_project", "has_team_member", "primary_contact"]
    }
    with open(storage_path / "schema.yaml", "w") as f:
        yaml.dump(schema, f)
    print(f"[OK] Schema written.")

def run_analyze():
    config, _ = load_config()
    vault_path = Path(config["obsidian"]["vault_path"])
    storage_path = Path(config["ontology"]["storage_path"])
    graph_file = storage_path / "graph.jsonl"
    if not graph_file.exists():
        print("[ERROR] graph.jsonl not found. Run extract first.")
        sys.exit(1)

    records = []
    with open(graph_file) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    insights = []
    persons = [r for r in records if r["entity"]["type"] == "Person"]
    projects = [r for r in records if r["entity"]["type"] == "Project"]
    orgs = [r for r in records if r["entity"]["type"] == "Organization"]

    # Missing email
    missing_email = [p["entity"]["properties"]["name"] for p in persons
                     if "email" not in p["entity"]["properties"]]
    for n in missing_email:
        insights.append(f"Person '{n}' is missing email address")

    # Missing deadline
    missing_deadline = [p["entity"]["properties"]["name"] for p in projects
                        if "deadline" not in p["entity"]["properties"]]
    for n in missing_deadline:
        insights.append(f"Project '{n}' is missing deadline")

    # Missing contract value
    missing_cv = [o["entity"]["properties"]["name"] for o in orgs
                  if "contract_value" not in o["entity"]["properties"]]
    for n in missing_cv:
        insights.append(f"Organization '{n}' is missing contract_value")

    # Broken project references
    all_project_ids = {r["entity"]["id"] for r in projects}
    all_relations = []
    for r in records:
        all_relations.extend(r.get("relations", []))
    assigned_project_ids = {rel["to"] for rel in all_relations if rel["rel"] in ("assigned_to", "has_project")}
    broken = assigned_project_ids - all_project_ids
    for pid in sorted(broken):
        insights.append(f"Broken project reference: '{pid}' referenced but no project entity found")

    # Team members with no assignments
    team_with_assignments = {rel["from"] for rel in all_relations if rel["rel"] == "assigned_to"}
    team_persons = [p for p in persons if p["entity"]["properties"].get("role") == "team_member"]
    for tp in team_persons:
        if tp["entity"]["id"] not in team_with_assignments:
            insights.append(f"Team member '{tp['entity']['properties']['name']}' has no assigned projects")

    # Store insights
    insights_path = vault_path / "ontology-sync" / "feedback"
    insights_path.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    daily_file = insights_path / "daily-insights.md"
    with open(daily_file, "w") as f:
        f.write(f"# Daily Insights - {today}\n\n")
        for ins in insights:
            f.write(f"- {ins}\n")
    print(f"[OK] {len(insights)} insights written to {daily_file}")
    return insights

def run_feedback():
    config, _ = load_config()
    vault_path = Path(config["obsidian"]["vault_path"])
    insights_path = vault_path / "ontology-sync" / "feedback"
    daily_file = insights_path / "daily-insights.md"
    if not daily_file.exists():
        print("[ERROR] daily-insights.md not found. Run analyze first.")
        sys.exit(1)

    insights = []
    with open(daily_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith('- '):
                insights.append(line[2:])

    missing_info = [i for i in insights if 'missing' in i.lower()]
    broken_refs = [i for i in insights if 'broken' in i.lower()]
    no_assign = [i for i in insights if 'no assigned' in i.lower()]

    today = datetime.date.today().isoformat()
    feedback_file = insights_path / "weekly-feedback.md"
    with open(feedback_file, "w") as f:
        f.write(f"# Sync Feedback - {today}\n\n")
        f.write(f"## Missing Information ({len(missing_info)} items)\n")
        for item in missing_info:
            f.write(f"- [ ] {item}\n")
        f.write(f"\n## Broken References ({len(broken_refs)} items)\n")
        for item in broken_refs:
            f.write(f"- [ ] {item}\n")
        f.write(f"\n## Unassigned Team Members ({len(no_assign)} items)\n")
        for item in no_assign:
            f.write(f"- [ ] {item}\n")
        f.write("\n## Relationship Insights\n")
        f.write("- See daily-insights.md for full details\n")
        f.write("\n## Template Suggestions\n")
        if missing_info:
            f.write("- Ensure all contact/team templates include Email field\n")
            f.write("- Ensure all project templates include Deadline field\n")

    print(f"[OK] Feedback report written to {feedback_file}")

    # Also write suggestions.md
    suggestions_file = insights_path / "suggestions.md"
    with open(suggestions_file, "w") as f:
        f.write(f"# Suggestions - {today}\n\n")
        for item in insights:
            f.write(f"- [ ] {item}\n")
    print(f"[OK] Suggestions written to {suggestions_file}")

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    cmd = args[0]
    dry_run = '--dry-run' in args
    verbose = '--verbose' in args
    if cmd == 'extract':
        run_extract(dry_run=dry_run, verbose=verbose)
    elif cmd == 'analyze':
        run_analyze()
    elif cmd == 'feedback':
        run_feedback()
    elif cmd == 'apply-feedback':
        print("[INFO] apply-feedback: safety backup + apply suggestions (not implemented in this version)")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == '__main__':
    main()
''')
sync_py.chmod(0o755)

# ── init.py ──────────────────────────────────────────────────────────────────
init_py = skill_dir / "init.py"
init_py.write_text(r'''#!/usr/bin/env python3
"""Initialize obsidian-ontology-sync directory structure."""
import sys
import yaml
from pathlib import Path

CONFIG_SEARCH_PATHS = [
    "/workspace/pkm_vault/ontology-sync/config.yaml",
    "/root/life/pkm/ontology-sync/config.yaml",
    "config.yaml",
]

def load_config():
    for p in CONFIG_SEARCH_PATHS:
        if Path(p).exists():
            with open(p) as f:
                return yaml.safe_load(f), p
    raise FileNotFoundError(f"config.yaml not found. Searched: {CONFIG_SEARCH_PATHS}")

def main():
    config, config_path = load_config()
    vault_path = Path(config["obsidian"]["vault_path"])
    storage_path = Path(config["ontology"]["storage_path"])
    feedback_path = Path(config["feedback"]["output_path"])
    logs_path = vault_path / "ontology-sync" / "logs"

    for d in [storage_path, feedback_path, logs_path]:
        d.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created: {d}")

    print(f"[OK] Initialized from config at: {config_path}")

if __name__ == '__main__':
    main()
''')
init_py.chmod(0o755)

# ── setup-cron.py ─────────────────────────────────────────────────────────────
setup_cron_py = skill_dir / "setup-cron.py"
setup_cron_py.write_text(r'''#!/usr/bin/env python3
"""Setup cron jobs for obsidian-ontology-sync."""
print("✓ Sync every 3 hours (0 */3 * * *)")
print("✓ Daily analysis at 9 AM (0 9 * * *)")
print("✓ Weekly feedback Monday 10 AM (0 10 * * MON)")
print("[OK] Cron jobs registered (mock mode in sandbox)")
''')
setup_cron_py.chmod(0o755)

# ── debug.py ──────────────────────────────────────────────────────────────────
debug_py = skill_dir / "debug.py"
debug_py.write_text(r'''#!/usr/bin/env python3
"""Debug extraction for a specific file."""
import sys
print(f"[DEBUG] Would analyze: {sys.argv}")
''')
debug_py.chmod(0o755)

# ── ontology.py (query tool) ──────────────────────────────────────────────────
ontology_py = ontology_script_dir / "ontology.py"
ontology_py.write_text(r'''#!/usr/bin/env python3
"""Ontology query tool."""
import sys, json
from pathlib import Path

GRAPH_PATHS = [
    "/workspace/pkm_vault/memory/ontology/graph.jsonl",
    "/root/life/pkm/memory/ontology/graph.jsonl",
]

def load_graph():
    for p in GRAPH_PATHS:
        if Path(p).exists():
            records = []
            with open(p) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            return records
    raise FileNotFoundError(f"graph.jsonl not found in {GRAPH_PATHS}")

def main():
    args = sys.argv[1:]
    records = load_graph()
    entity_type = None
    for i, a in enumerate(args):
        if a == '--type' and i+1 < len(args):
            entity_type = args[i+1]
    if entity_type:
        filtered = [r for r in records if r['entity']['type'] == entity_type]
        print(json.dumps(filtered, indent=2))
    else:
        print(json.dumps(records, indent=2))

if __name__ == '__main__':
    main()
''')
ontology_py.chmod(0o755)

# ─── PKM Vault Structure ──────────────────────────────────────────────────────
vault = WORKSPACE / "pkm_vault"

# ── references/contacts/ ──────────────────────────────────────────────────────
contacts_dir = vault / "references" / "contacts"
contacts_dir.mkdir(parents=True, exist_ok=True)

(contacts_dir / "Alice_Johnson.md").write_text("""\
# Alice Johnson

**Email:** alice@nexusanalytics.com
**Phone:** +1-555-0101
**Company:** Nexus Analytics
**Met At:** Strategy Summit 2026
**Projects:** [[Project Phoenix]], [[Project Meridian]]

## Notes
Sharp analytical mind. Prefers async communication. Follow up on pricing proposal.
""")

(contacts_dir / "Bob_Chen.md").write_text("""\
# Bob Chen

**Phone:** +1-555-0202
**Company:** Vertex Solutions
**Met At:** Strategy Summit 2026
**Projects:** [[Project Phoenix]]

## Notes
Strong engineering background. Needs intro to our data team.
""")

(contacts_dir / "Carol_Nakamura.md").write_text("""\
# Carol Nakamura

**Email:** carol@brightpath.io
**Company:** BrightPath
**Met At:** FinTech Forum 2025

## Notes
Interested in our compliance module. Warm lead.
""")

# ── references/clients/ ───────────────────────────────────────────────────────
clients_dir = vault / "references" / "clients"
clients_dir.mkdir(parents=True, exist_ok=True)

(clients_dir / "Nexus_Analytics.md").write_text("""\
# Nexus Analytics

**Contract Value:** $520,000
**Projects:** [[Project Phoenix]], [[Project Meridian]]
**Primary Contact:** Alice Johnson

## Background
Enterprise data consultancy. Renewed contract in Q1 2026.
""")

(clients_dir / "Vertex_Solutions.md").write_text("""\
# Vertex Solutions

**Projects:** [[Project Phoenix]]
**Primary Contact:** Bob Chen

## Background
Mid-market software firm. Pilot engagement in progress.
""")

# ── references/team/ ──────────────────────────────────────────────────────────
team_dir = vault / "references" / "team"
team_dir.mkdir(parents=True, exist_ok=True)

(team_dir / "David_Park.md").write_text("""\
# David Park

**Email:** david@ourconsulting.com
**Phone:** +1-555-0303
**Reports To:** Sarah Okonkwo
**Assignments:** [[Project Phoenix]], [[Project Meridian]]
**Response Pattern:** proactive

## Background
Lead architect. 5 years with the firm.
""")

(team_dir / "Eve_Torres.md").write_text("""\
# Eve Torres

**Phone:** +1-555-0404
**Reports To:** Sarah Okonkwo
**Assignments:** [[Project Meridian]]
**Response Pattern:** reactive

## Background
Data analyst. Joined Q3 2025.
""")

(team_dir / "Frank_Liu.md").write_text("""\
# Frank Liu

**Email:** frank@ourconsulting.com
**Response Pattern:** proactive

## Background
Junior consultant. On-boarding in progress. No project assigned yet.
""")

# ── projects/ ─────────────────────────────────────────────────────────────────
projects_dir = vault / "projects"
projects_dir.mkdir(parents=True, exist_ok=True)

(projects_dir / "Project_Phoenix.md").write_text("""\
# Project Phoenix

**Status:** active
**Client:** Nexus Analytics
**Value:** $320,000
**Deadline:** 2026-09-30
**Team:** [[David Park]], [[Eve Torres]]

## Scope
Full data platform migration. Phase 2 starts July.
""")

(projects_dir / "Project_Meridian.md").write_text("""\
# Project Meridian

**Status:** active
**Client:** Nexus Analytics
**Value:** $200,000
**Team:** [[David Park]], [[Eve Torres]]

## Scope
Analytics dashboard rollout. Client review pending.
""")

# ── daily-status/ ─────────────────────────────────────────────────────────────
ds_dir = vault / "daily-status" / "2026-06-10"
ds_dir.mkdir(parents=True, exist_ok=True)

(ds_dir / "standup.md").write_text("""\
# Standup 2026-06-10

## David Park
- Completed: API schema review for Project Phoenix
- Next: Kick-off call with Nexus Analytics stakeholders
- Blockers: None

## Eve Torres
- Completed: Dashboard prototype v2
- Next: Client demo prep for Project Meridian
- Blockers: Missing data access credentials from client

## Frank Liu
- Completed: Onboarding documentation
- Next: Shadow David on Project Phoenix
- Blockers: Awaiting project assignment
""")

# ── distractor files ──────────────────────────────────────────────────────────
inbox = vault / "inbox"
inbox.mkdir(exist_ok=True)
(inbox / "random_idea.md").write_text("# Random Idea\nMaybe automate weekly reports.\n")
(inbox / "reading_list.md").write_text("# Reading List\n- The Lean Startup\n- Zero to One\n")

archive = vault / "archive" / "2025"
archive.mkdir(parents=True, exist_ok=True)
(archive / "old_project_notes.md").write_text("# Old Project (Closed)\nCompleted Dec 2025.\n")
(archive / "Q4_retro.md").write_text("# Q4 Retrospective\nGood quarter overall.\n")

templates = vault / "templates"
templates.mkdir(exist_ok=True)
(templates / "contact_template.md").write_text("# {{name}}\n\n**Email:**\n**Company:**\n")
(templates / "project_template.md").write_text("# {{project_name}}\n\n**Client:**\n**Status:**\n")
(templates / "daily_template.md").write_text("# {{date}}\n\n## Updates\n")

notes = vault / "notes"
notes.mkdir(exist_ok=True)
(notes / "meeting_prep.md").write_text("# Meeting Prep\nReview Q2 metrics before call.\n")
(notes / "strategy_brainstorm.md").write_text("# Strategy Notes\nExpand to healthcare vertical?\n")

# ── a partial/broken config to mislead naive agents ──────────────────────────
broken_cfg = vault / "ontology-sync"
broken_cfg.mkdir(parents=True, exist_ok=True)
(broken_cfg / "config.yaml.bak").write_text("""\
# OLD / INCOMPLETE — do not use
obsidian:
  vault: /wrong/path
ontology:
  path: /wrong/ontology
""")

print("Workspace scaffold complete.")
print(f"Vault: {vault}")
print(f"Skill scripts: {skill_dir}")