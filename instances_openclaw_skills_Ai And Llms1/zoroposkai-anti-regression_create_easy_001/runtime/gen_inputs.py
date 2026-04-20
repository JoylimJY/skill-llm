from pathlib import Path

Path('input_marker.txt').write_text('MARKER-7F3A-ALPHA\n', encoding='utf-8')
Path('notes.txt').write_text('This is a distractor file.\n', encoding='utf-8')
