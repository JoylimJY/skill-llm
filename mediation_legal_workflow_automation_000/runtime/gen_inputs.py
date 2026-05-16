import os
import random
import stat

random.seed(42)

workspace = "/workspace"

# --- Create realistic distractor directory structure ---
dirs = [
    "legal/contracts/leases",
    "legal/contracts/amendments",
    "legal/disputes/2023",
    "legal/disputes/2024",
    "legal/correspondence/opposing_counsel",
    "legal/correspondence/internal",
    "hr/policies",
    "hr/records",
    "finance/invoices/q1",
    "finance/invoices/q2",
    "finance/reports",
    "operations/facilities",
    "operations/maintenance_logs",
    "scripts",
    "config",
    "tmp/scratch",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "legal/contracts/leases/lease_agreement_unit_4B.txt": """COMMERCIAL LEASE AGREEMENT
Tenant: Pinnacle Retail Group LLC
Landlord: Westfield Properties Inc.
Term: 2022-01-01 to 2027-12-31
Monthly Rent: $18,500
Dispute Clause: Section 14 — Mediation required before litigation.
""",
    "legal/contracts/leases/lease_addendum_parking.txt": """ADDENDUM: Parking Rights
12 reserved spaces, Level B2.
Subject to separate license agreement.
""",
    "legal/contracts/amendments/amendment_01_rent_escalation.txt": """AMENDMENT 1
Effective Date: 2023-06-01
Clause 4.2 modified: Annual rent escalation capped at 3%.
""",
    "legal/disputes/2024/dispute_log.txt": """DISPUTE LOG - Unit 4B
Date: 2024-03-15 — Tenant claims HVAC failure caused $220,000 in inventory loss.
Date: 2024-04-02 — Landlord disputes liability; cites tenant's failure to report.
Date: 2024-05-10 — Parties agreed to pursue mediation per Section 14.
Status: PENDING MEDIATION
""",
    "legal/disputes/2024/demand_letter_tenant.txt": """Via Certified Mail
Re: Demand for Compensation — HVAC Failure, Unit 4B

Dear Westfield Properties,
Pinnacle Retail Group formally demands $220,000 in compensatory damages...
""",
    "legal/disputes/2023/resolved_parking_dispute.txt": """RESOLVED: Parking overage dispute settled for $4,200.
No further action required.
""",
    "legal/correspondence/opposing_counsel/email_thread_may2024.txt": """From: j.morgan@westfieldlegal.com
To: d.chen@pinnaclelegal.com
Re: Mediation Scheduling

We are available for mediation any week in July 2024. Please confirm mediator selection.
""",
    "legal/correspondence/internal/strategy_notes_DRAFT.txt": """INTERNAL - PRIVILEGED AND CONFIDENTIAL
Our BATNA: File in Superior Court if mediation fails.
Max concession authority: $95,000.
Do NOT share with opposing counsel.
""",
    "hr/policies/vacation_policy_2024.pdf.txt": """VACATION POLICY (placeholder text)
Employees accrue 1.5 days per month...
""",
    "hr/records/org_chart_q2_2024.txt": """CEO - Rachel Okonkwo
CFO - James Park
General Counsel - Diana Chen
""",
    "finance/invoices/q1/inv_20240115_hvac_repair.txt": """INVOICE
Vendor: CoolAir Commercial HVAC
Amount: $14,320
Description: Emergency repair services, Unit 4B, Jan 15 2024
""",
    "finance/invoices/q2/inv_20240401_expert_witness.txt": """INVOICE
Vendor: BuildingTech Experts LLC
Amount: $8,500
Description: Expert witness assessment, HVAC systems
""",
    "finance/reports/loss_assessment_hvac_incident.txt": """LOSS ASSESSMENT REPORT
Prepared by: Finance Department
Incident: HVAC Failure, Jan 12-14 2024
Direct inventory loss: $187,400
Business interruption: $32,600
Total claimed: $220,000
""",
    "operations/facilities/hvac_maintenance_schedule.txt": """HVAC MAINTENANCE LOG - Unit 4B
Last service: 2023-09-10 by CoolAir Commercial HVAC
Next scheduled: 2024-03-10 (MISSED - unit failure occurred Jan 2024)
""",
    "operations/maintenance_logs/incident_report_20240112.txt": """INCIDENT REPORT
Date: 2024-01-12
Location: Unit 4B, Level 3
Description: Complete HVAC failure, compressor burnout.
Tenant notified at 14:32. Emergency crew dispatched 16:00.
""",
    "config/app_config.yaml": """environment: production
log_level: INFO
timeout: 30
""",
    "tmp/scratch/notes.txt": """TODO: Prepare mediation brief
- Check what the ADR tool outputs
- Need all process stages
- Include techniques + settlement terms
- Checklist for counsel
""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the scripts/script.sh with realistic mediation content ---
# This is the bespoke tool whose output defines the "correct" answer
script_content = r"""#!/usr/bin/env bash
set -euo pipefail

MEDIATION_DIR="${MEDIATION_DIR:-$HOME/.mediation/}"
VERSION="1.0.0"

CMD="${1:-help}"

case "$CMD" in

  intro)
    cat <<'EOF'
