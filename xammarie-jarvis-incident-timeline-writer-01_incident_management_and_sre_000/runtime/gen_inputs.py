import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "incidents/2024-07-15/raw_logs",
    "incidents/2024-07-15/slack_exports",
    "incidents/2024-07-15/metrics_snapshots",
    "incidents/2024-07-15/postmortem_drafts",
    "incidents/archive/2024-06-01",
    "incidents/archive/2024-05-20",
    "infra/terraform/modules/networking",
    "infra/terraform/modules/compute",
    "infra/runbooks/database",
    "infra/runbooks/cache",
    "monitoring/dashboards",
    "monitoring/alerts",
    "scripts/automation",
    "docs/slo_definitions",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files (10+) ───────────────────────────────────────────────────
distractors = {
    "infra/terraform/modules/networking/main.tf": """\
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}
""",
    "infra/terraform/modules/compute/variables.tf": """\
variable "instance_type" { default = "t3.medium" }
""",
    "infra/runbooks/database/failover.md": """\
# DB Failover Runbook
1. Check replica lag
2. Promote replica
3. Update DNS
""",
    "infra/runbooks/cache/redis_flush.sh": """\
#!/bin/bash
redis-cli FLUSHDB
""",
    "monitoring/dashboards/overview.json": '{"title":"Ops Overview","panels":[]}',
    "monitoring/alerts/latency_alert.yaml": """\
alert: HighLatency
expr: http_request_duration_seconds > 1.5
for: 5m
""",
    "docs/slo_definitions/api_slo.md": """\
# API SLO
Availability: 99.9%
Latency p99: < 500ms
""",
    "scripts/automation/restart_service.sh": """\
#!/bin/bash
systemctl restart app-server
""",
    "incidents/archive/2024-06-01/summary.txt": """\
Minor DB hiccup; resolved in 12 min.
""",
    "incidents/archive/2024-05-20/notes.txt": """\
CDN misconfiguration; rolled back. No customer impact.
""",
    "incidents/2024-07-15/metrics_snapshots/cpu_spike.csv": """\
timestamp,host,cpu_pct
2024-07-15T02:31:00Z,app-server-01,88
2024-07-15T02:32:00Z,app-server-01,97
2024-07-15T02:33:00Z,app-server-01,99
2024-07-15T02:34:00Z,app-server-02,62
2024-07-15T02:35:00Z,app-server-01,55
""",
    "incidents/2024-07-15/metrics_snapshots/error_rate.csv": """\
timestamp,service,error_rate_pct
2024-07-15T02:30:00Z,checkout-api,0.3
2024-07-15T02:31:00Z,checkout-api,4.7
2024-07-15T02:32:00Z,checkout-api,18.2
2024-07-15T02:33:00Z,checkout-api,23.1
2024-07-15T02:34:00Z,checkout-api,21.8
2024-07-15T02:35:00Z,checkout-api,9.4
2024-07-15T02:40:00Z,checkout-api,0.8
""",
    "incidents/2024-07-15/postmortem_drafts/draft_v0.txt": """\
something went wrong with checkout around 2am
ops were paged, took a while
eventually fixed
""",
}
for rel_path, content in distractors.items():
    (WORKSPACE / rel_path).write_text(content)

