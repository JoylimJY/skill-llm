import os
import random
import textwrap

random.seed(42)

workspace = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "docs",
    "src/pipeline",
    "src/pipeline/ingestion",
    "src/pipeline/transforms",
    "src/pipeline/outputs",
    "src/models",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",
    "scripts",
    "infra/terraform",
    "infra/docker",
    ".solo/stacks",
    "notebooks",
    "data/raw",
    "data/processed",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── CLAUDE.md ─────────────────────────────────────────────────────────────────
claude_md = textwrap.dedent("""\
    # CLAUDE.md — DataFlux ML Pipeline

    ## Project Overview
    DataFlux is a modular, real-time ML feature engineering pipeline designed for
    fraud detection at scale. Built for data engineers and ML practitioners.

    ## Key Documents
    - `docs/prd.md` — Product Requirements Document
    - `docs/architecture.md` — System architecture and data flow diagrams

    ## Tech Stack
    Stack: Python

    - **Runtime:** Python 3.11
    - **Pipeline:** Apache Beam 2.52.0
    - **Feature Store:** Feast 0.34
    - **Serving:** FastAPI 0.109
    - **Testing:** pytest, pytest-asyncio, pytest-cov
    - **Linting:** ruff (see ruff.toml)
    - **Task Runner:** Make (see Makefile)

    ## Architecture
    - Event-driven ingestion via Kafka topics
    - Stateless transform workers with Redis-backed state cache
    - Feature materialization to BigQuery + local Parquet fallback
    - REST serving layer with sub-50ms p99 latency target

    ## Commands
    - `make install` — Install dependencies
    - `make test` — Run full test suite
    - `make lint` — Run ruff linter
    - `make build` — Build Docker image
    - `make run-local` — Start local pipeline with sample data

    ## Do
    - Write type hints on all public functions
    - Use dataclasses or pydantic models for data contracts
    - Keep transforms pure and side-effect free
    - Log at INFO level with structured JSON

    ## Don't
    - Don't import from `src` directly in tests — use fixtures
    - Don't hardcode BigQuery table IDs
    - Don't suppress exceptions silently
    - Don't use global mutable state in pipeline transforms
""")

with open(os.path.join(workspace, "CLAUDE.md"), "w") as f:
    f.write(claude_md)

# ── docs/prd.md ───────────────────────────────────────────────────────────────
prd_md = textwrap.dedent("""\
    # PRD — DataFlux ML Pipeline

    ## Problem
    Fraud detection teams spend 60% of their time on ad-hoc feature engineering
    scripts that are brittle, untested, and not reusable across models.

    ## Target Users
    - Senior ML Engineers (primary)
    - Data Engineers (secondary)
    - Model Risk Analysts (tertiary)

    ## Solution
    A composable, schema-enforced pipeline that transforms raw event streams into
    validated feature vectors consumable by any model serving infrastructure.

    ## Core Features
    1. Schema-validated ingestion with dead-letter queue support
    2. Pluggable transform registry with versioning
    3. Point-in-time correct feature joins
    4. Automated data quality checks (Great Expectations integration)
    5. One-command local replay from Parquet snapshots

    ## Success Metrics
    - < 5 minutes from raw event to feature availability
    - > 99.5% schema validation pass rate
    - Zero untested business-logic transforms at release

    ## Pricing
    Internal tooling — no external pricing model.
    Infrastructure cost target: < $800/month on GCP.
""")

with open(os.path.join(workspace, "docs/prd.md"), "w") as f:
    f.write(prd_md)

