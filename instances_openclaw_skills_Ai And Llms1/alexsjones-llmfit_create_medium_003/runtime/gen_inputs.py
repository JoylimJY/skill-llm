from pathlib import Path
import json

# Deterministic input generation with marker content
workspace = Path('.')
inputs = {
    'hardware_profile.txt': 'MARKER:LOCAL-LLM-HW\nCPU: 8 cores\nRAM: 32 GB\nGPU: NVIDIA RTX 3060\nVRAM: 12 GB\n',
    'requirements.json': json.dumps({
        'use_cases': ['coding', 'chat'],
        'limit': 3,
        'prefer_ollama': True,
        'marker': 'MARKER:RECOMMENDATION-REQUEST'
    }, indent=2),
}
for name, content in inputs.items():
    (workspace / name).write_text(content, encoding='utf-8')
