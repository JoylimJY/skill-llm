import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "moot_prep/background",
    "moot_prep/drafts",
    "moot_prep/old_versions",
    "moot_prep/research/cases",
    "moot_prep/research/statutes",
    "moot_prep/team_notes",
    "moot_prep/opponent_analysis",
    "moot_prep/scoring_sheets",
    "admin/registrations",
    "admin/schedule",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Core input: Case Brief ───────────────────────────────────────────────────
case_brief = """\
CASE BRIEF — ARBITRATION MOOT COMPETITION 2025
===============================================
CASE REFERENCE: ICC/2025/ARB/0047

PARTIES:
  Claimant  : AURELION BIOTECH S.A. ("ABT"), a pharmaceutical manufacturer
               incorporated in the Republic of Solaris
  Respondent: MEDIVANCE DISTRIBUTION GmbH ("MDG"), a pharmaceutical
               distributor incorporated in the Federation of Krynn

BACKGROUND:
In January 2023, ABT and MDG entered into a Contract for the international
sale of 500,000 units of VaxPro-9, a novel antiviral vaccine. The Contract
was governed by the United Nations Convention on Contracts for the
International Sale of Goods (hereinafter "CISG") and specified delivery
to MDG's warehouse in Krynn by 30 June 2023.

KEY FACTS:
1. ABT delivered 498,000 units on 28 June 2023 (2,000 units short).
2. MDG conducted quality inspection on 15 July 2023 and discovered that
   approximately 12% of delivered units had temperature deviation records
   exceeding the ±2 °C threshold specified in Schedule B of the Contract.
3. MDG sent a written notice of non-conformity to ABT on 20 July 2023.
4. ABT disputes the validity of MDG's temperature logs, arguing MDG's
   storage facilities caused the deviation post-delivery.
5. MDG seeks: (a) reduction of price under Art. 50 CISG; (b) damages
   for lost resale contracts totalling EUR 2.4 million; (c) costs of
   disposal of non-conforming units (EUR 180,000).
6. ABT counterclaims: full payment of the outstanding invoice (EUR 3.1 M)
   and damages for wrongful repudiation.

DISPUTED ISSUES:
  Issue 1 – JURISDICTION: Whether the arbitral tribunal has jurisdiction
             given MDG's challenge based on the alleged invalidity of the
             arbitration clause (Art. 8 CISG and general principles of
             competence-competence).
  Issue 2 – CONFORMITY: Whether VaxPro-9 units were conforming at the
             time of delivery under Art. 35 CISG, and whether risk had
             passed to MDG under Art. 67 CISG at the relevant time.
  Issue 3 – REMEDIES: Whether MDG is entitled to the claimed price
             reduction and/or damages, and whether ABT's counterclaim
             for full invoice payment succeeds.

YOUR ROLE IN THIS COMPETITION:
  You are counsel for the CLAIMANT (ABT / Applicant side — building
  the primary argument, i.e., the "A party").

TIME ALLOCATION (as agreed between teams):
  Total pleading time per team: 20 minutes
  Recommended reservation for rebuttal/sur-rebuttal: 1 minute

TRIBUNAL COMPOSITION: Three arbitrators (Panel)

NOTE: The opposing counsel (MDG) is expected to challenge ABT's reliance
on the competence-competence doctrine and will likely argue that the
arbitration clause was unconscionably incorporated.
"""

with open(os.path.join(workspace, "moot_prep/background/case_brief.txt"), "w") as f:
    f.write(case_brief)

# ── Distractor 1: Old draft (contains bad phrases — DO NOT use as template) ──
old_draft = """\
OLD DRAFT v0.1 — DO NOT USE
============================
[Opening]
I think the tribunal should note that our client has fulfilled its obligations.
I believe the delivery was timely and conforming.
I am sorry for any confusion about the temperature logs.

Respondent is wrong to claim non-conformity.
The Respondent made a mistake in its inspection methodology.

[Issue 1 - Jurisdiction]
Any challenge to jurisdiction must fail. All arbitration clauses are valid.

[Transition]
Now, let us move to the next issue without further ado.

NOTES: This draft is rejected. Too informal. Rewrite from scratch.
"""
with open(os.path.join(workspace, "moot_prep/old_versions/draft_v0.1_REJECTED.txt"), "w") as f:
    f.write(old_draft)

