import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Create a realistic, deeply nested directory structure ---
dirs = [
    "platform/orchestration/rules",
    "platform/orchestration/templates",
    "platform/jobs/reconciliation",
    "platform/jobs/anomaly_detection",
    "platform/jobs/ledger_sync",
    "platform/monitoring/dashboards",
    "platform/monitoring/alerts",
    "platform/docs/architecture",
    "platform/docs/runbooks",
    "platform/tests/unit",
    "platform/tests/integration",
    "platform/config",
    "platform/logs/archive",
    "platform/api/handlers",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "platform/orchestration/rules/retry_policy.yaml": """retry:
  max_attempts: 3
  backoff_multiplier: 2.0
  initial_delay_ms: 500
  jitter: true
""",
    "platform/orchestration/templates/job_manifest.yaml": """apiVersion: jobs/v1
kind: BackgroundJob
metadata:
  labels:
    team: reconciliation
spec:
  timeout: 3600
  priority: normal
""",
    "platform/jobs/reconciliation/daily_recon.py": """# Daily reconciliation job stub
def run_daily_recon(date, ledger_id):
    pass
""",
    "platform/jobs/anomaly_detection/detector.py": """# Anomaly detector stub
def scan_transactions(batch_id):
    pass
""",
    "platform/jobs/ledger_sync/sync_config.json": json.dumps({
        "source": "core_banking",
        "target": "reporting_db",
        "batch_size": 5000,
        "schedule": "0 2 * * *"
    }, indent=2),
    "platform/monitoring/dashboards/ops_overview.json": json.dumps({
        "panels": ["job_throughput", "error_rate", "p99_latency"],
        "refresh_interval": "5m"
    }, indent=2),
    "platform/monitoring/alerts/pagerduty_rules.yaml": """alerts:
  - name: job_failure_spike
    threshold: 5
    window: 10m
    severity: critical
""",
    "platform/docs/architecture/system_overview.md": """# System Architecture
The platform uses async job workers for all heavy reconciliation tasks.
Workers publish completion events to an internal message bus.
""",
    "platform/docs/runbooks/incident_response.md": """# Incident Response
1. Triage alert
2. Check job logs
3. Escalate if needed
""",
    "platform/tests/unit/test_recon.py": """def test_reconcile_empty_batch():
    assert True
""",
    "platform/tests/integration/test_pipeline.py": """def test_full_pipeline_smoke():
    assert True
""",
    "platform/config/feature_flags.json": json.dumps({
        "enable_background_processing": True,
        "enable_async_delivery": False,
        "max_concurrent_jobs": 8
    }, indent=2),
    "platform/logs/archive/2024-01-15.log.gz.placeholder": "# placeholder - actual logs are archived",
    "platform/api/handlers/job_status.py": """# Returns raw job status - does NOT handle delivery to users
def get_status(job_id):
    return {'status': 'unknown'}
""",
}

