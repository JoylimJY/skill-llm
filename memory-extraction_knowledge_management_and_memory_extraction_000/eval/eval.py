import sys
import json
import re
from pathlib import Path

def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def evaluate(workspace: str):
    checks = []
    ws = Path(workspace)

    # ── Load JSONL storage ───────────────────────────────────────────────────
    jsonl_path = ws / "memory" / "knowledge-graph.jsonl"
    md_path = ws / "memory" / "KNOWLEDGE_GRAPH.md"

    try:
        records = load_jsonl(jsonl_path)
        entities = {}
        relations = []
        for r in records:
            if r.get("type") == "entity":
                e = r["data"]
                entities[e["name"]] = e
            elif r.get("type") == "relation":
                relations.append(r["data"])
    except Exception as ex:
        checks.append({"name": "knowledge-graph.jsonl_exists", "passed": False,
                        "detail": f"Cannot load JSONL: {ex}"})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    checks.append({"name": "knowledge-graph.jsonl_exists", "passed": True,
                    "detail": f"Loaded {len(records)} records, {len(entities)} entities, {len(relations)} relations"})

    # ── Check 1: User entity exists with correct entityType ─────────────────
    user_entity = None
    for name, e in entities.items():
        if e.get("entityType") == "user" and ("李明" in name or "liming" in name.lower()):
            user_entity = e
            break
    c1 = user_entity is not None
    checks.append({"name": "user_entity_liming", "passed": c1,
                    "detail": f"User entity '李明' with entityType='user' found: {c1}. Entities: {list(entities.keys())}"})

    # ── Check 2: Project entity 'DataFlow' with entityType='project' ─────────
    project_entity = None
    for name, e in entities.items():
        if e.get("entityType") == "project" and "dataflow" in name.lower():
            project_entity = e
            break
    c2 = project_entity is not None
    checks.append({"name": "project_entity_dataflow", "passed": c2,
                    "detail": f"Project entity 'DataFlow' with entityType='project' found: {c2}"})

    # ── Check 3: Tool entities exist (Python, Kafka, Redis) ──────────────────
    tool_entities = [e for e in entities.values() if e.get("entityType") == "tool"]
    tool_names_lower = [e["name"].lower() for e in tool_entities]
    found_tools = {
        "python": any("python" in n for n in tool_names_lower),
        "kafka": any("kafka" in n for n in tool_names_lower),
        "redis": any("redis" in n for n in tool_names_lower),
    }
    c3 = sum(found_tools.values()) >= 2  # At least 2 of the 3 tools
    checks.append({"name": "tool_entities_atleast2", "passed": c3,
                    "detail": f"Tool entities found: {found_tools}. Tool entity names: {tool_names_lower}"})

    # ── Check 4: Skill entity for Feishu/飞书 ────────────────────────────────
    skill_entity = None
    for name, e in entities.items():
        if e.get("entityType") == "skill" and ("飞书" in name or "feishu" in name.lower() or "lark" in name.lower()):
            skill_entity = e
            break
    c4 = skill_entity is not None
    checks.append({"name": "skill_entity_feishu", "passed": c4,
                    "detail": f"Skill entity for 飞书/Feishu with entityType='skill' found: {c4}"})

    # ── Check 5: Location entity (上海/Shanghai) ─────────────────────────────
    location_entity = None
    for name, e in entities.items():
        if e.get("entityType") == "location" and ("上海" in name or "shanghai" in name.lower()):
            location_entity = e
            break
    c5 = location_entity is not None
    checks.append({"name": "location_entity_shanghai", "passed": c5,
                    "detail": f"Location entity '上海' with entityType='location' found: {c5}"})

    # ── Check 6: Preference entity (dark theme / 深色) ───────────────────────
    pref_entity = None
    for name, e in entities.items():
        if e.get("entityType") == "preference" and (
                "深色" in name or "dark" in name.lower() or "主题" in name or "theme" in name.lower()):
            pref_entity = e
            break
    c6 = pref_entity is not None
    checks.append({"name": "preference_entity_dark_theme", "passed": c6,
                    "detail": f"Preference entity for dark theme found: {c6}. All preference entities: {[e['name'] for e in entities.values() if e.get('entityType')=='preference']}"})

    # ── Check 7: Relations use canonical relationType vocabulary ─────────────
    valid_relation_types = {"owns", "uses", "prefers", "located_at", "named", "created_on", "deployed_to"}
    all_rel_types = {r.get("relationType", "") for r in relations}
    invalid_types = all_rel_types - valid_relation_types
    c7 = len(invalid_types) == 0 and len(relations) >= 3
    checks.append({"name": "relations_canonical_types_and_count", "passed": c7,
                    "detail": f"All relation types: {all_rel_types}. Invalid types: {invalid_types}. Total relations: {len(relations)}"})

    # ── Check 8: 'owns' relation: 李明 owns DataFlow ─────────────────────────
    owns_rel = None
    for r in relations:
        if r.get("relationType") == "owns" and (
                "dataflow" in r.get("to", "").lower() or "dataflow" in r.get("from", "").lower()):
            if "李明" in r.get("from", "") or "liming" in r.get("from", "").lower():
                owns_rel = r
                break
            elif "李明" in r.get("to", "") or "liming" in r.get("to", "").lower():
                pass  # reversed, skip
    c8 = owns_rel is not None
    checks.append({"name": "relation_liming_owns_dataflow", "passed": c8,
                    "detail": f"Relation '李明 --[owns]--> DataFlow' found: {c8}. All owns relations: {[r for r in relations if r.get('relationType')=='owns']}"})

    # ── Check 9: 'deployed_to' relation for 腾讯云 ───────────────────────────
    deployed_rel = None
    for r in relations:
        if r.get("relationType") == "deployed_to" and (
                "腾讯" in r.get("to", "") or "tencent" in r.get("to", "").lower() or
                "腾讯" in r.get("from", "") or "tencent" in r.get("from", "").lower()):
            deployed_rel = r
            break
    c9 = deployed_rel is not None
    checks.append({"name": "relation_deployed_to_tencent", "passed": c9,
                    "detail": f"'deployed_to' relation for 腾讯云 found: {c9}. All deployed_to: {[r for r in relations if r.get('relationType')=='deployed_to']}"})

    # ── Check 10: Atomic observations on user (email + timezone separate) ────
    user_obs = []
    if user_entity:
        user_obs = user_entity.get("observations", [])

    obs_text = " ".join(user_obs).lower()
    has_email = "liming@example.com" in obs_text
    has_timezone = "asia/shanghai" in obs_text

    # Check atomicity: no single observation contains both email and timezone
    atomic_violation = False
    for obs in user_obs:
        obs_lower = obs.lower()
        if "liming@example.com" in obs_lower and "asia/shanghai" in obs_lower:
            atomic_violation = True
            break

    c10 = has_email and has_timezone and not atomic_violation
    checks.append({"name": "atomic_observations_email_and_timezone", "passed": c10,
                    "detail": f"Has email obs: {has_email}, Has timezone obs: {has_timezone}, Atomic violation (bundled): {atomic_violation}. User observations: {user_obs}"})

    # ── Check 11: KNOWLEDGE_GRAPH.md exported ────────────────────────────────
    try:
        md_content = md_path.read_text(encoding="utf-8")
        c11_exists = len(md_content) > 100
        # Should contain entity names and relation arrows
        c11_has_entities = "李明" in md_content or "liming" in md_content.lower()
        c11_has_relations = "--[" in md_content or "→" in md_content or "->" in md_content
        c11 = c11_exists and c11_has_entities
        checks.append({"name": "KNOWLEDGE_GRAPH_md_exported", "passed": c11,
                        "detail": f"MD exists: {c11_exists}, has entities: {c11_has_entities}, has relations: {c11_has_relations}. Length: {len(md_content)}"})
    except Exception as ex:
        checks.append({"name": "KNOWLEDGE_GRAPH_md_exported", "passed": False,
                        "detail": f"Cannot read KNOWLEDGE_GRAPH.md: {ex}"})
        c11 = False

    # ── Check 12: 'located_at' relation: 李明 located_at 上海 ────────────────
    located_rel = None
    for r in relations:
        if r.get("relationType") == "located_at":
            if ("李明" in r.get("from", "") or "liming" in r.get("from", "").lower()):
                located_rel = r
                break
    c12 = located_rel is not None
    checks.append({"name": "relation_liming_located_at_shanghai", "passed": c12,
                    "detail": f"'located_at' relation for 李明 found: {c12}. All located_at: {[r for r in relations if r.get('relationType')=='located_at']}"})

    # ── Score ────────────────────────────────────────────────────────────────
    all_checks = [c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12]
    # Weighted: core structural checks matter more
    weights = [2, 2, 1.5, 1, 1, 1, 2, 2, 1.5, 2, 1, 1.5]
    total_weight = sum(weights)
    score = sum(w for c, w in zip(all_checks, weights) if c) / total_weight

    passed = score >= 0.65  # Must pass at least 65% weighted

    result = {
        "passed": passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)