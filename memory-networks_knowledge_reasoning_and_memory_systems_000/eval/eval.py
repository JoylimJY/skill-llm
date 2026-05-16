import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight

# ─────────────────────────────────────────────
# CHECK 1: system_config.json exists and is correct
# ─────────────────────────────────────────────
config_files = list(Path(workspace).rglob("system_config.json"))
if not config_files:
    add_check("system_config.json exists", False, "File system_config.json not found anywhere in workspace", weight=2.0)
    config_data = None
else:
    config_path = config_files[0]
    try:
        with open(config_path) as f:
            config_data = json.load(f)
        add_check("system_config.json exists", True, f"Found at {config_path}", weight=2.0)
    except Exception as e:
        add_check("system_config.json exists", False, f"Failed to parse: {e}", weight=2.0)
        config_data = None

if config_data:
    mn = config_data.get("memory_network", {})
    
    # embedding_dim should be 128 (from spec Section 7)
    emb_dim = mn.get("embedding_dim")
    add_check(
        "config: embedding_dim=128",
        emb_dim == 128,
        f"embedding_dim={emb_dim}, expected 128",
        weight=1.0
    )

    # max_memory should be 1000
    max_mem = mn.get("max_memory")
    add_check(
        "config: max_memory=1000",
        max_mem == 1000,
        f"max_memory={max_mem}, expected 1000",
        weight=1.0
    )

    # hops should be 3
    hops = mn.get("hops")
    add_check(
        "config: hops=3",
        hops == 3,
        f"hops={hops}, expected 3",
        weight=1.5
    )

    # scoring method must be dot_product
    scoring = mn.get("scoring", {})
    method = scoring.get("method")
    add_check(
        "config: scoring.method=dot_product",
        method == "dot_product",
        f"scoring.method={method}, expected 'dot_product'",
        weight=1.5
    )

    # temperature must be 1.0
    temp = scoring.get("temperature")
    add_check(
        "config: scoring.temperature=1.0",
        temp == 1.0,
        f"scoring.temperature={temp}, expected 1.0",
        weight=1.0
    )

    # memory_management checks
    mm = mn.get("memory_management", {})
    consolidation = mm.get("consolidation")
    add_check(
        "config: memory_management.consolidation=true",
        consolidation == True,
        f"consolidation={consolidation}, expected true",
        weight=1.0
    )

    forgetting = mm.get("forgetting_threshold")
    add_check(
        "config: forgetting_threshold=0.1",
        forgetting == 0.1,
        f"forgetting_threshold={forgetting}, expected 0.1",
        weight=1.0
    )

    importance_weight = mm.get("importance_weight")
    add_check(
        "config: importance_weight=0.5",
        importance_weight == 0.5,
        f"importance_weight={importance_weight}, expected 0.5",
        weight=1.0
    )

# ─────────────────────────────────────────────
# CHECK 2: memory_state.json - Tiered Distribution
# ─────────────────────────────────────────────
# From SKILL.md Section 8:
# importance > 0.9 → tier3 (LongTerm)
# importance > 0.7 → tier2 (ShortTerm)
# else → tier1 (WorkingMemory)

KNOWLEDGE_DUMP_PATH = os.path.join(workspace, "research_institute/knowledge_base/raw/knowledge_dump.json")
with open(KNOWLEDGE_DUMP_PATH) as f:
    knowledge_dump = json.load(f)

entries = knowledge_dump["entries"]

# Ground truth tiers
expected_tier3 = set()  # importance > 0.9
expected_tier2 = set()  # importance > 0.7 and <= 0.9
expected_tier1 = set()  # importance <= 0.7

for e in entries:
    imp = e["importance_score"]
    eid = e["id"]
    if imp > 0.9:
        expected_tier3.add(eid)
    elif imp > 0.7:
        expected_tier2.add(eid)
    else:
        expected_tier1.add(eid)

# e001=0.95→t3, e002=0.75→t2, e003=0.92→t3, e004=0.91→t3, e005=0.93→t3
# e006=0.94→t3, e007=0.78→t2, e008=0.65→t1, e009=0.72→t2, e010=0.60→t1
# e011=0.55→t1, e012=0.58→t1

