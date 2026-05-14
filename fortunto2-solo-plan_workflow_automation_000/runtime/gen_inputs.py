import os
import random
from pathlib import Path
from datetime import datetime

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "src/genomix/parsers",
    "src/genomix/validators",
    "src/genomix/db",
    "src/genomix/etl",
    "src/genomix/utils",
    "src/genomix/models",
    "tests/unit/parsers",
    "tests/unit/validators",
    "tests/integration",
    "docs",
    "scripts",
    "config",
    "data/raw",
    "data/processed",
    ".github/workflows",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── pyproject.toml (PROJECT context trigger) ─────────────────────────────────
(workspace / "pyproject.toml").write_text("""\
[tool.poetry]
name = "genomix"
version = "0.4.2"
description = "Genomic data ingestion and processing pipeline"
authors = ["BioTeam <bio@example.com>"]

[tool.poetry.dependencies]
python = "^3.10"
pandas = "^2.0"
sqlalchemy = "^2.0"
biopython = "^1.81"
pydantic = "^2.0"
click = "^8.1"
httpx = "^0.24"

[tool.poetry.dev-dependencies]
pytest = "^7.4"
black = "^23.0"
flake8 = "^6.0"
pytest-cov = "^4.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""")

# ── CLAUDE.md ─────────────────────────────────────────────────────────────────
(workspace / "CLAUDE.md").write_text("""\
# GenomiX Pipeline — Architecture Reference

## Project Overview
GenomiX processes FASTQ/VCF genomic files, validates them against reference schemas,
and loads results into a PostgreSQL database for downstream analysis.

## Stack
- Python 3.10+
- SQLAlchemy 2.x (async engine)
- Pydantic v2 for validation models
- Click for CLI entry points
- pandas for data wrangling

## Key Commands
- `pytest tests/` — run all tests
- `black src/ tests/` — format
- `flake8 src/` — lint
- `python -m genomix.etl.pipeline --help` — ETL entry point

## Directory Layers
- `src/genomix/parsers/` — file format parsers (FASTQ, VCF, BED)
- `src/genomix/validators/` — Pydantic schema validation
- `src/genomix/db/` — SQLAlchemy models & session management
- `src/genomix/etl/` — orchestration pipeline
- `src/genomix/utils/` — shared helpers (logging, config loading)
- `src/genomix/models/` — domain data classes

## Constraints (Do/Don't)
- DO: Use Pydantic v2 model_validator for cross-field validation
- DON'T: Import db layer from parsers (one-way dependency)
- DO: All DB writes go through `db/session.py` context manager
- DON'T: Raw SQL strings — always use SQLAlchemy ORM
- DO: Each parser returns a typed dataclass, never a raw dict
- DON'T: Business logic in CLI entry points

## Module Boundary Rules
parsers → models (ok)
validators → models (ok)
etl → parsers, validators, db (ok)
db → models (ok)
parsers → db (FORBIDDEN)
validators → db (FORBIDDEN)
""")

# ── docs/prd.md ───────────────────────────────────────────────────────────────
(workspace / "docs/prd.md").write_text("""\
# Product Requirements: GenomiX

## Purpose
Provide a scalable, auditable pipeline for ingesting multi-format genomic files
from sequencing labs and persisting structured variant data to PostgreSQL.

## Core Features
1. Multi-format ingestion: FASTQ, VCF 4.2, BED
2. Schema validation with error reporting
3. Idempotent ETL runs (dedup by sample_id + run_id)
4. Audit log of all ingestion events
5. CLI interface for operators

## Known Pain Points
- Parser modules directly instantiate DB sessions (violates architecture)
- VCF parser returns raw dicts instead of typed models
- No retry logic on DB write failures
- Validators do not log validation errors to audit table
""")

# ── Source files ──────────────────────────────────────────────────────────────
(workspace / "src/genomix/parsers/fastq_parser.py").write_text("""\
\"\"\"FASTQ file parser — currently violates module boundary.\"\"\"
from genomix.db.session import get_session  # FORBIDDEN IMPORT
import pandas as pd

class FastqParser:
    def parse(self, filepath: str) -> dict:  # Should return typed model
        session = get_session()  # VIOLATION
        # ... parse logic
        return {"sample_id": "S001", "reads": 1000000, "quality_mean": 35.2}
""")

