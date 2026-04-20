from pathlib import Path

# Deterministic marker content for evaluation
Path('input_marker.txt').write_text('AAP_TASK_MARKER_2025_04_01\n', encoding='utf-8')
Path('README_NOTE.txt').write_text('Generate server.js and client.js based on the AAP demo requirements.\n', encoding='utf-8')
