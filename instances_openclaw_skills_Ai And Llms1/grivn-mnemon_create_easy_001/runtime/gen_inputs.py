from pathlib import Path

Path('task_context.txt').write_text(
    'Marker: PROJECT_ORION_RELEASE_CHECKLIST\n'
    'The release checklist for Project Orion lives in the shared docs folder and should be reviewed before Friday.\n',
    encoding='utf-8'
)
