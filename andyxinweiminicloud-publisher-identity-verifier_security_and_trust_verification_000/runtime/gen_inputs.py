import os
import json
import random

random.seed(42)

base = "/workspace"

# --- Directory structure with distractors ---
dirs = [
    "publishers",
    "publishers/raw",
    "publishers/raw/metadata",
    "marketplace/registry",
    "marketplace/approvals",
    "marketplace/approvals/pending",
    "marketplace/approvals/rejected",
    "security/audits",
    "security/audits/2024",
    "security/audits/2025",
    "security/policies",
    "internal/skills",
    "internal/skills/approved",
    "internal/skills/quarantine",
    "logs",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "marketplace/registry/skill_catalog.json": json.dumps({
        "version": "3.1",
        "skills": ["data-formatter", "api-bridge", "log-analyzer", "ml-pipeline-co/model-trainer"],
        "last_updated": "2025-06-01"
    }, indent=2),
    "marketplace/approvals/pending/batch_20250610.txt": "devtoolz-inc/csv-formatter\nml-pipeline-co/model-trainer\nanthropIc/reasoning-engine\n",
    "marketplace/approvals/rejected/notes.txt": "Rejected: missing attestation, see security/policies/P-109.md\n",
    "security/policies/signing_policy.txt": "All skills must be signed. Key rotation must be announced 30 days in advance. Attestation chain must be verifiable.\n",
    "security/audits/2024/q4_summary.txt": "Q4 2024: 3 publishers flagged for missing cross-platform presence. Follow-up pending.\n",
    "security/audits/2025/open_items.txt": "Open: anthroplc, ml-pipeline-co — awaiting identity report from security team.\n",
    "internal/skills/approved/approved_list.csv": "skill_id,publisher,approved_date\ncsv-formatter,devtoolz-inc,2024-03-15\ndata-normalizer,devtoolz-inc,2024-08-22\n",
    "internal/skills/quarantine/README_DO_NOT_DEPLOY.txt": "Skills in quarantine pending publisher identity verification. Do not deploy.\n",
    "logs/ingestion_2025-06-09.log": "[INFO] Ingestion pipeline started\n[WARN] Publisher 'anthroplc' identity not verified\n[WARN] Publisher 'ml-pipeline-co' anomalous key rotation detected\n[ERROR] Pipeline halted — awaiting security team sign-off\n",
    "tmp/scratch.txt": "TODO: run publisher identity checks before Monday standup\n",
    "security/audits/2025/flagged_publishers.json": json.dumps([
        {"publisher": "anthroplc", "reason": "possible impersonation", "flagged_by": "automated-scanner"},
        {"publisher": "ml-pipeline-co", "reason": "key rotation anomaly", "flagged_by": "automated-scanner"},
        {"publisher": "devtoolz-inc", "reason": "none", "flagged_by": "automated-scanner"}
    ], indent=2),
}

