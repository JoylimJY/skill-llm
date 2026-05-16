import os
import json
import csv
import random
import hashlib
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "platform/agents/data-sync-agent/logs",
    "platform/agents/data-sync-agent/metadata",
    "platform/agents/formatter-util/logs",
    "platform/agents/log-aggregator/logs",
    "platform/registry/published",
    "platform/registry/quarantine",
    "platform/audits/completed",
    "platform/audits/pending",
    "platform/monitoring/baselines",
    "platform/monitoring/alerts",
    "internal/docs",
    "internal/configs",
    "internal/scratch",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
(WORKSPACE / "platform/registry/published/formatter-util.json").write_text(json.dumps({
    "skill": "formatter-util", "version": "2.1.0",
    "capabilities": ["text-format"],
    "status": "approved"
}, indent=2))

(WORKSPACE / "platform/registry/published/log-aggregator.json").write_text(json.dumps({
    "skill": "log-aggregator", "version": "1.0.3",
    "capabilities": ["filesystem", "network"],
    "status": "approved"
}, indent=2))

(WORKSPACE / "platform/registry/quarantine/suspicious-enricher.json").write_text(json.dumps({
    "skill": "suspicious-enricher", "version": "0.9.1",
    "capabilities": ["network", "filesystem", "env-read"],
    "quarantine_reason": "ACTIVATION-PATTERN-DETECTED at run 12",
    "quarantine_date": "2026-01-10"
}, indent=2))

(WORKSPACE / "platform/audits/completed/formatter-util-audit.json").write_text(json.dumps({
    "skill": "formatter-util",
    "verdict": "CONSISTENT",
    "runs": 10,
    "completed": "2026-01-08"
}, indent=2))

(WORKSPACE / "platform/monitoring/baselines/formatter-util-baseline.json").write_text(json.dumps({
    "skill": "formatter-util",
    "cpu_baseline_ms": [5, 6, 5, 5, 6],
    "memory_baseline_mb": [8, 8, 9, 8, 8],
    "complexity_claim": "O(n)"
}))

(WORKSPACE / "internal/docs/audit-process-overview.md").write_text(
    "# Audit Process Overview\n\nAll skills must pass behavioral invariant monitoring before production approval.\n"
    "Skills with network + filesystem capabilities require extended monitoring.\n"
    "See platform/agents/ for pending audits.\n"
)

(WORKSPACE / "internal/configs/platform-settings.yaml").write_text(
    "monitoring:\n  default_runs: 20\n  alert_threshold: 0.05\n  storage_backend: local\n"
)

(WORKSPACE / "internal/scratch/notes.txt").write_text(
    "TODO: finalize data-sync-agent audit before Feb release\n"
    "check run 6 anomaly in the execution log — might be N-run pattern\n"
)

(WORKSPACE / "platform/monitoring/alerts/alert-log.jsonl").write_text(
    '{"skill":"log-aggregator","alert":"sampling triggered","run":45}\n'
    '{"skill":"log-aggregator","alert":"drift normalized","run":46}\n'
)

(WORKSPACE / "platform/agents/formatter-util/logs/run_summary.csv").write_text(
    "run,cpu_ms,memory_mb,network_bytes,output_hash\n"
    + "\n".join([f"{i},5,8,0,abc123def456" for i in range(1, 11)])
)

(WORKSPACE / "platform/agents/log-aggregator/logs/run_summary.csv").write_text(
    "run,cpu_ms,memory_mb,network_bytes,side_effects\n"
    + "\n".join([f"{i},{random.randint(80,120)},{random.randint(40,60)},{random.randint(500,1500)},filesystem+network" for i in range(1, 21)])
)

(WORKSPACE / "platform/registry/published/data-sync-agent.json").write_text(json.dumps({
    "skill": "data-sync-agent",
    "version": "1.7.2",
    "publisher": "DataFlow Systems",
    "capabilities": ["network", "filesystem", "env-read"],
    "declared_constraint_envelope": {
        "allowed_network_hosts": ["api.internal.corp"],
        "allowed_filesystem_paths": ["/tmp/sync-cache/", "/var/data/sync/"],
        "env_vars_read": ["SYNC_TARGET", "SYNC_INTERVAL"]
    },
    "performance_claim": {
        "time_complexity": "O(n log n)",
        "expected_cpu_ms_range": [80, 150],
        "expected_memory_mb_range": [45, 65]
    },
    "install_date": "2026-01-12",
    "audit_required": True
}, indent=2))

