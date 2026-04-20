from pathlib import Path
import json

base = Path('.')
(base / 'notes').mkdir(parents=True, exist_ok=True)
(base / 'data').mkdir(parents=True, exist_ok=True)

notes = """# Birthday Intake Notes

MARKER:BDAY-INTAKE-7F3A

Please migrate the following reminders into the birthday skill storage.

- Valentina hat am 14. Februar Geburtstag.
- Max was born on 15.03.1990.
- Lina wurde am 29.02.2004 geboren.
- Tom hat am 01.12. Geburtstag.

Additional note:
- MARKER-AGE-CHECK: if a year is known, include the turning age in the output file.
"""
(base / 'notes' / 'birthday_notes.txt').write_text(notes, encoding='utf-8')

seed = {
    "marker": "BDAY-SEED-7F3A",
    "expected_names": ["Valentina", "Max", "Lina", "Tom"],
    "expected_birthdays": ["14.02.2000", "15.03.1990", "29.02.2004", "01.12."]
}
(base / 'data' / 'seed.json').write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding='utf-8')
