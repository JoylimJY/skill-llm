import sys
import json
import re
from pathlib import Path
from datetime import datetime

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score
        if passed:
            total_score += weight

    MAX_SCORE = 10.0  # sum of all weights below

    # ═══════════════════════════════════════════════════════════════════════
    # BLOCK A: Merged Knowledge Graph (pharma_graph_merged.json)
    # ═══════════════════════════════════════════════════════════════════════

    graph_candidates = list(ws.rglob("pharma_graph_merged.json"))
    if not graph_candidates:
        # Also accept any file that looks like an updated/merged graph
        graph_candidates = list(ws.rglob("*merged*.json")) + list(ws.rglob("*updated*.json"))

    merged_graph = None
    graph_path = None
    if graph_candidates:
        graph_path = graph_candidates[0]
        try:
            merged_graph = json.loads(graph_path.read_text(encoding="utf-8"))
        except Exception as e:
            add_check("A1_merged_graph_parseable", False, f"JSON parse error: {e}", weight=0.5)
    
    if merged_graph is None:
        add_check("A1_merged_graph_exists", False, "No merged graph JSON file found (expected pharma_graph_merged.json)", weight=0.5)
        # Fill remaining A checks as failed
        for name in ["A2_version_incremented", "A3_sessions_incremented", "A4_entities_no_duplicate",
                     "A5_new_entities_added", "A6_entity_ids_valid", "A7_relations_have_valid_ids",
                     "A8_weight_in_range", "A9_metadata_counts_accurate", "A10_updated_at_present"]:
            add_check(name, False, "Skipped — no merged graph found", weight=0.5)
    else:
        add_check("A1_merged_graph_exists", True, f"Found at {graph_path}", weight=0.5)

        # A2: Version incremented (1.0.0 → 1.1.0 or higher minor)
        version = merged_graph.get("version", "")
        try:
            parts = version.split(".")
            minor = int(parts[1])
            passed = int(parts[0]) == 1 and minor >= 1
            add_check("A2_version_incremented", passed,
                      f"version='{version}', expected minor>=1 (e.g. 1.1.0)", weight=0.5)
        except Exception as e:
            add_check("A2_version_incremented", False, f"Could not parse version '{version}': {e}", weight=0.5)

        # A3: sessions_analyzed incremented from 1 → ≥2
        sessions = merged_graph.get("metadata", {}).get("sessions_analyzed", 0)
        add_check("A3_sessions_incremented", sessions >= 2,
                  f"sessions_analyzed={sessions}, expected ≥2", weight=1.0)

        # A4: No duplicate entity names
        entity_names = [e["name"] for e in merged_graph.get("entities", [])]
        duplicates = [n for n in entity_names if entity_names.count(n) > 1]
        unique_dups = list(set(duplicates))
        add_check("A4_entities_no_duplicate", len(unique_dups) == 0,
                  f"Duplicate entity names: {unique_dups}" if unique_dups else "No duplicates found", weight=1.0)

        # A5: New entities added beyond original 5
        total_entities = len(merged_graph.get("entities", []))
        # Expect at least 4 new entities from the brief (India, IPA, Biologic drugs, EMA, etc.)
        add_check("A5_new_entities_added", total_entities >= 9,
                  f"total entities={total_entities}, expected ≥9 (5 original + ≥4 new from brief)", weight=1.0)

        # A6: Entity IDs follow e001/e002... pattern and are unique
        entity_ids = [e.get("id", "") for e in merged_graph.get("entities", [])]
        id_pattern = re.compile(r'^e\d{3,}$')
        invalid_ids = [eid for eid in entity_ids if not id_pattern.match(eid)]
        duplicate_ids = [eid for eid in entity_ids if entity_ids.count(eid) > 1]
        id_ok = len(invalid_ids) == 0 and len(set(duplicate_ids)) == 0
        add_check("A6_entity_ids_valid", id_ok,
                  f"Invalid IDs: {invalid_ids}, Duplicate IDs: {list(set(duplicate_ids))}" if not id_ok else "All IDs valid", weight=0.5)

        # A7: All relations reference valid entity IDs
        valid_ids = set(entity_ids)
        bad_refs = []
        for r in merged_graph.get("relations", []):
            if r.get("source") not in valid_ids:
                bad_refs.append(f"source '{r.get('source')}' in relation {r}")
            if r.get("target") not in valid_ids:
                bad_refs.append(f"target '{r.get('target')}' in relation {r}")
        add_check("A7_relations_have_valid_ids", len(bad_refs) == 0,
                  f"Bad refs: {bad_refs[:3]}" if bad_refs else "All relation refs valid", weight=1.0)

        # A8: All relation weights in [0.0, 1.0]
        bad_weights = [r for r in merged_graph.get("relations", [])
                       if not isinstance(r.get("weight"), (int, float)) or not (0.0 <= r["weight"] <= 1.0)]
        add_check("A8_weight_in_range", len(bad_weights) == 0,
                  f"Out-of-range weights in: {bad_weights[:2]}" if bad_weights else "All weights valid", weight=0.5)

        # A9: metadata counts match actual lists
        meta = merged_graph.get("metadata", {})
        actual_e = len(merged_graph.get("entities", []))
        actual_r = len(merged_graph.get("relations", []))
        counts_ok = meta.get("total_entities") == actual_e and meta.get("total_relations") == actual_r
        add_check("A9_metadata_counts_accurate", counts_ok,
                  f"metadata says entities={meta.get('total_entities')},relations={meta.get('total_relations')}; "
                  f"actual entities={actual_e},relations={actual_r}", weight=0.5)

        # A10: updated_at is a valid ISO 8601 timestamp with timezone
        updated_at = merged_graph.get("updated_at", "")
        try:
            from dateutil import parser as dtparser
            dt = dtparser.parse(updated_at)
            tz_ok = dt.tzinfo is not None
            add_check("A10_updated_at_present", tz_ok,
                      f"updated_at='{updated_at}', timezone present={tz_ok}", weight=0.5)
        except Exception as e:
            add_check("A10_updated_at_present", False, f"Could not parse updated_at='{updated_at}': {e}", weight=0.5)

    # ═══════════════════════════════════════════════════════════════════════
    # BLOCK B: Strategy Output (pharma_strategy.json)
    # ═══════════════════════════════════════════════════════════════════════

    strategy_candidates = list(ws.rglob("pharma_strategy.json"))
    if not strategy_candidates:
        strategy_candidates = list(ws.rglob("*strategy*.json"))

    strategy = None
    if strategy_candidates:
        try:
            strategy = json.loads(strategy_candidates[0].read_text(encoding="utf-8"))
        except Exception as e:
            add_check("B1_strategy_parseable", False, f"JSON parse error: {e}", weight=0.5)

    if strategy is None:
        add_check("B1_strategy_exists", False, "No pharma_strategy.json found", weight=0.5)
        for name in ["B2_has_p0_strategy", "B3_has_p1_or_p2_strategy", "B4_has_reasoning_summary",
                     "B5_entity_refs_valid", "B6_generated_at_present"]:
            add_check(name, False, "Skipped — no strategy file found", weight=0.5)
    else:
        add_check("B1_strategy_exists", True, f"Found at {strategy_candidates[0]}", weight=0.5)

        strategies = strategy.get("strategies", [])
        priorities = [s.get("priority", "") for s in strategies]

        # B2: At least one P0 strategy
        has_p0 = "P0" in priorities
        add_check("B2_has_p0_strategy", has_p0,
                  f"priorities found: {priorities}", weight=1.0)

        # B3: At least one P1 or P2 strategy
        has_p1_p2 = "P1" in priorities or "P2" in priorities
        add_check("B3_has_p1_or_p2_strategy", has_p1_p2,
                  f"P1/P2 present: {has_p1_p2}", weight=0.5)

        # B4: reasoning_summary is non-empty
        summary = strategy.get("reasoning_summary", "")
        add_check("B4_has_reasoning_summary", isinstance(summary, str) and len(summary.strip()) > 20,
                  f"reasoning_summary length={len(summary.strip())}", weight=0.5)

        # B5: entity_refs in strategies are valid IDs (if merged graph exists)
        if merged_graph is not None:
            valid_ids_for_strat = set(e["id"] for e in merged_graph.get("entities", []))
            bad_strat_refs = []
            for s in strategies:
                for ref in s.get("entity_refs", []):
                    if ref not in valid_ids_for_strat:
                        bad_strat_refs.append(ref)
            add_check("B5_entity_refs_valid", len(bad_strat_refs) == 0,
                      f"Bad entity refs: {bad_strat_refs}" if bad_strat_refs else "All entity refs valid", weight=0.5)
        else:
            # Just check they look like IDs
            all_refs = [r for s in strategies for r in s.get("entity_refs", [])]
            id_pattern = re.compile(r'^e\d{3,}$')
            bad = [r for r in all_refs if not id_pattern.match(r)]
            add_check("B5_entity_refs_valid", len(bad) == 0,
                      f"Bad entity refs: {bad}" if bad else "All refs look valid", weight=0.5)

        # B6: generated_at is a valid timestamp
        gen_at = strategy.get("generated_at", "")
        try:
            from dateutil import parser as dtparser
            dtparser.parse(gen_at)
            add_check("B6_generated_at_present", True, f"generated_at='{gen_at}'", weight=0.5)
        except Exception as e:
            add_check("B6_generated_at_present", False, f"Could not parse generated_at='{gen_at}': {e}", weight=0.5)

    # ═══════════════════════════════════════════════════════════════════════
    # Final scoring
    # ═══════════════════════════════════════════════════════════════════════
    weight_sum = sum([
        0.5,  # A1
        0.5,  # A2
        1.0,  # A3
        1.0,  # A4
        1.0,  # A5
        0.5,  # A6
        1.0,  # A7
        0.5,  # A8
        0.5,  # A9
        0.5,  # A10
        0.5,  # B1
        1.0,  # B2
        0.5,  # B3
        0.5,  # B4
        0.5,  # B5
        0.5,  # B6
    ])
    score = round(total_score / weight_sum, 4)
    passed = score >= 0.70

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)