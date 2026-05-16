#!/usr/bin/env python3
"""
Builds the sandbox workspace for the meeting-risk-radar task.
"""

import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── 1. Skill directory structure ──────────────────────────────────────────────
SKILL_BASE = os.path.join(WORKSPACE, "skills", "meeting-risk-radar")

dirs = [
    os.path.join(SKILL_BASE, "scripts"),
    os.path.join(SKILL_BASE, "resources"),
    os.path.join(SKILL_BASE, "examples"),
    os.path.join(SKILL_BASE, "tests"),
    os.path.join(WORKSPACE, "meetings", "2024-Q4", "board"),
    os.path.join(WORKSPACE, "meetings", "2024-Q4", "ops"),
    os.path.join(WORKSPACE, "meetings", "2024-Q3", "board"),
    os.path.join(WORKSPACE, "archive", "risk_reports"),
    os.path.join(WORKSPACE, "archive", "templates"),
    os.path.join(WORKSPACE, "config"),
    os.path.join(WORKSPACE, "logs"),
]
for d in dirs:
    os.makedirs(d, exist_ok=True)


# ── 2. spec.json  ─────────────────────────────────────────────────────────────
spec = {
    "version": "1.0.0",
    "description": "会议风险雷达输入规范与输出结构",
    "input_schema": {
        "type": "object",
        "required": ["meeting_title", "attendees", "expected_decisions", "agenda_items"],
        "properties": {
            "meeting_title":       {"type": "string",  "description": "会议名称"},
            "meeting_date":        {"type": "string",  "description": "会议日期 YYYY-MM-DD"},
            "attendees": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "role"],
                    "properties": {
                        "name":       {"type": "string"},
                        "role":       {"type": "string"},
                        "department": {"type": "string"}
                    }
                }
            },
            "expected_decisions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "本次会议预期要做的决策列表"
            },
            "agenda_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["title", "duration_minutes", "owner"],
                    "properties": {
                        "title":            {"type": "string"},
                        "duration_minutes": {"type": "integer"},
                        "owner":            {"type": "string"},
                        "materials_ready":  {"type": "boolean"},
                        "description":      {"type": "string"}
                    }
                }
            },
            "background_docs": {
                "type": "array",
                "items": {"type": "string"},
                "description": "已准备好的背景材料列表"
            }
        }
    },
    "output_sections": [
        "会前风险",
        "缺失材料",
        "责任模糊点",
        "建议改议程",
        "必须提前确认的问题",
        "失控预案"
    ],
    "output_format": "markdown",
    "cli": {
        "command": "python3",
        "script": "{baseDir}/scripts/run.py",
        "flags": {
            "--input":  "path to input JSON file",
            "--output": "path where the markdown report will be written"
        }
    }
}

with open(os.path.join(SKILL_BASE, "resources", "spec.json"), "w", encoding="utf-8") as f:
    json.dump(spec, f, ensure_ascii=False, indent=2)


# ── 3. template.md  ───────────────────────────────────────────────────────────
template_md = """# 会议风险雷达报告

## 会前风险
<!-- 列出高风险议题及原因 -->

## 缺失材料
<!-- 列出尚未准备好的文件、数据或审批 -->

## 责任模糊点
<!-- 列出职责不清、权限重叠或授权缺失的地方 -->

## 建议改议程
<!-- 提出对会议议程的改进建议 -->

## 必须提前确认的问题
<!-- 列出开会前需要各方确认的关键问题 -->

## 失控预案
<!-- 针对可能失控讨论点的应急预案 -->
"""

with open(os.path.join(SKILL_BASE, "resources", "template.md"), "w", encoding="utf-8") as f:
    f.write(template_md)


