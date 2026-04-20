from pathlib import Path
import json

root = Path('.')
(root / 'prompts').mkdir(exist_ok=True)
(root / 'scripts').mkdir(exist_ok=True)

(root / 'prompts' / 'system.md').write_text(
    '# System Prompt\n\nMarker: TRINITY-SYS-001\nThis file contains a long prompt that should be compressed carefully while preserving code blocks, URLs, file paths, and variable names.\n\n```bash\nexport TRINITY_MODE=balanced\n````\n\nVisit https://example.com/docs/trinity-compress for reference.\n',
    encoding='utf-8'
)

(root / 'prompts' / 'developer.md').write_text(
    '# Developer Prompt\n\nMarker: TRINITY-DEV-002\nPlease keep the repository path ./skills/trinity-compress intact and do not rewrite identifiers like trinityCompressConfig.\n',
    encoding='utf-8'
)

(root / 'prompts' / 'user.md').write_text(
    '# User Prompt\n\nMarker: TRINITY-USER-003\nCompress the prompt bundle while keeping any file path such as scripts/trinity-compress.sh and Makefile targets readable.\n',
    encoding='utf-8'
)

config = {
    'mode': 'balanced',
    'targets': ['prompts/system.md', 'prompts/developer.md', 'prompts/user.md'],
    'preserve': ['code_blocks', 'urls', 'file_paths', 'variable_names']
}
(root / 'trinity-compress.config.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