(workspace / "src/genomix/parsers/vcf_parser.py").write_text("""\
\"\"\"VCF 4.2 parser — returns raw dicts (non-compliant).\"\"\"
from Bio import SeqIO

class VcfParser:
    def parse(self, filepath: str) -> dict:  # Should return VariantRecord model
        return {
            "chrom": "chr1", "pos": 12345, "ref": "A", "alt": "G",
            "qual": 99, "filter": "PASS", "info": {}
        }
""")

(workspace / "src/genomix/parsers/bed_parser.py").write_text("""\
\"\"\"BED format parser.\"\"\"
from genomix.models.region import GenomicRegion

class BedParser:
    def parse(self, filepath: str) -> list[GenomicRegion]:
        regions = []
        with open(filepath) as f:
            for line in f:
                chrom, start, end, *rest = line.strip().split()
                regions.append(GenomicRegion(chrom=chrom, start=int(start), end=int(end)))
        return regions
""")

(workspace / "src/genomix/models/__init__.py").write_text("")
(workspace / "src/genomix/models/variant.py").write_text("""\
\"\"\"Domain model for genomic variant records.\"\"\"
from dataclasses import dataclass
from typing import Optional

@dataclass
class VariantRecord:
    chrom: str
    pos: int
    ref: str
    alt: str
    qual: float
    filter_status: str
    sample_id: str
    run_id: str
    info: dict
""")

(workspace / "src/genomix/models/region.py").write_text("""\
from dataclasses import dataclass

@dataclass
class GenomicRegion:
    chrom: str
    start: int
    end: int
    name: str = ""
""")

(workspace / "src/genomix/models/read_group.py").write_text("""\
from dataclasses import dataclass

@dataclass
class ReadGroup:
    sample_id: str
    run_id: str
    reads: int
    quality_mean: float
    platform: str = "ILLUMINA"
""")

(workspace / "src/genomix/validators/variant_validator.py").write_text("""\
\"\"\"Pydantic v2 validator for VariantRecord.\"\"\"
from pydantic import BaseModel, model_validator
from typing import Optional

class VariantSchema(BaseModel):
    chrom: str
    pos: int
    ref: str
    alt: str
    qual: float
    filter_status: str
    sample_id: str
    run_id: str

    @model_validator(mode='after')
    def check_ref_alt_differ(self):
        if self.ref == self.alt:
            raise ValueError('ref and alt must differ')
        return self
""")

(workspace / "src/genomix/validators/read_group_validator.py").write_text("""\
from pydantic import BaseModel, field_validator

class ReadGroupSchema(BaseModel):
    sample_id: str
    run_id: str
    reads: int
    quality_mean: float

    @field_validator('reads')
    @classmethod
    def reads_positive(cls, v):
        if v <= 0:
            raise ValueError('reads must be positive')
        return v
""")

(workspace / "src/genomix/db/session.py").write_text("""\
\"\"\"SQLAlchemy async session management.\"\"\"
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import asynccontextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/genomix")
engine = create_async_engine(DATABASE_URL)

@asynccontextmanager
async def get_session():
    async with AsyncSession(engine) as session:
        yield session
""")

(workspace / "src/genomix/db/models.py").write_text("""\
\"\"\"SQLAlchemy ORM models.\"\"\"
from sqlalchemy import Column, String, Integer, Float, JSON, DateTime
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class VariantRow(Base):
    __tablename__ = 'variants'
    id = Column(Integer, primary_key=True)
    chrom = Column(String)
    pos = Column(Integer)
    ref = Column(String)
    alt = Column(String)
    qual = Column(Float)
    sample_id = Column(String, index=True)
    run_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True)
    event_type = Column(String)
    sample_id = Column(String)
    run_id = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
""")

(workspace / "src/genomix/etl/pipeline.py").write_text("""\
\"\"\"ETL orchestration — main pipeline entry point.\"\"\"
import click
from genomix.parsers.fastq_parser import FastqParser
from genomix.parsers.vcf_parser import VcfParser
from genomix.validators.variant_validator import VariantSchema
from genomix.db.session import get_session

@click.command()
@click.option('--input-dir', required=True)
@click.option('--run-id', required=True)
def run_pipeline(input_dir: str, run_id: str):
    \"\"\"Main ingestion pipeline.\"\"\"
    vcf_parser = VcfParser()
    # TODO: add retry logic, typed models, audit logging
    pass
""")

(workspace / "src/genomix/utils/logging.py").write_text("""\
import logging

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
""")

