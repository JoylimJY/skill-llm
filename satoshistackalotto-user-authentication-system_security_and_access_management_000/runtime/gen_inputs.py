#!/usr/bin/env python3
"""
Generate the initial sandbox workspace for the authentication system task.
"""
import os
import json
import random
import stat
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")
DATA_DIR = Path("/data")

# ---- Create OPENCLAW_DATA_DIR structure ----
auth_dir = DATA_DIR / "auth"
(auth_dir / "users").mkdir(parents=True, exist_ok=True)
(auth_dir / "roles").mkdir(parents=True, exist_ok=True)
(auth_dir / "roles" / "custom").mkdir(parents=True, exist_ok=True)
(auth_dir / "access").mkdir(parents=True, exist_ok=True)
(auth_dir / "logs" / "logins").mkdir(parents=True, exist_ok=True)
(auth_dir / "logs" / "access").mkdir(parents=True, exist_ok=True)
(auth_dir / "logs" / "admin").mkdir(parents=True, exist_ok=True)
(auth_dir / "logs" / "security").mkdir(parents=True, exist_ok=True)

# ---- Create role definition files ----
roles = {
    "senior_accountant": {
        "name": "senior_accountant",
        "description": "Senior accountant - full system access",
        "level": 4,
        "inherits": "accountant",
        "permissions": [
            "all_client_access", "user_management", "role_assignment",
            "system_configuration", "data_export_all", "compliance_override",
            "audit_log_access", "gdpr_operations", "billing_management",
            "skill_configuration"
        ],
        "client_access": "all"
    },
    "accountant": {
        "name": "accountant",
        "description": "Accountant - broad access to assigned clients",
        "level": 3,
        "inherits": "assistant",
        "permissions": [
            "client_data_full_access", "tax_filing_submit", "tax_optimization",
            "compliance_management", "financial_reporting", "efka_submissions",
            "banking_reconciliation", "deadline_management", "client_communication"
        ],
        "client_access": "assigned_only",
        "restrictions": ["cannot_manage_users", "cannot_change_system_config"]
    },
    "assistant": {
        "name": "assistant",
        "description": "Accountant assistant - operational access",
        "level": 2,
        "inherits": "viewer",
        "permissions": [
            "document_upload", "document_processing", "data_entry",
            "email_processing", "dashboard_access", "basic_reporting",
            "client_data_edit_basic", "alert_acknowledgement", "ocr_processing"
        ],
        "client_access": "assigned_only",
        "restrictions": [
            "cannot_submit_tax_filings",
            "cannot_export_sensitive_data",
            "cannot_modify_financial_records"
        ]
    },
    "viewer": {
        "name": "viewer",
        "description": "Read-only access to assigned client data",
        "level": 1,
        "permissions": [
            "dashboard_view", "client_data_view", "report_view",
            "deadline_view", "document_view"
        ],
        "client_access": "assigned_only",
        "restrictions": ["read_only", "no_data_modification", "no_data_export"]
    }
}

for role_name, role_data in roles.items():
    role_path = auth_dir / "roles" / f"{role_name}.json"
    with open(role_path, "w") as f:
        json.dump(role_data, f, indent=2)

# ---- Create existing senior_accountant user (admin) ----
admin_username = "nikos.p"
admin_dir = auth_dir / "users" / admin_username
(admin_dir / "sessions").mkdir(parents=True, exist_ok=True)
(admin_dir / "2fa").mkdir(parents=True, exist_ok=True)

admin_profile = {
    "username": admin_username,
    "full_name": "Nikos Papadopoulos",
    "email": "nikos@logistiki-firm.gr",
    "role": "senior_accountant",
    "status": "active",
    "created_at": "2024-01-15T09:00:00+02:00",
    "created_by": "system",
    "password_change_required": False,
    "2fa_enabled": True
}

admin_credentials = {
    "password_hash": "$2b$12$abc123fakehashfortestingpurposesonly",
    "password_set_at": "2024-01-15T09:00:00+02:00",
    "password_change_required": False
}

admin_permissions = {
    "role": "senior_accountant",
    "custom": []
}

# Simulate an active session for admin
admin_session_token = "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
admin_session = {
    "session_id": admin_session_token,
    "username": admin_username,
    "created_at": "2025-06-10T10:00:00+02:00",
    "expires_at": "2025-06-10T18:00:00+02:00",
    "last_activity": "2025-06-10T10:30:00+02:00",
    "device_info": {"browser": "internal-cli", "os": "linux"},
    "ip_address": "192.168.1.10",
    "role": "senior_accountant",
    "client_access": "all"
}

with open(admin_dir / "profile.json", "w") as f:
    json.dump(admin_profile, f, indent=2)
with open(admin_dir / "credentials.json", "w") as f:
    json.dump(admin_credentials, f, indent=2)
with open(admin_dir / "permissions.json", "w") as f:
    json.dump(admin_permissions, f, indent=2)
with open(admin_dir / f"sessions/{admin_session_token}.json", "w") as f:
    json.dump(admin_session, f, indent=2)

# ---- Create client_assignments.json with admin having all-client access ----
client_assignments = {
    admin_username: {
        "all_clients": True,
        "clients": []
    }
}
with open(auth_dir / "access" / "client_assignments.json", "w") as f:
    json.dump(client_assignments, f, indent=2)

