import os
import json
import random

random.seed(42)

BASE = "/workspace"

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "references",
    "leads/raw",
    "leads/processed",
    "pipeline/extractors",
    "pipeline/scorers",
    "pipeline/normalizers",
    "config/env",
    "config/schemas",
    "logs",
    "archive/2023/q4",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── Distractor files ────────────────────────────────────────────────────────
distractors = {
    "leads/raw/crm_export_2024_01.csv": (
        "lead_id,name,location_raw\n"
        "L001,Ravi Sharma,Andheri West\n"
        "L002,Priya Patel,Hinjewadi Phase 2\n"
        "L003,Amit Desai,Baner Road\n"
    ),
    "leads/raw/crm_export_2024_02.csv": (
        "lead_id,name,location_raw\n"
        "L010,Sunita Rao,Wakad\n"
        "L011,Kiran Mehta,Goregaon East\n"
    ),
    "pipeline/extractors/lead_extractor.py": (
        "# Lead extractor stub\ndef extract(raw): return raw\n"
    ),
    "pipeline/scorers/sentiment_priority_scorer.py": (
        "# Scorer stub\ndef score(lead): return lead\n"
    ),
    "pipeline/normalizers/old_normalizer_v0.py": (
        "# Deprecated v0 normalizer - do not use\ndef normalize(x): return x\n"
    ),
    "config/env/staging.env": (
        "ENV=staging\nDEBUG=true\nDB_HOST=localhost\n"
    ),
    "config/env/production.env": (
        "ENV=production\nDEBUG=false\nDB_HOST=prod-db.internal\n"
    ),
    "config/schemas/old_lead_schema_v0.json": json.dumps({
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {"lead_id": {"type": "string"}, "location": {"type": "string"}}
    }, indent=2),
    "logs/normalizer_run_2024_03_12.log": (
        "[INFO] Run started\n[WARN] 3 unresolved aliases\n[INFO] Run complete\n"
    ),
    "archive/2023/q4/leads_archive.json": json.dumps([
        {"lead_id": "A001", "location": "Powai"},
        {"lead_id": "A002", "location": "Kothrud"},
    ], indent=2),
    "pipeline/normalizers/README_DEPRECATED.txt": (
        "Old normalizer retired. Use india-location-normalizer skill.\n"
    ),
}
for path, content in distractors.items():
    full = os.path.join(BASE, path)
    with open(full, "w") as f:
        f.write(content)

# ── SKILL references ────────────────────────────────────────────────────────
# Input schema
input_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "LocationNormalizerInput",
    "type": "object",
    "required": ["leads"],
    "properties": {
        "leads": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["lead_id", "location_raw"],
                "properties": {
                    "lead_id":      {"type": "string"},
                    "location_raw": {"type": "string"}
                },
                "additionalProperties": False
            }
        }
    },
    "additionalProperties": False
}

# Output schema
output_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "LocationNormalizerOutput",
    "type": "object",
    "required": ["results"],
    "properties": {
        "results": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "lead_id",
                    "city",
                    "locality_canonical",
                    "micro_market",
                    "matched_alias",
                    "confidence",
                    "unresolved_flag"
                ],
                "properties": {
                    "lead_id":           {"type": "string"},
                    "city":              {"type": ["string", "null"]},
                    "locality_canonical":{"type": ["string", "null"]},
                    "micro_market":      {"type": ["string", "null"]},
                    "matched_alias":     {"type": "string"},
                    "confidence":        {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "unresolved_flag":   {"type": "boolean"}
                },
                "additionalProperties": False
            }
        }
    },
    "additionalProperties": False
}