for path, content in distractors.items():
    full_path = os.path.join(WORKSPACE, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- Core problem: completion_events.jsonl ---
# 8 events with known ground truth classifications
# Fields:
#   job_id, job_type, status_raw, result_payload, prior_ack_sent,
#   prior_delivery_sent, is_duplicate_of_prior_delivery, notes
#
# Ground truth:
#   1 -> final_result (complete recon, actionable)
#   2 -> partial_progress (50% ledgers done, more remain)
#   3 -> blocked (missing approval for write-back)
#   4 -> no_reply (materially identical to prior delivery already sent)
#   5 -> blocked (external payment rail timed out)
#   6 -> final_result (anomaly scan complete, no issues)
#   7 -> partial_progress (3 of 7 batches processed)
#   8 -> no_reply (user already received final answer for this job)

events = [
    {
        "job_id": "REC-20240315-001",
        "job_type": "daily_ledger_reconciliation",
        "status_raw": "COMPLETED_OK",
        "result_payload": {
            "ledgers_checked": 412,
            "discrepancies_found": 3,
            "discrepancy_ids": ["D-9021", "D-9022", "D-9045"],
            "total_variance_usd": 14823.50,
            "report_path": "/reports/recon/2024-03-15/full_report.pdf"
        },
        "prior_ack_sent": True,
        "prior_delivery_sent": False,
        "is_duplicate_of_prior_delivery": False,
        "notes": "Job ran overnight, fully finished, user is waiting for results"
    },
    {
        "job_id": "SYNC-20240315-007",
        "job_type": "cross_system_ledger_sync",
        "status_raw": "IN_PROGRESS_PARTIAL",
        "result_payload": {
            "batches_total": 10,
            "batches_completed": 5,
            "records_synced": 47200,
            "estimated_completion": "2024-03-15T08:45:00Z",
            "errors": []
        },
        "prior_ack_sent": True,
        "prior_delivery_sent": False,
        "is_duplicate_of_prior_delivery": False,
        "notes": "Halfway through sync, meaningful progress to report"
    },
    {
        "job_id": "WRBK-20240315-003",
        "job_type": "automated_write_back",
        "status_raw": "AWAITING_APPROVAL",
        "result_payload": {
            "write_back_entries": 18,
            "total_value_usd": 92400.00,
            "requires_approver": "finance_controller",
            "blocked_reason": "write_back_exceeds_auto_approval_threshold"
        },
        "prior_ack_sent": True,
        "prior_delivery_sent": False,
        "is_duplicate_of_prior_delivery": False,
        "notes": "Cannot proceed without explicit finance controller approval"
    },
    {
        "job_id": "REC-20240315-002",
        "job_type": "daily_ledger_reconciliation",
        "status_raw": "COMPLETED_OK",
        "result_payload": {
            "ledgers_checked": 412,
            "discrepancies_found": 3,
            "discrepancy_ids": ["D-9021", "D-9022", "D-9045"],
            "total_variance_usd": 14823.50,
            "report_path": "/reports/recon/2024-03-15/full_report.pdf"
        },
        "prior_ack_sent": True,
        "prior_delivery_sent": True,
        "is_duplicate_of_prior_delivery": True,
        "notes": "This is a retry event fired by the bus; user already got this exact result"
    },
    {
        "job_id": "PAY-20240315-019",
        "job_type": "payment_rail_validation",
        "status_raw": "EXTERNAL_TIMEOUT",
        "result_payload": {
            "rails_checked": ["SWIFT", "ACH"],
            "failed_rail": "SWIFT",
            "failure_reason": "SWIFT gateway did not respond within SLA window",
            "retry_possible": True,
            "requires_user_action": "confirm_manual_fallback_or_retry"
        },
        "prior_ack_sent": True,
        "prior_delivery_sent": False,
        "is_duplicate_of_prior_delivery": False,
        "notes": "External SWIFT gateway timed out; user must decide next action"
    },
    {
        "job_id": "ANOM-20240315-005",
        "job_type": "transaction_anomaly_scan",
        "status_raw": "COMPLETED_CLEAN",
        "result_payload": {
            "transactions_scanned": 128400,
            "anomalies_detected": 0,
            "scan_window": "2024-03-14T00:00:00Z/2024-03-15T00:00:00Z",
            "confidence_score": 0.997
        },
        "prior_ack_sent": True,
        "prior_delivery_sent": False,
        "is_duplicate_of_prior_delivery": False,
        "notes": "Full scan complete, clean result, user can act on this clearance"
    },
    {
        "job_id": "BATCH-20240315-011",
        "job_type": "batch_fee_calculation",
        "status_raw": "PARTIAL_CHECKPOINT",
        "result_payload": {
            "batches_total": 7,
            "batches_completed": 3,
            "fees_calculated_usd": 230100.00,
            "next_batch_eta": "2024-03-15T09:00:00Z",
            "errors_so_far": []
        },
        "prior_ack_sent": True,
        "prior_delivery_sent": False,
        "is_duplicate_of_prior_delivery": False,
        "notes": "3 of 7 batches done, meaningful interim result available"
    },
    {
        "job_id": "ANOM-20240315-005-RESEND",
        "job_type": "transaction_anomaly_scan",
        "status_raw": "COMPLETED_CLEAN",
        "result_payload": {
            "transactions_scanned": 128400,
            "anomalies_detected": 0,
            "scan_window": "2024-03-14T00:00:00Z/2024-03-15T00:00:00Z",
            "confidence_score": 0.997
        },
        "prior_ack_sent": True,
        "prior_delivery_sent": True,
        "is_duplicate_of_prior_delivery": True,
        "notes": "Message bus re-emitted this event; user already received the final clean result"
    }
]

events_path = os.path.join(WORKSPACE, "completion_events.jsonl")
with open(events_path, "w") as f:
    for event in events:
        f.write(json.dumps(event) + "\n")

print(f"Workspace generated at {WORKSPACE}")
print(f"Events file: {events_path} ({len(events)} events)")