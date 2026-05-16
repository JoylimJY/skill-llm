#!/usr/bin/env python3
"""Evaluation script for obsidian-ontology-sync task."""

import sys
import json
import re
from pathlib import Path

def load_jsonl(path):
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    vault = workspace / "pkm_vault"

    checks = []
    total_score = 0.0
    max_score = 0.0

    # ── CHECK 1: config.yaml exists and has correct vault_path ────────────────
    max_score += 1.0
    config_path = vault / "ontology-sync" / "config.yaml"
    try:
        import yaml
        with open(config_path) as f:
            cfg = yaml.safe_load(f)

        vault_path_in_cfg = cfg.get("obsidian", {}).get("vault_path", "")
        correct_vault = str(vault) in str(vault_path_in_cfg) or str(vault_path_in_cfg) in str(vault)
        if correct_vault:
            checks.append({"name": "config.yaml:vault_path", "passed": True,
                           "detail": f"vault_path correctly set to '{vault_path_in_cfg}'"})
            total_score += 1.0
        else:
            checks.append({"name": "config.yaml:vault_path", "passed": False,
                           "detail": f"vault_path='{vault_path_in_cfg}' does not match expected '{vault}'"})
    except Exception as e:
        checks.append({"name": "config.yaml:vault_path", "passed": False,
                       "detail": f"Could not load config.yaml: {e}"})

    # ── CHECK 2: config.yaml has correct ontology.storage_path ───────────────
    max_score += 1.0
    try:
        storage_path_in_cfg = cfg.get("ontology", {}).get("storage_path", "")
        expected_storage = str(vault / "memory" / "ontology")
        correct_storage = expected_storage in str(storage_path_in_cfg) or str(storage_path_in_cfg) in expected_storage
        if correct_storage:
            checks.append({"name": "config.yaml:ontology.storage_path", "passed": True,
                           "detail": f"storage_path='{storage_path_in_cfg}'"})
            total_score += 1.0
        else:
            checks.append({"name": "config.yaml:ontology.storage_path", "passed": False,
                           "detail": f"storage_path='{storage_path_in_cfg}' expected to contain '{expected_storage}'"})
    except Exception as e:
        checks.append({"name": "config.yaml:ontology.storage_path", "passed": False,
                       "detail": f"Error reading storage_path: {e}"})

    # ── CHECK 3: config.yaml has sources section with contacts/team/clients ──
    max_score += 1.0
    try:
        sources = cfg.get("obsidian", {}).get("sources", {})
        has_contacts = "contacts" in sources
        has_team = "team" in sources
        has_clients = "clients" in sources
        has_projects = "projects" in sources
        all_present = has_contacts and has_team and has_clients
        checks.append({
            "name": "config.yaml:sources_section",
            "passed": all_present,
            "detail": f"contacts={has_contacts}, team={has_team}, clients={has_clients}, projects={has_projects}"
        })
        if all_present:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "config.yaml:sources_section", "passed": False,
                       "detail": f"Error reading sources: {e}"})

    # ── CHECK 4: config.yaml has feedback.output_path ─────────────────────────
    max_score += 0.5
    try:
        feedback_path_in_cfg = cfg.get("feedback", {}).get("output_path", "")
        expected_fb = str(vault / "ontology-sync" / "feedback")
        correct_fb = expected_fb in str(feedback_path_in_cfg) or str(feedback_path_in_cfg) in expected_fb
        checks.append({
            "name": "config.yaml:feedback.output_path",
            "passed": correct_fb,
            "detail": f"feedback.output_path='{feedback_path_in_cfg}'"
        })
        if correct_fb:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "config.yaml:feedback.output_path", "passed": False,
                       "detail": f"Error: {e}"})

    # ── CHECK 5: graph.jsonl exists and has entities ──────────────────────────
    max_score += 1.5
    graph_path = vault / "memory" / "ontology" / "graph.jsonl"
    try:
        records = load_jsonl(graph_path)
        entity_types = {r["entity"]["type"] for r in records}
        has_person = "Person" in entity_types
        has_org = "Organization" in entity_types
        has_project = "Project" in entity_types
        all_types = has_person and has_org and has_project
        checks.append({
            "name": "graph.jsonl:entity_types",
            "passed": all_types,
            "detail": f"Found entity types: {entity_types}"
        })
        if all_types:
            total_score += 1.5
    except Exception as e:
        records = []
        checks.append({"name": "graph.jsonl:entity_types", "passed": False,
                       "detail": f"Could not load graph.jsonl: {e}"})

    # ── CHECK 6: Person entities have correct IDs (slug convention) ───────────
    max_score += 1.0
    try:
        person_ids = {r["entity"]["id"] for r in records if r["entity"]["type"] == "Person"}
        required_ids = {"person_alice_johnson", "person_david_park", "person_eve_torres", "person_frank_liu"}
        found = required_ids & person_ids
        passed = len(found) >= 3
        checks.append({
            "name": "graph.jsonl:person_ids_slug_convention",
            "passed": passed,
            "detail": f"Required IDs found: {found} (need ≥3 of {required_ids})"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "graph.jsonl:person_ids_slug_convention", "passed": False,
                       "detail": f"Error: {e}"})

    # ── CHECK 7: works_at relations extracted (contacts → orgs) ──────────────
    max_score += 1.0
    try:
        all_relations = []
        for r in records:
            all_relations.extend(r.get("relations", []))
        works_at_rels = [rel for rel in all_relations if rel["rel"] == "works_at"]
        has_alice_nexus = any(
            rel["from"] == "person_alice_johnson" and "nexus" in rel["to"]
            for rel in works_at_rels
        )
        has_some_works_at = len(works_at_rels) >= 2
        passed = has_some_works_at and has_alice_nexus
        checks.append({
            "name": "graph.jsonl:works_at_relations",
            "passed": passed,
            "detail": f"works_at count={len(works_at_rels)}, alice→nexus={has_alice_nexus}"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "graph.jsonl:works_at_relations", "passed": False,
                       "detail": f"Error: {e}"})

    # ── CHECK 8: assigned_to relations extracted ──────────────────────────────
    max_score += 1.0
    try:
        assigned_rels = [rel for rel in all_relations if rel["rel"] == "assigned_to"]
        passed = len(assigned_rels) >= 3
        checks.append({
            "name": "graph.jsonl:assigned_to_relations",
            "passed": passed,
            "detail": f"assigned_to relations found: {len(assigned_rels)}"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "graph.jsonl:assigned_to_relations", "passed": False,
                       "detail": f"Error: {e}"})

    # ── CHECK 9: Bob Chen missing email is in graph (no email property) ───────
    max_score += 0.5
    try:
        bob = next((r for r in records
                    if r["entity"]["type"] == "Person" and
                    "bob" in r["entity"]["id"]), None)
        if bob:
            has_no_email = "email" not in bob["entity"]["properties"]
            checks.append({
                "name": "graph.jsonl:bob_missing_email",
                "passed": has_no_email,
                "detail": f"Bob entity props: {list(bob['entity']['properties'].keys())}"
            })
            if has_no_email:
                total_score += 0.5
        else:
            checks.append({"name": "graph.jsonl:bob_missing_email", "passed": False,
                           "detail": "Bob entity not found in graph"})
    except Exception as e:
        checks.append({"name": "graph.jsonl:bob_missing_email", "passed": False,
                       "detail": f"Error: {e}"})

    # ── CHECK 10: Project Meridian missing deadline in graph ──────────────────
    max_score += 0.5
    try:
        meridian = next((r for r in records
                         if r["entity"]["type"] == "Project" and
                         "meridian" in r["entity"]["id"]), None)
        if meridian:
            no_deadline = "deadline" not in meridian["entity"]["properties"]
            checks.append({
                "name": "graph.jsonl:meridian_missing_deadline",
                "passed": no_deadline,
                "detail": f"Meridian props: {list(meridian['entity']['properties'].keys())}"
            })
            if no_deadline:
                total_score += 0.5
        else:
            checks.append({"name": "graph.jsonl:meridian_missing_deadline", "passed": False,
                           "detail": "Project Meridian entity not found"})
    except Exception as e:
        checks.append({"name": "graph.jsonl:meridian_missing_deadline", "passed": False,
                       "detail": f"Error: {e}"})

    # ── CHECK 11: weekly-feedback.md exists with missing info section ─────────
    max_score += 1.5
    feedback_file = vault / "ontology-sync" / "feedback" / "weekly-feedback.md"
    try:
        fb_text = feedback_file.read_text()
        has_missing_section = "Missing Information" in fb_text or "missing" in fb_text.lower()
        has_email_mention = "email" in fb_text.lower()
        has_deadline_mention = "deadline" in fb_text.lower()
        passed = has_missing_section and has_email_mention and has_deadline_mention
        checks.append({
            "name": "weekly-feedback.md:missing_info",
            "passed": passed,
            "detail": f"has_missing_section={has_missing_section}, email_mentioned={has_email_mention}, deadline_mentioned={has_deadline_mention}"
        })
        if passed:
            total_score += 1.5
    except Exception as e:
        checks.append({"name": "weekly-feedback.md:missing_info", "passed": False,
                       "detail": f"Could not read weekly-feedback.md: {e}"})

    # ── CHECK 12: weekly-feedback.md mentions broken references ───────────────
    max_score += 1.0
    try:
        has_broken = "broken" in fb_text.lower() or "Broken" in fb_text
        # Vertex Solutions has no contract value → missing cv, or broken project ref from contacts
        checks.append({
            "name": "weekly-feedback.md:broken_or_gap_refs",
            "passed": has_broken,
            "detail": f"Broken references section present: {has_broken}"
        })
        if has_broken:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "weekly-feedback.md:broken_or_gap_refs", "passed": False,
                       "detail": f"Error reading feedback file: {e}"})

    # ── CHECK 13: suggestions.md or daily-insights.md exists ─────────────────
    max_score += 0.5
    try:
        suggestions_file = vault / "ontology-sync" / "feedback" / "suggestions.md"
        daily_insights = vault / "ontology-sync" / "feedback" / "daily-insights.md"
        exists = suggestions_file.exists() or daily_insights.exists()
        checks.append({
            "name": "feedback_artifacts:suggestions_or_daily_insights",
            "passed": exists,
            "detail": f"suggestions.md={suggestions_file.exists()}, daily-insights.md={daily_insights.exists()}"
        })
        if exists:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "feedback_artifacts:suggestions_or_daily_insights", "passed": False,
                       "detail": f"Error: {e}"})

    # ── Final scoring ──────────────────────────────────────────────────────────
    score = round(total_score / max_score, 3) if max_score > 0 else 0.0
    passed = score >= 0.75

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()