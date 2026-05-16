import os
import json
import yaml
import random

random.seed(42)

workspace = "/workspace"

# ── deep directory structure (distractor files) ──────────────────────────────
dirs = [
    "platform/services/lab-ingestor/src",
    "platform/services/lab-ingestor/tests",
    "platform/services/billing-worker/src",
    "platform/services/billing-worker/tests",
    "platform/services/ehr-sync/src",
    "platform/services/alert-dispatcher/src",
    "platform/infra/terraform/modules",
    "platform/infra/k8s/manifests",
    "platform/docs/adr",
    "platform/docs/runbooks",
    "platform/monitoring/dashboards",
    "platform/monitoring/alerts",
    "platform/scripts/db-migrations",
    "platform/ci",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────

# 1. Broken/incomplete old design doc (distractor – missing required sections)
broken_design = """\
# Lab Results Messaging – DRAFT (v0.1)

## Overview
We publish lab results to a topic. Workers consume them.

## Retry Policy
Workers retry up to 3 times with a fixed 5-second delay.

## TODO
- Add DLQ
- Think about ordering
"""
with open(os.path.join(workspace, "platform/docs/adr/ADR-007-messaging-draft.md"), "w") as f:
    f.write(broken_design)

# 2. Old envelope schema (wrong fields, missing version/type)
old_schema = {
    "envelope": {
        "event_id": "uuid",
        "created_at": "iso8601",
        "body": "object"
    },
    "note": "DEPRECATED – do not use"
}
with open(os.path.join(workspace, "platform/docs/adr/ADR-005-event-schema-deprecated.json"), "w") as f:
    json.dump(old_schema, f, indent=2)

# 3. Terraform placeholder
with open(os.path.join(workspace, "platform/infra/terraform/modules/main.tf"), "w") as f:
    f.write('# TODO: provision message broker\nresource "aws_sqs_queue" "placeholder" {}\n')

# 4. K8s deployment with no consumer config
k8s_deploy = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {"name": "billing-worker"},
    "spec": {
        "replicas": 2,
        "template": {
            "spec": {
                "containers": [{"name": "billing-worker", "image": "billing-worker:latest"}]
            }
        }
    }
}
with open(os.path.join(workspace, "platform/infra/k8s/manifests/billing-worker.yaml"), "w") as f:
    yaml.dump(k8s_deploy, f)

# 5. Source stubs
for svc, fname in [
    ("lab-ingestor", "producer.py"),
    ("billing-worker", "consumer.py"),
    ("ehr-sync", "consumer.py"),
    ("alert-dispatcher", "consumer.py"),
]:
    stub = f"# TODO: implement {fname}\nclass {'Producer' if 'producer' in fname else 'Consumer'}:\n    pass\n"
    with open(os.path.join(workspace, f"platform/services/{svc}/src/{fname}"), "w") as f:
        f.write(stub)

# 6. Test stubs
for svc in ["lab-ingestor", "billing-worker"]:
    with open(os.path.join(workspace, f"platform/services/{svc}/tests/test_placeholder.py"), "w") as f:
        f.write("# placeholder\ndef test_todo(): pass\n")

# 7. CI config (distractor)
ci_config = {
    "stages": ["lint", "test", "build"],
    "variables": {"IMAGE_TAG": "$CI_COMMIT_SHA"},
}
with open(os.path.join(workspace, "platform/ci/pipeline.yml"), "w") as f:
    yaml.dump(ci_config, f)

# 8. Monitoring dashboard stub
dashboard = {"title": "Lab Platform", "panels": [], "note": "empty – needs lag metrics"}
with open(os.path.join(workspace, "platform/monitoring/dashboards/lab-platform.json"), "w") as f:
    json.dump(dashboard, f, indent=2)

# 9. Alert rule (wrong metric – distracting)
with open(os.path.join(workspace, "platform/monitoring/alerts/cpu-alert.yaml"), "w") as f:
    f.write("alert: HighCPU\nexpr: cpu_usage > 80\nfor: 5m\n")

# 10. DB migration script (distractor)
with open(os.path.join(workspace, "platform/scripts/db-migrations/001_create_lab_results.sql"), "w") as f:
    f.write("CREATE TABLE lab_results (id UUID PRIMARY KEY, patient_id UUID, result JSONB);\n")

# 11. Runbook (incomplete, wrong advice)
with open(os.path.join(workspace, "platform/docs/runbooks/consumer-lag-runbook.md"), "w") as f:
    f.write("# Consumer Lag\n\nIf lag is high, restart the consumer pod.\n\n(TODO: proper runbook)\n")

# 12. Confusing requirements doc (mentions "exactly-once" without caveats)
with open(os.path.join(workspace, "platform/docs/adr/ADR-010-requirements.md"), "w") as f:
    f.write(
        "# Messaging Requirements\n\n"
        "- Billing worker MUST process each lab result exactly once\n"
        "- EHR sync MUST reflect results in order\n"
        "- Alert dispatcher latency < 500ms\n"
        "- Do NOT lose messages\n"
    )

print("Workspace scaffolded successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    for fn in files:
        print(f"  {os.path.join(root, fn).replace(workspace, '')}")