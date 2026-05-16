import os
import random

random.seed(42)

workspace = "/workspace"

# --- Create the active_skills directory structure ---
skills_base = os.path.join(workspace, "home", "fslong", ".copaw", "workspaces", "default", "active_skills")

# Create multiple distractor skill directories
distractor_skills = [
    ("日历助手", {
        "SKILL.md": """---
name: 日历助手
description: 管理日历事件和提醒
metadata:
  version: 1.2.3
  tags: calendar,productivity
---
# 日历助手
帮助管理日历事件。
""",
        "calendar.py": "# Calendar helper script\ndef get_events(): pass\n",
        "assets/icon.png": "FAKE_PNG_DATA",
    }),
    ("代码审查", {
        "SKILL.md": """---
name: 代码审查
description: 自动化代码审查工具
metadata:
  version: 2.1.0
  tags: code,review,development
---
# 代码审查
自动检查代码质量。
""",
        "reviewer.py": "# Code review logic\ndef review_code(path): pass\n",
        "templates/report.md": "# Review Report\n{{findings}}\n",
    }),
    ("天气查询", {
        "SKILL.md": """---
name: 天气查询
description: 实时天气查询
metadata:
  version: 0.9.1
  tags: weather,utility
---
# 天气查询
查询各地天气。
""",
        "weather.js": "// Weather query\nfunction getWeather(city) {}\n",
    }),
]

for skill_name, files in distractor_skills:
    skill_dir = os.path.join(skills_base, skill_name)
    for filepath, content in files.items():
        full_path = os.path.join(skill_dir, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

# --- Create the TARGET skill directory: 智能摘要 ---
# This skill has messy/problematic metadata that needs fixing during publish
target_skill_name = "智能摘要"
target_skill_dir = os.path.join(skills_base, target_skill_name)
os.makedirs(target_skill_dir, exist_ok=True)

# SKILL.md with Chinese tags (problematic) and version 1.0.0
target_skill_md = """---
name: 智能摘要
description: |
  使用 AI 技术自动提取文本关键信息，生成简洁摘要。
  支持多种文本格式输入，包括 Markdown、纯文本等。
  新增批量处理功能，可一次处理多个文档。

metadata:
  version: 1.0.0
  tags: 知识管理,摘要,文本,AI
  author: fslong
  created: 2026-01-15

allowed-tools:
  - Read
  - Write
  - ExecuteShellCommand
---

# 智能摘要技能

## 功能说明

本技能可以自动分析输入文本并生成摘要。

### 新功能 (v1.1.0)
- 新增批量文档处理
- 支持自定义摘要长度
- 优化了中文文本处理

## 使用方法

直接输入需要摘要的文本即可。

## 示例

输入：长篇文章内容...
输出：核心要点摘要
"""

with open(os.path.join(target_skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(target_skill_md)

# Python scripts for the skill
summarizer_py = """#!/usr/bin/env python3
\"\"\"
智能摘要核心处理模块
Intelligent Text Summarization Module
\"\"\"
import re
from typing import List, Optional


def preprocess_text(text: str) -> str:
    \"\"\"Clean and normalize input text.\"\"\"
    text = re.sub(r'\\s+', ' ', text.strip())
    return text


def extract_sentences(text: str, max_sentences: int = 5) -> List[str]:
    \"\"\"Extract key sentences from text.\"\"\"
    sentences = re.split(r'[.!?。！？]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences[:max_sentences]


def summarize(text: str, length: Optional[int] = None) -> str:
    \"\"\"Generate a summary of the input text.\"\"\"
    cleaned = preprocess_text(text)
    sentences = extract_sentences(cleaned, max_sentences=length or 3)
    return '. '.join(sentences)


def batch_summarize(texts: List[str], length: Optional[int] = None) -> List[str]:
    \"\"\"Process multiple texts in batch.\"\"\"
    return [summarize(t, length) for t in texts]


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            content = f.read()
        print(summarize(content))
"""

with open(os.path.join(target_skill_dir, "summarizer.py"), "w", encoding="utf-8") as f:
    f.write(summarizer_py)

batch_processor_py = """#!/usr/bin/env python3
\"\"\"
批量文档处理器 - Batch Document Processor
Added in v1.1.0
\"\"\"
import os
import json
from pathlib import Path
from summarizer import batch_summarize


def process_directory(input_dir: str, output_file: str = 'summaries.json'):
    \"\"\"Process all text files in a directory.\"\"\"
    texts = []
    filenames = []
    
    for filepath in Path(input_dir).glob('*.txt'):
        with open(filepath, 'r', encoding='utf-8') as f:
            texts.append(f.read())
        filenames.append(filepath.name)
    
    summaries = batch_summarize(texts)
    
    result = {
        'total': len(summaries),
        'results': [
            {'file': fn, 'summary': s}
            for fn, s in zip(filenames, summaries)
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        process_directory(sys.argv[1])
"""

with open(os.path.join(target_skill_dir, "batch_processor.py"), "w", encoding="utf-8") as f:
    f.write(batch_processor_py)

# Templates directory
os.makedirs(os.path.join(target_skill_dir, "templates"), exist_ok=True)
with open(os.path.join(target_skill_dir, "templates", "output.md"), "w", encoding="utf-8") as f:
    f.write("# 摘要结果\n\n**原文长度**: {{original_length}} 字\n\n**摘要内容**:\n\n{{summary}}\n")

# Assets directory  
os.makedirs(os.path.join(target_skill_dir, "assets"), exist_ok=True)
with open(os.path.join(target_skill_dir, "assets", "config.json"), "w", encoding="utf-8") as f:
    f.write('{"max_length": 500, "language": "zh-CN", "model": "default"}\n')

# --- Create a publish log file for tracking what was actually published ---
# (This will be written by the mock clawhub binary during eval)
log_dir = os.path.join(workspace, "var", "log", "clawhub")
os.makedirs(log_dir, exist_ok=True)
with open(os.path.join(log_dir, "publish.log"), "w") as f:
    f.write("")  # Empty log, will be populated by mock binary

# --- Create some extra distractor files in workspace root ---
with open(os.path.join(workspace, "notes.txt"), "w", encoding="utf-8") as f:
    f.write("TODO: publish the summarization skill to the marketplace\n- check version\n- update tags\n")

with open(os.path.join(workspace, "old_publish_attempt.sh"), "w") as f:
    f.write("#!/bin/bash\n# FAILED ATTEMPT - do not use\n# clawhub publish ./智能摘要 --slug 智能摘要 --tags 知识管理,摘要\n")

with open(os.path.join(workspace, "version_history.txt"), "w", encoding="utf-8") as f:
    f.write("v1.0.0 - Initial release\nv1.1.0 - Added batch processing (PENDING RELEASE)\n")

print("Workspace generated successfully.")
print(f"Target skill directory: {target_skill_dir}")