for path, content in distractor_files.items():
    full_path = os.path.join(base, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- Publisher 1: devtoolz-inc (VERIFIED) ---
# Clean history, annual key rotation, multi-platform, valid credentials
publisher1 = {
    "publisher_id": "devtoolz-inc",
    "display_name": "DevToolz Inc.",
    "account_created": "2022-11-03",
    "account_age_months": 31,
    "skills": [
        {"name": "csv-formatter", "published": "2023-01-10", "category": "developer-tools"},
        {"name": "data-normalizer", "published": "2023-04-18", "category": "developer-tools"},
        {"name": "log-parser", "published": "2023-09-05", "category": "developer-tools"},
        {"name": "json-schema-validator", "published": "2024-02-14", "category": "developer-tools"},
        {"name": "yaml-linter", "published": "2024-07-20", "category": "developer-tools"},
    ],
    "total_downloads": 18400,
    "signing_keys": [
        {"key_id": "DT-KEY-001", "created": "2022-11-03", "revoked": "2023-11-10", "rotation_announcement": "2023-10-28"},
        {"key_id": "DT-KEY-002", "created": "2023-11-10", "revoked": "2024-11-15", "rotation_announcement": "2024-11-01"},
        {"key_id": "DT-KEY-003", "created": "2024-11-15", "revoked": None, "rotation_announcement": "2024-11-01"},
    ],
    "platforms": {
        "marketplace": True,
        "code_repository": "https://github.com/devtoolz-inc",
        "community_forum": "https://community.devtoolz.io",
        "social_presence": "https://twitter.com/devtoolzinc"
    },
    "credentials": {
        "email_verified": True,
        "repository_attestation": True,
        "signing_key_transparency_log": True,
        "credential_expiry": "2026-11-15"
    },
    "known_publishers_to_check_against": ["anthropic", "devtools-inc", "devtoolz"]
}

# --- Publisher 2: anthroplc (SUSPICIOUS — impersonation) ---
# Typo-squat of "anthropic", also has Cyrillic 'с' in display name, thin cross-platform, no attestation
# Display name uses Cyrillic 'с' (U+0441) replacing Latin 'c' in "Anthropic"
publisher2 = {
    "publisher_id": "anthroplc",
    "display_name": "Anthropi\u0441",   # Cyrillic с replacing Latin c
    "account_created": "2025-01-20",
    "account_age_months": 5,
    "skills": [
        {"name": "reasoning-engine", "published": "2025-02-10", "category": "ai-models"},
        {"name": "claude-wrapper", "published": "2025-03-05", "category": "ai-models"},
        {"name": "llm-bridge", "published": "2025-04-18", "category": "ai-models"},
    ],
    "total_downloads": 890,
    "signing_keys": [
        {"key_id": "ALP-KEY-001", "created": "2025-01-20", "revoked": None, "rotation_announcement": None},
    ],
    "platforms": {
        "marketplace": True,
        "code_repository": None,
        "community_forum": None,
        "social_presence": None
    },
    "credentials": {
        "email_verified": True,
        "repository_attestation": False,
        "signing_key_transparency_log": False,
        "credential_expiry": None
    },
    "known_publishers_to_check_against": ["anthropic", "anthropIc", "anthr0pic", "anthropic-inc"]
}

# --- Publisher 3: ml-pipeline-co (SUSPICIOUS — key rotation anomaly + topic shift) ---
# Months 1-10: ML data preprocessing tools. Month 11: suddenly publishes "wallet-audit" and "crypto-validator"
# Key rotated 1 day before the controversial crypto skills were published, no announcement
publisher3 = {
    "publisher_id": "ml-pipeline-co",
    "display_name": "ML Pipeline Co.",
    "account_created": "2024-05-01",
    "account_age_months": 13,
    "skills": [
        {"name": "feature-extractor", "published": "2024-05-15", "category": "ml-preprocessing"},
        {"name": "data-pipeline-builder", "published": "2024-06-20", "category": "ml-preprocessing"},
        {"name": "tensor-normalizer", "published": "2024-07-08", "category": "ml-preprocessing"},
        {"name": "batch-loader", "published": "2024-08-14", "category": "ml-preprocessing"},
        {"name": "model-trainer", "published": "2024-09-22", "category": "ml-preprocessing"},
        {"name": "hyperparameter-tuner", "published": "2024-10-30", "category": "ml-preprocessing"},
        {"name": "wallet-audit-tool", "published": "2025-04-17", "category": "crypto-finance"},
        {"name": "crypto-validator", "published": "2025-04-19", "category": "crypto-finance"},
    ],
    "total_downloads": 5600,
    "signing_keys": [
        {"key_id": "MLP-KEY-001", "created": "2024-05-01", "revoked": "2025-04-16", "rotation_announcement": None},
        {"key_id": "MLP-KEY-002", "created": "2025-04-16", "revoked": None, "rotation_announcement": None},
    ],
    "platforms": {
        "marketplace": True,
        "code_repository": None,
        "community_forum": None,
        "social_presence": None
    },
    "credentials": {
        "email_verified": True,
        "repository_attestation": False,
        "signing_key_transparency_log": False,
        "credential_expiry": "2025-05-01"
    },
    "known_publishers_to_check_against": ["ml-pipelines", "mlpipeline-co", "ml-pipeline"]
}

for pub_data in [publisher1, publisher2, publisher3]:
    pid = pub_data["publisher_id"]
    path = os.path.join(base, "publishers", "raw", f"{pid}.json")
    with open(path, "w") as f:
        json.dump(pub_data, f, indent=2)

# Also write a metadata index
index = {
    "pending_review": ["devtoolz-inc", "anthroplc", "ml-pipeline-co"],
    "review_requested_by": "marketplace-ingestion-pipeline",
    "review_deadline": "2025-06-13",
    "output_format": "One report file per publisher"
}
with open(os.path.join(base, "publishers", "raw", "metadata", "review_index.json"), "w") as f:
    json.dump(index, f, indent=2)

print("Workspace generated successfully.")