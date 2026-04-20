from pathlib import Path

workspace = Path('.')
(workspace / 'task_marker.txt').write_text('CLAUDITOR_TASK_MARKER\nstep=1\ndifficulty=easy\n', encoding='utf-8')
(workspace / 'reference_note.txt').write_text('Target user: sysaudit\nCommand family: useradd system account\n', encoding='utf-8')
