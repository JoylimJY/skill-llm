#!/usr/bin/env python3
"""
Generates the messy, realistic sandbox workspace for the conversation-flow-monitor evaluation.
This creates:
  - A 'plugins/' directory with 12 skill/plugin definition files, several missing or malformed YAML front matter
  - A 'operations_manifest.json' describing simulated operations with various failure modes
  - Distractor files: logs, configs, data files to increase realism
"""

import os
import json
import random

random.seed(42)

BASE = "/workspace"

# ── directory structure ───────────────────────────────────────────────────────

dirs = [
    "plugins/core",
    "plugins/experimental",
    "plugins/deprecated",
    "ops/scheduled",
    "ops/adhoc",
    "configs",
    "data/raw",
    "data/processed",
    "archive/2023",
    "archive/2024",
    ".learnings",           # exists but empty — agent must write here
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── helper ────────────────────────────────────────────────────────────────────

def write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)

# ── PLUGIN FILES (the key test fixtures) ─────────────────────────────────────
# Format that a VALID plugin file needs (per SKILL.md):
#   ---
#   name: <value>
#   description: <value>
#   ---
#   ... body content ...

# 1. VALID — has both name and description
write("plugins/core/browser_navigator.md", """\
---
name: browser-navigator
description: Navigates web pages and extracts structured content for downstream processing.
---

# Browser Navigator

Opens URLs, waits for content, and returns structured data.

## Usage
Call with a URL and optional CSS selector.
""")

# 2. VALID — has both name and description
write("plugins/core/file_manager.md", """\
---
name: file-manager
description: Handles file read/write operations with path validation and encoding detection.
---

# File Manager

Safe file I/O with encoding auto-detection.
""")

# 3. INVALID — missing 'description' field entirely
write("plugins/core/scheduler.md", """\
---
name: scheduler
---

# Scheduler Plugin

Schedules recurring tasks using cron expressions.

## Parameters
- cron_expression: standard cron string
- task_id: unique identifier
""")

# 4. INVALID — missing 'name' field entirely
write("plugins/core/memory_cache.md", """\
---
description: In-memory caching layer for frequently accessed data with LRU eviction.
---

# Memory Cache

Provides fast key-value storage during agent sessions.
""")

# 5. INVALID — has NEITHER name nor description (empty front matter)
write("plugins/experimental/vision_parser.md", """\
---
---

# Vision Parser

Experimental OCR and image analysis module.

## Warning
Not production ready.
""")

# 6. INVALID — NO front matter at all (no --- delimiters)
write("plugins/experimental/code_executor.md", """\
# Code Executor

Executes sandboxed Python snippets and returns stdout/stderr.

## Usage
Pass a code string; results returned as dict.
""")

# 7. INVALID — front matter present but 'name' is empty string
write("plugins/experimental/sentiment_analyzer.md", """\
---
name: 
description: Analyzes text sentiment using a local lightweight model, returning polarity scores.
---

# Sentiment Analyzer

Returns positive/negative/neutral classification.
""")

# 8. INVALID — front matter present but 'description' is empty string
write("plugins/deprecated/legacy_http.md", """\
---
name: legacy-http
description: 
---

# Legacy HTTP Client

Deprecated in favor of http_client_v2. Do not use in new workflows.
""")

# 9. VALID — has both name and description (deprecated but valid)
write("plugins/deprecated/old_ocr.md", """\
---
name: old-ocr
description: Legacy OCR module replaced by vision_parser. Kept for backward compatibility.
---

# Old OCR

Uses Tesseract 3. Deprecated.
""")

# 10. INVALID — front matter delimiter only appears once (malformed)
write("plugins/core/http_client_v2.md", """\
---
name: http-client-v2
description: Modern async HTTP client with connection pooling and retry support.

# HTTP Client v2

Production-grade HTTP operations. Replaces legacy_http.
""")

# 11. VALID — perfectly formed
write("plugins/core/data_transformer.md", """\
---
name: data-transformer
description: Transforms raw data between JSON, CSV, and Parquet formats with schema validation.
---

# Data Transformer

Schema-aware format conversion.
""")

# 12. INVALID — name contains only whitespace
write("plugins/experimental/graph_builder.md", """\
---
name:    
description: Builds knowledge graphs from unstructured text using entity extraction.
---

# Graph Builder

NLP-based graph construction.
""")

# ── OPERATIONS MANIFEST ───────────────────────────────────────────────────────
# Each operation has: id, tool_name, params, expected_behavior
# 'expected_behavior' tells us what will happen when executed:
#   "ok" = completes fine
#   "timeout" = will hang beyond timeout
#   "file_not_found" = references non-existent path
#   "network_timeout" = simulated network failure

