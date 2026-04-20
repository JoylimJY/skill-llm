from pathlib import Path

Path('input_marker.txt').write_text('TAIWAN_CALENDAR_TASK_MARKER_2025\nDate: 2025-01-03\n', encoding='utf-8')
Path('notes.txt').write_text('User wants the next working day after a specific date.\n', encoding='utf-8')
