from pathlib import Path
import json
import random

random.seed(42)

Path('input_context.txt').write_text(
    "Marker: TED_TALK_TASK_2025\n"
    "Context: The team discovered that a system designed for fast experimentation kept failing because people were optimizing for local speed instead of shared learning.\n"
    "Insight: The real bottleneck was not code generation, but decision latency.\n"
    "Details: They introduced a three-stage rhythm: capture uncertainty, validate assumptions, then codify the pattern.\n"
    "Examples: release reviews, incident retrospectives, and small-scale pilots.\n"
    "Concerns: people worried this would slow them down, but it reduced rework.\n",
    encoding='utf-8'
)

Path('notes.json').write_text(
    json.dumps({
        "marker": "TED_TALK_TASK_2025_JSON",
        "topic": "decision latency and learning loops",
        "audience": "engineering leaders",
        "tone": "inspiring but practical"
    }, indent=2),
    encoding='utf-8'
)