state_files = list(Path(workspace).rglob("memory_state.json"))
if not state_files:
    add_check("memory_state.json exists", False, "File not found", weight=2.0)
    add_check("tier3 (long-term) entries correct", False, "No memory_state.json to check", weight=2.0)
    add_check("tier2 (short-term) entries correct", False, "No memory_state.json to check", weight=2.0)
    add_check("tier1 (working) entries correct", False, "No memory_state.json to check", weight=2.0)
else:
    state_path = state_files[0]
    try:
        with open(state_path) as f:
            state_data = json.load(f)
        add_check("memory_state.json exists", True, f"Found at {state_path}", weight=2.0)

        tier3_actual = set(state_data.get("tier3_long_term", []))
        tier2_actual = set(state_data.get("tier2_short_term", []))
        tier1_actual = set(state_data.get("tier1_working", []))

        tier3_ok = tier3_actual == expected_tier3
        add_check(
            "tier3 (long-term) entries correct",
            tier3_ok,
            f"Expected {sorted(expected_tier3)}, got {sorted(tier3_actual)}",
            weight=2.0
        )

        tier2_ok = tier2_actual == expected_tier2
        add_check(
            "tier2 (short-term) entries correct",
            tier2_ok,
            f"Expected {sorted(expected_tier2)}, got {sorted(tier2_actual)}",
            weight=2.0
        )

        tier1_ok = tier1_actual == expected_tier1
        add_check(
            "tier1 (working memory) entries correct",
            tier1_ok,
            f"Expected {sorted(expected_tier1)}, got {sorted(tier1_actual)}",
            weight=2.0
        )

        # Working memory capacity check: must not exceed 7 items (Miller's 7±2)
        tier1_count = len(tier1_actual)
        add_check(
            "tier1 working memory capacity <= 7 (Miller's rule)",
            tier1_count <= 7,
            f"Working memory has {tier1_count} items, max allowed is 7",
            weight=1.5
        )

    except Exception as e:
        add_check("memory_state.json exists", True, f"Found but failed to parse: {e}", weight=2.0)
        add_check("tier3 (long-term) entries correct", False, f"Parse error: {e}", weight=2.0)
        add_check("tier2 (short-term) entries correct", False, f"Parse error: {e}", weight=2.0)
        add_check("tier1 (working) entries correct", False, f"Parse error: {e}", weight=2.0)

# ─────────────────────────────────────────────
# CHECK 3: reasoning_results.json - Multi-hop reasoning
# ─────────────────────────────────────────────
results_files = list(Path(workspace).rglob("reasoning_results.json"))
if not results_files:
    add_check("reasoning_results.json exists", False, "File not found", weight=2.0)
    add_check("q001 reasoning chain length >= 2 hops", False, "No results file", weight=2.0)
    add_check("q001 answer contains key concepts", False, "No results file", weight=2.0)
    add_check("q002 answer contains I-G-O-R framework", False, "No results file", weight=2.0)
    add_check("q002 reasoning chain references Memory Networks", False, "No results file", weight=1.5)
