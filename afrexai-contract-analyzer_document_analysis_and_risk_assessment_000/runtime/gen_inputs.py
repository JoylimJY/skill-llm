import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Distractor directory structure ---
dirs = [
    "contracts/archive/2021",
    "contracts/archive/2022",
    "contracts/active",
    "contracts/templates",
    "legal/correspondence",
    "legal/policies",
    "finance/invoices",
    "finance/reports",
    "hr/employment",
    "ops/vendor_management",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "contracts/archive/2021/vendor_nda_2021.txt": "MUTUAL NON-DISCLOSURE AGREEMENT dated January 5, 2021 between Apex Corp and DataSync Ltd. [Fully executed and archived]",
    "contracts/archive/2022/supply_agreement_2022.txt": "SUPPLY AGREEMENT dated March 10, 2022. [Archived - superseded by 2023 renewal]",
    "contracts/templates/nda_template.txt": "TEMPLATE: MUTUAL NDA - [PARTY A] and [PARTY B]. [Do not use without legal review]",
    "contracts/templates/msa_template.txt": "TEMPLATE: MASTER SERVICE AGREEMENT - Boilerplate v2.1. [Internal use only]",
    "legal/correspondence/counsel_email_2023-11-01.txt": "Subject: Re: Vendor Contract Review\nPlease ensure all contracts go through legal before signing.",
    "legal/policies/data_retention_policy.txt": "DATA RETENTION POLICY v3.2\nAll customer data must be retained for minimum 7 years per regulatory requirements.",
    "legal/policies/vendor_approval_checklist.txt": "VENDOR APPROVAL CHECKLIST\n1. SOC2 certification\n2. Insurance certificate\n3. Background check\n4. Contract review",
    "finance/invoices/inv_2024_001.txt": "INVOICE #2024-001\nVendor: MedAnalytics Inc.\nAmount: $24,500\nDue: Net-30",
    "finance/reports/q3_2024_vendor_spend.txt": "Q3 2024 Vendor Spend Report\nTotal SaaS: $182,000\nTop vendor: MedAnalytics Inc. ($74,000)",
    "hr/employment/offer_letter_template.txt": "OFFER LETTER TEMPLATE\nDear [CANDIDATE], We are pleased to offer you the position of...",
    "ops/vendor_management/vendor_contacts.txt": "VENDOR CONTACTS\nMedAnalytics Inc: contracts@medanalytics.io | 1-800-555-0192\nDataSync Ltd: legal@datasync.com | 1-800-555-0181",
    "ops/vendor_management/renewal_tracker.txt": "CONTRACT RENEWAL TRACKER\nMedAnalytics MSA: Expires 2025-03-31 | Auto-renewal: YES\nDataSync NDA: Expires 2025-01-15 | Auto-renewal: NO",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE PROBLEM: A messy, realistic SaaS contract with multiple risk issues ---
# This contract has: unlimited liability for one party, one-sided indemnification,
# aggressive auto-renewal with short notice window, broad IP assignment,
# extremely broad non-solicit, no force majeure, no data/privacy clause,
# payment terms Net-90, missing dispute resolution clause.

contract_text = """MASTER SERVICES AGREEMENT

This Master Services Agreement ("Agreement") is entered into as of the Effective Date
between MedAnalytics Inc., a Delaware corporation ("Vendor"), and the client entity
executing an Order Form referencing this Agreement ("Client").

SECTION 1. SERVICES

1.1 Vendor shall provide Client with access to the MedAnalytics cloud-based healthcare
data analytics platform ("Platform") as described in the applicable Order Form(s).

1.2 Vendor may modify, update, or discontinue any feature of the Platform at its sole
discretion with or without notice to Client.

1.3 Vendor shall use commercially reasonable efforts to maintain 95% monthly uptime.
No SLA credits or remedies are available to Client for any downtime below this threshold.

SECTION 2. FEES AND PAYMENT

2.1 Client shall pay all fees specified in the Order Form within ninety (90) calendar days
of the invoice date ("Net-90"). Invoices shall be issued monthly.

2.2 Vendor reserves the right to increase fees by any amount upon thirty (30) days written
notice prior to each annual renewal term.

2.3 All fees are non-refundable under any circumstances. Client shall not withhold or
offset any amounts owed.

2.4 Overdue invoices shall accrue interest at 5% per month compounded daily.

SECTION 3. TERM AND TERMINATION

3.1 This Agreement shall commence on the Effective Date and continue for an initial term
of two (2) years. Unless either party provides written notice of non-renewal at least
one hundred eighty (180) days prior to the end of the then-current term, this Agreement
shall automatically renew for successive two (2)-year terms.

3.2 Vendor may terminate this Agreement immediately for any reason by providing written
notice to Client.

3.3 Client may only terminate this Agreement for cause if Vendor has materially breached
this Agreement and failed to cure such breach within ninety (90) days of written notice.
Client has no right to terminate for convenience.

3.4 Upon termination for any reason, Client shall pay all fees that would have been owed
through the end of the then-current term as a termination penalty ("Breakage Fee").

SECTION 4. INTELLECTUAL PROPERTY

4.1 All inventions, developments, software, analyses, models, reports, and work product
created by Vendor or by Client's personnel in connection with the use of the Platform
("Work Product") shall be the sole and exclusive property of Vendor.

4.2 Client hereby irrevocably assigns to Vendor all right, title, and interest in any
Work Product, including any improvements or derivative works.

4.3 Client's data uploaded to the Platform ("Client Data") may be used by Vendor in
anonymized or aggregated form for product improvement, benchmarking, research, and
commercial purposes without additional compensation to Client.

SECTION 5. INDEMNIFICATION

5.1 Client shall indemnify, defend, and hold harmless Vendor and its affiliates, officers,
directors, employees, and agents from and against any and all claims, damages, losses,
liabilities, costs, and expenses (including reasonable attorneys' fees) arising out of or
related to: (a) Client's use of the Platform; (b) any breach of this Agreement by Client;
(c) any claim by a third party related to data submitted by Client; or (d) any regulatory
action or investigation related to Client's business.

5.2 Vendor shall have no indemnification obligations to Client under this Agreement.

SECTION 6. LIMITATION OF LIABILITY

6.1 IN NO EVENT SHALL VENDOR BE LIABLE TO CLIENT FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
CONSEQUENTIAL, OR PUNITIVE DAMAGES.

6.2 NOTWITHSTANDING THE FOREGOING, VENDOR'S TOTAL CUMULATIVE LIABILITY TO CLIENT FOR
ANY AND ALL CLAIMS SHALL NOT EXCEED ONE HUNDRED DOLLARS ($100.00).

6.3 CLIENT'S LIABILITY TO VENDOR SHALL BE UNLIMITED AND SHALL INCLUDE ALL DIRECT,
INDIRECT, CONSEQUENTIAL, INCIDENTAL, AND SPECIAL DAMAGES WITHOUT CAP OR LIMITATION.

SECTION 7. CONFIDENTIALITY

7.1 Each party agrees to maintain the confidentiality of the other party's Confidential
Information during the term of this Agreement only.

7.2 Confidentiality obligations shall expire upon termination of this Agreement.

7.3 Vendor may disclose Client's Confidential Information to its affiliates, subcontractors,
and third-party service providers without Client's consent.

SECTION 8. NON-SOLICITATION

8.1 During the term of this Agreement and for a period of five (5) years following
termination, Client shall not directly or indirectly solicit, hire, or engage any
current or former employee, contractor, or consultant of Vendor.

8.2 Client shall not, directly or indirectly, develop, market, sell, or assist any
third party to develop or market any product or service that is competitive with
any product or service offered by Vendor at any time during or after the term.

SECTION 9. GOVERNING LAW

9.1 This Agreement shall be governed by the laws of the State of Delaware, USA, without
regard to its conflict of laws provisions.

9.2 Any disputes shall be resolved exclusively in the state or federal courts located
in Wilmington, Delaware, and Client irrevocably consents to personal jurisdiction therein.

SECTION 10. GENERAL

10.1 This Agreement constitutes the entire agreement between the parties with respect
to its subject matter.

10.2 Vendor may assign this Agreement without Client's consent. Client may not assign
this Agreement without Vendor's prior written consent.

10.3 Vendor reserves the right to modify this Agreement at any time by posting a revised
version to its website, and Client's continued use of the Platform shall constitute
acceptance of such modifications.

EFFECTIVE DATE: This Agreement is effective as of the date the Order Form is executed.

MEDANALYTICS INC.               CLIENT
By: ___________________         By: ___________________
"""

contract_path = os.path.join(workspace, "contracts/active/medanalytics_msa_draft.txt")
with open(contract_path, "w") as f:
    f.write(contract_text)

print("Workspace generated successfully.")
print(f"Contract file: {contract_path}")
print(f"Total distractor files: {len(distractor_files)}")