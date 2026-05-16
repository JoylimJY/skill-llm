import os
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── SKILL reference files (these already "exist" per the skill's assumption) ──
skill_dir = workspace / "skill_docs"
skill_dir.mkdir(parents=True, exist_ok=True)

(skill_dir / "phases.md").write_text(textwrap.dedent("""\
    # Contract Drafting Phases

    ## Phase 1: Discovery
    - Identify contract type (services, NDA, employment, lease, etc.)
    - Identify all parties and their roles
    - Determine governing jurisdiction
    - Complete intake questionnaire (see intake.md)
    - CANNOT proceed to Phase 2 without completed discovery answers

    ## Phase 2: Structure
    - Define sections based on contract type
    - Mandatory sections for services agreements:
        * Parties & Recitals
        * Scope of Work
        * Compensation & Payment Terms
        * Intellectual Property
        * Confidentiality
        * Term & Termination
        * Limitation of Liability
        * Governing Law & Dispute Resolution
        * Signatures
    - Check clauses.md for required clause patterns

    ## Phase 3: Draft
    - Generate each section with complete clause text
    - For critical clauses (IP, liability), offer at least one alternative version in notes.md
    - Include AI disclaimer at top of every draft

    ## Phase 4: Review
    - Run risk analysis (see risks.md)
    - Flag ambiguous language
    - Record findings in notes.md

    ## Phase 5: Negotiate
    - If multiple parties with opposing interests, log positions in notes.md
    - Propose compromise language

    ## Phase 6: Finalize
    - Requires explicit human approval
    - Move to ~/contracts/{name}/ only after signing
"""))

(skill_dir / "intake.md").write_text(textwrap.dedent("""\
    # Intake Questionnaire by Contract Type

    ## Services Agreement
    1. Full legal name and address of Service Provider?
    2. Full legal name and address of Client?
    3. Describe the services in specific detail (deliverables, milestones)?
    4. What is the total compensation? Fixed fee or hourly?
    5. Payment schedule (upfront, milestone-based, net-30)?
    6. Who owns the IP created during the engagement?
    7. Are there confidentiality obligations?
    8. What is the contract term (start/end date or project-based)?
    9. Termination conditions (notice period, for-cause provisions)?
    10. Governing jurisdiction (state/country)?
    11. Any special restrictions (non-compete, exclusivity)?
    12. Dispute resolution preference (arbitration, mediation, litigation)?

    ## NDA
    1. Disclosing party name?
    2. Receiving party name?
    3. Purpose of disclosure?
    4. Duration of confidentiality obligation?
    5. Jurisdiction?

    ## Employment
    1. Employer legal name?
    2. Employee name and role?
    3. Compensation structure?
    4. Benefits?
    5. At-will or fixed term?
"""))

(skill_dir / "clauses.md").write_text(textwrap.dedent("""\
    # Clause Patterns

    ## Scope of Work
    Pattern: \"Service Provider agrees to perform the following services: [DESCRIPTION]. 
    Deliverables shall include: [LIST]. Any work outside this scope requires a written change order.\"

    ## Payment
    Pattern: \"Client shall pay Service Provider [AMOUNT] according to the following schedule: [SCHEDULE].
    Invoices unpaid after [N] days accrue interest at [RATE]% per month.\"

    ## IP Assignment (Client-Favoring)
    Pattern: \"All work product created under this Agreement shall be works made for hire. 
    To the extent not qualifying as works made for hire, Service Provider hereby assigns all right, 
    title, and interest to Client.\"

    ## IP License (Provider-Favoring)
    Pattern: \"Service Provider retains ownership of all pre-existing IP and tools. 
    Client receives a perpetual, non-exclusive license to use deliverables for internal purposes.\"

    ## Limitation of Liability
    Pattern: \"IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, 
    OR CONSEQUENTIAL DAMAGES. TOTAL LIABILITY SHALL NOT EXCEED THE FEES PAID IN THE 
    THREE (3) MONTHS PRECEDING THE CLAIM.\"

    ## Termination for Convenience
    Pattern: \"Either party may terminate this Agreement upon [N] days written notice.\"

    ## Governing Law
    Pattern: \"This Agreement shall be governed by the laws of [JURISDICTION], 
    without regard to conflict of law principles.\"
"""))

(skill_dir / "risks.md").write_text(textwrap.dedent("""\
    # Risk Analysis Guide

    ## Common Risks in Services Agreements
    - Scope creep: Vague deliverables lead to disputes. MITIGATION: Define deliverables exhaustively.
    - IP disputes: Ambiguous ownership. MITIGATION: Explicit assignment or license clause.
    - Non-payment: Client default. MITIGATION: Milestone payments, late fees, suspension clause.
    - Liability exposure: Unlimited liability catastrophic for freelancers. MITIGATION: Cap liability clause.
    - Jurisdiction risk: Unclear governing law. MITIGATION: Explicit choice-of-law clause.

    ## Disclaimer Requirements
    ALL drafts must include at the top:
    \"This document was generated by AI. It does NOT constitute legal advice.
    Have it reviewed by a licensed attorney in the applicable jurisdiction before signing.\"

    ## Escalation Triggers
    - Employment classification disputes → escalate to labor attorney
    - IP involving patents → escalate to IP attorney
    - Contract value > $500,000 → recommend attorney review
    - Cross-border international transactions → escalate
"""))

# ── Existing ~/contracts/ structure with distractors ──
contracts_dir = workspace / "contracts"
contracts_dir.mkdir(parents=True, exist_ok=True)

# Old finalized contracts (distractors)
old1 = contracts_dir / "logo-design-2022"
old1.mkdir(parents=True, exist_ok=True)
(old1 / "executed.pdf").write_bytes(b"%PDF-1.4 fake pdf content for logo design contract 2022")
(old1 / "meta.md").write_text(textwrap.dedent("""\
    # Logo Design Contract 2022
    - Client: Acme Corp
    - Provider: DesignStudio LLC
    - Status: EXECUTED
    - Date: 2022-03-15
    - Value: $3,500
"""))

old2 = contracts_dir / "office-lease-2021"
old2.mkdir(parents=True, exist_ok=True)
(old2 / "executed.pdf").write_bytes(b"%PDF-1.4 fake office lease pdf")
(old2 / "meta.md").write_text(textwrap.dedent("""\
    # Office Lease 2021
    - Lessor: 123 Properties LLC
    - Lessee: MyStartup Inc
    - Status: EXECUTED
    - Expiry: 2024-01-31
"""))

# Drafting folder with an UNRELATED old draft (distractor)
drafting_dir = contracts_dir / "drafting"
drafting_dir.mkdir(parents=True, exist_ok=True)

old_draft = drafting_dir / "nda-vendor-2023"
old_draft.mkdir(parents=True, exist_ok=True)
(old_draft / "current.md").write_text(textwrap.dedent("""\
    # NDA - Vendor 2023 (ABANDONED)
    Parties: TechCo / SupplyVendor
    Status: Abandoned - vendor withdrew
"""))
old_draft_versions = old_draft / "versions"
old_draft_versions.mkdir(parents=True, exist_ok=True)
(old_draft_versions / "v001.md").write_text("Initial NDA draft - vendor 2023 - DRAFT 1")
(old_draft / "intake.md").write_text("Type: NDA\nStatus: incomplete - vendor pulled out")
(old_draft / "parties.md").write_text("TechCo (disclosing)\nSupplyVendor (receiving) - WITHDREW")
(old_draft / "notes.md").write_text("2023-08-10: Vendor withdrew from deal. Draft abandoned.")

# Miscellaneous distractor files at root of contracts/
(contracts_dir / "TODO.txt").write_text(textwrap.dedent("""\
    TODO:
    - Follow up on webapp dev agreement request from Jordan
    - Renew office lease
    - Archive 2021 contracts
"""))
(contracts_dir / "template_scratch.md").write_text(textwrap.dedent("""\
    # Scratch notes - NOT a real contract
    Random clause ideas:
    - payment net-30
    - 60 day termination notice?
    - who owns the code??
"""))
(contracts_dir / "contacts.txt").write_text(textwrap.dedent("""\
    Legal Contacts:
    - Sarah Chen, Attorney: sarah@legalfirm.example.com
    - Mike Torres, Notary: mike@notary.example.com
"""))

# A fake corrupted/partial draft that agent must NOT use
bad_draft = drafting_dir / "webapp-dev-agreement"
bad_draft.mkdir(parents=True, exist_ok=True)
(bad_draft / "notes.md").write_text(textwrap.dedent("""\
    # webapp-dev-agreement scratchpad
    Client reached out 2024-11-01. Needs a dev contract ASAP.
    - They want a web app built
    - Budget around $18,000
    - 6 month project
    NOTE: This file was auto-created. Actual intake NOT done yet.
"""))
# Intentionally leave intake.md, parties.md, current.md, versions/ MISSING
# to force the agent to create them properly

print("Workspace generated successfully.")
print("Distractor files and partial stub created.")