import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Directory structure ---
dirs = [
    "workspace/team_docs/strategy",
    "workspace/team_docs/retros",
    "workspace/team_docs/hiring",
    "workspace/references",
    "workspace/research/classical_sources",
    "workspace/research/modern_commentary",
    "workspace/research/folklore_dump",
    "workspace/systems/infra_notes",
    "workspace/systems/architecture",
    "workspace/drafts/unprocessed",
    "workspace/drafts/processed",
    "workspace/archive",
]

for d in dirs:
    os.makedirs(os.path.join("/", d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "workspace/team_docs/strategy/q3_goals.txt": "Q3 goals:\n- Reduce p99 latency to under 50ms\n- Ship new auth service\n- Hire 2 backend engineers",
    "workspace/team_docs/retros/sprint_22_retro.md": "# Sprint 22 Retro\n\n## What went well\n- Deploy pipeline improved\n\n## What didn't\n- Too many context switches",
    "workspace/team_docs/hiring/jd_backend.txt": "Backend Engineer JD\nRequirements: 5+ years Python, distributed systems experience preferred.",
    "workspace/references/old_philosophy_notes.txt": "Various notes on stoicism and its application to engineering teams. Mostly Marcus Aurelius quotes.",
    "workspace/research/classical_sources/arthashastra_toc.txt": "Table of Contents - Arthashastra\nBook 1: The Subject of Training\nBook 2: The Duties of Government Superintendents\nBook 3: Concerning Law\nBook 4: The Removal of Thorns\n...",
    "workspace/research/modern_commentary/leadership_blog_notes.txt": "Notes from various leadership blogs. Not peer reviewed. Includes some Chanakya references but sources unclear.",
    "workspace/research/folklore_dump/internet_quotes.txt": "Collection of quotes found on motivational websites. Attribution uncertain.\n'Before you start a war, dig two graves.' - possibly Chanakya?\n'The biggest guru-mantra is: never share your secrets with anybody.' - widely cited online.",
    "workspace/systems/infra_notes/queue_design_notes.txt": "Queue design considerations:\n- Use dead-letter queues for failed messages\n- Monitor backpressure signals\n- Circuit breakers on downstream calls",
    "workspace/systems/architecture/service_mesh_notes.txt": "Service mesh evaluation:\n- Istio vs Linkerd\n- mTLS overhead acceptable\n- Sidecars add 10-15ms",
    "workspace/archive/old_principles_draft.txt": "OLD DRAFT - DO NOT USE\nSome rough notes on principles we wanted to adopt. Incomplete.",
    "workspace/drafts/processed/example_record_bad.json": json.dumps({
        "title": "Be Secretive",
        "quote": "Never tell anyone your plans",
        "note": "good advice",
        "confidence": "very high"
    }, indent=2),
}

for path, content in distractors.items():
    with open(os.path.join("/", path), "w") as f:
        f.write(content)

# --- THE CORE PROBLEM: raw unstructured input dump ---
# This is the messy raw input the agent must process
raw_input = """
=== RAW PRINCIPLES DUMP FOR LIBRARY PROCESSING ===
=== Source: Mixed — needs classification and structuring ===

--- ENTRY 1 ---
SOURCE HINT: Arthashastra, Book 1, Chapter 15 (scholarly paraphrase available)
RAW QUOTE: "The king shall employ as high officials only those persons who have been tested in loyalty through secret agents"
DOMAIN NOTE: This appears in multiple scholarly translations of the Arthashastra. Refers to using internal intelligence to verify loyalty before granting authority.
MODERN RELEVANCE NOTE: Submitted by infra team lead — wants application to how we grant elevated access permissions in production systems.

--- ENTRY 2 ---
SOURCE HINT: Chanakya Niti, Chapter 1 (widely referenced, multiple translations exist)
RAW QUOTE: "A person should not be too honest. Straight trees are cut first and honest people are screwed first."
DOMAIN NOTE: Found in multiple translations of Chanakya Niti. Historical meaning relates to strategic restraint in displaying capability to adversaries. Often misread as advocating dishonesty.
MODERN RELEVANCE NOTE: Product team wants this applied to competitive product positioning and when to reveal roadmap features publicly.

--- ENTRY 3 ---
SOURCE HINT: Internet motivational content, no verified classical source found
RAW QUOTE: "The biggest guru-mantra is: never share your secrets with anybody. It will destroy you."
DOMAIN NOTE: Widely circulated online as Chanakya. Not found in verified Arthashastra or Chanakya Niti translations. Possibly a modern paraphrase or invention.
MODERN RELEVANCE NOTE: Engineering manager wants to use this for a talk on information security culture.

--- ENTRY 4 ---
SOURCE HINT: Arthashastra, Book 2 (on governance and organizational structure, well-documented)
RAW QUOTE: "Each official shall confine himself to his own department and shall not meddle in the affairs of another."
DOMAIN NOTE: Strong scholarly backing. Classical meaning relates to preventing overlap of state administrative functions to avoid confusion of accountability.
MODERN RELEVANCE NOTE: Architecture team wants this applied to service boundary design and microservices ownership.

--- ENTRY 5 ---
SOURCE HINT: General Chanakya commentary, secondary sources only, no primary reference
RAW QUOTE: "A man is great by deeds, not by birth."
DOMAIN NOTE: Appears in various Chanakya Niti commentary but primary source citation is weak. May be an editorial summary of broader themes rather than a direct verse.
MODERN RELEVANCE NOTE: HR team wants this for performance review philosophy — merit over tenure.

"""

with open("/workspace/drafts/unprocessed/raw_principles_dump.txt", "w") as f:
    f.write(raw_input)

# Write a brief request context file (not a README or hint — just stakeholder context)
context = """
STAKEHOLDER REQUEST
===================
Team: Platform Engineering + Strategy
Requestor: VP of Engineering

We have collected a dump of classical strategy material from various sources.
Quality varies widely. Some entries are from proper academic references.
Others are from the internet with no real provenance.

We need a structured reference library file called: principles_library.json

Each entry in the library must be a proper structured record.
The library will be used by engineering leads to ground their team decisions
in classical strategic thinking — only when it genuinely applies.

The file must be placed somewhere findable in the workspace.
Reliability of each principle must be clearly indicated in each record.
"""

with open("/workspace/drafts/unprocessed/stakeholder_context.txt", "w") as f:
    f.write(context)

print("Workspace generated successfully.")
print("Key input file: /workspace/drafts/unprocessed/raw_principles_dump.txt")