# ── Distractor 2: Opponent analysis notes ────────────────────────────────────
opponent_notes = """\
OPPONENT ANALYSIS — MDG (Respondent)
=====================================
Likely arguments:
- Arbitration clause not incorporated: MDG will cite Art. 8 CISG (subjective
  intent) and argue no meeting of minds on dispute resolution.
- Non-conformity at delivery: Temperature deviation logs from MDG's IoT
  sensors are primary evidence. They will argue risk had NOT passed.
- Damages: Will claim EUR 2.58M total.

Weak points for us to exploit:
- MDG's own storage logs show 3-hour power outage on 5 July (post-delivery).
- MDG delayed notice by 22 days after inspection — borderline under Art. 39 CISG.
- MDG's resale contracts were speculative (no signed agreements presented).

Strategy: Focus tribunal attention on the power outage fact and the late notice.
"""
with open(os.path.join(workspace, "moot_prep/opponent_analysis/mdg_weaknesses.txt"), "w") as f:
    f.write(opponent_notes)

# ── Distractor 3: Research case notes ────────────────────────────────────────
case_notes = """\
CASE RESEARCH — KEY AUTHORITIES
================================
1. Arbitration Clause Validity:
   - Fiona Trust v Privalov [2007] UKHL 40: autonomy of arbitration clause.
   - Prima Paint Corp. v Flood & Conklin (US Supreme Court, 1967): separability.

2. CISG Conformity:
   - Bundesgerichtshof (BGH), Germany, 8 March 1995: Art. 35 — seller liable
     for goods not fit for ordinary purpose.
   - ICC Case No. 8128 (1995): risk passage under Art. 67 requires delivery
     to first carrier.

3. Late Notice:
   - OLG Frankfurt, 20 April 1994: Art. 39 CISG — notice must be given within
     a reasonable time; 30 days held reasonable in perishable goods context.

ABBREVIATIONS TO USE:
  - United Nations Convention on Contracts for the International Sale of Goods
    → CISG
  - International Chamber of Commerce → ICC
  - VaxPro-9 → VP9 (introduce on first use)
"""
with open(os.path.join(workspace, "moot_prep/research/cases/key_authorities.txt"), "w") as f:
    f.write(case_notes)

# ── Distractor 4: Statute excerpts ──────────────────────────────────────────
statute = """\
RELEVANT STATUTORY PROVISIONS
==============================
CISG Art. 35 — Conformity of Goods
  (1) The seller must deliver goods which are of the quantity, quality and
      description required by the contract …
  (2) … the goods do not conform with the contract unless they:
      (a) are fit for the purposes for which goods of the same description
          would ordinarily be used; …

CISG Art. 39 — Notice of Non-conformity
  (1) The buyer loses the right to rely on a lack of conformity of the goods
      if he does not give notice to the seller specifying the nature of the
      lack of conformity within a reasonable time after he has discovered it
      or ought to have discovered it.

CISG Art. 50 — Price Reduction
  If the goods do not conform with the contract … the buyer may reduce the
  price in the same proportion as the value that the goods actually delivered
  had at the time of delivery bears to the value that conforming goods would
  have had at that time.

CISG Art. 67 — Passing of Risk
  (1) If the contract of sale involves carriage of the goods and the seller
      is not bound to hand them over at a particular place, the risk passes
      to the buyer when the goods are handed over to the first carrier …
"""
with open(os.path.join(workspace, "moot_prep/research/statutes/cisg_excerpts.txt"), "w") as f:
    f.write(statute)

# ── Distractor 5: Team schedule ──────────────────────────────────────────────
schedule = """\
TEAM SCHEDULE — WEEK OF COMPETITION
====================================
Mon: Moot prep session 09:00-12:00 (Room 204)
Tue: Practice round vs. Team Epsilon, 14:00 (Moot Court Hall B)
Wed: Rest + individual prep
Thu: Registration + draw ceremony, 10:00 (Main Hall)
Fri: COMPETITION DAY 1 — Preliminary Rounds
     Round 1: 09:30 | Round 2: 14:00
Sat: COMPETITION DAY 2 — Elimination Rounds
     Quarters: 09:00 | Semis: 14:00 | Finals: 18:00

DRESS CODE: Business formal. No exceptions.
MATERIALS: Bring printed bundle + USB backup.
"""
with open(os.path.join(workspace, "admin/schedule/competition_schedule.txt"), "w") as f:
    f.write(schedule)

