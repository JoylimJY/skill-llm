import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "research/case_law/human_rights",
    "research/case_law/administrative",
    "research/articles",
    "briefs/applicant",
    "briefs/respondent",
    "team/schedules",
    "team/contacts",
    "precedents/iccpr",
    "precedents/echr",
    "notes/drafts",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "research/case_law/human_rights/Mukong_v_Cameroon.txt": (
        "Mukong v. Cameroon (1994)\nHRC Communication No. 458/1991\n"
        "Held: Detention conditions violated Art.10 ICCPR.\n"
        "Key ratio: minimum standards apply regardless of resources.\n"
    ),
    "research/case_law/human_rights/Van_Alphen_v_Netherlands.txt": (
        "Van Alphen v. Netherlands (1990)\nHRC Communication No. 305/1988\n"
        "Held: Detention not shown to be necessary – arbitrary.\n"
    ),
    "research/case_law/administrative/Chahal_v_UK.txt": (
        "Chahal v. United Kingdom (1996) ECHR\n"
        "National security detention – procedural safeguards required.\n"
    ),
    "research/articles/manfredi_arbitrariness.pdf.txt": (
        "Manfredi (2019) 'Reconsidering Arbitrariness in International Human Rights Law'\n"
        "Abstract: This article examines the three-limbed arbitrariness test...\n"
        "[Full text not available – purchase via JSTOR]\n"
    ),
    "research/articles/steiner_liberty.txt": (
        "Steiner & Alston – International Human Rights in Context (3rd ed.)\n"
        "Chapter 12: Detention and the Right to Liberty pp. 480-532\n"
    ),
    "briefs/applicant/memorial_final_v3.txt": (
        "MEMORIAL FOR THE APPLICANT\nKingdom of Novaris v. Republic of Keldoria\n"
        "Submitted: 15 January 2025\nWord count: 9,842\n"
        "PART I – JURISDICTION [pp.1-3]\nPART II – CLAIM ONE [pp.4-14]\nPART III – CLAIM TWO [pp.15-22]\n"
    ),
    "briefs/respondent/memorial_respondent_v2.txt": (
        "MEMORIAL FOR THE RESPONDENT\nKingdom of Novaris v. Republic of Keldoria\n"
        "Submitted: 15 January 2025\n"
        "COUNTER-ARGUMENTS TO CLAIM ONE [pp.1-9]\nCOUNTER-ARGUMENTS TO CLAIM TWO [pp.10-18]\n"
    ),
    "team/contacts/judges_pool.txt": (
        "Available Mock Judges:\n"
        "- Prof. Elena Marchetti (Int'l Law, expertise: ICCPR)\n"
        "- Dr. Kenji Nakamura (Human Rights, expertise: detention)\n"
        "- Adv. Sofia Petrov (Practitioner, expertise: procedural law)\n"
        "- Dr. Amara Diallo (Academic, expertise: African human rights system)\n"
        "- Mr. Lucas Brennan (Postgrad, Jessup alumnus 2021)\n"
    ),
    "notes/drafts/claim1_brainstorm.txt": (
        "CLAIM ONE BRAINSTORM – rough notes\n"
        "- arbitrary detention angle: strongest because HRC General Comment 35 is directly on point\n"
        "- lawfulness of arrest: statutory basis but which statute?\n"
        "- reasons for arrest: Art 9(2) ICCPR – they were never informed\n"
        "- fair trial elements leaking into admin detention context?\n"
        "- duration of detention – 14 months pre-charge is extreme\n"
        "- NOTE: don't try to cover everything, pick best angles\n"
    ),
    "notes/drafts/claim2_brainstorm.txt": (
        "CLAIM TWO BRAINSTORM\n"
        "- non-refoulement: core principle, CAT Art.3\n"
        "- diplomatic assurances: weak, lots of bad precedent for us\n"
        "- effective remedy: procedural hook, Art.2(3) ICCPR\n"
        "- risk of torture: factual – good evidence in record\n"
        "- burden of proof: they bear it but we have evidence anyway\n"
    ),
    "precedents/iccpr/GC35_liberty.txt": (
        "Human Rights Committee General Comment No. 35 (2014)\n"
        "Article 9 (Liberty and Security of Person)\n"
        "Para 12: 'arbitrariness' includes elements of inappropriateness, injustice, "
        "lack of predictability and due process of law...\n"
        "Para 13: Remand in custody must be necessary, reasonable, and proportionate...\n"
    ),
    "precedents/echr/Chahal_summary.txt": (
        "Chahal v UK – procedural requirements for national security detention.\n"
        "Special advocate procedure approved. Art 5(4) ECHR requires meaningful review.\n"
    ),
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")

