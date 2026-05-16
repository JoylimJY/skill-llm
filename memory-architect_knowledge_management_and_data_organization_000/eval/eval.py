import sys
import json
import re
from pathlib import Path

def load_text(p):
    try:
        return Path(p).read_text(encoding="utf-8")
    except Exception as e:
        return None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    ws = Path(workspace)
    checks = []

    # ── Locate the workspace subdirectory ──────────────────────────────────
    # Agent may write to workspace/ or workspace/workspace/
    # Determine the actual root containing MEMORY.md
    candidates = list(ws.rglob("MEMORY.md"))
    if not candidates:
        checks.append(check("MEMORY.md exists", False, "MEMORY.md not found anywhere in workspace"))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    # Prefer the highest-level one
    candidates.sort(key=lambda p: len(p.parts))
    memory_path = candidates[0]
    root = memory_path.parent
    checks.append(check("MEMORY.md exists", True, f"Found at {memory_path}"))

    # ── CHECK 1: MEMORY.md line count ≤ 30 ────────────────────────────────
    memory_text = load_text(memory_path) or ""
    memory_lines = [l for l in memory_text.splitlines()]
    line_count = len(memory_lines)
    c1_passed = line_count <= 30
    checks.append(check(
        "MEMORY.md router ≤30 lines",
        c1_passed,
        f"MEMORY.md has {line_count} lines (max 30)"
    ))

    # ── CHECK 2: MEMORY.md preserves system directives ────────────────────
    has_no_reply = "NO_REPLY" in memory_text
    has_heartbeat = "HEARTBEAT" in memory_text or "heartbeat" in memory_text.lower()
    c2_passed = has_no_reply and has_heartbeat
    checks.append(check(
        "MEMORY.md preserves system directives (NO_REPLY + HEARTBEAT)",
        c2_passed,
        f"NO_REPLY found: {has_no_reply}, HEARTBEAT found: {has_heartbeat}"
    ))

    # ── CHECK 3: MEMORY.md is a router (no project-specific content) ──────
    # Should not contain deal-specific addresses, prices, emails of external contacts
    project_specific_markers = [
        "789 Cascade", "44 Birchwood", "1,175,000", "2,340,000",
        "mwebb@gmail.com", "dhargrove@trustlaw.com",
        "TCW-2025-0814", "Under contract"
    ]
    found_markers = [m for m in project_specific_markers if m in memory_text]
    c3_passed = len(found_markers) == 0
    checks.append(check(
        "MEMORY.md contains zero project-specific content",
        c3_passed,
        f"Found project-specific content: {found_markers}" if found_markers else "Clean router"
    ))

    # ── CHECK 4: MEMORY.md references all three tier files ────────────────
    refs_protocols = "protocols" in memory_text.lower()
    refs_active = "active" in memory_text.lower()
    refs_archive = "archive" in memory_text.lower()
    refs_ontology = "ontology" in memory_text.lower() or "graph" in memory_text.lower()
    c4_passed = refs_protocols and refs_active and refs_archive and refs_ontology
    checks.append(check(
        "MEMORY.md references all tiers + ontology",
        c4_passed,
        f"protocols:{refs_protocols} active:{refs_active} archive:{refs_archive} ontology/graph:{refs_ontology}"
    ))

    # ── CHECK 5: protocols.md exists and has correct structure ─────────────
    proto_candidates = list(root.rglob("protocols.md"))
    if not proto_candidates:
        proto_candidates = list(ws.rglob("protocols.md"))
    proto_exists = len(proto_candidates) > 0
    checks.append(check("protocols.md exists", proto_exists, 
                         f"Found at {proto_candidates[0]}" if proto_exists else "Not found"))
    
    proto_text = ""
    if proto_exists:
        proto_text = load_text(proto_candidates[0]) or ""
        proto_lines = len(proto_text.splitlines())
        c5b_passed = proto_lines <= 100
        checks.append(check(
            "protocols.md ≤100 lines",
            c5b_passed,
            f"protocols.md has {proto_lines} lines"
        ))
        # Should contain actual workflow procedures (copy-pasteable commands)
        has_commands = ("python scripts/" in proto_text or 
                        "scripts/" in proto_text or
                        "mls_validator" in proto_text or
                        "offer_packager" in proto_text or
                        "weekly_digest" in proto_text)
        checks.append(check(
            "protocols.md contains copy-pasteable commands/workflows",
            has_commands,
            "Found script commands" if has_commands else "No script commands found"
        ))
        # Should NOT contain active project state
        active_leakage = any(x in proto_text for x in [
            "789 Cascade", "Marcus Webb", "Under contract", "Riverside", "Oakmont"
        ])
        checks.append(check(
            "protocols.md has no project-specific state",
            not active_leakage,
            "Clean" if not active_leakage else "Contains project-specific content"
        ))

    # ── CHECK 6: active.md exists, line count ≤ 80, has Waiting On ────────
    active_candidates = list(root.rglob("active.md"))
    if not active_candidates:
        active_candidates = list(ws.rglob("active.md"))
    active_exists = len(active_candidates) > 0
    checks.append(check("active.md exists", active_exists,
                         f"Found at {active_candidates[0]}" if active_exists else "Not found"))
    
    active_text = ""
    if active_exists:
        active_text = load_text(active_candidates[0]) or ""
        active_lines = len(active_text.splitlines())
        c6b_passed = active_lines <= 80
        checks.append(check(
            "active.md ≤80 lines",
            c6b_passed,
            f"active.md has {active_lines} lines"
        ))
        has_waiting_on = "Waiting On" in active_text or "waiting on" in active_text.lower()
        checks.append(check(
            "active.md contains 'Waiting On' section",
            has_waiting_on,
            "Waiting On section present" if has_waiting_on else "Missing Waiting On section"
        ))
        # Should contain current active deals
        has_active_deals = any(x in active_text for x in [
            "Riverside", "Oakmont", "Sunridge", "cascade", "birchwood"
        ])
        checks.append(check(
            "active.md contains current active deals",
            has_active_deals,
            "Active deals present" if has_active_deals else "No active deal content found"
        ))

    # ── CHECK 7: archive.md exists and has completed deals + contacts ──────
    archive_candidates = list(root.rglob("archive.md"))
    if not archive_candidates:
        archive_candidates = list(ws.rglob("archive.md"))
    archive_exists = len(archive_candidates) > 0
    checks.append(check("archive.md exists", archive_exists,
                         f"Found at {archive_candidates[0]}" if archive_exists else "Not found"))
    
    archive_text = ""
    if archive_exists:
        archive_text = load_text(archive_candidates[0]) or ""
        # Should have completed deals
        has_closed = any(x in archive_text for x in [
            "Elmwood", "Harbor View", "Pinebrook", "CLOSED", "Closed"
        ])
        checks.append(check(
            "archive.md contains completed deals",
            has_closed,
            "Closed deals found" if has_closed else "No closed deals found"
        ))
        # Should have people directory / contact data (headers/tables)
        has_contacts = any(x in archive_text for x in [
            "Okonkwo", "Sandra", "Tom Chen", "People", "Contacts", "Directory"
        ])
        checks.append(check(
            "archive.md contains contact/people reference data",
            has_contacts,
            "Contact data found" if has_contacts else "No contact data found"
        ))

    # ── CHECK 8: graph.jsonl exists and has valid JSONL entries ───────────
    graph_candidates = list(root.rglob("graph.jsonl"))
    if not graph_candidates:
        graph_candidates = list(ws.rglob("graph.jsonl"))
    graph_exists = len(graph_candidates) > 0
    checks.append(check("graph.jsonl exists", graph_exists,
                         f"Found at {graph_candidates[0]}" if graph_exists else "Not found"))

    graph_text = ""
    valid_entries = []
    parse_errors = []
    
    if graph_exists:
        graph_text = load_text(graph_candidates[0]) or ""
        lines = [l.strip() for l in graph_text.splitlines() if l.strip()]
        
        for i, line in enumerate(lines):
            try:
                obj = json.loads(line)
                valid_entries.append(obj)
            except json.JSONDecodeError as e:
                parse_errors.append(f"Line {i+1}: {e}")
        
        c8b_passed = len(parse_errors) == 0 and len(valid_entries) > 0
        checks.append(check(
            "graph.jsonl is valid JSONL (all lines parseable)",
            c8b_passed,
            f"{len(valid_entries)} valid entries, {len(parse_errors)} errors: {parse_errors[:3]}"
        ))

        # Check op fields
        ops = [e.get("op") for e in valid_entries]
        has_create = "create" in ops
        has_relate = "relate" in ops
        checks.append(check(
            "graph.jsonl has 'create' and 'relate' op types",
            has_create and has_relate,
            f"ops found: {set(ops)}"
        ))

        # Check ID conventions
        all_ids = []
        for e in valid_entries:
            if e.get("op") == "create" and "entity" in e:
                eid = e["entity"].get("id", "")
                all_ids.append(eid)
        
        valid_prefixes = ("p_", "grp_", "org_", "proj_", "prop_", "loc_")
        valid_id_entries = [i for i in all_ids if i.startswith(valid_prefixes)]
        c8c_passed = len(valid_id_entries) >= len(all_ids) * 0.8 if all_ids else False
        checks.append(check(
            "graph.jsonl entity IDs follow prefix conventions (p_, grp_/org_, proj_, prop_/loc_)",
            c8c_passed,
            f"{len(valid_id_entries)}/{len(all_ids)} IDs have valid prefixes. Sample: {all_ids[:5]}"
        ))

        # Check relation types
        valid_rel_types = {
            "member_of", "owns", "collaborates_on", "interested_in",
            "guides", "uses", "listed_by", "located_at"
        }
        relate_entries = [e for e in valid_entries if e.get("op") == "relate"]
        invalid_rels = [e.get("rel") for e in relate_entries if e.get("rel") not in valid_rel_types]
        c8d_passed = len(invalid_rels) == 0 and len(relate_entries) >= 2
        checks.append(check(
            "graph.jsonl 'relate' entries use valid relation types only",
            c8d_passed,
            f"{len(relate_entries)} relate entries, invalid rels: {invalid_rels[:5]}"
        ))

        # Check entity types coverage
        entity_types = set()
        for e in valid_entries:
            if e.get("op") == "create" and "entity" in e:
                entity_types.add(e["entity"].get("type", ""))
        has_person = "Person" in entity_types
        has_org = any(t in entity_types for t in ["Organization", "Org"])
        has_project = "Project" in entity_types
        c8e_passed = has_person and (has_org or has_project)
        checks.append(check(
            "graph.jsonl covers Person and Org/Project entity types",
            c8e_passed,
            f"Entity types found: {entity_types}"
        ))

        # Minimum entity count — should have extracted at least 8 people/orgs
        min_entities = len([e for e in valid_entries if e.get("op") == "create"]) >= 8
        checks.append(check(
            "graph.jsonl has at least 8 entity create entries",
            min_entities,
            f"Found {len([e for e in valid_entries if e.get('op') == 'create'])} create entries"
        ))

        # Check timestamps present
        has_timestamps = all(e.get("timestamp") for e in valid_entries)
        checks.append(check(
            "graph.jsonl all entries have timestamp field",
            has_timestamps,
            "All entries have timestamps" if has_timestamps else "Some entries missing timestamp"
        ))

    # ── SCORE CALCULATION ────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0

    # Hard gate: must pass the critical structural checks
    critical_checks = [
        "MEMORY.md router ≤30 lines",
        "active.md contains 'Waiting On' section",
        "graph.jsonl is valid JSONL (all lines parseable)",
        "graph.jsonl entity IDs follow prefix conventions (p_, grp_/org_, proj_, prop_/loc_)",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    overall_passed = score >= 0.75 and critical_passed

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))