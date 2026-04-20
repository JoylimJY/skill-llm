from pathlib import Path

workspace = Path('.')
(workspace / 'input.txt').write_text(
    'MARKER_HUMANIZER_INPUT\nAt the end of the day, the project was successful because it was able to bring together the team, the timeline, and the budget in a way that was both efficient and effective. First, the planning phase was completed, and secondly, the implementation phase was finished on schedule. I hope this helps, and let me know if you have any questions.\n',
    encoding='utf-8'
)
