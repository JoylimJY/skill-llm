import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Create deeply nested distractor directory structure ---
dirs = [
    "hr/archive/2022/q1",
    "hr/archive/2022/q2",
    "hr/archive/2023/q3",
    "hr/archive/2023/q4",
    "hr/templates/internal",
    "hr/templates/external",
    "recruiting/pipeline/biotech",
    "recruiting/pipeline/pharma",
    "recruiting/pipeline/rejected",
    "recruiting/jd_drafts",
    "admin/contracts",
    "admin/onboarding",
    "finance/headcount",
    "legal/nda",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "hr/archive/2022/q1/old_scorecard_template_v1.txt": """\
LEGACY SCORECARD (DEPRECATED - DO NOT USE)
Candidate: 
Role:
Skills: /10
Experience: /10
Total: /20
""",
    "hr/archive/2022/q2/batch_review_notes.txt": """\
Q2 2022 batch - 5 candidates screened for lab tech roles.
None proceeded past phone screen.
""",
    "hr/archive/2023/q3/hiring_freeze_memo.txt": """\
TO: All HR Staff
Hiring freeze effective Sept 1 2023 through Dec 31 2023.
No new scorecards to be generated during this period.
""",
    "hr/templates/internal/offer_letter_template.docx.txt": """\
[OFFER LETTER TEMPLATE - INTERNAL USE]
Dear [NAME],
We are pleased to extend this offer...
Base Salary: [AMOUNT]
Start Date: [DATE]
""",
    "hr/templates/external/job_posting_reg_affairs.txt": """\
HEAD OF REGULATORY AFFAIRS - JOB POSTING DRAFT
Company: Verdant Biopharma (Series B)
Location: Remote / Boston, MA
Requirements:
- 10+ years regulatory submissions (FDA, EMA)
- Experience with IND, NDA, BLA filings
- Strong leadership and cross-functional communication
- RAC certification preferred
""",
    "recruiting/pipeline/biotech/candidates_shortlist.txt": """\
SHORTLIST - HEAD OF REGULATORY AFFAIRS
Candidates advancing to final round:
1. Miriam Osei-Bonsu
2. Tariq Abubakar-Hassan
3. Svetlana Volkov-Petrov

Interview panel: Dr. Chen (CSO), Rachel Kim (CPO), Marcus Webb (CEO)
Interview dates: 2024-06-10 through 2024-06-12
""",
    "recruiting/pipeline/biotech/scheduling_notes.txt": """\
Interview logistics:
- Miriam: June 10, 2pm EST - virtual
- Tariq: June 11, 10am EST - onsite
- Svetlana: June 12, 3pm EST - virtual
Panel agreed: scorecards due EOD June 14.
""",
    "recruiting/pipeline/pharma/withdrawn_candidates.txt": """\
Withdrawn before final round:
- Candidate A (offer from Pfizer)
- Candidate B (salary mismatch)
""",
    "recruiting/pipeline/rejected/rejection_log_2024.txt": """\
2024 Rejection Log - Regulatory Affairs Pipeline
ID001 - Phone screen fail
ID002 - Technical interview fail
ID003 - Withdrew
ID004 - Background check issue
""",
    "recruiting/jd_drafts/reg_affairs_v3_feedback.txt": """\
JD FEEDBACK from Marcus (CEO):
- Add 'Series B/C experience' requirement
- Emphasize FDA PDUFA timelines knowledge
- Remove 'PhD required' - make it preferred
""",
    "admin/contracts/contractor_nda_template.txt": """\
NON-DISCLOSURE AGREEMENT
This NDA is entered into between Verdant Biopharma and [CONTRACTOR]...
""",
    "admin/onboarding/checklist_senior_roles.txt": """\
Senior Role Onboarding Checklist:
[ ] Background check cleared
[ ] IT equipment ordered
[ ] Benefits enrollment within 30 days
[ ] 90-day review scheduled
""",
    "finance/headcount/q2_2024_headcount_plan.txt": """\
Q2 2024 Headcount Plan
Open Reqs:
- Head of Regulatory Affairs (Priority: HIGH)
- Sr. CMC Scientist (Priority: MEDIUM)
- Clinical Data Manager (Priority: LOW)
Budget approved for 2 hires.
""",
    "legal/nda/candidate_nda_log.txt": """\
Candidate NDA Execution Log:
Miriam Osei-Bonsu - signed 2024-05-28
Tariq Abubakar-Hassan - signed 2024-05-30
Svetlana Volkov-Petrov - signed 2024-06-01
""",
}

for path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE PROBLEM: Raw, messy interview notes for 3 candidates ---
# These are intentionally messy, with scores buried in prose, inconsistent formatting,
# using the criterion names but not in the standard order, with interviewer opinions mixed in.

