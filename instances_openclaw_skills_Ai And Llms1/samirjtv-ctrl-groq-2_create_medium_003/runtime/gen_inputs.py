from pathlib import Path
import json

# Deterministic input generation with marker content
files = {
    'prompt.txt': 'MARKER_PROMPT: Summarize the following product update in two sentences.\n\nThe new release improves latency and adds batch export.\n',
    'system.txt': 'MARKER_SYSTEM: You are a concise assistant. Keep responses under 50 words.\n',
    'metadata.json': json.dumps({
        'marker': 'MARKER_META_7F3A',
        'task': 'groq completion utility',
        'version': 1
    }, indent=2) + '\n'
}
for name, content in files.items():
    Path(name).write_text(content, encoding='utf-8')
