#!/usr/bin/env python3
"""
gen_inputs_script.py
Builds the full sandbox workspace for the Nika skill creator task.
"""

import os
import json
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── helpers ──────────────────────────────────────────────────────────────────

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

# ═════════════════════════════════════════════════════════════════════════════
# 1. REFERENCE DOCUMENTS  (nika-spec, templates, checklist)
# ═════════════════════════════════════════════════════════════════════════════

write(WORKSPACE / "references/nika-spec.md", """\
---
name: nika-spec
description: Nika 平台约束规范
---

# Nika 平台约束规范

## 文档结构约束

### 两级文档结构
- 每个技能只允许两级文档：主文档 (main doc) + 子文档 (sub docs)
- 主文档文件名固定为 `README.md`，放在技能目录根部
- 子文档放在技能目录根部，与主文档同级，**不得建立更深目录**
- 绝对禁止三级或更深的文档嵌套

### 主文档约束
主文档只允许包含：
1. YAML front matter（必须字段：`name`、`description`）
2. 技能总览（一句话）
3. 输入契约（必要输入清单，含文件类型标注）
4. 输出契约（持久交付 + 临时交付）
5. 子文档索引（使用 `@子文档名` 引用，**禁止路径或扩展名**）
6. 可选：简短的快速开始（不超过 5 步）

主文档不得包含：
- 实现细节（步骤、清单、模板、示例）
- 超过 120 行内容

### 子文档约束
- 每个子文档必须有 YAML front matter（必须字段：`name`、`description`）
- 子文档只放实现细节（步骤、清单、模板、示例）
- 子文档之间不得互相引用（禁止任何 `@` 引用或路径链接）
- 单个子文档不超过 200 行

## 引用语法约束

### 正确引用方式
在主文档中引用子文档，必须使用：
```
@子文档名
```
例如：`@步骤清单`、`@输出模板`、`@示例集`

### 禁止的引用方式
以下写法全部禁止：
- `[子文档名](子文档名.md)` — 禁止路径引用
- `[子文档名](./子文档名.md)` — 禁止相对路径
- `[子文档名](path/to/子文档名.md)` — 禁止任何路径
- 在引用中出现 `.md`、`.txt`、`.json` 等扩展名

## YAML Front Matter 约束

主文档必须字段：
```yaml
---
name: 技能英文标识（kebab-case，无空格）
description: 一句话描述（中文，≤50字）
---
```

子文档必须字段：
```yaml
---
name: 子文档英文标识（kebab-case）
description: 子文档用途（中文，≤30字）
---
```

## 其他约束
- 所有文档使用 UTF-8 编码
- 技能目录名使用中文（与技能名一致）
- 禁止在文档中出现文件系统路径（如 `skills/xxx/yyy.md`）
""")

write(WORKSPACE / "references/main-doc-template.md", """\
---
name: nika-main-doc-template
description: 主文档骨架模板
---

# 主文档模板

```markdown
---
name: skill-name-in-kebab-case
description: 一句话技能描述（≤50字）
---

# 技能名称

一句话总览本技能的用途。

## 输入契约

| 输入项 | 文件类型 | 命名模式 | 最低要求 |
|--------|----------|----------|----------|
| XXX    | 设定文件 | xxx-setting.md | 需包含YYY字段 |

## 输出契约

### 持久交付
- 文件类型：设定文件 / 章节文件
- 命名规则：xxx-{主题}.md
- 内容结构：见 @输出模板

### 临时交付（屏幕输出）
- 摘要：XXX
- 检查结果：YYY
- 下一步指引：ZZZ

## 子文档索引

- @步骤清单 — 执行步骤与决策树
- @输出模板 — 交付文件的内容结构
- @示例集 — 典型输入输出示例
```
""")

write(WORKSPACE / "references/sub-doc-template.md", """\
---
name: nika-sub-doc-template
description: 子文档骨架模板
---

# 子文档模板

```markdown
---
name: sub-doc-name-in-kebab-case
description: 子文档用途（≤30字）
---

# 子文档标题

## 节一

内容...

## 节二

内容...
```

注意：
- 子文档不得包含 `@引用`
- 子文档不得包含文件路径或扩展名
- 不超过 200 行
""")

