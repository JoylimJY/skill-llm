from pathlib import Path

# Deterministic input generation with a marker file for evaluation context.
Path('input_marker.txt').write_text(
    'BENCHMARK_MARKER::DEEPSEEK_REASONER_LITE_AGENT::2025-05\n',
    encoding='utf-8'
)
