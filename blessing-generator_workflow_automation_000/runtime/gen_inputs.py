import os
import json
import random

random.seed(42)

BASE = "/workspace"

# ── directory skeleton ────────────────────────────────────────────────
dirs = [
    "SKILL_DIR/scripts",
    "SKILL_DIR/assets",
    "SKILL_DIR/configs",
    "campaign/requests",
    "campaign/archive",
    "campaign/templates",
    "logs",
    "exports",
    "distractor/data",
    "distractor/utils",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── realistic SKILL_DIR/scripts/generate_blessing.py mock ────────────
blessing_script = r'''#!/usr/bin/env python3
"""
Blessing generator — local mock implementation.
Accepts: --festival --target --relation --style --length
Outputs the canonical 3-version format defined in SKILL.md.
"""
import argparse
import sys
import hashlib

VALID_STYLES   = {"正式", "温情", "幽默", "文艺", "押韵"}
VALID_LENGTHS  = {"short", "medium", "long"}
VALID_RELATIONS = {"长辈", "平辈", "晚辈"}

parser = argparse.ArgumentParser()
parser.add_argument("--festival",  required=True)
parser.add_argument("--target",    required=True)
parser.add_argument("--relation",  required=True)
parser.add_argument("--style",     required=True)
parser.add_argument("--length",    required=True)
args = parser.parse_args()

errors = []
if args.style not in VALID_STYLES:
    errors.append(f"INVALID_STYLE:{args.style}")
if args.length not in VALID_LENGTHS:
    errors.append(f"INVALID_LENGTH:{args.length}")
if args.relation not in VALID_RELATIONS:
    errors.append(f"INVALID_RELATION:{args.relation}")

if errors:
    print("ERROR: " + "; ".join(errors), file=sys.stderr)
    sys.exit(1)

seed = hashlib.md5(f"{args.festival}{args.target}{args.relation}{args.style}{args.length}".encode()).hexdigest()[:6]

print(f"""🎁 版本一（正式温情）
祝{args.target}在{args.festival}里，岁月静好，一切安康。[{seed}-v1]

🎊 版本二（轻松活泼）
嘿，{args.target}！{args.festival}快乐呀，愿你天天开心！[{seed}-v2]

✨ 版本三（押韵文艺）
{args.festival}佳节好时光，祝{args.target}幸福万年长。[{seed}-v3]""")
'''

with open(os.path.join(BASE, "SKILL_DIR/scripts/generate_blessing.py"), "w", encoding="utf-8") as f:
    f.write(blessing_script)

# ── SKILL.md ───
skill_md = """\
---
name: blessing-generator
displayName: 万能祝福语生成器
version: 1.0.0
description: >
  输入被祝福人信息（称呼/辈分/近况/节日/风格），AI 生成个性化祝福语。
  覆盖全年所有节日（春节/妇女节/儿童节/光棍节/圣诞节等）和人生场合（生日/婚礼/升学等）。
author: antonia-sz
tags: [blessing, festival, holiday, greeting, social, ai]
---

# 万能祝福语生成器 🎉

## 你能做什么

帮你生成个性化、有温度的祝福语，覆盖全年所有节日和人生重要场合。

---

## 支持的节日和场合

### 🏮 中国传统节日
春节、元宵节、清明节、端午节、七夕节、中秋节、重阳节、冬至、除夕

### 🌍 现代 / 西式节日
情人节、妇女节（3.8）、愚人节、劳动节、儿童节（6.1）、父亲节、母亲节、光棍节（11.11）、圣诞节、元旦

### 🎂 人生重要时刻
生日、婚礼/结婚纪念日、宝宝满月/百天、乔迁新居、开业大吉、升学/毕业、升职加薪、康复出院、退休

### ✍️ 自定义场合
任何你想庆祝的事！

---

## 使用方式

### 快速生成

```
帮我生成一段妇女节祝福语，送给我妈妈，温情一点
```

```
帮老板写一段春节祝福，正式有格调
```

### 详细定制

```
节日：光棍节
对象：闺蜜，25岁，刚刚失恋
风格：幽默治愈
字数：100字左右
```

---

## 可配置参数

| 参数 | 选项 | 说明 |
|------|------|------|
| 对象/称呼 | 爸妈/老板/同学/甲方... | 自由填写 |
| 辈分/关系 | 长辈/平辈/晚辈 | 影响语气敬称 |
| 年龄段 | 小孩/青年/中年/老年 | 影响用词 |
| 近况 | 升学/结婚/创业... | 可选，增加个性化 |
| 节日/场合 | 见上方列表 | 必填 |
| 风格 | 正式/温情/幽默/文艺/押韵 | 默认温情 |
| 字数 | 50字内/50-150字/150字以上 | 默认中等 |

---

## 输出格式

一次生成 3 条供选择，可要求「再来几条」或「这条更幽默一点」微调。

```
🎁 版本一（正式温情）
[祝福语内容]

🎊 版本二（轻松活泼）
[祝福语内容]

✨ 版本三（押韵文艺）
[祝福语内容]
```

---

## 工具调用

```python
exec: python3 SKILL_DIR/scripts/generate_blessing.py \\
  --festival "妇女节" \\
  --target "妈妈" \\
  --relation "长辈" \\
  --style "温情" \\
  --length "medium"
```
"""

with open(os.path.join(BASE, "SKILL_DIR/SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# ── batch request file ─────────────────────────────────────────────────
batch_requests = {
    "campaign_id": "SPRING2025",
    "description": "Q1 holiday greeting card batch for CRM push",
    "requests": [
        {
            "id": "req_001",
            "occasion": "春节",
            "recipient_name": "爸爸",
            "recipient_seniority": "elder",
            "desired_tone": "formal",
            "message_size": "short"
        },
        {
            "id": "req_002",
            "occasion": "妇女节",
            "recipient_name": "同事小李",
            "recipient_seniority": "peer",
            "desired_tone": "humorous",
            "message_size": "medium"
        },
        {
            "id": "req_003",
            "occasion": "生日",
            "recipient_name": "外孙女",
            "recipient_seniority": "junior",
            "desired_tone": "poetic-rhyming",
            "message_size": "long"
        },
        {
            "id": "req_004",
            "occasion": "升职加薪",
            "recipient_name": "老板",
            "recipient_seniority": "elder",
            "desired_tone": "literary",
            "message_size": "medium"
        },
        {
            "id": "req_005",
            "occasion": "中秋节",
            "recipient_name": "奶奶",
            "recipient_seniority": "elder",
            "desired_tone": "warm",
            "message_size": "short"
        }
    ]
}

with open(os.path.join(BASE, "campaign/requests/batch_q1_2025.json"), "w", encoding="utf-8") as f:
    json.dump(batch_requests, f, ensure_ascii=False, indent=2)

# ── distractor files ──────────────────────────────────────────────────
distractors = {
    "SKILL_DIR/configs/default_style.yaml": "style: casual\nlength: 200\noutput_format: plain\n",
    "SKILL_DIR/assets/emoji_map.txt": "birthday=🎂\nfestival=🎉\nnew_year=🧧\n",
    "campaign/archive/batch_q4_2024_done.json": json.dumps({"campaign_id": "Q42024", "status": "completed"}, ensure_ascii=False),
    "campaign/templates/corporate_template.txt": "尊敬的{name}，\n值此{occasion}之际，谨致以最诚挚的祝福。\n",
    "campaign/templates/casual_template.txt": "嘿{name}！{occasion}快乐！",
    "logs/generator_run_20241201.log": "[INFO] batch completed\n[INFO] 10 blessings generated\n[WARN] 1 request had missing style field\n",
    "logs/errors_20241115.log": "ERROR req_099: INVALID_STYLE:casual\nERROR req_100: INVALID_LENGTH:200chars\n",
    "exports/previous_output_sample.txt": "祝您新春快乐，万事如意！（旧版本，仅供参考）\n",
    "distractor/data/festival_calendar.csv": "date,festival\n2025-01-01,元旦\n2025-01-29,春节\n2025-03-08,妇女节\n",
    "distractor/utils/text_cleaner.py": "def clean(text):\n    return text.strip()\n",
    "distractor/data/style_guide_v2.md": "# Old Style Guide\nUse tone=formal for corporate. DEPRECATED.\n",
}

for path, content in distractors.items():
    with open(os.path.join(BASE, path), "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")