write(WORKSPACE / "references/validation-checklist.md", """\
---
name: validation-checklist
description: 人工校验清单
---

# 人工校验清单

## 主文档检查

- [ ] YAML front matter 存在且包含 `name`、`description`
- [ ] `name` 为 kebab-case（无空格、无中文）
- [ ] `description` ≤ 50 字
- [ ] 主文档不超过 120 行
- [ ] 不包含实现细节（详细步骤/模板正文/示例正文）
- [ ] 子文档引用使用 `@子文档名`，无路径无扩展名
- [ ] 无文件系统路径出现

## 子文档检查

- [ ] 每个子文档有 YAML front matter（`name`、`description`）
- [ ] `name` 为 kebab-case
- [ ] `description` ≤ 30 字
- [ ] 不超过 200 行
- [ ] 不含 `@引用`
- [ ] 不含路径或扩展名引用

## 目录结构检查

- [ ] 主文档为 `README.md`
- [ ] 子文档与主文档同级（无子目录）
- [ ] 技能目录名为中文
""")

# ═════════════════════════════════════════════════════════════════════════════
# 2. SCRIPTS  (init_nika_skill.py + validate_nika_skill.py)
# ═════════════════════════════════════════════════════════════════════════════

write(WORKSPACE / "scripts/init_nika_skill.py", """\
#!/usr/bin/env python3
\"\"\"
init_nika_skill.py  —  scaffold a new Nika skill directory.
Usage: python3 scripts/init_nika_skill.py "技能中文名"
\"\"\"
import sys
import os
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/init_nika_skill.py \\"技能中文名\\"")
        sys.exit(1)

    skill_name = sys.argv[1].strip()
    skill_dir = Path("skills") / skill_name

    if skill_dir.exists():
        print(f"[WARN] 目录已存在: {skill_dir}")
    else:
        skill_dir.mkdir(parents=True)

    readme = skill_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            f\"\"\"---
name: {skill_name.replace(' ', '-').lower()}
description: （请填写一句话技能描述，≤50字）
---

# {skill_name}

（请填写技能总览）

## 输入契约

| 输入项 | 文件类型 | 命名模式 | 最低要求 |
|--------|----------|----------|----------|
|        |          |          |          |

## 输出契约

### 持久交付
（请描述）

### 临时交付（屏幕输出）
（请描述）

## 子文档索引

（请用 @子文档名 引用子文档）
\"\"\",
            encoding="utf-8"
        )
        print(f"[OK] 已生成主文档: {readme}")
    else:
        print(f"[SKIP] 主文档已存在: {readme}")

    print(f"[DONE] 技能目录初始化完成: {skill_dir}")

if __name__ == "__main__":
    main()
""")

