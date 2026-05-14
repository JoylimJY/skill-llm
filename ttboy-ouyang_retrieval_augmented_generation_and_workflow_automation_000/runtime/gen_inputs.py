#!/usr/bin/env python3
"""
Generate the sandbox workspace with realistic legal research memory files
placed in the correct jasper-recall directory structure, plus distractors.
"""
import os
import random
import hashlib
from pathlib import Path

random.seed(42)

HOME = Path.home()
WORKSPACE = Path("/workspace")

# ── 1. Create the jasper-recall memory directory structure ─────────────────
MEMORY_ROOT = WORKSPACE / "legal-memory"
MEMORY_ROOT.mkdir(parents=True, exist_ok=True)
(MEMORY_ROOT / "session-digests").mkdir(exist_ok=True)
(MEMORY_ROOT / "repos").mkdir(exist_ok=True)
(MEMORY_ROOT / "founder-logs").mkdir(exist_ok=True)

# ── 2. Write realistic legal research memory markdown files ────────────────

# Top-level memory files
(MEMORY_ROOT / "MEMORY.md").write_text("""# Legal Research Memory

## Overview
This memory file tracks key decisions, precedents, and research threads
for our AI-assisted legal research platform.

## Active Research Threads
- Fourth Amendment digital privacy cases (2018-2024)
- Intellectual property in AI-generated content
- Antitrust enforcement in platform markets

## Key Contacts
- Lead Counsel: Morgan Ashford
- Research Director: Priya Nair
- Tech Compliance: Devlin Chase
""")

(MEMORY_ROOT / "daily-notes-2024-01-15.md").write_text("""# Daily Notes — January 15, 2024

## Research Session
Spent the morning reviewing Carpenter v. United States (2018).
The Supreme Court held that accessing historical cell-site location information
constitutes a Fourth Amendment search. Key takeaway: third-party doctrine
has limits when it comes to comprehensive digital surveillance data.

## Action Items
- Cross-reference with United States v. Jones (2012) GPS tracking case
- Draft memo on reasonable expectation of privacy in digital era
- Review circuit splits on warrant requirements for cloud data
""")

(MEMORY_ROOT / "daily-notes-2024-02-03.md").write_text("""# Daily Notes — February 3, 2024

## AI Copyright Research
Long session on Thaler v. Vidal and AI-generated works copyright eligibility.
USPTO and Copyright Office both require human authorship.
The Naruto monkey selfie case (Naruto v. Slater) provides useful analogy —
non-human entities cannot hold copyright.

## Platform Antitrust Notes
Reviewed FTC v. Meta Platforms (2021). The court dismissed the original complaint
but allowed the amended complaint to proceed. Key issue: market definition
for personal social networking services.

## Tomorrow
- Look into EU Digital Markets Act implications
- Check status of DOJ v. Google antitrust case
""")

(MEMORY_ROOT / "case-tracker.md").write_text("""# Case Tracker

## Fourth Amendment — Digital Privacy
| Case | Year | Holding | Relevance |
|------|------|---------|-----------|
| Katz v. United States | 1967 | Reasonable expectation of privacy standard | Foundation |
| United States v. Jones | 2012 | GPS tracking is a search | Location data |
| Riley v. California | 2014 | Cell phone search requires warrant | Digital devices |
| Carpenter v. United States | 2018 | CSLI data requires warrant | Historical location |

## AI & Intellectual Property
| Case | Year | Holding | Relevance |
|------|------|---------|-----------|
| Thaler v. Vidal | 2022 | AI cannot be named inventor | Patent law |
| Thaler v. Perlmutter | 2023 | AI-generated art not copyrightable | Copyright |
| Andersen v. Stability AI | Pending | Training data copyright claims | Generative AI |

## Antitrust — Platform Markets
| Case | Year | Status | Issue |
|------|------|--------|-------|
| FTC v. Meta | 2021 | Ongoing | Social networking monopoly |
| DOJ v. Google | 2023 | Trial completed | Search advertising monopoly |
| Epic v. Apple | 2021 | Partial win for Apple | App store practices |
""")

