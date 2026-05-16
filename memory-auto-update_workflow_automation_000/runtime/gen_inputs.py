import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Skill directory structure ──────────────────────────────────────────────
skill_dir = workspace / "skills" / "memory-auto-update"
scripts_dir = skill_dir / "scripts"
data_dir = skill_dir / "data"

for d in [scripts_dir, data_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ── SKILL.md ───────────────────────────────────────────────────────────────
skill_md = """---
name: memory-auto-update
description: |
  记忆自动更新 - 智能识别重要内容，自动更新记忆，再也不用担心忘记了。
---

# 记忆自动更新 Memory Auto Update

## 记忆文件格式

**标准格式（保持一致）：**

```markdown
# YYYY-MM-DD 记忆

## 今日事项

### [主题1]
- **事件：** [简要描述]
- **决策：** [重要决定]
- **待办：** [ ] 事项1 - 负责人 - 截止时间
- **链接：** [相关链接]

### [主题2]
...
```

## 功能模块

### 1. 智能识别 - 提取重要内容

| 类别 | 识别内容 | 示例 |
|------|---------|------|
| **决策** | 重要决定、选择、结论 | "我们决定用方案 A" |
| **待办** | 谁要做什么、截止时间 | "@小明 周五前完成" |
| **约定** | 时间、地点、见面 | "下周三下午3点开会" |
| **事实** | 重要信息、数据 | "预算是 10 万" |
| **偏好** | 用户的喜好、习惯 | "我喜欢用飞书" |
| **项目** | 项目启动、里程碑 | "新项目开始了" |

### 3. 三种更新模式

#### 模式1：主动模式
#### 模式2：被动模式
#### 模式3：智能混合模式（默认推荐）

### 4. 五种更新频率

| 频率选项 | 说明 |
|---------|------|
| **实时** | 重要内容立即保存 |
| **每 30 分钟** | 半实时 |
| **每 1 小时** | 低频率 |
| **手动** | 完全用户控制 |
| **对话结束** | 对话结束时总结（默认） |

## 文件说明

- `scripts/extract_memory.py` - 提取记忆内容
- `scripts/generate_summary.py` - 生成摘要
- `scripts/write_memory.py` - 写入记忆文件
- `scripts/user_settings.py` - 用户设置管理
- `data/memory_template.md` - 记忆模板
- `data/default_settings.json` - 默认设置
"""
(skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

# ── default_settings.json ─────────────────────────────────────────────────
default_settings = {
    "update_mode": "intelligent_hybrid",
    "update_frequency": "end_of_conversation",
    "reminder_style": "important_immediate_others_wait",
    "auto_extract_categories": ["decision", "todo", "appointment", "fact", "preference", "project"],
    "memory_dir": "memory",
    "date_format": "%Y-%m-%d"
}
(data_dir / "default_settings.json").write_text(
    json.dumps(default_settings, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── memory_template.md ────────────────────────────────────────────────────
memory_template = """# {date} 记忆

## 今日事项

### {topic}
- **事件：** {event}
- **决策：** {decision}
- **待办：** [ ] {todo} - {owner} - {deadline}
- **链接：** {link}
"""
(data_dir / "memory_template.md").write_text(memory_template, encoding="utf-8")

# ── user_settings.py ──────────────────────────────────────────────────────
user_settings_py = '''#!/usr/bin/env python3
"""用户设置管理脚本"""
import json
import sys
import argparse
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent.parent / "data" / "user_settings.json"
DEFAULT_FILE = Path(__file__).parent.parent / "data" / "default_settings.json"

VALID_MODES = ["proactive", "passive", "intelligent_hybrid"]
VALID_FREQUENCIES = ["realtime", "every_30min", "every_1hour", "manual", "end_of_conversation"]
VALID_REMINDER_STYLES = ["immediate", "end_of_conversation", "important_immediate_others_wait"]

def load_settings():
    if SETTINGS_FILE.exists():
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    elif DEFAULT_FILE.exists():
        return json.loads(DEFAULT_FILE.read_text(encoding="utf-8"))
    return {}

def save_settings(settings):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Settings saved to {SETTINGS_FILE}")

def show_settings(settings):
    print(json.dumps(settings, ensure_ascii=False, indent=2))

def main():
    parser = argparse.ArgumentParser(description="User Settings Manager")
    parser.add_argument("--mode", choices=VALID_MODES, help="Update mode")
    parser.add_argument("--frequency", choices=VALID_FREQUENCIES, help="Update frequency")
    parser.add_argument("--reminder", choices=VALID_REMINDER_STYLES, help="Reminder style")
    parser.add_argument("--show", action="store_true", help="Show current settings")
    parser.add_argument("--reset", action="store_true", help="Reset to defaults")
    args = parser.parse_args()

    settings = load_settings()

    if args.reset:
        if DEFAULT_FILE.exists():
            settings = json.loads(DEFAULT_FILE.read_text(encoding="utf-8"))
            save_settings(settings)
        return

    if args.show:
        show_settings(settings)
        return

    changed = False
    if args.mode:
        settings["update_mode"] = args.mode
        changed = True
    if args.frequency:
        settings["update_frequency"] = args.frequency
        changed = True
    if args.reminder:
        settings["reminder_style"] = args.reminder
        changed = True

    if changed:
        save_settings(settings)
    elif not args.show and not args.reset:
        show_settings(settings)

if __name__ == "__main__":
    main()
'''
(scripts_dir / "user_settings.py").write_text(user_settings_py, encoding="utf-8")

# ── extract_memory.py ─────────────────────────────────────────────────────
extract_memory_py = '''#!/usr/bin/env python3
"""从对话文本中提取记忆内容"""
import json
import sys
import argparse
import re
from pathlib import Path

CATEGORY_KEYWORDS = {
    "decision": ["决定", "选择", "结论", "采用", "确定", "decision", "decided", "chose"],
    "todo": ["待办", "完成", "负责", "截止", "todo", "action item", "by", "finish", "完成"],
    "appointment": ["时间", "地点", "见面", "会议", "下周", "明天", "appointment", "meeting", "schedule"],
    "fact": ["预算", "数据", "金额", "数量", "budget", "cost", "amount", "fact"],
    "preference": ["喜欢", "偏好", "习惯", "prefer", "like", "prefer"],
    "project": ["项目", "启动", "里程碑", "project", "launch", "milestone"]
}

def extract_items(text, categories=None):
    if categories is None:
        categories = list(CATEGORY_KEYWORDS.keys())
    
    results = {}
    lines = text.split("\\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        for cat in categories:
            if cat not in results:
                results[cat] = []
            for kw in CATEGORY_KEYWORDS[cat]:
                if kw.lower() in line.lower():
                    if line not in results[cat]:
                        results[cat].append(line)
                    break
    
    # Remove empty categories
    results = {k: v for k, v in results.items() if v}
    return results

def main():
    parser = argparse.ArgumentParser(description="Extract memory from conversation")
    parser.add_argument("--input", required=True, help="Input conversation file")
    parser.add_argument("--output", help="Output JSON file (default: stdout)")
    parser.add_argument("--categories", nargs="+", 
                        choices=list(CATEGORY_KEYWORDS.keys()),
                        help="Categories to extract")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")
    extracted = extract_items(text, args.categories)

    output = json.dumps(extracted, ensure_ascii=False, indent=2)
    
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"[OK] Extracted to {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()
'''
(scripts_dir / "extract_memory.py").write_text(extract_memory_py, encoding="utf-8")

# ── generate_summary.py ───────────────────────────────────────────────────
generate_summary_py = '''#!/usr/bin/env python3
"""根据提取的记忆内容生成摘要"""
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

def generate_summary(extracted_data, date_str=None, topic="今日会议"):
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    summary = {
        "date": date_str,
        "topic": topic,
        "sections": []
    }

    section = {"title": topic, "items": []}

    cat_label = {
        "decision": "决策",
        "todo": "待办",
        "appointment": "约定",
        "fact": "事实",
        "preference": "偏好",
        "project": "项目"
    }

    for cat, items in extracted_data.items():
        label = cat_label.get(cat, cat)
        for item in items:
            section["items"].append({
                "category": cat,
                "label": label,
                "content": item
            })

    summary["sections"].append(section)
    return summary

def main():
    parser = argparse.ArgumentParser(description="Generate memory summary")
    parser.add_argument("--input", required=True, help="Extracted JSON file")
    parser.add_argument("--output", help="Output summary JSON file")
    parser.add_argument("--date", help="Date string YYYY-MM-DD")
    parser.add_argument("--topic", default="今日会议", help="Main topic/theme")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    extracted = json.loads(input_path.read_text(encoding="utf-8"))
    summary = generate_summary(extracted, args.date, args.topic)

    output = json.dumps(summary, ensure_ascii=False, indent=2)
    
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"[OK] Summary written to {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()
'''
(scripts_dir / "generate_summary.py").write_text(generate_summary_py, encoding="utf-8")

# ── write_memory.py ───────────────────────────────────────────────────────
write_memory_py = '''#!/usr/bin/env python3
"""将摘要写入标准格式的记忆文件"""
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

def render_memory_file(summary):
    date = summary.get("date", datetime.now().strftime("%Y-%m-%d"))
    lines = [f"# {date} 记忆", "", "## 今日事项", ""]

    for section in summary.get("sections", []):
        title = section.get("title", "未命名")
        lines.append(f"### {title}")

        items_by_cat = {}
        for item in section.get("items", []):
            cat = item["category"]
            if cat not in items_by_cat:
                items_by_cat[cat] = []
            items_by_cat[cat].append(item["content"])

        cat_field_map = {
            "decision": "决策",
            "todo": "待办",
            "appointment": "约定",
            "fact": "事实",
            "preference": "偏好",
            "project": "项目"
        }

        rendered_cats = set()
        for cat, field in cat_field_map.items():
            if cat in items_by_cat:
                rendered_cats.add(cat)
                for content in items_by_cat[cat]:
                    if cat == "todo":
                        lines.append(f"- **{field}：** [ ] {content}")
                    else:
                        lines.append(f"- **{field}：** {content}")

        lines.append("")

    return "\\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Write memory file")
    parser.add_argument("--input", required=True, help="Summary JSON file")
    parser.add_argument("--output-dir", default="memory", help="Output directory")
    parser.add_argument("--date", help="Override date (YYYY-MM-DD)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    summary = json.loads(input_path.read_text(encoding="utf-8"))
    
    if args.date:
        summary["date"] = args.date
    
    date = summary.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{date}.md"
    content = render_memory_file(summary)
    output_file.write_text(content, encoding="utf-8")
    print(f"[OK] Memory written to {output_file}")

if __name__ == "__main__":
    main()
'''
(scripts_dir / "write_memory.py").write_text(write_memory_py, encoding="utf-8")

# ── tips.md ────────────────────────────────────────────────────────────────
tips_md = """# 使用技巧

## 常见问题

1. Q: 如何切换模式？
   A: 使用 `设置更新模式` 命令

2. Q: 记忆文件保存在哪里？
   A: 默认保存在 `memory/YYYY-MM-DD.md`

3. Q: 如何查看历史记忆？
   A: 查看 `memory/` 目录下的文件
"""
(skill_dir / "tips.md").write_text(tips_md, encoding="utf-8")

# ── _meta.json ────────────────────────────────────────────────────────────
meta = {
    "name": "memory-auto-update",
    "version": "1.2.0",
    "author": "SiVi Team",
    "created": "2024-01-01"
}
(skill_dir / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

# ── RAW MESSY INPUT: conversation log ─────────────────────────────────────
# This is a realistic meeting transcript the agent must process
# Contains content from ALL 6 categories to test comprehensive extraction
conv_dir = workspace / "inputs"
conv_dir.mkdir(exist_ok=True)

conversation_log = """产品设计周会 - 2024-03-15

[09:00] 项目经理 王磊：好，大家都到了，我们开始今天的设计评审会。首先，关于移动端改版，我们决定采用方案B，放弃原来的方案A。

[09:05] 设计师 李梅：好的。另外，用户调研显示我们的留存率目前是62%，这是关键数据。

[09:08] 项目经理 王磊：对，这个很重要。新版本上线后我们的目标预算是50万人民币，不能超过这个数字。

[09:12] 前端 张伟：我负责完成首页重构，截止时间是下周五，也就是3月22日。

[09:15] 后端 陈芳：API接口文档我周三前搞定，大家等我的通知。

[09:20] 项目经理 王磊：好。另外我们下周三，也就是3月20日下午两点，在3号会议室开下一次评审。

[09:25] 设计师 李梅：对了，我们团队的风格偏好是简洁风，不要太花哨，这个以后新页面都要遵守。

[09:28] 项目经理 王磊：新项目"星河计划"正式启动！这是我们今年最重要的里程碑。

[09:30] 项目经理 王磊：好，就这样，今天就这样，散会！
"""

(conv_dir / "meeting_2024-03-15.txt").write_text(conversation_log, encoding="utf-8")

# ── Distractor files ───────────────────────────────────────────────────────
distractor_dir = workspace / "archive"
distractor_dir.mkdir(exist_ok=True)

(distractor_dir / "old_notes.txt").write_text("旧的会议记录，2023年的内容，已归档。", encoding="utf-8")
(distractor_dir / "template_backup.md").write_text("# 旧模板\n这个模板已弃用。", encoding="utf-8")

logs_dir = workspace / "logs"
logs_dir.mkdir(exist_ok=True)
(logs_dir / "app.log").write_text("2024-03-14 INFO app started\n2024-03-14 DEBUG processing request\n", encoding="utf-8")
(logs_dir / "error.log").write_text("2024-03-13 ERROR connection timeout\n", encoding="utf-8")

config_dir = workspace / "config"
config_dir.mkdir(exist_ok=True)
(config_dir / "app.yaml").write_text("app:\n  name: workspace\n  debug: false\n", encoding="utf-8")
(config_dir / "nginx.conf").write_text("# nginx placeholder config\nserver { listen 80; }\n", encoding="utf-8")

temp_dir = workspace / "tmp"
temp_dir.mkdir(exist_ok=True)
(temp_dir / "draft_summary.txt").write_text("DRAFT - not finalized - do not use\n", encoding="utf-8")
(temp_dir / "scratch.json").write_text('{"status": "incomplete"}', encoding="utf-8")

docs_dir = workspace / "docs"
docs_dir.mkdir(exist_ok=True)
(docs_dir / "onboarding.md").write_text("# Onboarding\nWelcome to the team.\n", encoding="utf-8")
(docs_dir / "api_spec.md").write_text("# API Spec\nSee Swagger for details.\n", encoding="utf-8")
(docs_dir / "changelog.md").write_text("# Changelog\n## v1.0.0\n- Initial release\n", encoding="utf-8")

print("[gen_inputs] Workspace structure created successfully.")
print(f"[gen_inputs] Skill dir: {skill_dir}")
print(f"[gen_inputs] Conversation log: {conv_dir / 'meeting_2024-03-15.txt'}")