# ── 4. run.py  ────────────────────────────────────────────────────────────────
run_py = '''#!/usr/bin/env python3
"""
meeting-risk-radar CLI entry point.
Usage: python3 run.py --input <input.json> --output <output.md>
"""

import argparse
import json
import os
import sys


RISK_KEYWORDS = ["预算", "budget", "合规", "compliance", "裁员", "重组", "restructure",
                 "监管", "regulatory", "法律", "legal", "数据隐私", "隐私", "privacy"]


def load_input(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyse(data: dict) -> dict:
    title    = data.get("meeting_title", "未命名会议")
    date     = data.get("meeting_date", "日期未知")
    attendees = data.get("attendees", [])
    decisions = data.get("expected_decisions", [])
    agenda    = data.get("agenda_items", [])
    bg_docs   = data.get("background_docs", [])

    # ── 会前风险 ────────────────────────────────────────────────────────────
    pre_risks = []
    for item in agenda:
        desc = (item.get("description") or "").lower()
        ttl  = (item.get("title") or "").lower()
        for kw in RISK_KEYWORDS:
            if kw in desc or kw in ttl:
                pre_risks.append(
                    f"- 议题【{item['title']}】涉及高风险关键词「{kw}」，需提前进行合规审查。"
                )
                break
    if len(attendees) > 8:
        pre_risks.append(f"- 参会人数 {len(attendees)} 人，超过8人可能导致决策效率下降。")
    if not decisions:
        pre_risks.append("- 未设定预期决策项，会议目标不明确，存在议而不决风险。")
    if not pre_risks:
        pre_risks.append("- 暂未发现明显高风险议题，建议会前再次核查议程细节。")

    # ── 缺失材料 ────────────────────────────────────────────────────────────
    missing = []
    for item in agenda:
        if not item.get("materials_ready", True):
            missing.append(f"- 议题【{item['title']}】的支撑材料尚未准备好。")
    if not bg_docs:
        missing.append("- 未提供任何背景文件，建议会前分发会议简报。")
    if not missing:
        missing.append("- 所有议题材料已就绪，无明显缺失。")

    # ── 责任模糊点 ──────────────────────────────────────────────────────────
    owner_counts: dict = {}
    for item in agenda:
        owner = item.get("owner", "未指定")
        owner_counts[owner] = owner_counts.get(owner, 0) + 1
    ambiguous = []
    for item in agenda:
        if not item.get("owner") or item["owner"].strip() == "":
            ambiguous.append(f"- 议题【{item['title']}】未指定负责人。")
    roles = [a.get("role", "") for a in attendees]
    if roles.count("决策者") == 0:
        ambiguous.append("- 参会人员中未明确指定决策者角色，决策权归属不清。")
    if not ambiguous:
        ambiguous.append("- 各议题责任人已明确，暂无模糊点。")

    # ── 建议改议程 ──────────────────────────────────────────────────────────
    suggestions = []
    total_time = sum(i.get("duration_minutes", 0) for i in agenda)
    if total_time > 120:
        suggestions.append(f"- 总议程时长 {total_time} 分钟，建议精简或拆分为两场会议。")
    for item in agenda:
        if item.get("duration_minutes", 0) < 5:
            suggestions.append(f"- 议题【{item['title']}】时长不足5分钟，建议合并至其他议题或改为邮件通知。")
    if not suggestions:
        suggestions.append("- 议程安排合理，无需调整。")

    # ── 必须提前确认的问题 ──────────────────────────────────────────────────
    confirmations = []
    for d in decisions:
        confirmations.append(f"- 决策项「{d}」：请确认相关数据、审批材料及授权已到位。")
    if not confirmations:
        confirmations.append("- 请会前确认所有议题的主责人已收到会议邀请及材料。")

    # ── 失控预案 ────────────────────────────────────────────────────────────
    contingency = []
    high_risk_items = [i["title"] for i in agenda
                       if any(kw in (i.get("description") or "").lower() or
                              kw in i.get("title", "").lower()
                              for kw in RISK_KEYWORDS)]
    if high_risk_items:
        contingency.append(
            f"- 若讨论失控，主持人应及时将议题【{'、'.join(high_risk_items)}】"
            f"移至下一议程或转交专项小组离线处理。"
        )
    contingency.append("- 如出现重大分歧，暂停讨论，由主持人收集各方意见后30分钟内给出汇总。")
    contingency.append("- 若会议超时，优先保证核心决策事项完成，其余议题顺延。")

    return {
        "title":        title,
        "date":         date,
        "pre_risks":    pre_risks,
        "missing":      missing,
        "ambiguous":    ambiguous,
        "suggestions":  suggestions,
        "confirmations": confirmations,
        "contingency":  contingency,
    }


def render(result: dict) -> str:
    lines = [
        f"# 会议风险雷达报告",
        f"",
        f"**会议名称：** {result[\'title\']}",
        f"**会议日期：** {result[\'date\']}",
        f"",
        f"---",
        f"",
        f"## 会前风险",
        *result["pre_risks"],
        f"",
        f"## 缺失材料",
        *result["missing"],
        f"",
        f"## 责任模糊点",
        *result["ambiguous"],
        f"",
        f"## 建议改议程",
        *result["suggestions"],
        f"",
        f"## 必须提前确认的问题",
        *result["confirmations"],
        f"",
        f"## 失控预案",
        *result["contingency"],
        f"",
    ]
    return "\\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="会议风险雷达 CLI")
    parser.add_argument("--input",  required=True, help="输入 JSON 文件路径")
    parser.add_argument("--output", required=True, help="输出 Markdown 文件路径")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERROR] 输入文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    data   = load_input(args.input)
    result = analyse(data)
    report = render(result)

    out_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(out_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[OK] 报告已写入: {args.output}")


if __name__ == "__main__":
    main()
'''

