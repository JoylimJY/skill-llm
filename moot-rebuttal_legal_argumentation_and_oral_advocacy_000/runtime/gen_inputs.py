import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor structure
dirs = [
    "case_files/exhibits",
    "case_files/pleadings/written",
    "case_files/pleadings/oral",
    "research/precedents/icj",
    "research/precedents/icsid",
    "research/secondary_sources",
    "team_notes/applicant",
    "team_notes/respondent",
    "competition_rules",
    "practice_rounds/round1",
    "practice_rounds/round2",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "case_files/exhibits/exhibit_A_treaty_text.txt": "Article 12: States shall ensure freedom of movement for all persons within their jurisdiction...\nArticle 15: Emergency measures may be taken in cases of public health threats, subject to proportionality.",
    "case_files/exhibits/exhibit_B_state_communication.txt": "Official Note Verbale dated 14 March 2021:\nThe Government of Arantia hereby notifies the closure of its land borders effective immediately...",
    "case_files/pleadings/written/memorial_applicant.txt": "IN THE INTERNATIONAL COURT OF JUSTICE\nCASE CONCERNING BORDER RESTRICTIONS\nBetween VALDORIA (Applicant) and ARANTIA (Respondent)\n\nMEMORIAL OF THE APPLICANT\n\n1. Valdoria submits that Arantia's border closure violates Article 12 of the 2005 Bilateral Mobility Treaty...",
    "case_files/pleadings/written/counter_memorial_respondent.txt": "COUNTER-MEMORIAL OF THE RESPONDENT\n\n1. Arantia submits that the border closure was a lawful exercise of emergency powers under customary international law...\n2. The measures were necessary, proportionate, and temporary...",
    "case_files/pleadings/oral/applicant_opening_notes.txt": "Agent 1 opening - cover jurisdiction and admissibility\nAgent 2 - merits: treaty violation and state responsibility",
    "research/precedents/icj/nicaragua_v_usa_summary.txt": "Military and Paramilitary Activities Case (1986):\nCourt found that customary international law prohibits intervention...",
    "research/precedents/icj/corfu_channel_summary.txt": "Corfu Channel Case (1949):\nAlbania held responsible for failure to notify mines...",
    "research/precedents/icsid/arbitration_notes.txt": "Note: ICSID rules differ from ICJ procedure. Not directly applicable here.",
    "research/secondary_sources/brownlie_extract.txt": "Principles of Public International Law (Brownlie):\nState responsibility arises from internationally wrongful acts attributable to the state...",
    "research/secondary_sources/crawford_commentary.txt": "ILC Articles on State Responsibility, Commentary:\nArticle 25 - Necessity: A state may not invoke necessity unless the act is the only way to safeguard an essential interest...",
    "team_notes/applicant/strategy_notes.txt": "Focus on: (1) treaty obligation is clear and unambiguous; (2) emergency exception does not apply because measures were disproportionate; (3) Arantia failed to notify Valdoria in advance.",
    "team_notes/respondent/strategy_notes.txt": "Defense: (1) necessity under customary law; (2) treaty's Article 15 emergency clause applies; (3) measures were proportionate and temporary.",
    "team_notes/applicant/agent1_outline.txt": "Jurisdiction: Compromissory clause in Article 22 of the Treaty. Admissibility: No requirement for prior diplomatic negotiations exhausted.",
    "team_notes/respondent/agent2_outline.txt": "Merits defense: Article 15 is lex specialis. Necessity doctrine applies. No breach of treaty.",
    "competition_rules/scoring_rubric.txt": "Oral Advocacy Scoring (per judge, per speaker):\n- Knowledge of law: 0-10\n- Responsiveness: 0-10\n- Organization: 0-10\n- Style & Delivery: 0-10\nTotal: 40 points per speaker per judge.",
    "competition_rules/time_limits.txt": "Time Limits:\n- Opening submissions (Agent 1): 20 minutes\n- Opening submissions (Agent 2): 20 minutes\n- Rebuttal: 5 minutes\n- Surrebuttal: 5 minutes\nRed light = time expired. Yellow light = 2 minutes remaining.",
    "practice_rounds/round1/feedback.txt": "Round 1 Coach Feedback:\n- Rebuttal was too long and introduced new arguments not raised in main submissions.\n- Need to practice the formal opening phrases.\n- Surrebuttal missed Agent 1's point about proportionality.",
    "practice_rounds/round2/feedback.txt": "Round 2 Coach Feedback:\n- Good improvement. Watch tone during rebuttal - don't sound confrontational.\n- Time extension request phrasing was incorrect - you said 'I see my time is up' instead of the proper formula.",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN PROBLEM FILE: case brief with opponent's arguments for rebuttal exercise
case_brief = """MOOT COURT PRACTICE BRIEF
Case: Valdoria v. Arantia (Border Closure During Public Health Emergency)
Round: Final Round Oral Arguments

=== BACKGROUND ===
Valdoria (Applicant) claims Arantia (Respondent) violated the 2005 Bilateral Mobility Treaty by
closing its land borders without notice during a declared public health emergency, stranding
thousands of Valdorian workers.

=== RESPONDENT'S (ARANTIA'S) MAIN ORAL ARGUMENTS ===
The following arguments were presented by Arantia's two agents during their submissions:

RESPONDENT AGENT 1 argued:
  [R1] The border closure was authorized under Article 15 of the Treaty, which permits emergency
       measures during public health crises, and Arantia satisfied all conditions of that clause.
  [R2] Under customary international law, the doctrine of necessity (ILC Article 25) provides an
       independent legal basis for the measures, as Arantia faced an imminent threat to an
       essential interest (public health of 4 million citizens).

RESPONDENT AGENT 2 argued:
  [R3] The measures were proportionate: the closure lasted only 47 days and targeted only land
       borders, not air travel, demonstrating a calibrated response.
  [R4] Valdoria's own travel advisories issued the same week implicitly acknowledged the
       legitimacy of such restrictions, constituting a form of acquiescence.

=== APPLICANT'S (VALDORIA'S) TASK ===
The Applicant must now prepare a REBUTTAL targeting Arantia's arguments.
After the rebuttal, the Respondent must prepare a SURREBUTTAL responding to all of Applicant's
rebuttal points.

Additionally, during practice, the Applicant's agent has been told to prepare the exact
time-extension request phrase to use at the moment the red light activates (time has expired).

=== INSTRUCTION ===
Produce the file 'rebuttal_script.txt' containing all three components as described above.
"""

with open(os.path.join(workspace, "case_brief.txt"), "w", encoding="utf-8") as f:
    f.write(case_brief)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in os.walk(workspace) for f in _[2])}")