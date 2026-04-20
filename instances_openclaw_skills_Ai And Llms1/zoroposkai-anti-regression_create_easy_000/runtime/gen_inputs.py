from pathlib import Path

Path('input_marker.txt').write_text('This is a deterministic marker file.\nMARKER-42\n', encoding='utf-8')
