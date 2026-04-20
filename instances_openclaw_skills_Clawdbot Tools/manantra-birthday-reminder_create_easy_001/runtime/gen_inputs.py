from pathlib import Path

base = Path('.')
(base / 'data').mkdir(exist_ok=True)
(base / 'data' / 'birthdays.md').write_text(
    '# Geburtstage\n\n'
    '- **Marker Person** - 01.01.1999\n'
    '- **Existing Friend** - 31.12.2001 (wird 25)\n',
    encoding='utf-8'
)