# session-digests/
(MEMORY_ROOT / "session-digests" / "session-2024-01-10.md").write_text("""# Session Digest — January 10, 2024

## Topics Discussed
- Fourth Amendment reasonable expectation of privacy doctrine
- Digital warrant requirements post-Carpenter
- Cell site location information (CSLI) legal framework

## Tools Used
- WestLaw search for circuit court opinions
- Recall system to find prior research notes
- Citation cross-reference tool

## Key Decisions
Decided to focus the Q1 memo on the Carpenter framework and its implications
for law enforcement access to cloud-stored communications data.
The third-party doctrine erosion is the central thesis.

## Follow-up
Schedule review meeting with Morgan Ashford for February 1.
""")

(MEMORY_ROOT / "session-digests" / "session-2024-01-22.md").write_text("""# Session Digest — January 22, 2024

## Topics Discussed
- AI-generated content and intellectual property ownership
- Comparison of US vs EU approaches to AI copyright
- Implications for our clients in the creative technology sector

## Research Completed
Completed comparative analysis of US Copyright Office guidance (2023)
vs EU AI Act provisions on AI-generated works.
US approach: human authorship required, no protection for purely AI output.
EU approach: more nuanced, some protection possible with significant human input.

## Key Decisions
Recommend clients in generative AI space adopt human-in-the-loop workflows
to preserve copyright eligibility for their AI-assisted creative outputs.

## Action Items
- Draft client advisory on AI copyright best practices
- Review Andersen v. Stability AI complaint for training data exposure
""")

(MEMORY_ROOT / "session-digests" / "session-2024-02-07.md").write_text("""# Session Digest — February 7, 2024

## Topics Discussed
- Platform antitrust enforcement trends in US and EU
- Google Search antitrust trial outcomes
- Meta's ongoing FTC litigation

## Research Completed
Analyzed Judge Mehta's findings in DOJ v. Google — Google found to have
illegally maintained monopoly in general search and search text advertising.
This is a landmark ruling that will shape platform antitrust for years.

## Key Decisions
The DOJ v. Google ruling confirms that default agreements (e.g., with Apple Safari)
can constitute exclusionary conduct even without traditional predatory pricing.
This expands the antitrust toolkit significantly for platform cases.

## Follow-up
Monitor remedies phase of DOJ v. Google closely.
Apply framework to assess exposure for other platform clients.
""")

# repos/
(MEMORY_ROOT / "repos" / "research-platform-docs.md").write_text("""# Research Platform Documentation

## Architecture Overview
Our legal research platform integrates:
- AI-assisted case law retrieval (semantic search)
- Citation graph analysis
- Regulatory change tracking
- Client matter management

## Key Modules

### Semantic Search Engine
Uses sentence-transformer embeddings to match research queries to relevant
case law, statutes, and internal memos. Indexed nightly.

### Fourth Amendment Digital Privacy Module
Specialized retrieval for digital privacy cases. Contains curated index of
post-Carpenter cases with warrant requirement analysis.

### IP and AI Module
Tracks evolving landscape of AI intellectual property. Auto-updates when
Copyright Office or USPTO issues new guidance.

## Data Sources
- WestLaw API integration
- Federal court PACER records
- Internal research memos
- Client advisories (anonymized)
""")

(MEMORY_ROOT / "repos" / "compliance-notes.md").write_text("""# Compliance Notes

## Data Retention Policy
All research session logs retained for 7 years per firm policy.
Client-privileged materials stored with enhanced encryption.
AI-generated research summaries reviewed by licensed attorney before delivery.

## Model Usage Compliance
All AI models used in research assistance are:
- Locally hosted (no data sent to external APIs)
- Reviewed quarterly for bias and accuracy
- Documented per ABA Model Rules on technology competence

## Antitrust Compliance Notes
When advising platform clients, ensure all competitive analysis is
based on publicly available information and properly documented.
Avoid structuring advice that could facilitate anticompetitive coordination.
""")

