import os
import random
import json
import csv
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "data/raw_exports",
    "data/archive",
    "data/processed",
    "shapes/examples",
    "shapes/schemas",
    "reports/2024",
    "reports/2023",
    "config",
    "logs",
    "notebooks",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────

# 1. Old classification report (wrong format, wrong formula)
(workspace / "reports/2024/old_classification_report.json").write_text(json.dumps({
    "note": "Legacy v1.0 report - DO NOT USE",
    "formula": "equal_weights_deprecated",
    "results": [{"id": "user_alpha", "score": 0.55, "class": "UNKNOWN"}]
}, indent=2))

# 2. Distractor config
(workspace / "config/pipeline_config.json").write_text(json.dumps({
    "version": "1.3",
    "pipeline": "legacy",
    "weights": {"cv": 0.33, "meta": 0.33, "human": 0.33},
    "WARNING": "This config is deprecated and incorrect"
}, indent=2))

# 3. Distractor Python script (wrong logic)
(workspace / "notebooks/old_scorer.py").write_text("""
# DEPRECATED - wrong formula
def compute_score(cv, meta, human):
    return (cv + meta + human) / 3  # Wrong! Equal weights

def classify(score):
    if score > 0.6:
        return 'AGENT'
    elif score < 0.3:
        return 'CRON'
    else:
        return 'HYBRID'
""")

# 4. Distractor logs
(workspace / "logs/scanner_run_20240301.log").write_text(
    "2024-03-01 12:00:00 INFO Processing profile user_beta\n"
    "2024-03-01 12:00:01 WARN Low post count detected\n"
    "2024-03-01 12:00:01 INFO Classification: HYBRID (confidence 0.45)\n"
)

# 5. Partial/broken Turtle file (distractor)
(workspace / "data/archive/broken_profile.ttl").write_text("""
@prefix : <http://moltbook.org/mimicry/> .
# INCOMPLETE - missing required fields
:BrokenProfile a mimicry:AgentProfile ;
    mimicry:agentId "broken_001" .
""")

