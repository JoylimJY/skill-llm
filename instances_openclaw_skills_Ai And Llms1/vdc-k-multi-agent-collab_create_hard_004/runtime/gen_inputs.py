from pathlib import Path
import json
import random

random.seed(1337)

root = Path('.')

materials = {
    'project_brief.txt': (
        'PROJECT: lighthouse\n'
        'GOAL: ship a multi-agent documentation sync package\n'
        'KNOWN_MARKER: BRIEF-7F3A\n'
        'SCOPE: task board, changelog, context, weekly report, llms index\n'
        'NOTES: focus on document-driven sync and on-demand retrieval\n'
    ),
    'worklog.json': json.dumps({
        'project': 'lighthouse',
        'identity': 'by opal',
        'markers': ['WLOG-19C2', 'SYNC-READY'],
        'completed': [
            {'tag': '#docs', 'item': 'created initial task board'},
            {'tag': '#sync', 'item': 'captured collaboration protocol'},
            {'tag': '#weekly', 'item': 'prepared report structure'}
        ],
        'major_decision': 'Use document-driven synchronization with QMD-style retrieval.'
    }, indent=2),
    'tasks_seed.md': (
        '# lighthouse seeds\n\n'
        '- [ ] initialize task board\n'
        '- [ ] write changelog entries\n'
        '- [ ] record context decisions\n'
        '- [ ] draft weekly report\n'
        '- [ ] add machine-readable index\n'
        'MARKER: TASK-SEED-44B1\n'
    ),
    'report_requirements.txt': (
        'Weekly report must include:\n'
        '1. completed work summary\n'
        '2. tagged changelog aggregation\n'
        '3. pattern discovery\n'
        '4. candidate skill note if an operation repeats three or more times\n'
        'MARKER: REPORT-REQ-8D10\n'
    )
}

for name, content in materials.items():
    Path(name).write_text(content, encoding='utf-8')
