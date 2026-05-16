import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic deeply nested directory structure for a content moderation platform
dirs = [
    "moderation_platform/src/classifiers",
    "moderation_platform/src/pipelines",
    "moderation_platform/src/utils",
    "moderation_platform/tests/unit",
    "moderation_platform/tests/integration",
    "moderation_platform/config/environments",
    "moderation_platform/config/policies",
    "moderation_platform/data/samples",
    "moderation_platform/data/outputs",
    "moderation_platform/docs",
    "moderation_platform/scripts",
    "moderation_platform/.github/workflows",
    "audit_logs/2024/q1",
    "audit_logs/2024/q2",
    "reports/monthly",
    "reports/compliance",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "moderation_platform/src/classifiers/toxicity_v1.py": '''"""Legacy toxicity classifier - DO NOT USE in production."""
import re

def classify_toxicity(text):
    # Naive keyword-based approach
    bad_words = ["hate", "kill", "spam"]
    score = sum(1 for w in bad_words if w in text.lower())
    return {"toxic": score > 0, "confidence": min(score * 0.3, 0.9)}
''',
    "moderation_platform/src/classifiers/toxicity_v2.py": '''"""Improved toxicity classifier with context awareness."""
class ToxicityClassifierV2:
    VERSION = "2.1.0"
    
    def __init__(self, threshold=0.75):
        self.threshold = threshold
    
    def predict(self, text):
        # Placeholder for ML model inference
        return {"toxic": False, "confidence": 0.88, "reason": "context_clear"}
''',
    "moderation_platform/src/pipelines/moderation_pipeline.py": '''"""Main moderation pipeline orchestrator."""
from typing import List, Dict

class ModerationPipeline:
    def __init__(self, classifiers: List):
        self.classifiers = classifiers
    
    def run(self, content: str) -> Dict:
        results = [c.predict(content) for c in self.classifiers]
        return {"results": results, "status": "pending_review"}
''',
    "moderation_platform/src/utils/content_hash.py": '''"""Utility for content deduplication."""
import hashlib

def hash_content(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]
''',
    "moderation_platform/tests/unit/test_toxicity.py": '''import pytest
# placeholder tests
def test_basic():
    assert True
''',
    "moderation_platform/tests/integration/test_pipeline.py": '''"""Integration tests for moderation pipeline."""
import subprocess
import json

def test_pipeline_runs():
    # This test requires the consensus board to be initialized
    pass
''',
    "moderation_platform/config/environments/development.json": json.dumps({
        "environment": "development",
        "log_level": "DEBUG",
        "database": {"host": "localhost", "port": 5432},
        "feature_flags": {"use_consensus": True, "use_v2_classifier": True}
    }, indent=2),
    "moderation_platform/config/environments/production.json": json.dumps({
        "environment": "production",
        "log_level": "WARNING",
        "database": {"host": "prod-db.internal", "port": 5432},
        "feature_flags": {"use_consensus": True, "use_v2_classifier": True}
    }, indent=2),
    "moderation_platform/config/policies/content_policy_v3.json": json.dumps({
        "version": "3.0",
        "categories": ["hate_speech", "violence", "spam", "misinformation"],
        "escalation_threshold": 0.8,
        "auto_remove_threshold": 0.95,
        "review_required_above": 0.65
    }, indent=2),
    "moderation_platform/data/samples/test_content.jsonl": '\n'.join([
        json.dumps({"id": f"post_{i}", "text": f"Sample content item {i}", "flagged": random.choice([True, False])})
        for i in range(1, 8)
    ]),
    "moderation_platform/docs/architecture.md": """# Moderation Platform Architecture

## Overview
The platform uses a multi-stage pipeline to evaluate content:
1. Automated classifiers (v1, v2)
2. **Consensus adjudication** for borderline cases
3. Final audit logging

## Consensus Workflow
When classifiers disagree, the platform initiates a structured review:
- Multiple agents submit their verdict
- Reviewers cast votes on submissions
- Policy determines the winner

See `consensus_quickstart.sh` for setup commands.
""",
    "moderation_platform/scripts/setup_board.sh": """#!/bin/bash
# TODO: initialize and configure the consensus board
# This script is incomplete - needs implementation
echo "Board setup not yet implemented"
""",
    "moderation_platform/.github/workflows/ci.yml": """name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: python3 -m pytest tests/
""",
    "audit_logs/2024/q1/audit_001.jsonl": '\n'.join([
        json.dumps({"timestamp": f"2024-0{i}-15T10:00:00Z", "action": "content_reviewed", "outcome": random.choice(["approved", "rejected", "escalated"])})
        for i in range(1, 4)
    ]),
    "audit_logs/2024/q2/audit_002.jsonl": '\n'.join([
        json.dumps({"timestamp": f"2024-0{i+3}-10T09:00:00Z", "action": "content_reviewed", "outcome": random.choice(["approved", "rejected"])})
        for i in range(1, 4)
    ]),
    "reports/compliance/q2_2024_report.md": """# Q2 2024 Compliance Report

## Summary
- Total items reviewed: 15,482
- Auto-approved: 12,301 (79.5%)
- Auto-rejected: 1,847 (11.9%)
- Escalated to consensus: 1,334 (8.6%)

## Pending Actions
- Initialize consensus board with SQLite backend for better concurrency
- Migrate from JSON storage to SQLite
- Implement APPROVAL_VOTE policy for borderline cases
""",
    "reports/monthly/october_2024.json": json.dumps({
        "month": "2024-10",
        "total_reviews": 5200,
        "consensus_required": 412,
        "avg_consensus_time_seconds": 47,
        "policy_used": "APPROVAL_VOTE"
    }, indent=2),
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# The core task specification file - describes the business requirement
task_spec = {
    "task": "content_moderation_consensus_run",
    "description": "A disputed piece of content requires adjudication via structured multi-agent consensus.",
    "content_under_review": "This product is absolutely terrible and the company should be shut down. Complete garbage.",
    "content_id": "post_disputed_8821",
    "review_context": "Two automated agents have produced competing moderation verdicts. A structured vote-based consensus process must determine the final outcome.",
    "agent_verdicts": [
        {
            "agent_id": "classifier_alpha",
            "verdict": {"toxic": False, "confidence": 0.72, "brief_reason": "Negative opinion but not threatening or hateful."},
            "summary": "Content is harsh criticism but does not violate hate speech or harassment policies."
        },
        {
            "agent_id": "classifier_beta",
            "verdict": {"toxic": True, "confidence": 0.81, "brief_reason": "Aggressive language may discourage constructive discourse."},
            "summary": "Content uses aggressive language patterns that border on harassment policy violation."
        }
    ],
    "vote_instructions": {
        "reviewer_alpha": {"votes_for": "classifier_alpha", "vote_type": "YES"},
        "reviewer_beta": {"votes_for": "classifier_alpha", "vote_type": "YES"},
        "reviewer_gamma": {"votes_for": "classifier_beta", "vote_type": "YES"},
    },
    "required_policy": "APPROVAL_VOTE",
    "required_storage_backend": "sqlite",
    "output_file": "consensus_verdict.json"
}

with open(os.path.join(workspace, "moderation_platform/data/task_spec.json"), "w") as f:
    json.dump(task_spec, f, indent=2)

print("Workspace generated successfully.")
print(f"Task spec written to: {workspace}/moderation_platform/data/task_spec.json")