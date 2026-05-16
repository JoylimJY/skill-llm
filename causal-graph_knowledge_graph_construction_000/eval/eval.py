import sys
import json
import os
from pathlib import Path

def find_output_file(workspace: str) -> Path | None:
    """Search for knowledge_graph.json anywhere in the workspace."""
    workspace_path = Path(workspace)
    candidates = list(workspace_path.rglob("knowledge_graph.json"))
    if candidates:
        return candidates[0]
    return None

def slugify(text: str) -> str:
    """Rough slug: lowercase, replace spaces and underscores with hyphens."""
    import re
    text = text.lower()
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'[^\w\-]', '', text)
    return text

def run_eval(workspace: str):
    checks = []
    score = 0.0
    total_weight = 0.0

    # ── Check 1: Output file exists ──────────────────────────────────────
    output_file = find_output_file(workspace)
    check1_passed = output_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": check1_passed,
        "detail": f"Found at {output_file}" if check1_passed else "knowledge_graph.json not found anywhere in workspace"
    })
    weight1 = 1.0
    total_weight += weight1
    if check1_passed:
        score += weight1

    if not check1_passed:
        return checks, score, total_weight

    # ── Parse JSON ────────────────────────────────────────────────────────
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            graph = json.load(f)
    except Exception as e:
        checks.append({
            "name": "json_parseable",
            "passed": False,
            "detail": f"Failed to parse JSON: {e}"
        })
        total_weight += 9.0
        return checks, score, total_weight

    checks.append({
        "name": "json_parseable",
        "passed": True,
        "detail": "JSON parsed successfully"
    })
    total_weight += 1.0
    score += 1.0

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # ── Check 2: Has nodes and edges keys ─────────────────────────────────
    has_structure = isinstance(nodes, list) and isinstance(edges, list)
    checks.append({
        "name": "has_nodes_and_edges_keys",
        "passed": has_structure,
        "detail": f"nodes: {type(nodes).__name__}, edges: {type(edges).__name__}"
    })
    total_weight += 1.0
    if has_structure:
        score += 1.0

    if not has_structure:
        return checks, score, total_weight

    # ── Check 3: Node schema compliance ───────────────────────────────────
    # Each node must have: id, type, label
    # type must be one of: project, tool, event, person, concept, entity
    VALID_NODE_TYPES = {"project", "tool", "event", "person", "concept", "entity"}
    node_schema_issues = []
    for n in nodes:
        if not isinstance(n, dict):
            node_schema_issues.append(f"Node is not a dict: {n}")
            continue
        if "id" not in n:
            node_schema_issues.append(f"Missing 'id' in node: {n}")
        if "type" not in n:
            node_schema_issues.append(f"Missing 'type' in node: {n}")
        elif n["type"] not in VALID_NODE_TYPES:
            node_schema_issues.append(f"Invalid node type '{n['type']}' — must be one of {VALID_NODE_TYPES}")
        if "label" not in n:
            node_schema_issues.append(f"Missing 'label' in node: {n}")

    node_schema_ok = len(node_schema_issues) == 0
    checks.append({
        "name": "node_schema_compliance",
        "passed": node_schema_ok,
        "detail": "All nodes have id/type/label with valid types" if node_schema_ok else "; ".join(node_schema_issues[:5])
    })
    total_weight += 2.0
    if node_schema_ok:
        score += 2.0

    # ── Check 4: Edge schema compliance ───────────────────────────────────
    VALID_EDGE_TYPES = {"causes", "enables", "requires", "relates", "affects"}
    edge_schema_issues = []
    for e in edges:
        if not isinstance(e, dict):
            edge_schema_issues.append(f"Edge is not a dict: {e}")
            continue
        for field in ("from", "to", "type"):
            if field not in e:
                edge_schema_issues.append(f"Missing '{field}' in edge: {e}")
        if "type" in e and e["type"] not in VALID_EDGE_TYPES:
            edge_schema_issues.append(f"Invalid edge type '{e['type']}' — must be one of {VALID_EDGE_TYPES}")

    edge_schema_ok = len(edge_schema_issues) == 0
    checks.append({
        "name": "edge_schema_compliance",
        "passed": edge_schema_ok,
        "detail": "All edges have from/to/type with valid types" if edge_schema_ok else "; ".join(edge_schema_issues[:5])
    })
    total_weight += 2.0
    if edge_schema_ok:
        score += 2.0

    # ── Check 5: Key entities present ─────────────────────────────────────
    # Must have AgentAwaken (project), NeuroBoost (project), Vercel (tool), GitHub (tool)
    node_labels_lower = {n.get("label", "").lower() for n in nodes}
    node_ids_lower = {n.get("id", "").lower() for n in nodes}
    all_identifiers = node_labels_lower | node_ids_lower

    required_entities = {
        "agentawaken": ["agentawaken", "agent-awaken", "agent awaken"],
        "neuroboost": ["neuroboost", "neuro-boost", "neuro boost"],
        "vercel": ["vercel"],
        "github": ["github"],
    }

    missing_entities = []
    for canonical, variants in required_entities.items():
        found = any(
            any(v in ident for v in variants)
            for ident in all_identifiers
        )
        if not found:
            missing_entities.append(canonical)

    entities_ok = len(missing_entities) == 0
    checks.append({
        "name": "key_entities_present",
        "passed": entities_ok,
        "detail": "All required entities found" if entities_ok else f"Missing entities: {missing_entities}"
    })
    total_weight += 2.0
    if entities_ok:
        score += 2.0

    # ── Check 6: At least one event node with timestamp ───────────────────
    event_nodes = [n for n in nodes if n.get("type") == "event"]
    events_with_timestamps = [n for n in event_nodes if "timestamp" in n and n["timestamp"]]
    has_events = len(event_nodes) >= 1
    has_timestamped = len(events_with_timestamps) >= 1

    checks.append({
        "name": "event_nodes_with_timestamps",
        "passed": has_events and has_timestamped,
        "detail": f"Found {len(event_nodes)} event nodes, {len(events_with_timestamps)} with timestamps"
    })
    total_weight += 2.0
    if has_events and has_timestamped:
        score += 2.0

    # ── Check 7: Requires edges present (AgentAwaken → Vercel or GitHub) ──
    # Must have at least one 'requires' edge
    requires_edges = [e for e in edges if e.get("type") == "requires"]
    has_requires = len(requires_edges) >= 1

    # Also check: AgentAwaken should require Vercel or GitHub
    node_id_map = {n.get("id", "").lower(): n for n in nodes}
    node_label_map = {n.get("label", "").lower(): n for n in nodes}

    def get_node_by_ref(ref):
        ref_lower = ref.lower()
        if ref_lower in node_id_map:
            return node_id_map[ref_lower]
        if ref_lower in node_label_map:
            return node_label_map[ref_lower]
        return None

    agentawaken_requires_tool = False
    for e in requires_edges:
        from_node = get_node_by_ref(e.get("from", ""))
        to_node = get_node_by_ref(e.get("to", ""))
        if from_node and to_node:
            from_label = from_node.get("label", "").lower()
            to_type = to_node.get("type", "").lower()
            to_label = to_node.get("label", "").lower()
            if ("agentawaken" in from_label or "agent-awaken" in from_label or "agent awaken" in from_label):
                if to_type == "tool" or any(t in to_label for t in ["vercel", "github", "pnpm"]):
                    agentawaken_requires_tool = True
                    break

    requires_ok = has_requires and agentawaken_requires_tool
    checks.append({
        "name": "requires_edges_with_agentawaken",
        "passed": requires_ok,
        "detail": f"{len(requires_edges)} 'requires' edges found; AgentAwaken→tool requires edge: {agentawaken_requires_tool}"
    })
    total_weight += 2.0
    if requires_ok:
        score += 2.0

    # ── Check 8: Causes edges from causal inference ────────────────────────
    # Must infer at least one 'causes' edge from log text
    causes_edges = [e for e in edges if e.get("type") == "causes"]
    has_causes = len(causes_edges) >= 1
    checks.append({
        "name": "causes_edges_from_inference",
        "passed": has_causes,
        "detail": f"Found {len(causes_edges)} 'causes' edges (need ≥1)"
    })
    total_weight += 2.0
    if has_causes:
        score += 2.0

    # ── Check 9: Deduplication — no duplicate entity labels ───────────────
    # AgentAwaken should appear as ONE node, not multiple
    label_counts: dict[str, int] = {}
    for n in nodes:
        label = n.get("label", "").strip().lower()
        if label:
            label_counts[label] = label_counts.get(label, 0) + 1

    duplicates = {k: v for k, v in label_counts.items() if v > 1}
    dedup_ok = len(duplicates) == 0
    checks.append({
        "name": "no_duplicate_entity_labels",
        "passed": dedup_ok,
        "detail": "No duplicate labels found" if dedup_ok else f"Duplicates: {dict(list(duplicates.items())[:5])}"
    })
    total_weight += 1.0
    if dedup_ok:
        score += 1.0

    # ── Check 10: IDs are slug-format (lowercase, hyphenated) ─────────────
    import re
    slug_pattern = re.compile(r'^[a-z0-9][a-z0-9\-]*$')
    bad_ids = [n.get("id", "") for n in nodes if not slug_pattern.match(n.get("id", ""))]
    ids_ok = len(bad_ids) == 0
    checks.append({
        "name": "node_ids_are_slugs",
        "passed": ids_ok,
        "detail": "All node IDs are valid slugs" if ids_ok else f"Non-slug IDs: {bad_ids[:5]}"
    })
    total_weight += 1.0
    if ids_ok:
        score += 1.0

    # ── Check 11: Minimum graph size (richness) ───────────────────────────
    min_nodes = 8
    min_edges = 5
    size_ok = len(nodes) >= min_nodes and len(edges) >= min_edges
    checks.append({
        "name": "graph_richness",
        "passed": size_ok,
        "detail": f"{len(nodes)} nodes (need ≥{min_nodes}), {len(edges)} edges (need ≥{min_edges})"
    })
    total_weight += 1.0
    if size_ok:
        score += 1.0

    # ── Check 12: Person nodes present ───────────────────────────────────
    person_nodes = [n for n in nodes if n.get("type") == "person"]
    person_labels_lower = {n.get("label", "").lower() for n in person_nodes}
    required_people = ["瓜农", "jason zuo", "龙虾"]
    found_people = sum(
        1 for p in required_people
        if any(p.lower() in lbl for lbl in person_labels_lower)
    )
    people_ok = found_people >= 2
    checks.append({
        "name": "person_nodes_present",
        "passed": people_ok,
        "detail": f"Found {found_people}/3 required people as person-type nodes"
    })
    total_weight += 1.0
    if people_ok:
        score += 1.0

    return checks, score, total_weight


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score, total_weight = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    normalized_score = round(score / total_weight, 4) if total_weight > 0 else 0.0
    passed = normalized_score >= 0.75

    result = {
        "passed": passed,
        "score": normalized_score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()