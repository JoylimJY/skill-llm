import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Create a deeply nested distractor directory structure ---
dirs = [
    "data_platform/ddl/archive",
    "data_platform/ddl/deprecated",
    "data_platform/etl/scripts",
    "data_platform/etl/configs",
    "data_platform/docs/design",
    "data_platform/docs/meetings",
    "data_platform/monitoring/alerts",
    "data_platform/monitoring/dashboards",
    "data_platform/access_control/roles",
    "data_platform/access_control/policies",
    "data_platform/tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files (wrong/old DDLs, configs, notes) ---
distractor_files = {
    "data_platform/ddl/archive/old_user_table_v1.sql": """\
-- DEPRECATED: Do not use this schema
CREATE TABLE user_log (
    user_id INT,
    action VARCHAR(255),
    log_time TIMESTAMP
);
""",
    "data_platform/ddl/archive/dws_ord_merchant_stats.sql": """\
-- Old merchant stats table - wrong format
CREATE TABLE prod_workspace.dws_ord_merchant_sales (
    merchant_id BIGINT,
    total_sales DOUBLE
)
STORED AS PARQUET;
""",
    "data_platform/ddl/deprecated/ads_mkt_campaign_report_df.sql": """\
-- ads layer example (deprecated style, no lifecycle)
CREATE TABLE prod_workspace.ads_mkt_campaign_report_df (
    campaign_id BIGINT COMMENT '活动ID',
    click_cnt BIGINT COMMENT '点击数'
)
COMMENT '营销活动报告'
PARTITIONED BY (ds STRING)
STORED AS ALIORC;
""",
    "data_platform/etl/scripts/user_behavior_loader.py": """\
# ETL loader for user behavior data
# Reads from Kafka, writes to ODS layer
import json

def load_events(topic, batch_size=1000):
    # placeholder
    pass
""",
    "data_platform/etl/configs/kafka_config.yaml": """\
bootstrap_servers: kafka-cluster:9092
topics:
  - user_click_events
  - user_browse_events
group_id: etl_consumer_group
""",
    "data_platform/docs/design/dwd_layer_design_v2.md": """\
# DWD Layer Design Notes (DRAFT)

## User Behavior Log
- Source: Kafka click stream
- Grain: one row per user action
- Refresh: every hour
- Fields: user_id, session_id, event_type, page_url, duration_sec

NOTE: Table naming TBD, waiting for standards doc confirmation.
""",
    "data_platform/docs/meetings/2024-03-meeting-notes.txt": """\
Meeting Notes - Data Platform Sync
Date: 2024-03-15

Action items:
- [ ] Create DWD user behavior hourly table for test environment
- [ ] Define partitioning strategy
- [ ] Set appropriate data retention policy (team said ~6 months for DWD)
- [ ] Assign ownership to analytics team
""",
    "data_platform/monitoring/alerts/data_freshness_rules.json": """\
{
    "rules": [
        {"table": "dwd_usr_*", "max_delay_hours": 2},
        {"table": "dws_ord_*", "max_delay_hours": 6}
    ]
}
""",
    "data_platform/monitoring/dashboards/table_health.json": """\
{
    "dashboards": [
        {"name": "DWD Layer Health", "refresh": "1h"},
        {"name": "DWS Layer Health", "refresh": "6h"}
    ]
}
""",
    "data_platform/access_control/roles/analyst_roles.yaml": """\
roles:
  - name: data_analyst
    permissions:
      - SELECT on prod_workspace.*
      - SELECT on test_workspace.*
""",
    "data_platform/access_control/policies/retention_policy.md": """\
# Data Retention Policy

| Layer | Min TTL | Max TTL |
|-------|---------|---------|
| ODS   | 30d     | 90d     |
| DWD   | 180d    | 365d    |
| DWS   | 365d    | 730d    |
| ADS   | 90d     | 365d    |
| DIM   | 365d    | -       |
""",
    "data_platform/tmp/scratch_notes.txt": """\
Possible table name ideas (NOT finalized):
- test_workspace.dwd_usr_user_click_log_hourly
- test_workspace.dwd_log_user_behavior_h
- user_click_log_test

Fields needed (rough list):
user_id, session_id, event_type, item_id, page_name, duration_sec, client_ip, user_agent, timestamp
""",
}

for rel_path, content in distractor_files.items():
    full_path = WORKSPACE / rel_path
    full_path.write_text(content, encoding="utf-8")

# --- The problem statement: a requirements brief (messy, incomplete) ---
requirements_brief = """\
# User Behavior Click Log Table - Requirements Brief

## Business Context
The analytics team needs to track real-time user click and browse behavior on our e-commerce platform.
Data arrives from Kafka every hour and should be ingested incrementally.

## Environment
- Target environment: TEST (for validation before promotion to prod)

## Data Layer
- This is cleaned, structured event data (detail-level, after deduplication and field enrichment)

## Update Frequency
- Refresh every HOUR
- Each run loads only NEW records (incremental)

## Required Fields
| Field (English)   | Chinese Name     | Type            | Notes                        |
|-------------------|------------------|-----------------|------------------------------|
| user_id           | 用户ID           | BIGINT          |                              |
| session_id        | 会话ID           | STRING          |                              |
| event_type        | 事件类型         | STRING          | click/browse/search etc      |
| item_id           | 商品ID           | BIGINT          |                              |
| page_name         | 页面名称         | STRING          |                              |
| duration_sec      | 页面停留秒数     | BIGINT          |                              |
| client_ip         | 客户端IP         | STRING          |                              |
| event_time        | 事件发生时间     | DATETIME        |                              |

## Data Domain
- This belongs to the USER behavior domain (log data, but primary subject is user)

## Retention
- Team agreement: keep for approximately 6 months (standard for this layer)

## Output
Please produce the DDL SQL file named: `dwd_usr_user_click_log_hinc.sql`
Store it somewhere in the workspace.
"""

(WORKSPACE / "data_platform/docs/design/requirements_brief.md").write_text(
    requirements_brief, encoding="utf-8"
)

print("Workspace scaffold generated successfully.")
print(f"Files created in: {WORKSPACE}")