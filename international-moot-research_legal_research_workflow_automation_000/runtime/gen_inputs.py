import os
import json
import random

random.seed(42)

BASE = "/workspace"

# Create directory structure
dirs = [
    "competition/jessup_2025",
    "competition/vis_moot_2025",
    "research_notes/general",
    "research_notes/drafts",
    "research_notes/ai_experiments",
    "databases/guides",
    "databases/access_logs",
    "citations/cases",
    "citations/articles",
    "team_docs/pleadings",
    "team_docs/memos",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---

# 1. General citation style guide (distractor)
with open(os.path.join(BASE, "citations/bluebook_guide.txt"), "w") as f:
    f.write("""BLUEBOOK CITATION GUIDE (21st Edition)
======================================
For law review articles: Author, Title, Volume Journal Page (Year).
For cases: Case Name, Volume Reporter Page (Court Year).
For international treaties: Treaty Name, opened for signature Date, parties.
Note: Always check the most recent edition for updates.
This guide does NOT cover OSCOLA or ILSA citation formats.
""")

# 2. Outdated database list (distractor with WRONG info)
with open(os.path.join(BASE, "databases/guides/old_database_list.txt"), "w") as f:
    f.write("""OUTDATED DATABASE REFERENCE (DO NOT USE - 2019)
================================================
- LexisNexis International: Primary source for all international law
- Westlaw Campus: Student access portal
- JSTOR: Academic journals archive
- Google Scholar: Free alternative to paid databases
- HeinOnline: US-centric law journals

Note: Oxford OPIL access expired. Contact library for renewal.
Recommendation: Use JSTOR and Google Scholar as primary resources.
""")

# 3. Partial, messy research notes with wrong database assignments (the main problem file)
with open(os.path.join(BASE, "research_notes/drafts/cyber_ops_notes_INCOMPLETE.txt"), "w") as f:
    f.write("""RESEARCH NOTES - CYBER OPERATIONS & STATE RESPONSIBILITY
=========================================================
Topic: State responsibility for cyber operations by non-state actors
Competition: Vis Moot 2025 (International Commercial Arbitration track)

ATTEMPTS SO FAR (not working well):
------------------------------------
Search 1: "cyber operations" AND "state responsibility" → 2.6M results, too broad
Search 2: "cyber" AND "non-state actors" AND "international law" → still messy
Search 3: tried on Google Scholar, got some results but not sure if authoritative

DATABASES TRIED:
- Wikipedia (obviously not ideal)
- Google Scholar (free but incomplete)
- ResearchGate (some papers but can't verify quality)

ISSUES:
- Can't find the right databases for this
- Not sure how to narrow down the search
- AI (ChatGPT) gave me a list of articles but some don't seem to exist
- Don't know which database is best for commercial arbitration vs public intl law

TODO:
- Find proper academic databases
- Learn boolean search operators  
- Figure out the right keyword combinations
- Understand what AI can/cannot do in research

KEYWORD IDEAS (raw brainstorm):
cyber attack, hacking, state sponsored, terrorism, non-state actors, IHL,
attribution, due diligence, countermeasures, UN charter article 2(4),
self-defense, Tallinn Manual (is this citable?), armed attack threshold
""")

# 4. Competition compromis (problem statement)
with open(os.path.join(BASE, "competition/vis_moot_2025/compromis_summary.txt"), "w") as f:
    f.write("""VIS MOOT 2025 - COMPETITION PROBLEM SUMMARY
============================================
CASE: Solaris Tech Corp (Claimant) v. Republic of Nordavia (Respondent)

LEGAL ISSUES RAISED:
1. International Commercial Arbitration: Jurisdiction and applicable law
2. State Responsibility: Whether Nordavia bears responsibility for cyber
   operations conducted by the "Nordavian Digital Collective" (NDC),
   a non-state hacker group allegedly acting under state direction
3. Attribution: Standard of control required to attribute non-state 
   cyber operations to a state under international law
4. Due Diligence: Whether Nordavia failed its due diligence obligations
   by knowingly allowing NDC to operate from its territory
5. Remedies: Damages and cessation obligations under international law

RELEVANT LEGAL FRAMEWORKS:
- ILC Articles on State Responsibility (ARSIWA)
- UN Charter Article 2(4) and Article 51
- Customary International Law on Attribution
- Tallinn Manual 2.0 on Cyber Operations
- Commercial arbitration rules (VIAC / ICC)

NOTE: Teams must address BOTH the public international law dimension
(state responsibility) AND the commercial arbitration procedural issues.
""")

# 5. Incomplete AI experiment log (distractor showing failed AI usage)
with open(os.path.join(BASE, "research_notes/ai_experiments/chatgpt_log.txt"), "w") as f:
    f.write("""AI EXPERIMENT LOG
=================
Date: 2025-01-15
Tool: ChatGPT-4

Q: "List 10 key articles on state responsibility for cyber attacks"
A: [AI provided list including:]
   - Schmitt, M. (2017) "Cyber Operations and the Jus in Bello" AJIL 45(2):112-134
   - Henderson, R. (2019) "Attribution in Cyberspace" EJIL 30(1):55-89
   
VERIFICATION ATTEMPT: Could not find "AJIL 45(2):112-134" - article does not exist
VERIFICATION ATTEMPT: Henderson article citation format seems wrong

Q: "Write footnotes for my brief on cyber attribution"
A: [AI generated detailed footnotes]
VERIFICATION: Multiple citation errors found - wrong volume numbers, non-existent pages

CONCLUSION: AI is unreliable for direct citation generation.
TODO: Need better strategy for using AI in research.
""")

# 6. General research methodology guide (distractor)
with open(os.path.join(BASE, "research_notes/general/basic_research_tips.txt"), "w") as f:
    f.write("""BASIC LEGAL RESEARCH TIPS
==========================
1. Start with secondary sources (textbooks, encyclopedias)
2. Move to primary sources (cases, treaties, statutes)
3. Use boolean operators: AND, OR, NOT
4. Check citation frequency (more cited = more authoritative)
5. Verify all sources independently

Common databases (general law):
- Westlaw
- LexisNexis
- HeinOnline
- JSTOR

These tips apply to domestic law research. International law may differ.
""")

# 7. Jessup team notes (distractor - different competition, different databases)
with open(os.path.join(BASE, "competition/jessup_2025/team_strategy.txt"), "w") as f:
    f.write("""JESSUP 2025 TEAM STRATEGY
==========================
Topics: Use of force, humanitarian intervention, R2P
Primary databases needed: ICJ case law, UN documents, AJIL

Note: Jessup focuses on PUBLIC international law - ICJ jurisdiction,
state-to-state disputes, UN Charter interpretation.

Databases prioritized:
- ICJ website (free)
- UN Treaty Collection (free)  
- AJIL via HeinOnline
""")

# 8. Access credentials placeholder (distractor)
with open(os.path.join(BASE, "databases/access_logs/library_access.txt"), "w") as f:
    f.write("""LIBRARY DATABASE ACCESS STATUS
================================
Institution: Moot Court Team
Access Period: Academic Year 2024-2025

Status:
- Westlaw: ACTIVE (via university proxy)
- LexisNexis: ACTIVE
- HeinOnline: ACTIVE
- Oxford Academic: ACTIVE (note: check publication date restrictions)
- JSTOR: ACTIVE

For databases not on this list, contact library@university.edu
""")

# 9. Draft pleading fragment (distractor)
with open(os.path.join(BASE, "team_docs/pleadings/memorial_draft_v1.txt"), "w") as f:
    f.write("""MEMORIAL DRAFT v1 - CLAIMANT
=============================
I. JURISDICTION
[...]

II. STATE RESPONSIBILITY
Nordavia bears responsibility for the actions of NDC pursuant to the 
ILC Articles on State Responsibility. Article 8 ARSIWA provides that
conduct shall be attributed to a State if the person or group of persons
acting on the instructions of, or under the direction or control of,
that State.

The standard of control has been debated extensively. The ICJ in 
Nicaragua v. United States (1986) applied the "effective control" test.
The ICTY in Tadić (1999) applied a "overall control" standard.

[CITATION NEEDED - need to verify these and find more sources]
[ARGUMENT NEEDS DEVELOPMENT - find academic commentary]

III. DUE DILIGENCE
[TO BE COMPLETED - need research on due diligence in cyber context]
""")

# 10. Random case note files (distractors)
cases = [
    ("Nicaragua_v_US_1986.txt", "Nicaragua v. United States (1986)\nICJ Reports 14\nKey holding: Effective control standard for attribution\nNote: Military and Paramilitary Activities case"),
    ("Tadic_1999.txt", "Prosecutor v. Tadić (1999)\nICTY Appeals Chamber\nKey holding: Overall control standard\nNote: Different from ICJ's effective control test - tension in law"),
    ("Corfu_Channel_1949.txt", "Corfu Channel Case (1949)\nICJ Reports 4\nKey holding: State knowledge of dangerous activities = responsibility\nNote: Relevant to due diligence argument"),
]
for fname, content in cases:
    with open(os.path.join(BASE, "citations/cases", fname), "w") as f:
        f.write(content)

# 11. Distractor: wrong memo template
with open(os.path.join(BASE, "team_docs/memos/memo_template_WRONG.txt"), "w") as f:
    f.write("""RESEARCH MEMO TEMPLATE (GENERIC - NOT FOR INTERNATIONAL LAW)
=============================================================
Date:
Researcher:
Topic:
Sources consulted: [list databases used]
Key findings: [bullet points]
Recommended next steps: [action items]

NOTE: This template is for domestic law research.
For international law, a different format may be required.
""")

print("Workspace generated successfully.")
print(f"Files created in {BASE}:")
for root, dirs_list, files in os.walk(BASE):
    for file in files:
        print(f"  {os.path.join(root, file)}")