# ── PRIMARY INPUT 1: raw on-call log (messy, out-of-order, duplicates) ───────
raw_oncall_log = """\
[02:47Z] @alice  ok i think its recovering?? error rate dropping
[02:31Z] @bob  paged. looking at dashboards now
[02:55Z] @alice  confirmed. all green. closing incident
[02:38Z] @bob  found it - deploy d4e5f6 pushed a bad DB connection pool config
[02:29Z] AUTOMATED ALERT: checkout-api error rate > 5% (currently 18%)  SEV-2 triggered
[02:31Z] @bob  checkout-api throwing DB timeout errors. heap of them
[02:42Z] @alice  rollback complete. watching metrics
[02:33Z] @bob  error rate now 23%. DB connection pool exhausted on app-server-01
[02:38Z] @alice  agree. initiating rollback of d4e5f6
[02:55Z] @bob  post-incident review scheduled for tomorrow 10am
[02:29Z] AUTOMATED ALERT: PagerDuty SEV-2 fired - checkout-api
[02:35Z] @alice  joined. DB pool maxed. no new connections possible on app-server-01
[02:40Z] @charlie  heads up: 3 enterprise customers opened support tickets (TICK-8821, TICK-8822, TICK-8823)
[02:31Z] AUTOMATED ALERT: app-server-01 CPU > 95%
[02:43Z] @charlie  one customer reporting they lost a cart worth ~$4200
[02:33Z] @alice  @bob confirmed db pool size was halved in that deploy
[02:50Z] @charlie  notified customers of resolution via status page
"""
(WORKSPACE / "incidents/2024-07-15/raw_logs/oncall_chat.log").write_text(raw_oncall_log)

# ── PRIMARY INPUT 2: slack export (JSON-ish, noisy) ──────────────────────────
slack_export = """\
{"ts":"1721008140","user":"ops-bot","text":"Deploy d4e5f6 started - checkout-api v2.4.1"}
{"ts":"1721008200","user":"ops-bot","text":"Deploy d4e5f6 completed successfully - checkout-api v2.4.1"}
{"ts":"1721008740","user":"alice","text":"getting pages, brb"}
{"ts":"1721008800","user":"bob","text":"SEV-2 declared"}
{"ts":"1721009280","user":"bob","text":"root cause: db_pool_size reduced from 100 to 50 in deploy config"}
{"ts":"1721009520","user":"alice","text":"rollback initiated d4e5f6 -> d3c4b5"}
{"ts":"1721009640","user":"alice","text":"rollback done"}
{"ts":"1721009880","user":"ops-bot","text":"Deploy d3c4b5 completed - checkout-api v2.4.0"}
{"ts":"1721009940","user":"charlie","text":"enterprise customer TICK-8821 compensated $50 credit"}
{"ts":"1721010300","user":"alice","text":"incident closed. duration ~26 min"}
{"ts":"1721010300","user":"bob","text":"action item: add db_pool_size to deployment checklist"}
{"ts":"1721010300","user":"alice","text":"action item: add alert for db pool utilization > 80%"}
{"ts":"1721010300","user":"charlie","text":"action item: review change review process for config-only deploys"}
"""
(WORKSPACE / "incidents/2024-07-15/slack_exports/ops_channel.jsonl").write_text(slack_export)

# ── PRIMARY INPUT 3: engineer notes (freeform, fragmented) ──────────────────
engineer_notes = """\
July 15 incident notes - Bob

- We were NOT monitoring db connection pool utilization. Blind spot.
- The deploy passed all CI checks because unit tests mock the DB pool.
- Pool size change was buried in a 200-line config diff, reviewer missed it.
- app-server-02 was unaffected (different config template, lucky).
- We have no automated rollback trigger; manual decision took ~9 min after RCA.
- SLO breach confirmed: availability dropped to ~76% during 02:29-02:55Z window (SLO = 99.9%)
- Revenue impact estimate: $4200 direct + unknown cart abandonment.
- Three enterprise customers affected; all contacted.
- Existing runbook for DB issues did NOT cover connection pool exhaustion.

Unknowns:
- How many non-enterprise users abandoned carts? (need analytics pull)
- Was db_pool_size ever 50 intentionally in any environment?

Suggested fixes (my opinion, not validated):
- Add db_pool_size to deploy checklist (today)
- Add Prometheus metric + alert for pool utilization > 80% (this week)
- Rewrite DB config template to disallow values < 80 without explicit override flag (this week)
- Mandate two-engineer review for config-only deploys (this week)
- Update runbook to include connection pool section (this week)
"""
(WORKSPACE / "incidents/2024-07-15/raw_logs/engineer_notes.txt").write_text(engineer_notes)

print("Workspace generated successfully.")
print(f"Files created: {len(list(WORKSPACE.rglob('*')))}")