from pathlib import Path

# Deterministic input generation with a marker for evaluation
Path('project_name.txt').write_text('Deepseek V3 Lite Agent\n', encoding='utf-8')
Path('project_tagline.txt').write_text('An effective content creator for concise documentation tasks.\n', encoding='utf-8')
Path('marker.txt').write_text('DEEPSEEK_V3_LITE_AGENT_READY\n', encoding='utf-8')
Path('notes.txt').write_text('Write a short README draft with Overview, Features, Usage, and Notes sections.\n', encoding='utf-8')
