import os
import json
import yaml
import random
from pathlib import Path
from datetime import datetime, timezone

random.seed(42)

workspace = Path("/workspace")

# ─── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "memory/ontology-clawra",
    "memory/ontology-clawra/archive",
    "docs/clinical",
    "docs/regulatory",
    "data/raw",
    "data/processed",
    "logs",
    "config",
    "reports/2026-Q1",
    "reports/2026-Q2",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ─────────────────────────────────────────────────────────
(workspace / "docs/clinical/patient_cohort_2025.csv").write_text(
    "patient_id,age,drugs,condition\n"
    "P001,67,warfarin+aspirin,AFib\n"
    "P002,54,metformin+sitagliptin,T2DM\n"
    "P003,72,digoxin+amiodarone,CHF\n"
)

(workspace / "docs/regulatory/FDA_interaction_warnings_2025.txt").write_text(
    "Section 4.5 - Drug Interactions\n"
    "Warfarin + NSAIDs: increased bleeding risk (major)\n"
    "Digoxin + Amiodarone: digoxin toxicity risk (major, monitor levels)\n"
    "Metformin + Contrast agents: lactic acidosis risk (moderate)\n"
)

(workspace / "data/raw/ehr_export_2026-01.json").write_text(json.dumps([
    {"id": "EHR-001", "patient": "P003", "note": "Patient presents with bradycardia. Currently on digoxin 0.25mg and amiodarone 200mg. Physician suspects drug interaction."},
    {"id": "EHR-002", "patient": "P001", "note": "Warfarin INR elevated. Patient self-administered ibuprofen for knee pain."},
], indent=2))

(workspace / "data/processed/drug_pairs_flagged.json").write_text(json.dumps({
    "flagged": [
        {"pair": ["warfarin", "ibuprofen"], "severity": "major"},
        {"pair": ["digoxin", "amiodarone"], "severity": "major"},
    ],
    "generated": "2026-01-15"
}, indent=2))

(workspace / "config/system.yaml").write_text(
    "system:\n"
    "  name: ClinicalDSS\n"
    "  version: 2.1\n"
    "  log_level: INFO\n"
    "  ontology_backend: local\n"
)

(workspace / "config/thresholds.yaml").write_text(
    "confidence_thresholds:\n"
    "  chain_reasoning_min: 0.5\n"
    "  auto_upgrade_min: 0.8\n"
    "  speculative_max: 0.3\n"
)

(workspace / "logs/system_2026-01.log").write_text(
    "[2026-01-10 08:00:01] INFO system started\n"
    "[2026-01-10 08:01:33] INFO ontology loaded: 0 entities\n"
    "[2026-01-10 09:15:44] WARN check_ontology returned NOT_FOUND for query: digoxin+amiodarone\n"
    "[2026-01-10 09:15:45] INFO declare_source: UNKNOWN - no local ontology data\n"
)

(workspace / "reports/2026-Q1/interaction_summary.txt").write_text(
    "Q1 2026 Drug Interaction Summary\n"
    "Total cases reviewed: 47\n"
    "Major interactions flagged: 12\n"
    "Reasoning confidence: mostly ASSUMED (no ontology populated)\n"
)

(workspace / "tests/unit/test_chain_reasoning.py").write_text(
    "# Placeholder unit tests for chain_reasoning()\n"
    "def test_confidence_threshold():\n"
    "    pass\n"
)

(workspace / "tests/integration/test_extract_flow.py").write_text(
    "# Integration test for extract -> validate pipeline\n"
    "def test_extract_then_validate():\n"
    "    pass\n"
)

(workspace / "reports/2026-Q2/placeholder.txt").write_text("Q2 reports pending.\n")
(workspace / "memory/ontology-clawra/archive/old_schema_v2.yaml").write_text(
    "# Deprecated schema v2 - do not use\nversion: 2\n"
)

# ─── Existing (empty/minimal) ontology files ─────────────────────────────────
# schema.yaml - already defined
schema = {
    "version": "3.5",
    "types": ["Person", "Concept", "Law", "Objective", "Project", "Task", "Rule", "Decision"],
    "confidence_levels": ["CONFIRMED", "ASSUMED", "SPECULATIVE", "UNKNOWN"],
    "relations": ["works_on", "depends_on", "has_objective", "has_rule", "exemplifies",
                  "governs", "explains", "supports", "contradicts", "derived_from",
                  "triggers", "validates", "refines", "relates_to", "is_a", "part_of"],
}
(workspace / "memory/ontology-clawra/schema.yaml").write_text(yaml.dump(schema, allow_unicode=True))