# founder-logs/
(MEMORY_ROOT / "founder-logs" / "product-decisions-q1-2024.md").write_text("""# Product Decisions — Q1 2024

## Decision: Memory System Architecture
Date: January 5, 2024
Decision: Adopt local RAG system for research memory over cloud-based solution.
Rationale: Client confidentiality requires all data remain on-premises.
           Local embedding model sufficient for our semantic search needs.

## Decision: Focus Areas for 2024
Date: January 8, 2024
Decision: Prioritize three practice areas for AI assistance:
1. Digital privacy / Fourth Amendment litigation support
2. AI intellectual property advisory
3. Platform antitrust analysis
Rationale: Highest demand from current client base.

## Decision: Copyright Advisory Service Launch
Date: February 1, 2024
Decision: Launch AI copyright advisory service in Q2 2024.
Rationale: Rapid growth in generative AI client inquiries.
           Thaler decisions clarify the legal landscape enough to advise.
""")

# ── 3. Distractor files (not in memory structure, should not be indexed) ───
DISTRACTOR_ROOT = WORKSPACE / "distractors"
DISTRACTOR_ROOT.mkdir(exist_ok=True)

(DISTRACTOR_ROOT / "old-research.txt").write_text(
    "Old research notes in plain text format. Fourth Amendment cases from 2015.")
(DISTRACTOR_ROOT / "client-emails" ).mkdir(exist_ok=True)
(DISTRACTOR_ROOT / "client-emails" / "email-001.txt").write_text(
    "Re: Carpenter v. US — client inquiry about cell location data warrants.")
(DISTRACTOR_ROOT / "client-emails" / "email-002.txt").write_text(
    "Re: AI copyright — can we protect our generative art pipeline outputs?")
(DISTRACTOR_ROOT / "drafts").mkdir(exist_ok=True)
(DISTRACTOR_ROOT / "drafts" / "memo-draft-v1.md").write_text(
    "# Draft Memo\nThis is an unfinished draft about antitrust in tech platforms.")
(DISTRACTOR_ROOT / "drafts" / "memo-draft-v2.md").write_text(
    "# Draft Memo v2\nRevised section on DOJ v. Google remedies phase.")
(DISTRACTOR_ROOT / "archives" / "2023").mkdir(parents=True, exist_ok=True)
(DISTRACTOR_ROOT / "archives" / "2023" / "old-session-logs.json").write_text(
    '{"sessions": [{"id": 1, "topic": "patent law basics"}]}')
(DISTRACTOR_ROOT / "archives" / "2023" / "deprecated-index.db").write_bytes(b"\x00\x01\x02database")
(DISTRACTOR_ROOT / "config.yaml").write_text(
    "workspace: /workspace/legal-memory\ndebug: false\nmax_results: 10\n")
(DISTRACTOR_ROOT / "requirements-old.txt").write_text(
    "chromadb==0.3.0\nsentence-transformers==2.2.0\n")
(DISTRACTOR_ROOT / "README-old.txt").write_text(
    "Deprecated setup. Use new system.\n")

# ── 4. Write the task specification file the agent will see ───────────────
# This is the business request — placed at workspace root
(WORKSPACE / "audit-request.txt").write_text("""KNOWLEDGE AUDIT REQUEST
=======================
From: Priya Nair, Research Director
To: AI Systems Team
Date: February 10, 2024

We need to verify that our institutional memory system is working correctly
before our Q1 board presentation.

Please produce a file called memory_audit_report.json at the workspace root
(/workspace/memory_audit_report.json).

The report must contain the top 3 most relevant memory entries for each of
these three research topics we care most about:

  1. "Fourth Amendment digital privacy warrant requirements"
  2. "AI generated content copyright ownership"  
  3. "platform antitrust monopoly enforcement"

The memory files are stored in /workspace/legal-memory/

For each topic, we need to know: what documents came up, and how confident
the system is in each result.

The output file must be valid JSON. Our downstream compliance tool will
parse it, so please structure it as a JSON object where each topic is a key
mapping to a list of result objects. Each result object must have at minimum
a "document" field (the text content or excerpt) and a "score" field
(the similarity/confidence score as a number).

Thank you,
Priya
""")

print("Workspace generated successfully.")
print(f"Memory files: {list(MEMORY_ROOT.rglob('*.md'))}")
print(f"Distractor files: {list(DISTRACTOR_ROOT.rglob('*'))}")