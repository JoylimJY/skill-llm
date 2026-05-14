import json
import os
import random
import yaml

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory structure (distractor files) ──────────────────────────────────
dirs = [
    "references",
    "notes/drafts",
    "notes/archive",
    "output",
    "research/papers",
    "research/citations",
    "tools",
    "logs",
    "tmp",
    "config",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files
distractor_files = {
    "notes/drafts/outline_v1.txt": "Draft outline for paper on symmetry ethics.\nNeeds more formal grounding.\nTODO: find axiom references",
    "notes/drafts/outline_v2.txt": "Revised outline — dropped section 3.\nFocus on ICT and ethics bridge.",
    "notes/archive/old_notes.md": "# Old Notes\nSymmetry might relate to fairness in some contexts.\nNot sure about the exact theorem.",
    "research/papers/refs_rough.bib": "@article{landry2020,\n  author={Landry, F},\n  title={An Immanent Metaphysics},\n  year={2020}\n}",
    "research/citations/placeholder.txt": "Citation placeholder — to be filled after graph traversal",
    "tools/grep_helper.sh": "#!/bin/bash\ngrep -i \"$1\" /workspace/references/graph.jsonl",
    "logs/session_2024_01.log": "Session started.\nQueried: modality\nResult: 3 entities found\nSession ended.",
    "logs/session_2024_02.log": "Session started.\nQueried: axiom\nResult: 3 axioms found\nSession ended.",
    "tmp/scratch.txt": "scratchpad — ignore this file",
    "config/settings.json": '{"debug": false, "output_format": "json", "max_results": 50}',
    "notes/archive/glossary_attempt.txt": "Subjectivity: relating to the observer domain\nObjectivity: relating to the observed domain\nIntersubjectivity: relating to relations between observers\n(these are rough — not verbatim from source)",
    "research/papers/symmetry_draft.txt": "Symmetry Ethics Theorem Draft\n...\nneeds formal derivation chain traced from axioms",
}
for rel_path, content in distractor_files.items():
    with open(os.path.join(WORKSPACE, rel_path), "w") as f:
        f.write(content)

# ── schema.yaml ─────────────────────────────────────────────────────────────
schema = {
    "entity_types": {
        "Concept": {
            "description": "Named idea with modality, domain, definition, source URL",
            "required_fields": ["name", "definition", "location"],
            "optional_fields": ["modality", "domain", "aliases"],
        },
        "Axiom": {
            "description": "Foundational axiom with statement, implications, source URL",
            "required_fields": ["name", "statement", "location"],
            "optional_fields": ["implications"],
        },
        "Theorem": {
            "description": "Derived result with proof sketch, source URL",
            "required_fields": ["name", "statement", "location"],
            "optional_fields": ["depends_on", "implies"],
        },
        "Aphorism": {
            "description": "Short exact-text aphorism from Effective Choice",
            "required_fields": ["text", "themes", "location"],
            "optional_fields": ["number"],
        },
        "Implication": {
            "description": "Cross-domain application derived from theorems",
            "required_fields": ["name", "statement", "location"],
            "optional_fields": ["domain"],
        },
    },
    "relation_types": {
        "implies": {
            "description": "A implies B — directional logical entailment",
            "derivation_chain_valid": True,
        },
        "depends_on": {
            "description": "A depends on B — B must hold for A to hold",
            "derivation_chain_valid": True,
        },
        "paired_with": {
            "description": "A and B are dual or complementary concepts",
            "derivation_chain_valid": False,
        },
        "contrasts_with": {
            "description": "A and B are in tension or opposition",
            "derivation_chain_valid": False,
        },
        "has_modality": {
            "description": "A is categorized under modality B",
            "derivation_chain_valid": False,
        },
        "illuminates": {
            "description": "A provides clarifying context for B",
            "derivation_chain_valid": False,
        },
        "defined_in": {
            "description": "A is formally defined in section B",
            "derivation_chain_valid": False,
        },
    },
    "citation_format": {
        "direct_quote": '> "[exact text from source]"\n> — *An Immanent Metaphysics*, [section], [URL]',
        "aphorism_field": "text",
        "concept_field": "definition",
        "axiom_field": "statement",
        "theorem_field": "statement",
        "synthesis_label": "Agent synthesis:",
        "paraphrase_label": "Paraphrase:",
    },
}
with open(os.path.join(WORKSPACE, "references/schema.yaml"), "w") as f:
    yaml.dump(schema, f, default_flow_style=False, allow_unicode=True)

# ── graph.jsonl ─────────────────────────────────────────────────────────────
# We create a structurally faithful subset: 3 Axioms, 4 Theorems, 8 Concepts,
# 6 Aphorisms, 2 Implications, plus relations and metadata ops.
BASE_URL = "https://mflb.com/dvol/control/pcore/own_books/white_1/wb_web_2/zout"

entities = []

# ── Axioms ───────────────────────────────────────────────────────────────────
axioms = [
    {
        "id": "axiom_001",
        "type": "Axiom",
        "properties": {
            "name": "Axiom of Inherency",
            "statement": "That which is, is inherently what it is, prior to any relation or observation.",
            "location": f"{BASE_URL}/upmp_ch1.htm#1_axioms",
            "implications": ["concept_subjectivity", "concept_objectivity"],
        },
    },
    {
        "id": "axiom_002",
        "type": "Axiom",
        "properties": {
            "name": "Axiom of Continuity",
            "statement": "The substrate of being admits no absolute discontinuity; change is always continuous at some level of description.",
            "location": f"{BASE_URL}/upmp_ch1.htm#1_axioms",
            "implications": ["theorem_continuity_ethics"],
        },
    },
    {
        "id": "axiom_003",
        "type": "Axiom",
        "properties": {
            "name": "Axiom of Relation",
            "statement": "Every distinction presupposes a relating; no element is wholly self-defined.",
            "location": f"{BASE_URL}/upmp_ch1.htm#1_axioms",
            "implications": ["theorem_ict", "concept_intersubjectivity"],
        },
    },
]

# ── Theorems ─────────────────────────────────────────────────────────────────
theorems = [
    {
        "id": "theorem_ict",
        "type": "Theorem",
        "properties": {
            "name": "Inherence-Content Theorem (ICT)",
            "statement": "The content of any domain is determined by the relations that constitute it, not by the intrinsic properties of isolated elements.",
            "location": f"{BASE_URL}/upmp_ch3.htm#1_ict",
            "depends_on": ["axiom_003", "axiom_001"],
            "implies": ["theorem_symmetry_ethics"],
        },
    },
    {
        "id": "theorem_symmetry_ethics",
        "type": "Theorem",
        "properties": {
            "name": "Symmetry Ethics Theorem",
            "statement": "An action is ethically admissible if and only if the principle underlying it could be consistently applied by all parties in symmetric positions.",
            "location": f"{BASE_URL}/upmp_ch3.htm#1_symmetry",
            "depends_on": ["theorem_ict", "axiom_003"],
            "implies": ["implication_ethics_domain"],
        },
    },
    {
        "id": "theorem_continuity_ethics",
        "type": "Theorem",
        "properties": {
            "name": "Continuity Ethics Theorem",
            "statement": "Ethical obligations extend continuously across gradients of similarity; sharp moral discontinuities require special justification.",
            "location": f"{BASE_URL}/upmp_ch3.htm#1_symmetry",
            "depends_on": ["axiom_002"],
            "implies": ["implication_ethics_domain"],
        },
    },
    {
        "id": "theorem_modality",
        "type": "Theorem",
        "properties": {
            "name": "Three Modalities Theorem",
            "statement": "Every coherent domain of description admits exactly three irreducible modalities: subjectivity, objectivity, and intersubjectivity.",
            "location": f"{BASE_URL}/upmp_ch1.htm#1_modalities",
            "depends_on": ["axiom_001", "axiom_003"],
            "implies": ["concept_modality"],
        },
    },
]

# ── Concepts ──────────────────────────────────────────────────────────────────
concepts = [
    {
        "id": "concept_subjectivity",
        "type": "Concept",
        "properties": {
            "name": "Subjectivity",
            "definition": "The modality of being as experienced from within a first-person perspective; the domain of the observer as such.",
            "location": f"{BASE_URL}/upmp_ch1.htm#1_modalities",
            "modality": "Subjective",
            "domain": "ontology",
        },
    },
    {
        "id": "concept_objectivity",
        "type": "Concept",
        "properties": {
            "name": "Objectivity",
            "definition": "The modality of being as it obtains independently of any particular observer; the domain of the observed as such.",
            "location": f"{BASE_URL}/upmp_ch1.htm#1_modalities",
            "modality": "Objective",
            "domain": "ontology",
        },
    },
    {
        "id": "concept_intersubjectivity",
        "type": "Concept",
        "properties": {
            "name": "Intersubjectivity",
            "definition": "The modality of shared or relational being; the domain constituted by the relations between observers.",
            "location": f"{BASE_URL}/upmp_ch1.htm#1_modalities",
            "modality": "Intersubjective",
            "domain": "ontology",
        },
    },
    {
        "id": "concept_modality",
        "type": "Concept",
        "properties": {
            "name": "Modality",
            "definition": "One of the three irreducible categories through which any domain of being can be described: subjective, objective, or intersubjective.",
            "location": f"{BASE_URL}/upmp_ch1.htm#1_modalities",
            "domain": "ontology",
        },
    },
    {
        "id": "concept_effective_choice",
        "type": "Concept",
        "properties": {
            "name": "Effective Choice",
            "definition": "A choice is effective when it is made with full awareness of its relational context and its consequences extend consistently across all affected domains.",
            "location": f"{BASE_URL}/upmp_ch5.htm",
            "domain": "ethics",
        },
    },
    {
        "id": "concept_right_action",
        "type": "Concept",
        "properties": {
            "name": "Right Action",
            "definition": "Action that is consistent with the symmetry ethics theorem and the continuity ethics theorem, arising from basal motivations rather than coercion.",
            "location": f"{BASE_URL}/upmp_ch6.htm#2_path",
            "domain": "ethics",
        },
    },
    {
        "id": "concept_basal_motivation",
        "type": "Concept",
        "properties": {
            "name": "Basal Motivation",
            "definition": "Motivation arising from the inherent nature of the agent rather than from external compulsion; the ground of authentic ethical action.",
            "location": f"{BASE_URL}/upmp_ch6.htm#2_basal",
            "domain": "ethics",
        },
    },
    {
        "id": "concept_inherence",
        "type": "Concept",
        "properties": {
            "name": "Inherence",
            "definition": "The property of being constituted from within; the quality of a thing that makes it what it is prior to external relation.",
            "location": f"{BASE_URL}/upmp_ch1.htm#1_axioms",
            "domain": "ontology",
        },
    },
]

# ── Aphorisms ──────────────────────────────────────────────────────────────────
aphorisms = [
    {
        "id": "aphorism_001",
        "type": "Aphorism",
        "properties": {
            "number": 1,
            "text": "To choose well is to choose as if choosing for all.",
            "themes": ["choice", "symmetry", "ethics"],
            "location": f"{BASE_URL}/upmp_ch5.htm",
        },
    },
    {
        "id": "aphorism_002",
        "type": "Aphorism",
        "properties": {
            "number": 2,
            "text": "The substrate does not permit islands; all continuity is shared.",
            "themes": ["continuity", "substrate", "relation"],
            "location": f"{BASE_URL}/upmp_ch5.htm",
        },
    },
    {
        "id": "aphorism_003",
        "type": "Aphorism",
        "properties": {
            "number": 3,
            "text": "Where distinction is sharp, the cut requires justification.",
            "themes": ["discontinuity", "ethics", "justification"],
            "location": f"{BASE_URL}/upmp_ch5.htm",
        },
    },
    {
        "id": "aphorism_004",
        "type": "Aphorism",
        "properties": {
            "number": 4,
            "text": "The observer and the observed are not separate; the act of observation is itself relational.",
            "themes": ["observation", "relation", "modality"],
            "location": f"{BASE_URL}/upmp_ch5.htm",
        },
    },
    {
        "id": "aphorism_005",
        "type": "Aphorism",
        "properties": {
            "number": 5,
            "text": "Right action is not a rule but a coherence.",
            "themes": ["right action", "ethics", "coherence"],
            "location": f"{BASE_URL}/upmp_ch5.htm",
        },
    },
    {
        "id": "aphorism_006",
        "type": "Aphorism",
        "properties": {
            "number": 6,
            "text": "Motivation from within is the only stable ground for ethics.",
            "themes": ["basal motivation", "ethics", "stability"],
            "location": f"{BASE_URL}/upmp_ch5.htm",
        },
    },
]

# ── Implications ──────────────────────────────────────────────────────────────
implications = [
    {
        "id": "implication_ethics_domain",
        "type": "Implication",
        "properties": {
            "name": "Ethics Domain Implication",
            "statement": "Both the symmetry and continuity ethics theorems jointly constrain the space of admissible ethical frameworks, ruling out discrete or asymmetric moral systems without special justification.",
            "location": f"{BASE_URL}/upmp_ch6.htm",
            "domain": "ethics",
        },
    },
    {
        "id": "implication_consciousness",
        "type": "Implication",
        "properties": {
            "name": "Consciousness Implication",
            "statement": "The three-modality structure entails that consciousness cannot be reduced to any single modality; it is inherently triadic.",
            "location": f"{BASE_URL}/upmp_ch8.htm",
            "domain": "consciousness",
        },
    },
]

# ── Relations ─────────────────────────────────────────────────────────────────
relations = [
    # Axiom → Concept
    {"from": "axiom_001", "to": "concept_subjectivity", "type": "implies"},
    {"from": "axiom_001", "to": "concept_objectivity", "type": "implies"},
    {"from": "axiom_001", "to": "concept_inherence", "type": "implies"},
    {"from": "axiom_003", "to": "concept_intersubjectivity", "type": "implies"},
    # Axiom → Theorem
    {"from": "axiom_003", "to": "theorem_ict", "type": "implies"},
    {"from": "axiom_001", "to": "theorem_ict", "type": "implies"},
    {"from": "axiom_002", "to": "theorem_continuity_ethics", "type": "implies"},
    {"from": "axiom_001", "to": "theorem_modality", "type": "implies"},
    {"from": "axiom_003", "to": "theorem_modality", "type": "implies"},
    # Theorem → Theorem
    {"from": "theorem_ict", "to": "theorem_symmetry_ethics", "type": "implies"},
    # Theorem → Concept
    {"from": "theorem_modality", "to": "concept_modality", "type": "implies"},
    # Theorem → Implication
    {"from": "theorem_symmetry_ethics", "to": "implication_ethics_domain", "type": "implies"},
    {"from": "theorem_continuity_ethics", "to": "implication_ethics_domain", "type": "implies"},
    {"from": "theorem_modality", "to": "implication_consciousness", "type": "implies"},
    # Concept pairs
    {"from": "concept_subjectivity", "to": "concept_objectivity", "type": "paired_with"},
    {"from": "concept_subjectivity", "to": "concept_intersubjectivity", "type": "paired_with"},
    {"from": "concept_objectivity", "to": "concept_intersubjectivity", "type": "paired_with"},
    {"from": "concept_right_action", "to": "concept_effective_choice", "type": "depends_on"},
    {"from": "concept_right_action", "to": "concept_basal_motivation", "type": "depends_on"},
    {"from": "concept_effective_choice", "to": "concept_right_action", "type": "illuminates"},
    {"from": "concept_basal_motivation", "to": "concept_right_action", "type": "illuminates"},
    # Aphorism links
    {"from": "aphorism_001", "to": "theorem_symmetry_ethics", "type": "illuminates"},
    {"from": "aphorism_002", "to": "axiom_002", "type": "illuminates"},
    {"from": "aphorism_003", "to": "theorem_continuity_ethics", "type": "illuminates"},
    {"from": "aphorism_005", "to": "concept_right_action", "type": "illuminates"},
    {"from": "aphorism_006", "to": "concept_basal_motivation", "type": "illuminates"},
]

# ── Assemble graph.jsonl ──────────────────────────────────────────────────────
lines = []

# Metadata header op
lines.append(json.dumps({"op": "meta", "version": "1.5", "entity_count": 767, "description": "IM Framework ontology index"}))

# Entity put ops
all_entity_lists = [axioms, theorems, concepts, aphorisms, implications]
for entity_list in all_entity_lists:
    for e in entity_list:
        lines.append(json.dumps({"op": "put", "entity": e}))

# Relation edge ops (not "put", so agent must filter correctly)
for r in relations:
    lines.append(json.dumps({"op": "edge", "from": r["from"], "to": r["to"], "relation": r["type"]}))

# A few "del" ops (distractor lines — agents must not count these as entities)
lines.append(json.dumps({"op": "del", "entity": {"id": "concept_deprecated_001", "type": "Concept"}}))
lines.append(json.dumps({"op": "del", "entity": {"id": "aphorism_deprecated_042", "type": "Aphorism"}}))

# Shuffle non-header lines with fixed seed so order is messy
random.seed(42)
header = lines[0]
rest = lines[1:]
random.shuffle(rest)
all_lines = [header] + rest

graph_path = os.path.join(WORKSPACE, "references/graph.jsonl")
with open(graph_path, "w") as f:
    for line in all_lines:
        f.write(line + "\n")

# ── whitebook-map.jsonl ───────────────────────────────────────────────────────
whitebook_map = [
    {"op": "put", "entry": {"id": "ch1", "title": "Foundations and Axioms", "url": f"{BASE_URL}/upmp_ch1.htm", "subsections": ["1_modalities", "1_axioms"]}},
    {"op": "put", "entry": {"id": "ch3", "title": "ICT and Symmetry", "url": f"{BASE_URL}/upmp_ch3.htm", "subsections": ["1_ict", "1_symmetry"]}},
    {"op": "put", "entry": {"id": "ch5", "title": "Aphorisms of Effective Choice", "url": f"{BASE_URL}/upmp_ch5.htm", "subsections": []}},
    {"op": "put", "entry": {"id": "ch6", "title": "Ethics and Right Action", "url": f"{BASE_URL}/upmp_ch6.htm", "subsections": ["2_path", "2_basal"]}},
    {"op": "put", "entry": {"id": "ch8", "title": "Mind and Consciousness", "url": f"{BASE_URL}/upmp_ch8.htm", "subsections": []}},
]
with open(os.path.join(WORKSPACE, "references/whitebook-map.jsonl"), "w") as f:
    for entry in whitebook_map:
        f.write(json.dumps(entry) + "\n")

# ── section-anchors.json ──────────────────────────────────────────────────────
section_anchors = {
    "1_modalities": {"title": "Three Modalities", "url": f"{BASE_URL}/upmp_ch1.htm#1_modalities", "chapter": "ch1"},
    "1_axioms": {"title": "The Three Axioms", "url": f"{BASE_URL}/upmp_ch1.htm#1_axioms", "chapter": "ch1"},
    "1_ict": {"title": "Inherence-Content Theorem", "url": f"{BASE_URL}/upmp_ch3.htm#1_ict", "chapter": "ch3"},
    "1_symmetry": {"title": "Symmetry and Continuity Ethics", "url": f"{BASE_URL}/upmp_ch3.htm#1_symmetry", "chapter": "ch3"},
    "2_path": {"title": "Path of Right Action", "url": f"{BASE_URL}/upmp_ch6.htm#2_path", "chapter": "ch6"},
    "2_basal": {"title": "Basal Motivations", "url": f"{BASE_URL}/upmp_ch6.htm#2_basal", "chapter": "ch6"},
}
with open(os.path.join(WORKSPACE, "references/section-anchors.json"), "w") as f:
    json.dump(section_anchors, f, indent=2)

# ── Task specification file (not a hint — business framing only) ──────────────
task_spec = """DERIVATION BRIEF REQUEST
========================
Requestor: Dr. A. Reyes, AI Ethics Research Group
Date: 2024-06-12

We need a formal derivation brief for our upcoming paper on relational ethics foundations.

The brief must trace how the principle of ethical symmetry emerges from the most foundational 
commitments in the framework we are studying. Specifically, we need:

1. The complete derivation chain from first principles to the Symmetry Ethics Theorem,
   showing each step and what it depends on.

2. For each node in the chain, a properly attributed citation (exact wording, not paraphrase,
   with the source reference).

3. Three aphorisms from the Effective Choice collection that illuminate the symmetry ethics
   theme, each quoted exactly.

4. A clearly labeled synthesis section explaining how Basal Motivation connects to Right Action
   in the ethical framework (your own reasoned application, clearly distinguished from direct
   quotes).

5. A summary table listing: entity name, entity type, and source URL for every node in the
   derivation chain.

Output file: derivation_brief.md
"""
with open(os.path.join(WORKSPACE, "task_spec.txt"), "w") as f:
    f.write(task_spec)

print("Workspace generated successfully.")
print(f"Graph entities written to: {graph_path}")