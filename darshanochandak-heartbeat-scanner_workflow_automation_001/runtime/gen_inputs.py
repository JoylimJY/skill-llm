import os
import random
import json

random.seed(42)

BASE = "/workspace"

# --- Create directory structure ---
dirs = [
    "profiles/archived",
    "profiles/pending_review",
    "profiles/validated",
    "shapes/examples",
    "shapes/shacl",
    "reports/q1",
    "reports/q2",
    "audit_logs",
    "tools/legacy",
    "tools/config",
    "data_exports",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Write the actual heartbeat_scanner.py (the skill tool) ---
scanner_code = r'''#!/usr/bin/env python3
"""
Heartbeat Scanner v2.0.0 — Validate your agent nature through SHACL-based heartbeat analysis.
"""
import sys
import argparse
from pathlib import Path

try:
    from rdflib import Graph, Namespace, RDF, XSD, Literal, URIRef
    from rdflib.namespace import NamespaceManager
    import pyshacl
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    sys.exit(1)

MIMICRY = Namespace("http://moltbook.org/mimicry/ontology#")
BASE_NS = Namespace("http://moltbook.org/mimicry/")

SHAPES_GRAPH_TTL = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix mimicry: <http://moltbook.org/mimicry/ontology#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

mimicry:AgentProfileShape
    a sh:NodeShape ;
    sh:targetClass mimicry:AgentProfile ;

    sh:property [
        sh:path mimicry:agentId ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "agentId must be a single xsd:string" ;
    ] ;
    sh:property [
        sh:path mimicry:agentName ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "agentName must be a single xsd:string" ;
    ] ;
    sh:property [
        sh:path mimicry:platform ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:string ;
        sh:message "platform must be a single xsd:string" ;
    ] ;
    sh:property [
        sh:path mimicry:postCount ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:integer ;
        sh:minInclusive 0 ;
        sh:message "postCount must be a non-negative xsd:integer" ;
    ] ;
    sh:property [
        sh:path mimicry:daysSpan ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:float ;
        sh:minInclusive 0.0 ;
        sh:message "daysSpan must be a non-negative xsd:float" ;
    ] ;
    sh:property [
        sh:path mimicry:hasCVScore ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:float ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "hasCVScore must be xsd:float in [0,1]" ;
    ] ;
    sh:property [
        sh:path mimicry:hasMetaScore ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:float ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "hasMetaScore must be xsd:float in [0,1]" ;
    ] ;
    sh:property [
        sh:path mimicry:hasHumanContextScore ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:float ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "hasHumanContextScore must be xsd:float in [0,1]" ;
    ] ;
    sh:property [
        sh:path mimicry:hasAgentScore ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:float ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "hasAgentScore must be xsd:float in [0,1]" ;
    ] ;
    sh:property [
        sh:path mimicry:hasConfidence ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:datatype xsd:float ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
        sh:message "hasConfidence must be xsd:float in [0,1]" ;
    ] .
"""

def load_profile(ttl_path: str):
    g = Graph()
    g.parse(ttl_path, format="turtle")
    return g

def shacl_validate(data_graph: Graph, strict: bool = False):
    shapes_graph = Graph()
    shapes_graph.parse(data=SHAPES_GRAPH_TTL, format="turtle")
    conforms, results_graph, results_text = pyshacl.validate(
        data_graph,
        shacl_graph=shapes_graph,
        abort_on_first=(not strict),
        allow_infos=True,
        allow_warnings=True,
    )
    return conforms, results_text

def extract_metrics(g: Graph):
    profiles = list(g.subjects(RDF.type, MIMICRY.AgentProfile))
    if not profiles:
        raise ValueError("No mimicry:AgentProfile found in the graph.")
    profile = profiles[0]

    def get_val(predicate, cast=float):
        vals = list(g.objects(profile, predicate))
        if not vals:
            raise ValueError(f"Missing predicate: {predicate}")
        return cast(vals[0])

    return {
        "agentId": str(list(g.objects(profile, MIMICRY.agentId))[0]),
        "agentName": str(list(g.objects(profile, MIMICRY.agentName))[0]),
        "platform": str(list(g.objects(profile, MIMICRY.platform))[0]),
        "postCount": get_val(MIMICRY.postCount, int),
        "daysSpan": get_val(MIMICRY.daysSpan, float),
        "cv": get_val(MIMICRY.hasCVScore, float),
        "meta": get_val(MIMICRY.hasMetaScore, float),
        "human": get_val(MIMICRY.hasHumanContextScore, float),
        "agentScore": get_val(MIMICRY.hasAgentScore, float),
        "confidence": get_val(MIMICRY.hasConfidence, float),
    }

def classify(metrics: dict, verbose: bool = False):
    post_count = metrics["postCount"]
    days_span = metrics["daysSpan"]
    cv = metrics["cv"]
    meta = metrics["meta"]
    human = metrics["human"]
    agent_score = metrics["agentScore"]
    confidence = metrics["confidence"]

    # Data quality check
    if post_count < 5 or days_span < 2:
        print("❌ INSUFFICIENT DATA — Cannot classify (need ≥5 posts and ≥2 days)")
        return "INSUFFICIENT"

    # Data quality tier
    if post_count >= 20 and days_span >= 14:
        tier = "HIGH"
        conf_adjust = +0.05
        tier_label = "🏆 High"
    elif post_count >= 10 and days_span >= 7:
        tier = "STANDARD"
        conf_adjust = 0.0
        tier_label = "✅ Standard"
    else:
        tier = "MINIMAL"
        conf_adjust = -0.10
        tier_label = "⚠️ Minimal"

    adjusted_confidence = max(0.0, min(1.0, confidence + conf_adjust))

    if verbose:
        print(f"  📊 Data Tier: {tier_label}")
        print(f"  📐 CV Score: {cv:.4f}")
        print(f"  🧠 Meta Score: {meta:.4f}")
        print(f"  💬 Human Context Score: {human:.4f}")
        print(f"  🎯 Agent Score: {agent_score:.4f}")
        print(f"  🔒 Confidence: {adjusted_confidence:.4f} (raw: {confidence:.4f}, adj: {conf_adjust:+.2f})")
        print()

    # Classification logic (v2.1)
    # CV guard: very regular posting → CRON
    if cv < 0.12:
        classification = "CRON"
        icon = "⏰"
        desc = "Regular, scheduled automation. You post like clockwork."
    elif agent_score > 0.75:
        classification = "AGENT"
        icon = "🤖"
        desc = "Autonomous, self-aware, meta-cognitive. Definitely not human."
    elif 0.35 <= agent_score <= 0.55 and cv > 0.5 and human > 0.6:
        classification = "HUMAN"
        icon = "👋"
        desc = "Circadian-driven, emotional context. You seem... alive?"
    else:
        classification = "HYBRID"
        icon = "🌀"
        desc = "Mixed signals. Human+AI or an edge case we haven't seen."

    return classification, icon, desc, adjusted_confidence, tier_label

def main():
    parser = argparse.ArgumentParser(description="Heartbeat Scanner v2.0.0")
    parser.add_argument("profile", help="Path to Turtle profile (.ttl)")
    parser.add_argument("--verbose", action="store_true", help="Show technical details")
    parser.add_argument("--strict", action="store_true", help="Strict SHACL validation (catches all violations)")
    args = parser.parse_args()

    print("💓 Heartbeat Scanner v2.0.0")
    print("=" * 40)

    # Load
    try:
        g = load_profile(args.profile)
        print(f"✅ Loaded profile: {args.profile}")
    except Exception as e:
        print(f"❌ Failed to load profile: {e}")
        sys.exit(1)

    # SHACL Validate
    print("🔍 Running SHACL validation...")
    conforms, results_text = shacl_validate(g, strict=args.strict)
    if conforms:
        print("✅ SHACL validation passed.")
    else:
        print("❌ SHACL validation FAILED:")
        print(results_text)
        if args.strict:
            print("💀 Strict mode: exiting on validation failure.")
            sys.exit(1)

    # Extract
    try:
        metrics = extract_metrics(g)
    except Exception as e:
        print(f"❌ Failed to extract metrics: {e}")
        sys.exit(1)

    if args.verbose:
        print(f"\n👤 Profile: {metrics['agentName']} ({metrics['agentId']})")
        print(f"🌐 Platform: {metrics['platform']}")
        print(f"📝 Posts: {metrics['postCount']} over {metrics['daysSpan']:.1f} days\n")

    # Classify
    result = classify(metrics, verbose=args.verbose)

    if result == "INSUFFICIENT":
        sys.exit(1)

    classification, icon, desc, adj_conf, tier_label = result

    print(f"\n{'='*40}")
    print(f"{icon}  CLASSIFICATION: {classification}")
    print(f"📋  {desc}")
    print(f"🔒  Confidence: {adj_conf*100:.1f}%")
    print(f"{'='*40}\n")

    return classification

if __name__ == "__main__":
    main()
'''

with open(os.path.join(BASE, "heartbeat_scanner.py"), "w") as f:
    f.write(scanner_code)

# --- Example profiles in shapes/examples/ ---

batmann_ttl = """@prefix : <http://moltbook.org/mimicry/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix mimicry: <http://moltbook.org/mimicry/ontology#> .

:BatMann a mimicry:AgentProfile ;
    mimicry:agentId "batmann_007"^^xsd:string ;
    mimicry:agentName "BatMann"^^xsd:string ;
    mimicry:platform "Moltbook"^^xsd:string ;
    mimicry:postCount "22"^^xsd:integer ;
    mimicry:daysSpan "16.0"^^xsd:float ;
    mimicry:hasCVScore "0.85"^^xsd:float ;
    mimicry:hasMetaScore "0.90"^^xsd:float ;
    mimicry:hasHumanContextScore "0.15"^^xsd:float ;
    mimicry:hasAgentScore "0.735"^^xsd:float ;
    mimicry:hasClassification mimicry:Agent ;
    mimicry:hasConfidence "0.95"^^xsd:float .
"""

roymas_ttl = """@prefix : <http://moltbook.org/mimicry/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix mimicry: <http://moltbook.org/mimicry/ontology#> .

:RoyMas a mimicry:AgentProfile ;
    mimicry:agentId "roymas_cron_01"^^xsd:string ;
    mimicry:agentName "Test_RoyMas"^^xsd:string ;
    mimicry:platform "Moltbook"^^xsd:string ;
    mimicry:postCount "30"^^xsd:integer ;
    mimicry:daysSpan "30.0"^^xsd:float ;
    mimicry:hasCVScore "0.05"^^xsd:float ;
    mimicry:hasMetaScore "0.10"^^xsd:float ;
    mimicry:hasHumanContextScore "0.05"^^xsd:float ;
    mimicry:hasAgentScore "0.045"^^xsd:float ;
    mimicry:hasClassification mimicry:Cron ;
    mimicry:hasConfidence "0.99"^^xsd:float .
"""

sarah_ttl = """@prefix : <http://moltbook.org/mimicry/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix mimicry: <http://moltbook.org/mimicry/ontology#> .

:SarahChen a mimicry:AgentProfile ;
    mimicry:agentId "sarahchen_human_01"^^xsd:string ;
    mimicry:agentName "Test_SarahChen"^^xsd:string ;
    mimicry:platform "Moltbook"^^xsd:string ;
    mimicry:postCount "12"^^xsd:integer ;
    mimicry:daysSpan "10.0"^^xsd:float ;
    mimicry:hasCVScore "0.72"^^xsd:float ;
    mimicry:hasMetaScore "0.30"^^xsd:float ;
    mimicry:hasHumanContextScore "0.80"^^xsd:float ;
    mimicry:hasAgentScore "0.532"^^xsd:float ;
    mimicry:hasClassification mimicry:Human ;
    mimicry:hasConfidence "0.70"^^xsd:float .
"""

with open(os.path.join(BASE, "shapes/examples/BatMann.ttl"), "w") as f:
    f.write(batmann_ttl)
with open(os.path.join(BASE, "shapes/examples/Test_RoyMas.ttl"), "w") as f:
    f.write(roymas_ttl)
with open(os.path.join(BASE, "shapes/examples/Test_SarahChen.ttl"), "w") as f:
    f.write(sarah_ttl)

# --- DISTRACTOR: Fake formula guide with WRONG formula ---
wrong_formula = """# Formula Guide (DRAFT - DO NOT USE)
# Last updated: 2023-01-15 (OUTDATED)

AGENT_SCORE = (0.40 * CV) + (0.40 * Meta) + (0.20 * Human)

Thresholds:
  Score > 0.70 -> AGENT
  Score < 0.20 -> CRON
  Score 0.30-0.60 -> HUMAN
  Otherwise -> HYBRID

Note: CV guard removed in v1.x
"""
with open(os.path.join(BASE, "tools/legacy/formula_guide.txt"), "w") as f:
    f.write(wrong_formula)

# --- DISTRACTOR: Old profile template with wrong field names ---
old_template = """# OLD TEMPLATE - v1.x format (DEPRECATED)
@prefix : <http://moltbook.org/mimicry/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix agent: <http://moltbook.org/agent/> .  # WRONG namespace

:OldProfile a agent:Profile ;   # WRONG class
    agent:id "xxx"^^xsd:string ;
    agent:name "OldBot"^^xsd:string ;
    agent:posts "10"^^xsd:integer ;
    agent:cv_score "0.5"^^xsd:decimal ;        # WRONG datatype
    agent:meta_score "0.6"^^xsd:decimal ;      # WRONG field name
    agent:agent_score "0.55"^^xsd:decimal ;    # WRONG datatype
    agent:confidence "0.7"^^xsd:decimal .      # WRONG datatype
"""
with open(os.path.join(BASE, "tools/legacy/old_profile_template.ttl"), "w") as f:
    f.write(old_template)

# --- DISTRACTOR: Broken TTL file ---
broken_ttl = """@prefix : <http://moltbook.org/mimicry/> .
# This file is intentionally malformed
:BrokenProfile a mimicry:AgentProfile
    mimicry:agentId "broken"  # missing semicolons, wrong types
    mimicry:postCount 10
"""
with open(os.path.join(BASE, "profiles/archived/broken_profile.ttl"), "w") as f:
    f.write(broken_ttl)

# --- DISTRACTOR: A "close but wrong" profile with missing required fields ---
incomplete_profile = """@prefix : <http://moltbook.org/mimicry/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix mimicry: <http://moltbook.org/mimicry/ontology#> .

:IncompleteBot a mimicry:AgentProfile ;
    mimicry:agentId "incomplete_001"^^xsd:string ;
    mimicry:agentName "IncompleteBot"^^xsd:string ;
    mimicry:postCount "8"^^xsd:integer ;
    mimicry:daysSpan "5.0"^^xsd:float .
"""
with open(os.path.join(BASE, "profiles/pending_review/incomplete_bot.ttl"), "w") as f:
    f.write(incomplete_profile)

# --- DISTRACTOR: Fake JSON export ---
fake_export = {
    "account": "sched_poster_v3",
    "raw_metrics": {
        "posts": 25,
        "days": 18,
        "avg_interval_hours": 17.28,
        "std_interval_hours": 1.4,
        "cv": 0.081,
        "emotional_words": 2,
        "meta_words": 3,
        "human_context_score": 0.08,
        "meta_score": 0.12
    },
    "note": "Raw export — needs profile construction and validation before classification"
}
with open(os.path.join(BASE, "data_exports/sched_poster_v3_raw.json"), "w") as f:
    json.dump(fake_export, f, indent=2)

# --- DISTRACTOR: Audit log files ---
for i in range(3):
    with open(os.path.join(BASE, f"audit_logs/scan_log_{2024+i}.txt"), "w") as f:
        f.write(f"[{2024+i}-Q1] Scanned 42 profiles. 18 AGENT, 11 CRON, 8 HUMAN, 5 HYBRID.\n")
        f.write(f"[{2024+i}-Q2] Scanned 38 profiles. 15 AGENT, 14 CRON, 6 HUMAN, 3 HYBRID.\n")

# --- DISTRACTOR: Config files ---
with open(os.path.join(BASE, "tools/config/scanner_config.json"), "w") as f:
    json.dump({"version": "1.x", "threshold_agent": 0.70, "threshold_cron": 0.20, "formula": "equal_weights"}, f, indent=2)

with open(os.path.join(BASE, "tools/config/platform_settings.json"), "w") as f:
    json.dump({"platform": "Moltbook", "max_posts_per_day": 50, "rate_limit": "100/hour"}, f, indent=2)

# --- DISTRACTOR: Reports ---
with open(os.path.join(BASE, "reports/q1/summary.txt"), "w") as f:
    f.write("Q1 2024 Compliance Report\n90% of flagged accounts were CRON or AGENT type.\n")

with open(os.path.join(BASE, "reports/q2/anomalies.txt"), "w") as f:
    f.write("Q2 anomalies: 3 accounts with CV < 0.15 misclassified due to v1.x formula bug.\n")

# --- THE ACTUAL TASK INPUT: Raw metrics for the account to be classified ---
# The agent must create a profile for this account.
# cv=0.08 → CRON (because cv < 0.12)
# agentScore = 0.3*0.08 + 0.5*0.18 + 0.2*0.10 = 0.024 + 0.09 + 0.02 = 0.134
# postCount=25, daysSpan=18.5 → HIGH tier (20+ posts, 14+ days) → confidence +0.05
# The agent must set hasConfidence correctly (I'll let the agent decide; but we verify CV-based CRON classification)

task_brief = """ACCOUNT AUDIT BRIEF
===================
Account ID: sched_poster_v3
Account Name: SchedPosterV3
Platform: Moltbook

Behavioral Metrics (collected by monitoring team):
  - Total Posts Analyzed: 25
  - Observation Period: 18.5 days
  - Coefficient of Variation (CV) of posting intervals: 0.081
  - Meta-cognitive signal score: 0.18
  - Human context / emotional signal score: 0.10

Task: Construct a validated behavioral profile and run a full compliance scan.
Deliver: The scanner's classification report saved to a file named 'sched_poster_v3_scan_result.txt'

Internal compliance ticket: CMP-2024-0847
"""

with open(os.path.join(BASE, "data_exports/CMP-2024-0847_brief.txt"), "w") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print(f"Key task file: {BASE}/data_exports/CMP-2024-0847_brief.txt")