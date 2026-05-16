#!/usr/bin/env python3
"""
Generate the sandbox workspace for the pharmaceutical supply-chain
event-driven architecture design task.
"""

import json
import os
import random
import yaml

random.seed(42)

BASE = "/workspace"

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "current_system/services",
    "current_system/api_specs",
    "current_system/incidents",
    "current_system/db_schemas",
    "infra/monitoring",
    "infra/networking",
    "docs/legacy",
    "docs/meetings",
    "ops/runbooks",
    "ops/alerts",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── helper ──────────────────────────────────────────────────────────────────
def write_json(path, obj):
    with open(os.path.join(BASE, path), "w") as f:
        json.dump(obj, f, indent=2)

def write_yaml(path, obj):
    with open(os.path.join(BASE, path), "w") as f:
        yaml.dump(obj, f, default_flow_style=False)

def write_text(path, text):
    with open(os.path.join(BASE, path), "w") as f:
        f.write(text)

# ── current system: service definitions ────────────────────────────────────
services = {
    "order_service": {
        "name": "OrderService",
        "language": "Java 17",
        "database": "PostgreSQL 14",
        "description": "Receives new drug orders from pharmacies, validates stock, writes to orders table, then synchronously calls InventoryService and ShippingService.",
        "endpoints": [
            "POST /orders",
            "GET /orders/{id}",
            "PUT /orders/{id}/cancel"
        ],
        "sync_calls": ["InventoryService.reserveStock", "ShippingService.createShipment", "BillingService.chargeCustomer", "ComplianceService.auditOrder"],
        "known_issues": [
            "If ShippingService times out, order is left in PENDING with stock already reserved — orphaned reservation.",
            "ComplianceService occasionally returns 503; entire order creation fails and must be retried manually.",
            "No idempotency key on POST /orders — duplicate orders created on client retry."
        ]
    },
    "inventory_service": {
        "name": "InventoryService",
        "language": "Python 3.10",
        "database": "PostgreSQL 14",
        "description": "Tracks drug stock levels per distribution center. Called synchronously by OrderService.",
        "endpoints": ["POST /reserve", "DELETE /reserve/{reservationId}", "GET /stock/{drugId}"],
        "known_issues": [
            "Stock reservation and order confirmation are not atomic — stock can be reserved but order never confirmed.",
            "No event emitted when stock falls below reorder threshold."
        ]
    },
    "shipping_service": {
        "name": "ShippingService",
        "language": "Go 1.21",
        "database": "MySQL 8",
        "description": "Creates and tracks shipments. Integrates with 3PL provider via REST.",
        "endpoints": ["POST /shipments", "GET /shipments/{id}", "POST /shipments/{id}/status"],
        "known_issues": [
            "3PL webhook for delivery confirmation sometimes fires twice — billing charged twice.",
            "No dead-letter handling for failed status updates."
        ]
    },
    "billing_service": {
        "name": "BillingService",
        "language": "Python 3.11",
        "database": "PostgreSQL 14",
        "description": "Charges pharmacies for fulfilled orders.",
        "endpoints": ["POST /charges", "POST /refunds"],
        "known_issues": [
            "Duplicate charges observed when ShippingService webhook fires twice.",
            "Refund process requires manual intervention when upstream order data is inconsistent."
        ]
    },
    "compliance_service": {
        "name": "ComplianceService",
        "language": "Java 11",
        "database": "Oracle 19c",
        "description": "Logs all order and shipment events for FDA/DEA regulatory audit trail. Called synchronously.",
        "endpoints": ["POST /audit-log", "GET /audit-log/{orderId}"],
        "known_issues": [
            "Oracle connection pool exhaustion under load causes 503 errors that propagate to OrderService.",
            "Audit log entries missing when OrderService fails mid-transaction."
        ]
    },
    "notification_service": {
        "name": "NotificationService",
        "language": "Node.js 18",
        "database": "None (stateless)",
        "description": "Sends email/SMS alerts to pharmacies. Called by OrderService after order creation.",
        "endpoints": ["POST /notify"],
        "known_issues": [
            "If notification fails, OrderService rolls back the entire order — pharmacist receives no notification AND order is cancelled.",
        ]
    }
}

for svc_id, svc_data in services.items():
    write_json(f"current_system/services/{svc_id}.json", svc_data)