# ---- Create policies.json (distractor) ----
policies = {
    "password_policy": {
        "min_length": 12,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special": True,
        "max_age_days": 90,
        "history_count": 5
    },
    "lockout_policy": {
        "max_failed_attempts": 5,
        "lockout_duration_minutes": 30
    },
    "session_policy": {
        "absolute_timeout_hours": 8,
        "idle_timeout_minutes": 15,
        "max_concurrent_sessions": 3
    }
}
with open(auth_dir / "access" / "policies.json", "w") as f:
    json.dump(policies, f, indent=2)

# ---- Create ip_whitelist.json (distractor) ----
ip_whitelist = {
    "enabled": True,
    "allowed_ranges": ["192.168.1.0/24"],
    "action_on_violation": "block_and_alert"
}
with open(auth_dir / "access" / "ip_whitelist.json", "w") as f:
    json.dump(ip_whitelist, f, indent=2)

# ---- Create the onboarding requests file ---- 
# This is the "messy" input the agent needs to process
onboarding_requests = {
    "pending_onboarding": [
        {
            "request_id": "ONB-2025-001",
            "requested_by": "nikos.p",
            "request_date": "2025-06-09",
            "new_staff": {
                "username": "elena.k",
                "full_name": "Elena Kyriakou",
                "email": "elena.k@logistiki-firm.gr",
                "role": "assistant",
                "assigned_clients": ["EL801234567", "EL802345678", "EL803456789"]
            },
            "notes": "Junior hire, starting immediately"
        },
        {
            "request_id": "ONB-2025-002",
            "requested_by": "nikos.p",
            "request_date": "2025-06-09",
            "new_staff": {
                "username": "stavros.m",
                "full_name": "Stavros Mitropoulos",
                "email": "stavros.m@logistiki-firm.gr",
                "role": "accountant",
                "assigned_clients": ["EL804567890", "EL805678901"]
            },
            "notes": "Transfer from Thessaloniki branch"
        }
    ]
}
with open(WORKSPACE / "onboarding_requests.json", "w") as f:
    json.dump(onboarding_requests, f, indent=2)

# ---- Create distractor files in workspace ----
distractor_dir = WORKSPACE / "firm_docs"
distractor_dir.mkdir(exist_ok=True)

# Client registry (distractor)
clients = {}
vats = [
    "EL801234567", "EL802345678", "EL803456789",
    "EL804567890", "EL805678901", "EL806789012",
    "EL807890123", "EL808901234"
]
company_names = [
    "Alpha Imports SA", "Beta Constructions", "Gamma Foods MONOPROSOPOS",
    "Delta Services LLC", "Epsilon Travel", "Zeta Shipping",
    "Eta Medical AMKE", "Theta IT Solutions"
]
for vat, name in zip(vats, company_names):
    clients[vat] = {"company_name": name, "vat": vat, "active": True}

with open(distractor_dir / "client_registry.json", "w") as f:
    json.dump(clients, f, indent=2)

# Old user template (distractor — wrong format)
old_template = {
    "user": "template",
    "permissions": "all",  # Wrong format - should be list
    "active": 1  # Wrong format - should be bool
}
with open(distractor_dir / "old_user_template.json", "w") as f:
    json.dump(old_template, f, indent=2)

# Random accounting data distractors
(distractor_dir / "tax_periods").mkdir(exist_ok=True)
for year in [2023, 2024]:
    with open(distractor_dir / "tax_periods" / f"vat_deadlines_{year}.json", "w") as f:
        json.dump({"year": year, "q1": "2025-04-25", "q2": "2025-07-25"}, f, indent=2)

(distractor_dir / "compliance_reports").mkdir(exist_ok=True)
with open(distractor_dir / "compliance_reports" / "june_2025_summary.json", "w") as f:
    json.dump({"period": "2025-06", "total_filings": 47, "pending": 3}, f, indent=2)

# Incomplete auth attempt log (distractor)
with open(distractor_dir / "failed_setup_notes.txt", "w") as f:
    f.write("Previous setup attempt failed - missing credentials\n")
    f.write("TODO: Set up elena.k and stavros.m accounts\n")
    f.write("Remember to lock down the auth directory after setup\n")

# Stale config (distractor)
stale_config = {
    "data_dir": "/var/openclaw",  # Wrong path
    "auth_backend": "ldap",  # Wrong - should be local
    "version": "0.9.0"
}
with open(distractor_dir / "stale_config.json", "w") as f:
    json.dump(stale_config, f, indent=2)

# More distractors
(distractor_dir / "templates").mkdir(exist_ok=True)
with open(distractor_dir / "templates" / "invoice_template.json", "w") as f:
    json.dump({"type": "invoice", "currency": "EUR", "vat_rate": 0.24}, f, indent=2)

with open(distractor_dir / "templates" / "payroll_template.json", "w") as f:
    json.dump({"type": "payroll", "ikp_rate": 0.2222, "efka_rate": 0.1356}, f, indent=2)

with open(WORKSPACE / "system_notes.txt", "w") as f:
    f.write("OpenClaw system - Logistiki Firm\n")
    f.write("Environment: OPENCLAW_DATA_DIR=/data\n")
    f.write("Admin contact: nikos.p\n")

print("Workspace generated successfully.")
print(f"Workspace: {WORKSPACE}")
print(f"Data dir: {DATA_DIR}")