#!/usr/bin/env python3
"""
Evaluation script for obsidian-ontology-sync task.
Checks:
1. config.yaml exists at correct path with required fields
2. graph.jsonl written to correct ontology storage path
3. Expected Person entities extracted (Alice Johnson, Bob Martinez, Carol Lee, Priya Sharma, Jin Park)
4. works_at relations extracted for contacts
5. Feedback files exist (weekly-feedback.md, suggestions.md, daily-insights.md)
6. Feedback correctly mentions missing emails (Bob Martinez, Jin Park)
7. Feedback mentions broken project references (project_gamma, project_delta)
8. config.yaml schedule matches SKILL.md cron patterns
"""
import sys
import json
import re
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def load_jsonl(path):
    records = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    except Exception as e:
        return None, str(e)
    return records, None


def main(workspace):
    checks = []
    total_score = 0.0

    ws = Path(workspace)
    # The vault is /root/life/pkm which is symlinked from workspace/life/pkm
    vault = Path("/root/life/pkm")
    if not vault.exists():
        vault = ws / "life" / "pkm"

    # ── Check 1: config.yaml exists at correct path ───────────────────────────
    config_path = vault / "ontology-sync" / "config.yaml"
    config_ok = False
    cfg = {}
    try:
        if config_path.exists():
            if YAML_AVAILABLE:
                with open(config_path) as f:
                    cfg = yaml.safe_load(f) or {}
            else:
                cfg = {}
            config_ok = True
            detail = f"Found config.yaml at {config_path}"
        else:
            # Try the .bak path - should NOT be used
            detail = f"config.yaml NOT found at {config_path}"
    except Exception as e:
        detail = f"Error reading config.yaml: {e}"

    checks.append({"name": "config_yaml_exists_at_correct_path", "passed": config_ok, "detail": detail})
    if config_ok:
        total_score += 0.10

    # ── Check 2: config.yaml has required vault_path field ───────────────────
    vault_path_correct = False
    try:
        vp = cfg.get("obsidian", {}).get("vault_path", "")
        vault_path_correct = vp in ["/root/life/pkm", str(vault)]
        detail = f"vault_path = '{vp}'"
    except Exception as e:
        detail = f"Error checking vault_path: {e}"
    checks.append({"name": "config_has_correct_vault_path", "passed": vault_path_correct, "detail": detail})
    if vault_path_correct:
        total_score += 0.05

    # ── Check 3: config.yaml has ontology storage_path ───────────────────────
    storage_path_correct = False
    try:
        sp = cfg.get("ontology", {}).get("storage_path", "")
        storage_path_correct = sp in ["/root/life/pkm/memory/ontology", str(vault / "memory" / "ontology")]
        detail = f"ontology.storage_path = '{sp}'"
    except Exception as e:
        detail = f"Error checking storage_path: {e}"
    checks.append({"name": "config_has_ontology_storage_path", "passed": storage_path_correct, "detail": detail})
    if storage_path_correct:
        total_score += 0.05

    # ── Check 4: config.yaml has correct cron schedules ──────────────────────
    schedules_ok = False
    try:
        schedule = cfg.get("schedule", {})
        si = schedule.get("sync_interval", "")
        ad = schedule.get("analyze_daily", "")
        fw = schedule.get("feedback_weekly", "")
        schedules_ok = (
            si == "0 */3 * * *" and
            ad == "0 9 * * *" and
            fw == "0 10 * * MON"
        )
        detail = f"sync_interval='{si}', analyze_daily='{ad}', feedback_weekly='{fw}'"
    except Exception as e:
        detail = f"Error checking schedule: {e}"
    checks.append({"name": "config_has_correct_cron_schedules", "passed": schedules_ok, "detail": detail})
    if schedules_ok:
        total_score += 0.10

    # ── Check 5: graph.jsonl exists at ontology storage path ─────────────────
    # Determine actual storage path from config
    storage_dir = Path("/root/life/pkm/memory/ontology")
    if cfg and "ontology" in cfg:
        sp = cfg["ontology"].get("storage_path", "")
        if sp:
            storage_dir = Path(sp)
    graph_file = storage_dir / "graph.jsonl"
    graph_exists = graph_file.exists()
    detail = f"graph.jsonl at {graph_file}: {'found' if graph_exists else 'NOT FOUND'}"
    checks.append({"name": "graph_jsonl_written_to_correct_path", "passed": graph_exists, "detail": detail})
    if graph_exists:
        total_score += 0.10

    # ── Check 6: Person entities extracted ───────────────────────────────────
    expected_people = {
        "person_alice_johnson": "Alice Johnson",
        "person_bob_martinez": "Bob Martinez",
        "person_carol_lee": "Carol Lee",
        "person_priya_sharma": "Priya Sharma",
        "person_jin_park": "Jin Park",
    }
    people_found = {}
    records = []
    if graph_exists:
        records, err = load_jsonl(graph_file)
        if records is None:
            records = []
        for rec in records:
            ent = rec.get("entity")
            if ent and ent.get("type") == "Person":
                people_found[ent["id"]] = ent

    found_ids = set(people_found.keys())
    expected_ids = set(expected_people.keys())
    people_ok = expected_ids.issubset(found_ids)
    missing = expected_ids - found_ids
    extra = found_ids - expected_ids
    detail = f"Found: {sorted(found_ids)}. Missing: {sorted(missing)}"
    checks.append({"name": "person_entities_extracted", "passed": people_ok, "detail": detail})
    if people_ok:
        total_score += 0.10

    # ── Check 7: Organization entities extracted ──────────────────────────────
    expected_orgs = {"org_acme_corp", "org_techhub"}
    orgs_found = set()
    if records:
        for rec in records:
            ent = rec.get("entity")
            if ent and ent.get("type") == "Organization":
                orgs_found.add(ent["id"])
    orgs_ok = expected_orgs.issubset(orgs_found)
    detail = f"Orgs found: {sorted(orgs_found)}. Expected: {sorted(expected_orgs)}"
    checks.append({"name": "organization_entities_extracted", "passed": orgs_ok, "detail": detail})
    if orgs_ok:
        total_score += 0.10

    # ── Check 8: works_at relations extracted ─────────────────────────────────
    works_at_rels = []
    if records:
        for rec in records:
            for r in rec.get("relations", []):
                if r.get("rel") == "works_at":
                    works_at_rels.append((r["from"], r["to"]))

    expected_works_at = [
        ("person_alice_johnson", "org_acme_corp"),
        ("person_bob_martinez", "org_techhub"),
    ]
    works_at_ok = all(pair in works_at_rels for pair in expected_works_at)
    detail = f"works_at relations: {works_at_rels}. Expected to contain: {expected_works_at}"
    checks.append({"name": "works_at_relations_extracted", "passed": works_at_ok, "detail": detail})
    if works_at_ok:
        total_score += 0.10

    # ── Check 9: team members have role=team_member ───────────────────────────
    team_ids = {"person_priya_sharma", "person_marcus_wells", "person_jin_park"}
    team_roles_ok = True
    missing_role = []
    if records:
        for rec in records:
            ent = rec.get("entity")
            if ent and ent.get("id") in team_ids:
                if ent.get("properties", {}).get("role") != "team_member":
                    team_roles_ok = False
                    missing_role.append(ent["id"])
    detail = f"Team members with wrong/missing role: {missing_role}"
    checks.append({"name": "team_members_have_role_team_member", "passed": team_roles_ok, "detail": detail})
    if team_roles_ok:
        total_score += 0.05

    # ── Check 10: feedback directory and files exist ──────────────────────────
    feedback_path_cfg = cfg.get("feedback", {}).get("output_path", "") if cfg else ""
    feedback_dirs = [
        Path(feedback_path_cfg) if feedback_path_cfg else None,
        vault / "ontology-sync" / "feedback",
    ]
    feedback_dir = None
    for fd in feedback_dirs:
        if fd and fd.exists():
            feedback_dir = fd
            break

    feedback_files_needed = ["weekly-feedback.md", "suggestions.md", "daily-insights.md"]
    feedback_found = {}
    if feedback_dir:
        for fn in feedback_files_needed:
            fp = feedback_dir / fn
            feedback_found[fn] = fp.exists()
    else:
        feedback_found = {fn: False for fn in feedback_files_needed}

    all_feedback_present = all(feedback_found.values())
    detail = f"Feedback dir: {feedback_dir}. Files: {feedback_found}"
    checks.append({"name": "feedback_files_exist", "passed": all_feedback_present, "detail": detail})
    if all_feedback_present:
        total_score += 0.10

    # ── Check 11: Feedback mentions missing emails (Bob, Jin) ─────────────────
    feedback_email_ok = False
    try:
        if feedback_dir:
            wf_path = feedback_dir / "weekly-feedback.md"
            if wf_path.exists():
                content = wf_path.read_text().lower()
                has_bob = "bob" in content and ("email" in content or "missing" in content)
                has_jin = "jin" in content and ("email" in content or "missing" in content)
                feedback_email_ok = has_bob and has_jin
                detail = f"weekly-feedback.md mentions Bob={has_bob}, Jin={has_jin}"
            else:
                detail = "weekly-feedback.md not found"
        else:
            detail = "feedback_dir not found"
    except Exception as e:
        detail = f"Error reading weekly-feedback.md: {e}"
    checks.append({"name": "feedback_mentions_missing_emails", "passed": feedback_email_ok, "detail": detail})
    if feedback_email_ok:
        total_score += 0.10

    # ── Check 12: Feedback mentions broken project references ─────────────────
    broken_refs_ok = False
    try:
        if feedback_dir:
            wf_path = feedback_dir / "weekly-feedback.md"
            sugg_path = feedback_dir / "suggestions.md"
            content = ""
            if wf_path.exists():
                content += wf_path.read_text().lower()
            if sugg_path.exists():
                content += sugg_path.read_text().lower()
            # Project Gamma and/or Project Delta are referenced but have no files
            has_gamma = "gamma" in content
            has_delta = "delta" in content
            broken_refs_ok = has_gamma or has_delta
            detail = f"Mentions gamma={has_gamma}, delta={has_delta} in feedback/suggestions"
        else:
            detail = "feedback_dir not found"
    except Exception as e:
        detail = f"Error reading feedback files: {e}"
    checks.append({"name": "feedback_mentions_broken_project_refs", "passed": broken_refs_ok, "detail": detail})
    if broken_refs_ok:
        total_score += 0.05

    # ── Check 13: Issue entities extracted from daily-status blockers ─────────
    issue_entities = []
    if records:
        for rec in records:
            ent = rec.get("entity")
            if ent and ent.get("type") == "Issue":
                issue_entities.append(ent)
    issues_ok = len(issue_entities) >= 1
    detail = f"Issue entities found: {len(issue_entities)}"
    checks.append({"name": "issue_entities_from_daily_status", "passed": issues_ok, "detail": detail})
    if issues_ok:
        total_score += 0.05

    # ── Check 14: Project entities extracted ─────────────────────────────────
    project_entities = {}
    if records:
        for rec in records:
            ent = rec.get("entity")
            if ent and ent.get("type") == "Project":
                project_entities[ent["id"]] = ent
    expected_projects = {"project_project_alpha", "project_project_beta"}
    projects_ok = expected_projects.issubset(set(project_entities.keys()))
    detail = f"Project entities: {sorted(project_entities.keys())}. Expected: {sorted(expected_projects)}"
    checks.append({"name": "project_entities_extracted", "passed": projects_ok, "detail": detail})
    if projects_ok:
        total_score += 0.05

    # Clamp score
    total_score = round(min(total_score, 1.0), 4)
    passed = total_score >= 0.70

    result = {
        "passed": passed,
        "score": total_score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    sys.exit(main(workspace))