# ── PRIMARY INPUT 1: case_arguments.txt  ────────────────────────────────────
# Deliberately messy: wrong ordering (procedural before substantive),
# inflated weak arguments, and no clear hierarchy.
case_arguments_content = """\
ORAL ARGUMENT NOTES – Kingdom of Novaris v. Republic of Keldoria
Prepared by: Team Research Lead
Date: 2025-03-01
Status: DRAFT – ordering TBD

=============================================================
CLAIM ONE: Violation of the Right to Liberty (Art. 9 ICCPR)
=============================================================

Sub-argument C1-A: LAWFULNESS OF ARREST
  Type: procedural
  Strength assessment: moderate-weak
  Notes: Respondent did not follow domestic statutory procedure for issuing
         arrest warrant. Pure procedural defect. Not very significant legally
         but easy to explain. Probably not what judges care most about.

Sub-argument C1-B: ARBITRARY DETENTION
  Type: substantive
  Strength assessment: VERY STRONG
  Notes: HRC General Comment 35 directly supports our interpretation. Multiple
         HRC Views (Fillastre, Mukong, Van Alphen) all support arbitrariness
         finding. This is THE central issue in liberty jurisprudence. Scholars
         universally treat this as the primary prism for Art.9 analysis.
         Human Rights Committee's own interpretation is binding guidance.

Sub-argument C1-C: RIGHT TO BE INFORMED OF REASONS FOR ARREST
  Type: substantive (but narrower)
  Strength assessment: strong
  Notes: Art.9(2) – detainees were never told why they were being held. Good
         factual record. However, this is slightly narrower than C1-B and
         functions as a supporting point rather than a freestanding claim.
         Judges may conflate with C1-B so should come after C1-B is established.

Sub-argument C1-D: RIGHT TO FAIR TRIAL ELEMENTS IN ADMINISTRATIVE DETENTION
  Type: substantive (doctrinal bridge)
  Strength assessment: moderate-strong
  Notes: Controversial doctrinal point – arguing that Art.14 fair trial
         guarantees partially apply to administrative detention. Interesting
         and provocative for specialist judges. Should come BEFORE the narrow
         Art.9(2) reason-for-arrest point because its theoretical scope is
         broader and requires a different analytical lens (focuses on WHY
         criminal procedure norms extend to admin detention, not just on
         quantification of rights violations).

Sub-argument C1-E: DURATION OF DETENTION
  Type: factual/substantive
  Strength assessment: moderate
  Notes: 14 months pre-charge. Supports arbitrariness but is really just
         evidence for C1-B rather than a standalone point. Can be woven in.

=============================================================
CLAIM TWO: Non-Refoulement Violation (CAT Art.3 / ICCPR Art.7)
=============================================================

Sub-argument C2-A: DIPLOMATIC ASSURANCES ARE INSUFFICIENT
  Type: substantive
  Strength assessment: WEAK
  Notes: Our position relies on arguing assurances were vague and unenforceable.
         BUT there is a lot of case law where tribunals have accepted assurances.
         This is our weakest point. Mention briefly if at all; if not asked,
         skip it.

Sub-argument C2-B: RISK OF TORTURE IS WELL-ESTABLISHED
  Type: factual/substantive  
  Strength assessment: VERY STRONG
  Notes: Record contains three independent NGO reports, prior documented
         incidents of torture of political detainees, and a UN Special
         Rapporteur visit report. Overwhelming factual basis. This is the
         foundation of Claim Two.

Sub-argument C2-C: EFFECTIVE REMEDY OBLIGATION
  Type: procedural
  Strength assessment: moderate
  Notes: Art.2(3) ICCPR – state failed to provide any meaningful domestic
         remedy. Procedural hook. Important but secondary to the substantive
         non-refoulement argument.

Sub-argument C2-D: BURDEN OF PROOF AND STANDARD
  Type: procedural/evidentiary
  Strength assessment: moderate-strong
  Notes: CAT Committee jurisprudence: once a prima facie case is made, burden
         shifts. We have made the prima facie case (see C2-B). This evidentiary
         argument SHOULD come right after C2-B to reinforce why respondent
         cannot escape. It is a doctrinal bridge, not just procedure.

=============================================================
WEAKNESSES TO CONSIDER
=============================================================
W1: State argued national security exception – we have a counterargument but
    it's not airtight. Only address if judge asks.
W2: Diplomatic assurances (C2-A) – concede weakness and move on quickly.
W3: Jurisdiction over Claim Two has been challenged – we have a solid response
    but it's purely procedural; don't volunteer it.
"""

