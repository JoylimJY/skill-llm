from pathlib import Path
import json

base = Path('.')
inputs = base / 'inputs'
inputs.mkdir(exist_ok=True)

# Deterministic marker content
markers = {
    'system_name.txt': 'TARGET_SYSTEM=checkout-api\nMARKER=OPTIMIZE-7F3A\n',
    'baseline_metrics.json': {
        'database': {'latency_ms': 180, 'throughput_rps': 120, 'cost_usd': 42.5},
        'application': {'latency_ms': 95, 'throughput_rps': 210, 'cost_usd': 31.0},
        'frontend': {'latency_ms': 140, 'throughput_rps': 180, 'cost_usd': 18.75}
    },
    'after_metrics.json': {
        'database': {'latency_ms': 130, 'throughput_rps': 150, 'cost_usd': 39.0},
        'application': {'latency_ms': 80, 'throughput_rps': 240, 'cost_usd': 29.5},
        'frontend': {'latency_ms': 110, 'throughput_rps': 195, 'cost_usd': 17.25}
    },
    'bottleneck_hint.txt': 'TOP_BOTTLENECK=database\nNOTE=QUERY_PLAN_REGRESSION\n'
}

(inputs / 'system_name.txt').write_text(markers['system_name.txt'], encoding='utf-8')
(inputs / 'baseline_metrics.json').write_text(json.dumps(markers['baseline_metrics.json'], indent=2), encoding='utf-8')
(inputs / 'after_metrics.json').write_text(json.dumps(markers['after_metrics.json'], indent=2), encoding='utf-8')
(inputs / 'bottleneck_hint.txt').write_text(markers['bottleneck_hint.txt'], encoding='utf-8')

# Simple manifest for debugging/eval assistance
manifest = {
    'files': ['system_name.txt', 'baseline_metrics.json', 'after_metrics.json', 'bottleneck_hint.txt'],
    'marker': 'OPTIMIZE-7F3A'
}
(inputs / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