# Alias map — the authoritative lookup (india-location-aliases-v1.json)
alias_map = {
    "aliases": [
        # ── Mumbai entries ──
        {
            "city": "Mumbai",
            "locality_canonical": "Santa Cruz",
            "micro_market": "Western Suburbs",
            "aliases": ["Santa Cruz", "Santacruz", "Scruz", "S Cruz", "SantaCruz West", "Santacruz West", "Santacruz (W)"]
        },
        {
            "city": "Mumbai",
            "locality_canonical": "Andheri",
            "micro_market": "Western Suburbs",
            "aliases": ["Andheri", "Andheri West", "Andheri W", "Andheri (W)", "Andheri-West", "Andheri East", "Andheri E", "Andheri (E)", "Andheri-East"]
        },
        {
            "city": "Mumbai",
            "locality_canonical": "Bandra",
            "micro_market": "Western Suburbs",
            "aliases": ["Bandra", "Bandra West", "Bandra W", "Bandra (W)", "Turner Road", "Carter Road", "Pali Hill", "Bandra-West"]
        },
        {
            "city": "Mumbai",
            "locality_canonical": "Khar",
            "micro_market": "Western Suburbs",
            "aliases": ["Khar", "Khar West", "Khar (W)", "Khar Road", "Khar W"]
        },
        {
            "city": "Mumbai",
            "locality_canonical": "Goregaon",
            "micro_market": "Western Suburbs",
            "aliases": ["Goregaon", "Goregaon West", "Goregaon W", "Goregaon (W)", "Goregaon East", "Goregaon E", "Goregaon (E)"]
        },
        {
            "city": "Mumbai",
            "locality_canonical": "Powai",
            "micro_market": "Eastern Suburbs",
            "aliases": ["Powai", "Powai Lake", "IIT Powai", "Hiranandani Powai", "Hiranandani Gardens"]
        },
        {
            "city": "Mumbai",
            "locality_canonical": "Malad",
            "micro_market": "Western Suburbs",
            "aliases": ["Malad", "Malad West", "Malad (W)", "Malad W", "Malad East", "Malad E", "Malad (E)"]
        },
        # ── Pune entries ──
        {
            "city": "Pune",
            "locality_canonical": "Hinjewadi",
            "micro_market": "Rajiv Gandhi IT Park",
            "aliases": ["Hinjewadi", "Hinjawadi", "Hinjewadi Phase 1", "Hinjewadi Phase 2", "Hinjewadi Phase 3", "Hinjewadi Ph 1", "Hinjewadi Ph 2", "Hinjewadi Ph 3", "Hinjawadi Phase 2"]
        },
        {
            "city": "Pune",
            "locality_canonical": "Baner",
            "micro_market": "North Pune",
            "aliases": ["Baner", "Baner Road", "Baner Pashan Link Road", "Baner-Pashan"]
        },
        {
            "city": "Pune",
            "locality_canonical": "Wakad",
            "micro_market": "North Pune",
            "aliases": ["Wakad", "Wakad Road", "Wakad Pune"]
        },
        {
            "city": "Pune",
            "locality_canonical": "Pimpri-Chinchwad",
            "micro_market": "PCMC",
            "aliases": ["PCMC", "Pimpri Chinchwad", "Pimpri-Chinchwad", "Pimpri", "Chinchwad", "Pimpri Chinchwad Municipal Corporation"]
        },
        {
            "city": "Pune",
            "locality_canonical": "Kothrud",
            "micro_market": "West Pune",
            "aliases": ["Kothrud", "Kothrud Pune", "Karve Road", "Karve Nagar"]
        },
        {
            "city": "Pune",
            "locality_canonical": "Viman Nagar",
            "micro_market": "East Pune",
            "aliases": ["Viman Nagar", "Vimannagar", "Viman-Nagar", "Airport Road Pune"]
        },
        # ── Ambiguous entry (intentionally maps to two cities for trap) ──
        # "Balewadi" appears under both Baner micro-market in some listings;
        # we add it as a separate ambiguous entry with TWO canonical records
        {
            "city": "Pune",
            "locality_canonical": "Balewadi",
            "micro_market": "North Pune",
            "aliases": ["Balewadi", "Balewadi High Street"]
        }
    ]
}

with open(os.path.join(BASE, "references/location-normalizer-input.schema.json"), "w") as f:
    json.dump(input_schema, f, indent=2)

with open(os.path.join(BASE, "references/location-normalizer-output.schema.json"), "w") as f:
    json.dump(output_schema, f, indent=2)

with open(os.path.join(BASE, "references/india-location-aliases-v1.json"), "w") as f:
    json.dump(alias_map, f, indent=2)

# ── The messy input leads file the agent must normalize ─────────────────────
# This simulates a real CRM export handed to the agent.
# It contains: exact aliases, token-normalized aliases, ambiguous aliases,
# genuinely unknown locations, and a case where two aliases clash.

messy_leads = {
    "leads": [
        # L001: exact alias match → Bandra / Turner Road
        {"lead_id": "L001", "location_raw": "Turner Road"},
        # L002: exact alias match → Santa Cruz / Scruz
        {"lead_id": "L002", "location_raw": "Scruz"},
        # L003: token-normalized (extra spaces, mixed case) → Andheri
        {"lead_id": "L003", "location_raw": "  andheri  w  "},
        # L004: token-normalized punctuation variant → PCMC → Pimpri-Chinchwad
        {"lead_id": "L004", "location_raw": "P.C.M.C"},
        # L005: exact alias → Hinjewadi Phase 2
        {"lead_id": "L005", "location_raw": "Hinjawadi Phase 2"},
        # L006: Khar - exact alias
        {"lead_id": "L006", "location_raw": "Khar W"},
        # L007: Baner Road - exact alias
        {"lead_id": "L007", "location_raw": "Baner Road"},
        # L008: GENUINELY UNKNOWN - not in alias map → unresolved
        {"lead_id": "L008", "location_raw": "Koramangala"},
        # L009: Carter Road → Bandra
        {"lead_id": "L009", "location_raw": "Carter Road"},
        # L010: Hiranandani Gardens → Powai
        {"lead_id": "L010", "location_raw": "Hiranandani Gardens"},
        # L011: token-normalized fuzzy → Goregaon East
        {"lead_id": "L011", "location_raw": "Goregaon-East"},
        # L012: ambiguous — "Balewadi High Street" is in alias map, unambiguous → Balewadi
        {"lead_id": "L012", "location_raw": "Balewadi High Street"},
        # L013: completely unknown garbage → unresolved
        {"lead_id": "L013", "location_raw": "XYZ Nagar Phase 99"},
    ]
}

with open(os.path.join(BASE, "leads/raw/messy_leads_for_normalization.json"), "w") as f:
    json.dump(messy_leads, f, indent=2)

print("Workspace initialized successfully.")
print(f"Files created under {BASE}/")