# ── Distractor 6: Scoring rubric ─────────────────────────────────────────────
rubric = """\
SCORING RUBRIC (Arbitrator's Sheet)
=====================================
Criterion                     Max Points
─────────────────────────────────────────
Knowledge of Law                   30
Argument & Analysis                30
Response to Questions              20
Style & Presentation               10
Organization & Clarity             10
─────────────────────────────────────────
TOTAL                             100

Notes from last year:
- Judges deduct heavily for reading from script.
- Eye contact was specifically praised/criticized.
- Time management: teams that ran over were penalised 5 points.
"""
with open(os.path.join(workspace, "moot_prep/scoring_sheets/arbitrator_rubric.txt"), "w") as f:
    f.write(rubric)

# ── Distractor 7: Registration admin ─────────────────────────────────────────
registration = """\
REGISTRATION CONFIRMATION
==========================
Team: AURELION BIOTECH LEGAL TEAM (Team #17)
Institution: Solaris University School of Law
Speakers: [TBD — finalize by Wed]
Coach: Prof. Verena Holt
Emergency Contact: +49-30-555-0147

Registration Fee: EUR 450 (PAID)
Hotel: Grand Arbitration Hotel, Room 312/313
Checkout: Sunday 11:00
"""
with open(os.path.join(workspace, "admin/registrations/team17_registration.txt"), "w") as f:
    f.write(registration)

# ── Distractor 8: Team internal memo ─────────────────────────────────────────
memo = """\
INTERNAL MEMO — CONFIDENTIAL
==============================
To: All team members
From: Coach Holt
Re: Strategy adjustment after practice round

After yesterday's practice round, I want to emphasize:
1. Do NOT say "I think" or "I believe" in front of the tribunal. Use "submit".
2. Stop apologizing mid-argument. No "I am sorry".
3. When opposing counsel makes a claim you disagree with, do NOT say they are
   "wrong" or "made a mistake". Find a respectful formulation.
4. Abbreviations: ALWAYS introduce the full form first time.
5. The roadmap at the start must be crisp — max 30 seconds.
6. Remember to reserve time for rebuttal in your opening statement.
"""
with open(os.path.join(workspace, "moot_prep/team_notes/coach_memo.txt"), "w") as f:
    f.write(memo)

# ── Distractor 9: Competitor analysis ────────────────────────────────────────
comp_analysis = """\
COMPETITOR ANALYSIS — TEAM EPSILON (Practice Opponent)
=======================================================
Strengths: Very polished delivery, good eye contact, no filler words.
Weaknesses: Weak on Art. 67 CISG analysis; relied heavily on one case.
Their strategy: Attacked jurisdiction first, then tried to flip on conformity.
Our performance: Good jurisdiction argument. Conformity needs more structure.
Roadmap was unclear — judges asked twice to repeat the issues.
"""
with open(os.path.join(workspace, "moot_prep/opponent_analysis/team_epsilon_notes.txt"), "w") as f:
    f.write(comp_analysis)

# ── Distractor 10: Draft timeline ────────────────────────────────────────────
timeline = """\
ARGUMENT TIMELINE PLAN (rough)
================================
Min 0-1   : Opening, self-introduction, roadmap
Min 1-7   : Issue 1 — Jurisdiction (competence-competence)
Min 7-14  : Issue 2 — Conformity (Art. 35 & 67 CISG)
Min 14-19 : Issue 3 — Remedies / Counterclaim
Min 19    : Conclude + reserve rebuttal time
(Total: 20 min, reserve 1 min rebuttal)

Co-counsel split: Speaker 1 = Issues 1 & 2; Speaker 2 = Issue 3
"""
with open(os.path.join(workspace, "moot_prep/background/argument_timeline.txt"), "w") as f:
    f.write(timeline)

# ── Distractor 11: Blank template placeholder (wrong format) ─────────────────
bad_template = """\
TEMPLATE (NOT FILLED IN)
=========================
[OPENING]: ...
[ISSUE 1]: ...
[ISSUE 2]: ...
[ISSUE 3]: ...
[CLOSE]: ...

This is just a skeleton. Do not use as final output.
"""
with open(os.path.join(workspace, "moot_prep/drafts/template_skeleton.txt"), "w") as f:
    f.write(bad_template)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    for fname in files:
        print(" ", os.path.join(root, fname))