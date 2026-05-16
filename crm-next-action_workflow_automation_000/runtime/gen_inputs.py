import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Skill directory structure ──────────────────────────────────────────────
skill_dir = WORKSPACE / "skills" / "crm-next-action"
for d in ["scripts", "resources", "examples", "tests", "archive", "config"]:
    (skill_dir / d).mkdir(parents=True, exist_ok=True)

# ── 2. spec.json  (the proprietary rule engine the agent must read) ──────────
spec = {
    "version": "1.0.0",
    "priority_rules": {
        "high": {
            "conditions": [
                "deal_value >= 100000",
                "stage in ['Negotiation', 'Proposal Sent', 'Contract Review']"
            ],
            "label": "P1-紧急"
        },
        "medium": {
            "conditions": [
                "deal_value >= 30000",
                "stage in ['Discovery', 'Demo Scheduled', 'Qualified']"
            ],
            "label": "P2-跟进"
        },
        "low": {
            "conditions": [
                "deal_value < 30000"
            ],
            "label": "P3-观望"
        }
    },
    "required_fields": ["opportunity_id", "company", "deal_value", "stage", "owner", "last_interaction"],
    "missing_field_policy": "list_as_待确认项",
    "output_sections": [
        "机会摘要",
        "下一步动作",
        "行动理由",
        "不推进原因",
        "风险与阻塞",
        "优先级"
    ],
    "no_advance_trigger_keywords": ["budget freeze", "no response", "competitor selected", "internal hold", "lost contact"],
    "draft_mode": True,
    "language": "zh-CN"
}

