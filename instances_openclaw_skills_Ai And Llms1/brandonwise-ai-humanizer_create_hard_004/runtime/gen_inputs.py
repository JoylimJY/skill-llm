from pathlib import Path
import random

random.seed(1337)

base = Path('.')
text = (
    'In today\'s rapidly evolving landscape, the implementation of sustainable mobility solutions '
    'serves as a testament to the crucial role of innovation, collaboration, and strategic planning. '
    'Experts believe that these transformative initiatives are shaping the future in a holistic way, '
    'highlighting a multifaceted approach that leverages synergy across stakeholders. '
    'It is worth noting that the city\'s transit pilot, MARKER_PILOT_4821, reduced commute times by 17% '
    'over a six-week period, according to the transport department. '
    'Despite challenges, the program continues to thrive and will likely empower communities to embrace '
    'a seamless ecosystem of solutions. The future looks bright.'
)
(base / 'draft.txt').write_text(text, encoding='utf-8')

notes = [
    'MARKER_SUMMARY_4821',
    'Remove filler and hype',
    'Keep the transit pilot statistic',
    'Prefer concrete language over generic conclusions',
]
(base / 'notes.txt').write_text('\n'.join(notes), encoding='utf-8')
