import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ── directory structure ────────────────────────────────────────────────────────
dirs = [
    "templates",
    "candidates/quantum_hoe_2024",
    "candidates/rejected",
    "company/strategy",
    "company/engineering",
    "hiring/past_rounds",
    "hiring/scorecards_archive",
    "hr/policies",
    "hr/compensation",
    "tools",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── SKILL.md ───────────────────────────────────────────────────────────────────
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
(WORKSPACE / "SKILL.md").write_text(skill_md)

# ── templates/interview_guide_template.md ─────────────────────────────────────
template = """\
# Interview Guide: {{role_title}}

**Candidate**: {{candidate_name}}
**Date Prepared**: {{date}}
**Prepared By**: Interview Designer (Evidence-Based Methodology)

---

## Section 1: Scorecard
> *(Defined BEFORE reviewing resume — sets the A-Player standard)*

### Mission
{{mission}}

### 12-Month Outcomes
{{outcomes}}

### Required Competencies
{{competencies}}

---

## Section 2: Forensic Resume Analysis

### [Green Signals] — Highlight Verification
{{green_signals}}

### [Red Flags] — Gaps & Concerns
{{red_flags}}

---

## Section 3: Interview Question Bank

### Pressure Test Scripts (Past Behavior)
> *Forensic STAR follow-ups targeting identified concerns*

{{pressure_test_questions}}

### Future Simulation
> *Specific Performance Problem tied to company context*

{{future_simulation}}

---

## Section 4: Evaluation Summary

### Overall Assessment
{{overall_assessment}}

### Recommended Next Steps
{{next_steps}}
"""
(WORKSPACE / "templates" / "interview_guide_template.md").write_text(template)

# ── JD: Head of Engineering at QuantumLeap Labs ────────────────────────────────
jd = """\
POSITION: Head of Engineering
COMPANY: QuantumLeap Labs
LOCATION: San Francisco, CA (Hybrid)

ABOUT QUANTUMLEAP LABS:
QuantumLeap Labs is a Series B quantum computing startup (47 employees, $28M raised) building
the world's first fault-tolerant logical qubit platform for pharmaceutical drug discovery.
We are 18 months from our first commercial deployment with Roche and need a Head of Engineering
who can scale our 12-person engineering team to 35 while maintaining our 99.7% uptime SLA on
our hybrid quantum-classical simulation clusters.

ROLE MANDATE:
The Head of Engineering will own the full engineering organization: quantum hardware integration,
classical compute infrastructure, and the software SDK layer consumed by external pharma partners.
This is not a "VP of Engineering" title role — it is a hands-on, board-accountable position
reporting directly to the CEO. The first 12 months will be defined by three non-negotiable
deliverables:

1. Ship QuantumLeap OS v2.0 (our proprietary qubit orchestration layer) by Q3 2025,
   enabling 1000-qubit logical circuits for Roche's protein folding pipeline.
2. Hire and onboard 23 additional engineers (targeting 8 QEC specialists, 10 software,
   5 infrastructure) without degrading current team velocity or culture.
3. Establish a hardware-software co-design process that reduces qubit error correction
   overhead by 40% compared to our current surface code implementation.

MUST-HAVE TECHNICAL DEPTH:
- Direct experience shipping quantum error correction (QEC) systems, OR
  provable track record scaling deeply technical infrastructure teams (ML systems, compilers)
- Understands the trade-off space between logical qubit fidelity and gate speed
- Has personally debugged production incidents at the hardware-software boundary

COMPENSATION: $280k–$340k base + equity (0.3%–0.6% fully diluted)
"""
(WORKSPACE / "candidates" / "quantum_hoe_2024" / "job_description.txt").write_text(jd)

# ── Candidate Resume: Dr. Priya Venkataraman ───────────────────────────────────
resume = """\
DR. PRIYA VENKATARAMAN
priya.v@email.com | linkedin.com/in/priyav | San Francisco, CA

SUMMARY
Quantum computing leader with 12+ years experience spanning academia and industry.
Led quantum algorithm teams at Google Quantum AI and IBM Research. Published 23
peer-reviewed papers on quantum error correction. Passionate about bridging theory
and commercial applications.

EXPERIENCE

GOOGLE QUANTUM AI, Mountain View, CA                               2019 – 2024
Senior Staff Research Engineer → Principal Engineer

• Led the "Willow chip" error correction validation team (team of 14 researchers + 6 engineers)
• Achieved "beyond breakeven" QEC milestone (published in Nature, Dec 2024)
• Drove cross-functional alignment between hardware, software, and research orgs (200+ stakeholders)
• Managed $18M annual research budget across 3 concurrent projects
• Reduced qubit calibration time by 67% through ML-assisted parameter optimization (patent pending)

IBM RESEARCH, Yorktown Heights, NY                                 2016 – 2019
Research Scientist II

• Contributed to Qiskit open-source framework (quantum SDK) — 2.3M+ GitHub stars
• Designed quantum volume benchmarking protocols adopted as IBM standard
• Co-authored IBM Quantum Network partnership framework (12 enterprise clients)

STANFORD UNIVERSITY, Stanford, CA                                  2011 – 2016
Ph.D. Candidate → Postdoctoral Researcher (Quantum Information Science)

• Dissertation: "Threshold Theorems for Topological Quantum Error Correction"
• Developed novel flag fault-tolerance protocols (cited 340+ times)
• Teaching Assistant for CS359Q (Quantum Computing, Prof. Aaronson)

EDUCATION
Ph.D., Quantum Information Science — Stanford University (2016)
B.Tech., Computer Science & Engineering — IIT Bombay (2011), Gold Medalist

PUBLICATIONS (selected)
• "Quantum error correction below the surface code threshold" — Nature (2024), co-first author
• "Scalable flag fault-tolerance for arbitrary Clifford circuits" — PRL (2021)
• 21 additional publications, Google Scholar h-index: 31

TECHNICAL SKILLS
Quantum: Surface codes, flag fault-tolerance, quantum volume, randomized benchmarking,
         Qiskit, Cirq, PennyLane
Classical: Python, C++, CUDA, Kubernetes, AWS/GCP
Leadership: OKRs, Agile, technical roadmapping, board presentations

NOTABLE
• MIT Technology Review "35 Innovators Under 35" (2022)
• Invited speaker: QIP 2023, IEEE Quantum Week 2022, Davos (World Economic Forum, 2024)
"""
(WORKSPACE / "candidates" / "quantum_hoe_2024" / "resume_priya_venkataraman.txt").write_text(resume)

# ── distractor files ───────────────────────────────────────────────────────────
distractors = {
    "hiring/past_rounds/head_of_sales_2023_notes.txt": """\
Interview notes from Head of Sales search, Q4 2023.
Final candidate: Marcus Tran. Passed technical screen. Cultural fit TBD.
Offer extended at $220k base. Rejected — went to competitor.
""",
    "hiring/scorecards_archive/head_of_sales_scorecard_2023.txt": """\
SCORECARD: Head of Sales 2023
Mission: Own $10M ARR target in Year 1.
Outcomes: Close 3 enterprise deals >$500k, build outbound motion, hire 4 AEs.
Competencies: Enterprise SaaS sales, CRM hygiene, quota attainment history.
""",
    "company/strategy/2024_roadmap_confidential.txt": """\
QUANTUMLEAP LABS — CONFIDENTIAL STRATEGY 2024-2026

Phase 1 (2024): Stabilize Willow-class qubit integration. Ship SDK v1.8.
Phase 2 (2025): QuantumLeap OS v2.0 launch. Roche contract go-live.
Phase 3 (2026): Series C fundraise, target 200-qubit logical circuits at scale.

Key risk: Engineering talent pipeline. Critical hire: Head of Engineering by Q1 2025.
""",
    "company/engineering/current_team_org.txt": """\
Engineering Team — QuantumLeap Labs (Dec 2024)

CTO: Dr. Yuki Tanaka (reports to CEO)
  - Quantum Hardware: 4 engineers (2 PhD, 2 MS)
  - Quantum Software: 5 engineers
  - Infrastructure/DevOps: 3 engineers

Head of Engineering role: Peer to CTO, owns execution while CTO owns research direction.
NOTE: CTO has veto on technical architecture decisions.
""",
    "company/engineering/qubit_error_budget_q3.txt": """\
Q3 2024 Error Budget Report
Surface code cycle: 1.1µs
Physical error rate: 0.28% (target: <0.1% for v2.0)
Logical error rate: 1.2e-4 per cycle
QEC overhead ratio: 847 physical qubits per logical qubit (target: <500 for v2.0)
Calibration drift incidents: 7 (3 customer-impacting)
""",
    "candidates/rejected/alex_morrison_resume.txt": """\
ALEX MORRISON
Former Engineering Director at Rigetti Computing.
Left after Rigetti's SPAC collapsed. Strong classical infra background but
limited QEC depth. Rejected at technical screen — could not explain threshold theorem.
""",
    "hr/policies/interview_process_sop.txt": """\
HR INTERVIEW PROCESS SOP v3.2

Standard pipeline for IC roles: Phone screen → Technical → Loop (4 interviews) → Debrief
Standard pipeline for Director+: Phone screen → Case study → Executive panel → Reference checks → Offer

NOTE: All structured interview guides must be filed in /hiring/active/ before first interview.
Reference check template: hr/templates/ref_check_template.txt (must contact min 3 references)
""",
    "hr/compensation/leveling_guide_2024.txt": """\
QuantumLeap Labs — Compensation Leveling Guide 2024
L7 Staff Engineer: $200k–$240k + 0.05%–0.1% equity
L8 Principal Engineer: $240k–$280k + 0.1%–0.2% equity
L9 Head of Engineering: $280k–$340k + 0.3%–0.6% equity
L10 VP Engineering: $320k–$380k + 0.5%–1.0% equity
""",
    "tools/bias_checklist_legacy.txt": """\
LEGACY BIAS CHECKLIST (deprecated — see new interview designer skill)
[ ] Did you form an opinion in first 5 minutes?
[ ] Are you hiring in your own image?
[ ] Have you checked for halo effect from brand-name employer?
[ ] Did you verify claims independently?
""",
    "hiring/past_rounds/cto_search_2022_debrief.txt": """\
CTO Search 2022 — Post-Mortem Debrief
Hired: Dr. Yuki Tanaka from QuEra Computing.
Process worked well. Key lesson: candidates from large labs (Google, IBM)
often struggle with resource scarcity. Must test for scrappiness explicitly.
Recommend adding "startup constraint simulation" to future senior engineering interviews.
""",
    "candidates/quantum_hoe_2024/scheduling_notes.txt": """\
SCHEDULING NOTES — Priya Venkataraman
Availability: Jan 13-17, 2025
Preferred format: Video call (Zoom)
Travel: Can fly in for final panel, needs 2-week notice
Recruiter contact: talent@quantumleaplabs.com
NOTE: Candidate is actively interviewing at IonQ and PsiQuantum. Decision timeline: ~3 weeks.
""",
}
for path, content in distractors.items():
    full_path = WORKSPACE / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")