import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic, deeply nested directory structure for a law firm IT project
dirs = [
    "it_projects/email_consolidation/vendor_quotes",
    "it_projects/email_consolidation/staff_lists",
    "it_projects/email_consolidation/old_configs",
    "it_projects/network_upgrade/switches",
    "it_projects/network_upgrade/firewall_rules",
    "hr_records/onboarding/2023",
    "hr_records/onboarding/2024",
    "legal_docs/contracts/vendors",
    "legal_docs/nda_templates",
    "finance/invoices/Q1",
    "finance/invoices/Q2",
    "finance/budgets",
    "it_projects/email_consolidation/scripts",
    "it_projects/email_consolidation/references",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "it_projects/email_consolidation/vendor_quotes/techcorp_quote_2024.txt": (
        "TechCorp Email Migration Services\nQuote #2024-8821\nEstimated cost: $12,000\nTimeline: 6 weeks\n"
    ),
    "it_projects/email_consolidation/vendor_quotes/databridge_proposal.txt": (
        "DataBridge Solutions - Email Migration Proposal\nApproach: Hybrid PST/IMAP sync\nLicenses: 50 users\n"
    ),
    "it_projects/email_consolidation/staff_lists/all_staff_june2024.csv": (
        "name,department,current_email,target_email\n"
        "Alice Chen,Litigation,alice@yahoo.com,alice@firmlaw.com\n"
        "Bob Patel,Corporate,bob@zoho.com,bob@firmlaw.com\n"
        "Carol Russo,IP,carol@protonmail.com,carol@firmlaw.com\n"
        "Dan Whitmore,Finance,dan@icloud.com,dan@firmlaw.com\n"
        "Eve Tanaka,HR,eve@zoho.com,eve_t@firmlaw.com\n"
        "Frank O'Brien,IT,frank@yahoo.com,frank@firmlaw.com\n"
        "Gina Marsh,Paralegal,gina@protonmail.com,gina@firmlaw.com\n"
    ),
    "it_projects/email_consolidation/old_configs/legacy_imap_settings.ini": (
        "[yahoo]\nhost=imap.mail.yahoo.com\nport=993\nssl=true\n\n[zoho]\nhost=imap.zoho.com\nport=993\nssl=true\n"
    ),
    "it_projects/email_consolidation/old_configs/thunderbird_profile_backup.txt": (
        "# Old Thunderbird profile paths\nprofile_dir=/home/itadmin/.thunderbird/abc123.default\nlast_sync=2023-11-15\n"
    ),
    "it_projects/network_upgrade/switches/vlan_config_2024.txt": (
        "VLAN 10: Management\nVLAN 20: Staff\nVLAN 30: Guest\n"
    ),
    "it_projects/network_upgrade/firewall_rules/outbound_rules.txt": (
        "ALLOW TCP 993 OUTBOUND # IMAP SSL\nALLOW TCP 587 OUTBOUND # SMTP TLS\nDENY ALL\n"
    ),
    "hr_records/onboarding/2024/checklist_template.txt": (
        "New Employee IT Checklist\n1. Assign laptop\n2. Create email account\n3. VPN setup\n4. Badge access\n"
    ),
    "legal_docs/nda_templates/vendor_nda_v3.txt": (
        "NON-DISCLOSURE AGREEMENT\nThis agreement is entered into by TechCorp Solutions and Meridian Law Firm LLP...\n"
    ),
    "finance/budgets/it_budget_2024.txt": (
        "IT Budget FY2024\nEmail Migration: $15,000 allocated\nNetwork Upgrade: $45,000 allocated\nHardware Refresh: $22,000 allocated\n"
    ),
    "finance/invoices/Q1/techcorp_inv_001.txt": (
        "Invoice #TC-001\nService: Email audit and scoping\nAmount: $2,500\nDue: 2024-03-15\n"
    ),
    "it_projects/email_consolidation/scripts/placeholder.txt": (
        "# Migration scripts will be placed here\n# imap-test.py - connectivity testing\n# mailbox-size.py - size estimation\n"
    ),
    "it_projects/email_consolidation/references/notes.txt": (
        "See vendor documentation for detailed procedures.\nContact: it-support@firmlaw.com\n"
    ),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# The main input file: a messy, partially filled migration request spreadsheet as JSON
# This is the "raw messy input" the agent must process
migration_requests_raw = {
    "project": "Meridian Law Firm - Email Consolidation Project 2024",
    "requested_by": "Sandra Willis, IT Director",
    "target_domain": "firmlaw.com",
    "target_platform": "Gmail (Google Workspace)",
    "note": "All staff moving to Google Workspace. Need full assessment per migration scenario.",
    "migrations": [
        {
            "id": "MIG-001",
            "staff_name": "Alice Chen",
            "department": "Litigation",
            "source_provider": "Yahoo Mail",
            "account_type": "free",
            "notes_from_user": "Uses 2FA. Has many custom folders."
        },
        {
            "id": "MIG-002",
            "staff_name": "Bob Patel",
            "department": "Corporate",
            "source_provider": "Zoho Mail",
            "account_type": "business",
            "notes_from_user": "Standard account, no issues reported."
        },
        {
            "id": "MIG-003",
            "staff_name": "Carol Russo",
            "department": "IP",
            "source_provider": "ProtonMail",
            "account_type": "free",
            "notes_from_user": "Wants all email preserved. Prefers automated approach."
        },
        {
            "id": "MIG-004",
            "staff_name": "Dan Whitmore",
            "department": "Finance",
            "source_provider": "iCloud Mail",
            "account_type": "personal",
            "notes_from_user": "Apple device user. Standard setup."
        },
        {
            "id": "MIG-005",
            "staff_name": "Eve Tanaka",
            "department": "HR",
            "source_provider": "Zoho Mail",
            "account_type": "business",
            "notes_from_user": "Large mailbox, approx 18GB."
        },
        {
            "id": "MIG-006",
            "staff_name": "Frank O'Brien",
            "department": "IT",
            "source_provider": "Yahoo Mail",
            "account_type": "free",
            "notes_from_user": "Has subfolders for every client matter."
        },
        {
            "id": "MIG-007",
            "staff_name": "Gina Marsh",
            "department": "Paralegal",
            "source_provider": "ProtonMail",
            "account_type": "paid",
            "notes_from_user": "Paying ProtonMail subscriber."
        }
    ]
}

raw_input_path = os.path.join(workspace, "it_projects/email_consolidation/migration_requests_raw.json")
with open(raw_input_path, "w") as f:
    json.dump(migration_requests_raw, f, indent=2)

print(f"Workspace created at: {workspace}")
print(f"Raw migration requests written to: {raw_input_path}")
print("Distractor files created.")