# ── pyproject.toml ────────────────────────────────────────────────────────────
pyproject_toml = textwrap.dedent("""\
    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [project]
    name = "dataflux"
    version = "0.3.1"
    description = "Real-time ML feature engineering pipeline for fraud detection"
    requires-python = ">=3.11"
    dependencies = [
        "apache-beam==2.52.0",
        "feast==0.34.1",
        "fastapi==0.109.2",
        "pydantic==2.5.3",
        "redis==5.0.1",
        "kafka-python==2.0.2",
        "google-cloud-bigquery==3.14.1",
        "pyarrow==14.0.2",
        "structlog==24.1.0",
    ]

    [project.optional-dependencies]
    dev = [
        "pytest==7.4.4",
        "pytest-asyncio==0.23.3",
        "pytest-cov==4.1.0",
        "ruff==0.2.1",
        "mypy==1.8.0",
        "hypothesis==6.96.1",
        "great-expectations==0.18.8",
    ]

    [tool.pytest.ini_options]
    asyncio_mode = "auto"
    testpaths = ["tests"]
    addopts = "--cov=src --cov-report=term-missing --cov-fail-under=80"

    [tool.hatch.envs.default]
    features = ["dev"]
""")

with open(os.path.join(workspace, "pyproject.toml"), "w") as f:
    f.write(pyproject_toml)

# ── Makefile ──────────────────────────────────────────────────────────────────
makefile = textwrap.dedent("""\
    .PHONY: install test lint build run-local clean

    install:
    \tpip install -e ".[dev]"

    test:
    \tpytest tests/ -v

    lint:
    \truff check src/ tests/

    format:
    \truff format src/ tests/

    build:
    \tdocker build -t dataflux:latest .

    run-local:
    \tpython -m dataflux.runner --source data/raw --sink data/processed

    clean:
    \tfind . -type d -name __pycache__ -exec rm -rf {} +
    \trm -rf .coverage htmlcov/ dist/ .pytest_cache/
""")

with open(os.path.join(workspace, "Makefile"), "w") as f:
    f.write(makefile)

# ── ruff.toml ─────────────────────────────────────────────────────────────────
ruff_toml = textwrap.dedent("""\
    [tool.ruff]
    line-length = 100
    target-version = "py311"
    select = ["E", "F", "I", "N", "W", "UP", "ANN", "B", "C4", "PT"]
    ignore = ["ANN101", "ANN102", "ANN401"]

    [tool.ruff.per-file-ignores]
    "tests/**" = ["ANN", "S101"]
    "scripts/**" = ["ANN", "T201"]
""")

with open(os.path.join(workspace, "ruff.toml"), "w") as f:
    f.write(ruff_toml)

