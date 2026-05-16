import sys
import json
import re
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── Find the output file ─────────────────────────────────────────────────
    candidates = list(workspace.rglob("ralstp_analysis.json"))
    if not candidates:
        add_check("file_exists", False, "ralstp_analysis.json not found anywhere in workspace")
        return {"passed": False, "score": 0.0, "checks": checks}

    output_file = candidates[0]
    add_check("file_exists", True, f"Found at {output_file.relative_to(workspace)}")

    # ── Parse JSON ───────────────────────────────────────────────────────────
    try:
        data = json.loads(output_file.read_text())
    except Exception as e:
        add_check("json_valid", False, f"JSON parse error: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    add_check("json_valid", True, "Valid JSON")

    # ── Check required top-level sections ───────────────────────────────────
    required_sections = [
        "agents_identified",
        "passive_objects",
        "dependency_graph",
        "difficulty_assessment",
        "strategic_phase",
        "tactical_phase",
        "decomposition_suggestion",
    ]
    missing = [s for s in required_sections if s not in data]
    sec_ok = add_check(
        "required_sections",
        len(missing) == 0,
        f"Missing sections: {missing}" if missing else "All 7 sections present"
    )

    # ── Agent Identification (RALSTP rule: dynamic types only) ──────────────
    # Correct agents per PDDL analysis: developer, tester, security_scanner, ops_engineer
    # These appear as first arg in at-end effects (available, busy, deployed, etc.)
    # passive_types: feature_branch, artifact, ticket, environment, registry,
    #                pipeline_agent, work_item, infrastructure  (parent types + static)
    CORRECT_AGENTS = {"developer", "tester", "security_scanner", "ops_engineer"}
    FORBIDDEN_AS_AGENTS = {"environment", "registry", "feature_branch", "artifact",
                           "ticket", "work_item", "infrastructure", "pipeline_agent"}

    agents_section = data.get("agents_identified", {})
    # Accept either a list or a dict with a "list" key
    if isinstance(agents_section, list):
        agent_names_raw = agents_section
    elif isinstance(agents_section, dict):
        agent_names_raw = agents_section.get("list", agents_section.get("agents", []))
    else:
        agent_names_raw = []

    agent_names = set()
    for item in agent_names_raw:
        if isinstance(item, str):
            agent_names.add(item.lower().strip())
        elif isinstance(item, dict):
            n = item.get("name", item.get("type", ""))
            if n:
                agent_names.add(n.lower().strip())

    # Normalize underscores/hyphens
    def norm(s):
        return s.replace("-", "_").lower()

    agent_names_norm = {norm(a) for a in agent_names}
    correct_norm = {norm(a) for a in CORRECT_AGENTS}
    forbidden_norm = {norm(a) for a in FORBIDDEN_AS_AGENTS}

    all_correct_present = correct_norm.issubset(agent_names_norm)
    no_forbidden = len(forbidden_norm & agent_names_norm) == 0

    add_check(
        "agents_correct_identified",
        all_correct_present,
        f"Expected agents {sorted(correct_norm)}, found {sorted(agent_names_norm)}"
    )
    add_check(
        "no_static_types_as_agents",
        no_forbidden,
        f"Forbidden (static) types incorrectly listed as agents: {sorted(forbidden_norm & agent_names_norm)}"
        if not no_forbidden else "No static types incorrectly promoted to agents"
    )

    # ── Passive Objects ───────────────────────────────────────────────────────
    passive_section = data.get("passive_objects", {})
    if isinstance(passive_section, list):
        passive_names_raw = passive_section
    elif isinstance(passive_section, dict):
        passive_names_raw = passive_section.get("list", passive_section.get("objects", []))
    else:
        passive_names_raw = []

    passive_names = set()
    for item in passive_names_raw:
        if isinstance(item, str):
            passive_names.add(norm(item))
        elif isinstance(item, dict):
            n = item.get("name", item.get("type", ""))
            if n:
                passive_names.add(norm(n))

    # artifact, feature_branch, ticket must be in passive
    required_passive = {"artifact", "feature_branch", "ticket"}
    required_passive_norm = {norm(p) for p in required_passive}
    passive_ok = required_passive_norm.issubset(passive_names)
    add_check(
        "passive_objects_correct",
        passive_ok,
        f"Required passive objects {sorted(required_passive_norm)} found in {sorted(passive_names)}"
    )

    # ── Difficulty Assessment ─────────────────────────────────────────────────
    difficulty = data.get("difficulty_assessment", {})

    # Agent count should be 4
    agent_count = None
    if isinstance(difficulty, dict):
        ac = difficulty.get("agent_count", difficulty.get("Agent Count", None))
        if ac is not None:
            try:
                agent_count = int(str(ac).strip())
            except Exception:
                pass

    add_check(
        "agent_count_correct",
        agent_count == 4,
        f"Expected agent_count=4, got {agent_count}"
    )

    # Entanglement must be "High"
    entanglement_val = None
    if isinstance(difficulty, dict):
        ent = difficulty.get("entanglement", difficulty.get("Entanglement", ""))
        if isinstance(ent, str):
            entanglement_val = ent.strip().lower()

    entanglement_high = entanglement_val in ("high", "high (3)", "3")
    add_check(
        "entanglement_high",
        entanglement_high,
        f"Expected entanglement=High, got '{entanglement_val}'"
    )

    # Buksz Complexity Score = Agent Count × Entanglement Factor
    # With 4 agents and High entanglement (factor=3), score = 12
    buksz = None
    if isinstance(difficulty, dict):
        bs = difficulty.get("buksz_complexity_score",
             difficulty.get("estimated_complexity",
             difficulty.get("Estimated Complexity", None)))
        if bs is not None:
            try:
                buksz = int(float(str(bs).strip()))
            except Exception:
                # Try to extract number from string like "12 (High)"
                m = re.search(r'\d+', str(bs))
                if m:
                    buksz = int(m.group())

    add_check(
        "buksz_score_correct",
        buksz == 12,
        f"Expected Buksz score=12 (4 agents × 3 entanglement factor), got {buksz}"
    )

    # ── Landmark Chain ────────────────────────────────────────────────────────
    # Must contain: artifact-ready → tested → cleared → registered → deployed
    # and/or the goal facts: deployed, ticket-resolved, smoke-passed
    strategic = str(data.get("strategic_phase", "")).lower()
    tactical = str(data.get("tactical_phase", "")).lower()
    decomp = str(data.get("decomposition_suggestion", "")).lower()

    landmark_keywords = ["artifact", "tested", "cleared", "deployed", "smoke"]
    landmark_in_strategic = sum(1 for kw in landmark_keywords if kw in strategic)
    landmark_in_tactical = sum(1 for kw in landmark_keywords if kw in tactical)

    add_check(
        "landmark_chain_in_strategic",
        landmark_in_strategic >= 3,
        f"Strategic phase mentions {landmark_in_strategic}/5 landmark keywords {landmark_keywords}"
    )
    add_check(
        "landmark_chain_in_tactical",
        landmark_in_tactical >= 3,
        f"Tactical phase mentions {landmark_in_tactical}/5 landmark keywords {landmark_keywords}"
    )

    # ── Dependency Graph ──────────────────────────────────────────────────────
    dep_graph = str(data.get("dependency_graph", "")).lower()
    # Must show developer → tester → security_scanner → ops_engineer dependency
    dep_keywords = ["developer", "tester", "security", "ops"]
    dep_found = sum(1 for kw in dep_keywords if kw in dep_graph)
    add_check(
        "dependency_graph_complete",
        dep_found >= 3,
        f"Dependency graph mentions {dep_found}/4 key actors"
    )

    # ── Decomposition Suggestion mentions parallelization or split ────────────
    parallel_hint = any(kw in decomp for kw in ["parallel", "concurrent", "simultan", "split"])
    add_check(
        "decomposition_parallelization",
        parallel_hint,
        "Decomposition suggestion mentions parallelization/split: " + str(parallel_hint)
    )

    # ── Final scoring ─────────────────────────────────────────────────────────
    scored_checks = [
        ("file_exists", 0.05),
        ("json_valid", 0.05),
        ("required_sections", 0.10),
        ("agents_correct_identified", 0.15),
        ("no_static_types_as_agents", 0.10),
        ("passive_objects_correct", 0.05),
        ("agent_count_correct", 0.05),
        ("entanglement_high", 0.10),
        ("buksz_score_correct", 0.10),
        ("landmark_chain_in_strategic", 0.08),
        ("landmark_chain_in_tactical", 0.08),
        ("dependency_graph_complete", 0.05),
        ("decomposition_parallelization", 0.04),
    ]

    check_map = {c["name"]: c["passed"] for c in checks}
    score = sum(w for name, w in scored_checks if check_map.get(name, False))
    score = round(min(score, 1.0), 4)
    passed = score >= 0.70

    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))