write(WORKSPACE / "scripts/validate_nika_skill.py", """\
#!/usr/bin/env python3
\"\"\"
validate_nika_skill.py  —  validate a Nika skill directory against nika-spec.
Usage: python3 scripts/validate_nika_skill.py "skills/技能中文名"
Exit 0 if all checks pass, 1 if any fail.
\"\"\"
import sys
import re
from pathlib import Path

ERRORS = []
WARNINGS = []

def err(msg): ERRORS.append(msg)
def warn(msg): WARNINGS.append(msg)

def check_yaml_frontmatter(text: str, filepath: Path):
    if not text.startswith("---"):
        err(f"{filepath}: 缺少 YAML front matter")
        return {}
    end = text.find("---", 3)
    if end == -1:
        err(f"{filepath}: YAML front matter 未闭合")
        return {}
    block = text[3:end]
    fields = {}
    for line in block.strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fields[k.strip()] = v.strip()
    return fields

def validate_main_doc(readme: Path):
    text = readme.read_text(encoding="utf-8")
    lines = text.splitlines()

    # front matter
    fields = check_yaml_frontmatter(text, readme)
    if "name" not in fields:
        err(f"{readme}: front matter 缺少 name 字段")
    else:
        if re.search(r'[\\s_A-Z]', fields["name"]) or re.search(r'[^a-z0-9\\-]', fields["name"]):
            err(f"{readme}: name 不是合法 kebab-case: {fields['name']!r}")
    if "description" not in fields:
        err(f"{readme}: front matter 缺少 description 字段")
    else:
        if len(fields["description"]) > 50:
            err(f"{readme}: description 超过 50 字: {len(fields['description'])} 字")

    # line limit
    if len(lines) > 120:
        err(f"{readme}: 主文档超过 120 行（当前 {len(lines)} 行）")

    # forbidden path/extension references in links
    forbidden_link = re.compile(r'\\[.*?\\]\\(.*?\\.(md|txt|json|yaml).*?\\)')
    for i, line in enumerate(lines, 1):
        if forbidden_link.search(line):
            err(f"{readme}:{i}: 禁止路径/扩展名引用: {line.strip()!r}")

    # sub-doc references must use @name syntax (check that @ refs exist in index section)
    at_refs = re.findall(r'@([\\w\\-\\u4e00-\\u9fff]+)', text)
    if not at_refs:
        warn(f"{readme}: 主文档中没有找到任何 @子文档名 引用")

    # no filesystem paths
    fs_path = re.compile(r'skills/|references/|scripts/')
    for i, line in enumerate(lines, 1):
        if fs_path.search(line):
            err(f"{readme}:{i}: 禁止出现文件系统路径: {line.strip()!r}")

    return at_refs

def validate_sub_doc(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    fields = check_yaml_frontmatter(text, path)
    if "name" not in fields:
        err(f"{path}: front matter 缺少 name 字段")
    else:
        if re.search(r'[\\s_A-Z]', fields["name"]) or re.search(r'[^a-z0-9\\-]', fields["name"]):
            err(f"{path}: name 不是合法 kebab-case: {fields['name']!r}")
    if "description" not in fields:
        err(f"{path}: front matter 缺少 description 字段")
    else:
        if len(fields["description"]) > 30:
            err(f"{path}: description 超过 30 字: {len(fields['description'])} 字")

    if len(lines) > 200:
        err(f"{path}: 子文档超过 200 行（当前 {len(lines)} 行）")

    # no @ refs in sub-docs
    at_refs = re.findall(r'@([\\w\\-\\u4e00-\\u9fff]+)', text)
    if at_refs:
        err(f"{path}: 子文档不得包含 @引用: {at_refs}")

    # no path/extension links
    forbidden_link = re.compile(r'\\[.*?\\]\\(.*?\\.(md|txt|json|yaml).*?\\)')
    for i, line in enumerate(lines, 1):
        if forbidden_link.search(line):
            err(f"{path}:{i}: 禁止路径/扩展名引用: {line.strip()!r}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/validate_nika_skill.py \\"skills/技能中文名\\"")
        sys.exit(1)

    skill_dir = Path(sys.argv[1])
    if not skill_dir.exists():
        print(f"[ERROR] 目录不存在: {skill_dir}")
        sys.exit(1)

    readme = skill_dir / "README.md"
    if not readme.exists():
        print(f"[ERROR] 缺少主文档: {readme}")
        sys.exit(1)

    print(f"=== 校验主文档: {readme} ===")
    at_refs = validate_main_doc(readme)

    # check sub-docs: all .md files except README.md
    sub_docs = [f for f in skill_dir.glob("*.md") if f.name != "README.md"]
    if not sub_docs:
        warn(f"{skill_dir}: 没有找到任何子文档")

    # check no subdirectories
    sub_dirs = [d for d in skill_dir.iterdir() if d.is_dir()]
    if sub_dirs:
        err(f"{skill_dir}: 技能目录内不得有子目录: {[d.name for d in sub_dirs]}")

    for sd in sub_docs:
        print(f"=== 校验子文档: {sd} ===")
        validate_sub_doc(sd)

    # check that @refs in main doc correspond to actual sub-doc files
    sub_doc_names = {f.stem for f in sub_docs}
    for ref in at_refs:
        if ref not in sub_doc_names:
            err(f"主文档引用了 @{ref}，但找不到对应子文档文件 {ref}.md")

    print()
    if WARNINGS:
        for w in WARNINGS:
            print(f"[WARN] {w}")
    if ERRORS:
        for e in ERRORS:
            print(f"[FAIL] {e}")
        print(f"\\n校验失败：{len(ERRORS)} 个错误，{len(WARNINGS)} 个警告")
        sys.exit(1)
    else:
        print(f"校验通过！（{len(WARNINGS)} 个警告）")
        sys.exit(0)

if __name__ == "__main__":
    main()
""")

# ═════════════════════════════════════════════════════════════════════════════
# 3. EXISTING EXAMPLE SKILLS  (distractors showing correct format)
# ═════════════════════════════════════════════════════════════════════════════

write(WORKSPACE / "skills/世界观设定生成/README.md", """\
---
name: worldbuilding-generator
description: 根据用户提供的世界观关键词，生成结构化的世界观设定文档
---

# 世界观设定生成

根据关键词生成完整世界观设定，输出设定文件。

## 输入契约

| 输入项 | 文件类型 | 命名模式 | 最低要求 |
|--------|----------|----------|----------|
| 关键词列表 | 笔记文件 | world-keywords.md | 至少 5 个关键词 |

## 输出契约

### 持久交付
- 文件类型：设定文件
- 命名规则：world-setting.md
- 内容结构：见 @输出模板

### 临时交付（屏幕输出）
- 摘要：已生成世界观要素 N 项
- 下一步指引：检查设定一致性

## 子文档索引

- @生成步骤 — 世界观生成的执行步骤
- @输出模板 — 设定文件内容结构
""")

