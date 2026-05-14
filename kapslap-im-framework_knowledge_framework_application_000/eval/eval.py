import sys
import json
import re
from pathlib import Path
from collections import defaultdict

def load_graph(workspace):
    """Load all 'put' entities from graph.jsonl."""
    graph_path = Path(workspace) / "references" / "graph.jsonl"
    entities = {}
    if not graph_path.exists():
        return entities
    with open(graph_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if d.get("op") == "put" and "entity" in d:
                    e = d["entity"]
                    entities[e["id"]] = e
            except Exception:
                pass
    return entities

def get_verbatim_field(entity):
    """Return the correct verbatim field for an entity per SKILL.md rules."""
    etype = entity.get("type", "")
    props = entity.get("properties", {})
    if etype == "Aphorism":
        return props.get("text", "")
    elif etype in ("Concept",):
        return props.get("definition", "")
    elif etype in ("Axiom", "Theorem", "Implication"):
        return props.get("statement", "")
    return ""

def expected_derivation_chain():
    """
    The expected derivation chain to Symmetry Ethics Theorem.
    Uses only 'implies' and 'depends_on' relations (derivation_chain_valid: True per schema.yaml).
    Shortest canonical path:
      axiom_001 --implies--> theorem_ict --implies--> theorem_symmetry_ethics
      axiom_003 --implies--> theorem_ict
      axiom_003 --implies--> concept_intersubjectivity (supporting)
      theorem_ict depends_on [axiom_003, axiom_001]
      theorem_symmetry_ethics depends_on [theorem_ict, axiom_003]
    Required nodes (minimum): axiom_001, axiom_003, theorem_ict, theorem_symmetry_ethics
    """
    return {
        "axiom_001": "Axiom",
        "axiom_003": "Axiom",
        "theorem_ict": "Theorem",
        "theorem_symmetry_ethics": "Theorem",
    }

def evaluate(workspace):
    checks = []

    # ── Load graph entities ────────────────────────────────────────────────────
    entities = load_graph(workspace)

    # ── Find output file ───────────────────────────────────────────────────────
    output_files = list(Path(workspace).rglob("derivation_brief.md"))
    if not output_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "No derivation_brief.md found anywhere in workspace."}],
        }

    brief_path = output_files[0]
    try:
        content = brief_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_readable", "passed": False, "detail": f"Could not read derivation_brief.md: {e}"}],
        }

    content_lower = content.lower()

    # ── CHECK 1: Derivation chain completeness ─────────────────────────────────
    # All four key entities must be named in the document
    chain_nodes = expected_derivation_chain()
    chain_check_passed = True
    missing_nodes = []
    for eid, etype in chain_nodes.items():
        e = entities.get(eid, {})
        props = e.get("properties", {})
        name = props.get("name", eid)
        if name.lower() not in content_lower and eid not in content_lower:
            chain_check_passed = False
            missing_nodes.append(name)

    checks.append({
        "name": "derivation_chain_completeness",
        "passed": chain_check_passed,
        "detail": f"Missing derivation chain nodes: {missing_nodes}" if missing_nodes else "All required chain nodes present.",
    })

    # ── CHECK 2: Correct verbatim fields used (Aphorism = text, Concept = definition) ──
    # The brief must contain the exact 'text' field of at least one aphorism (not paraphrase)
    aphorism_verbatim = []
    for eid, e in entities.items():
        if e.get("type") == "Aphorism":
            props = e.get("properties", {})
            text = props.get("text", "")
            if text and text in content:
                aphorism_verbatim.append(text[:60])

    aphorism_check_passed = len(aphorism_verbatim) >= 3
    checks.append({
        "name": "aphorism_verbatim_text_field",
        "passed": aphorism_check_passed,
        "detail": f"Found {len(aphorism_verbatim)} aphorism(s) quoted verbatim from 'text' field. Need ≥3. Found: {aphorism_verbatim[:3]}",
    })

    # ── CHECK 3: Verbatim axiom/theorem statements present ────────────────────
    verbatim_count = 0
    verbatim_found = []
    for eid in ["axiom_001", "axiom_003", "theorem_ict", "theorem_symmetry_ethics"]:
        e = entities.get(eid, {})
        verbatim = get_verbatim_field(e)
        if verbatim and verbatim in content:
            verbatim_count += 1
            verbatim_found.append(eid)

    verbatim_check_passed = verbatim_count >= 3
    checks.append({
        "name": "verbatim_axiom_theorem_statements",
        "passed": verbatim_check_passed,
        "detail": f"Found verbatim statements for {verbatim_count}/4 key entities: {verbatim_found}. Need ≥3.",
    })

    # ── CHECK 4: Citation format — blockquote with URL pattern ─────────────────
    # SKILL.md mandates:  > "[exact text]"
    #                     > — *An Immanent Metaphysics*, [section], [URL]
    blockquote_lines = [line.strip() for line in content.split("\n") if line.strip().startswith(">")]
    has_quote_blockquote = any('"' in line and line.startswith(">") for line in blockquote_lines)
    has_attribution_line = any(
        ("An Immanent Metaphysics" in line or "immanent metaphysics" in line.lower())
        and line.startswith(">")
        for line in blockquote_lines
    )
    citation_format_passed = has_quote_blockquote and has_attribution_line
    checks.append({
        "name": "citation_blockquote_format",
        "passed": citation_format_passed,
        "detail": (
            f"has_quote_blockquote={has_quote_blockquote}, "
            f"has_attribution_An_Immanent_Metaphysics={has_attribution_line}. "
            "Expected: > \"[text]\" followed by > — *An Immanent Metaphysics*, ..."
        ),
    })

    # ── CHECK 5: URLs from location fields appear in citations ─────────────────
    BASE_URL = "https://mflb.com/dvol/control/pcore/own_books/white_1/wb_web_2/zout"
    expected_urls = [
        f"{BASE_URL}/upmp_ch1.htm#1_axioms",
        f"{BASE_URL}/upmp_ch3.htm#1_ict",
        f"{BASE_URL}/upmp_ch3.htm#1_symmetry",
    ]
    urls_found = [u for u in expected_urls if u in content]
    url_check_passed = len(urls_found) >= 2
    checks.append({
        "name": "location_urls_in_citations",
        "passed": url_check_passed,
        "detail": f"Found {len(urls_found)}/3 required location URLs. Found: {urls_found}",
    })

    # ── CHECK 6: Summary table with entity name, type, and URL ────────────────
    # Must contain a table-like structure with | separators and the words
    # "Axiom", "Theorem", and URL fragments
    table_lines = [line for line in content.split("\n") if "|" in line]
    has_table = len(table_lines) >= 4  # header + separator + at least 2 data rows
    table_has_types = any("Axiom" in line for line in table_lines) and any("Theorem" in line for line in table_lines)
    table_has_urls = any("mflb.com" in line for line in table_lines)
    summary_table_passed = has_table and table_has_types and table_has_urls
    checks.append({
        "name": "summary_table_entity_type_url",
        "passed": summary_table_passed,
        "detail": (
            f"has_table={has_table} (rows={len(table_lines)}), "
            f"table_has_types={table_has_types}, "
            f"table_has_urls={table_has_urls}"
        ),
    })

    # ── CHECK 7: Synthesis section explicitly labeled ──────────────────────────
    # SKILL.md: "Agent synthesis:" label required for non-quoted application
    synthesis_labels = [
        "agent synthesis",
        "synthesis:",
        "my own application",
        "my application",
        "synthesis section",
    ]
    has_synthesis_label = any(label in content_lower for label in synthesis_labels)

    # Must NOT present synthesis as if it were a direct quote (no > block for synthesis paragraph)
    # This is hard to test precisely, so we check that the label exists and is distinct
    checks.append({
        "name": "synthesis_section_labeled",
        "passed": has_synthesis_label,
        "detail": f"Synthesis label found: {has_synthesis_label}. SKILL.md requires clearly labeling agent-synthesized content.",
    })

    # ── CHECK 8: Only derivation-chain-valid relations used for chain ──────────
    # The chain section must NOT claim paired_with or contrasts_with as derivation steps
    # We check that the words "paired_with" or "contrasts_with" are NOT presented as
    # derivation/dependency steps (they may appear in explanation but not as chain logic)
    # Soft check: count of "implies" or "depends_on" mentions as chain arrows
    chain_relation_mentions = content_lower.count("implies") + content_lower.count("depends_on")
    invalid_chain_mentions = content_lower.count("paired_with") + content_lower.count("contrasts_with")
    # The brief should reference implies/depends_on and not use non-chain relations as chain steps
    relation_check_passed = chain_relation_mentions >= 2
    checks.append({
        "name": "derivation_chain_valid_relations",
        "passed": relation_check_passed,
        "detail": f"Chain relation mentions (implies/depends_on): {chain_relation_mentions}. Non-chain as chain: {invalid_chain_mentions}. Need ≥2 valid chain relation references.",
    })

    # ── CHECK 9: Aphorisms are symmetry-themed (not arbitrary) ────────────────
    # The three selected aphorisms must be thematically related to symmetry ethics
    # Aphorisms 001, 003, and 005 are the most relevant per themes field
    relevant_aphorism_texts = []
    for eid, e in entities.items():
        if e.get("type") == "Aphorism":
            props = e.get("properties", {})
            themes = props.get("themes", [])
            text = props.get("text", "")
            if any(t in ["symmetry", "ethics", "right action", "discontinuity", "choice"] for t in themes):
                if text and text in content:
                    relevant_aphorism_texts.append(text[:60])

    aphorism_theme_passed = len(relevant_aphorism_texts) >= 2
    checks.append({
        "name": "aphorisms_symmetry_themed",
        "passed": aphorism_theme_passed,
        "detail": f"Found {len(relevant_aphorism_texts)} symmetry/ethics-themed aphorisms quoted verbatim. Need ≥2. Found: {relevant_aphorism_texts}",
    })

    # ── CHECK 10: Attribution to Forrest Landry ───────────────────────────────
    attribution_check = "forrest landry" in content_lower or "forrest" in content_lower
    checks.append({
        "name": "attribution_to_forrest_landry",
        "passed": attribution_check,
        "detail": f"Attribution to Forrest Landry found: {attribution_check}",
    })

    # ── Score & pass ──────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_checks / total, 3)
    # Must pass at least 7/10 checks, and MUST pass checks 1, 2, 3, 4, 5
    critical = [
        "derivation_chain_completeness",
        "aphorism_verbatim_text_field",
        "verbatim_axiom_theorem_statements",
        "citation_blockquote_format",
        "location_urls_in_citations",
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    overall_passed = critical_passed and passed_checks >= 7

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))