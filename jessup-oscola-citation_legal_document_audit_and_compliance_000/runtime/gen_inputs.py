import os
import json
import random

random.seed(42)

# Create a realistic deeply-nested workspace simulating a moot court team's project folder
base = "/workspace"

dirs = [
    "jessup_2024/briefs/applicant",
    "jessup_2024/briefs/respondent",
    "jessup_2024/research/case_law",
    "jessup_2024/research/treaties",
    "jessup_2024/research/articles",
    "jessup_2024/admin/schedules",
    "jessup_2024/admin/team_notes",
    "jessup_2024/drafts/v1",
    "jessup_2024/drafts/v2",
    "jessup_2024/references/oscola_examples",
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Distractor files
distractors = [
    ("jessup_2024/admin/schedules/timeline.txt",
     "Dec 1: First meeting\nDec 5: Research complete\nDec 10: First draft due\nJan 15: Final submission\n"),
    ("jessup_2024/admin/team_notes/meeting_notes_nov28.txt",
     "Discussed memorial structure. Agreed on 4 issues. Assigned sections to team members.\n"),
    ("jessup_2024/research/case_law/icj_cases_list.txt",
     "Nicaragua v USA (1986)\nCorfu Channel (1949)\nGenocide Convention (Bosnia v Serbia) (2007)\nKosovo Advisory Opinion (2010)\n"),
    ("jessup_2024/research/treaties/treaty_sources.txt",
     "Vienna Convention on the Law of Treaties 1969\nUN Charter 1945\nStatute of the ICJ 1945\n"),
    ("jessup_2024/research/articles/relevant_authors.txt",
     "Malcolm Shaw, International Law (8th edn, CUP 2017)\nIan Brownlie, Principles of Public International Law\nAntonio Cassese, International Law\n"),
    ("jessup_2024/admin/team_notes/style_discussion.txt",
     "Team discussed citation style. Some prefer Bluebook, others OSCOLA. Need to decide.\n"),
    ("jessup_2024/drafts/v1/outline_v1.txt",
     "Issue I: Jurisdiction\nIssue II: State Responsibility\nIssue III: Self-Defense\nIssue IV: Remedies\n"),
    ("jessup_2024/drafts/v2/outline_v2.txt",
     "Updated outline after supervisor feedback. Issue III merged with II.\n"),
    ("jessup_2024/references/oscola_examples/oscola_quick_ref.txt",
     "Case: Party v Party [year] Reporter page\nBook: Author, Title (edition, Publisher year)\nJournal: Author, 'Title' (year) vol Journal abbrev first page, pinpoint\n"),
    ("jessup_2024/research/articles/icj_procedure_notes.txt",
     "Provisional measures under Article 41 ICJ Statute.\nAdmissibility challenges must be raised as preliminary objections.\n"),
    ("jessup_2024/briefs/respondent/respondent_skeleton.txt",
     "Respondent argues: 1) No jurisdiction, 2) No breach, 3) No reparation owed.\n"),
]

for fpath, content in distractors:
    with open(os.path.join(base, fpath), "w", encoding="utf-8") as f:
        f.write(content)

# =========================================================
# THE MAIN PROBLEM FILE: A messy Jessup applicant memorial
# with deliberate citation violations
# =========================================================

# We will craft a brief with the following planted violations:
#
# VIOLATION TYPE 1: MIXED CITATION STYLES
#   - Footnotes 1, 2, 3, 6, 9, 11 use OSCOLA format
#   - Footnotes 4, 7, 10 use Bluebook format  (mixed → violation)
#   - Footnote 5 uses APA format              (mixed → violation)
#
# VIOLATION TYPE 2: MISSING PAGE NUMBERS
#   - Footnote 8: cites a case but no pinpoint page
#   - Footnote 12: cites a journal article but no pinpoint page
#   - Footnote 3: CORRECT (has page number) — not a violation
#
# VIOLATION TYPE 3: INCORRECT SUPRA NOTE REFERENCES
#   - Footnote 14: "Shaw (n 3)" — but Shaw was first cited in footnote 6, not 3 → WRONG
#   - Footnote 16: "Nicaragua (n 2)" — Nicaragua was first cited in footnote 1 → WRONG
#   - Footnote 18: "Corfu Channel (n 9)" — Corfu Channel first cited in footnote 9 → CORRECT (not a violation)
#   - Footnote 20: "Cassese (n 11)" — Cassese first cited in footnote 11 → CORRECT (not a violation)
#   - Footnote 22: "Vienna Convention (n 7)" — Vienna Convention first cited in footnote 4 → WRONG (also Bluebook original)

brief_text = """MEMORIAL FOR THE APPLICANT

IN THE INTERNATIONAL COURT OF JUSTICE

FEDERATIVE REPUBLIC OF AURELIA
v.
KINGDOM OF BRANDONIA

MEMORIAL OF THE APPLICANT

───────────────────────────────────────────────────────────

TABLE OF CONTENTS

I.    STATEMENT OF JURISDICTION .....................................  3
II.   STATEMENT OF FACTS .............................................  5
III.  STATEMENT OF LAW ...............................................  8
IV.   SUBMISSIONS ....................................................  42

───────────────────────────────────────────────────────────

I. STATEMENT OF JURISDICTION

The International Court of Justice has jurisdiction over this dispute pursuant to Article 36(2) of the Statute of the ICJ, to which both Aurelia and Brandonia are parties.¹ The Court has consistently held that declarations under the Optional Clause create binding obligations between accepting States.² Brandonia's reservation cannot exclude the present dispute from the Court's jurisdiction.³

───────────────────────────────────────────────────────────

II. STATEMENT OF FACTS

2.1 Background

Aurelia and Brandonia share a 400-kilometre border established by the Treaty of Velantia (1923). Relations deteriorated following Brandonia's announcement of the "Sovereign Resource Doctrine" in March 2023.⁴

2.2 The Incident

On 14 April 2023, Brandonian armed forces entered Aurelian territory and destroyed the Kelvari hydroelectric facility.⁵ Forty-seven Aurelian nationals were killed. Aurelia protested the incursion through diplomatic notes dated 15 and 22 April 2023.⁶

2.3 Subsequent Events

Brandonia claimed the action was a lawful exercise of self-defence under Article 51 of the UN Charter.⁷ Aurelia denies that any armed attack against Brandonia had occurred prior to the incursion.⁸ Negotiations between the parties broke down in July 2023.⁹

───────────────────────────────────────────────────────────

III. STATEMENT OF LAW

ISSUE I: THE COURT HAS JURISDICTION

3.1 Brandonia's Optional Clause Declaration

Both States have accepted the compulsory jurisdiction of the Court.¹⁰ The Court confirmed in the Nicaragua case that the Optional Clause creates binding obligations.¹¹ Brandonia cannot invoke its reservation to exclude the present dispute.

3.2 The Reservation Does Not Apply

The reservation invoked by Brandonia concerns disputes arising from "multilateral treaty obligations."¹² The present claim is grounded in customary international law, not treaty law alone. Shaw has argued that reservations must be interpreted narrowly.¹³ This view has been consistently upheld.¹⁴

ISSUE II: BRANDONIA BEARS STATE RESPONSIBILITY

3.3 Attribution of Conduct

The conduct of Brandonian armed forces is attributable to Brandonia under Article 4 of the ILC Articles on State Responsibility.¹⁵ The Nicaragua judgment established the standard of "effective control" for attribution.¹⁶ Brandonia exercised full effective control over the forces that conducted the incursion.

3.4 Breach of Obligation

The destruction of the Kelvari facility constitutes a breach of the prohibition on the use of force under Article 2(4) of the UN Charter.¹⁷ The Corfu Channel case established that States may not use their territory to conduct acts prejudicial to another State.¹⁸ This principle applies with equal force to the present situation.

ISSUE III: BRANDONIA'S SELF-DEFENCE CLAIM IS UNFOUNDED

3.5 No Armed Attack

For self-defence to be lawful under Article 51, an armed attack must have occurred.¹⁹ Cassese has noted that the threshold for an armed attack is high and cannot be satisfied by minor frontier incidents.²⁰ No such attack preceded Brandonia's incursion.

3.6 Proportionality

Even if an armed attack had occurred, Brandonia's response was wholly disproportionate.²¹ The Vienna Convention principles of treaty interpretation confirm that Article 51 must be read restrictively.²² Destroying a civilian infrastructure facility serving 2 million people cannot satisfy the proportionality requirement.

───────────────────────────────────────────────────────────

IV. SUBMISSIONS

For the foregoing reasons, Aurelia respectfully requests the Court to adjudge and declare that:

(1) The Court has jurisdiction over this dispute;
(2) Brandonia has violated its obligations under international law;
(3) Brandonia is under an obligation to make full reparation.

Respectfully submitted on behalf of the Applicant.

───────────────────────────────────────────────────────────

FOOTNOTES

1. Military and Paramilitary Activities in and against Nicaragua (Nicaragua v United States of America) (Jurisdiction) [1984] ICJ Rep 392, 399.
2. Corfu Channel Case (United Kingdom v Albania) (Merits) [1949] ICJ Rep 4, 22.
3. Malcolm Shaw, International Law (8th edn, Cambridge University Press 2017) 701.
4. Treaty of Velantia, 44 UNTS 112, 115 (1923).
5. A. Cassese, International Law (2nd ed., Oxford University Press, 2005), p. 148.
6. Vienna Convention on the Law of Treaties (adopted 23 May 1969, entered into force 27 January 1980) 1155 UNTS 331, art 31.
7. UN Charter art 51, in Military and Paramilitary Activities in and against Nicaragua (Nicaragua v United States of America) (Merits) 1986 I.C.J. 14, 103 (June 27).
8. Gabčíkovo-Nagymaros Project (Hungary v Slovakia) (Judgment) [1997] ICJ Rep 7.
9. Legality of the Threat or Use of Nuclear Weapons (Advisory Opinion) [1996] ICJ Rep 226, 244.
10. Armed Activities on the Territory of the Congo (Democratic Republic of the Congo v Uganda) (Judgment) [2005] ICJ Rep 168, 223.
11. Nicaragua (n 1) 418.
12. Marko Milanovic, 'State Responsibility for Genocide' (2006) 17 European Journal of International Law 553.
13. Malcolm Shaw, International Law (8th edn, Cambridge University Press 2017) 714.
14. Shaw (n 3) 714.
15. ILC, 'Articles on Responsibility of States for Internationally Wrongful Acts' (2001) UN Doc A/56/10, art 4.
16. Nicaragua (n 2) 64.
17. UN Charter art 2(4).
18. Corfu Channel (n 9) 22.
19. Oil Platforms (Islamic Republic of Iran v United States of America) (Judgment) [2003] ICJ Rep 161, 187.
20. Cassese (n 11) 148.
21. Legality of the Threat or Use of Nuclear Weapons (n 9) 245.
22. Vienna Convention (n 7) art 31.
"""

brief_path = os.path.join(base, "jessup_2024/briefs/applicant/applicant_memorial_draft.txt")
with open(brief_path, "w", encoding="utf-8") as f:
    f.write(brief_text)

# Also write a metadata file about the brief (distractor)
meta = {
    "document": "Applicant Memorial - Draft v3",
    "team": "Aurelia",
    "last_edited": "2024-12-08",
    "word_count": 1247,
    "status": "needs citation review"
}
with open(os.path.join(base, "jessup_2024/briefs/applicant/brief_metadata.json"), "w") as f:
    json.dump(meta, f, indent=2)

# Write a partial citation style guide (distractor, not the real SKILL.md)
with open(os.path.join(base, "jessup_2024/references/oscola_examples/partial_guide.txt"), "w", encoding="utf-8") as f:
    f.write("""PARTIAL OSCOLA NOTES (INCOMPLETE)

Cases: Party v Party (year) Reporter page
Books: Author, Title (edn, Publisher year) page
Supra: Short title (n X) pinpoint

Note: This is an incomplete internal guide. Refer to official SKILL.md for full rules.
""")

print("Workspace generated successfully.")
print(f"Main brief: {brief_path}")
print("\nPlanted violations summary:")
print("MIXED STYLES: FN4 (Bluebook treaty), FN5 (APA), FN7 (Bluebook ICJ case)")
print("MISSING PAGE NUMBERS: FN8 (Gabcikovo - no pinpoint), FN12 (Milanovic article - no pinpoint)")
print("WRONG SUPRA REFS: FN14 'Shaw (n 3)' should be (n 13); FN16 'Nicaragua (n 2)' should be (n 1); FN22 'Vienna Convention (n 7)' should be (n 6)")