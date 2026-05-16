#!/usr/bin/env python3
"""
Evaluation script for obsidian-ontology-sync task.
Checks:
  1. config.yaml exists with correct vault path and storage path
  2. graph.jsonl exists and contains expected entity types and IDs
  3. Expected relations present (works_at, assigned_to, for_client, reports_to)
  4. daily-insights.md exists under feedback/
  5. weekly-feedback.md exists under feedback/ with missing-email items
  6. suggestions.md exists under feedback/
  7. cron jobs file exists with correct schedule strings (the proprietary trap)
"""

import sys, json, os, re
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
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── Canonical paths ────────────────────────────────────────────────────
    VAULT = "/root/life/pkm"
    CONFIG_PATH = Path(VAULT) / "ontology-sync" / "config.yaml"
    GRAPH_PATH  = Path(VAULT) / "memory" / "ontology" / "graph.jsonl"
    SCHEMA_PATH = Path(VAULT) / "memory" / "ontology" / "schema.yaml"
    FEEDBACK_DIR = Path(VAULT) / "ontology-sync" / "feedback"
    DAILY_INSIGHTS = FEEDBACK_DIR / "daily-insights.md"
    WEEKLY_FEEDBACK = FEEDBACK_DIR / "weekly-feedback.md"
    SUGGESTIONS = FEEDBACK_DIR / "suggestions.md"
    CRON_FILE = Path(workspace) / "var" / "cron" / "jobs.json"

    # ── Check 1: config.yaml ───────────────────────────────────────────────
    try:
        import yaml
        assert CONFIG_PATH.exists(), f"config.yaml not found at {CONFIG_PATH}"
        with open(CONFIG_PATH) as f:
            cfg = yaml.safe_load(f)
        assert cfg["obsidian"]["vault_path"] == VAULT, \
            f"vault_path should be {VAULT}, got {cfg['obsidian']['vault_path']}"
        assert cfg["ontology"]["storage_path"] == str(Path(VAULT) / "memory" / "ontology"), \
            f"storage_path wrong: {cfg['ontology']['storage_path']}"
        assert cfg["feedback"]["output_path"] == str(FEEDBACK_DIR), \
            f"feedback output_path wrong"
        checks.append({"name": "config.yaml exists with correct paths",
                        "passed": True, "detail": "vault, storage, feedback paths OK"})
    except Exception as e:
        checks.append({"name": "config.yaml exists with correct paths",
                        "passed": False, "detail": str(e)})

    # ── Check 2: graph.jsonl exists and has entities ───────────────────────
    try:
        assert GRAPH_PATH.exists(), f"graph.jsonl not found at {GRAPH_PATH}"
        records = load_jsonl(GRAPH_PATH)
        entities = [r for r in records if r.get("record_type") == "entity"]
        relations = [r for r in records if r.get("record_type") == "relation"]
        assert len(entities) >= 10, f"Expected ≥10 entities, got {len(entities)}"
        types = set(e["type"] for e in entities)
        for et in ["Person", "Organization", "Project", "Event"]:
            assert et in types, f"Entity type '{et}' missing from graph"
        checks.append({"name": "graph.jsonl populated with diverse entity types",
                        "passed": True,
                        "detail": f"{len(entities)} entities, {len(relations)} relations, types={types}"})
    except Exception as e:
        checks.append({"name": "graph.jsonl populated with diverse entity types",
                        "passed": False, "detail": str(e)})
        records, entities, relations = [], [], []

    # ── Check 3: Correct entity IDs (proprietary id format) ───────────────
    try:
        entity_ids = {e["id"] for e in entities}
        expected_ids = [
            "person_alice_johnson",
            "person_eve_torres",
            "person_frank_lee",
            "org_acme_corp",
            "project_project_alpha",
        ]
        missing = [eid for eid in expected_ids if eid not in entity_ids]
        assert not missing, f"Missing entity IDs: {missing}. Found: {sorted(entity_ids)}"
        checks.append({"name": "Entity IDs use correct prefix_snake_case format",
                        "passed": True,
                        "detail": f"All expected IDs present: {expected_ids}"})
    except Exception as e:
        checks.append({"name": "Entity IDs use correct prefix_snake_case format",
                        "passed": False, "detail": str(e)})

    # ── Check 4: Expected relations present ───────────────────────────────
    try:
        rel_types = set(r["rel"] for r in relations)
        for rt in ["works_at", "assigned_to", "for_client", "reports_to"]:
            assert rt in rel_types, f"Relation type '{rt}' missing. Found: {rel_types}"
        # Spot-check: Alice works_at Acme Corp
        alice_org = [r for r in relations
                     if r["from"] == "person_alice_johnson" and r["rel"] == "works_at"]
        assert alice_org, "No works_at relation for person_alice_johnson"
        assert alice_org[0]["to"] == "org_acme_corp", \
            f"Alice should work_at org_acme_corp, got {alice_org[0]['to']}"
        checks.append({"name": "Key relations extracted correctly",
                        "passed": True,
                        "detail": f"Relation types present: {rel_types}"})
    except Exception as e:
        checks.append({"name": "Key relations extracted correctly",
                        "passed": False, "detail": str(e)})

    # ── Check 5: daily-insights.md ────────────────────────────────────────
    try:
        assert DAILY_INSIGHTS.exists(), f"daily-insights.md not found at {DAILY_INSIGHTS}"
        content = DAILY_INSIGHTS.read_text()
        assert "insight" in content.lower() or "missing" in content.lower() or \
               "analysis" in content.lower(), \
               "daily-insights.md appears empty or unrelated"
        checks.append({"name": "daily-insights.md generated in feedback/",
                        "passed": True,
                        "detail": f"File size: {len(content)} chars"})
    except Exception as e:
        checks.append({"name": "daily-insights.md generated in feedback/",
                        "passed": False, "detail": str(e)})

    # ── Check 6: weekly-feedback.md with missing info ─────────────────────
    try:
        assert WEEKLY_FEEDBACK.exists(), f"weekly-feedback.md not found at {WEEKLY_FEEDBACK}"
        content = WEEKLY_FEEDBACK.read_text()
        # Should mention Grace Kim or Bob Smith as missing email
        has_missing_email = re.search(r"missing email", content, re.IGNORECASE)
        assert has_missing_email, \
            "weekly-feedback.md should flag missing email addresses"
        has_template = "template" in content.lower() or "suggestion" in content.lower()
        assert has_template, "weekly-feedback.md should have template suggestions"
        checks.append({"name": "weekly-feedback.md flags missing data and template suggestions",
                        "passed": True,
                        "detail": "Missing email detection + template suggestions present"})
    except Exception as e:
        checks.append({"name": "weekly-feedback.md flags missing data and template suggestions",
                        "passed": False, "detail": str(e)})

    # ── Check 7: suggestions.md ───────────────────────────────────────────
    try:
        assert SUGGESTIONS.exists(), f"suggestions.md not found at {SUGGESTIONS}"
        content = SUGGESTIONS.read_text()
        assert len(content.strip()) > 50, "suggestions.md appears empty"
        checks.append({"name": "suggestions.md generated in feedback/",
                        "passed": True,
                        "detail": f"File size: {len(content)} chars"})
    except Exception as e:
        checks.append({"name": "suggestions.md generated in feedback/",
                        "passed": False, "detail": str(e)})

    # ── Check 8: Cron jobs with EXACT proprietary schedule strings ─────────
    try:
        assert CRON_FILE.exists(), \
            f"Cron jobs file not found at {CRON_FILE}. Was setup-cron.py run?"
        with open(CRON_FILE) as f:
            jobs = json.load(f)
        schedules = [j["schedule"] for j in jobs]
        assert "0 */3 * * *" in schedules, \
            f"Missing 3-hourly extract schedule '0 */3 * * *'. Found: {schedules}"
        assert "0 9 * * *" in schedules, \
            f"Missing daily analysis schedule '0 9 * * *'. Found: {schedules}"
        assert "0 10 * * MON" in schedules, \
            f"Missing weekly feedback schedule '0 10 * * MON'. Found: {schedules}"
        assert len(jobs) == 3, f"Expected exactly 3 cron jobs, got {len(jobs)}"
        checks.append({"name": "Cron jobs registered with correct proprietary schedules",
                        "passed": True,
                        "detail": f"Schedules: {schedules}"})
    except Exception as e:
        checks.append({"name": "Cron jobs registered with correct proprietary schedules",
                        "passed": False, "detail": str(e)})

    # ── Check 9: schema.yaml ──────────────────────────────────────────────
    try:
        assert SCHEMA_PATH.exists(), f"schema.yaml not found at {SCHEMA_PATH}"
        import yaml as _yaml
        schema = _yaml.safe_load(SCHEMA_PATH.read_text())
        assert "entity_types" in schema, "schema.yaml missing entity_types"
        assert "Person" in schema["entity_types"], "schema.yaml missing Person type"
        checks.append({"name": "schema.yaml generated with entity type definitions",
                        "passed": True,
                        "detail": f"Entity types: {schema['entity_types']}"})
    except Exception as e:
        checks.append({"name": "schema.yaml generated with entity type definitions",
                        "passed": False, "detail": str(e)})

    # ── Scoring ───────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    overall_passed = passed_count >= 7  # must pass at least 7/9

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()