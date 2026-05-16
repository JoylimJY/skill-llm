import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "candidates/active",
    "candidates/archived",
    "templates",
    "hiring/vp_computational_biology",
    "hiring/senior_scientist",
    "hiring/archived_2022",
    "hr/policies",
    "hr/scorecards_old",
    "skills",
    "meeting_notes",
    "org_charts",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = """\
---
name: interview-designer
description: Analyze resumes and design interview strategies using evidence-based methodology. Transforms interview prep from "read resume → ask questions" into "define standard → forensic evidence → future simulation". Combines Geoff Smart's Topgrading, Lou Adler's performance-based hiring, and Daniel Kahneman's bias control. Use when preparing for interviews, creating structured interview guides, or designing questions to validate candidate competencies.
---

# Interview Designer Skill

> **Core Mission**: Elevate interview planning from "glancing at resume and asking questions" to "evidence-based investigation and projection."
> **Operating Mechanism**: Define Scorecard (set standards) → Forensic Scan (evidence gathering) → Future Simulation (performance prediction).
> **Prompt Strategy**: This skill uses <Chain of Thought>. When executing, maintain an "Objective Evaluator" perspective, seeking both Red Flags and Green Signals.

## 1. Dynamic War Room (Expert Panel)

Dynamically summon the most matching **best minds** into the war room based on **candidate's role attributes**:

*   **Geoff Smart (Who)**: Responsible for **Define & Verify**.
    *   *Principle*: Scorecard First. Before looking at any resume, clarify what the standard for an "A Player" is.
*   **Lou Adler (Performance-based)**: Responsible for **Predict**.
    *   *Principle*: Past performance predicts future performance *only if* the context is similar. Must design simulations for future scenarios.
*   **Daniel Kahneman (Bias Control)**: Responsible for **De-bias**.
    *   *Principle*: Beware of "confirmation bias." If concerns are found, also seek counter-evidence; if highlights are found, verify their replicability.
*   **Domain Expert**: Responsible for **Depth**.

## 2. Core Execution Workflow

### Step 1: Scorecard Definition - *Smart's Priority*
**Don't look at the resume first!** Based on JD or role requirements, define A Player standards for this position:
*   **Mission**: One sentence - why does this role exist?
*   **Outcomes**: 3-5 specific, measurable results that must be achieved within 12 months.
*   **Competencies**: Hard/soft skills required to achieve the above outcomes.

### Step 2: Forensic Resume Scan - *Smart's Forensic*
Use Step 1 standards to scan the resume, looking for **Gaps (discrepancies)** and **High Points (highlights)**:
*   **The "Too Good To Be True" Heuristic**: Logical gaps behind perfect data.
*   **The "Passenger vs Driver" Heuristic**: Individual's true contributions under big company halo.
*   **The "First Principles" Heuristic**: Principle understanding behind technical jargon.

### Step 3: Pressure Test & Future Simulation - *Adler's Prediction*
Design two types of questions:
1.  **Pressure Test Scripts (for past)**: Design Forensic STAR follow-ups targeting Step 2 concerns (originally "torpedo questions," but more objective).
2.  **Future Simulation (for future)**: Design a specific Performance Problem.
    *   *Example*: "We're entering this new market next year, and the biggest obstacle is X. If you join, how would you analyze this problem in your first week?"

## 3. Question Design Principles

1.  **Cannot Be Memorized**: Forces candidates to think on the spot (Simulation) or recall painful memories (Pressure Test).
2.  **Forced Trade-offs**: Choose between two "correct" options to test values.
3.  **Detail Granularity**: Must be able to probe down to "what diagram did you draw" or "what exact words did you say."

## 4. Output Format

Directly call `templates/interview_guide_template.md` to generate the report.
**Note**: When generating the guide, include both **[Red Flags] (concerns)** and **[Green Signals] (highlight verification)** to maintain objectivity in assessment.
"""
(workspace / "skills" / "SKILL.md").write_text(skill_md)

