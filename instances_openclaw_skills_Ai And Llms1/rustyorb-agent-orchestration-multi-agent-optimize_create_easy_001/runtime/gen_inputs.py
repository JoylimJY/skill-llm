import json
from pathlib import Path

marker = "MULTI_AGENT_OPTIMIZATION_MARKER_2025"
inputs = {
    "system_profile.json": {
        "target": "fictional multi-agent workflow",
        "baseline_latency_ms": 420,
        "baseline_cost_units": 18,
        "marker": marker
    },
    "agent_metrics.json": {
        "agents": [
            {"name": "planner", "latency_ms": 120, "cost_units": 5},
            {"name": "retriever", "latency_ms": 170, "cost_units": 7},
            {"name": "writer", "latency_ms": 130, "cost_units": 6}
        ],
        "marker": marker
    }
}

for filename, data in inputs.items():
    Path(filename).write_text(json.dumps(data, indent=2), encoding="utf-8")