=== MEDIATION: INTRODUCTION ===

Mediation is a voluntary, confidential process in which a neutral third party
(the mediator) facilitates negotiation between disputing parties to help them
reach a mutually acceptable resolution.

Key Principles:
  - Voluntary participation
  - Confidentiality of proceedings
  - Mediator neutrality (no decision-making power)
  - Party self-determination

Comparison:
  Litigation   : Formal, adversarial, judge decides, public record, costly
  Arbitration  : Semi-formal, arbitrator decides, binding, limited appeal
  Mediation    : Informal, collaborative, parties decide, private, cost-effective

Best Suited For:
  - Ongoing business relationships worth preserving
  - Disputes where privacy is important
  - Cases where creative solutions are needed
  - Cost/time-sensitive situations

EOF
    ;;

  process)
    cat <<'EOF'
=== MEDIATION: PROCESS STAGES ===

Stage 1 — OPENING STATEMENT
  Mediator introduces process, establishes ground rules, confirms confidentiality,
  and explains their role. Each party delivers uninterrupted opening remarks.

Stage 2 — JOINT SESSION (Information Gathering)
  Parties present their perspectives, interests, and concerns.
  Mediator uses active listening and open-ended questions to surface underlying needs.
  Key documents and evidence may be referenced.

Stage 3 — CAUCUS (Private Sessions)
  Mediator meets privately with each party separately.
  Explores confidential interests, tests assumptions, reality-checks positions.
  Information shared in caucus is kept confidential unless permission granted.

Stage 4 — NEGOTIATION (Bargaining Phase)
  Parties (directly or through mediator shuttle) exchange proposals.
  Mediator facilitates movement from positions to interests.
  Multiple rounds of proposals may occur.

Stage 5 — CLOSURE
  If agreement reached: terms are recorded in a written Settlement Agreement.
  If impasse: mediator documents the deadlock and may suggest next steps (e.g., arbitration).
  Confidentiality obligations survive closure.

EOF
    ;;

  techniques)
    cat <<'EOF'
=== MEDIATION: MEDIATOR TECHNIQUES ===

Technique 1 — REFRAMING
  Restating a party's negative or positional statement in neutral, interest-based
  language to reduce hostility and open dialogue.
  Example: "You're saying you need certainty about the repair timeline."

Technique 2 — REALITY TESTING
  Helping a party evaluate the strength and risk of their own position by asking
  probing questions about evidence, costs, and litigation outcomes.
  Example: "What do you think a judge would say about this clause?"

Technique 3 — BATNA/WATNA ANALYSIS
  Best Alternative To a Negotiated Agreement (BATNA): the strongest fallback option.
  Worst Alternative To a Negotiated Agreement (WATNA): the worst realistic outcome.
  Mediator helps each party privately assess both to calibrate settlement willingness.

Technique 4 — ANCHORING
  Strategic use of the first offer to set the psychological reference point for
  subsequent negotiations. Parties with strong BATNAs typically anchor high/low.
  Mediator may neutralize destructive anchors through reframing or sequencing.