# ── API specs (messy OpenAPI fragments) ─────────────────────────────────────
order_api_spec = {
    "openapi": "3.0.0",
    "info": {"title": "OrderService API", "version": "2.3.1"},
    "paths": {
        "/orders": {
            "post": {
                "summary": "Create a new drug order",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "pharmacyId": {"type": "string"},
                                    "drugId": {"type": "string"},
                                    "quantity": {"type": "integer"},
                                    "distributionCenterId": {"type": "string"},
                                    "urgency": {"type": "string", "enum": ["ROUTINE", "URGENT", "EMERGENCY"]}
                                },
                                "required": ["pharmacyId", "drugId", "quantity"]
                            }
                        }
                    }
                },
                "responses": {"201": {"description": "Order created"}, "503": {"description": "Downstream failure"}}
            }
        }
    }
}
write_json("current_system/api_specs/order_service_openapi.json", order_api_spec)

# ── incident reports ────────────────────────────────────────────────────────
incidents = [
    {
        "id": "INC-2024-0312",
        "date": "2024-03-12",
        "severity": "P1",
        "title": "Double billing on emergency drug shipments",
        "description": "3PL delivery webhook fired twice for 47 emergency orders. BillingService charged pharmacies twice. Manual refunds took 3 days. Root cause: no idempotency check in BillingService, ShippingService webhook has no deduplication.",
        "affected_services": ["ShippingService", "BillingService"],
        "resolution": "Manual SQL update to reverse charges. No systemic fix deployed."
    },
    {
        "id": "INC-2024-0489",
        "date": "2024-04-28",
        "severity": "P1",
        "title": "Orphaned stock reservations causing drug shortage",
        "description": "ComplianceService 503 storm caused OrderService to roll back 312 orders AFTER InventoryService had already reserved stock. Stock appeared unavailable for 6 hours during a shortage of a controlled substance.",
        "affected_services": ["OrderService", "InventoryService", "ComplianceService"],
        "resolution": "Manual DB update to release reservations. ComplianceService connection pool increased."
    },
    {
        "id": "INC-2024-0601",
        "date": "2024-05-15",
        "severity": "P2",
        "title": "Missing FDA audit log entries",
        "description": "14 orders processed during Oracle maintenance window have no compliance audit log. FDA audit scheduled for Q3. Entries reconstructed manually from application logs.",
        "affected_services": ["ComplianceService", "OrderService"],
        "resolution": "Manual log reconstruction. Oracle maintenance now scheduled during off-peak."
    },
    {
        "id": "INC-2024-0734",
        "date": "2024-06-30",
        "severity": "P2",
        "title": "Pharmacy order cancellations due to NotificationService failure",
        "description": "SMS provider outage caused NotificationService to return 500 for 2 hours. OrderService treated notification failure as a hard error and cancelled 89 valid orders. Pharmacies received neither drugs nor notifications.",
        "affected_services": ["NotificationService", "OrderService"],
        "resolution": "Hotfix: OrderService now ignores notification failures (introduced separate risk of silent failures)."
    }
]
for inc in incidents:
    write_json(f"current_system/incidents/{inc['id']}.json", inc)

# ── DB schemas ───────────────────────────────────────────────────────────────
orders_schema = """
-- OrderService PostgreSQL schema (current, monolithic)
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pharmacy_id VARCHAR(64) NOT NULL,
    drug_id VARCHAR(64) NOT NULL,
    quantity INTEGER NOT NULL,
    distribution_center_id VARCHAR(64),
    urgency VARCHAR(16) DEFAULT 'ROUTINE',
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',  -- PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED, FAILED
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
    -- NOTE: No outbox table. Events published inline after DB commit (known gap).
    -- NOTE: No idempotency_key column. Duplicate POST /orders creates duplicate rows.
);

CREATE TABLE stock_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id),
    drug_id VARCHAR(64) NOT NULL,
    distribution_center_id VARCHAR(64) NOT NULL,
    quantity_reserved INTEGER NOT NULL,
    status VARCHAR(16) DEFAULT 'ACTIVE',  -- ACTIVE, RELEASED, CONSUMED
    reserved_at TIMESTAMPTZ DEFAULT NOW()
    -- Reservation not released atomically with order cancellation.
);
"""
write_text("current_system/db_schemas/orders_schema.sql", orders_schema)

billing_schema = """
-- BillingService PostgreSQL schema
CREATE TABLE charges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL,
    pharmacy_id VARCHAR(64) NOT NULL,
    amount_usd NUMERIC(12,2) NOT NULL,
    status VARCHAR(16) DEFAULT 'PENDING',
    charged_at TIMESTAMPTZ DEFAULT NOW()
    -- No idempotency_key. order_id is NOT UNIQUE — allows duplicate charges.
);
"""
write_text("current_system/db_schemas/billing_schema.sql", billing_schema)

