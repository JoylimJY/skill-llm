#!/usr/bin/env python3
"""
Generates the sandbox workspace for the lead-storage evaluation task.
"""
import json
import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))

# ── Directory structure ────────────────────────────────────────────────────────
dirs = [
    "references",
    "agent",
    "agent/handlers",
    "agent/utils",
    "broker_inbox",
    "broker_inbox/raw",
    "broker_inbox/processed",
    "config",
    "logs",
    "storage",
    "tests",
    "tests/fixtures",
    "docs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────────
distractors = {
    "config/app_config.yaml": "environment: production\ndebug: false\nlog_level: INFO\n",
    "config/db_conn.ini": "[database]\nhost=localhost\nport=5432\ndbname=leads_prod\n",
    "docs/onboarding.md": "# CRE Brokerage Onboarding\nWelcome to the platform.\n",
    "docs/api_overview.txt": "Internal API overview — see Confluence for details.\n",
    "logs/app.log": "2024-01-10 09:00:00 INFO  Service started\n2024-01-10 09:01:00 INFO  Listening on :8080\n",
    "logs/errors.log": "",
    "agent/utils/helpers.py": "# Utility helpers\ndef noop(): pass\n",
    "agent/utils/validators.py": "# Field validators placeholder\n",
    "agent/handlers/__init__.py": "",
    "agent/__init__.py": "",
    "tests/fixtures/sample_lead.json": json.dumps({"lead_id": "SAMPLE-001", "broker_name": "Test Broker"}, indent=2),
    "broker_inbox/processed/.gitkeep": "",
    "storage/.gitkeep": "",
}
for rel_path, content in distractors.items():
    (WORKSPACE / rel_path).write_text(content)

# ── CORE ARTIFACT 1: storage-input.schema.json ────────────────────────────────
storage_input_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "LeadStorageInput",
    "type": "object",
    "required": ["confirmation_token", "leads"],
    "properties": {
        "confirmation_token": {
            "type": "string",
            "minLength": 1,
            "description": "Non-empty token issued by Supervisor confirming write authorization."
        },
        "leads": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["lead_id", "broker_name", "contact_phone", "property_address"],
                "properties": {
                    "lead_id":           {"type": "string"},
                    "broker_name":       {"type": "string"},
                    "contact_phone":     {"type": "string"},
                    "property_address":  {"type": "string"},
                    # extraction metadata (optional)
                    "deal_type":         {"type": "string"},
                    "asset_class":       {"type": "string"},
                    "price_basis":       {"type": "string"},
                    "area_sqft":         {"type": ["number", "null"]},
                    "area_basis":        {"type": "string"},
                    # record typing (optional)
                    "dataset_mode":      {"type": "string"},
                    "record_type":       {"type": "string"},
                    # location (optional)
                    "city":              {"type": "string"},
                    "city_canonical":    {"type": "string"},
                    "locality_canonical":{"type": "string"},
                    "micro_market":      {"type": "string"},
                    "location_hint":     {"type": "string"},
                    # prioritization (optional)
                    "urgency":           {"type": "string"},
                    "priority_bucket":   {"type": "string"}
                },
                "additionalProperties": True
            }
        }
    },
    "additionalProperties": False
}
(WORKSPACE / "references" / "storage-input.schema.json").write_text(
    json.dumps(storage_input_schema, indent=2)
)

# ── CORE ARTIFACT 2: storage-output.schema.json ───────────────────────────────
storage_output_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "LeadStorageOutput",
    "type": "object",
    "required": ["status", "stored_count", "duplicate_count", "records"],
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success", "failure"]
        },
        "stored_count":   {"type": "integer", "minimum": 0},
        "duplicate_count":{"type": "integer", "minimum": 0},
        "records": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["lead_id", "write_status"],
                "properties": {
                    "lead_id":      {"type": "string"},
                    "write_status": {"type": "string", "enum": ["written", "duplicate", "rejected"]},
                    "stored_fields": {
                        "type": "object",
                        "description": "Full copy of the lead fields that were persisted."
                    }
                },
                "additionalProperties": False
            }
        },
        "error_message": {"type": "string"}
    },
    "additionalProperties": False
}
(WORKSPACE / "references" / "storage-output.schema.json").write_text(
    json.dumps(storage_output_schema, indent=2)
)

