import os
import json
import random

random.seed(42)

os.makedirs('scripts', exist_ok=True)

skill_md = '''# TokenGuard — LLM API 429 Prevention Engine

**Version:** 1.5.0

## Supported Models

- gemini-3-flash (1M TPM)
- gemini-3-pro (2M TPM)
- claude-haiku (50K TPM)
- claude-sonnet (200K TPM)
- claude-opus (200K TPM)
- gpt-4o (800K TPM)
- deepseek (1M TPM)
'''

with open('SKILL.md', 'w') as f:
    f.write(skill_md)

test_prompts = {
    'short_prompt': 'Hello, how are you today?',
    'medium_prompt': 'Explain the concept of rate limiting in APIs. ' * 20,
    'cjk_prompt': '你好世界。这是一个测试提示词，用于验证CJK字符的token估算功能。' * 10,
    'long_prompt': 'This is a very long document. ' * 500,
    'marker_prompt': 'MARKER_CONTENT_XK9Z: This prompt has a unique marker for duplicate detection testing.'
}

with open('test_prompts.json', 'w', encoding='utf-8') as f:
    json.dump(test_prompts, f, ensure_ascii=False, indent=2)

print('Input files created: SKILL.md, test_prompts.json')
