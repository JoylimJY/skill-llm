import os
import random
import subprocess

random.seed(42)

WORKSPACE = "/workspace"
os.makedirs(WORKSPACE, exist_ok=True)

# --- Initialize git repo ---
subprocess.run(["git", "init"], cwd=WORKSPACE, check=True)
subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=WORKSPACE, check=True)
subprocess.run(["git", "config", "user.name", "TestUser"], cwd=WORKSPACE, check=True)

# --- Create deeply nested directory structure (distractor files) ---
dirs = [
    "src/api/routes",
    "src/api/middleware",
    "src/models",
    "src/services/notification",
    "src/services/auth",
    "src/utils",
    "tests/unit",
    "tests/integration",
    ".context",
    "docs",
    "scripts",
    "config",
    "migrations",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor source files ---
files = {
    "src/api/routes/medications.py": '''\
from flask import Blueprint, jsonify, request
from src.models.medication import Medication
from src.services.notification.sms import send_sms_alert

medications_bp = Blueprint("medications", __name__)

@medications_bp.route("/medications", methods=["GET"])
def list_medications():
    # TODO: add pagination
    meds = Medication.query.all()
    return jsonify([m.to_dict() for m in meds])

@medications_bp.route("/medications/<int:med_id>/adherence", methods=["POST"])
def record_adherence(med_id):
    data = request.get_json()
    # FIXME: no validation here
    med = Medication.query.get(med_id)
    if not med:
        return jsonify({"error": "not found"}), 404
    # TODO: check drug interactions before recording
    med.record_taken(data.get("taken_at"))
    return jsonify({"status": "ok"})
''',
    "src/api/routes/alerts.py": '''\
from flask import Blueprint, jsonify
# TODO: wire up AI interaction engine
alerts_bp = Blueprint("alerts", __name__)

@alerts_bp.route("/alerts", methods=["GET"])
def list_alerts():
    # HACK: returning static data for now
    return jsonify([])
''',
    "src/api/middleware/auth.py": '''\
from functools import wraps
from flask import request, jsonify

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "unauthorized"}), 401
        # TODO: validate JWT properly
        return f(*args, **kwargs)
    return decorated
''',
    "src/models/medication.py": '''\
from datetime import datetime
from src.utils.db import db

class Medication(db.Model):
    __tablename__ = "medications"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    rxcui = db.Column(db.String(20))  # RxNorm concept ID
    patient_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def record_taken(self, taken_at):
        # FIXME: no error handling
        pass

    def to_dict(self):
        return {"id": self.id, "name": self.name, "rxcui": self.rxcui}
''',
    "src/models/patient.py": '''\
from src.utils.db import db

class Patient(db.Model):
    __tablename__ = "patients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    dob = db.Column(db.Date)
    # XXX: no HIPAA audit log
''',
    "src/services/notification/sms.py": '''\
import os

def send_sms_alert(phone_number, message):
    # TODO: implement retry logic
    api_key = os.getenv("SMS_API_KEY")
    if not api_key:
        raise ValueError("SMS_API_KEY not set")
    print(f"[SMS] {phone_number}: {message}")
''',
    "src/services/auth/jwt_service.py": '''\
import jwt
import os

SECRET = os.getenv("JWT_SECRET", "insecure-default")

def encode_token(payload):
    return jwt.encode(payload, SECRET, algorithm="HS256")

def decode_token(token):
    # HACK: no expiry check
    return jwt.decode(token, SECRET, algorithms=["HS256"])
''',
    "src/utils/db.py": '''\
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
''',
    "src/utils/logger.py": '''\
import logging
logger = logging.getLogger("medtrack")
''',
    "tests/unit/test_medication.py": '''\
import pytest

def test_medication_to_dict():
    # TODO: write real tests
    pass
''',
    "tests/integration/test_adherence_api.py": '''\
# FIXME: integration tests not wired to test DB
def test_record_adherence():
    pass
''',
    "config/settings.py": '''\
DEBUG = True
DATABASE_URI = "postgresql://localhost/medtrack_dev"
SENTRY_DSN = ""  # TODO: add Sentry for error tracking
''',
    "migrations/001_initial.sql": '''\
CREATE TABLE patients (id SERIAL PRIMARY KEY, name VARCHAR(200), dob DATE);
CREATE TABLE medications (id SERIAL PRIMARY KEY, name VARCHAR(200), rxcui VARCHAR(20), patient_id INTEGER, created_at TIMESTAMP);
''',
    "scripts/seed_data.py": '''\
# Seeds dev DB with sample patients and medications
print("Seeding...")
''',
    "docs/architecture_overview.md": '''\
# MedTrack Architecture

## Current Stack
- Flask REST API
- PostgreSQL
- Celery for async tasks (not yet wired)
- SMS notifications via third-party

## Known Gaps
- No drug interaction checking
- No HIPAA audit trail
- Alerts system is stub only
''',
}

for path, content in files.items():
    full_path = os.path.join(WORKSPACE, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- CLAUDE.md ---
claude_md = """\
# MedTrack Project Context

## Project
Medication adherence tracking SaaS for chronic disease patients.

## Tech Stack
- Backend: Flask + SQLAlchemy + PostgreSQL
- Async: Celery (partially wired)
- Notifications: SMS via third-party provider
- Auth: JWT

## Current Sprint Goal
Add AI-powered drug interaction alert system.

## Team Norms
- All new code paths must have unit tests
- Error handling must be explicit — no bare except
- HIPAA compliance is required for all patient data access
- Feature flags required for all new AI features

## Known Technical Debt
- JWT auth does not validate expiry
- No structured logging — using print() in several places
- Celery not yet connected to alert pipeline
"""
with open(os.path.join(WORKSPACE, "CLAUDE.md"), "w") as f:
    f.write(claude_md)

# --- TODOS.md ---
todos_md = """\
# TODOS

## Critical
- [ ] HIPAA audit log for all patient data reads
- [ ] JWT token expiry validation
- [ ] Integrate Sentry for error tracking

## Medium Priority
- [ ] Drug interaction check before recording adherence
- [ ] Pagination for /medications endpoint
- [ ] Celery retry logic for SMS alerts

## Low Priority
- [ ] Add integration test DB fixture
- [ ] Seed data script for staging
"""
with open(os.path.join(WORKSPACE, "TODOS.md"), "w") as f:
    f.write(todos_md)

# --- .context/drug_interaction_design.md (design doc — the agent must find this) ---
design_doc = """\
# Design: AI Drug Interaction Alert System

## Problem Statement
Patients on multiple chronic medications face serious risk from drug interactions.
Currently, MedTrack records adherence but performs zero interaction checking.
Clinical partners report 3 near-miss events in the past quarter due to unreported polypharmacy.

## Constraints
- Must not add latency > 200ms to the adherence recording API endpoint
- Must be HIPAA-compliant (no PHI sent to external AI APIs without BAA)
- Must degrade gracefully — if AI service is down, adherence recording still works
- Feature flag required: `ff_drug_interaction_ai`

## Proposed Approach
1. On each adherence record POST, extract RxCUI codes for all active patient medications
2. Call an internal AI microservice (not external) that wraps an approved LLM with a BAA
3. If interaction detected (confidence > 0.85), create an alert and notify patient + prescriber via SMS
4. Log all AI decisions with patient_id, medication_ids, confidence_score, action_taken

## Out of Scope (for this sprint)
- Real-time EHR sync
- Patient-facing mobile app changes
- Multi-language alert messages

## Open Questions
- What happens if the AI service returns confidence = 0.84? (below threshold — no alert, but log)
- Who owns the alert if the prescriber SMS fails?
- How do we handle duplicate alerts for the same interaction within 24h?
"""
with open(os.path.join(WORKSPACE, ".context/drug_interaction_design.md"), "w") as f:
    f.write(design_doc)

# --- Make multiple git commits to simulate history ---
commit_data = [
    ("Initial project scaffold", [
        "src/utils/db.py", "src/utils/logger.py", "config/settings.py",
        "migrations/001_initial.sql"
    ]),
    ("Add patient and medication models", [
        "src/models/medication.py", "src/models/patient.py"
    ]),
    ("Add medications API routes", [
        "src/api/routes/medications.py", "src/api/middleware/auth.py"
    ]),
    ("Add stub alerts route", [
        "src/api/routes/alerts.py"
    ]),
    ("Add SMS notification service", [
        "src/services/notification/sms.py", "src/services/auth/jwt_service.py"
    ]),
    ("Add docs and todos", [
        "docs/architecture_overview.md", "CLAUDE.md", "TODOS.md",
        "tests/unit/test_medication.py", "tests/integration/test_adherence_api.py",
        "scripts/seed_data.py"
    ]),
    ("Add drug interaction design doc", [
        ".context/drug_interaction_design.md"
    ]),
]

for message, files_to_add in commit_data:
    subprocess.run(["git", "add"] + files_to_add, cwd=WORKSPACE, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=WORKSPACE, check=True)

print("Workspace generated successfully.")
print(f"Files in workspace: {sum(1 for _ in os.walk(WORKSPACE))}")