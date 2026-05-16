import os
import json
import random
import textwrap

random.seed(42)

# ── workspace root ──────────────────────────────────────────────────────────
WS = "/workspace"

# ── skill base dir ──────────────────────────────────────────────────────────
BASE = os.path.join(WS, "skills", "manufacturing-shift-handoff")

dirs = [
    os.path.join(BASE, "scripts"),
    os.path.join(BASE, "resources"),
    os.path.join(BASE, "examples"),
    os.path.join(BASE, "tests"),
    os.path.join(WS, "plant_data", "raw_logs"),
    os.path.join(WS, "plant_data", "archive"),
    os.path.join(WS, "plant_data", "maintenance_records"),
    os.path.join(WS, "plant_data", "quality_reports"),
    os.path.join(WS, "plant_data", "hr"),
    os.path.join(WS, "reports", "completed"),
    os.path.join(WS, "reports", "pending"),
    os.path.join(WS, "config"),
    os.path.join(WS, "tmp"),
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── spec.json ────────────────────────────────────────────────────────────────
spec = {
    "version": "1.0.0",
    "output_format": "markdown",
    "required_sections": [
        "班次摘要",
        "设备状态",
        "异常与处置",
        "待处理事项",
        "安全提醒",
        "下班次重点"
    ],
    "section_order": "strict",
    "missing_info_policy": "list_as_pending_confirmation",
    "pending_confirmation_label": "待确认项",
    "safety_omission_policy": "never_omit",
    "draft_label": "【可审阅草案】",
    "executable_label": "【可执行清单】",
    "fields": {
        "班次摘要": ["班次时间", "班组长", "在岗人数", "生产目标", "实际完成"],
        "设备状态": ["设备编号", "设备名称", "运行状态", "最近保养时间"],
        "异常与处置": ["异常编号", "发生时间", "描述", "处置措施", "当前状态"],
        "待处理事项": ["事项描述", "负责人", "期望完成时间"],
        "安全提醒": ["提醒内容"],
        "下班次重点": ["重点事项"]
    }
}
with open(os.path.join(BASE, "resources", "spec.json"), "w", encoding="utf-8") as f:
    json.dump(spec, f, ensure_ascii=False, indent=2)

# ── template.md ──────────────────────────────────────────────────────────────
template_md = textwrap.dedent("""\
# 班次交接摘要

> 状态：{{draft_label}}

---

## 班次摘要

| 字段 | 内容 |
|------|------|
| 班次时间 | {{shift_time}} |
| 班组长 | {{shift_leader}} |
| 在岗人数 | {{headcount}} |
| 生产目标 | {{production_target}} |
| 实际完成 | {{actual_output}} |

---

## 设备状态

{% for eq in equipment %}
| 设备编号 | {{eq.id}} |
| 设备名称 | {{eq.name}} |
| 运行状态 | {{eq.status}} |
| 最近保养时间 | {{eq.last_maintenance}} |
{% endfor %}

---

## 异常与处置

{% for anomaly in anomalies %}
- **[{{anomaly.id}}]** {{anomaly.time}} | {{anomaly.description}} | 处置：{{anomaly.action}} | 状态：{{anomaly.current_status}}
{% endfor %}

---

## 待处理事项

{% for item in pending_items %}
- [ ] {{item.description}}（负责人：{{item.owner}}，期望完成：{{item.due}}）
{% endfor %}

---

## 安全提醒

{% for s in safety %}
- ⚠️ {{s}}
{% endfor %}

---

## 下班次重点

{% for r in next_shift_focus %}
- {{r}}
{% endfor %}

---

## 待确认项

{% for q in pending_confirmation %}
- ❓ {{q}}
{% endfor %}
""")
with open(os.path.join(BASE, "resources", "template.md"), "w", encoding="utf-8") as f:
    f.write(template_md)

# ── run.py  (the actual processing script) ───────────────────────────────────
run_py = textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"
Manufacturing Shift Handoff Processor
Usage: python3 run.py --input <input_file> --output <output_file>
\"\"\"
import argparse, json, os, sys, re
from pathlib import Path

SPEC_PATH = Path(__file__).parent.parent / "resources" / "spec.json"
TEMPLATE_PATH = Path(__file__).parent.parent / "resources" / "template.md"

def load_spec():
    with open(SPEC_PATH, encoding="utf-8") as f:
        return json.load(f)

def parse_input(text):
    \"\"\"
    Parse a semi-structured shift log text into structured data.
    Handles missing fields by recording them as pending confirmations.
    \"\"\"
    data = {
        "shift_time": None,
        "shift_leader": None,
        "headcount": None,
        "production_target": None,
        "actual_output": None,
        "equipment": [],
        "anomalies": [],
        "pending_items": [],
        "safety": [],
        "next_shift_focus": [],
        "pending_confirmation": []
    }

    # --- shift summary ---
    m = re.search(r"班次时间[：:]\s*(.+)", text)
    data["shift_time"] = m.group(1).strip() if m else None

    m = re.search(r"班组长[：:]\s*(.+)", text)
    data["shift_leader"] = m.group(1).strip() if m else None

    m = re.search(r"在岗人数[：:]\s*(.+)", text)
    data["headcount"] = m.group(1).strip() if m else None

    m = re.search(r"生产目标[：:]\s*(.+)", text)
    data["production_target"] = m.group(1).strip() if m else None

    m = re.search(r"实际完成[：:]\s*(.+)", text)
    data["actual_output"] = m.group(1).strip() if m else None

    # --- equipment ---
    eq_blocks = re.findall(
        r"设备编号[：:]\s*(.+?)[\\n\\r].*?设备名称[：:]\s*(.+?)[\\n\\r].*?运行状态[：:]\s*(.+?)[\\n\\r](?:.*?最近保养[：:]\s*(.+?))?[\\n\\r]",
        text, re.DOTALL)
    for b in eq_blocks:
        data["equipment"].append({
            "id": b[0].strip(),
            "name": b[1].strip(),
            "status": b[2].strip(),
            "last_maintenance": b[3].strip() if b[3] else "待确认"
        })

    # fallback: try simpler equipment line parsing
    if not data["equipment"]:
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            if re.search(r"设备编号", lines[i]):
                eq = {"id": "", "name": "", "status": "", "last_maintenance": "待确认"}
                m2 = re.search(r"设备编号[：:]\s*(.+)", lines[i])
                if m2: eq["id"] = m2.group(1).strip()
                if i+1 < len(lines):
                    m2 = re.search(r"设备名称[：:]\s*(.+)", lines[i+1])
                    if m2: eq["name"] = m2.group(1).strip()
                if i+2 < len(lines):
                    m2 = re.search(r"运行状态[：:]\s*(.+)", lines[i+2])
                    if m2: eq["status"] = m2.group(1).strip()
                if i+3 < len(lines):
                    m2 = re.search(r"最近保养[：:]\s*(.+)", lines[i+3])
                    if m2: eq["last_maintenance"] = m2.group(1).strip()
                data["equipment"].append(eq)
                i += 4
            else:
                i += 1

    # --- anomalies ---
    anomaly_blocks = re.findall(
        r"异常编号[：:]\s*(.+?)\n.*?发生时间[：:]\s*(.+?)\n.*?描述[：:]\s*(.+?)\n(?:.*?处置[：:]\s*(.+?)\n)?(?:.*?当前状态[：:]\s*(.+?))?(?:\n|$)",
        text, re.DOTALL)
    for b in anomaly_blocks:
        data["anomalies"].append({
            "id": b[0].strip(),
            "time": b[1].strip(),
            "description": b[2].strip(),
            "action": b[3].strip() if b[3] else "待确认",
            "current_status": b[4].strip() if b[4] else "待确认"
        })

    # fallback anomaly parsing
    if not data["anomalies"]:
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            if re.search(r"异常编号", lines[i]):
                an = {"id": "", "time": "", "description": "", "action": "待确认", "current_status": "待确认"}
                m2 = re.search(r"异常编号[：:]\s*(.+)", lines[i])
                if m2: an["id"] = m2.group(1).strip()
                if i+1 < len(lines):
                    m2 = re.search(r"发生时间[：:]\s*(.+)", lines[i+1])
                    if m2: an["time"] = m2.group(1).strip()
                if i+2 < len(lines):
                    m2 = re.search(r"描述[：:]\s*(.+)", lines[i+2])
                    if m2: an["description"] = m2.group(1).strip()
                if i+3 < len(lines):
                    m2 = re.search(r"处置[：:]\s*(.+)", lines[i+3])
                    if m2: an["action"] = m2.group(1).strip()
                if i+4 < len(lines):
                    m2 = re.search(r"当前状态[：:]\s*(.+)", lines[i+4])
                    if m2: an["current_status"] = m2.group(1).strip()
                data["anomalies"].append(an)
                i += 5
            else:
                i += 1

    # --- pending items ---
    lines = text.splitlines()
    for line in lines:
        if re.search(r"待处理|待办|action item", line, re.IGNORECASE):
            m2 = re.search(r"[：:]\s*(.+)", line)
            if m2:
                data["pending_items"].append({
                    "description": m2.group(1).strip(),
                    "owner": "待确认",
                    "due": "待确认"
                })

    # parse structured pending items
    i = 0
    while i < len(lines):
        if re.search(r"^[\-\*]?\s*事项描述[：:]", lines[i]):
            item = {"description": "", "owner": "待确认", "due": "待确认"}
            m2 = re.search(r"事项描述[：:]\s*(.+)", lines[i])
            if m2: item["description"] = m2.group(1).strip()
            if i+1 < len(lines):
                m2 = re.search(r"负责人[：:]\s*(.+)", lines[i+1])
                if m2: item["owner"] = m2.group(1).strip()
            if i+2 < len(lines):
                m2 = re.search(r"期望完成[：:]\s*(.+)", lines[i+2])
                if m2: item["due"] = m2.group(1).strip()
            data["pending_items"].append(item)
            i += 3
        else:
            i += 1

    # --- safety ---
    in_safety = False
    for line in lines:
        if re.search(r"安全提醒|安全注意|safety", line, re.IGNORECASE):
            in_safety = True
            continue
        if in_safety:
            if re.search(r"^##|^---", line):
                in_safety = False
            elif line.strip().startswith("-") or line.strip().startswith("*"):
                data["safety"].append(line.strip().lstrip("-*").strip())
            elif line.strip():
                data["safety"].append(line.strip())

    # --- next shift focus ---
    in_next = False
    for line in lines:
        if re.search(r"下班次重点|下班次|next shift", line, re.IGNORECASE):
            in_next = True
            continue
        if in_next:
            if re.search(r"^##|^---", line):
                in_next = False
            elif line.strip().startswith("-") or line.strip().startswith("*"):
                data["next_shift_focus"].append(line.strip().lstrip("-*").strip())
            elif line.strip():
                data["next_shift_focus"].append(line.strip())

    # --- pending confirmations based on missing fields ---
    spec = load_spec()
    if not data["shift_time"]:   data["pending_confirmation"].append("班次时间未提供")
    if not data["shift_leader"]: data["pending_confirmation"].append("班组长姓名未提供")
    if not data["headcount"]:    data["pending_confirmation"].append("在岗人数未提供")
    if not data["production_target"]: data["pending_confirmation"].append("生产目标未提供")
    if not data["actual_output"]:     data["pending_confirmation"].append("实际完成数量未提供")
    for eq in data["equipment"]:
        if eq["last_maintenance"] == "待确认":
            data["pending_confirmation"].append(f"设备 {eq['id']} 的最近保养时间未提供")
    for an in data["anomalies"]:
        if an["action"] == "待确认":
            data["pending_confirmation"].append(f"异常 {an['id']} 的处置措施未提供")
        if an["current_status"] == "待确认":
            data["pending_confirmation"].append(f"异常 {an['id']} 的当前状态未提供")

    return data

def render_output(data, spec):
    lines = []
    lines.append("# 班次交接摘要")
    lines.append("")
    lines.append(f"> 状态：{spec['draft_label']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. 班次摘要
    lines.append("## 班次摘要")
    lines.append("")
    lines.append("| 字段 | 内容 |")
    lines.append("|------|------|")
    lines.append(f"| 班次时间 | {data['shift_time'] or '待确认'} |")
    lines.append(f"| 班组长 | {data['shift_leader'] or '待确认'} |")
    lines.append(f"| 在岗人数 | {data['headcount'] or '待确认'} |")
    lines.append(f"| 生产目标 | {data['production_target'] or '待确认'} |")
    lines.append(f"| 实际完成 | {data['actual_output'] or '待确认'} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 2. 设备状态
    lines.append("## 设备状态")
    lines.append("")
    if data["equipment"]:
        for eq in data["equipment"]:
            lines.append("| 字段 | 内容 |")
            lines.append("|------|------|")
            lines.append(f"| 设备编号 | {eq['id']} |")
            lines.append(f"| 设备名称 | {eq['name']} |")
            lines.append(f"| 运行状态 | {eq['status']} |")
            lines.append(f"| 最近保养时间 | {eq['last_maintenance']} |")
            lines.append("")
    else:
        lines.append("（无设备状态信息，请确认）")
        lines.append("")
    lines.append("---")
    lines.append("")

    # 3. 异常与处置
    lines.append("## 异常与处置")
    lines.append("")
    if data["anomalies"]:
        for an in data["anomalies"]:
            lines.append(f"- **[{an['id']}]** {an['time']} | {an['description']} | 处置：{an['action']} | 状态：{an['current_status']}")
    else:
        lines.append("（本班次无记录异常）")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 4. 待处理事项
    lines.append("## 待处理事项")
    lines.append("")
    if data["pending_items"]:
        for item in data["pending_items"]:
            lines.append(f"- [ ] {item['description']}（负责人：{item['owner']}，期望完成：{item['due']}）")
    else:
        lines.append("（无待处理事项）")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 5. 安全提醒
    lines.append("## 安全提醒")
    lines.append("")
    if data["safety"]:
        for s in data["safety"]:
            lines.append(f"- ⚠️ {s}")
    else:
        lines.append("- ⚠️ （未提供安全提醒，请班组长确认后补充）")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 6. 下班次重点
    lines.append("## 下班次重点")
    lines.append("")
    if data["next_shift_focus"]:
        for r in data["next_shift_focus"]:
            lines.append(f"- {r}")
    else:
        lines.append("（待确认）")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 待确认项
    lines.append("## 待确认项")
    lines.append("")
    if data["pending_confirmation"]:
        for q in data["pending_confirmation"]:
            lines.append(f"- ❓ {q}")
    else:
        lines.append("（无待确认项）")
    lines.append("")

    return "\\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        text = f.read()

    spec = load_spec()
    data = parse_input(text)
    result = render_output(data, spec)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"[run.py] 交接摘要已写入: {args.output}")

if __name__ == "__main__":
    main()
""")
with open(os.path.join(BASE, "scripts", "run.py"), "w", encoding="utf-8") as f:
    f.write(run_py)

# ── smoke-test.md ────────────────────────────────────────────────────────────
smoke_test = textwrap.dedent("""\
# Smoke Test

## 测试目标
验证 run.py 能正常读取输入文件并生成包含6个标准章节的交接摘要。

## 运行方式
```
python3 scripts/run.py --input tests/sample_input.txt --output /tmp/smoke_output.md
```

## 通过条件
- 输出文件存在
- 包含所有6个必需章节
- 缺失字段标注为"待确认"
""")
with open(os.path.join(BASE, "tests", "smoke-test.md"), "w", encoding="utf-8") as f:
    f.write(smoke_test)

# ── example input ─────────────────────────────────────────────────────────────
example_input = textwrap.dedent("""\
班次时间：2024-03-15 08:00 - 16:00
班组长：王建国
在岗人数：12
生产目标：800件
实际完成：762件

设备编号：PRS-001
设备名称：冲压机A
运行状态：正常
最近保养：2024-03-10

设备编号：PRS-002
设备名称：冲压机B
运行状态：异常停机
最近保养：2024-02-28

异常编号：ANO-2024-031501
发生时间：10:30
描述：PRS-002液压油泄漏
处置：已停机隔离，通知维修班
当前状态：维修中

事项描述：更换PRS-002液压密封件
负责人：李维修
期望完成：2024-03-15 18:00

安全提醒
- 液压油泄漏区域已拉警戒线，进入需穿防滑鞋
- PRS-002旁禁止明火

下班次重点
- 跟进PRS-002维修进度
- 确认PRS-001模具更换计划
""")
with open(os.path.join(BASE, "examples", "example_input.txt"), "w", encoding="utf-8") as f:
    f.write(example_input)

# ── example output ────────────────────────────────────────────────────────────
example_output = textwrap.dedent("""\
# 班次交接摘要

> 状态：【可审阅草案】

---

## 班次摘要

| 字段 | 内容 |
|------|------|
| 班次时间 | 2024-03-15 08:00 - 16:00 |
| 班组长 | 王建国 |
| 在岗人数 | 12 |
| 生产目标 | 800件 |
| 实际完成 | 762件 |

---

## 设备状态

... (see template.md for full structure)

---

## 异常与处置
...
## 待处理事项
...
## 安全提醒
...
## 下班次重点
...
## 待确认项
...
""")
with open(os.path.join(BASE, "examples", "example_output.md"), "w", encoding="utf-8") as f:
    f.write(example_output)

# ── THE ACTUAL MESSY INPUT FILE THE AGENT MUST PROCESS ───────────────────────
messy_input = textwrap.dedent("""\
【夜班交接原始记录 - 汽车冲压车间 N班】
记录时间：2024-06-18 23:55

班次时间：2024-06-18 22:00 至 2024-06-19 06:00
班组长：赵磊
在岗人数：9

生产目标：600件（A柱左右各300）
实际完成：571件  ← 29件未完成，原因见异常记录

=== 设备状态 ===

设备编号：STM-101
设备名称：伺服冲床1号
运行状态：正常运行
最近保养：2024-06-12

设备编号：STM-102
设备名称：伺服冲床2号
运行状态：降速运行（75%）
（最近保养时间不详，需查台账）

设备编号：ROB-005
设备名称：上料机器人5号
运行状态：E-STOP报警停机
最近保养：2024-05-30

=== 异常记录 ===

异常编号：ERR-240619-001
发生时间：00:47
描述：ROB-005 关节3轴位置偏差超限，触发E-STOP
处置：已通知自动化班紧急响应，复位尝试失败2次
当前状态：停机待修，自动化班预计06:30到场

异常编号：ERR-240619-002
发生时间：03:12
描述：STM-102 润滑系统低压警告，已手动补油
（处置后是否彻底解决：未知，建议白班跟进）

=== 待办 ===

事项描述：ROB-005 关节3轴检修及回零操作
负责人：自动化班（班长：陈工）
期望完成：2024-06-19 08:00前

事项描述：STM-102 润滑系统全面检查
负责人：（待指定）
期望完成：白班内完成

事项描述：补录29件缺口的生产计划追单
负责人：生产调度
期望完成：2024-06-19 07:30前

=== 安全提醒 ===
- ROB-005安全围栏已上锁，钥匙由班长保管，未经授权禁止入内
- STM-102补油操作已按SOP执行，油桶已移回指定储存位
- 夜班期间地面有少量冷却液，清洁班已通知，白班开始前需确认清洁完成

=== 下班次重点 ===
- ROB-005复机时必须进行完整安全功能验证（STO/SLS），不可跳过
- 追认STM-102最近保养台账，确认保养状态
- 跟进29件缺口补产
- 检查ROB-005 E-STOP触发后的安全回路日志
""")
messy_input_path = os.path.join(WS, "plant_data", "raw_logs", "night_shift_20240619.txt")
with open(messy_input_path, "w", encoding="utf-8") as f:
    f.write(messy_input)

# ── distractor files ──────────────────────────────────────────────────────────
distractor_files = {
    os.path.join(WS, "plant_data", "archive", "shift_20240601.txt"):
        "班次时间：2024-06-01 06:00-14:00\n班组长：刘明\n（已归档，请勿修改）",
    os.path.join(WS, "plant_data", "archive", "shift_20240602.txt"):
        "班次时间：2024-06-02 14:00-22:00\n班组长：孙华\n（已归档）",
    os.path.join(WS, "plant_data", "maintenance_records", "STM-101_log.csv"):
        "date,type,technician\n2024-06-12,定期保养,张工\n2024-03-10,定期保养,张工",
    os.path.join(WS, "plant_data", "maintenance_records", "ROB-005_log.csv"):
        "date,type,technician\n2024-05-30,月度检查,陈工\n2024-02-28,季度保养,陈工",
    os.path.join(WS, "plant_data", "quality_reports", "qc_june.xlsx"):
        "BINARY_PLACEHOLDER_NOT_REAL_XLSX",
    os.path.join(WS, "plant_data", "quality_reports", "defect_rate_may.txt"):
        "五月缺陷率：0.34%\n主要问题：毛刺、尺寸偏差",
    os.path.join(WS, "plant_data", "hr", "headcount_june.txt"):
        "六月在编人数：47\n夜班固定编制：9\n白班固定编制：14",
    os.path.join(WS, "reports", "completed", "morning_shift_20240618.md"):
        "# 白班交接摘要\n已完成，归档。",
    os.path.join(WS, "reports", "pending", "PLACEHOLDER.txt"):
        "此目录用于存放待审阅交接报告",
    os.path.join(WS, "config", "plant_config.json"):
        json.dumps({"plant_id": "FAC-SZ-03", "lines": ["STAMP-A", "STAMP-B"], "timezone": "Asia/Shanghai"}, ensure_ascii=False, indent=2),
    os.path.join(WS, "tmp", "old_draft.md"):
        "# 旧版草案\n（请勿使用，版本已过期）",
    os.path.join(WS, "config", "notification_list.txt"):
        "白班班组长：王建国\n生产主管：李总\n维修主管：赵工",
}
for path, content in distractor_files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ Workspace generated successfully.")
print(f"   Skill base dir : {BASE}")
print(f"   Messy input    : {messy_input_path}")