from pathlib import Path
import json

root = Path('.')
(root / 'inputs').mkdir(exist_ok=True)

marker = {
    'target': 'ecommerce_checkout_pipeline',
    'baseline_bottleneck': 'excessive sequential coordination between agents',
    'optimization_change': 'parallelize profiling and reduce cross-agent chatter',
    'expected_benefit': 'lower latency and better throughput'
}

(root / 'inputs' / 'benchmark.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
(root / 'inputs' / 'notes.txt').write_text(
    'MARKER: baseline bottleneck is sequential coordination.\n'
    'MARKER: desired change is parallel profiling.\n'
    'MARKER: expected benefit is reduced latency.\n',
    encoding='utf-8'
)
