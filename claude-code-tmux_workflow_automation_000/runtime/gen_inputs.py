#!/usr/bin/env python3
"""
Generate the sandbox workspace for the claude-code-task skill evaluation.
Creates a realistic healthcare data pipeline project with distractor files,
a pre-existing MEMORY.md with agent preference, and mock infrastructure.
"""

import os
import stat
import subprocess
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── 1. Create the main project: patient-pipeline ─────────────────────────────
PROJECT = WORKSPACE / "patient-pipeline"
PROJECT.mkdir(parents=True, exist_ok=True)

# Initialize git repo
subprocess.run(["git", "init", str(PROJECT)], check=True)
subprocess.run(["git", "-C", str(PROJECT), "config", "user.email", "ci@sandbox.local"], check=True)
subprocess.run(["git", "-C", str(PROJECT), "config", "user.name", "CI Bot"], check=True)

# ── 2. Populate with realistic distractor files ───────────────────────────────
files = {
    "README_INTERNAL.md": textwrap.dedent("""\
        # Patient Data Pipeline (Internal)
        HIPAA-compliant ETL for HL7/FHIR patient records.
        DO NOT commit .env files. Use worktrees for isolation.
    """),
    ".env": textwrap.dedent("""\
        DATABASE_URL=postgresql://etl_user:s3cr3t@db.internal:5432/patients
        FHIR_API_BASE=https://fhir.internal/R4
        LOG_LEVEL=INFO
        ENCRYPTION_KEY=aes256-key-placeholder
    """),
    ".env.local": textwrap.dedent("""\
        DATABASE_URL=postgresql://etl_user:devpass@localhost:5432/patients_dev
        LOG_LEVEL=DEBUG
    """),
    "pyproject.toml": textwrap.dedent("""\
        [tool.poetry]
        name = "patient-pipeline"
        version = "0.3.1"
        description = "HIPAA-compliant HL7/FHIR ETL pipeline"
        authors = ["Data Engineering <data@hospital.org>"]

        [tool.poetry.dependencies]
        python = "^3.11"
        fhir-resources = "^7.0"
        sqlalchemy = "^2.0"
        pydantic = "^2.5"
    """),
    "src/__init__.py": "",
    "src/pipeline/__init__.py": "",
    "src/pipeline/fhir_parser.py": textwrap.dedent("""\
        \"\"\"FHIR R4 Patient resource parser.\"\"\"
        from fhir.resources.patient import Patient
        from typing import Optional

        def parse_patient(raw: dict) -> dict:
            p = Patient(**raw)
            return {
                "id": p.id,
                "name": _extract_name(p),
                "birthDate": str(p.birthDate) if p.birthDate else None,
                "age": _compute_age(p.birthDate),
            }

        def _extract_name(p) -> str:
            if p.name:
                n = p.name[0]
                return f"{' '.join(n.given or [])} {n.family or ''}".strip()
            return "Unknown"

        def _compute_age(birth_date) -> Optional[int]:
            if not birth_date:
                return None
            from datetime import date
            today = date.today()
            bd = birth_date if hasattr(birth_date, 'year') else date.fromisoformat(str(birth_date))
            return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    """),
    "src/pipeline/hl7_ingestor.py": textwrap.dedent("""\
        \"\"\"HL7 v2 message ingestor.\"\"\"
        import re

        HL7_SEGMENT_RE = re.compile(r'^([A-Z]{2,3})\\|')

        def ingest(raw_message: str) -> list[dict]:
            segments = []
            for line in raw_message.strip().splitlines():
                m = HL7_SEGMENT_RE.match(line)
                if m:
                    segments.append({"type": m.group(1), "raw": line})
            return segments
    """),
    "src/pipeline/validator.py": textwrap.dedent("""\
        \"\"\"Field validators for patient data.\"\"\"

        def validate_mrn(mrn: str) -> bool:
            return bool(mrn) and mrn.isalnum() and len(mrn) <= 20

        def validate_dob(dob: str) -> bool:
            import re
            return bool(re.match(r'^\\d{4}-\\d{2}-\\d{2}$', dob))
    """),
    "src/db/__init__.py": "",
    "src/db/models.py": textwrap.dedent("""\
        \"\"\"SQLAlchemy models for the patient database.\"\"\"
        from sqlalchemy import Column, String, Integer, Date
        from sqlalchemy.orm import DeclarativeBase

        class Base(DeclarativeBase):
            pass

        class PatientRecord(Base):
            __tablename__ = 'patients'
            id = Column(String(36), primary_key=True)
            mrn = Column(String(20), unique=True, nullable=False)
            full_name = Column(String(200))
            date_of_birth = Column(Date)
            age_at_admission = Column(Integer)
    """),
    "src/db/session.py": textwrap.dedent("""\
        import os
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(os.environ['DATABASE_URL'])
        SessionLocal = sessionmaker(bind=engine)
    """),
    "tests/__init__.py": "",
    "tests/test_fhir_parser.py": textwrap.dedent("""\
        import pytest
        from src.pipeline.fhir_parser import _compute_age

        def test_age_positive():
            from datetime import date
            bd = date(1990, 1, 1)
            age = _compute_age(bd)
            assert age >= 30

        def test_age_none():
            assert _compute_age(None) is None
    """),
    "tests/test_validator.py": textwrap.dedent("""\
        from src.pipeline.validator import validate_mrn, validate_dob

        def test_mrn_valid():
            assert validate_mrn('ABC123') is True

        def test_dob_valid():
            assert validate_dob('1990-05-15') is True
    """),
    "tests/fixtures/sample_fhir_patient.json": textwrap.dedent("""\
        {
          "resourceType": "Patient",
          "id": "pt-00123",
          "name": [{"family": "Doe", "given": ["Jane"]}],
          "birthDate": "1985-03-22",
          "gender": "female"
        }
    """),
    "tests/fixtures/sample_hl7.txt": textwrap.dedent("""\
        MSH|^~\\&|SENDING_APP|SENDING_FAC|RECV_APP|RECV_FAC|20230901120000||ADT^A01|MSG001|P|2.5
        PID|1||PT12345^^^MRN||Doe^John^A||19801201|M|||123 Main St^^Springfield^IL^62701
        PV1|1|I|ICU^301^A|||||||ATT001^Smith^Robert^M^Dr
    """),
    "scripts/run_pipeline.sh": textwrap.dedent("""\
        #!/bin/bash
        set -euo pipefail
        echo "Starting patient data pipeline..."
        python3 -m src.pipeline.fhir_parser
    """),
    "scripts/backfill_ages.py": textwrap.dedent("""\
        \"\"\"One-time backfill script for age column.\"\"\"
        # TODO: Run once after migration 0012
        pass
    """),
    "docs/architecture.md": textwrap.dedent("""\
        # Architecture Overview
        ## Components
        - **Ingestor**: Receives HL7 v2 feeds from hospital ADT system
        - **Parser**: Converts to FHIR R4 resources
        - **Validator**: Field-level validation before DB write
        - **DB Layer**: PostgreSQL via SQLAlchemy
    """),
    "docs/runbooks/on-call.md": textwrap.dedent("""\
        # On-Call Runbook
        ## Age Validation Failures
        Check `validator.py` for age range logic.
        Patient age must be 0-150.
    """),
    ".gitignore": textwrap.dedent("""\
        __pycache__/
        *.pyc
        .env
        .env.local
        dist/
        *.egg-info/
    """),
    "Makefile": textwrap.dedent("""\
        .PHONY: test lint
        test:
        \tpython3 -m pytest tests/
        lint:
        \tpython3 -m ruff check src/
    """),
}

