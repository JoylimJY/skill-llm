import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# Directory structure
dirs = [
    "case_materials/facts",
    "case_materials/exhibits",
    "research/international_law",
    "research/precedents",
    "drafts/old_versions",
    "drafts/notes",
    "team_docs/schedule",
    "team_docs/contacts",
    "training/mock_sessions",
    "training/feedback",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ---- Distractor files ----

# 1. Research memo (distractor)
with open(os.path.join(WORKSPACE, "research/international_law/icc_jurisdiction_memo.md"), "w") as f:
    f.write("""# ICC Jurisdiction Research Memo

## Issue: Jurisdiction under Article 25 of the ICC Rules

The ICC Rules (2021) provide broad arbitral jurisdiction over commercial disputes.
Key case: *Dallah v Pakistan* [2010] UKSC 46 - establishes the separability doctrine.

**Relevant provisions:**
- Art. 6(3): The arbitral tribunal has the power to rule on its own jurisdiction.
- Art. 23: Terms of Reference must be established.
- Art. 25: Establishing the facts of the case.

*Note: always check the governing law clause in the contract.*
""")

# 2. Citation list (distractor)
with open(os.path.join(WORKSPACE, "research/precedents/citation_list.txt"), "w") as f:
    f.write("""CITATION LIST - ICC Case Preparation

1. ICC Award No. 12345 (2019) - Force Majeure interpretation
2. Metalclad Corp v Mexico, ICSID Case ARB(AF)/97/1
3. Siemens v Argentina, ICSID Case ARB/02/8
4. Chevron v Ecuador, PCA Case 2009-23
5. ICC Award No. 6560 (1990) - Good faith obligation
6. Vienna Convention on the Law of Treaties, Art. 31
7. UNIDROIT Principles 2016, Art. 7.1.7
""")

# 3. Old schedule (distractor)
with open(os.path.join(WORKSPACE, "team_docs/schedule/training_schedule.txt"), "w") as f:
    f.write("""TEAM TRAINING SCHEDULE - Week 8

Monday: Practice oral argument (Issue 1)
Tuesday: Research review - force majeure precedents
Wednesday: Full mock session - invite Prof. Chen as judge
Thursday: Q&A session with coach
Friday: Final script polish + timing run
Saturday: Rest / light review
Sunday: Travel to competition venue
""")

# 4. Contact list (distractor)
with open(os.path.join(WORKSPACE, "team_docs/contacts/judges_contact.txt"), "w") as f:
    f.write("""POTENTIAL MOCK JUDGES

1. Prof. Li Wei - Commercial Law, Tsinghua University - liwei@tsinghua.edu.cn
2. Atty. Sarah Johnson - ICC Arbitrator - sjohnson@lawfirm.com
3. Mr. David Park - Former Vis Moot Champion (2018) - dpark@chamber.com
4. Dr. Amara Diallo - OHADA Law Expert - adiallo@university.fr
""")

# 5. Exhibit (distractor)
with open(os.path.join(WORKSPACE, "case_materials/exhibits/contract_excerpt.txt"), "w") as f:
    f.write("""EXCERPT FROM SUPPLY AGREEMENT (Exhibit C-1)

Article 12 - Force Majeure
"Neither party shall be liable for any delay or failure to perform its obligations under 
this Agreement if such delay or failure is caused by circumstances beyond its reasonable 
control, including but not limited to acts of God, government regulations, war, or 
pandemic events."

Article 15 - Governing Law & Dispute Resolution
"This Agreement shall be governed by Swiss law. All disputes shall be finally settled 
under the ICC Rules of Arbitration by three arbitrators appointed in accordance 
with said Rules."

Article 16 - Notice
"All notices shall be in writing and delivered by registered mail or electronic means."
""")

# 6. Old feedback notes (distractor)
with open(os.path.join(WORKSPACE, "training/feedback/mock_session_3_feedback.txt"), "w") as f:
    f.write("""MOCK SESSION 3 FEEDBACK - Coach Notes

General:
- Good energy but speaking too fast
- Lost track of argument structure mid-way
- Recovered well after judge's question on Art. 25

Specific comments:
- Oralist 1: needs to work on transitions between claims
- Oralist 2: strong on facts but weak on legal citations
- Both: eye contact needs improvement
- Timing: Oralist 1 ran 2 min over; Oralist 2 finished 3 min early

Action items:
- Practice roadmap delivery
- Memorize paragraph numbers for key facts
- Reduce filler words ("um", "basically", "so")
""")

# 7. Exhibits index (distractor)
with open(os.path.join(WORKSPACE, "case_materials/exhibits/exhibits_index.txt"), "w") as f:
    f.write("""EXHIBITS INDEX

C-1: Supply Agreement dated 15 March 2021
C-2: Purchase Order No. 2021-447
C-3: Email correspondence (March-June 2021)
C-4: Bank transfer records
C-5: Expert report on market conditions
R-1: Notice of Force Majeure (Respondent)
R-2: Government decree (pandemic restrictions)
R-3: Alternative supplier records
""")

# 8. Random research notes (distractor)
with open(os.path.join(WORKSPACE, "research/international_law/good_faith_research.md"), "w") as f:
    f.write("""# Good Faith in International Commercial Arbitration

## Overview
Good faith is a general principle recognized across civil and common law systems.

## Key Sources
- UNIDROIT Principles Art. 1.7: duty to act in good faith and fair dealing
- Swiss Code of Obligations Art. 2: prohibition of manifest abuse of rights
- ICC Award 5713: good faith requires disclosure of material information

## Application to Our Case
The Respondent's failure to notify promptly may constitute bad faith under Swiss law.
Relevant paragraph: ¶ 34-38 of the Moot Problem.
""")

# 9. Training drill notes (distractor)
with open(os.path.join(WORKSPACE, "training/mock_sessions/drill_notes.txt"), "w") as f:
    f.write("""DRILL NOTES - Rebuttal Practice

Focus areas:
1. Counter-argument on Force Majeure foreseeability
2. Response to "why didn't you mitigate?" question
3. Distinguish Metalclad from our facts

Timing targets:
- Rebuttal: 3 minutes max
- Surrebuttal: 2 minutes max

Remember: stay calm, do not get defensive, address the panel directly.
""")

# 10. Old argument outline (distractor - wrong format, not a proper script)
with open(os.path.join(WORKSPACE, "drafts/notes/rough_argument_outline.txt"), "w") as f:
    f.write("""ROUGH OUTLINE - NOT FINAL

Issue 1: Jurisdiction
- Art. 6(3) ICC Rules
- Dallah case
- Our position: tribunal has jurisdiction

Issue 2: Force Majeure
- Art. 12 of contract
- UNIDROIT 7.1.7
- Government decree qualifies
- Respondent failed to notify properly

Need to write actual script later.
""")

# ---- THE PROBLEM FILE: A messy, error-laden draft script ----
# This is what the agent must REPLACE/TRANSFORM by producing the correct output

with open(os.path.join(WORKSPACE, "drafts/old_versions/BROKEN_draft_script_v1.md"), "w") as f:
    f.write("""# DRAFT ORAL ARGUMENT SCRIPT - ICC CASE 2024 (DO NOT USE - OLD VERSION)

## Oralist 1 Draft (BROKEN - many errors, for reference only)

Your Excellency, Mister Arbitrators,    <!-- WRONG: ICC uses "Your Honor" not "Your Excellency" -->

I am the counsel for the Applicant in this case.    <!-- WRONG: should use "we" not "I" -->
I will address two issues today: Jurisdiction and Force Majeure.    <!-- missing roadmap structure -->

**On Issue 1: Jurisdiction**

I submit that this tribunal has all jurisdiction over this dispute.   <!-- WRONG: "all" is an absolute word, avoid -->
Every provision of the ICC Rules supports my position.   <!-- WRONG: "every", "my" -->
I believe that many cases support this view.   <!-- WRONG: "I", "many cases" vague -->

Thank you for your question, Your Excellency.    <!-- WRONG: should not say this; wrong title -->
I understand your concern, but I think the facts are clear.    <!-- WRONG: banned phrases; wrong pronouns -->

**On Issue 2: Force Majeure**

I will now turn to Force Majeure.   <!-- should be "we will" or "the Applicant submits" -->
The opinio juris (pronounced "JEW-ris") on this is clear.   <!-- WRONG pronunciation noted in skill -->
I argue that any reasonable interpretation supports our case.   <!-- WRONG: "I", "any" absolute word -->

Conclusion: I respectfully request that this tribunal rules in my favor.   <!-- WRONG: "I", "my" -->
Thank you very much.
""")

# ---- THE CASE FACTS FILE (the agent should use this as source material) ----
with open(os.path.join(WORKSPACE, "case_materials/facts/moot_problem_facts.md"), "w") as f:
    f.write("""# MOOT PROBLEM - ICC CASE 2024/447

## Parties
- **Applicant (Claimant):** NovaTech Solutions GmbH ("NovaTech"), a German technology manufacturer
- **Respondent:** PacificRim Distributors Ltd. ("PacificRim"), a Hong Kong distributor

## Seat of Arbitration: Geneva, Switzerland
## Applicable Rules: ICC Rules of Arbitration (2021)
## Governing Law: Swiss law

## Background Facts

¶1. On 15 March 2021, NovaTech and PacificRim entered into a two-year Supply Agreement 
for the exclusive distribution of NovaTech's semiconductor products in Southeast Asia.

¶2. The agreement required PacificRim to purchase a minimum of 50,000 units per quarter 
at a fixed price of USD 200 per unit.

¶3. On 12 April 2021, the Government of Hong Kong issued Decree No. HK-2021-88, 
imposing strict import restrictions on electronic components due to the ongoing 
semiconductor shortage and pandemic conditions.

¶4. PacificRim sent a notice to NovaTech on 3 May 2021 - approximately three weeks 
after the decree - invoking the force majeure clause and suspending all purchases.

¶5. NovaTech disputed the validity of the force majeure claim, arguing that:
   (a) the semiconductor shortage was foreseeable as of the contract signing date;
   (b) PacificRim failed to provide timely notice as required by the contract;
   (c) PacificRim did not take reasonable steps to mitigate the situation.

¶6. NovaTech subsequently found alternative buyers for 30,000 of the 50,000 units 
but suffered losses on the remaining 20,000 units.

¶7. On 10 September 2021, NovaTech filed a Request for Arbitration with the ICC.

¶8. PacificRim challenges the tribunal's jurisdiction, arguing the force majeure 
clause operates as a limitation on NovaTech's right to claim damages.

¶9. The estimated total damages claimed by NovaTech are USD 4,000,000 
(20,000 units × USD 200/unit).

¶10. PacificRim has counterclaimed for USD 500,000 in alleged losses due to 
NovaTech's failure to provide alternative sourcing assistance.

## Issues in Dispute

**Issue 1 (Jurisdiction):** Whether the ICC tribunal has jurisdiction to hear NovaTech's 
claims given PacificRim's jurisdictional objection.

**Issue 2 (Force Majeure):** Whether PacificRim's invocation of force majeure under 
Article 12 of the Supply Agreement was valid, and if not, what damages NovaTech 
is entitled to recover.
""")

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}")