#!/usr/bin/env python3
"""
Evaluation script for the pharmaceutical supply-chain event-driven architecture task.

Usage: python eval_script.py /workspace
"""

import json
import sys
import re
from pathlib import Path

def load_design(workspace: Path):
    """Find and load the event_driven_design.json file."""
    candidates = list(workspace.rglob("event_driven_design.json"))
    if not candidates:
        return None, "File 'event_driven_design.json' not found anywhere in workspace."
    # Prefer the most recently modified if multiple
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    with open(candidates[0]) as f:
        return json.load(f), str(candidates[0])

def text_contains_any(text: str, keywords: list) -> bool:
    """Case-insensitive check if text contains any of the given keywords."""
    t = text.lower()
    return any(kw.lower() in t for kw in keywords)

def deep_text(obj) -> str:
    """Recursively extract all string content from a JSON object."""
    if isinstance(obj, str):
        return obj + " "
    if isinstance(obj, list):
        return " ".join(deep_text(i) for i in obj)
    if isinstance(obj, dict):
        return " ".join(deep_text(v) for v in obj.values())
    return str(obj) + " "

def run_checks(design: dict, filepath: str) -> list:
    checks = []
    full_text = deep_text(design).lower()

    # ── CHECK 1: Six stages present ──────────────────────────────────────────
    stage_keywords = {
        "stage_1_event_identification": [
            "event", "command", "domain event", "bounded context", "event catalog",
            "producer", "consumer", "identify"
        ],
        "stage_2_contracts_versioning": [
            "schema", "contract", "version", "backward", "compat", "deprecat",
            "registry", "evolut"
        ],
        "stage_3_delivery_semantics": [
            "partition", "idempoten", "dedupe", "deduplication", "delivery semantic",
            "at-least", "at_least"
        ],
        "stage_4_orchestration_choreography": [
            "saga", "orchestrat", "choreograph", "outbox", "coordinator"
        ],
        "stage_5_observability": [
            "correlation", "trace", "tracing", "lag", "dlq", "dead-letter",
            "metric", "observ"
        ],
        "stage_6_failure_replay": [
            "dead-letter", "dlq", "replay", "poison", "failure", "idempotent replay"
        ],
    }
    stage_coverage = 0
    for stage_name, keywords in stage_keywords.items():
        found = text_contains_any(full_text, keywords)
        stage_coverage += 1 if found else 0
        checks.append({
            "name": f"Stage coverage: {stage_name}",
            "passed": found,
            "detail": f"Keywords searched: {keywords[:3]}... Found: {found}"
        })

    # ── CHECK 2: Event catalog with required fields ──────────────────────────
    # Look for a list/dict of events with name, schema, producers, consumers, SLA
    required_event_fields = ["name", "schema", "producer", "consumer", "sla"]
    event_catalog_text = full_text

    field_coverage = sum(1 for f in required_event_fields if f in event_catalog_text)
    catalog_ok = field_coverage >= 4
    checks.append({
        "name": "Event catalog has required fields (name, schema, producers, consumers, SLA)",
        "passed": catalog_ok,
        "detail": f"Found {field_coverage}/5 required fields: {required_event_fields}"
    })

    # ── CHECK 3: Domain events vs Commands distinction ──────────────────────
    has_domain_event = text_contains_any(full_text, [
        "domain event", "domain_event", "fact", "happened", "occurred",
        "orderplaced", "order_placed", "orderconfirmed", "stockreserved",
        "shipmentcreated", "shipmentsent", "deliveryconfirmed", "auditlogged"
    ])
    has_command = text_contains_any(full_text, [
        "command", "request", "reservestock", "reserve_stock", "createshipment",
        "create_shipment", "chargeCustomer", "charge_customer"
    ])
    events_vs_commands_ok = has_domain_event and has_command
    checks.append({
        "name": "Distinguishes domain events (facts) from commands (requests)",
        "passed": events_vs_commands_ok,
        "detail": f"domain_event found: {has_domain_event}, command found: {has_command}"
    })

    # ── CHECK 4: At-least-once delivery as default (NOT exactly-once default) ─
    # The SKILL.md explicitly states "Assume at-least-once delivery unless proven otherwise"
    has_at_least_once = text_contains_any(full_text, [
        "at-least-once", "at_least_once", "at least once"
    ])
    # Check it's not stated as default exactly-once
    exactly_once_as_default = bool(re.search(
        r'default[^.]{0,40}exactly.once|exactly.once[^.]{0,30}default|assumed[^.]{0,30}exactly.once',
        full_text, re.IGNORECASE
    ))
    delivery_ok = has_at_least_once and not exactly_once_as_default
    checks.append({
        "name": "Delivery semantics: at-least-once as default (not exactly-once)",
        "passed": delivery_ok,
        "detail": f"at-least-once mentioned: {has_at_least_once}, exactly-once as default (bad): {exactly_once_as_default}"
    })

    # ── CHECK 5: Outbox pattern for DB+event atomicity ────────────────────────
    has_outbox = text_contains_any(full_text, [
        "outbox", "transactional outbox", "outbox pattern"
    ])
    outbox_linked_to_atomicity = text_contains_any(full_text, [
        "atomic", "transactional consistency", "db write", "database write",
        "publish must align", "write and publish", "same transaction"
    ])
    outbox_ok = has_outbox and outbox_linked_to_atomicity
    checks.append({
        "name": "Outbox pattern specified for DB write + event publish atomicity",
        "passed": outbox_ok,
        "detail": f"outbox mentioned: {has_outbox}, linked to atomicity/consistency: {outbox_linked_to_atomicity}"
    })

    # ── CHECK 6: Saga pattern ────────────────────────────────────────────────
    has_saga = text_contains_any(full_text, [
        "saga", "compensating transaction", "compensating action", "rollback event"
    ])
    checks.append({
        "name": "Saga pattern (with compensating transactions) specified",
        "passed": has_saga,
        "detail": f"saga/compensating transaction mentioned: {has_saga}"
    })

    # ── CHECK 7: Correlation IDs in observability ────────────────────────────
    has_correlation_id = text_contains_any(full_text, [
        "correlation id", "correlation_id", "correlationid", "trace id",
        "distributed trace", "trace context"
    ])
    checks.append({
        "name": "Observability: correlation/trace IDs on events",
        "passed": has_correlation_id,
        "detail": f"correlation/trace ID mentioned: {has_correlation_id}"
    })

    # ── CHECK 8: DLQ + lag metrics ───────────────────────────────────────────
    has_dlq = text_contains_any(full_text, [
        "dead-letter", "dead letter", "dlq", "dead letter queue"
    ])
    has_lag_metric = text_contains_any(full_text, [
        "lag", "consumer lag", "queue depth", "dlq depth", "backlog"
    ])
    observability_ops_ok = has_dlq and has_lag_metric
    checks.append({
        "name": "Observability: DLQ depth and lag metrics specified",
        "passed": observability_ops_ok,
        "detail": f"DLQ mentioned: {has_dlq}, lag/depth metrics mentioned: {has_lag_metric}"
    })

    # ── CHECK 9: Idempotent consumers with partition strategy ────────────────
    has_idempotent_consumer = text_contains_any(full_text, [
        "idempotent consumer", "idempotency key", "idempotency_key", "dedupe key",
        "deduplicate", "idempotent"
    ])
    has_partition_key = text_contains_any(full_text, [
        "partition key", "partition_key", "partitioned by", "ordering", "per-entity order"
    ])
    idempotency_ok = has_idempotent_consumer and has_partition_key
    checks.append({
        "name": "Idempotent consumers AND partition key strategy documented",
        "passed": idempotency_ok,
        "detail": f"idempotent consumer: {has_idempotent_consumer}, partition key: {has_partition_key}"
    })

    # ── CHECK 10: Failure & replay — poison message handling ─────────────────
    has_poison = text_contains_any(full_text, [
        "poison message", "poison pill", "unprocessable", "malformed message",
        "message that cannot be processed"
    ])
    has_replay = text_contains_any(full_text, [
        "replay", "reprocess", "event replay"
    ])
    failure_ok = has_poison and has_replay
    checks.append({
        "name": "Failure strategy: poison message handling AND replay tooling",
        "passed": failure_ok,
        "detail": f"poison message: {has_poison}, replay: {has_replay}"
    })

    # ── CHECK 11: Final review checklist — bounded context / event ownership ──
    has_ownership = text_contains_any(full_text, [
        "owner", "ownership", "bounded context", "owning service", "responsible"
    ])
    checks.append({
        "name": "Event ownership / bounded context assignment (Final Checklist item)",
        "passed": has_ownership,
        "detail": f"ownership/bounded context mentioned: {has_ownership}"
    })

    # ── CHECK 12: Versioned contracts with compatibility rules ────────────────
    has_compat_rule = text_contains_any(full_text, [
        "backward compat", "backward-compat", "forward compat",
        "ignore unknown", "unknown field", "schema evolution",
        "deprecation policy", "deprecated version", "schema version"
    ])
    checks.append({
        "name": "Versioned contracts with compatibility rules (consumers ignore unknown fields / deprecation policy)",
        "passed": has_compat_rule,
        "detail": f"backward compat / deprecation policy mentioned: {has_compat_rule}"
    })

    # ── CHECK 13: Addresses specific pharmaceutical pain points ──────────────
    has_pharma_context = text_contains_any(full_text, [
        "order", "pharmacy", "drug", "shipment", "compliance", "audit",
        "billing", "inventory", "stock", "regulation", "fda", "dea"
    ])
    checks.append({
        "name": "Design is contextually applied to the pharmaceutical supply chain domain",
        "passed": has_pharma_context,
        "detail": f"Domain-specific context found: {has_pharma_context}"
    })

    return checks

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

    results = {"passed": False, "score": 0.0, "checks": []}

    try:
        design, filepath = load_design(workspace)
    except Exception as e:
        results["checks"].append({
            "name": "File loading",
            "passed": False,
            "detail": f"Exception loading design file: {e}"
        })
        print(json.dumps(results))
        return

    if design is None:
        results["checks"].append({
            "name": "File existence",
            "passed": False,
            "detail": filepath
        })
        print(json.dumps(results))
        return

    results["checks"].append({
        "name": "File existence",
        "passed": True,
        "detail": f"Found at: {filepath}"
    })

    try:
        checks = run_checks(design, filepath)
        results["checks"].extend(checks)
    except Exception as e:
        results["checks"].append({
            "name": "Check execution",
            "passed": False,
            "detail": f"Exception during checks: {e}"
        })

    # Score: proportion of checks passed
    total = len(results["checks"])
    passed_count = sum(1 for c in results["checks"] if c["passed"])
    results["score"] = round(passed_count / total, 3) if total > 0 else 0.0

    # Overall pass: must pass at least 11 out of 14 checks (including file existence)
    # AND must pass the four most critical proprietary traps:
    critical_check_names = [
        "Delivery semantics: at-least-once as default (not exactly-once)",
        "Outbox pattern specified for DB write + event publish atomicity",
        "Distinguishes domain events (facts) from commands (requests)",
        "Idempotent consumers AND partition key strategy documented",
    ]
    critical_passed = all(
        any(c["name"] == cn and c["passed"] for c in results["checks"])
        for cn in critical_check_names
    )
    results["passed"] = (passed_count >= 11) and critical_passed

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()