(workspace / "case_arguments.txt").write_text(case_arguments_content, encoding="utf-8")

# ── PRIMARY INPUT 2: competition_calendar.txt  ──────────────────────────────
# Provides competition dates for scheduling mock sessions
competition_calendar_content = """\
JESSUP 2025 – TEAM COMPETITION SCHEDULE
Team: Novaris University School of Law

--- KEY DATES ---

First available date for moot practice: 2025-03-10

Regional Rounds:
  Round R1: 2025-04-05 (National Regional Preliminary – Day 1)
  Round R2: 2025-04-06 (National Regional Preliminary – Day 2)
  Round R3: 2025-04-07 (National Regional Finals)

International Rounds (Washington D.C.):
  Round I1: 2025-04-26 (International Preliminary – Room A)
  Round I2: 2025-04-27 (International Preliminary – Room B)
  Round I3: 2025-04-29 (International Advanced Rounds)

--- NOTES ---
- Team departs for Washington on 2025-04-23
- All practice must be completed before departure
- International rounds: treat 2025-04-25 as last possible practice date (day before I1)
"""

(workspace / "competition_calendar.txt").write_text(competition_calendar_content, encoding="utf-8")

# ── PRIMARY INPUT 3: team_roster.txt  ───────────────────────────────────────
team_roster_content = """\
TEAM ROSTER – Novaris University Jessup 2025

ORALISTS:
  1. Maya Chen       – Oralist A (Claim One lead)
  2. Tobias Ritter   – Oralist B (Claim Two lead)

SUPPORTING MEMBERS:
  3. Priya Anand     – Researcher / Memorial writer
  4. Leo Fontaine    – Researcher / Memorial writer
  5. Suki Watanabe   – Team Manager / Logistics

EXTERNAL COACHES/JUDGES AVAILABLE:
  6. Prof. Elena Marchetti  – Senior coach (available Mon/Wed/Fri only)
  7. Dr. Kenji Nakamura     – Mock judge (available weekends)
  8. Adv. Sofia Petrov      – Mock judge (available Thursdays and weekends)

NOTES:
  - Priya and Leo can serve as mock judges when external judges unavailable
  - Suki handles timing duties for all mock sessions
  - All 5 team members must participate in each mock session in some capacity
"""

(workspace / "team_roster.txt").write_text(team_roster_content, encoding="utf-8")

# ── Extra distractor ─────────────────────────────────────────────────────────
(workspace / "team/schedules/old_schedule_v1.txt").write_text(
    "DEPRECATED – DO NOT USE\nOld practice schedule from January. Superseded by competition_calendar.txt\n",
    encoding="utf-8",
)
(workspace / "notes/drafts/timing_rough.txt").write_text(
    "Rough timing ideas:\n- Each speaker maybe 15 min? or 20?\n- Need to check rules\n"
    "- Applicant goes first always\n- Rebuttal 2-3 min?\n",
    encoding="utf-8",
)

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")