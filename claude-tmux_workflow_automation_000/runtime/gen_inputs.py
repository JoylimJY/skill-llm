#!/usr/bin/env python3
"""
Generate the sandbox workspace with distractor files and project structure.
The actual tmux sessions are created in setup_script.sh (runtime).
"""
import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Project directory structure (distractors) ---
dirs = [
    "phoenix-api/src/auth",
    "phoenix-api/src/handlers",
    "phoenix-api/src/models",
    "phoenix-api/tests/unit",
    "phoenix-api/tests/integration",
    "phoenix-api/.github/workflows",
    "phoenix-api/docs",
    "phoenix-api/scripts",
    "infra/terraform/modules",
    "infra/k8s/manifests",
    "shared/utils",
    "shared/config",
    "logs/2024-01",
    "logs/2024-02",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor source files
files = {
    "phoenix-api/src/auth/jwt_handler.py": """\
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "dev-secret-only"

def generate_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=1)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
""",
    "phoenix-api/src/handlers/review_handler.py": """\
from flask import Blueprint, request, jsonify
from ..models.review import Review

review_bp = Blueprint('reviews', __name__)

@review_bp.route('/reviews', methods=['POST'])
def create_review():
    data = request.get_json()
    if not data.get('code'):
        return jsonify({'error': 'code field required'}), 400
    review = Review.from_dict(data)
    review.save()
    return jsonify(review.to_dict()), 201
""",
    "phoenix-api/src/models/review.py": """\
from dataclasses import dataclass, field
from typing import Optional
import uuid

@dataclass
class Review:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    code: str = ''
    language: str = 'python'
    status: str = 'pending'
    comments: Optional[str] = None

    def save(self):
        pass  # TODO: persist to DB

    @classmethod
    def from_dict(cls, d: dict) -> 'Review':
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}
""",
    "phoenix-api/tests/unit/test_review.py": """\
import pytest
from phoenix_api.src.models.review import Review

def test_review_defaults():
    r = Review(code='print(1)')
    assert r.language == 'python'
    assert r.status == 'pending'
    assert r.id is not None
""",
    "phoenix-api/tests/integration/test_api.py": """\
import requests

BASE = 'http://localhost:5000'

def test_post_review():
    resp = requests.post(f'{BASE}/reviews', json={'code': 'x=1'})
    assert resp.status_code == 201
""",
    "phoenix-api/.github/workflows/ci.yml": """\
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/
""",
    "phoenix-api/docs/architecture.md": """\
# Phoenix API Architecture

## Overview
REST API built with Flask. Handles code review requests.

## Components
- Auth: JWT-based authentication
- Handlers: Route definitions
- Models: Data layer (DB-backed via SQLAlchemy)
""",
    "phoenix-api/scripts/seed_db.py": """\
#!/usr/bin/env python3
# Seeds development database with sample data
from phoenix_api.src.models.review import Review
samples = [
    Review(code='def hello(): pass', language='python'),
    Review(code='const x = 1;', language='javascript'),
]
for s in samples:
    s.save()
print(f'Seeded {len(samples)} reviews.')
""",
    "infra/terraform/modules/rds.tf": """\
resource "aws_db_instance" "main" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "15.2"
  instance_class       = "db.t3.micro"
  db_name              = "phoenix_db"
  username             = var.db_user
  password             = var.db_password
  skip_final_snapshot  = true
}
""",
    "infra/k8s/manifests/deployment.yaml": """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: phoenix-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: phoenix-api
  template:
    spec:
      containers:
      - name: phoenix-api
        image: phoenix-api:latest
        ports:
        - containerPort: 5000
""",
    "shared/utils/logger.py": """\
import logging
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
        logger.addHandler(h)
    logger.setLevel(logging.DEBUG)
    return logger
""",
    "shared/config/settings.py": """\
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/phoenix_dev')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
""",
    "logs/2024-01/app.log": """\
2024-01-15 09:12:33 INFO api: Server started on port 5000
2024-01-15 09:13:01 INFO api: POST /reviews 201 42ms
2024-01-15 09:13:45 ERROR api: DB connection timeout after 30s
2024-01-15 09:14:02 INFO api: DB reconnected
""",
    "logs/2024-02/app.log": """\
2024-02-03 11:00:00 INFO api: Deploy v1.4.2
2024-02-03 11:00:05 INFO api: Health check OK
2024-02-03 14:22:17 WARN api: Rate limit approaching for user abc123
""",
}

for rel_path, content in files.items():
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# Write a task context file — business description only, no hints about tmux workflow
task_context = """\
PROJECT: phoenix-api
AI ASSISTANT SESSION: phoenix-api

The team has an AI coding assistant running in a background terminal session
named 'phoenix-api'. It has been helping with code reviews.

Your task:
1. Check the current state of the AI assistant session 'phoenix-api' and retrieve
   the most recent conversation exchange shown in its terminal.
2. Send the following message to the assistant and wait for its response:
   "What are the top 3 risks in the current JWT implementation?"
3. After receiving the response, trigger a memory optimization routine on the assistant.
4. Save a report to a file called 'session_report.txt' containing:
   - The target pane identifier you used (e.g. session:window.pane)
   - The last exchange you found before sending your message (both the user prompt line and the AI reply line)
   - The full response from the assistant to your new question
   - A confirmation line that the memory optimization was triggered
"""
(workspace / "TASK.txt").write_text(task_context)

print("Workspace generated successfully.")