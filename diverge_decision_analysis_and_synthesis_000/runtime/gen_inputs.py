import os
import random

random.seed(42)

BASE = "/workspace"

# Directory structure - deeply nested, realistic healthcare tech project
dirs = [
    "docs/architecture",
    "docs/compliance",
    "docs/meeting_notes",
    "docs/product",
    "docs/legal",
    "src/backend/api",
    "src/backend/models",
    "src/frontend/components",
    "tests/unit",
    "tests/integration",
    "data/clinical_trials",
    "data/user_research",
    "reports/q3",
    "reports/q4",
    "config",
    "scripts",
    "stakeholder_inputs",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ---- DISTRACTOR FILES ----

distractor_files = {
    "docs/architecture/system_overview.md": """# System Architecture Overview
MediAssist Platform v2.3
- Microservices: auth-service, patient-service, recommendation-engine
- Database: PostgreSQL 14, Redis cache
- Deployment: Kubernetes on AWS EKS
Last updated: 2024-01-15
""",
    "docs/architecture/api_gateway.md": """# API Gateway Config
Rate limiting: 1000 req/min per tenant
Auth: JWT RS256
Endpoints prefixed /api/v2/
""",
    "docs/compliance/hipaa_checklist.txt": """HIPAA Compliance Checklist (partial)
[x] Encryption at rest (AES-256)
[x] Audit logging enabled
[ ] Business Associate Agreements - PENDING for 3 vendors
[ ] Annual risk assessment - overdue by 2 months
[!] AI decision audit trail - not yet defined for new features
""",
    "docs/compliance/gdpr_notes.txt": """GDPR notes - EU expansion Q2
- Data residency: EU-West-1 region required
- Right to erasure: implemented in patient-service v1.4
- Consent management: needs update for AI recommendations
""",
    "docs/meeting_notes/2024_03_12_standup.txt": """Standup 2024-03-12
- Backend: fixing latency in recommendation-engine
- Frontend: new dashboard UI almost done
- Blocker: waiting on legal sign-off for dosage AI feature
""",
    "docs/meeting_notes/2024_03_05_product_sync.txt": """Product sync notes
Discussed: AI dosage recommendation feature timeline
Sarah (PM): wants to launch in Q2
Dev team: needs 6 more weeks for safety testing
Legal: has concerns, reviewing FDA guidance
No consensus reached.
""",
    "docs/meeting_notes/2024_02_20_stakeholder_call.txt": """Stakeholder call recording notes (rough)
Multiple parties expressed concerns and excitement.
Notes incomplete - transcription failed halfway.
Action items: unclear
""",
    "docs/product/roadmap_2024.md": """# Product Roadmap 2024
Q1: Dashboard refresh, mobile app beta
Q2: AI dosage recommendation (PENDING APPROVAL)
Q3: EHR integration
Q4: Predictive readmission alerts
""",
    "docs/product/feature_requests.csv": """feature_id,title,votes,status
F-101,AI dosage recommendation,342,pending
F-102,Voice notes,89,in_dev
F-103,Family caregiver portal,201,backlog
F-104,Insurance pre-auth automation,156,backlog
F-105,Dark mode,412,done
""",
    "docs/legal/fda_samd_guidance_summary.txt": """FDA SaMD (Software as Medical Device) Guidance Summary
- AI/ML-based SaMD requires predicate or De Novo pathway
- Predetermined Change Control Plan (PCCP) needed for adaptive AI
- Post-market surveillance mandatory
- Dosage recommendation classified as Class II device functionality
- Clinical validation studies required before deployment
""",
    "src/backend/models/dosage_model.py": """# Placeholder - do not use in production
# Model under development
import numpy as np

def predict_dosage(patient_data):
    # TODO: replace with validated clinical model
    return np.random.choice([10, 20, 50], p=[0.5, 0.3, 0.2])
""",
    "src/backend/api/recommendation_endpoint.py": """# DRAFT - not reviewed
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/api/v2/recommend/dosage', methods=['POST'])
def recommend_dosage():
    data = request.json
    # TODO: integrate validated model
    return jsonify({'recommendation': 'pending_validation', 'confidence': 0.0})
""",
    "tests/unit/test_dosage_model.py": """import pytest
# Unit tests for dosage model - INCOMPLETE
def test_output_range():
    pass  # TODO

def test_edge_cases():
    pass  # TODO
""",
    "data/clinical_trials/trial_summary_draft.txt": """Clinical Trial Summary (DRAFT - v0.2 - NOT REVIEWED)
Study: AI-assisted dosage for chronic pain management
N=87 (small sample, underpowered)
Primary endpoint: dosage accuracy vs. physician baseline
Result: 71% concordance (CI: 64-78%)
Note: Trial excluded patients >75yo and pediatric cases
Adverse events: 2 cases of under-dosing flagged by supervising physician
Status: Awaiting IRB review of extended trial
""",
    "data/user_research/survey_results_2024.csv": """respondent_id,role,would_use_ai_dosage,concern_level,top_concern
1,patient,yes,high,safety
2,caregiver,maybe,high,liability
3,patient,no,very_high,trust
4,physician,yes,medium,accuracy
5,patient,yes,low,none
6,caregiver,no,high,errors
7,physician,maybe,high,liability
8,patient,yes,medium,privacy
""",
    "reports/q3/quarterly_review.md": """# Q3 2024 Review
- MAU: 24,500 (+12% QoQ)
- Churn: 4.2% (up from 3.1% - investigation needed)
- NPS: 42
- Top churn reason: 'missing features' (38% of exit surveys)
""",
    "reports/q4/metrics_snapshot.txt": """Q4 snapshot (preliminary)
MAU: 26,100
Top requested feature: AI dosage recommendation (mentioned in 28% of support tickets)
""",
    "config/feature_flags.yaml": """features:
  ai_dosage_recommendation:
    enabled: false
    rollout_percentage: 0
    requires_approval: true
    approval_status: pending
  voice_notes:
    enabled: true
    rollout_percentage: 100
""",
    "scripts/run_compliance_check.sh": """#!/bin/bash
echo "Running compliance checks..."
# Stub - not implemented
exit 0
""",
}

for fpath, content in distractor_files.items():
    full_path = os.path.join(BASE, fpath)
    with open(full_path, "w") as f:
        f.write(content)

# ---- THE ACTUAL PROBLEM: The feature brief the agent must analyze ----
feature_brief = """INTERNAL BRIEF — MediAssist AI Dosage Recommendation Feature
Date: 2024-04-01
Prepared by: Product Team

BACKGROUND:
MediAssist is a telehealth platform used by 26,000+ monthly active users including patients
with chronic conditions, their family caregivers, and licensed physicians. We are evaluating
whether to ship an AI-powered medication dosage recommendation engine to be surfaced directly
to patients and physicians within our app.

THE FEATURE:
- The AI model analyzes patient history, current medications, and lab results
- It outputs a suggested dosage for common chronic-condition medications
- Physicians can approve, modify, or reject recommendations
- Patients can see "suggested" dosage before their physician reviews it
- Caregivers can view recommendations on behalf of family members
- Insurance pre-authorization would be triggered automatically if physician approves

KNOWN TENSIONS:
- Some physicians see this as clinical decision support; others see it as liability exposure
- Patients want faster answers; patient advocates raise safety concerns
- The current clinical trial has a small sample and excludes elderly/pediatric populations
- FDA has classified this as a Class II SaMD (Software as Medical Device) — regulatory path unclear
- Insurance companies may deny claims if AI-generated dosages differ from formulary
- Security: patient PHI (Protected Health Information) flows through the recommendation engine
- The model has 71% concordance with physician baseline — below the 85% internal threshold

DECISION NEEDED:
Leadership needs a comprehensive multi-stakeholder analysis of whether to:
  (A) Launch as-is in Q2
  (B) Delay and conduct additional validation
  (C) Launch in a restricted pilot (physicians-only view)
  (D) Abandon the feature entirely

Please produce a thorough analysis. This decision affects patient safety, regulatory standing,
and company growth trajectory.
"""

with open(os.path.join(BASE, "stakeholder_inputs", "ai_dosage_feature_brief.txt"), "w") as f:
    f.write(feature_brief)

# A partial, incomplete stakeholder note (messy, unhelpful on its own)
partial_notes = """Rough notes from 1:1s (not synthesized):
- Dr. Chen: "71% is not enough. I wouldn't trust it for my patients yet."
- Maria (caregiver): "I just want to help my mom, any tool helps"
- Insurance rep: "we'd need to audit every AI-approved recommendation"
- Patient focus group word cloud: safety, trust, speed, error, helpful
- Regulator contact: "you need a predicate or De Novo before launch"
These are NOT complete perspectives. Do not use as final analysis.
"""
with open(os.path.join(BASE, "stakeholder_inputs", "rough_1on1_notes.txt"), "w") as f:
    f.write(partial_notes)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 2}")