EOF
    ;;

  types)
    cat <<'EOF'
=== ADR SPECTRUM: TYPES ===

1. NEGOTIATION
   Direct party-to-party discussion. No third party. Fastest, least formal.

2. MEDIATION
   Neutral facilitator. Non-binding. Parties retain control of outcome.

3. MED-ARB (Mediation-Arbitration)
   Begins as mediation; if no settlement, mediator becomes arbitrator and decides.
   Risk: chilling effect on candor in mediation phase.

4. ARBITRATION
   Neutral arbitrator hears evidence and issues binding award.
   Faster/cheaper than litigation but limited appeal rights.

5. EARLY NEUTRAL EVALUATION (ENE)
   Neutral expert provides non-binding assessment of case merits early in dispute.
   Useful for technical disputes (e.g., construction, IP, engineering).

6. LITIGATION
   Court process. Public, adversarial, expensive, slow. Judge or jury decides.

EOF
    ;;

  preparation)
    cat <<'EOF'
=== MEDIATION: PREPARATION GUIDE ===

1. POSITION STATEMENT
   Prepare a written summary of your position, key facts, and desired outcome.
   Keep confidential sections clearly labeled.

2. BATNA/WATNA ASSESSMENT
   Identify your Best Alternative and Worst Alternative to settlement.
   Quantify costs of non-settlement (legal fees, time, reputational risk).

3. AUTHORITY
   Ensure the attending representative has full settlement authority.
   Lack of authority is a leading cause of mediation failure.

4. DOCUMENTS
   Gather supporting documents: contracts, correspondence, financial records, expert reports.
   Organize chronologically. Prepare a concise exhibit list.

5. INTERESTS VS. POSITIONS
   Identify underlying interests (what you really need) vs. stated positions (what you say you want).
   Prepare to discuss interests openly in caucus.

6. SETTLEMENT PARAMETERS
   Define your reservation point (minimum acceptable outcome).
   Prepare a range of creative settlement options beyond pure monetary compensation.

EOF
    ;;

  settlement)
    cat <<'EOF'
=== SETTLEMENT AGREEMENTS: ESSENTIAL GUIDE ===

Essential Terms (must include all of the following):

  1. PARTIES — Full legal names of all parties to the agreement.
  2. RECITALS — Brief statement of the dispute and the mediation context.
  3. PAYMENT TERMS — Amount, currency, payment schedule, and method.
  4. RELEASES — Scope of mutual release of claims (specify "known and unknown" if applicable).
  5. CONFIDENTIALITY — Prohibition on disclosure of settlement terms (if desired).
  6. NON-DISPARAGEMENT — Optional clause prohibiting negative public statements.
  7. DISMISSAL/WITHDRAWAL — Agreement to dismiss any pending litigation or claims.
  8. BREACH REMEDIES — Consequences and jurisdiction for enforcement if a party defaults.
  9. GOVERNING LAW — Specify applicable jurisdiction and law.
  10. SIGNATURES — All parties and counsel must sign; date of execution required.

Enforceability Notes:
  - Settlement agreements are contracts; standard contract formation rules apply.
  - In many jurisdictions, mediation settlement agreements are enforceable as contracts.
  - Some jurisdictions allow entry as a court order (consent judgment) for direct enforcement.
  - Confidentiality clauses are generally enforceable but may have carve-outs for legal proceedings.

Tax Implications:
  - Compensatory damages for physical injury: generally excludable from income (IRC §104).
  - Business loss settlements: typically ordinary income; consult tax counsel.
  - Structured payments: special tax treatment may apply; consider installment reporting.

EOF
    ;;

  ethics)
    cat <<'EOF'
=== MEDIATOR ETHICS ===

Core Ethical Obligations:

  1. NEUTRALITY — Mediator must not favor either party. Must disclose any bias or prior relationship.
  2. CONFIDENTIALITY — All communications in mediation are privileged and confidential.
     Exceptions: imminent harm, court order, crime-fraud.
  3. SELF-DETERMINATION — Parties must reach their own agreement voluntarily.
     Mediator may not coerce, pressure, or impose solutions.
  4. COMPETENCE — Mediator must have adequate training and subject matter awareness.
  5. CONFLICTS OF INTEREST — Prior representation, financial interest, or personal
     relationship with any party must be disclosed and waived or recused.
  6. IMPARTIALITY IN CAUCUS — Information shared in private session must be kept
     confidential from other party unless express permission given.

