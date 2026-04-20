import os
from pathlib import Path
import json

root = Path('.')
notes = root / 'notes.txt'
notes.write_text(
    'MARKER:LAUNCH-42\n'
    'Product name: LumaDesk\n'
    'Category: portable smart desk lamp\n'
    'Key facts: 3 light modes, 12-hour battery, USB-C charging, under 900g\n'
    'Audience: remote workers and students\n'
    'Launch angle: focus on comfort, portability, and battery life\n',
    encoding='utf-8'
)

(root / 'brand_guidelines.txt').write_text(
    'MARKER:BRAND-GUIDE-7\n'
    'Tone: clear, modern, optimistic, not hypey\n'
    'Avoid: exaggerated claims, technical jargon without explanation\n'
    'Preferred phrasing: compact, reliable, workspace-friendly\n',
    encoding='utf-8'
)

(root / 'source_quote.txt').write_text(
    'MARKER:QUOTE-19\n'
    'Founder quote: "We built LumaDesk to make long work sessions feel lighter and more comfortable."\n',
    encoding='utf-8'
)