write(WORKSPACE / "skills/世界观设定生成/生成步骤.md", """\
---
name: worldbuilding-steps
description: 世界观生成执行步骤
---

# 世界观生成执行步骤

## 步骤一：解析关键词

从用户提供的笔记文件中提取关键词，分类为：地理、历史、种族、魔法体系。

## 步骤二：生成各维度设定

针对每个维度展开 200-400 字描述。

## 步骤三：一致性检查

确认各维度设定无逻辑矛盾。
""")

write(WORKSPACE / "skills/世界观设定生成/输出模板.md", """\
---
name: worldbuilding-output-template
description: 世界观设定文件输出模板
---

# 世界观设定文件模板

## 世界名称

## 地理概述

## 历史脉络

## 种族与势力

## 魔法或科技体系

## 文化习俗
""")

write(WORKSPACE / "skills/角色弧光规划/README.md", """\
---
name: character-arc-planner
description: 为小说主要角色规划完整的心理成长弧光曲线
---

# 角色弧光规划

分析角色初始状态与目标状态，规划各幕的心理转折点。

## 输入契约

| 输入项 | 文件类型 | 命名模式 | 最低要求 |
|--------|----------|----------|----------|
| 角色基础设定 | 设定文件 | char-{角色名}.md | 含性格、目标、创伤 |
| 故事大纲 | 设定文件 | outline.md | 含三幕结构 |

## 输出契约

### 持久交付
- 文件类型：设定文件
- 命名规则：arc-{角色名}.md

### 临时交付（屏幕输出）
- 弧光摘要、关键转折点列表

## 子文档索引

- @弧光分析步骤 — 心理弧光分析方法
- @弧光模板 — 交付文件结构
- @示例 — 典型角色弧光案例
""")

write(WORKSPACE / "skills/角色弧光规划/弧光分析步骤.md", """\
---
name: arc-analysis-steps
description: 角色心理弧光分析步骤
---

# 角色弧光分析步骤

## 步骤一：锚定起点与终点

从角色设定文件提取：初始信念、核心创伤、故事终态。

## 步骤二：划分幕节点

按三幕结构划定：第一幕末、中点、第二幕末、高潮前的心理状态。

## 步骤三：设计转折触发器

为每个节点设计触发心理转变的外部事件。
""")

write(WORKSPACE / "skills/角色弧光规划/弧光模板.md", """\
---
name: arc-template
description: 角色弧光交付文件结构模板
---

# 角色弧光模板

## 角色名

## 起点状态（第一幕开始）

## 第一幕末转折

## 中点事件

## 第二幕末低谷

## 高潮决断

## 终态（成长结果）
""")

write(WORKSPACE / "skills/角色弧光规划/示例.md", """\
---
name: arc-examples
description: 典型角色弧光示例
---

# 典型角色弧光示例

## 示例：救赎型弧光

起点：不信任他人，独行侠。
中点：被迫与队友合作，首次动摇。
终态：接受他人，学会信任。
""")

# ═════════════════════════════════════════════════════════════════════════════
# 4. DISTRACTOR FILES
# ═════════════════════════════════════════════════════════════════════════════

write(WORKSPACE / "drafts/chapter-continuity-notes.txt", """\
章节连贯性审查草稿（废弃）

需要检查的内容：
- 人物情绪前后是否一致
- 道具是否出现/消失合理
- 时间线有无跳跃
- 配角称呼是否统一

这只是一个笔记，不是正式文档。
""")

write(WORKSPACE / "drafts/old-skill-format-example.md", """\
# 旧格式技能：章节校对（不符合Nika约束，勿用）

## 步骤
1. 读入章节
2. 检查人名
3. 输出报告

## 子文档
[详细步骤](steps/detail.md)
[模板](templates/output.md)
""")

write(WORKSPACE / "archive/legacy-skills/continuity-checker-v0.md", """\
---
name: continuity-checker-v0
description: 遗留版本，格式不符合当前规范
---

# 连贯性检查器（遗留）

这是早期版本。子文档引用方式已废弃：
- [检查清单](checklist.md)
- [示例](examples/sample.md)

请勿参考此文档的引用格式。
""")

