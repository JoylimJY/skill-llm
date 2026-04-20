from pathlib import Path

base = Path('.')
data_dir = base / 'home' / 'clawd' / 'clawd' / 'data'
data_dir.mkdir(parents=True, exist_ok=True)

content = """# Geburtsliste

# MARKER: birthday-input-seed-2025-04-19

- **Existing Person** - 11.11.1991
- **Valentina** - 14.02.1999
- **Unrelated Note** - keep this line intact
"""
(data_dir / 'birthdays.md').write_text(content, encoding='utf-8')

# Secondary marker file for evaluation robustness
(base / 'birthdays_seed.txt').write_text('seed=424242\nmarker=BIRTHDAY_REMINDER_TASK\n', encoding='utf-8')