# ── Source files (distractors) ────────────────────────────────────────────────
files = {
    "src/__init__.py": '"""DataFlux pipeline package."""\n__version__ = "0.3.1"\n',

    "src/pipeline/__init__.py": '"""Pipeline subpackage."""\n',

    "src/pipeline/ingestion/kafka_consumer.py": textwrap.dedent("""\
        \"\"\"Kafka event consumer with schema validation.\"\"\"
        from __future__ import annotations
        import structlog
        from dataclasses import dataclass

        log = structlog.get_logger()

        @dataclass
        class RawEvent:
            topic: str
            payload: bytes
            offset: int

        def consume(topic: str, group_id: str) -> list[RawEvent]:
            log.info("consuming", topic=topic, group_id=group_id)
            return []
    """),

    "src/pipeline/transforms/feature_extractor.py": textwrap.dedent("""\
        \"\"\"Feature extraction transforms — pure functions only.\"\"\"
        from __future__ import annotations
        from typing import Any
        import apache_beam as beam  # type: ignore

        class ExtractFeatures(beam.DoFn):
            def process(self, element: dict[str, Any]):  # type: ignore
                yield {
                    "amount_usd": element.get("amount", 0.0),
                    "merchant_country": element.get("country", "UNKNOWN"),
                }
    """),

    "src/pipeline/outputs/bigquery_sink.py": textwrap.dedent("""\
        \"\"\"BigQuery output sink.\"\"\"
        from __future__ import annotations
        import structlog

        log = structlog.get_logger()

        def write_features(table_ref: str, rows: list[dict]) -> None:
            log.info("writing_to_bq", table=table_ref, row_count=len(rows))
    """),

    "src/models/__init__.py": '"""Model definitions."""\n',

    "src/models/fraud_scorer.py": textwrap.dedent("""\
        \"\"\"Fraud scoring model wrapper.\"\"\"
        from pydantic import BaseModel

        class FraudScore(BaseModel):
            transaction_id: str
            score: float
            threshold: float = 0.85
            is_fraud: bool = False

            def evaluate(self) -> None:
                self.is_fraud = self.score >= self.threshold
    """),

    "src/utils/schema_validator.py": textwrap.dedent("""\
        \"\"\"Schema validation utilities.\"\"\"
        from __future__ import annotations
        from typing import Any
        from pydantic import BaseModel, ValidationError

        def validate(model: type[BaseModel], data: dict[str, Any]) -> bool:
            try:
                model(**data)
                return True
            except ValidationError:
                return False
    """),

    "tests/__init__.py": "",
    "tests/unit/__init__.py": "",
    "tests/integration/__init__.py": "",

    "tests/unit/test_schema_validator.py": textwrap.dedent("""\
        \"\"\"Tests for schema validation utilities.\"\"\"
        import pytest
        from src.utils.schema_validator import validate
        from src.models.fraud_scorer import FraudScore

        def test_valid_score():
            assert validate(FraudScore, {"transaction_id": "tx_001", "score": 0.9})

        def test_invalid_score():
            assert not validate(FraudScore, {"transaction_id": "tx_001", "score": "not_a_float"})
    """),

    "tests/fixtures/sample_events.json": '[\n  {"amount": 120.50, "country": "US"},\n  {"amount": 9999.00, "country": "NG"}\n]\n',

    "scripts/replay_local.py": textwrap.dedent("""\
        \"\"\"Local replay helper for development testing.\"\"\"
        import argparse, json, pathlib

        def main():
            parser = argparse.ArgumentParser()
            parser.add_argument("--source", required=True)
            args = parser.parse_args()
            data = list(pathlib.Path(args.source).glob("*.json"))
            print(f"Found {len(data)} fixture files")

        if __name__ == "__main__":
            main()
    """),

    "infra/docker/Dockerfile.pipeline": textwrap.dedent("""\
        FROM python:3.11-slim
        WORKDIR /app
        COPY . .
        RUN pip install -e .
        CMD ["python", "-m", "dataflux.runner"]
    """),

    "infra/terraform/main.tf": textwrap.dedent("""\
        terraform {
          required_providers {
            google = { source = "hashicorp/google", version = "~> 5.0" }
          }
        }
        resource "google_bigquery_dataset" "features" {
          dataset_id = "ml_features"
          location   = "US"
        }
    """),

    "notebooks/eda_fraud_patterns.py": textwrap.dedent("""\
        # %% [markdown]
        # # EDA — Fraud Pattern Analysis
        # %%
        import pandas as pd
        df = pd.read_parquet("data/processed/features.parquet")
        print(df.describe())
    """),

    "data/raw/.gitkeep": "",
    "data/processed/.gitkeep": "",

    ".solo/stacks/python.yaml": textwrap.dedent("""\
        stack: python
        test_framework: pytest
        linter: ruff
        tdd_policy: Moderate
        commit_strategy: Conventional Commits
    """),
}

for rel_path, content in files.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── docs/architecture.md (distractor — NOT prd or workflow) ───────────────────
arch_md = textwrap.dedent("""\
    # Architecture — DataFlux

    ## Data Flow
    ```
    Kafka → Consumer → Validator → Transform Workers → Feature Store → BQ / Parquet
    ```

    ## Components
    - **Ingestion Layer:** Kafka consumers with dead-letter routing
    - **Transform Layer:** Stateless beam DoFns, horizontally scalable
    - **Storage Layer:** Feast feature store → BigQuery long-term, Redis short-term
    - **Serving Layer:** FastAPI with feature retrieval endpoints
""")

with open(os.path.join(workspace, "docs/architecture.md"), "w") as f:
    f.write(arch_md)

print("Workspace initialized successfully.")
print(f"Files created: {sum(1 for _ in __import__('pathlib').Path(workspace).rglob('*') if _.is_file())}")