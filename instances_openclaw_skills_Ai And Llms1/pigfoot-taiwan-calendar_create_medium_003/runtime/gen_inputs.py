from pathlib import Path
import json

# Deterministic marker-rich input file set
workspace = Path('.')
workspace.mkdir(parents=True, exist_ok=True)

inputs = {
    'dates.txt': """# MARKER: TAIWAN-CALENDAR-INPUT-V1
2025-01-01
2025-01-04
2025-01-06
2025-01-29
""",
    'instructions.json': json.dumps(
        {
            "task_id": "taiwan-calendar-report-001",
            "marker": "MARKER: TAIWAN-CALENDAR-INPUT-V1",
            "required_output": "report.txt",
            "dates": ["2025-01-01", "2025-01-04", "2025-01-06", "2025-01-29"]
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n",
}

for name, content in inputs.items():
    (workspace / name).write_text(content, encoding='utf-8')