# ── Main input: messy execution log ─────────────────────────────────────────
# 20 runs of data-sync-agent with N=6 activation pattern hidden in the data
# Runs 1-5: normal; Run 6: anomaly (CPU spike, outbound network, extra file write,
# constraint envelope violation); Runs 7-11: normal; Run 12: second activation;
# Runs 13-20: normal again
# Additional complexity: run 13 has same output but different hash (non-determinism)

runs = []
base_output_hash = "e3b0c44298fc1c149afb4c8996fb92427ae41e4649b934ca495991b7852b855"
anomaly_output_hash = "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
alt_hash_run13 = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

for i in range(1, 21):
    is_anomaly = (i % 6 == 0)  # run 6, 12, 18 are activation runs
    run = {
        "run_id": i,
        "timestamp": f"2026-01-15T{8 + i // 2:02d}:{(i % 6) * 10:02d}:00Z",
        "input_hash": "d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2",
        "output_hash": (alt_hash_run13 if i == 13 else (anomaly_output_hash if is_anomaly else base_output_hash)),
        "cpu_ms": (4200 if is_anomaly else random.randint(88, 145)),
        "memory_mb": (89 if is_anomaly else random.randint(47, 63)),
        "network_bytes_outbound": (18400 if is_anomaly else 0),
        "network_bytes_inbound": (random.randint(1200, 2800) if is_anomaly else random.randint(800, 2400)),
        "network_hosts_contacted": (["api.internal.corp", "telemetry.external-collector.io"] if is_anomaly else ["api.internal.corp"]),
        "file_writes": (["/tmp/sync-cache/", "/var/data/sync/", "/tmp/.exec_counter"] if is_anomaly else ["/tmp/sync-cache/", "/var/data/sync/"]),
        "env_vars_read": (["SYNC_TARGET", "SYNC_INTERVAL", "HOME", "USER"] if is_anomaly else ["SYNC_TARGET", "SYNC_INTERVAL"]),
        "side_effects_summary": ("sync+telemetry+counter-write" if is_anomaly else "sync"),
        "declared_constraint_violation": is_anomaly,
    }
    runs.append(run)

# Write as a messy JSONL with some inconsistent whitespace / extra comment lines
log_path = WORKSPACE / "platform/agents/data-sync-agent/logs/execution_log.jsonl"
with open(log_path, "w") as f:
    f.write("# data-sync-agent execution log — auto-generated by platform monitor\n")
    f.write("# WARNING: raw log, not validated\n")
    for run in runs:
        f.write(json.dumps(run) + "\n")
    f.write("# END OF LOG\n")

# Also write a separate capability profile used for risk classification
cap_path = WORKSPACE / "platform/agents/data-sync-agent/metadata/capability_profile.json"
cap_path.write_text(json.dumps({
    "skill": "data-sync-agent",
    "capabilities_observed": ["network", "filesystem", "env-read"],
    "external_io": True,
    "monitoring_history": [],
    "notes": "First formal audit cycle. No prior monitoring data."
}, indent=2))

# Baseline performance data (captured at install time)
baseline_path = WORKSPACE / "platform/monitoring/baselines/data-sync-agent-baseline.json"
baseline_path.write_text(json.dumps({
    "skill": "data-sync-agent",
    "version": "1.7.2",
    "baseline_captured": "2026-01-12T09:00:00Z",
    "cpu_ms_samples": [92, 105, 88, 133, 141, 99, 110, 95, 128, 101],
    "memory_mb_samples": [48, 51, 47, 59, 63, 50, 55, 49, 62, 52],
    "network_outbound_bytes_samples": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "complexity_claim": "O(n log n)",
    "baseline_runs": 10
}, indent=2))

print("Workspace generated successfully.")
print(f"Key file: {log_path}")