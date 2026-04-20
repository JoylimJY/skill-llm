import os
from pathlib import Path

root = Path('.')
(root / 'agents').mkdir(exist_ok=True)
(root / '.claude').mkdir(exist_ok=True)
(root / '.claude' / 'agents').mkdir(parents=True, exist_ok=True)

files = {
    root / 'agents' / 'security-auditor.md': """---\nname: security-auditor\ncategory: security\nmarker: REGISTRY-MARKER-SEC-001\n---\nReview code for vulnerabilities.\n""",
    root / '.claude' / 'agents' / 'code-reviewer.md': """---\nname: code-reviewer\ncategory: review\nmarker: REGISTRY-MARKER-REV-002\n---\nReview code for style and bugs.\n""",
}

for path, content in files.items():
    path.write_text(content, encoding='utf-8')
