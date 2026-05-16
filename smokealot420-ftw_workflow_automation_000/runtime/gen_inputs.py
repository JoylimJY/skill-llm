import os
import random
import stat

random.seed(42)

workspace = "/workspace"

# ── 1. Create a realistic Python microservice project (the "patient scheduler") ──
src_dirs = [
    "patient_scheduler/api",
    "patient_scheduler/models",
    "patient_scheduler/services",
    "patient_scheduler/utils",
    "patient_scheduler/tests",
    "patient_scheduler/config",
    "patient_scheduler/migrations",
    "patient_scheduler/scripts",
    "docs/architecture",
    "infra/docker",
    "infra/k8s",
]
for d in src_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

files = {
    "patient_scheduler/__init__.py": '"""Patient Appointment Scheduler Service"""\n__version__ = "0.1.0"\n',
    "patient_scheduler/api/__init__.py": "",
    "patient_scheduler/api/appointments.py": '''from flask import Blueprint, request, jsonify
appointments_bp = Blueprint("appointments", __name__)

@appointments_bp.route("/appointments", methods=["GET"])
def list_appointments():
    # TODO: implement
    return jsonify([])

@appointments_bp.route("/appointments", methods=["POST"])
def create_appointment():
    data = request.json
    # TODO: validate and persist
    return jsonify({"id": "new-id", "status": "pending"}), 201
''',
    "patient_scheduler/api/patients.py": '''from flask import Blueprint, request, jsonify
patients_bp = Blueprint("patients", __name__)

@patients_bp.route("/patients/<patient_id>", methods=["GET"])
def get_patient(patient_id):
    # TODO: implement DB lookup
    return jsonify({"id": patient_id, "name": "Unknown"})
''',
    "patient_scheduler/models/__init__.py": "",
    "patient_scheduler/models/appointment.py": '''import dataclasses
from datetime import datetime

@dataclasses.dataclass
class Appointment:
    id: str
    patient_id: str
    provider_id: str
    scheduled_at: datetime
    status: str = "pending"
    notes: str = ""
''',
    "patient_scheduler/models/patient.py": '''import dataclasses

@dataclasses.dataclass
class Patient:
    id: str
    first_name: str
    last_name: str
    dob: str
    insurance_id: str = ""
''',
    "patient_scheduler/models/provider.py": '''import dataclasses

@dataclasses.dataclass
class Provider:
    id: str
    name: str
    specialty: str
    available_slots: list = dataclasses.field(default_factory=list)
''',
    "patient_scheduler/services/__init__.py": "",
    "patient_scheduler/services/scheduler.py": '''class SchedulerService:
    def __init__(self, db):
        self.db = db

    def book_appointment(self, patient_id, provider_id, slot):
        # TODO: check availability, conflict detection
        raise NotImplementedError

    def cancel_appointment(self, appointment_id):
        raise NotImplementedError

    def reschedule(self, appointment_id, new_slot):
        raise NotImplementedError
''',
    "patient_scheduler/services/notifications.py": '''class NotificationService:
    def send_reminder(self, appointment_id):
        # TODO: integrate with email/SMS
        pass

    def send_cancellation_notice(self, appointment_id):
        pass
''',
    "patient_scheduler/utils/__init__.py": "",
    "patient_scheduler/utils/validators.py": '''def validate_date_format(date_str: str) -> bool:
    """Check if date_str is ISO 8601 format."""
    from datetime import datetime
    try:
        datetime.fromisoformat(date_str)
        return True
    except ValueError:
        return False
''',
    "patient_scheduler/utils/helpers.py": '''import uuid

def generate_id() -> str:
    return str(uuid.uuid4())
''',
    "patient_scheduler/config/__init__.py": "",
    "patient_scheduler/config/settings.py": '''import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/scheduler_dev")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
''',
    "patient_scheduler/tests/__init__.py": "",
    "patient_scheduler/tests/test_appointments.py": '''import pytest

def test_create_appointment_placeholder():
    # TODO: replace with real tests
    assert True

def test_list_appointments_placeholder():
    assert True
''',
    "patient_scheduler/migrations/001_initial.sql": '''-- Initial schema
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    insurance_id VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients(id),
    provider_id UUID,
    scheduled_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT \'pending\',
    notes TEXT
);
''',
    "patient_scheduler/scripts/seed_data.py": '''"""Seed the database with test data."""
# TODO: implement
print("Seed data script - not yet implemented")
''',
    "docs/architecture/overview.md": '''# Architecture Overview

The patient scheduler service handles:
- Appointment booking and management
- Provider availability tracking
- Patient record access (read-only from EHR)
- Notification dispatch

## Components
- REST API (Flask)
- PostgreSQL database
- Redis for caching availability
- Celery for async notifications
''',
    "docs/architecture/data_flow.md": '''# Data Flow

1. Patient requests appointment via API
2. Service checks provider availability
3. Conflict detection runs
4. Appointment persisted to DB
5. Confirmation notification sent
''',
    "infra/docker/Dockerfile": '''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run"]
''',
    "infra/docker/docker-compose.yml": '''version: "3.9"
services:
  api:
    build: .
    ports:
      - "5000:5000"
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: scheduler_dev
  redis:
    image: redis:7
''',
    "infra/k8s/deployment.yaml": '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: patient-scheduler
spec:
  replicas: 2
  selector:
    matchLabels:
      app: patient-scheduler
  template:
    metadata:
      labels:
        app: patient-scheduler
    spec:
      containers:
      - name: scheduler
        image: patient-scheduler:latest
        ports:
        - containerPort: 5000
''',
    "requirements.txt": '''flask>=2.3
psycopg2-binary>=2.9
redis>=4.6
celery>=5.3
pytest>=7.4
dataclasses-json>=0.6
''',
    "setup.py": '''from setuptools import setup, find_packages

setup(
    name="patient-scheduler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["flask", "psycopg2-binary", "redis"],
)
''',
    ".gitignore": '''__pycache__/
*.pyc
.env
*.egg-info/
dist/
build/
.pytest_cache/
''',
}

for path, content in files.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── 2. Initialize git repo ──
os.system(f"cd {workspace} && git init && git add -A && git commit -m 'Initial project scaffold'")

print("Workspace generated successfully.")
print("Project: patient_scheduler microservice")
print("No PRD, PRPs, or WORKFLOW.md exist — agent must bootstrap PIV structure.")