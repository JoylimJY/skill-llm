from pathlib import Path

text = """Draft Title: The future of neighborhood cafés

Great question! In today's digital age, neighborhood cafés play a crucial role in the local community. They serve as a vibrant hub where people can work, study, and connect. Moreover, they offer a seamless experience that caters to diverse needs. The future looks bright.

Marker: CAFE-4242
"""
Path('draft.txt').write_text(text, encoding='utf-8')
