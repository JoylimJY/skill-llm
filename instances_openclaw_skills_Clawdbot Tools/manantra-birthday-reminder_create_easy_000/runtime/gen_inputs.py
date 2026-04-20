from pathlib import Path

base = Path('.')
(base / 'data').mkdir(exist_ok=True)
(base / 'data' / 'marker.txt').write_text('BIRTHDAY_REMINDER_MARKER_7F3A2C\n', encoding='utf-8')
