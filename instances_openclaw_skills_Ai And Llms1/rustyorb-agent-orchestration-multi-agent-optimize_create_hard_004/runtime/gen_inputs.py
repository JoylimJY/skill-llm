from pathlib import Path
import json
import random

random.seed(202405)
base = Path('.')

# Deterministic marker-rich input files
(base / 'target_system.txt').write_text(
    'TARGET=enterprise_api_gateway\n'
    'ENV=production\n'
    'MARKER_SYSTEM=orbit-payments-v2\n'
    'MARKER_OWNER=platform-observability\n'
    'SLO_LATENCY_P95_MS=250\n'
    'SLO_ERROR_RATE_PCT=0.50\n',
    encoding='utf-8'
)

(base / 'metrics.csv').write_text(
    'component,baseline_p95_ms,baseline_error_rate_pct,baseline_cost_per_1k,requests_per_min\n'
    'db,180,0.10,0.18,4200\n'
    'app,220,0.30,0.24,4200\n'
    'frontend,140,0.05,0.12,4200\n'
    'orchestrator,95,0.02,0.08,4200\n',
    encoding='utf-8'
)

plan = {
    'marker': 'BENCHMARK-MULTI-AGENT-OPTIMIZATION',
    'targets': {
        'latency_reduction_pct': 18,
        'cost_reduction_pct': 12,
        'error_rate_reduction_pct': 25,
    },
    'constraints': {
        'budget_usd_monthly': 4800,
        'max_context_tokens': 4096,
        'rollout_mode': 'gradual',
    },
    'agents': [
        {'name': 'db-agent', 'weight': 0.35},
        {'name': 'app-agent', 'weight': 0.40},
        {'name': 'frontend-agent', 'weight': 0.15},
        {'name': 'orchestrator-agent', 'weight': 0.10},
    ]
}
(base / 'optimization_brief.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')

# Deterministic workload trace with embedded markers
rows = [
    'timestamp,agent,queue_depth,token_usage,latency_ms,marker',
    '2025-04-01T09:00:00Z,db-agent,12,1800,205,TRACE-A',
    '2025-04-01T09:00:10Z,app-agent,18,2400,260,TRACE-B',
    '2025-04-01T09:00:20Z,frontend-agent,5,900,150,TRACE-C',
    '2025-04-01T09:00:30Z,orchestrator-agent,7,700,110,TRACE-D',
]
(base / 'workload_trace.csv').write_text('\n'.join(rows) + '\n', encoding='utf-8')
