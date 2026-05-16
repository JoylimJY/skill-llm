import os
import random
import json
import yaml

random.seed(42)

BASE = "/workspace"

# --- Create realistic, deeply nested directory structure with distractor files ---

dirs = [
    "emr_source/schemas",
    "emr_source/sample_data",
    "emr_source/access_notes",
    "warehouse/staging",
    "warehouse/production",
    "warehouse/audit_logs",
    "infra/terraform/modules",
    "infra/monitoring",
    "docs/legacy",
    "docs/meeting_notes",
    "scripts/ingestion",
    "scripts/transforms",
    "scripts/utils",
    "reports/q1",
    "reports/q2",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---

# 1. Legacy ETL design (wrong format, missing stages)
with open(os.path.join(BASE, "docs/legacy/old_etl_notes.txt"), "w") as f:
    f.write("""ETL Notes - 2021
We basically dump the whole patients table nightly.
No dedup logic. Just truncate and reload.
Validation: none. Hope for the best.
Contact: data_team@hospital.internal
""")

# 2. Meeting notes with partial requirements
with open(os.path.join(BASE, "docs/meeting_notes/kickoff_2024.txt"), "w") as f:
    f.write("""Kickoff Meeting - 2024-03-15
Attendees: CTO, Lead Data Engineer, Analytics Manager
Action Items:
- Migrate patient_encounters from OLTP to BigQuery
- Reduce data latency from T+24h to T+4h
- Handle patient deletes (HIPAA requirement)
- Analytics team complains about duplicate rows in encounters table
Open questions:
- What is the SLA for backfill if we need to reprocess 2 years of data?
- How do we handle the EMR rate limits (max 500 req/min on read replica)?
""")

# 3. Terraform infra stubs (distractors)
with open(os.path.join(BASE, "infra/terraform/modules/bigquery.tf"), "w") as f:
    f.write("""resource "google_bigquery_dataset" "warehouse" {
  dataset_id = "patient_analytics"
  location   = "US"
}
""")

# 4. Monitoring config (distractor)
with open(os.path.join(BASE, "infra/monitoring/alerts.yaml"), "w") as f:
    yaml.dump({
        "alerts": [
            {"name": "pipeline_lag", "threshold_minutes": 60, "channel": "pagerduty"},
            {"name": "row_count_drop", "threshold_pct": 5, "channel": "slack"}
        ]
    }, f)

# 5. Incomplete ingestion script (distractor)
with open(os.path.join(BASE, "scripts/ingestion/pull_encounters.py"), "w") as f:
    f.write("""# TODO: implement watermark logic
import psycopg2
import datetime

def pull_encounters(since: datetime.datetime):
    # STUB - not implemented
    raise NotImplementedError("watermark pull not done")
""")

# 6. Broken transform script (distractor)
with open(os.path.join(BASE, "scripts/transforms/normalize_encounters.py"), "w") as f:
    f.write("""# BROKEN - do not use
def normalize(row):
    return row['patient_id'] + row['encounter_dt']  # type error: int + str
""")

# 7. Partial schema JSON (messy, missing fields)
with open(os.path.join(BASE, "emr_source/schemas/encounters_schema_v1.json"), "w") as f:
    json.dump({
        "table": "patient_encounters",
        "columns": [
            {"name": "enc_id", "type": "integer"},
            {"name": "patient_id", "type": "integer"},
            {"name": "visit_type", "type": "varchar(50)"},
            {"name": "admit_dt", "type": "timestamp"},
            {"name": "discharge_dt", "type": "timestamp"},
            {"name": "diagnosis_codes", "type": "varchar(500)", "note": "comma-separated ICD-10"},
            {"name": "attending_physician_id", "type": "integer"},
            {"name": "facility_id", "type": "integer"},
            {"name": "billing_amount", "type": "numeric(12,2)"},
        ],
        "notes": "updated_at column was dropped in v2 migration - tracking changes unclear",
        "approximate_row_count": 14000000,
        "read_replica": "emr-replica.internal:5432",
        "rate_limit": "500 queries/min"
    }, f, indent=2)

# 8. Newer schema with updated_at added back but ambiguous PK
with open(os.path.join(BASE, "emr_source/schemas/encounters_schema_v2.json"), "w") as f:
    json.dump({
        "table": "patient_encounters",
        "version": "2.1",
        "columns": [
            {"name": "enc_id", "type": "integer", "note": "internal auto-increment, may be reused after archival"},
            {"name": "patient_id", "type": "integer"},
            {"name": "visit_type", "type": "varchar(50)"},
            {"name": "admit_dt", "type": "timestamp"},
            {"name": "discharge_dt", "type": "timestamp", "nullable": True},
            {"name": "diagnosis_codes", "type": "varchar(500)"},
            {"name": "attending_physician_id", "type": "integer"},
            {"name": "facility_id", "type": "integer"},
            {"name": "billing_amount", "type": "numeric(12,2)"},
            {"name": "updated_at", "type": "timestamp", "note": "set on INSERT and UPDATE"},
            {"name": "is_deleted", "type": "boolean", "note": "soft delete flag, set to true when record logically removed"},
            {"name": "record_version", "type": "integer", "note": "increments on each UPDATE"},
        ],
        "candidate_keys": ["enc_id", "(patient_id, admit_dt, facility_id)"],
        "approximate_row_count": 14000000,
        "daily_new_or_updated": 35000,
        "read_replica": "emr-replica-v2.internal:5432",
        "rate_limit": "500 queries/min",
        "hard_delete_policy": "never - soft deletes only via is_deleted flag"
    }, f, indent=2)

# 9. Sample raw data (messy CSV with duplicates and a deleted record)
with open(os.path.join(BASE, "emr_source/sample_data/encounters_sample.csv"), "w") as f:
    f.write("""enc_id,patient_id,visit_type,admit_dt,discharge_dt,diagnosis_codes,attending_physician_id,facility_id,billing_amount,updated_at,is_deleted,record_version
1001,5001,INPATIENT,2024-01-10 08:00:00,2024-01-13 14:00:00,"Z00.00,J18.9",201,3,4520.00,2024-01-13 15:00:00,false,1
1001,5001,INPATIENT,2024-01-10 08:00:00,2024-01-13 14:00:00,"Z00.00,J18.9",201,3,4520.00,2024-01-13 15:00:00,false,1
1002,5002,OUTPATIENT,2024-01-11 09:30:00,,E11.9,202,3,310.00,2024-01-11 09:30:00,false,1
1003,5001,EMERGENCY,2024-01-15 23:00:00,2024-01-16 02:00:00,"S00.01,R07.9",203,1,8900.00,2024-01-16 03:00:00,false,2
1004,5003,INPATIENT,2024-01-05 07:00:00,2024-01-08 11:00:00,C34.10,201,2,12000.00,2024-01-20 10:00:00,true,3
""")

# 10. Access notes
with open(os.path.join(BASE, "emr_source/access_notes/replica_constraints.txt"), "w") as f:
    f.write("""EMR Read Replica Constraints (as of 2024-Q1)
- Max concurrent connections: 10
- Rate limit enforced at app layer: 500 queries/min
- Replication lag: typically 5-30 seconds, spikes to 120s during batch windows
- Available window for bulk extraction: 01:00-04:00 UTC (off-peak)
- No CDC (Debezium/binlog) access available - network policy blocks it
- Full table scan on patient_encounters: ~18 minutes at current size
""")

# 11. Warehouse audit log stub
with open(os.path.join(BASE, "warehouse/audit_logs/load_history.jsonl"), "w") as f:
    for i in range(5):
        f.write(json.dumps({
            "batch_id": f"2024-01-{10+i:02d}",
            "status": "SUCCESS" if i != 3 else "PARTIAL",
            "rows_extracted": 34000 + random.randint(-500, 500),
            "rows_loaded": 34000 + random.randint(-500, 500),
            "duration_seconds": 420 + random.randint(-30, 60)
        }) + "\n")

# 12. Q1 report (distractor)
with open(os.path.join(BASE, "reports/q1/analytics_complaints.txt"), "w") as f:
    f.write("""Q1 Analytics Issues Report
- Duplicate encounter rows in BI dashboard (Tableau): ~0.3% of records
- Missing encounters for patient 5003 in Jan cohort (appears deleted in source?)
- Billing totals off by ~$2,400 vs finance system for week of Jan 15
- Data team suspects pipeline re-runs cause double inserts
""")

# 13. Staging table DDL stub (distractor)
with open(os.path.join(BASE, "warehouse/staging/stg_encounters.sql"), "w") as f:
    f.write("""-- STUB - not finalized
CREATE TABLE IF NOT EXISTS stg_encounters (
    enc_id INT64,
    patient_id INT64,
    -- TODO: add all columns
    _load_ts TIMESTAMP
);
""")

# 14. Utility script stub
with open(os.path.join(BASE, "scripts/utils/checksum_util.py"), "w") as f:
    f.write("""# Utility: row-level MD5 checksum
import hashlib

def row_checksum(row_dict):
    canonical = '|'.join(str(row_dict[k]) for k in sorted(row_dict.keys()))
    return hashlib.md5(canonical.encode()).hexdigest()
""")

# 15. SLA requirements doc
with open(os.path.join(BASE, "docs/sla_requirements.txt"), "w") as f:
    f.write("""Data Warehouse SLA Requirements - Patient Encounters
- Data freshness: T+4h (data available in warehouse within 4 hours of EMR update)
- Backfill window: must support replaying 24 months of history within 72 hours
- Duplicate tolerance: zero - any duplicate enc_id in final table is a P1 incident
- Delete handling: deleted patients must not appear in analytics (HIPAA)
- Row count reconciliation: alert if warehouse count differs from source by >1%
- Pipeline retry: failed batches must be safely re-runnable without double-counting
""")

print("Workspace generated successfully.")
print(f"Files created in: {BASE}")