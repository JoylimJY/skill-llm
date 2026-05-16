import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ── 1. Skill directory structure (simulating the installed skill) ──────────────
SKILL_DIR = WORKSPACE / "skills" / "account-handoff-builder"
for subdir in ["scripts", "resources", "examples", "tests"]:
    (SKILL_DIR / subdir).mkdir(parents=True, exist_ok=True)

# ── spec.json ─────────────────────────────────────────────────────────────────
spec = {
    "version": "1.0.0",
    "output_sections": [
        {"id": "customer_summary",     "label": "客户摘要",          "required": True},
        {"id": "commitments",          "label": "已承诺事项",        "required": True},
        {"id": "prerequisites",        "label": "实施前提",          "required": True},
        {"id": "commitment_risks",     "label": "承诺风险",          "required": True},
        {"id": "open_questions",       "label": "需要确认的问题",    "required": True},
        {"id": "next_steps",           "label": "下一步计划",        "required": True}
    ],
    "risk_keywords": ["保证", "一定", "承诺", "免费", "无限", "立即", "定制"],
    "missing_data_placeholder": "【待确认】",
    "rules": {
        "no_fabrication": True,
        "no_omit_unfavorable": True,
        "draft_before_checklist": True
    }
}
(SKILL_DIR / "resources" / "spec.json").write_text(
    json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── template.md ───────────────────────────────────────────────────────────────
template_md = textwrap.dedent("""\
# 客户交接包 — {{account_name}}

生成日期：{{date}}
负责 AE：{{ae_name}}
负责 CSM：{{csm_name}}

---

## 一、客户摘要
{{customer_summary}}

---

## 二、已承诺事项
{{commitments}}

---

## 三、实施前提
{{prerequisites}}

---

## 四、承诺风险
{{commitment_risks}}

---

## 五、需要确认的问题
{{open_questions}}

---

## 六、下一步计划
{{next_steps}}
""")
(SKILL_DIR / "resources" / "template.md").write_text(template_md, encoding="utf-8")

# ── scripts/run.py ─────────────────────────────────────────────────────────────
run_py = textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"
account-handoff-builder  run.py
Usage: python3 run.py --input <input_file> --output <output_file>

Reads raw sales notes from <input_file>, applies spec.json rules and
template.md structure, and writes the structured handoff package to
<output_file>.

Rules applied automatically:
  - Flags any sentence containing a risk_keyword as a Commitment Risk entry.
  - Any field that cannot be determined from the input is written as 【待确认】.
  - Unfavorable/risky information is preserved, never removed.
  - Output follows the 6-section structure defined in spec.json.
\"\"\"
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BASE_DIR   = SCRIPT_DIR.parent

spec     = json.loads((BASE_DIR / "resources" / "spec.json").read_text(encoding="utf-8"))
template = (BASE_DIR / "resources" / "template.md").read_text(encoding="utf-8")

RISK_KW   = spec["risk_keywords"]
MISSING   = spec["missing_data_placeholder"]

def flag_risks(text: str) -> list[str]:
    risks = []
    for line in text.splitlines():
        if any(kw in line for kw in RISK_KW):
            risks.append(line.strip())
    return risks

def extract_field(text: str, *keys: str) -> str:
    \"\"\"Return first non-empty line after any of the key labels, else MISSING.\"\"\"
    lines = text.splitlines()
    for i, line in enumerate(lines):
        for k in keys:
            if k in line and i + 1 < len(lines):
                candidate = lines[i + 1].strip()
                if candidate:
                    return candidate
    return MISSING

def build_package(raw: str) -> str:
    today = date.today().isoformat()

    account_name = extract_field(raw, "客户名称", "Account", "公司名")
    ae_name      = extract_field(raw, "销售代表", "AE", "Account Executive")
    csm_name     = extract_field(raw, "CSM", "客户成功", "交付负责人")

    # --- 客户摘要: first 3 non-empty lines after 【背景】 or 【客户背景】
    summary_lines = []
    in_bg = False
    for line in raw.splitlines():
        if re.search(r"背景|Background|Summary", line):
            in_bg = True
            continue
        if in_bg:
            stripped = line.strip()
            if stripped:
                summary_lines.append(stripped)
            if len(summary_lines) >= 4:
                break
    customer_summary = "\\n".join(summary_lines) if summary_lines else MISSING

    # --- 已承诺事项: lines under 【承诺】 / 【已承诺】 / 【Commitment】
    commit_lines = []
    in_commit = False
    for line in raw.splitlines():
        if re.search(r"承诺|Commitment|已答应", line):
            in_commit = True
            continue
        if in_commit:
            stripped = line.strip()
            if stripped.startswith("##") or stripped.startswith("【"):
                in_commit = False
            elif stripped:
                commit_lines.append("- " + stripped)
    commitments = "\\n".join(commit_lines) if commit_lines else MISSING

    # --- 实施前提: lines under 【前提】 / 【Prerequisites】
    prereq_lines = []
    in_pre = False
    for line in raw.splitlines():
        if re.search(r"前提|Prerequisite|依赖", line):
            in_pre = True
            continue
        if in_pre:
            stripped = line.strip()
            if stripped.startswith("##") or stripped.startswith("【"):
                in_pre = False
            elif stripped:
                prereq_lines.append("- " + stripped)
    prerequisites = "\\n".join(prereq_lines) if prereq_lines else MISSING

    # --- 承诺风险: auto-detected risk sentences + explicit risk section
    detected = flag_risks(raw)
    risk_lines = []
    in_risk = False
    for line in raw.splitlines():
        if re.search(r"风险|Risk|隐患", line):
            in_risk = True
            continue
        if in_risk:
            stripped = line.strip()
            if stripped.startswith("##") or stripped.startswith("【"):
                in_risk = False
            elif stripped:
                risk_lines.append(stripped)
    all_risks = list(dict.fromkeys(detected + risk_lines))  # deduplicate, preserve order
    commitment_risks = "\\n".join("- " + r for r in all_risks) if all_risks else "暂未发现明显风险"

    # --- 需要确认的问题: lines under 【待确认】 / 【Open Questions】
    oq_lines = []
    in_oq = False
    for line in raw.splitlines():
        if re.search(r"待确认|Open Question|未确定|TBD", line):
            in_oq = True
            continue
        if in_oq:
            stripped = line.strip()
            if stripped.startswith("##") or stripped.startswith("【"):
                in_oq = False
            elif stripped:
                oq_lines.append("- " + stripped)
    # Also add MISSING fields as open questions
    missing_fields = []
    if account_name == MISSING: missing_fields.append("- 客户名称未确认")
    if ae_name == MISSING:      missing_fields.append("- 销售代表未确认")
    if csm_name == MISSING:     missing_fields.append("- CSM 未确认")
    open_questions = "\\n".join(oq_lines + missing_fields) if (oq_lines or missing_fields) else MISSING

    # --- 下一步计划: lines under 【下一步】 / 【Next Steps】 / 【行动计划】
    ns_lines = []
    in_ns = False
    for line in raw.splitlines():
        if re.search(r"下一步|Next Step|行动计划|Action", line):
            in_ns = True
            continue
        if in_ns:
            stripped = line.strip()
            if stripped.startswith("##") or stripped.startswith("【"):
                in_ns = False
            elif stripped:
                ns_lines.append("- " + stripped)
    next_steps = "\\n".join(ns_lines) if ns_lines else MISSING

    out = template
    out = out.replace("{{account_name}}", account_name)
    out = out.replace("{{date}}", today)
    out = out.replace("{{ae_name}}", ae_name)
    out = out.replace("{{csm_name}}", csm_name)
    out = out.replace("{{customer_summary}}", customer_summary)
    out = out.replace("{{commitments}}", commitments)
    out = out.replace("{{prerequisites}}", prerequisites)
    out = out.replace("{{commitment_risks}}", commitment_risks)
    out = out.replace("{{open_questions}}", open_questions)
    out = out.replace("{{next_steps}}", next_steps)
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    raw = Path(args.input).read_text(encoding="utf-8")
    package = build_package(raw)
    Path(args.output).write_text(package, encoding="utf-8")
    print(f"[run.py] Handoff package written to: {args.output}")

if __name__ == "__main__":
    main()
""")
(SKILL_DIR / "scripts" / "run.py").write_text(run_py, encoding="utf-8")

# ── tests/smoke-test.md ────────────────────────────────────────────────────────
smoke = textwrap.dedent("""\
# Smoke Test

Run:
    python3 scripts/run.py --input examples/sample_input.txt --output /tmp/smoke_out.md

Verify /tmp/smoke_out.md contains all 6 sections and no fabricated data.
""")
(SKILL_DIR / "tests" / "smoke-test.md").write_text(smoke, encoding="utf-8")

# ── examples/ (sample I/O) ────────────────────────────────────────────────────
sample_input = textwrap.dedent("""\
【客户名称】
SampleCorp Ltd.

【销售代表】
Alice Wang

【CSM】
Bob Chen

【背景】
SampleCorp 是一家中型电商公司，员工 800 人。
当前使用老旧 HR 系统，迁移需求紧迫。

【承诺】
提供 3 个月免费试用期
Q3 上线

【前提】
客户需提供 SSO 集成文档
数据迁移窗口需双方确认

【待确认】
合同签署日期
定价折扣最终确认

【下一步】
安排技术对接会
发送 SoW 草稿
""")
(SKILL_DIR / "examples" / "sample_input.txt").write_text(sample_input, encoding="utf-8")

sample_output = textwrap.dedent("""\
# 客户交接包 — SampleCorp Ltd.

生成日期：2024-01-01
负责 AE：Alice Wang
负责 CSM：Bob Chen

---

## 一、客户摘要
SampleCorp 是一家中型电商公司，员工 800 人。
当前使用老旧 HR 系统，迁移需求紧迫。

---

## 二、已承诺事项
- 提供 3 个月免费试用期
- Q3 上线

---

## 三、实施前提
- 客户需提供 SSO 集成文档
- 数据迁移窗口需双方确认

---

## 四、承诺风险
- 提供 3 个月免费试用期

---

## 五、需要确认的问题
- 合同签署日期
- 定价折扣最终确认

---

## 六、下一步计划
- 安排技术对接会
- 发送 SoW 草稿
""")
(SKILL_DIR / "examples" / "sample_output.md").write_text(sample_output, encoding="utf-8")

# ── 2. The actual PROBLEM INPUT (messy, realistic, multi-source) ──────────────
DEALS_DIR = WORKSPACE / "deals" / "globalbank-hr-2024"
DEALS_DIR.mkdir(parents=True, exist_ok=True)

# The raw, messy input the agent must process
raw_sales_notes = textwrap.dedent("""\
=== GlobalBank Enterprise HR Platform — Sales Handoff Notes ===
Prepared by: Jenny Luo (AE, Enterprise East)
Date: 2024-06-10  [DRAFT — do not distribute]

【客户名称】
GlobalBank Financial Group (GBFG)

【销售代表】
Jenny Luo

【CSM】
(交付负责人尚未分配，预计本周内确认)

【背景】
GlobalBank 是一家持牌商业银行，在境内拥有 12,000 名员工，分布于 34 个城市分行。
集团 IT 部门要求所有 SaaS 供应商通过等保三级认证（现有认证过期日：2024-09-30）。
现有 HR 系统供应商合同将于 2024-08-31 到期，客户有强烈切换意愿。
客户 CTO 曾明确表示：若我们不能在 8 月 31 日前完成核心模块上线，合同可能作废。

【承诺】（销售侧已口头/书面确认，需 CS 接棒兑现）
1. 系统将在 2024-08-15 前完成核心 HR 模块上线（工资核算、考勤、组织架构）
2. 提供专属实施顾问（1 名全职，驻场 3 个月）
3. 数据迁移期间保证零丢失、零停机
4. 定制开发：一定会支持 GlobalBank 内部审批流（预计工期 6 周）
5. 首年免费提供高级分析模块（原计划单独报价 ¥180,000）
6. 承诺系统支持无限并发用户（当前平台实际上限约 5,000 并发）

【实施前提】
- 客户需在 2024-06-30 前提供完整的旧系统数据导出（CSV/Excel 格式）
- 客户 IT 需开放防火墙端口：443, 8443, 9000
- 必须完成等保三级评审（预计 6-8 周周期，需客户配合提供材料）
- 签署 DPA（数据处理协议），因银行数据涉及个人金融信息，属合规强制项
- 需客户 HR、IT、法务三方联合确认需求规格书（SRS）

【风险】
- 8 月 15 日上线节点极为激进，实施团队目前排期已满，存在严重资源冲突
- "无限并发"承诺与平台技术上限矛盾，需产品团队评审是否可扩容或需修正措辞
- 等保三级认证若未能在 8 月前通过，可能导致整个项目暂停
- 定制审批流 6 周工期评估未经研发确认，存在低估风险

【待确认】
- CSM/交付负责人姓名（本周内确认）
- 定制开发报价是否含在合同总价内，还是需要补充协议
- 高级分析模块"免费首年"是否有书面记录（Jenny 口头承诺，未见合同附件）
- 等保评审启动时间及责任方
- 数据迁移方案（全量迁移？增量？分批？）

【下一步计划】
1. CS 团队本周内指派 CSM（deadline: 2024-06-14）
2. 安排销售—CS—客户三方交接会（建议 2024-06-17 前）
3. 向客户发送实施前提清单，要求 2024-06-30 前回复
4. 研发团队评审"无限并发"可行性（deadline: 2024-06-21）
5. 法务出具 DPA 草稿（deadline: 2024-06-20）
6. 启动等保三级评审流程

=== 附注 ===
注意：Jenny 在最后一次会议中口头保证"一定能按时上线"，客户 CTO 已截图留存。
这条承诺风险极高，请 CS 团队在交接后立即与客户对齐预期。
""")
(DEALS_DIR / "raw_sales_notes.txt").write_text(raw_sales_notes, encoding="utf-8")

# ── 3. Distractor files ────────────────────────────────────────────────────────
distractors = {
    "deals/globalbank-hr-2024/email_thread_export.eml": """\
From: jenny.luo@company.com
To: cto@globalbank.com
Subject: Re: HR Platform Proposal — Final Terms

Hi David,

Thanks for the call this afternoon. As discussed, our team will do everything possible
to meet the August 15 go-live. I'll loop in our delivery lead this week.

Best,
Jenny
""",
    "deals/globalbank-hr-2024/pricing_v3_CONFIDENTIAL.txt": """\
GlobalBank Pricing Sheet v3 (CONFIDENTIAL)
Base License: ¥1,200,000 / year
Advanced Analytics: ¥180,000 / year (waived Year 1 per verbal agreement)
Custom Approval Flow Dev: TBD (Est. ¥240,000 — NOT IN CONTRACT YET)
Dedicated Consultant: ¥360,000 / quarter
""",
    "deals/globalbank-hr-2024/call_notes_2024-06-05.txt": """\
Call Notes — 2024-06-05
Participants: Jenny Luo (AE), David Zhang (CTO, GlobalBank), Mary Sun (IT Director)

- David confirmed hard deadline: 2024-08-31 contract expiry
- Mary flagged network security review needed (est. 3-4 weeks)
- Jenny committed to dedicated on-site consultant
- Pricing finalization deferred to legal review
""",
    "deals/globalbank-hr-2024/competitor_analysis_draft.txt": """\
Competitor Landscape (Internal Draft)
Vendor A: Strong on compliance, weak on customization
Vendor B: Cheaper, but no domestic data residency
Our position: Premium, compliance-ready, local support
""",
    "deals/archive/old_template_v1.md": """\
# Old Handoff Template (DEPRECATED - do not use)
Section 1: Client
Section 2: Deal
Section 3: Notes
""",
    "deals/archive/legacy_crm_export_2023.csv": """\
AccountID,Name,AE,Stage,Value
1001,RetailCo,Tom,Closed Won,500000
1002,ManufactCo,Jenny,Closed Lost,300000
""",
    "internal/onboarding/new_csm_guide.txt": """\
New CSM Onboarding Guide
1. Read client handoff package
2. Schedule kickoff call within 3 business days
3. Review SoW and confirm scope
4. Submit resource request to delivery manager
""",
    "internal/onboarding/escalation_matrix.txt": """\
Escalation Matrix
L1: CSM
L2: Delivery Manager
L3: VP Customer Success
Legal/Compliance: Forward to legal@company.com
""",
    "internal/tools/crm_sync_config.yaml": """\
crm_sync:
  enabled: false
  endpoint: https://crm.internal.company.com/api/v2
  auth: bearer_token_placeholder
  sync_interval_minutes: 60
""",
    "internal/tools/slack_notifier.sh": """\
#!/bin/bash
# Sends deal update to #cs-handoffs Slack channel
# NOT ACTIVE — requires SLACK_TOKEN env var
echo "Slack notifier: token not set, skipping."
""",
    "README_internal.txt": """\
This directory contains sales deal materials.
For CS handoff procedures, see internal/onboarding/new_csm_guide.txt
""",
}

for rel_path, content in distractors.items():
    full = WORKSPACE / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(textwrap.dedent(content), encoding="utf-8")

print("[gen_inputs] Workspace scaffold complete.")
print(f"  Skill dir  : {SKILL_DIR}")
print(f"  Problem input: {DEALS_DIR / 'raw_sales_notes.txt'}")