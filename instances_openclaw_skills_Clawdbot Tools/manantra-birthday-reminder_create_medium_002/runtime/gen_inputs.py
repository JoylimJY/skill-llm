from pathlib import Path
import json
import os

def main():
    data_dir = Path('data')
    data_dir.mkdir(parents=True, exist_ok=True)
    birthdays = data_dir / 'birthdays.md'
    birthdays.write_text(
        '# Geburstage\n\n'
        '- **MarkerAlpha** - 01.01.2001 (wird 25)\n'
        '- **MarkerBeta** - 12.06.1999\n'
        '- **MarkerGamma** - 23.11.1988\n',
        encoding='utf-8'
    )

if __name__ == '__main__':
    main()
