import os
import random

random.seed(42)

workspace = "/workspace"

# --- Directory structure ---
dirs = [
    "paystream/docs/architecture",
    "paystream/docs/compliance",
    "paystream/docs/incidents",
    "paystream/src/api",
    "paystream/src/auth",
    "paystream/src/payments",
    "paystream/src/notifications",
    "paystream/infra/terraform",
    "paystream/infra/k8s",
    "paystream/tests/unit",
    "paystream/tests/integration",
    "paystream/monitoring",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---

# Architecture diagram (text-based, messy)
with open(os.path.join(workspace, "paystream/docs/architecture/system_overview.txt"), "w") as f:
    f.write("""PayStream Real-Time Payment Platform - System Overview
=======================================================
Last updated: 2023-11-01 (DRAFT - not final)

Components:
- Mobile App (iOS/Android) - customer-facing
- Merchant Portal (Web) - merchant dashboard
- API Gateway (Kong) - entry point for all external requests
- Auth Service - handles OAuth2 tokens and session management
- Payment Processor - core business logic, calls external bank APIs
- Card Tokenization Service - stores/retrieves card tokens
- Settlement Engine - batch job, runs nightly
- Notification Service - sends SMS/email via third-party providers
- PostgreSQL (primary DB) - transactional data
- Redis Cache - session tokens, rate limit counters
- Kafka - event streaming between services
- Admin Panel - internal staff only, on VPN
- Bank APIs (external) - Visa, Mastercard, ACH networks
- Fraud Detection Service (third-party) - calls out to external ML API

Data flows (approximate):
1. Customer/Merchant -> API Gateway -> Auth Service -> Payment Processor -> DB
2. Payment Processor -> Bank APIs (external)
3. Payment Processor -> Card Tokenization Service -> DB
4. Payment Processor -> Kafka -> Settlement Engine -> DB
5. Payment Processor -> Kafka -> Notification Service -> Third-party SMS/email
6. Payment Processor -> Fraud Detection Service (external)
7. Admin Panel -> API Gateway -> Auth Service -> (all internal services)

Known issues (from last sprint):
- Rate limiting on API Gateway not yet configured for all endpoints
- Card Tokenization Service logs full PAN in debug mode (ticket #4821 - open)
- Settlement Engine runs with DB admin privileges (legacy, not yet fixed)
- Admin Panel accessible from public internet with VPN auth only
- Auth tokens expire after 24h (long expiry requested by merchants)
""")

# Compliance notes
with open(os.path.join(workspace, "paystream/docs/compliance/pci_notes.txt"), "w") as f:
    f.write("""PCI-DSS Compliance Notes (Preliminary)
=======================================
- PCI-DSS Level 1 certification pending
- Cardholder data must be encrypted at rest (AES-256)
- All card operations must be logged
- Admin access must use MFA
- Network segmentation required between card data environment and other systems
- Annual penetration testing required
- Incident response plan: NOT YET WRITTEN

Regulatory notes:
- GDPR applies to EU customers
- FinCEN reporting for transactions > $10,000
- FFIEC guidelines for authentication
""")

# Incident history
with open(os.path.join(workspace, "paystream/docs/incidents/past_incidents.txt"), "w") as f:
    f.write("""Past Security Incidents (Internal - Confidential)
=================================================
2022-03: Merchant Portal - CSRF attack allowed unauthorized fund transfer initiation.
         Mitigated: CSRF tokens added to all forms. No customer funds lost.

2022-09: API Gateway - A merchant's API key was leaked in a public GitHub repo.
         Attacker used key to initiate test transactions. Detected by anomaly alerts.
         Mitigated: Key revoked. Now scanning public repos for leaked keys.

2023-02: Auth Service - Brute force attack on merchant login. 50k attempts over 2 days.
         Account lockout was not enabled. Now enabled (5 attempts -> 30min lockout).

2023-06: Card Tokenization Service - Debug logs containing partial card numbers found
         in S3 bucket with public read access. Bucket now private. Full audit underway.
""")

# API spec (messy/incomplete)
with open(os.path.join(workspace, "paystream/src/api/openapi_draft.yaml"), "w") as f:
    f.write("""openapi: 3.0.0
info:
  title: PayStream API
  version: 0.9.1-draft
paths:
  /v1/payments:
    post:
      summary: Initiate payment
      # TODO: add auth requirement
  /v1/payments/{id}:
    get:
      summary: Get payment status
  /v1/cards/tokenize:
    post:
      summary: Tokenize card
      # WARNING: currently returns token AND last4 in same response
  /v1/admin/users:
    get:
      summary: List all users (admin only)
      # TODO: add RBAC check
  /v1/merchant/settlements:
    get:
      summary: Get settlement report
""")

# Auth service notes
with open(os.path.join(workspace, "paystream/src/auth/auth_design.md"), "w") as f:
    f.write("""# Auth Service Design Notes

## Current Implementation
- OAuth2 with JWT tokens
- Token expiry: 24 hours (merchant request)
- No refresh token rotation
- MFA: optional for merchants, NOT implemented for customers yet
- Admin accounts: MFA via TOTP required
- Session storage: Redis (shared between all services)

## Known Gaps
- No token binding to device/IP
- Refresh tokens never expire
- No concurrent session limit
- Audit log: only failed logins logged, successful logins NOT logged
""")

# Payment processor notes  
with open(os.path.join(workspace, "paystream/src/payments/payment_flow.md"), "w") as f:
    f.write("""# Payment Processor Flow

1. Validate request (amount, currency, merchant ID)
2. Check fraud score via external Fraud Detection API
3. Call Card Tokenization Service to retrieve card details
4. Submit to appropriate bank network (Visa/MC/ACH)
5. Store result in PostgreSQL
6. Publish event to Kafka
7. Return result to caller

## Issues
- Fraud detection API key hardcoded in config (not in secret manager)
- No idempotency key enforcement -> duplicate payment risk
- Error messages include internal stack traces (sent to merchant)
- No transaction signing - replay attack possible
""")

# Infra notes
with open(os.path.join(workspace, "paystream/infra/terraform/infra_notes.txt"), "w") as f:
    f.write("""Infrastructure Notes
====================
- All services in AWS (us-east-1)
- K8s (EKS) for application tier
- RDS PostgreSQL (multi-AZ)
- ElastiCache Redis
- MSK (Kafka)
- VPC with public/private subnets
- API Gateway (Kong) in public subnet
- All internal services in private subnet
- Admin Panel: EC2 in private subnet, exposed via VPN only
- S3 for settlement reports (previously public - now fixed)
- No WAF currently deployed
- Security Groups: some overly permissive (0.0.0.0/0 on port 5432 in dev, not cleaned up in prod)
""")

# K8s notes
with open(os.path.join(workspace, "paystream/infra/k8s/rbac_notes.txt"), "w") as f:
    f.write("""K8s RBAC Notes
==============
- Most service accounts have cluster-admin for legacy reasons
- Pod security policies not enforced
- Secrets stored as base64 in etcd (not encrypted at rest)
- Network policies: NOT configured (all pods can talk to all pods)
""")

# Monitoring config
with open(os.path.join(workspace, "paystream/monitoring/alerts.yaml"), "w") as f:
    f.write("""alerts:
  - name: high_payment_failure_rate
    threshold: 10%
    window: 5m
  - name: api_latency_p99
    threshold: 2000ms
  # TODO: add security alerts
  # - failed login attempts
  # - unusual transaction patterns
  # - admin access outside business hours
""")

# Test files (distractors)
with open(os.path.join(workspace, "paystream/tests/unit/test_payment.py"), "w") as f:
    f.write("# Unit tests for payment processor\n# TODO: add security test cases\n")

with open(os.path.join(workspace, "paystream/tests/integration/test_api.py"), "w") as f:
    f.write("# Integration tests\n")

# Notification service
with open(os.path.join(workspace, "paystream/src/notifications/sms_config.txt"), "w") as f:
    f.write("SMS provider: Twilio\nEmail provider: SendGrid\nWebhook callbacks: merchant-defined URLs (no validation)\n")

# Fraud detection notes
with open(os.path.join(workspace, "paystream/src/payments/fraud_detection_notes.txt"), "w") as f:
    f.write("""Fraud Detection Service Notes
=============================
- Third-party ML API (FraudGuard Inc.)
- Sends: card token, merchant ID, amount, customer IP, device fingerprint
- Receives: risk score 0-100
- API key: hardcoded in payment_processor_config.yaml
- No fallback if service is unavailable -> payment blocked entirely
- Data sharing agreement: NOT yet reviewed by legal
""")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")