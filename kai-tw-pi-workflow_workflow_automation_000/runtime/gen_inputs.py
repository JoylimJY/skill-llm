import os
import random
import datetime

random.seed(42)

workspace = "/workspace"

# Create the full directory structure
dirs = [
    "tasks",
    "memory",
    "src/pipeline",
    "src/feature_store",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "config/dev",
    "config/prod",
    "docs/architecture",
    "docs/runbooks",
    "scripts",
    "logs",
    ".git/objects",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ---- Distractor files ----

# Source code files (distractors)
with open(os.path.join(workspace, "src/pipeline/ingest.py"), "w") as f:
    f.write("""import pandas as pd
import logging

logger = logging.getLogger(__name__)

def ingest_features(source_path: str) -> pd.DataFrame:
    \"\"\"Ingest raw features from source.\"\"\"
    df = pd.read_parquet(source_path)
    logger.info(f"Ingested {len(df)} rows from {source_path}")
    return df
""")

with open(os.path.join(workspace, "src/pipeline/transform.py"), "w") as f:
    f.write("""import pandas as pd
from typing import List

def normalize_features(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    for col in columns:
        df[col] = (df[col] - df[col].mean()) / df[col].std()
    return df

def fill_nulls(df: pd.DataFrame) -> pd.DataFrame:
    return df.fillna(0)
""")

with open(os.path.join(workspace, "src/feature_store/client.py"), "w") as f:
    f.write("""import requests

FEATURE_STORE_URL = "http://feast.internal.corp:6566"

def push_features(df, feature_view: str):
    # BUG: This was using wrong endpoint before incident
    resp = requests.post(f"{FEATURE_STORE_URL}/v2/push", json={
        "feature_view_name": feature_view,
        "df": df.to_dict()
    })
    resp.raise_for_status()
    return resp.json()
""")

with open(os.path.join(workspace, "src/feature_store/validator.py"), "w") as f:
    f.write("""def validate_schema(df, expected_cols):
    missing = set(expected_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return True
""")

with open(os.path.join(workspace, "src/utils/retry.py"), "w") as f:
    f.write("""import time
import functools

def retry(max_attempts=3, delay=1.0):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator
""")

# Test files
with open(os.path.join(workspace, "tests/unit/test_transform.py"), "w") as f:
    f.write("""import pytest
import pandas as pd
from src.pipeline.transform import normalize_features, fill_nulls

def test_normalize_basic():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
    result = normalize_features(df, ["a"])
    assert abs(result["a"].mean()) < 1e-10

def test_fill_nulls():
    df = pd.DataFrame({"a": [1.0, None, 3.0]})
    result = fill_nulls(df)
    assert result["a"].isna().sum() == 0
""")

with open(os.path.join(workspace, "tests/integration/test_pipeline_e2e.py"), "w") as f:
    f.write("""# Integration test - requires running feature store
# TODO: These tests were FAILING during incident
import pytest

@pytest.mark.skip(reason="requires live feast server")
def test_full_pipeline_push():
    pass
""")

# Config files
with open(os.path.join(workspace, "config/dev/pipeline.yaml"), "w") as f:
    f.write("""environment: development
feature_store:
  url: http://localhost:6566
  timeout: 30
pipeline:
  batch_size: 1000
  retry_attempts: 3
""")

with open(os.path.join(workspace, "config/prod/pipeline.yaml"), "w") as f:
    f.write("""environment: production
feature_store:
  url: http://feast.internal.corp:6566
  timeout: 10
pipeline:
  batch_size: 5000
  retry_attempts: 1
""")

# Docs
with open(os.path.join(workspace, "docs/architecture/feature_pipeline_design.md"), "w") as f:
    f.write("""# Feature Pipeline Architecture

## Overview
The feature pipeline ingests raw events, transforms them, and pushes to Feast feature store.

## Components
- **Ingest**: Reads parquet from S3
- **Transform**: Normalizes and imputes features
- **Push**: Writes to Feast via HTTP API

## Known Issues
- See incident report for 2025-07-15 outage details (TBD)
""")

with open(os.path.join(workspace, "docs/runbooks/restart_pipeline.md"), "w") as f:
    f.write("""# Restart Pipeline Runbook

1. Check logs: `kubectl logs -l app=feature-pipeline -n mlops`
2. Check feature store health: `curl http://feast.internal.corp:6566/health`
3. Restart deployment: `kubectl rollout restart deployment/feature-pipeline -n mlops`
""")

# Scripts
with open(os.path.join(workspace, "scripts/deploy.sh"), "w") as f:
    f.write("""#!/bin/bash
set -e
echo "Deploying feature pipeline..."
docker build -t feature-pipeline:latest .
kubectl apply -f k8s/
kubectl rollout status deployment/feature-pipeline -n mlops
""")

with open(os.path.join(workspace, "scripts/run_tests.sh"), "w") as f:
    f.write("""#!/bin/bash
set -e
python3 -m pytest tests/unit/ -v
echo "Unit tests passed"
""")

# Logs (messy incident logs as context)
with open(os.path.join(workspace, "logs/incident_20250715.log"), "w") as f:
    f.write("""2025-07-15T03:22:14Z ERROR feature_store.client: HTTP 422 Unprocessable Entity - {"detail": "feature_view_name not found: user_features_v1"}
2025-07-15T03:22:14Z ERROR pipeline.main: Push failed after 1 retry (prod retry_attempts=1)
2025-07-15T03:22:15Z CRITICAL monitoring.alerter: SLA breach - feature freshness > 15 min threshold
2025-07-15T03:22:15Z INFO pipeline.main: Rolling back to last known good state
2025-07-15T03:22:18Z ERROR feature_store.client: HTTP 422 Unprocessable Entity - {"detail": "feature_view_name not found: user_features_v1"}
2025-07-15T03:22:20Z INFO ops.oncall: PagerDuty alert sent to on-call engineer
2025-07-15T03:23:01Z INFO ops.oncall: Engineer acknowledged incident
2025-07-15T03:45:33Z INFO pipeline.main: Manual intervention - feature view renamed to user_features_v2 in registry
2025-07-15T03:46:10Z INFO pipeline.main: Pipeline resumed, features flowing normally
2025-07-15T04:01:00Z INFO monitoring.alerter: SLA restored
""")

with open(os.path.join(workspace, "logs/pipeline_20250714.log"), "w") as f:
    f.write("""2025-07-14T00:00:01Z INFO pipeline.main: Batch job started
2025-07-14T00:02:44Z INFO pipeline.main: Ingested 982341 rows
2025-07-14T00:04:12Z INFO pipeline.main: Transform complete
2025-07-14T00:05:03Z INFO pipeline.main: Push to feature store complete
2025-07-14T00:05:03Z INFO monitoring.alerter: All checks passed
""")

# Memory dir placeholder
with open(os.path.join(workspace, "memory/.gitkeep"), "w") as f:
    f.write("")

# A messy pre-existing todo (incomplete, wrong format - agent must create proper one)
with open(os.path.join(workspace, "tasks/old_notes.txt"), "w") as f:
    f.write("""rough notes july 15 incident:
- the feature view name changed in feast registry without updating the pipeline config
- need to add schema validation before push
- retry logic in prod is too aggressive (only 1 attempt)
- no automated test that checks feature view name exists before deploy
- would be nice if the pipeline could auto-discover feature view names from registry
- ali got paged at 3am, terrible experience
""")

# git placeholder
with open(os.path.join(workspace, ".git/objects/.gitkeep"), "w") as f:
    f.write("")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")