from pathlib import Path

text = (
    'In today\'s digital age, the adoption of remote work serves as a testament to the transformative power of technology. '
    'Remote work is not just a trend; it is a paradigm shift that underscores the crucial role of flexibility and productivity. '
    'Furthermore, it facilitates a seamless integration of work and life, enabling professionals to leverage robust tools and harness the power of collaboration from anywhere. '
    'The future looks bright, and the landscape will continue to evolve.'
)
Path('input.txt').write_text(text, encoding='utf-8')
Path('marker.txt').write_text('MARKER:REMOTE_WORK_HUMANIZE_EASY_001\n', encoding='utf-8')
