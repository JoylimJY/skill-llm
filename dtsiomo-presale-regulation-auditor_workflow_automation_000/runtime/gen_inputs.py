import os
import json
import yaml
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure ────────────────────────────────────────────────────────
dirs = [
    "references",
    "regulations/active",
    "regulations/archive",
    "operations/incident_logs",
    "operations/behavior_snapshots",
    "config/current",
    "config/proposed",           # agent must populate this
    "reports",                    # agent must populate this
    "scripts/utils",
    "scripts/validators",
    "docs/internal",
    "docs/external",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── references/regulation-check-workflow.md ────────────────────────────────────
workflow_md = """\
# Regulation Check Workflow

## Overview
This document defines the canonical audit process for NexusSell pre-sales compliance controls.

## Step 1 — Collect Regulation Sources
- Load all regulation files from `regulations/active/`.
- Each regulation file is JSON and contains: `rule_id`, `description`, `version_date`, `owner`, `policy_checks`, `fact_resolution`, `routing_impacts`.
- Record the `version_date` of each rule.

## Step 2 — Staleness Classification
Apply the following classification logic (non-negotiable):
- A rule is **stale** if its `version_date` is more than **180 days** before the audit date.
- A rule is **conflicting** if `conflict_count` in the matching incident log entry is **greater than 0**, regardless of age.
- A rule is **active** if it is neither stale nor conflicting.
- A rule may be **both** stale AND conflicting; in that case, classify it as **conflicting** (conflicting takes priority).

The audit date for this workspace is: **2025-06-15**

## Step 3 — Build the Staleness Matrix
Produce a JSON file `staleness_matrix.json` with the following structure:
```json
{
  "audit_date": "2025-06-15",
  "rules": [
    {
      "rule_id": "<id>",
      "status": "<stale|conflicting|active>",
      "version_date": "<ISO date>",
      "days_old": <integer>,
      "evidence": "<human-readable reason>"
    }
  ]
}
```

## Step 4 — Produce Config Diffs
For every rule that is **stale** or **conflicting**, produce a proposed config diff.
Output file: `config/proposed/config_diffs.json`

Structure:
```json
{
  "generated_at": "<ISO datetime>",
  "diffs": [
    {
      "rule_id": "<id>",
      "change_reason": "<stale|conflicting>",
      "policy_checks": { "before": <old_value>, "after": <proposed_value> },
      "fact_resolution": { "before": <old_value>, "after": <proposed_value> },
      "routing_impacts": { "before": <old_value>, "after": <proposed_value> }
    }
  ]
}
```
- For **stale** rules: increment `policy_checks.version` by 1, set `fact_resolution.refresh_required` to `true`, set `routing_impacts.review_queue` to `"compliance_backlog"`.
- For **conflicting** rules: set `policy_checks.suspended` to `true`, set `fact_resolution.override_mode` to `"manual"`, set `routing_impacts.review_queue` to `"conflict_resolution"`.

## Step 5 — Change Report
Output file: `reports/change_report.json`

Structure:
```json
{
  "report_date": "2025-06-15",
  "summary": {
    "total_rules": <int>,
    "stale_count": <int>,
    "conflicting_count": <int>,
    "active_count": <int>
  },
  "changes": [
    {
      "rule_id": "<id>",
      "risk_class": "<low|medium|critical>",
      "rollout_recommendation": "<string>",
      "backward_compatible": <true|false>
    }
  ],
  "backward_compatibility_notes": "<overall notes string>"
}
```

Risk class assignment:
- **stale** rules → `"medium"` risk class.
- **conflicting** rules → `"critical"` risk class.
- **active** rules → `"low"` risk class (include in changes list for completeness).

Rollout recommendation strings:
- `"medium"` → `"Schedule update in next sprint cycle with regression testing."`
- `"critical"` → `"Immediate suspension pending manual conflict resolution."`
- `"low"` → `"No action required. Monitor in next quarterly review."`

Backward compatibility:
- A change is **NOT** backward compatible (`false`) if `risk_class` is `"critical"`.
- All other changes are backward compatible (`true`).
- `backward_compatibility_notes` field: concatenate one sentence per non-backward-compatible rule: `"Rule <rule_id> suspension breaks existing routing automations. "`
"""
(WORKSPACE / "references" / "regulation-check-workflow.md").write_text(workflow_md)

# ── Regulation files ──────────────────────────────────────────────────────────
# audit_date = 2025-06-15
# Rule dates chosen to produce specific staleness outcomes:
# REG-001: version_date=2024-05-01 → 410 days old → STALE (no conflict)
# REG-002: version_date=2025-03-10 → 97 days old → but conflict_count=3 → CONFLICTING
# REG-003: version_date=2024-11-20 → 207 days old → STALE (no conflict)
# REG-004: version_date=2025-05-01 → 45 days old → ACTIVE
# REG-005: version_date=2024-06-01 → 379 days old → STALE AND conflict_count=2 → CONFLICTING (priority)

regulations = [
    {
        "rule_id": "REG-001",
        "description": "Discount approval threshold: deals above $50k require VP sign-off.",
        "version_date": "2024-05-01",
        "owner": "sales-ops@nexussell.com",
        "policy_checks": {"version": 3, "suspended": False, "threshold_usd": 50000},
        "fact_resolution": {"refresh_required": False, "source": "crm_primary", "override_mode": "auto"},
        "routing_impacts": {"review_queue": "vp_approval", "escalation_path": "sales_director"}
    },
    {
        "rule_id": "REG-002",
        "description": "Customer data handling: PII fields must be masked before handoff to pre-sales.",
        "version_date": "2025-03-10",
        "owner": "legal@nexussell.com",
        "policy_checks": {"version": 7, "suspended": False, "pii_masking": True},
        "fact_resolution": {"refresh_required": True, "source": "legal_db", "override_mode": "auto"},
        "routing_impacts": {"review_queue": "legal_review", "escalation_path": "cpo"}
    },
    {
        "rule_id": "REG-003",
        "description": "Deal qualification: minimum ARR threshold is $10k for enterprise track.",
        "version_date": "2024-11-20",
        "owner": "rev-ops@nexussell.com",
        "policy_checks": {"version": 2, "suspended": False, "min_arr_usd": 10000},
        "fact_resolution": {"refresh_required": False, "source": "crm_primary", "override_mode": "auto"},
        "routing_impacts": {"review_queue": "enterprise_queue", "escalation_path": "ae_lead"}
    },
    {
        "rule_id": "REG-004",
        "description": "Contract renewal: 90-day advance notice required for enterprise renewals.",
        "version_date": "2025-05-01",
        "owner": "cs-ops@nexussell.com",
        "policy_checks": {"version": 1, "suspended": False, "notice_days": 90},
        "fact_resolution": {"refresh_required": False, "source": "renewal_db", "override_mode": "auto"},
        "routing_impacts": {"review_queue": "renewal_queue", "escalation_path": "csm_lead"}
    },
    {
        "rule_id": "REG-005",
        "description": "Competitor displacement: requires explicit approval from product marketing.",
        "version_date": "2024-06-01",
        "owner": "product-mktg@nexussell.com",
        "policy_checks": {"version": 5, "suspended": False, "requires_approval": True},
        "fact_resolution": {"refresh_required": False, "source": "mktg_db", "override_mode": "auto"},
        "routing_impacts": {"review_queue": "product_mktg_approval", "escalation_path": "vp_marketing"}
    },
]
for reg in regulations:
    path = WORKSPACE / "regulations" / "active" / f"{reg['rule_id']}.json"
    path.write_text(json.dumps(reg, indent=2))

# ── Archived old regulations (distractor) ─────────────────────────────────────
archive_regs = [
    {"rule_id": "REG-OLD-001", "description": "Legacy free trial policy (deprecated 2023).", "version_date": "2021-01-10", "status": "archived"},
    {"rule_id": "REG-OLD-002", "description": "Pre-COVID travel expense rule (deprecated 2022).", "version_date": "2019-07-22", "status": "archived"},
]
for r in archive_regs:
    (WORKSPACE / "regulations" / "archive" / f"{r['rule_id']}.json").write_text(json.dumps(r, indent=2))

# ── Incident logs (with conflict_count) ──────────────────────────────────────
incident_log = {
    "log_date": "2025-06-14",
    "entries": [
        {"rule_id": "REG-001", "incident_count": 0, "conflict_count": 0, "notes": "No incidents in last 90 days."},
        {"rule_id": "REG-002", "incident_count": 5, "conflict_count": 3, "notes": "Three routing conflicts with GDPR override module."},
        {"rule_id": "REG-003", "incident_count": 1, "conflict_count": 0, "notes": "Minor threshold dispute resolved manually."},
        {"rule_id": "REG-004", "incident_count": 0, "conflict_count": 0, "notes": "Operating normally."},
        {"rule_id": "REG-005", "incident_count": 2, "conflict_count": 2, "notes": "Two conflicts with new competitive intel feed integration."},
    ]
}
(WORKSPACE / "operations" / "incident_logs" / "incident_log_2025Q2.json").write_text(json.dumps(incident_log, indent=2))

# ── Behavior snapshots (distractor operational data) ──────────────────────────
behavior_snapshot = {
    "snapshot_date": "2025-06-10",
    "active_rules_observed": ["REG-001", "REG-002", "REG-003", "REG-004", "REG-005"],
    "automated_routing_active": True,
    "override_events": [
        {"rule_id": "REG-002", "event": "manual_override", "timestamp": "2025-06-08T14:23:00Z"},
        {"rule_id": "REG-005", "event": "manual_override", "timestamp": "2025-06-09T09:11:00Z"},
    ]
}
(WORKSPACE / "operations" / "behavior_snapshots" / "snapshot_2025-06-10.json").write_text(json.dumps(behavior_snapshot, indent=2))

# ── Current config (distractor) ───────────────────────────────────────────────
current_config = {
    "config_version": "4.2.1",
    "last_updated": "2025-04-01",
    "rules_loaded": ["REG-001", "REG-002", "REG-003", "REG-004", "REG-005"],
    "global_settings": {
        "auto_routing": True,
        "pii_masking_global": True,
        "conflict_detection": "enabled"
    }
}
(WORKSPACE / "config" / "current" / "runtime_config.json").write_text(json.dumps(current_config, indent=2))

# ── Distractor scripts ────────────────────────────────────────────────────────
(WORKSPACE / "scripts" / "utils" / "date_helpers.py").write_text(
    "# Date utility helpers\nimport datetime\n\ndef days_between(d1, d2):\n    return abs((d2 - d1).days)\n"
)
(WORKSPACE / "scripts" / "validators" / "schema_validator.py").write_text(
    "# Schema validation stub\ndef validate(obj, schema):\n    pass\n"
)

# ── Distractor docs ───────────────────────────────────────────────────────────
(WORKSPACE / "docs" / "internal" / "onboarding_guide.md").write_text(
    "# NexusSell Onboarding Guide\nWelcome to NexusSell. This guide covers first-week setup.\n"
)
(WORKSPACE / "docs" / "external" / "partner_sla.md").write_text(
    "# Partner SLA\nAll partners must adhere to a 99.5% uptime SLA.\n"
)
(WORKSPACE / "docs" / "internal" / "data_dictionary.md").write_text(
    "# Data Dictionary\n- ARR: Annual Recurring Revenue\n- PII: Personally Identifiable Information\n- CSM: Customer Success Manager\n"
)

# ── Distractor tests ──────────────────────────────────────────────────────────
(WORKSPACE / "tests" / "unit" / "test_routing.py").write_text(
    "# Unit tests for routing logic\ndef test_queue_assignment():\n    assert True\n"
)
(WORKSPACE / "tests" / "integration" / "test_reg_load.py").write_text(
    "# Integration test for regulation loading\ndef test_load_all_regs():\n    assert True\n"
)

# ── Empty placeholder in config/proposed and reports to confirm agent must create them ──
(WORKSPACE / "config" / "proposed" / ".gitkeep").write_text("")
(WORKSPACE / "reports" / ".gitkeep").write_text("")

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in WORKSPACE.rglob('*') if _.is_file())}")