Governing Standards:
  - Model Standards of Conduct for Mediators (AAA/ABA/ACR, 2005)
  - State-specific mediator certification requirements vary.

EOF
    ;;

  checklist)
    cat <<'EOF'
=== MEDIATION READINESS CHECKLIST ===

PRE-MEDIATION (Complete at least 5 business days before session):
  [ ] Confirm mediator selection and neutrality (no conflicts of interest)
  [ ] Serve and receive position statements / mediation briefs
  [ ] Verify attending representative has full settlement authority
  [ ] Compile and organize supporting documents (contracts, invoices, correspondence)
  [ ] Complete BATNA/WATNA analysis and define reservation point
  [ ] Identify underlying interests distinct from stated positions
  [ ] Prepare list of creative settlement options (non-monetary if applicable)

DAY-OF MEDIATION:
  [ ] Arrive early; review key documents and opening remarks
  [ ] Bring executed copies of any required confidentiality agreements
  [ ] Have blank Settlement Agreement template available
  [ ] Confirm authority level with client/principal before session starts

POST-MEDIATION:
  [ ] If settled: draft and execute Settlement Agreement same day where possible
  [ ] File dismissal or notice of settlement with any pending tribunal within required deadline
  [ ] Preserve all mediation communications per confidentiality obligations
  [ ] If impasse: evaluate next ADR step (arbitration, ENE, or litigation)

EOF
    ;;

  help)
    cat <<'EOF'
=== MEDIATION ADR REFERENCE TOOL v1.0.0 ===

Usage: scripts/script.sh <command>

Commands:
  intro        Overview of mediation vs. litigation vs. arbitration
  process      Five-stage mediation process
  techniques   Mediator techniques (reframing, reality testing, BATNA/WATNA, anchoring)
  types        Full ADR spectrum
  preparation  How to prepare for mediation
  settlement   Settlement agreement essential terms
  ethics       Mediator ethics and confidentiality
  checklist    Mediation readiness checklist
  version      Show version
  help         Show this help

Configuration:
  MEDIATION_DIR   Data directory (default: ~/.mediation/)

EOF
    ;;

  version)
    echo "mediation-skill version $VERSION"
    ;;

  *)
    echo "ERROR: Unknown command '$CMD'. Run 'scripts/script.sh help' for usage." >&2
    exit 1
    ;;
esac
"""

script_path = os.path.join(workspace, "scripts", "script.sh")
os.makedirs(os.path.join(workspace, "scripts"), exist_ok=True)
with open(script_path, "w") as f:
    f.write(script_content)

# Make it executable
os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# --- Create a minimal SKILL.md in workspace ---
skill_md = """---
name: "mediation"
version: "1.0.0"
description: "Mediation and ADR reference — dispute resolution processes, mediator techniques, caucus strategy, settlement agreements."
---

# Mediation — Alternative Dispute Resolution Reference

## Commands

### `intro`
```bash
scripts/script.sh intro
```

### `process`
```bash
scripts/script.sh process
```

### `techniques`
```bash
scripts/script.sh techniques
```

### `types`
```bash
scripts/script.sh types
```

### `preparation`
```bash
scripts/script.sh preparation
```

### `settlement`
```bash
scripts/script.sh settlement
```

### `ethics`
```bash
scripts/script.sh ethics
```

### `checklist`
```bash
scripts/script.sh checklist
```

### `help`
```bash
scripts/script.sh help
```

### `version`
```bash
scripts/script.sh version
```

## Configuration

| Variable | Description |
|----------|-------------|
| `MEDIATION_DIR` | Data directory (default: ~/.mediation/) |
"""

with open(os.path.join(workspace, "SKILL.md"), "w") as f:
    f.write(skill_md)

print("Workspace initialized successfully.")
print(f"Files created: {len(distractor_files)} distractor files + scripts/script.sh + SKILL.md")