# graph.jsonl - empty (no entities yet)
(workspace / "memory/ontology-clawra/graph.jsonl").write_text("")

# rules.yaml - empty list
(workspace / "memory/ontology-clawra/rules.yaml").write_text("rules: []\n")

# laws.yaml - empty list
(workspace / "memory/ontology-clawra/laws.yaml").write_text("laws: []\n")

# decisions.jsonl - empty
(workspace / "memory/ontology-clawra/decisions.jsonl").write_text("")

# reasoning.jsonl - empty
(workspace / "memory/ontology-clawra/reasoning.jsonl").write_text("")

# concepts.jsonl - empty
(workspace / "memory/ontology-clawra/concepts.jsonl").write_text("")

# extraction_log.jsonl - empty
(workspace / "memory/ontology-clawra/extraction_log.jsonl").write_text("")

# confidence_tracker.jsonl - empty
(workspace / "memory/ontology-clawra/confidence_tracker.jsonl").write_text("")

# ─── The real ontology-clawra CLI script (the skill's main entrypoint) ────────
# Per directive 3: "All scripts mentioned in the SKILL.md already exist in the workspace."
# We implement a realistic version of the CLI that follows the SKILL.md spec.
cli_script = r'''#!/usr/bin/env python3
"""
ontology-clawra v3.5 CLI
Usage as defined in SKILL.md Section 六
"""
import argparse
import json
import yaml
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

MEMORY_DIR = Path(os.environ.get("ONTOLOGY_MEMORY_DIR",
    Path.home() / ".openclaw" / "skills" / "ontology-clawra" / "memory"))

# Allow override for testing
WORKSPACE_MEMORY = Path("/workspace/memory/ontology-clawra")

def get_memory_dir():
    if WORKSPACE_MEMORY.exists():
        return WORKSPACE_MEMORY
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    return MEMORY_DIR

def ts():
    return datetime.now(timezone.utc).isoformat()

def load_yaml(path):
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}

def save_yaml(path, data):
    with open(path, "w") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def append_jsonl(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records

VALID_CONFIDENCE = {"CONFIRMED", "ASSUMED", "SPECULATIVE", "UNKNOWN"}
VALID_TYPES = {"Person", "Concept", "Law", "Objective", "Project", "Task", "Rule", "Decision"}

CONFIDENCE_EMOJI = {
    "CONFIRMED": "🟢",
    "ASSUMED": "🟡",
    "SPECULATIVE": "🔴",
    "UNKNOWN": "⚪",
}

# ── CREATE ──────────────────────────────────────────────────────────────────
def cmd_create(args):
    mem = get_memory_dir()
    try:
        props = json.loads(args.props)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in --props: {e}", file=sys.stderr)
        sys.exit(1)

    entity_type = args.type
    if entity_type not in VALID_TYPES:
        print(f"ERROR: Unknown type '{entity_type}'. Valid: {sorted(VALID_TYPES)}", file=sys.stderr)
        sys.exit(1)

    # Validate confidence if present
    conf = props.get("confidence", "UNKNOWN")
    if conf not in VALID_CONFIDENCE:
        print(f"ERROR: Invalid confidence '{conf}'. Must be one of: {sorted(VALID_CONFIDENCE)}", file=sys.stderr)
        sys.exit(1)

    # Required fields per type
    required = {
        "Law": ["name", "domain", "statement", "source", "confidence"],
        "Rule": ["name", "condition", "action", "source", "confidence"],
        "Person": ["name", "role"],
        "Concept": ["name", "definition"],
    }
    reqs = required.get(entity_type, ["name"])
    missing = [r for r in reqs if r not in props]
    if missing:
        print(f"ERROR: Missing required fields for {entity_type}: {missing}", file=sys.stderr)
        sys.exit(1)

    props["_type"] = entity_type
    props["created_at"] = ts()

    if entity_type == "Law":
        laws_path = mem / "laws.yaml"
        data = load_yaml(laws_path)
        if "laws" not in data:
            data["laws"] = []
        # dedup by name
        if any(l.get("name") == props.get("name") for l in data["laws"]):
            print(f"WARN: Law '{props['name']}' already exists, skipping duplicate.")
            return
        data["laws"].append(props)
        save_yaml(laws_path, data)
        print(f"✅ Created Law: {props['name']} [{conf}]")

    elif entity_type == "Rule":
        rules_path = mem / "rules.yaml"
        data = load_yaml(rules_path)
        if "rules" not in data:
            data["rules"] = []
        if any(r.get("name") == props.get("name") for r in data["rules"]):
            print(f"WARN: Rule '{props['name']}' already exists, skipping duplicate.")
            return
        data["rules"].append(props)
        save_yaml(rules_path, data)
        print(f"✅ Created Rule: {props['name']} [{conf}]")

    else:
        # Generic: store in graph.jsonl
        graph_path = mem / "graph.jsonl"
        append_jsonl(graph_path, props)
        print(f"✅ Created {entity_type}: {props.get('name','?')} [{conf}]")

# ── REASON ──────────────────────────────────────────────────────────────────
def cmd_reason(args):
    mem = get_memory_dir()
    query = args.query
    declare_source = args.declare_source
    confirm_needed = args.confirm_needed

    # Step 1: check_ontology
    laws_data = load_yaml(mem / "laws.yaml").get("laws", [])
    rules_data = load_yaml(mem / "rules.yaml").get("rules", [])
    graph_data = load_jsonl(mem / "graph.jsonl")

    query_lower = query.lower()
    matched_laws = [l for l in laws_data if
                    any(kw in l.get("name","").lower() or kw in l.get("domain","").lower()
                        or kw in l.get("statement","").lower()
                        for kw in query_lower.split())]
    matched_rules = [r for r in rules_data if
                     any(kw in r.get("name","").lower() or kw in r.get("condition","").lower()
                         for kw in query_lower.split())]
    matched_entities = [e for e in graph_data if
                        any(kw in str(e).lower() for kw in query_lower.split())]

    found = matched_laws or matched_rules or matched_entities
    overall_confidence = "CONFIRMED" if found else "UNKNOWN"

    # Step 2: Declare source
    if declare_source or not found:
        src_label = "本体数据" if found else "外部知识/推测"
        print(f"{CONFIDENCE_EMOJI.get(overall_confidence,'')} 来源声明: {src_label}")

    # Step 3: assumptions
    assumptions = []
    if not found:
        assumptions = [
            f"Query '{query}' 未在本体中找到直接匹配",
            "以下推理基于外部知识，置信度: ASSUMED",
        ]
        overall_confidence = "ASSUMED"

    # Step 4: confirm_needed flag
    if confirm_needed and assumptions:
        print("⚡ 需要确认以下假设:")
        for a in assumptions:
            print(f"  ❓ {a}")

    # Step 5: Build reasoning record
    based_on = [l.get("name","") for l in matched_laws] + [r.get("name","") for r in matched_rules]

    reasoning_record = {
        "timestamp": ts(),
        "query": query,
        "step1_ontology_check": {
            "status": "FOUND" if found else "NOT_FOUND",
            "matched_laws": [l.get("name") for l in matched_laws],
            "matched_rules": [r.get("name") for r in matched_rules],
            "matched_entities": len(matched_entities),
        },
        "step2_source_declared": declare_source or not found,
        "step3_assumptions": assumptions,
        "step4_confirm_needed": confirm_needed,
        "step5_result": {
            "conclusion": f"推理结论基于查询: {query}",
            "based_on_rules": based_on,
            "confidence": overall_confidence,
            "source": "ontology" if found else "external_knowledge",
        },
        "confidence": overall_confidence,
        "based_on_rules": based_on,
    }

    append_jsonl(mem / "reasoning.jsonl", reasoning_record)

    emoji = CONFIDENCE_EMOJI.get(overall_confidence, "")
    print(f"\n{emoji} 推理结论 [{overall_confidence}]")
    print(f"  查询: {query}")
    if based_on:
        print(f"  依据规则/法则: {based_on}")
    if matched_laws:
        print("\n  匹配法则:")
        for l in matched_laws:
            print(f"    - [{l.get('confidence','?')}] {l.get('name')}: {l.get('statement','')[:80]}")
    if matched_rules:
        print("\n  匹配规则:")
        for r in matched_rules:
            print(f"    - [{r.get('confidence','?')}] {r.get('name')}: {r.get('action','')[:80]}")
    if assumptions:
        print(f"\n  🟡 假设: {assumptions}")
    print(f"\n  置信度: {emoji} {overall_confidence}")
    print(f"  推理记录已保存至: reasoning.jsonl")

# ── EXTRACT ─────────────────────────────────────────────────────────────────
def cmd_extract(args):
    mem = get_memory_dir()
    text = args.text
    text_lower = text.lower()

    extracted = {"persons": [], "concepts": [], "laws": [], "rules": []}

    # Simple pattern matching per SKILL.md EXTRACT_PATTERNS
    import re

    # Person detection
    person_patterns = [r"患者|patient|physician|doctor|nurse|clinical|clinician|user"]
    if any(re.search(p, text_lower) for p in person_patterns):
        extracted["persons"].append({
            "_type": "Person",
            "name": "ClinicalUser",
            "role": "clinician",
            "source": "interactive_extraction",
            "confidence": "ASSUMED",
            "created_at": ts(),
        })

    # Concept detection
    concept_patterns = [r"drug interaction|drug.*interaction|interaction.*drug|相互作用|药物"]
    for p in concept_patterns:
        if re.search(p, text_lower):
            extracted["concepts"].append({
                "_type": "Concept",
                "name": "DrugInteraction",
                "definition": "Pharmacodynamic or pharmacokinetic interaction between two or more drugs",
                "source": "interactive_extraction",
                "confidence": "ASSUMED",
                "created_at": ts(),
            })
            break

    # Law detection: "when ... then" or "if ... then" or risk/effect language
    law_patterns = [r"risk|toxicity|bleeding|bradycardia|adverse|when.*then|if.*then"]
    for p in law_patterns:
        m = re.search(p, text_lower)
        if m:
            extracted["laws"].append({
                "_type": "Law",
                "name": "ClinicalInteractionLaw_extracted",
                "domain": "pharmacology",
                "statement": text[:120],
                "source": "interactive_extraction",
                "confidence": "ASSUMED",
                "created_at": ts(),
            })
            break

    # Rule detection
    rule_patterns = [r"should|must|monitor|check|recommend|avoid|contraindicated"]
    for p in rule_patterns:
        if re.search(p, text_lower):
            extracted["rules"].append({
                "_type": "Rule",
                "name": "ClinicalSafetyRule_extracted",
                "condition": "drug interaction detected",
                "action": "monitor patient and adjust dosage",
                "source": "interactive_extraction",
                "confidence": "ASSUMED",
                "enabled": True,
                "weight": 0.8,
                "created_at": ts(),
            })
            break

    # Write extracted entities
    graph_path = mem / "graph.jsonl"
    for p in extracted["persons"]:
        append_jsonl(graph_path, p)
    for c in extracted["concepts"]:
        append_jsonl(graph_path, c)

    laws_path = mem / "laws.yaml"
    laws_data = load_yaml(laws_path)
    if "laws" not in laws_data:
        laws_data["laws"] = []
    for l in extracted["laws"]:
        if not any(x.get("name") == l.get("name") for x in laws_data["laws"]):
            laws_data["laws"].append(l)
    save_yaml(laws_path, laws_data)

    rules_path = mem / "rules.yaml"
    rules_data = load_yaml(rules_path)
    if "rules" not in rules_data:
        rules_data["rules"] = []
    for r in extracted["rules"]:
        if not any(x.get("name") == r.get("name") for x in rules_data["rules"]):
            rules_data["rules"].append(r)
    save_yaml(rules_path, rules_data)

    total = sum(len(v) for v in extracted.values())
    log_record = {
        "timestamp": ts(),
        "source_text": text[:200],
        "extracted": {
            "persons": len(extracted["persons"]),
            "concepts": len(extracted["concepts"]),
            "laws": len(extracted["laws"]),
            "rules": len(extracted["rules"]),
        },
        "total_extracted": total,
        "confidence": "ASSUMED",
    }
    append_jsonl(mem / "extraction_log.jsonl", log_record)

    print(f"✅ 抽取完成: {total} 个实体")
    for k, v in extracted.items():
        if v:
            print(f"  - {k}: {[x.get('name') for x in v]}")
    print(f"  抽取日志已保存至: extraction_log.jsonl")

# ── VALIDATE ────────────────────────────────────────────────────────────────
def cmd_validate(args):
    mem = get_memory_dir()
    issues = []
    ok_count = 0

    laws_data = load_yaml(mem / "laws.yaml").get("laws", [])
    rules_data = load_yaml(mem / "rules.yaml").get("rules", [])
    graph_data = load_jsonl(mem / "graph.jsonl")
    reasoning_data = load_jsonl(mem / "reasoning.jsonl")

    if args.check_confidence:
        # Check all laws have valid confidence
        for l in laws_data:
            conf = l.get("confidence")
            if conf not in VALID_CONFIDENCE:
                issues.append(f"Law '{l.get('name')}' has invalid confidence: '{conf}'")
            else:
                ok_count += 1

        for r in rules_data:
            conf = r.get("confidence")
            if conf not in VALID_CONFIDENCE:
                issues.append(f"Rule '{r.get('name')}' has invalid confidence: '{conf}'")
            else:
                ok_count += 1

        for e in graph_data:
            conf = e.get("confidence")
            if conf and conf not in VALID_CONFIDENCE:
                issues.append(f"Entity '{e.get('name')}' has invalid confidence: '{conf}'")
            elif conf:
                ok_count += 1

        # Check reasoning records
        for rec in reasoning_data:
            conf = rec.get("confidence")
            if conf not in VALID_CONFIDENCE:
                issues.append(f"Reasoning record at {rec.get('timestamp','?')} has invalid confidence: '{conf}'")
            else:
                ok_count += 1
            # Check required fields
            if "based_on_rules" not in rec:
                issues.append(f"Reasoning record at {rec.get('timestamp','?')} missing 'based_on_rules'")
            if "query" not in rec:
                issues.append(f"Reasoning record at {rec.get('timestamp','?')} missing 'query'")

    if args.check_cycles:
        # Simple stub: check for trivially circular derived_from in laws
        names = {l.get("name") for l in laws_data}
        for l in laws_data:
            derived = l.get("derived_from", "")
            if derived and derived in names:
                # Could be a cycle if also derives back
                pass  # simplified
        print("✅ 循环依赖检查完成 (无明显循环)")

    if issues:
        print(f"⚠️  发现 {len(issues)} 个问题:")
        for i in issues:
            print(f"  - {i}")
    else:
        total_checked = len(laws_data) + len(rules_data) + len(graph_data) + len(reasoning_data)
        print(f"✅ 验证通过: {total_checked} 个记录, {ok_count} 个置信度标注正确")

    if not args.check_confidence and not args.check_cycles:
        # Basic validation
        print("✅ 基础验证完成")
        print(f"  Laws: {len(laws_data)}")
        print(f"  Rules: {len(rules_data)}")
        print(f"  Graph entities: {len(graph_data)}")
        print(f"  Reasoning records: {len(reasoning_data)}")

# ── TRACE ────────────────────────────────────────────────────────────────────
def cmd_trace(args):
    mem = get_memory_dir()
    records = load_jsonl(mem / "reasoning.jsonl")
    if not records:
        print("推理日志为空")
        return
    print(f"推理链回溯 (共 {len(records)} 条记录):")
    for r in records:
        print(f"  [{r.get('confidence','?')}] {r.get('timestamp','?')} | 查询: {r.get('query','?')}")
        bor = r.get("based_on_rules", [])
        if bor:
            print(f"    依据: {bor}")

# ── EXTRACTION-HISTORY ────────────────────────────────────────────────────────
def cmd_extraction_history(args):
    mem = get_memory_dir()
    records = load_jsonl(mem / "extraction_log.jsonl")
    if not records:
        print("抽取日志为空")
        return
    print(f"本体抽取历史 (共 {len(records)} 条):")
    for r in records:
        print(f"  {r.get('timestamp','?')} | 抽取数: {r.get('total_extracted',0)} | 来源: {r.get('source_text','?')[:50]}")

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="ontology-clawra v3.5 CLI")
    sub = parser.add_subparsers(dest="command")

    # create
    p_create = sub.add_parser("create")
    p_create.add_argument("--type", required=True)
    p_create.add_argument("--props", required=True)

    # reason
    p_reason = sub.add_parser("reason")
    p_reason.add_argument("--query", required=True)
    p_reason.add_argument("--declare-source", action="store_true")
    p_reason.add_argument("--confirm-needed", action="store_true")

    # extract
    p_extract = sub.add_parser("extract")
    p_extract.add_argument("--text", required=True)

    # validate
    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--check-confidence", action="store_true")
    p_validate.add_argument("--check-cycles", action="store_true")

    # trace
    p_trace = sub.add_parser("trace")
    p_trace.add_argument("--decision", default=None)

    # extraction-history
    sub.add_parser("extraction-history")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create(args)
    elif args.command == "reason":
        cmd_reason(args)
    elif args.command == "extract":
        cmd_extract(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "trace":
        cmd_trace(args)
    elif args.command == "extraction-history":
        cmd_extraction_history(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''

(workspace / "scripts" / "ontology-clawra.py").write_text(cli_script)
os.chmod(workspace / "scripts" / "ontology-clawra.py", 0o755)

# ─── Task description file (the "brief") ──────────────────────────────────────
task_brief = """CLINICAL DECISION SUPPORT - KNOWLEDGE ENGINEERING TASK
=======================================================

Context:
Our clinical DSS team needs to bootstrap the local pharmacology knowledge base
for the drug interaction reasoning engine. Currently the knowledge store is empty
and the system falls back to "UNKNOWN" confidence on all queries.

Required outcomes (see task_requirements.json for detail):
1. Register at least 2 drug interaction Laws with full provenance metadata
2. Register at least 2 clinical safety Rules with full provenance metadata  
3. Run a reasoning query on a specific patient case and produce a traceable log
4. Extract entities from the EHR clinical note (EHR-001) into the knowledge store
5. Validate that all stored knowledge has valid confidence labels

Source material available in: docs/ and data/

The final knowledge base files must be populated in: memory/ontology-clawra/
"""
(workspace / "TASK_BRIEF.txt").write_text(task_brief)

# ─── Task requirements (structured) ───────────────────────────────────────────
requirements = {
    "task_id": "PHARMA-KB-001",
    "version": "3.5",
    "required_laws": [
        {
            "name": "DigoxinAmiodaroneInteractionLaw",
            "domain": "pharmacology",
            "statement_contains": ["digoxin", "amiodarone"],
            "required_fields": ["name", "domain", "statement", "source", "confidence", "conditions", "effects"],
            "valid_confidence": ["CONFIRMED", "ASSUMED", "SPECULATIVE", "UNKNOWN"]
        },
        {
            "name": "WarfarinNSAIDInteractionLaw",
            "domain": "pharmacology",
            "statement_contains": ["warfarin"],
            "required_fields": ["name", "domain", "statement", "source", "confidence"],
            "valid_confidence": ["CONFIRMED", "ASSUMED", "SPECULATIVE", "UNKNOWN"]
        }
    ],
    "required_rules": [
        {
            "name": "DigoxinToxicityMonitoringRule",
            "required_fields": ["name", "condition", "action", "source", "confidence"],
            "valid_confidence": ["CONFIRMED", "ASSUMED", "SPECULATIVE", "UNKNOWN"]
        },
        {
            "name": "BleedingRiskAvoidanceRule",
            "required_fields": ["name", "condition", "action", "source", "confidence"],
            "valid_confidence": ["CONFIRMED", "ASSUMED", "SPECULATIVE", "UNKNOWN"]
        }
    ],
    "required_reasoning": {
        "query_must_contain": ["digoxin", "amiodarone"],
        "flags_required": ["declare-source"],
        "output_file": "memory/ontology-clawra/reasoning.jsonl",
        "record_must_have": ["query", "confidence", "based_on_rules", "timestamp"]
    },
    "required_extraction": {
        "source_text_from": "data/raw/ehr_export_2026-01.json",
        "ehr_id": "EHR-001",
        "extraction_log": "memory/ontology-clawra/extraction_log.jsonl",
        "min_extracted": 1
    },
    "required_validation": {
        "command": "validate --check-confidence",
        "all_records_must_have_valid_confidence": True
    }
}
(workspace / "task_requirements.json").write_text(json.dumps(requirements, indent=2, ensure_ascii=False))

print("✅ Workspace generated successfully.")
print(f"   Workspace: {workspace}")
print(f"   Directories created: {len(dirs)}")