operations = [
    {
        "id": "op_001",
        "tool_name": "file_manager",
        "params": {"action": "read", "path": "/workspace/data/raw/sensor_readings.csv"},
        "expected_behavior": "file_not_found",
        "description": "Read sensor data from raw data lake"
    },
    {
        "id": "op_002",
        "tool_name": "data_transformer",
        "params": {"action": "convert", "input_format": "json", "output_format": "csv"},
        "expected_behavior": "ok",
        "description": "Convert daily metrics JSON to CSV for reporting"
    },
    {
        "id": "op_003",
        "tool_name": "browser_navigator",
        "params": {"action": "open", "url": "https://internal-dashboard.corp/metrics"},
        "expected_behavior": "timeout",
        "description": "Fetch live metrics from internal dashboard"
    },
    {
        "id": "op_004",
        "tool_name": "http_client_v2",
        "params": {"action": "get", "url": "https://api.weather.service/v1/forecast"},
        "expected_behavior": "network_timeout",
        "description": "Pull weather forecast for scheduling optimization"
    },
    {
        "id": "op_005",
        "tool_name": "memory_cache",
        "params": {"action": "get", "key": "last_run_timestamp"},
        "expected_behavior": "ok",
        "description": "Retrieve cached timestamp of last successful pipeline run"
    },
    {
        "id": "op_006",
        "tool_name": "scheduler",
        "params": {"action": "register", "cron_expression": "0 2 * * *", "task_id": "nightly_etl"},
        "expected_behavior": "ok",
        "description": "Register nightly ETL job"
    },
    {
        "id": "op_007",
        "tool_name": "file_manager",
        "params": {"action": "write", "path": "/workspace/data/processed/output.json"},
        "expected_behavior": "ok",
        "description": "Write transformed data to processed store"
    },
    {
        "id": "op_008",
        "tool_name": "http_client_v2",
        "params": {"action": "post", "url": "https://notify.internal/alerts"},
        "expected_behavior": "network_timeout",
        "description": "Send pipeline completion notification"
    }
]

write("ops/scheduled/operations_manifest.json", json.dumps(operations, indent=2))

# ── DISTRACTOR FILES ──────────────────────────────────────────────────────────

write("configs/pipeline_config.yaml", """\
pipeline:
  name: nightly_etl
  schedule: "0 2 * * *"
  max_retries: 3
  timeout_seconds: 3600

databases:
  primary:
    host: db.internal
    port: 5432
  cache:
    host: redis.internal
    port: 6379
""")

write("configs/logging_config.json", """\
{
  "version": 1,
  "handlers": {
    "file": {"class": "logging.FileHandler", "filename": "pipeline.log"},
    "console": {"class": "logging.StreamHandler"}
  },
  "root": {"level": "INFO", "handlers": ["file", "console"]}
}
""")

write("data/raw/schema_definition.json", """\
{
  "sensor_readings": {
    "fields": ["timestamp", "sensor_id", "value", "unit"],
    "primary_key": "sensor_id",
    "nullable": ["unit"]
  }
}
""")

write("data/processed/.gitkeep", "")

write("archive/2023/pipeline_run_log.txt", """\
2023-11-01 02:00:01 INFO  Pipeline started
2023-11-01 02:00:45 INFO  Fetched 14203 records
2023-11-01 02:01:22 INFO  Transformed to CSV
2023-11-01 02:01:23 INFO  Pipeline completed successfully
""")

write("archive/2024/pipeline_run_log.txt", """\
2024-03-15 02:00:00 INFO  Pipeline started
2024-03-15 02:00:02 ERROR Browser navigation timed out after 60s
2024-03-15 02:00:02 WARN  Falling back to cached metrics
2024-03-15 02:01:55 INFO  Pipeline completed with warnings
""")

write("ops/adhoc/manual_trigger.sh", """\
#!/bin/bash
# Manual pipeline trigger for emergency runs
echo "Starting manual pipeline run..."
python3 /workspace/run_pipeline.py --mode=manual --notify=false
""")

write("data/raw/sample_metrics.json", """\
[
  {"timestamp": "2024-06-01T00:00:00Z", "metric": "cpu_usage", "value": 0.72},
  {"timestamp": "2024-06-01T00:01:00Z", "metric": "cpu_usage", "value": 0.68},
  {"timestamp": "2024-06-01T00:02:00Z", "metric": "memory_usage", "value": 0.81}
]
""")

write("archive/2024/failed_plugins_report.txt", """\
Report Date: 2024-05-30
Plugins that failed registration: 7
Root causes:
  - Missing YAML front matter: 4 cases
  - Malformed YAML structure: 2 cases
  - Empty required fields: 1 case
Action: Manual review required before next deployment.
""")

print("Workspace generated successfully.")
print("Key artifacts:")
print("  plugins/  — 12 plugin files (7 invalid, 5 valid)")
print("  ops/scheduled/operations_manifest.json — 8 operations to process")
print("  .learnings/ — empty directory awaiting ERRORS.md")