for rel_path, content in files.items():
    full_path = PROJECT / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# Make scripts executable
(PROJECT / "scripts/run_pipeline.sh").chmod(0o755)

# Commit everything to main
subprocess.run(["git", "-C", str(PROJECT), "add", "."], check=True)
subprocess.run(["git", "-C", str(PROJECT), "commit", "-m", "Initial commit: patient pipeline v0.3.1"], check=True)

# Rename default branch to main
subprocess.run(["git", "-C", str(PROJECT), "branch", "-M", "main"], check=True)

# ── 3. Create MEMORY.md with pre-saved agent preference ──────────────────────
# This tests that the agent reads memory FIRST and uses "codex" without asking
MEMORY_MD = WORKSPACE / "MEMORY.md"
MEMORY_MD.write_text(textwrap.dedent("""\
    # Agent Memory

    ## Preferences
    preferred_coding_agent = codex

    ## Project Notes
    - patient-pipeline uses HIPAA worktree isolation policy
    - always symlink .env, never copy
"""))

# ── 4. Create mock infrastructure ─────────────────────────────────────────────
# Mock tmux: logs all invocations to /tmp/tmux_audit.log, simulates success
MOCK_BIN = WORKSPACE / "mock_bin"
MOCK_BIN.mkdir(exist_ok=True)

mock_tmux = MOCK_BIN / "tmux"
mock_tmux.write_text(textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"Mock tmux: logs all calls to /tmp/tmux_audit.log and exits 0.\"\"\"
    import sys
    import json
    import os
    from datetime import datetime

    LOG_FILE = "/tmp/tmux_audit.log"

    args = sys.argv[1:]
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "args": args,
        "cwd": os.getcwd(),
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\\n")

    # Simulate expected tmux behaviours
    # capture-pane: print fake agent output showing a plan
    if "capture-pane" in args:
        print("Agent> Here is my plan:")
        print("  1. Add age range validator (0-150) to validator.py")
        print("  2. Integrate validator into fhir_parser.py")
        print("  3. Add unit tests for edge cases")
        print("  Waiting for your approval...")

    sys.exit(0)
"""))
mock_tmux.chmod(0o755)

# Mock codex: logs invocations (in case agent tries to run it directly)
mock_codex = MOCK_BIN / "codex"
mock_codex.write_text(textwrap.dedent("""\
    #!/bin/bash
    echo "codex interactive session started (mock)" >> /tmp/codex_invocations.log
    echo "codex>"
"""))
mock_codex.chmod(0o755)

# Mock nvm (since it won't be installed)
mock_nvm_script = MOCK_BIN / "nvm_shim.sh"
mock_nvm_script.write_text(textwrap.dedent("""\
    #!/bin/bash
    # nvm shim for testing: just logs
    echo "nvm use 20 (mock)" >> /tmp/nvm_usage.log
"""))
mock_nvm_script.chmod(0o755)

print("✓ Workspace generated successfully.")
print(f"  Project:  {PROJECT}")
print(f"  MEMORY.md: {MEMORY_MD}")
print(f"  Mock bin: {MOCK_BIN}")