write(WORKSPACE / "archive/legacy-skills/character-tracker-v1.md", """\
---
name: character-tracker
description: 跟踪全书角色出场记录
---

# 角色出场追踪（旧版）

旧版格式，子目录结构已不支持。
""")

write(WORKSPACE / "config/platform-config.json", """\
{
  "platform": "nika",
  "version": "2.1.0",
  "skill_root": "skills",
  "max_main_doc_lines": 120,
  "max_sub_doc_lines": 200,
  "enforce_kebab_case": true
}
""")

write(WORKSPACE / "config/editor-team.yaml", """\
team: editorial-fiction
members:
  - alice
  - bob
  - carol
workflow: chapter-by-chapter
platform_integration: nika
""")

write(WORKSPACE / "notes/project-phoenix.md", """\
# Project Phoenix 编辑规范笔记

章节连贯性审查是高频需求，目前靠人工，希望自动化。

需要审查维度：
1. 登场人物情绪连贯
2. 道具与场景前后一致
3. 时间线与季节描写匹配
4. 人物关系称呼统一

目标：在 Nika 平台上建立此技能，由 AI 辅助编辑完成审查。
""")

write(WORKSPACE / "notes/nika-onboarding.md", """\
# Nika 平台入驻笔记

- 技能目录放在 skills/ 下
- 每个技能有主文档 README.md 和若干子文档
- 引用子文档用 @子文档名（不带路径和扩展名）
- 记得跑 validate 脚本确认格式正确
""")

write(WORKSPACE / "tmp/scratch.txt", """\
临时文件，可忽略。
章节连贯性审查技能规划中...
""")

write(WORKSPACE / "tmp/broken-yaml-test.md", """\
---
name: broken test
description: 故意破坏的测试文件
""")

# ═════════════════════════════════════════════════════════════════════════════
# 5. SKILL.md in workspace root (the entry point the agent must read)
# ═════════════════════════════════════════════════════════════════════════════

write(WORKSPACE / "SKILL.md", """\
---
name: nika-skill-creator
description: Create or update Nika platform skills (main doc + sub docs) that follow Nika constraints (two-level docs, @sub-doc references, no path/extension references). Use when user asks to make a Nika skill, refactor an existing one to Nika format, or validate a Nika skill draft; also useful to output documents that can be pasted into Nika.
---

# Nika Skill Creator

本技能用于在本仓库内创建/更新符合 Nika 平台约束的技能文档，并提供可复制到 Nika 的主文档与子文档内容。

重要核心：
- 本技能生成的"目标技能文档内容"必须遵循 Nika 约束（见 @nika-spec）。

## 快速开始

1. 生成一个目标技能骨架（主文档 + 子文档占位）：

```bash
python3 scripts/init_nika_skill.py "你的目标技能中文名"
```

2. 校验目标技能是否满足 Nika 约束与本仓库约定：

```bash
python3 scripts/validate_nika_skill.py "skills/你的目标技能中文名"
```

## 工作流（创建/更新目标技能）

### 1) 需求澄清（先定边界）

收集并锁定：
- 目标技能用途（一句话）
- 典型触发语 3-5 条（用户会怎么说）
- 目标用户（作家/编辑/通用）
- 技能类型（写作类/工具类）
- 是否需要拆子文档

### 2) 输入契约（必要输入清单）

目标技能必须明确"必要输入内容、形式"：
- 每一项输入都要标注文件类型：设定文件 / 章节文件 / 笔记文件
- 推荐的文件名或命名模式
- 最低内容要求

### 3) 输入获取策略（先查找，找不到再问）

### 4) 交付物契约（持久 + 临时）

目标技能必须同时定义两类交付物：
- 持久交付：要写入哪些设定文件/章节文件
- 临时交付：屏幕输出哪些内容

### 5) 子文档拆分（渐进式加载）

目标技能的主文档只保留：
- 导航与总流程
- 输入/输出契约
- 子文档索引（用 @子文档名 引用，禁止路径或扩展名）

子文档只放可复用的细节（步骤、清单、模板、示例）。

### 6) 生成与交付（仓库落盘 + 屏幕摘要）

### 7) 校验与迭代

完成后运行：
```bash
python3 scripts/validate_nika_skill.py "skills/目标技能中文名"
```

## 参考索引

- @nika-spec — Nika 平台约束
- @main-doc-template — 主文档骨架模板
- @sub-doc-template — 子文档模板
- @validation-checklist — 人工校验清单
""")

print("Workspace scaffold complete.")
print("Files created:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")