# ── interview_guide_template.md ───────────────────────────────────────────────
template_md = """\
# Interview Guide: [CANDIDATE_NAME] — [ROLE_TITLE]

**Prepared by:** Interview Design System  
**Date:** [DATE]  
**Interviewer(s):** [INTERVIEWER_NAMES]

---

## PART 1: SCORECARD (Define the Standard First)

### Mission
> [One sentence: why does this role exist?]

### Outcomes (12-Month Measurable Results)
| # | Outcome | Success Metric |
|---|---------|---------------|
| 1 | [Outcome] | [Metric] |
| 2 | [Outcome] | [Metric] |
| 3 | [Outcome] | [Metric] |

### Required Competencies
**Hard Skills:**
- [Skill 1]

**Soft Skills:**
- [Skill 1]

---

## PART 2: FORENSIC RESUME SCAN

### [Red Flags] — Gaps & Concerns
| Heuristic Applied | Observation | Risk Level |
|-------------------|-------------|------------|
| [Heuristic Name]  | [Detail]    | High/Med/Low |

### [Green Signals] — Highlights & Verification Targets
| Heuristic Applied | Observation | Verification Priority |
|-------------------|-------------|----------------------|
| [Heuristic Name]  | [Detail]    | High/Med/Low         |

---

## PART 3: QUESTION BANK

### Section A: Pressure Test Scripts (Forensic STAR — Past Behavior)
> Target: Address concerns identified in Part 2 Red Flags

**Q1 — [Topic]:**  
[Question text]  
*Follow-up probes:*  
- [Probe 1]  
- [Probe 2]  

### Section B: Future Simulation (Performance Problem)
> Target: Predict on-the-job performance in our specific context

**Scenario:**  
[Describe the specific business obstacle/context]

**The Challenge Put to Candidate:**  
[Exact question text]

*Evaluation Criteria:*  
- [Criterion 1]  
- [Criterion 2]  

### Section C: Green Signal Verification (Highlight Validation)
> Target: Verify and stress-test the highlights from Part 2

**Q1 — [Topic]:**  
[Question text]

---

## PART 4: SCORING RUBRIC

| Competency | 1 (No Evidence) | 3 (Meets Bar) | 5 (A Player) |
|-----------|----------------|---------------|--------------|
| [Competency 1] | ... | ... | ... |

---

*Generated using Interview Designer Skill — Topgrading + Performance-Based Hiring + Bias Control*
"""
(workspace / "templates" / "interview_guide_template.md").write_text(template_md)

# ── JOB DESCRIPTION ──────────────────────────────────────────────────────────
jd = """\
POSITION: Vice President, Computational Biology
COMPANY: NovaTerra Therapeutics (Series C, ~180 employees)
LOCATION: Cambridge, MA (Hybrid)
REPORTS TO: Chief Scientific Officer

ABOUT THE ROLE:
NovaTerra is building an AI-driven small-molecule drug discovery engine targeting
RNA secondary structure dysregulation in oncology. We have 3 preclinical programs
and are planning our first IND filing (target: Q3 next year). The VP of
Computational Biology will own our in silico platform strategy and must translate
computational insights into actionable chemistry decisions within 18 months.

KEY RESPONSIBILITIES:
- Architect and lead a team of 8 computational scientists across ML, cheminformatics,
  and structural biology
- Own the RNA-targeting virtual screening pipeline from hit identification through
  ADMET triage
- Establish a cross-functional collaboration framework with medicinal chemistry,
  biology, and clinical teams
- Drive vendor selection for HPC/cloud infrastructure to support 10x throughput
  scaling by Q4
- Present program updates to the Board and external investors quarterly

MINIMUM REQUIREMENTS:
- PhD in computational biology, bioinformatics, cheminformatics, or closely related
- 10+ years post-PhD experience; at least 3 years in a leadership role
- Track record of at least one program advanced to IND or beyond under direct
  computational leadership
- Expert in structure-based drug design (SBDD) and free energy perturbation (FEP)
- Strong publication record in high-impact journals

PREFERRED:
- Experience with RNA-targeted therapeutics or non-traditional target classes
- Familiarity with GCP/AWS for large-scale ML workflows
- Prior experience presenting to a Board of Directors
"""
(workspace / "hiring" / "vp_computational_biology" / "job_description.md").write_text(jd)

