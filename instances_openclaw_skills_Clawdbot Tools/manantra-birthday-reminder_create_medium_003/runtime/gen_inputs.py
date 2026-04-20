from pathlib import Path

base = Path('.')
(base / 'data').mkdir(parents=True, exist_ok=True)
(base / 'data' / 'birthdays.md').write_text('# Geburtstage\n\n- **Max** - 15.03.1990\n', encoding='utf-8')
(base / 'marker.txt').write_text('MARKER_BIRTHDAY_INPUT_V1', encoding='utf-8')