# ── CORE ARTIFACT 3: The messy input batch from the Supervisor ────────────────
# Scenario:
#   - 5 leads total.
#   - Lead A (CRE-2024-001): valid, full optional metadata.
#   - Lead B (CRE-2024-002): valid, minimal fields.
#   - Lead C (CRE-2024-001): DUPLICATE of Lead A (same lead_id, broker forwarded again).
#   - Lead D (CRE-2024-003): valid, partial optional metadata.
#   - Lead E (CRE-2024-004): MISSING confirmation_token scenario is tested at payload level
#     (we'll create a second payload file with no token).

approved_batch = {
    "confirmation_token": "SVR-CONF-20240315-XK9",
    "leads": [
        {
            "lead_id": "CRE-2024-001",
            "broker_name": "Rajesh Malhotra",
            "contact_phone": "+91-98200-11111",
            "property_address": "Tower 4B, BKC, Mumbai",
            "deal_type": "lease",
            "asset_class": "office",
            "price_basis": "per_sqft_monthly",
            "area_sqft": 12500,
            "area_basis": "carpet",
            "dataset_mode": "live",
            "record_type": "inbound",
            "city": "Mumbai",
            "city_canonical": "mumbai",
            "locality_canonical": "bandra_kurla_complex",
            "micro_market": "BKC North",
            "location_hint": "Near G-Block metro",
            "urgency": "high",
            "priority_bucket": "tier1"
        },
        {
            "lead_id": "CRE-2024-002",
            "broker_name": "Sunita Verma",
            "contact_phone": "+91-99300-22222",
            "property_address": "Plot 12, Whitefield, Bangalore"
        },
        {
            # DUPLICATE — same lead_id as first entry
            "lead_id": "CRE-2024-001",
            "broker_name": "Rajesh Malhotra",
            "contact_phone": "+91-98200-11111",
            "property_address": "Tower 4B, BKC, Mumbai",
            "deal_type": "lease",
            "asset_class": "office"
        },
        {
            "lead_id": "CRE-2024-003",
            "broker_name": "Amit Desai",
            "contact_phone": "+91-98700-33333",
            "property_address": "Sector 62, Noida",
            "city": "Noida",
            "city_canonical": "noida",
            "priority_bucket": "tier2",
            "urgency": "medium",
            "dataset_mode": "live",
            "record_type": "inbound"
        },
        {
            "lead_id": "CRE-2024-004",
            "broker_name": "Priya Nair",
            "contact_phone": "+91-97500-44444",
            "property_address": "Hiranandani Gardens, Powai, Mumbai",
            "deal_type": "sale",
            "asset_class": "retail",
            "area_sqft": 3200,
            "area_basis": "built_up",
            "city": "Mumbai",
            "city_canonical": "mumbai",
            "locality_canonical": "powai",
            "micro_market": "Hiranandani",
            "urgency": "low",
            "priority_bucket": "tier3"
        }
    ]
}
(WORKSPACE / "broker_inbox" / "approved_batch.json").write_text(
    json.dumps(approved_batch, indent=2)
)

# Second payload: missing confirmation_token — agent must handle gracefully
no_token_batch = {
    "confirmation_token": "",
    "leads": [
        {
            "lead_id": "CRE-2024-005",
            "broker_name": "Farhan Sheikh",
            "contact_phone": "+91-96600-55555",
            "property_address": "Magarpatta City, Pune"
        }
    ]
}
(WORKSPACE / "broker_inbox" / "unconfirmed_batch.json").write_text(
    json.dumps(no_token_batch, indent=2)
)

# ── Additional distractor files ────────────────────────────────────────────────
(WORKSPACE / "broker_inbox" / "raw" / "broker_whatsapp_dump.txt").write_text(
    "Rajesh: Hi I have a great property in BKC, 12500 sqft, interested?\n"
    "Sunita: Whitefield plot 12 available for lease, call me.\n"
)
(WORKSPACE / "tests" / "test_validators.py").write_text(
    "# placeholder test file\ndef test_noop(): assert True\n"
)
(WORKSPACE / "agent" / "handlers" / "extraction_handler.py").write_text(
    "# This handles RAW message parsing — NOT lead storage.\n"
    "def parse_raw(msg): raise NotImplementedError\n"
)

print("Workspace generated successfully.")
print(f"Files created under: {WORKSPACE}")