# ── CANDIDATE RESUME (deliberately messy / ambiguous) ────────────────────────
resume = """\
DR. WEI CHEN, Ph.D.
Cambridge, MA | wei.chen@email.com | LinkedIn: linkedin.com/in/weichen-compbio

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROFESSIONAL SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Visionary computational biology leader with 15+ years transforming drug discovery
through AI/ML innovation. Proven ability to build world-class teams and deliver
breakthrough results at the intersection of biology and technology.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXPERIENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Senior Director, Computational Sciences
Pfizer Global R&D | Cambridge, MA                           2018 – Present

• Led computational strategy for oncology portfolio (small molecules + RNA-targeted)
• Our team's AI-driven screening identified 3 clinical candidates; one advanced to
  Phase I trials in 2023
• Managed department of 22 scientists across 4 locations globally
• Implemented FEP+ workflows that reduced lead optimization cycle time by 40%
• Drove cloud migration of HPC workloads to AWS (saved ~$4M annually)
• Co-inventor on 7 patents; 14 publications (Nature Methods, JCTC, JCIM)

─────────────────────────────────────────────────────────────────
Director, Computational Chemistry
Novartis Institutes for BioMedical Research | Basel, Switzerland   2013 – 2018

• Built CADD group from scratch (0 → 15 scientists) supporting 12 active programs
• Contributed to structure-based hit identification campaigns for 3 kinase programs
• Introduced machine learning for ADMET prediction; model achieved AUC 0.91 on
  internal test set
• Presented results at ACS, ISMB, and Gordon Research Conferences

─────────────────────────────────────────────────────────────────
Postdoctoral Fellow
Broad Institute of MIT and Harvard | Cambridge, MA          2010 – 2013

• Developed novel graph neural network architectures for protein-ligand binding
  affinity prediction (published Nature Methods 2013, cited 800+)
• Collaborated with 5 labs across Broad; project involved 12 co-authors

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EDUCATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ph.D., Computational Biophysics — MIT (2010)
B.S., Applied Mathematics — Peking University (2004)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TECHNICAL SKILLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Molecular Dynamics: GROMACS, AMBER, Desmond
Docking/SBDD: Glide, AutoDock Vina, ICM
ML/AI: PyTorch, TensorFlow, scikit-learn, Graph Neural Networks
Cheminformatics: RDKit, OpenEye toolkits
Cloud: AWS (EC2, S3, Batch), Kubernetes
Programming: Python (expert), C++, R, bash

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SELECTED PUBLICATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Chen W. et al. "Graph-based deep learning for protein-ligand affinity prediction"
  Nature Methods, 2013.
Chen W., Zhao L. et al. "FEP-guided lead optimization in Bcl-2 oncology program"
  J. Chem. Theory Comput., 2021.
[+12 additional publications]
"""
(workspace / "candidates" / "active" / "wei_chen_resume.md").write_text(resume)

# ── DISTRACTOR FILES ──────────────────────────────────────────────────────────

# 1. Old scorecard (wrong format, different role)
(workspace / "hr" / "scorecards_old" / "scorecard_2022_cmo.md").write_text("""\
# Scorecard - Chief Medical Officer (2022)
Mission: Lead clinical development...
Outcomes: File 2 NDAs by 2024 | Build Phase III infrastructure...
[ARCHIVED - DO NOT USE]
""")

# 2. Meeting notes
(workspace / "meeting_notes" / "hiring_committee_2024-11-03.md").write_text("""\
# Hiring Committee Notes — VP Comp Bio Search
Present: Sarah K. (CSO), Marcus T. (CEO), Priya N. (HR)
- Wei Chen interview scheduled for Dec 5
- Also interviewing Dr. Anika Patel and Dr. James Liu
- Concern raised: does Chen have direct RNA experience or is it secondhand?
- Action: Prepare structured interview approach
""")