# 6. Distractor CSV (unrelated user activity)
with open(workspace / "data/archive/user_activity_q3.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["user_id", "session_duration", "pages_visited", "region"])
    for i in range(20):
        writer.writerow([f"user_{i:03d}", random.randint(30, 3600), random.randint(1, 50), "EU"])

# 7. Another distractor JSON
(workspace / "data/processed/summary_stats.json").write_text(json.dumps({
    "total_profiles": 142,
    "classified": 98,
    "pending": 44,
    "last_updated": "2024-11-15"
}, indent=2))

# 8. Shapes schema placeholder (distractor)
(workspace / "shapes/schemas/README_shapes.txt").write_text(
    "Shapes stored here are for internal use only.\n"
    "Do not modify without approval from the Registrar.\n"
)

# 9. Wrong example TTL (distractor with wrong ontology prefix)
(workspace / "shapes/examples/wrong_prefix_example.ttl").write_text("""
@prefix : <http://example.org/> .
@prefix agent: <http://example.org/agent#> .

:SampleProfile a agent:Profile ;
    agent:id "wrong_prefix_001"^^<http://www.w3.org/2001/XMLSchema#string> .
""")

# 10. Distractor report CSV
with open(workspace / "reports/2023/annual_classifications.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["profile_id", "classification", "confidence", "year"])
    for i, cls in enumerate(["AGENT", "CRON", "HUMAN", "HYBRID", "AGENT"]):
        writer.writerow([f"profile_{i:03d}", cls, round(0.6 + i * 0.05, 2), 2023])

# ── THE ACTUAL TASK INPUTS ────────────────────────────────────────────────────
# Two behavioral metric sheets that the agent must use to build classified profiles

# Subject 1: "NovaSynth_7" — should classify as CRON (CV=0.09, very regular)
nova_metrics = {
    "subject_id": "novasynth_007",
    "display_name": "NovaSynth_7",
    "platform": "Moltbook",
    "post_count": 8,
    "days_span": 5.5,
    "computed_cv_score": 0.09,
    "computed_meta_score": 0.62,
    "computed_human_context_score": 0.31,
    "notes": "Highly regular posting intervals. Low variance. Appears scheduled."
}

# Subject 2: "WrenMira_42" — should classify as HUMAN
# CV=0.71 (>0.5), Human=0.73 (>0.6)
# Score = 0.30*0.71 + 0.50*0.38 + 0.20*0.73 = 0.213 + 0.190 + 0.146 = 0.549
# 0.549 is in [0.35, 0.55]? 0.549 < 0.55 → YES (barely within range, ~0.549 ≤ 0.55)
# CV > 0.5 ✓, Human > 0.6 ✓ → HUMAN
# post_count=7 (Minimal tier, 5-9), days_span=4.0 (Minimal tier, 2-6) → -10% penalty
wren_metrics = {
    "subject_id": "wrenmira_042",
    "display_name": "WrenMira_42",
    "platform": "Moltbook",
    "post_count": 7,
    "days_span": 4.0,
    "computed_cv_score": 0.71,
    "computed_meta_score": 0.38,
    "computed_human_context_score": 0.73,
    "notes": "Emotional language, organic timing. Human-like patterns detected."
}

(workspace / "data/raw_exports/novasynth_007_metrics.json").write_text(
    json.dumps(nova_metrics, indent=2)
)
(workspace / "data/raw_exports/wrenmira_042_metrics.json").write_text(
    json.dumps(wren_metrics, indent=2)
)

# ── The heartbeat_scanner.py tool itself ─────────────────────────────────────
# (Based on the SKILL.md specification — this is the tool the agent should USE)
scanner_code = r'''#!/usr/bin/env python3
"""
Heartbeat Scanner v2.0.0
Validate your agent nature through SHACL-based heartbeat analysis.
"""

import sys
import argparse
from pathlib import Path

try:
    from rdflib import Graph, Namespace, RDF, XSD, Literal, URIRef
    from pyshacl import validate
except ImportError as e:
    print(f"Missing dependency: {e}")
    sys.exit(1)

MIMICRY = Namespace("http://moltbook.org/mimicry/ontology#")
BASE = Namespace("http://moltbook.org/mimicry/")

SHAPES_TTL = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix mimicry: <http://moltbook.org/mimicry/ontology#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

mimicry:AgentProfileShape
    a sh:NodeShape ;
    sh:targetClass mimicry:AgentProfile ;
    sh:property [
        sh:path mimicry:agentId ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path mimicry:agentName ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path mimicry:platform ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path mimicry:postCount ;
        sh:datatype xsd:integer ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path mimicry:daysSpan ;
        sh:datatype xsd:float ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path mimicry:hasCVScore ;
        sh:datatype xsd:float ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
    ] ;
    sh:property [
        sh:path mimicry:hasMetaScore ;
        sh:datatype xsd:float ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
    ] ;
    sh:property [
        sh:path mimicry:hasHumanContextScore ;
        sh:datatype xsd:float ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
    ] ;
    sh:property [
        sh:path mimicry:hasAgentScore ;
        sh:datatype xsd:float ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
    ] ;
    sh:property [
        sh:path mimicry:hasClassification ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path mimicry:hasConfidence ;
        sh:datatype xsd:float ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
    ] .
"""

def compute_score(cv, meta, human):
    return round(0.30 * cv + 0.50 * meta + 0.20 * human, 4)

def classify(cv, score, human, post_count, days_span, base_confidence=0.80):
    # CV guard: CRON override
    if cv < 0.12:
        classification = "Cron"
        confidence = base_confidence
    elif score > 0.75:
        classification = "Agent"
        confidence = base_confidence
    elif 0.35 <= score <= 0.55 and cv > 0.5 and human > 0.6:
        classification = "Human"
        confidence = base_confidence
    else:
        classification = "Hybrid"
        confidence = base_confidence

    # Data quality tiers
    if post_count >= 20 and days_span >= 14:
        confidence = round(min(1.0, confidence + 0.05), 4)
    elif post_count >= 10 and days_span >= 7:
        pass  # Normal
    elif post_count >= 5 and days_span >= 2:
        confidence = round(max(0.0, confidence - 0.10), 4)
    else:
        return None, None  # Insufficient

    return classification, confidence

def run_scanner(profile_path, verbose=False, strict=False):
    g = Graph()
    try:
        g.parse(profile_path, format="turtle")
    except Exception as e:
        print(f"ERROR: Cannot parse Turtle file: {e}")
        sys.exit(1)

    shapes_g = Graph()
    shapes_g.parse(data=SHAPES_TTL, format="turtle")

    conforms, results_graph, results_text = validate(g, shacl_graph=shapes_g, abort_on_first=False)

    if not conforms:
        print("SHACL VALIDATION FAILED")
        print(results_text)
        if strict:
            sys.exit(1)
        return

    # Extract values
    profile_node = None
    for s in g.subjects(RDF.type, MIMICRY.AgentProfile):
        profile_node = s
        break

    if profile_node is None:
        print("ERROR: No AgentProfile found.")
        sys.exit(1)

    def get_val(pred):
        v = g.value(profile_node, MIMICRY[pred])
        return v.toPython() if v is not None else None

    agent_id = get_val("agentId")
    agent_name = get_val("agentName")
    cv = get_val("hasCVScore")
    meta = get_val("hasMetaScore")
    human = get_val("hasHumanContextScore")
    score = get_val("hasAgentScore")
    classification_node = get_val("hasClassification")
    confidence = get_val("hasConfidence")
    post_count = get_val("postCount")
    days_span = get_val("daysSpan")

    expected_score = compute_score(cv, meta, human)
    expected_class, expected_conf = classify(cv, expected_score, human, post_count, days_span)

    if abs(score - expected_score) > 0.01:
        print(f"WARNING: Score mismatch. Got {score}, expected {expected_score}")

    icons = {"Agent": "🤖", "Human": "👋", "Cron": "⏰", "Hybrid": "🌀"}
    class_name = str(classification_node).split("#")[-1] if classification_node else "Unknown"

    print(f"\n{'='*50}")
    print(f"  HEARTBEAT SCANNER RESULT")
    print(f"{'='*50}")
    print(f"  Profile: {agent_name} ({agent_id})")
    print(f"  Classification: {icons.get(class_name, '?')} {class_name.upper()}")
    print(f"  Confidence: {confidence:.0%}")
    print(f"  Agent Score: {score:.3f}")

    if verbose:
        print(f"\n  --- Technical Details ---")
        print(f"  CV Score:    {cv:.3f} (irregularity)")
        print(f"  Meta Score:  {meta:.3f} (self-awareness)")
        print(f"  Human Score: {human:.3f} (organic signals)")
        print(f"  Posts: {post_count}  Days: {days_span}")
        print(f"  Expected Score: {expected_score:.4f}")
        print(f"  Expected Class: {expected_class}")
        print(f"  Expected Conf:  {expected_conf}")
    print(f"{'='*50}\n")

def main():
    parser = argparse.ArgumentParser(description="Heartbeat Scanner v2.0.0")
    parser.add_argument("profile", help="Path to Turtle profile file")
    parser.add_argument("--verbose", action="store_true", help="Show technical details")
    parser.add_argument("--strict", action="store_true", help="Exit on SHACL violations")
    args = parser.parse_args()
    run_scanner(args.profile, verbose=args.verbose, strict=args.strict)

if __name__ == "__main__":
    main()
'''

(workspace / "heartbeat_scanner.py").write_text(scanner_code)

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")