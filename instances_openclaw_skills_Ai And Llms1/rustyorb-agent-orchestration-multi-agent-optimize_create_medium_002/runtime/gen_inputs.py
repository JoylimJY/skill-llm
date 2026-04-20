import json
import os
from pathlib import Path

ROOT = Path('.')

# Deterministic marker content
agent_logs = [
    {
        "agent": "db-agent",
        "latency_ms": 240,
        "tokens": 8200,
        "errors": 1,
        "marker": "ALPHA-DB-2025"
    },
    {
        "agent": "app-agent",
        "latency_ms": 310,
        "tokens": 9100,
        "errors": 0,
        "marker": "ALPHA-APP-2025"
    },
    {
        "agent": "frontend-agent",
        "latency_ms": 180,
        "tokens": 6400,
        "errors": 2,
        "marker": "ALPHA-FE-2025"
    }
]

workload = {
    "work_items": [
        {"id": "w1", "type": "query-tuning", "cost": 5, "priority": 3},
        {"id": "w2", "type": "render-optimization", "cost": 4, "priority": 2},
        {"id": "w3", "type": "cache-review", "cost": 2, "priority": 1},
        {"id": "w4", "type": "async-audit", "cost": 6, "priority": 4}
    ],
    "marker": "WORKLOAD-MARKER-42"
}

target_goals = {
    "target": "multi-agent checkout pipeline",
    "performance_goals": {
        "latency_reduction_percent": 20,
        "token_reduction_percent": 15,
        "error_rate_max": 1
    },
    "marker": "GOALS-MARKER-2025"
}

(ROOT / 'agent_logs.json').write_text(json.dumps(agent_logs, indent=2), encoding='utf-8')
(ROOT / 'workload.json').write_text(json.dumps(workload, indent=2), encoding='utf-8')
(ROOT / 'goals.json').write_text(json.dumps(target_goals, indent=2), encoding='utf-8')
