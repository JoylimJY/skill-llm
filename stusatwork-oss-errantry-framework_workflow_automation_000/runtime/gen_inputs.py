import os
import json
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory Structure ---
dirs = [
    "omnroute/docs",
    "omnroute/pipeline/agents",
    "omnroute/pipeline/connectors",
    "omnroute/pipeline/orchestrator",
    "omnroute/audit",
    "omnroute/legacy",
    "omnroute/infra/k8s",
    "omnroute/infra/monitoring",
    "omnroute/tests",
    "omnroute/notes/meetings",
    "omnroute/notes/drafts",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor Files ---
distractor_files = {
    "omnroute/docs/api_schema.json": json.dumps({
        "version": "2.1.0",
        "endpoints": ["/routes", "/depots", "/vehicles"],
        "auth": "Bearer"
    }, indent=2),

    "omnroute/pipeline/agents/route_planner.py": textwrap.dedent("""\
        # Route planner agent - GPT-4 backed
        import openai
        def plan_route(origin, destination, constraints):
            # TODO: replace with local model
            response = openai.ChatCompletion.create(
                model='gpt-4',
                messages=[{'role':'user','content':f'Plan route from {origin} to {destination}'}]
            )
            return response.choices[0].message.content
    """),

    "omnroute/pipeline/agents/demand_forecaster.py": textwrap.dedent("""\
        # Demand forecasting agent
        import random
        def forecast(region, days=7):
            # HACK: synthetic data, not validated
            return [random.randint(50, 200) for _ in range(days)]
    """),

    "omnroute/pipeline/connectors/fleet_api.py": textwrap.dedent("""\
        # Fleet API connector
        FLEET_API_URL = 'https://fleet.omnroute.internal/v2'
        def get_vehicle_status(vehicle_id):
            import requests
            return requests.get(f'{FLEET_API_URL}/vehicles/{vehicle_id}').json()
    """),

    "omnroute/pipeline/connectors/weather_api.py": textwrap.dedent("""\
        # Weather data connector
        WEATHER_URL = 'https://api.weather.internal'
        def get_forecast(lat, lon):
            import requests
            return requests.get(f'{WEATHER_URL}?lat={lat}&lon={lon}').json()
    """),

    "omnroute/pipeline/orchestrator/main.py": textwrap.dedent("""\
        # Orchestrator - coordinates all agents
        # Uses rule-based routing, no consensus protocol
        def orchestrate(job):
            if job['priority'] == 'high':
                return route_planner(job)
            else:
                return demand_forecaster(job)
    """),

    "omnroute/legacy/old_router.py": textwrap.dedent("""\
        # DEPRECATED: brute force exhaustive search router
        # Runs on x86 cluster - very compute intensive
        # Average: 4200 watts per batch job
        def brute_force_route(graph, start, end):
            from itertools import permutations
            best = None
            for perm in permutations(graph.nodes):
                cost = evaluate(perm)
                if best is None or cost < best[0]:
                    best = (cost, perm)
            return best
    """),

    "omnroute/infra/k8s/deployment.yaml": textwrap.dedent("""\
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: omnroute-orchestrator
        spec:
          replicas: 3
          selector:
            matchLabels:
              app: orchestrator
    """),

    "omnroute/infra/monitoring/alerts.json": json.dumps({
        "alerts": [
            {"name": "high_latency", "threshold_ms": 2000},
            {"name": "model_drift", "threshold": 0.15},
            {"name": "memory_overflow", "threshold_gb": 8}
        ]
    }, indent=2),

    "omnroute/tests/test_route_planner.py": textwrap.dedent("""\
        # Unit tests - only happy path tested
        # No adversarial inputs tested
        def test_basic_route():
            result = plan_route('NYC', 'LA', {})
            assert result is not None
    """),

    "omnroute/notes/meetings/2024_03_kickoff.txt": textwrap.dedent("""\
        Kickoff meeting notes - March 2024
        - Team agreed to use multi-agent approach
        - Concern raised: demand_forecaster uses synthetic data
        - Action: validate synthetic data before production
        - Decision: skip red-team testing to meet deadline
        - Concern: orchestrator has no consensus mechanism
        - Deferred: compute cost analysis
    """),

    "omnroute/notes/drafts/arch_notes_v1.txt": textwrap.dedent("""\
        Architecture notes (DRAFT)
        The orchestrator pulls from a static knowledge base (last updated Q1 2023).
        No live data connections established yet.
        Fleet API is an external integration point - not security reviewed.
        Weather API connector has no error handling.
        Demand forecaster output is used directly without validation.
        Model: GPT-4 (cloud, high cost per token).
        Fallback: legacy brute-force router.
    """),
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE MAIN PROBLEM: Messy pipeline description to be audited ---
pipeline_description = textwrap.dedent("""\
# OmnRoute AI Pipeline — System Description v0.9 (DRAFT)

## Overview
OmnRoute is building a multi-agent logistics AI pipeline. The following describes
the current proposed architecture for review.

## Components

### Agent 1: Route Planner
- Backed by GPT-4 (cloud API, ~$0.03/1k tokens, average 8k tokens per job)
- Purpose: Generate optimal delivery routes from origin to destination
- Data source: Static routing database (frozen Q1 2023 snapshot)
- Output: Route JSON fed directly to dispatch system without validation

### Agent 2: Demand Forecaster
- Uses synthetic training data (randomly generated, not validated against real demand)
- Purpose: Predict package volumes per region per day
- Optimizes for: Prediction speed (< 100ms response time)
- Note: Output directly influences inventory allocation decisions

### Agent 3: Fleet Status Monitor
- Connects to Fleet API (external, unauthenticated endpoint)
- Connects to Weather API (external, no error handling)
- Purpose: Track vehicle positions and conditions
- Integration: Both APIs are external boundary points

### Orchestrator
- Rule-based priority routing (high/low priority only)
- No consensus mechanism between agents
- Knowledge base: Static document store, last updated Q1 2023
- Decision: Skip adversarial/red-team testing to meet March deadline
- Fallback: Legacy brute-force exhaustive search (x86 cluster, ~4200W per batch)

## Outstanding Concerns (from kickoff meeting)
- Demand forecaster uses unvalidated synthetic data
- No adversarial testing planned
- Compute costs not analyzed
- Orchestrator knowledge base is frozen/dead
- No failure mode documentation exists

## Deployment Decision
The team has decided to deploy by end of Q2 regardless of outstanding concerns,
using the brute-force fallback if the AI agents underperform.
""")

with open(os.path.join(WORKSPACE, "omnroute/pipeline_description_v0.9.md"), "w") as f:
    f.write(pipeline_description)

# --- Framework reference file (the SKILL.md is provided to the agent via standard means) ---
# Create a placeholder indicating where the framework doc lives
with open(os.path.join(WORKSPACE, "omnroute/audit/.gitkeep"), "w") as f:
    f.write("")

print("Workspace initialized successfully.")
print(f"Files created in: {WORKSPACE}")