(workspace / "src/genomix/utils/config.py").write_text("""\
import os
from dataclasses import dataclass

@dataclass
class AppConfig:
    database_url: str
    input_dir: str
    log_level: str = "INFO"
    max_retries: int = 3

def load_config() -> AppConfig:
    return AppConfig(
        database_url=os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/genomix"),
        input_dir=os.getenv("INPUT_DIR", "/data/raw"),
    )
""")

# ── Tests ─────────────────────────────────────────────────────────────────────
(workspace / "tests/unit/parsers/test_vcf_parser.py").write_text("""\
from genomix.parsers.vcf_parser import VcfParser

def test_vcf_parse_returns_dict():
    parser = VcfParser()
    # TODO: This test should check for VariantRecord, not dict
    result = parser.parse('/dev/null')
    assert isinstance(result, dict)
    assert 'chrom' in result
""")

(workspace / "tests/unit/validators/test_variant_validator.py").write_text("""\
import pytest
from genomix.validators.variant_validator import VariantSchema

def test_variant_valid():
    v = VariantSchema(
        chrom='chr1', pos=100, ref='A', alt='G',
        qual=99.0, filter_status='PASS', sample_id='S1', run_id='R1'
    )
    assert v.chrom == 'chr1'

def test_variant_ref_eq_alt_fails():
    with pytest.raises(Exception):
        VariantSchema(
            chrom='chr1', pos=100, ref='A', alt='A',
            qual=99.0, filter_status='PASS', sample_id='S1', run_id='R1'
        )
""")

(workspace / "tests/integration/test_pipeline.py").write_text("""\
\"\"\"Integration tests for the ETL pipeline.\"\"\"
# TODO: mock DB session, test full pipeline with sample VCF
def test_pipeline_placeholder():
    pass
""")

# ── Config files ──────────────────────────────────────────────────────────────
(workspace / "config/logging.yaml").write_text("""\
version: 1
formatters:
  default:
    format: '%(asctime)s %(name)s %(levelname)s %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    formatter: default
root:
  level: INFO
  handlers: [console]
""")

(workspace / "config/pipeline.yaml").write_text("""\
pipeline:
  batch_size: 1000
  max_retries: 3
  retry_delay_seconds: 5
  formats: [fastq, vcf, bed]
  audit_enabled: true
""")

# ── Deploy infrastructure (triggers Deploy phase requirement) ─────────────────
(workspace / "Dockerfile").write_text("""\
FROM python:3.10-slim

WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry install --no-dev

COPY src/ ./src/
COPY config/ ./config/

ENV DATABASE_URL=""
ENV INPUT_DIR="/data/raw"

CMD ["python", "-m", "genomix.etl.pipeline", "--input-dir", "/data/raw", "--run-id", "auto"]
""")

(workspace / "scripts/deploy.sh").write_text("""\
#!/bin/bash
set -e
echo "Building Docker image..."
docker build -t genomix:latest .
echo "Pushing to registry..."
docker tag genomix:latest registry.example.com/genomix:latest
docker push registry.example.com/genomix:latest
echo "Deploying to VPS..."
ssh deploy@vps.example.com 'docker pull registry.example.com/genomix:latest && docker-compose up -d'
echo "Deploy complete."
""")

# ── .github/workflows ─────────────────────────────────────────────────────────
(workspace / ".github/workflows/ci.yml").write_text("""\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install poetry && poetry install
      - run: pytest tests/ --cov=src/
      - run: flake8 src/
      - run: black --check src/ tests/
""")

# ── Distractor files ──────────────────────────────────────────────────────────
(workspace / "data/raw/.gitkeep").write_text("")
(workspace / "data/processed/.gitkeep").write_text("")
(workspace / "scripts/seed_db.py").write_text("""\
\"\"\"Seed script for local dev DB.\"\"\"
print('Seeding local database...')
""")
(workspace / "scripts/benchmark.py").write_text("""\
\"\"\"Benchmark parser throughput.\"\"\"
import time
print('Benchmarking parsers...')
""")
(workspace / "src/genomix/__init__.py").write_text('__version__ = "0.4.2"\n')
(workspace / "src/genomix/parsers/__init__.py").write_text("")
(workspace / "src/genomix/validators/__init__.py").write_text("")
(workspace / "src/genomix/db/__init__.py").write_text("")
(workspace / "src/genomix/etl/__init__.py").write_text("")
(workspace / "src/genomix/utils/__init__.py").write_text("")

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")