# 3. Generic interview question bank (distractor)
(workspace / "hr" / "generic_interview_questions.md").write_text("""\
# Generic Interview Questions (HR Template)
1. Tell me about yourself.
2. Where do you see yourself in 5 years?
3. What are your strengths and weaknesses?
4. Why do you want to work here?
[NOT ROLE-SPECIFIC - general HR use only]
""")

# 4. Org chart
(workspace / "org_charts" / "novattera_org_v3.md").write_text("""\
# NovaTerra Therapeutics Org Chart (v3, Oct 2024)
CEO: Marcus Thornton
  CSO: Sarah Kim
    VP Computational Biology: [OPEN]
    VP Biology: Dr. Raj Patel
    VP Chemistry: Dr. Helena Cruz
  CFO: David Lee
  CMO: [search ongoing]
""")

# 5. Archived candidate (different role)
(workspace / "candidates" / "archived" / "patel_anika_2023.md").write_text("""\
# Dr. Anika Patel — Archived Application
Role Applied: Senior Scientist, Structural Biology (2023)
Status: Offer declined
Notes: Strong CRYO-EM background, left for academia
""")

# 6. Vendor evaluation (distractor)
(workspace / "hiring" / "vp_computational_biology" / "cloud_vendor_notes.md").write_text("""\
# Cloud HPC Vendor Shortlist
- AWS: $2.1M/yr estimate, strong Batch integration
- Azure: $1.9M/yr, good for Windows-based legacy tools
- GCP: $2.3M/yr, Vertex AI attractive for ML workloads
Decision needed by VP Comp Bio hire.
""")

# 7. Old interview guide (incomplete/wrong format — distractor)
(workspace / "hiring" / "archived_2022" / "interview_guide_old_format.md").write_text("""\
# Interview Notes - Candidate X (2022)
Q: Tell me about your biggest accomplishment.
Q: Can you code in Python?
Q: Do you have leadership experience?
[INFORMAL - NOT STRUCTURED]
""")

# 8. Salary benchmarking
(workspace / "hr" / "policies" / "salary_bands_2024.md").write_text("""\
# Salary Bands FY2024
VP Level: $240,000 - $320,000 base + equity
Senior Director: $185,000 - $230,000 base
Director: $155,000 - $190,000 base
[CONFIDENTIAL]
""")

# 9. Another candidate resume (irrelevant)
(workspace / "candidates" / "active" / "liu_james_resume.md").write_text("""\
# Dr. James Liu — VP Computational Biology Candidate
Background: 12 years in structural biology, Genentech then Relay Therapeutics
Note: Specializes in cryo-EM, limited CADD/FEP experience
Status: First-round phone screen completed; marginal fit on computational depth
""")

# 10. README-like but actually a process doc for HR (not helpful for the task)
(workspace / "hr" / "policies" / "hiring_process_overview.md").write_text("""\
# NovaTerra Hiring Process (Standard)
1. HR screens applications
2. Hiring manager phone screen (30 min)
3. Technical interview (60 min)
4. Panel interview (90 min)
5. Reference checks
6. Offer extended
Note: All senior hires (Director+) require CSO approval.
""")

# 11. Partial FEP technical note (domain depth distractor)
(workspace / "hiring" / "vp_computational_biology" / "technical_context_note.md").write_text("""\
# Technical Context for VP Comp Bio Interview Panel
Our RNA-targeting platform:
- Uses SHAPE-MaP data to define secondary structure ensembles
- Virtual screening against RNA pockets using rDock and GNINA
- FEP calculations run on Schrodinger suite (Desmond backend)
- Key bottleneck: RNA conformational sampling at therapeutic temperatures

FEP note: Our medicinal chemistry team uses relative binding free energy (RBFE)
for SAR. The VP will need to critically evaluate these numbers, not just delegate.
- Current throughput: ~50 FEP perturbations/week
- Target: 500/week by Q4 (requires HPC redesign)
""")

# 12. Skills directory placeholder (not the actual SKILL.md location hint)
(workspace / "skills" / "README_skills.md").write_text("""\
# Skills Directory
This directory contains agent skill definitions.
Active skills: interview-designer, report-writer, literature-summarizer
""")

print("Workspace initialized successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")