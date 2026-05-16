#!/usr/bin/env python3
"""
Generate a realistic biotech startup workspace with distractor files.
The agent must navigate this to find context and produce the NDA DOCX.
"""
import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create deeply nested directory structure with distractor files ---

dirs = [
    "legal/contracts/templates",
    "legal/contracts/signed",
    "legal/compliance/gdpr",
    "legal/compliance/hipaa",
    "research/protocols/phase1",
    "research/protocols/phase2",
    "vendors/evaluation/crimelab_bio",
    "vendors/evaluation/genomatix_cro",
    "vendors/approved",
    "finance/invoices/2024",
    "finance/invoices/2025",
    "hr/onboarding",
    "hr/policies",
    "ops/infrastructure",
    "ops/runbooks",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor: old SAFE agreement template (not NDA)
(workspace / "legal/contracts/templates/yc_safe_template_v2.md").write_text(
    """# YC SAFE Template (Placeholder)
This is a Simple Agreement for Future Equity.
Parties: [Investor Name], [Company Name]
Amount: $[Investment Amount]
Valuation Cap: $[Valuation Cap]
Discount Rate: [X]%
"""
)

# Distractor: a partially filled old NDA (wrong format, wrong tool)
(workspace / "legal/contracts/signed/old_nda_acme_2023.txt").write_text(
    """MUTUAL NON-DISCLOSURE AGREEMENT
Between: NovaBiotek Inc. AND Acme Supplies Ltd.
Date: January 15, 2023
Purpose: General vendor supplies discussion
[SIGNED - ARCHIVED]
"""
)

# Distractor: compliance checklist
(workspace / "legal/compliance/gdpr/data_processing_checklist.json").write_text(
    json.dumps({
        "checklist": [
            {"item": "Data mapping complete", "status": "done"},
            {"item": "DPA signed with vendors", "status": "pending"},
            {"item": "Privacy policy updated", "status": "done"},
        ]
    }, indent=2)
)

# Distractor: vendor evaluation notes
(workspace / "vendors/evaluation/genomatix_cro/initial_notes.md").write_text(
    """# Genomatix CRO - Initial Vendor Evaluation Notes

## Contact
- Primary: Dr. Sarah Lim, VP Business Development
- Email: s.lim@genomatix-cro.example.com

## Capabilities
- Phase I/II clinical trial management
- Biomarker analysis
- Regulatory submissions (FDA, EMA)

## Status
- Intro call: 2025-06-10
- Technical review: SCHEDULED 2025-07-01
- **NDA: REQUIRED BEFORE SHARING PROTOCOL DETAILS**

## Notes
We need to share our proprietary liquid biopsy protocol details (NovaBiotek 
Confidential Research Protocol v3.1) before the technical review. Legal has 
confirmed we need a one-way NDA since only WE are disclosing — Genomatix 
is just evaluating our methodology, not sharing their own secrets.
"""
)

# Distractor: another vendor (already has NDA, not relevant)
(workspace / "vendors/evaluation/crimelab_bio/nda_status.txt").write_text(
    "NDA signed 2025-04-22. On file: legal/contracts/signed/crimelab_bio_nda_2025.docx\n"
)

# Distractor: research protocol (the sensitive doc that will be shared AFTER NDA)
(workspace / "research/protocols/phase1/liquid_biopsy_protocol_v3_1.md").write_text(
    """# NovaBiotek Confidential Research Protocol v3.1
## Liquid Biopsy Methodology

**CONFIDENTIAL - DO NOT DISTRIBUTE WITHOUT SIGNED NDA**

### Overview
This protocol describes NovaBiotek's proprietary approach to cell-free DNA 
extraction and analysis for early-stage cancer detection.

### Key Steps
1. Blood draw and sample processing (patent-pending centrifugation method)
2. cfDNA isolation using modified SPRI bead protocol
3. Library preparation with UMI barcoding
4. Bioinformatics pipeline (NovaBiotek PipelineX v2)
5. Variant calling and clinical interpretation

### IP Notice
All methods described herein are proprietary to NovaBiotek Inc.
"""
)

# Distractor: HR onboarding doc mentioning NDAs (red herring)
(workspace / "hr/onboarding/employee_nda_process.md").write_text(
    """# Employee NDA Process

All new employees must sign the standard employee NDA within their first week.
Contact HR at hr@novabiotek.example.com for the DocuSign link.

Note: Employee NDAs are handled separately from vendor/partner NDAs.
For vendor NDAs, contact legal@novabiotek.example.com.
"""
)

# Distractor: ops runbook (irrelevant)
(workspace / "ops/runbooks/deployment_checklist.md").write_text(
    """# Deployment Checklist
1. Run unit tests
2. Build Docker image
3. Push to registry
4. Update Helm chart
5. Deploy to staging
6. Smoke test
7. Deploy to production
"""
)

# Distractor: finance invoice (irrelevant)
(workspace / "finance/invoices/2025/inv_001_labsupplies.json").write_text(
    json.dumps({
        "invoice_id": "INV-2025-001",
        "vendor": "LabSupplies Co.",
        "amount": 12450.00,
        "currency": "USD",
        "date": "2025-06-01",
        "status": "paid"
    }, indent=2)
)

# Distractor: a generic JSON template that looks like it could be NDA fields but is wrong
(workspace / "legal/contracts/templates/generic_nda_fields_DRAFT.json").write_text(
    json.dumps({
        "_WARNING": "THIS IS AN OUTDATED DRAFT - DO NOT USE",
        "company_a": "",
        "company_b": "",
        "date": "",
        "confidential_info": "",
        "term_years": "2"
    }, indent=2)
)

# Distractor: an empty placeholder for the output (wrong extension)
(workspace / "legal/contracts/genomatix_nda_placeholder.txt").write_text(
    "PLACEHOLDER: Final NDA DOCX to be generated here once fields are confirmed.\n"
)

# --- KEY CONTEXT FILE: the business brief for the agent ---
# This provides the business context WITHOUT revealing CLI commands or field names.
(workspace / "vendors/evaluation/genomatix_cro/legal_request.md").write_text(
    """# Legal Request: NDA for Genomatix CRO Engagement

## Requestor
Operations Team, NovaBiotek Inc.

## Background
NovaBiotek Inc. (a Delaware corporation) is evaluating Genomatix CRO Ltd. 
as a potential contract research partner for Phase I clinical trial management.

Before the technical review meeting scheduled for July 1, 2025, we need to 
share details of our proprietary liquid biopsy protocol. Legal has confirmed:

- **NovaBiotek is the ONLY disclosing party** (one-way disclosure)
- Genomatix will NOT be sharing any of their own confidential information
- This is purely for vendor evaluation purposes

## Required Agreement Details
- Disclosing Party: NovaBiotek Inc.
- Receiving Party: Genomatix CRO Ltd.
- Effective Date: July 1, 2025
- Purpose: Evaluating Genomatix CRO Ltd. as a potential contract research 
  organization for Phase I clinical trial management services

## Output Required
A signable Word document (DOCX format) named: `genomatix_one_way_nda.docx`
Save it in the `legal/contracts/` directory.

## Urgency
Needed before July 1, 2025. Please generate ASAP.
"""
)

# Distractor: an old Python script that tried to generate NDAs differently (wrong approach)
(workspace / "ops/infrastructure/old_nda_generator.py").write_text(
    """#!/usr/bin/env python3
# DEPRECATED: Old NDA generator - replaced by proper tooling
# This script no longer works and should not be used.
import sys

def generate_nda(party1, party2, date):
    raise NotImplementedError("This script is deprecated. Use the approved legal tooling instead.")

if __name__ == "__main__":
    print("ERROR: This script is deprecated.")
    sys.exit(1)
"""
)

# Distractor: package.json that has nothing to do with NDA (red herring for Node.js)
(workspace / "ops/infrastructure/package.json").write_text(
    json.dumps({
        "name": "novabiotek-ops-scripts",
        "version": "1.0.0",
        "description": "Internal ops automation scripts",
        "scripts": {
            "health-check": "node healthcheck.js"
        },
        "dependencies": {
            "axios": "^1.6.0"
        }
    }, indent=2)
)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")