# ── infra / monitoring (distractors) ────────────────────────────────────────
write_yaml("infra/monitoring/prometheus_rules.yaml", {
    "groups": [{
        "name": "service_alerts",
        "rules": [
            {"alert": "HighErrorRate", "expr": 'rate(http_requests_total{status=~"5.."}[5m]) > 0.05', "for": "2m"},
            {"alert": "ComplianceServiceDown", "expr": 'up{job="compliance_service"} == 0', "for": "1m"}
        ]
    }]
})

write_yaml("infra/networking/service_mesh.yaml", {
    "mesh": "istio",
    "version": "1.19",
    "services": list(services.keys()),
    "mtls": "STRICT",
    "timeouts": {
        "order_service": "30s",
        "compliance_service": "10s",
        "shipping_service": "15s"
    },
    "retries": {
        "order_service": {"attempts": 3, "perTryTimeout": "10s"}
    }
})

# ── docs/legacy (distractors) ───────────────────────────────────────────────
write_text("docs/legacy/old_architecture_notes.txt", """
Original architecture circa 2019:
- Monolithic Rails app, single PostgreSQL DB
- Split into microservices 2021 but kept synchronous REST between all services
- Considered Kafka in 2022 but deferred due to ops complexity
- ComplianceService was Oracle-based legacy from 2015 acquisition
- 3PL integration via REST webhooks, no message queue
""")

write_text("docs/meetings/2024_q2_postmortem.txt", """
Q2 2024 Architecture Postmortem - Action Items:
- MUST fix double-billing (INC-2024-0312) before Q3
- MUST ensure FDA audit log is never missing (INC-2024-0601) — regulatory risk
- Consider async messaging between services
- OrderService cannot be the synchronous hub for all downstream services
- Need compensating transactions for partial failures
- Team lead: "We need to look at saga patterns and event-driven approaches"
- Timeline: Design proposal due end of Q3 2024
""")

write_json("docs/meetings/stakeholder_requirements.json", {
    "regulatory": {
        "requirement": "Every order and shipment event must appear in compliance audit log within 5 minutes, even during downstream failures.",
        "standard": "FDA 21 CFR Part 11, DEA 1304.04",
        "consequence_of_breach": "License suspension, $2M fine per incident"
    },
    "business": {
        "availability_sla": "99.9% for order creation",
        "billing_accuracy": "Zero duplicate charges tolerated",
        "notification_latency": "Pharmacy notified within 2 minutes of order status change"
    },
    "technical": {
        "current_p99_latency_order_creation": "4200ms",
        "target_p99_latency": "800ms",
        "current_duplicate_order_rate": "0.3%"
    }
})

# ── ops/runbooks (distractors) ───────────────────────────────────────────────
write_text("ops/runbooks/manual_reservation_release.md", """
# Manual Stock Reservation Release Runbook

## When to use
When OrderService fails after InventoryService has reserved stock but before order is confirmed.

## Steps
1. Connect to InventoryService PostgreSQL
2. Run: SELECT * FROM stock_reservations WHERE status = 'ACTIVE' AND order_id IN (SELECT id FROM orders WHERE status = 'FAILED');
3. Verify with OrderService team that orders are truly failed
4. UPDATE stock_reservations SET status = 'RELEASED' WHERE ...
5. Notify pharmacy operations team

## Owner: Platform Engineering
## Last updated: 2024-05-01
""")

write_text("ops/alerts/pagerduty_config.txt", """
PagerDuty routing:
- P1 alerts -> on-call platform engineer (15min escalation)
- ComplianceService down -> immediate regulatory team notification
- BillingService error rate > 1% -> immediate finance team notification
""")

# ── a red-herring "design" file that is incomplete / wrong ──────────────────
write_json("docs/legacy/partial_kafka_spike.json", {
    "note": "Incomplete spike from 2022 — DO NOT USE",
    "proposed_topics": ["orders", "shipments"],
    "missing": ["event schema", "consumer groups", "saga design", "outbox pattern", "DLQ strategy"],
    "status": "ABANDONED",
    "reason": "Team lacked expertise; no saga or outbox pattern considered; exactly-once delivery assumed (incorrect)"
})

print("Workspace generated successfully.")
print(f"Files created in {BASE}:")
for root, dirs_list, files in os.walk(BASE):
    for fn in files:
        full = os.path.join(root, fn)
        print(f"  {full}")