with open(os.path.join(SKILL_BASE, "scripts", "run.py"), "w", encoding="utf-8") as f:
    f.write(run_py)


# ── 5. Example input/output (reference) ──────────────────────────────────────
example_input = {
    "meeting_title": "Q3 产品路线图评审会",
    "meeting_date": "2024-09-10",
    "attendees": [
        {"name": "张伟", "role": "决策者", "department": "产品"},
        {"name": "李娜", "role": "参与者", "department": "技术"},
        {"name": "王磊", "role": "参与者", "department": "市场"}
    ],
    "expected_decisions": ["确定Q4核心功能优先级", "批准设计规范V2"],
    "agenda_items": [
        {"title": "Q3复盘", "duration_minutes": 20, "owner": "张伟", "materials_ready": True,
         "description": "回顾Q3完成情况"},
        {"title": "Q4规划", "duration_minutes": 40, "owner": "李娜", "materials_ready": False,
         "description": "讨论Q4功能规划与资源分配"}
    ],
    "background_docs": ["Q3季报.pdf"]
}

with open(os.path.join(SKILL_BASE, "examples", "sample_input.json"), "w", encoding="utf-8") as f:
    json.dump(example_input, f, ensure_ascii=False, indent=2)


# ── 6. Smoke test  ────────────────────────────────────────────────────────────
smoke_md = """# 冒烟测试

## 测试步骤
1. 运行：`python3 {baseDir}/scripts/run.py --input {baseDir}/examples/sample_input.json --output /tmp/smoke_output.md`
2. 检查 `/tmp/smoke_output.md` 是否包含以下六个标题：
   - ## 会前风险
   - ## 缺失材料
   - ## 责任模糊点
   - ## 建议改议程
   - ## 必须提前确认的问题
   - ## 失控预案
3. 文件应为 UTF-8 编码的 Markdown 文件。

## 期望结果
输出文件存在，包含所有六个标题，无异常退出。
"""
with open(os.path.join(SKILL_BASE, "tests", "smoke-test.md"), "w", encoding="utf-8") as f:
    f.write(smoke_md)


# ── 7. DISTRACTOR FILES  ──────────────────────────────────────────────────────
# Deliberately messy, misleading files to test the agent's contextual awareness.

# Old / wrong template in archive
old_template = """# Risk Report Template (Deprecated v0.3)
## Risk Items
## Action Items
## Follow-up
"""
with open(os.path.join(WORKSPACE, "archive", "templates", "old_risk_template.md"), "w") as f:
    f.write(old_template)

# A plausible but incorrect meeting JSON (wrong schema — missing required fields)
bad_meeting = {
    "title": "Board Meeting Draft",
    "participants": ["Alice", "Bob"],
    "topics": ["Budget Review", "HR Policy"]
}
with open(os.path.join(WORKSPACE, "meetings", "2024-Q3", "board", "board_meeting_draft.json"), "w") as f:
    json.dump(bad_meeting, f, indent=2)