else:
    results_path = results_files[0]
    try:
        with open(results_path) as f:
            results_data = json.load(f)
        add_check("reasoning_results.json exists", True, f"Found at {results_path}", weight=2.0)

        results_list = results_data.get("results", [])
        results_by_id = {r.get("query_id"): r for r in results_list}

        # q001: Transformer → machine learning chain (should be >= 2 hops)
        q001 = results_by_id.get("q001")
        if q001:
            chain = q001.get("chain", [])
            hops_used = q001.get("hops_used", 0)
            answer = q001.get("answer", "").lower()

            chain_length_ok = len(chain) >= 2 or hops_used >= 2
            add_check(
                "q001 reasoning chain length >= 2 hops",
                chain_length_ok,
                f"Chain length={len(chain)}, hops_used={hops_used}",
                weight=2.0
            )

            keywords_q001 = ["transformer", "machine learning"]
            answer_ok = all(kw.lower() in answer for kw in keywords_q001)
            add_check(
                "q001 answer contains key concepts",
                answer_ok,
                f"Answer: '{q001.get('answer', '')}' | Required keywords: {keywords_q001}",
                weight=2.0
            )
        else:
            add_check("q001 reasoning chain length >= 2 hops", False, "q001 not found in results", weight=2.0)
            add_check("q001 answer contains key concepts", False, "q001 not found in results", weight=2.0)

        # q002: Memory Networks → I-G-O-R
        q002 = results_by_id.get("q002")
        if q002:
            answer_q002 = q002.get("answer", "").lower()
            chain_q002 = " ".join(q002.get("chain", [])).lower()

            igor_in_answer = "i-g-o-r" in answer_q002 or "igor" in answer_q002 or "i g o r" in answer_q002
            add_check(
                "q002 answer contains I-G-O-R framework",
                igor_in_answer,
                f"Answer: '{q002.get('answer', '')}' | Looking for I-G-O-R",
                weight=2.0
            )

            memnn_in_chain = "memory networks" in chain_q002 or "weston" in chain_q002 or "memory network" in chain_q002
            add_check(
                "q002 reasoning chain references Memory Networks",
                memnn_in_chain,
                f"Chain text: '{chain_q002[:200]}' | Looking for 'memory networks' or 'weston'",
                weight=1.5
            )
        else:
            add_check("q002 answer contains I-G-O-R framework", False, "q002 not found in results", weight=2.0)
            add_check("q002 reasoning chain references Memory Networks", False, "q002 not found in results", weight=1.5)

    except Exception as e:
        add_check("reasoning_results.json exists", True, f"Found but failed to parse: {e}", weight=2.0)
        add_check("q001 reasoning chain length >= 2 hops", False, f"Parse error: {e}", weight=2.0)
        add_check("q001 answer contains key concepts", False, f"Parse error: {e}", weight=2.0)
        add_check("q002 answer contains I-G-O-R framework", False, f"Parse error: {e}", weight=2.0)
        add_check("q002 reasoning chain references Memory Networks", False, f"Parse error: {e}", weight=1.5)

# ─────────────────────────────────────────────
# CHECK 4: memory_system.py exists and implements required classes
# ─────────────────────────────────────────────
py_files = list(Path(workspace).rglob("memory_system.py"))
if not py_files:
    add_check("memory_system.py exists", False, "File not found", weight=1.0)
    add_check("memory_system.py contains TieredMemoryNetwork", False, "No file", weight=1.0)
    add_check("memory_system.py implements multi-hop reasoning", False, "No file", weight=1.0)
else:
    py_path = py_files[0]
    try:
        with open(py_path) as f:
            py_content = f.read()
        add_check("memory_system.py exists", True, f"Found at {py_path}", weight=1.0)

        has_tiered = "TieredMemoryNetwork" in py_content or "tiered_memory" in py_content.lower() or "tier" in py_content.lower()
        add_check(
            "memory_system.py contains TieredMemoryNetwork",
            has_tiered,
            f"Found tiered memory reference: {has_tiered}",
            weight=1.0
        )

        has_multihop = "multi_hop" in py_content.lower() or "multihop" in py_content.lower() or "hop" in py_content.lower()
        add_check(
            "memory_system.py implements multi-hop reasoning",
            has_multihop,
            f"Found multi-hop reference: {has_multihop}",
            weight=1.0
        )

        # Check importance thresholds appear in the code
        has_09_threshold = "0.9" in py_content
        has_07_threshold = "0.7" in py_content
        thresholds_ok = has_09_threshold and has_07_threshold
        add_check(
            "memory_system.py uses correct importance thresholds (0.9, 0.7)",
            thresholds_ok,
            f"Found 0.9: {has_09_threshold}, Found 0.7: {has_07_threshold}",
            weight=1.5
        )

    except Exception as e:
        add_check("memory_system.py exists", True, f"Found but failed to read: {e}", weight=1.0)
        add_check("memory_system.py contains TieredMemoryNetwork", False, f"Read error", weight=1.0)
        add_check("memory_system.py implements multi-hop reasoning", False, f"Read error", weight=1.0)
        add_check("memory_system.py uses correct importance thresholds (0.9, 0.7)", False, f"Read error", weight=1.5)

# ─────────────────────────────────────────────
# FINAL SCORING
# ─────────────────────────────────────────────
final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
passed = final_score >= 0.70

output = {
    "passed": passed,
    "score": final_score,
    "checks": checks
}

print(json.dumps(output, indent=2))