interview_notes = {
    "recruiting/pipeline/biotech/interview_notes_miriam.txt": """\
INTERVIEW NOTES - MIRIAM OSEI-BONSU
Role: Head of Regulatory Affairs
Date: June 10, 2024
Interviewers: Dr. Chen, Rachel Kim, Marcus Webb

PANEL DISCUSSION AFTER INTERVIEW:

Technical / Regulatory Knowledge:
Dr. Chen: Miriam absolutely nailed the CMC submission deep-dive. She described the eCTD
structure for a BLA almost perfectly. Knows FDA 21 CFR Part 314 cold. I'd give her a 5 
for technical skills — she's genuinely exceptional, top 5% we've seen.

Work History & Background:
Rachel: 14 years at large pharma (Genentech, then Amgen). Led three successful NDA filings.
However, she's never worked at a startup, which gives me pause about velocity expectations.
I'll score her experience a 4 — clearly above average even with the startup gap.

Team & Culture:
Marcus: She seems process-driven to a fault. During the culture conversation she kept 
referencing 'established SOPs' rather than talking about building them from scratch.
For a Series B that's a real concern. Culture fit: 2 — she has notable gaps for our stage.

Communication Skills:
Rachel: Her written exercise was excellent. Verbal communication was polished, maybe a 
little rehearsed. I'd say 4 on communication.

Problem Solving:
Dr. Chen: The case study she was given involved a partial clinical hold scenario. She 
identified the root cause quickly but took a very conservative, slow path. Appropriate for 
big pharma, risky for us. Problem solving score: 3. Meets the bar.

Long-term Potential:
Marcus: At 51 and coming from big pharma, I'm not sure she's looking to grow into a 
C-suite role. Short runway for us. Growth potential: 2.

OVERALL RECOMMENDATION FROM PANEL: MAYBE — strong regulatory chops, cultural risk is real.
""",

    "recruiting/pipeline/biotech/interview_notes_tariq.txt": """\
INTERVIEW NOTES - TARIQ ABUBAKAR-HASSAN
Role: Head of Regulatory Affairs  
Date: June 11, 2024
Interviewers: Dr. Chen, Rachel Kim, Marcus Webb

NOTE: Tariq came in onsite. Energy in the room was very different — much more dynamic.

After debrief:

On technical regulatory expertise:
Tariq's background is primarily EU/EMA — he built the regulatory function at a UK biotech
from scratch. His FDA knowledge is theoretical, not hands-on. Dr. Chen scores him 3 on 
technical skills — he meets the bar but there's a real gap on US submissions.

Relevant Experience:
This is where Tariq shines. He was Head of Regulatory at a Series A → C journey, so he 
knows exactly what we're going through. Rachel: strong 5 here — exceptional fit for our 
stage. He's seen it all at this scale.

Culture / Startup Fit:
Marcus loved him. "He gets it" was Marcus's exact quote. Tariq talked about shipping first,
iterating on process, and moving fast before FDA interaction. Culture fit score: 5. Exceptional.

Communication:
His presentation was energetic but slightly disorganized. Written exercise had a few errors.
Panel consensus: 3 for communication — meets bar.

Problem Solving:
The partial clinical hold case study — Tariq immediately proposed a creative path: pre-submission
meeting with FDA to negotiate scope. Unconventional but smart. Score: 4. Clearly above average.

Growth Potential:
He's 38, ambitious, mentioned he wants to become a Chief Regulatory Officer at a public 
biotech. Panel thinks he could grow into a broader R&D leadership role here. Score: 5. Exceptional.

Panel Recommendation: HIRE — the cultural and growth upside outweighs the FDA experience gap.
""",

    "recruiting/pipeline/biotech/interview_notes_svetlana.txt": """\
INTERVIEW NOTES - SVETLANA VOLKOV-PETROV
Role: Head of Regulatory Affairs
Date: June 12, 2024
Panel: Dr. Chen, Rachel Kim, Marcus Webb

Background: PhD in Biochemistry, previously VP Regulatory at mid-size biotech (Series D),
also spent 5 years at FDA CDER as a reviewer — an unusual and valuable background.

Post-interview panel notes:

TECHNICAL SKILLS: Dr. Chen: Svetlana having been a reviewer at FDA gives her an
almost unfair advantage. She thinks like a regulator. Score = 5. Top 5% without question.

EXPERIENCE (Relevant): Rachel: The combination of FDA + VP-level biotech = extremely 
relevant. But her most recent role was 3 years ago (she took a career break). Slight
concern. Score: 4 (strong, above average — the break is minor given the depth).

CULTURE FIT: This is complicated. She was very formal, almost guarded. Didn't connect
well with Marcus's questions about startup agility. But she's self-aware about it and
actually said "I know I need to shift gears from FDA culture." Panel was split.
Rachel gives her a 3, Dr. Chen gives 2, Marcus gives 2. Let's go with 2 — below bar.

COMMUNICATION: Her written submission was flawless. Verbal was clear, precise, a bit 
clinical. Score: 4.

PROBLEM SOLVING: The clinical hold scenario — she essentially recited the exact FDA 
response playbook. Technically perfect, no creative thinking. Score: 3.

GROWTH POTENTIAL: She's 44, seems more interested in depth than breadth. Not a future
CRO candidate in Marcus's view. Score: 3 — meets bar.

PANEL RECOMMENDATION: MAYBE — exceptional regulatory brain, cultural fit is the blocker.
""",
}

for path, content in interview_notes.items():
    full_path = os.path.join(WORKSPACE, path)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}")