# Another meeting file with partial data (has meeting_title but missing attendees)
partial_meeting = {
    "meeting_title": "Q4 预算专项会议",
    "meeting_date": "2024-12-01",
    "expected_decisions": ["批准2025年度预算"],
    "agenda_items": []
}
with open(os.path.join(WORKSPACE, "meetings", "2024-Q4", "ops", "partial_meeting.json"), "w") as f:
    json.dump(partial_meeting, f, ensure_ascii=False, indent=2)

# A config file that looks relevant but isn't
config_data = {
    "tool": "meeting-risk-radar",
    "version": "0.9.9",
    "output_dir": "/tmp/reports",
    "sections": ["risks", "materials", "owners"],
    "note": "THIS IS AN OLD CONFIG — do not use"
}
with open(os.path.join(WORKSPACE, "config", "radar_config_OLD.json"), "w") as f:
    json.dump(config_data, f, indent=2)

# A log file from a previous run
with open(os.path.join(WORKSPACE, "logs", "run_2024-10-01.log"), "w") as f:
    f.write("[INFO] run.py started\n[INFO] Input: meeting.json\n[ERROR] Missing field: attendees\n[INFO] Exiting with code 1\n")

# A fake README-like note (but NOT helpful for this task)
with open(os.path.join(WORKSPACE, "archive", "risk_reports", "NOTES.txt"), "w") as f:
    f.write("Archive of risk reports from 2022-2023. Format changed in v1.0. Do not reference.\n")

# ── 8. THE ACTUAL TASK INPUT  ─────────────────────────────────────────────────
# This is the messy, real-world meeting brief the agent must process.
task_meeting = {
    "meeting_title": "FinTech 监管合规专项董事会会议",
    "meeting_date": "2024-12-15",
    "attendees": [
        {"name": "陈建国", "role": "决策者",  "department": "董事会"},
        {"name": "周晓梅", "role": "参与者",  "department": "法务合规"},
        {"name": "刘洋",   "role": "参与者",  "department": "财务"},
        {"name": "赵志远", "role": "参与者",  "department": "风险管理"},
        {"name": "孙倩",   "role": "参与者",  "department": "技术"},
        {"name": "吴鹏",   "role": "参与者",  "department": "产品"},
        {"name": "郑华",   "role": "参与者",  "department": "运营"},
        {"name": "冯丽",   "role": "参与者",  "department": "人力资源"},
        {"name": "蒋明",   "role": "参与者",  "department": "市场"},
        {"name": "韩雪",   "role": "观察者",  "department": "外部审计"}
    ],
    "expected_decisions": [
        "批准2025年监管合规路线图",
        "确定数据隐私合规整改方案",
        "授权法务部门与监管机构签署备忘录"
    ],
    "agenda_items": [
        {
            "title": "2024年监管检查结果通报",
            "duration_minutes": 20,
            "owner": "周晓梅",
            "materials_ready": False,
            "description": "汇报监管机构对公司合规状态的审查结论，涉及数据隐私与反洗钱合规两项"
        },
        {
            "title": "数据隐私整改专项",
            "duration_minutes": 35,
            "owner": "孙倩",
            "materials_ready": False,
            "description": "讨论隐私数据分级、用户同意管理及跨境数据传输合规整改方案"
        },
        {
            "title": "2025预算审批",
            "duration_minutes": 25,
            "owner": "",
            "materials_ready": False,
            "description": "审议并批准2025年度合规与技术改造预算，预算方案尚在财务审核中"
        },
        {
            "title": "监管备忘录授权",
            "duration_minutes": 15,
            "owner": "周晓梅",
            "materials_ready": True,
            "description": "授权法务负责人与银保监会代表签署合作备忘录"
        },
        {
            "title": "其他事项",
            "duration_minutes": 3,
            "owner": "陈建国",
            "materials_ready": True,
            "description": "临时动议"
        }
    ],
    "background_docs": []
}

task_input_path = os.path.join(WORKSPACE, "meetings", "2024-Q4", "board", "board_compliance_meeting.json")
with open(task_input_path, "w", encoding="utf-8") as f:
    json.dump(task_meeting, f, ensure_ascii=False, indent=2)

print(f"[OK] Workspace built. Task input: {task_input_path}")
print(f"[OK] Skill base: {SKILL_BASE}")