(skill_dir / "resources" / "spec.json").write_text(
    json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── 3. template.md ────────────────────────────────────────────────────────────
template_md = textwrap.dedent("""\
# CRM 下一步动作 — 可审阅草案

> 生成时间：{{timestamp}}
> 输入文件：{{input_file}}

---

{% for opp in opportunities %}
## 机会：{{opp.opportunity_id}} — {{opp.company}}

### 机会摘要
{{opp.summary}}

### 下一步动作
{{opp.next_action}}

### 行动理由
{{opp.rationale}}

### 不推进原因
{{opp.no_advance_reason}}

### 风险与阻塞
{{opp.risks}}

### 优先级
{{opp.priority}}

{% if opp.pending_items %}
### 待确认项
{% for item in opp.pending_items %}
- [ ] {{item}}
{% endfor %}
{% endif %}

---
{% endfor %}
""")

(skill_dir / "resources" / "template.md").write_text(template_md, encoding="utf-8")

# ── 4. run.py  (the execution engine) ─────────────────────────────────────────
run_py = textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"
CRM Next-Action Generator — run.py
Usage:
    python3 run.py --input <input_json_or_csv> --output <output_md>
\"\"\"

import argparse
import json
import csv
import sys
import io
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR   = SCRIPT_DIR.parent
SPEC_PATH  = BASE_DIR / "resources" / "spec.json"

NO_ADVANCE_KEYWORDS = [
    "budget freeze", "no response", "competitor selected",
    "internal hold", "lost contact"
]

def load_spec():
    with open(SPEC_PATH, encoding="utf-8") as f:
        return json.load(f)

def load_input(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        if isinstance(data, dict) and "opportunities" in data:
            return data["opportunities"]
        if isinstance(data, list):
            return data
        raise ValueError("JSON must be list or {opportunities: [...]}")
    elif path.suffix.lower() == ".csv":
        reader = csv.DictReader(io.StringIO(text))
        return [row for row in reader]
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

def detect_priority(opp: dict, spec: dict) -> str:
    try:
        val = float(opp.get("deal_value", 0))
    except (ValueError, TypeError):
        val = 0
    stage = opp.get("stage", "")
    rules = spec["priority_rules"]
    high_stages = ["Negotiation", "Proposal Sent", "Contract Review"]
    medium_stages = ["Discovery", "Demo Scheduled", "Qualified"]
    if val >= 100000 and stage in high_stages:
        return rules["high"]["label"]
    if val >= 30000 and stage in medium_stages:
        return rules["medium"]["label"]
    return rules["low"]["label"]

def detect_no_advance(opp: dict) -> str:
    text_blob = " ".join(str(v).lower() for v in opp.values())
    hits = [kw for kw in NO_ADVANCE_KEYWORDS if kw in text_blob]
    if hits:
        return f"检测到以下信号：{', '.join(hits)}。建议暂缓推进，待客户侧明确意向后再跟进。"
    return "暂无明确不推进信号，继续推进。"

def find_missing_fields(opp: dict, required: list) -> list:
    missing = []
    for field in required:
        v = opp.get(field, "")
        if v is None or str(v).strip() == "" or str(v).strip().lower() == "n/a":
            missing.append(f"缺少字段：{field}")
    return missing

def build_summary(opp: dict) -> str:
    company = opp.get("company", "未知公司")
    stage   = opp.get("stage", "未知阶段")
    val     = opp.get("deal_value", "未知金额")
    owner   = opp.get("owner", "未知负责人")
    notes   = opp.get("notes", "")
    return (
        f"公司：{company}｜阶段：{stage}｜预估金额：{val}｜负责人：{owner}"
        + (f"｜备注：{notes}" if notes else "")
    )

def build_next_action(opp: dict, missing: list) -> str:
    if opp.get("stage", "") in ["Negotiation", "Contract Review"]:
        return "安排合同条款对齐会议，确认决策链关键人签字意愿。"
    if opp.get("stage", "") == "Proposal Sent":
        return "发送跟进邮件确认提案反馈，询问是否需要补充技术演示。"
    if opp.get("stage", "") in ["Demo Scheduled", "Discovery", "Qualified"]:
        return "完成需求调研收集，准备定制化演示材料，安排 Demo 时间。"
    if missing:
        return "补全待确认项后，制定具体跟进方案。"
    return "重新评估机会状态，与客户确认当前需求优先级。"

def build_rationale(opp: dict) -> str:
    val = 0
    try:
        val = float(opp.get("deal_value", 0))
    except (ValueError, TypeError):
        pass
    stage = opp.get("stage", "")
    if val >= 100000:
        return f"该机会预估金额 {opp.get('deal_value')} 元，属高价值标的，优先资源投入可显著提升本季度 ARR。"
    if stage in ["Negotiation", "Contract Review"]:
        return "已进入决策阶段，推进摩擦成本低，是本周期最值得跟进的机会之一。"
    return f"当前处于 {stage} 阶段，关键节点推进有助于缩短销售周期。"

def build_risks(opp: dict, missing: list) -> str:
    risks = []
    if missing:
        risks.append("关键信息缺失，可能导致跟进策略偏差。")
    notes_lower = opp.get("notes", "").lower()
    if "competitor" in notes_lower or "竞品" in notes_lower:
        risks.append("客户已与竞品接触，需强化差异化价值主张。")
    if "delay" in notes_lower or "延期" in notes_lower:
        risks.append("客户侧决策周期可能延长，关注预算审批节点。")
    if not risks:
        risks.append("暂无明显阻塞，维持正常推进节奏。")
    return "；".join(risks)

def render_opportunity(opp: dict, spec: dict) -> str:
    required = spec["required_fields"]
    missing  = find_missing_fields(opp, required)
    opp_id   = opp.get("opportunity_id", "UNKNOWN")
    company  = opp.get("company", "未知")
    summary     = build_summary(opp)
    next_action = build_next_action(opp, missing)
    rationale   = build_rationale(opp)
    no_advance  = detect_no_advance(opp)
    risks       = build_risks(opp, missing)
    priority    = detect_priority(opp, spec)

    lines = [
        f"## 机会：{opp_id} — {company}",
        "",
        "### 机会摘要",
        summary,
        "",
        "### 下一步动作",
        next_action,
        "",
        "### 行动理由",
        rationale,
        "",
        "### 不推进原因",
        no_advance,
        "",
        "### 风险与阻塞",
        risks,
        "",
        "### 优先级",
        priority,
    ]

    if missing:
        lines += ["", "### 待确认项"]
        for item in missing:
            lines.append(f"- [ ] {item}")

    lines += ["", "---"]
    return "\\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="CRM Next-Action Generator")
    parser.add_argument("--input",  required=True, help="Input JSON or CSV file")
    parser.add_argument("--output", required=True, help="Output Markdown file")
    args = parser.parse_args()

    input_path  = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    spec = load_spec()
    opportunities = load_input(input_path)

    header = [
        "# CRM 下一步动作 — 可审阅草案",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 输入文件：{input_path.name}",
        f"> 机会总数：{len(opportunities)}",
        "",
        "---",
        "",
    ]

    sections = []
    for opp in opportunities:
        sections.append(render_opportunity(opp, spec))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\\n".join(header + sections), encoding="utf-8")
    print(f"[run.py] Done. Output written to: {output_path}")

if __name__ == "__main__":
    main()
""")

(skill_dir / "scripts" / "run.py").write_text(run_py, encoding="utf-8")

# ── 5. examples/ ─────────────────────────────────────────────────────────────
example_input = {
    "opportunities": [
        {
            "opportunity_id": "OPP-DEMO-001",
            "company": "示例科技",
            "deal_value": 80000,
            "stage": "Demo Scheduled",
            "owner": "张三",
            "last_interaction": "2024-11-15",
            "notes": "客户对产品感兴趣，需要定制演示"
        }
    ]
}
(skill_dir / "examples" / "sample_input.json").write_text(
    json.dumps(example_input, ensure_ascii=False, indent=2), encoding="utf-8"
)

example_output = textwrap.dedent("""\
# CRM 下一步动作 — 可审阅草案

> 生成时间：2024-11-20 09:00:00
> 输入文件：sample_input.json
> 机会总数：1

---

## 机会：OPP-DEMO-001 — 示例科技

### 机会摘要
公司：示例科技｜阶段：Demo Scheduled｜预估金额：80000｜负责人：张三｜备注：客户对产品感兴趣，需要定制演示

### 下一步动作
完成需求调研收集，准备定制化演示材料，安排 Demo 时间。

### 行动理由
当前处于 Demo Scheduled 阶段，关键节点推进有助于缩短销售周期。

### 不推进原因
暂无明确不推进信号，继续推进。

### 风险与阻塞
暂无明显阻塞，维持正常推进节奏。

### 优先级
P2-跟进

---
""")
(skill_dir / "examples" / "sample_output.md").write_text(example_output, encoding="utf-8")

# ── 6. smoke-test.md ──────────────────────────────────────────────────────────
smoke_test = textwrap.dedent("""\
# Smoke Test

## 测试步骤
1. python3 scripts/run.py --input examples/sample_input.json --output /tmp/smoke_out.md
2. 检查 /tmp/smoke_out.md 包含 "机会摘要"、"下一步动作"、"优先级"

## 预期结果
- 输出文件存在
- 包含 6 个标准章节
- OPP-DEMO-001 优先级为 P2-跟进
""")
(skill_dir / "tests" / "smoke-test.md").write_text(smoke_test, encoding="utf-8")

# ── 7. Distractor files ───────────────────────────────────────────────────────
distractors = {
    "archive/q3_pipeline_dump.csv": (
        "opportunity_id,company,deal_value,stage,owner,last_interaction\n"
        "OPP-OLD-001,老客户A,20000,Closed Won,李四,2024-08-01\n"
        "OPP-OLD-002,老客户B,55000,Closed Lost,王五,2024-07-15\n"
    ),
    "archive/migration_notes.txt": (
        "2024 Q3 pipeline migrated from Salesforce to internal CRM.\n"
        "Note: deal_value field was renamed from 'amount' in legacy system.\n"
    ),
    "config/crm_field_map.json": json.dumps({
        "legacy_field_mapping": {
            "amount": "deal_value",
            "acct_name": "company",
            "close_dt": "last_interaction"
        }
    }, indent=2),
    "config/email_templates.yaml": (
        "follow_up:\n"
        "  subject: '跟进：{{company}} 合作机会'\n"
        "  body: '您好，感谢上次的沟通...'\n"
    ),
    "scripts/export_to_csv.py": (
        "# Utility: export CRM records to CSV (not part of next-action skill)\n"
        "import csv, json, sys\n"
        "# ... placeholder\n"
    ),
    "resources/old_spec_v0.9.json": json.dumps({
        "version": "0.9.0",
        "priority_rules": {"high": "TBD", "low": "TBD"},
        "note": "DEPRECATED — do not use"
    }, indent=2),
    "archive/2024Q2_action_items.md": (
        "# Q2 Action Items (ARCHIVED)\n\n"
        "- OPP-OLD-003: Send proposal by 2024-06-15\n"
        "- OPP-OLD-004: Schedule exec review\n"
    ),
    "config/integrations.json": json.dumps({
        "salesforce": {"enabled": False, "sync": "read-only"},
        "hubspot": {"enabled": False},
        "slack_notifications": {"enabled": False, "channel": "#sales-ops"}
    }, indent=2),
    "tests/integration_test_stub.py": (
        "# Integration test stub — requires live CRM credentials\n"
        "# DO NOT RUN IN CI\n"
        "import pytest\n"
    ),
    "archive/competitor_analysis_notes.txt": (
        "Competitor A: Strong in SMB segment.\n"
        "Competitor B: Weak support, price competitive.\n"
        "Internal: Do not share outside sales team.\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = skill_dir / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

# ── 8. THE ACTUAL TASK INPUT (messy, realistic, with missing fields) ──────────
# Placed in the workspace root so the agent finds it as described in the prompt.
# 4 opportunities:
#   OPP-2025-001: Full data, high-value Negotiation → P1-紧急
#   OPP-2025-002: Full data, Proposal Sent, no-advance keyword "no response" → P2-跟进 + no-advance triggered
#   OPP-2025-003: Missing last_interaction → 待确认项
#   OPP-2025-004: Missing stage → 待确认项

task_input = {
    "opportunities": [
        {
            "opportunity_id": "OPP-2025-001",
            "company": "云跃网络科技有限公司",
            "deal_value": 250000,
            "stage": "Negotiation",
            "owner": "赵磊",
            "last_interaction": "2025-01-08",
            "notes": "已进入合同谈判，客户法务团队要求修改SLA条款，决策人为CTO张总"
        },
        {
            "opportunity_id": "OPP-2025-002",
            "company": "恒信数据服务集团",
            "deal_value": 88000,
            "stage": "Proposal Sent",
            "owner": "林晓雯",
            "last_interaction": "2024-12-20",
            "notes": "已发送完整方案，但no response超过三周，怀疑内部预算重新评估中"
        },
        {
            "opportunity_id": "OPP-2025-003",
            "company": "青松智能制造",
            "deal_value": 175000,
            "stage": "Contract Review",
            "owner": "陈伟",
            "last_interaction": "",
            "notes": "合同已进入法务审核，但上次沟通时间记录遗失，需要确认"
        },
        {
            "opportunity_id": "OPP-2025-004",
            "company": "新亚跨境电商平台",
            "deal_value": 42000,
            "stage": "",
            "owner": "周敏",
            "last_interaction": "2025-01-03",
            "notes": "客户刚完成内部系统迁移，有意向但阶段标签在CRM导出时丢失"
        }
    ]
}

task_input_path = WORKSPACE / "q1_pipeline_opportunities.json"
task_input_path.write_text(json.dumps(task_input, ensure_ascii=False, indent=2), encoding="utf-8")

print("Workspace generation complete.")
print(f"Task input: {task_input_path}")
print(f"Skill dir:  {skill_dir}")