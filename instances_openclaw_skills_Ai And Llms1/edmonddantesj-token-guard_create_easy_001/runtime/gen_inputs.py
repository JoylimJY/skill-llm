from pathlib import Path

skill_md = Path('SKILL.md')
content = """# TokenGuard — LLM API 429 Prevention Engine

<!-- Marker: TG-EASY-001 -->

**Version:** 1.5.0  
**Author:** Aoineco & Co.  
**License:** MIT  
**Tags:** rate-limit, 429, token-management, cost-optimization, llm-guard, high-performance

## Supported Models
- gemini-3-flash
- gemini-3-pro
- claude-haiku
- claude-sonnet
- claude-opus
- gpt-4o
- deepseek
"""
skill_md.write_text(content, encoding='utf-8')
