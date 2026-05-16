import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Skill directory structure ──────────────────────────────────────────────
skill_base = WORKSPACE / "skills" / "nonprofit-grant-outline"
(skill_base / "scripts").mkdir(parents=True, exist_ok=True)
(skill_base / "resources").mkdir(parents=True, exist_ok=True)
(skill_base / "examples").mkdir(parents=True, exist_ok=True)
(skill_base / "tests").mkdir(parents=True, exist_ok=True)

# ── spec.json ─────────────────────────────────────────────────────────────────
spec = {
    "version": "1.0.0",
    "output_sections": [
        {"key": "project_summary",   "label": "项目摘要",   "required": True},
        {"key": "problem_definition", "label": "问题定义",  "required": True},
        {"key": "action_plan",       "label": "行动方案",   "required": True},
        {"key": "budget_framework",  "label": "预算框架",   "required": True},
        {"key": "impact_metrics",    "label": "影响指标",   "required": True},
        {"key": "evidence_and_risks","label": "证据与风险", "required": True}
    ],
    "pending_placeholder": "【待确认项】",
    "missing_data_policy": "explicit_placeholder",
    "fabrication_policy": "forbidden",
    "required_input_fields": [
        "project_name", "objective", "beneficiaries",
        "budget_total", "evidence", "risks"
    ],
    "optional_input_fields": ["impact_metrics", "duration_months", "org_name"]
}
(skill_base / "resources" / "spec.json").write_text(
    json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── template.md ───────────────────────────────────────────────────────────────
template_md = textwrap.dedent("""\
# Grant Proposal 大纲草案

## 项目摘要
{{ project_summary }}

## 问题定义
{{ problem_definition }}

## 行动方案
{{ action_plan }}

## 预算框架
{{ budget_framework }}

## 影响指标
{{ impact_metrics }}

## 证据与风险
{{ evidence_and_risks }}

---
_本文件为可审阅草案，未经正式合规审核，不得直接提交。_
""")
(skill_base / "resources" / "template.md").write_text(template_md, encoding="utf-8")

# ── run.py ────────────────────────────────────────────────────────────────────
run_py = textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"
nonprofit-grant-outline run.py
Usage: python3 run.py --input <input_json> --output <output_md>
\"\"\"
import argparse, json, sys
from pathlib import Path
from jinja2 import Template

BASE = Path(__file__).parent.parent
SPEC_PATH = BASE / "resources" / "spec.json"
TEMPLATE_PATH = BASE / "resources" / "template.md"

PLACEHOLDER = "【待确认项】"

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def render_section(value, label):
    if value is None or str(value).strip() == "" or str(value).strip().upper() == "NULL":
        return f"{PLACEHOLDER}：{label} 尚未提供，请在正式申请前补充。"
    return str(value).strip()

def process(input_data, spec):
    ctx = {}
    name    = input_data.get("project_name", "")
    obj     = input_data.get("objective", "")
    bene    = input_data.get("beneficiaries", None)
    budget  = input_data.get("budget_total", None)
    evidence= input_data.get("evidence", None)
    risks   = input_data.get("risks", None)
    impact  = input_data.get("impact_metrics", None)
    org     = input_data.get("org_name", "")
    dur     = input_data.get("duration_months", None)

    # project_summary
    summary_parts = []
    if name: summary_parts.append(f"项目名称：{name}")
    if org:  summary_parts.append(f"申请机构：{org}")
    if obj:  summary_parts.append(f"核心目标：{obj}")
    if dur:  summary_parts.append(f"项目周期：{dur} 个月")
    ctx["project_summary"] = "\\n".join(summary_parts) if summary_parts else PLACEHOLDER + "：项目摘要信息不足。"

    # problem_definition
    if obj and obj.strip():
        ctx["problem_definition"] = f"本项目聚焦于以下核心问题：\\n{obj}"
    else:
        ctx["problem_definition"] = f"{PLACEHOLDER}：问题定义（objective）未提供。"

    # action_plan
    if bene and str(bene).strip() not in ("", "NULL", "null"):
        ctx["action_plan"] = f"目标受益群体：{bene}\\n具体行动方案待项目团队根据目标制定。"
    else:
        ctx["action_plan"] = f"{PLACEHOLDER}：受益人（beneficiaries）未提供，行动方案无法完整生成。"

    # budget_framework
    if budget is not None and str(budget).strip() not in ("", "NULL", "null", "CORRUPTED", "N/A", "TBD"):
        ctx["budget_framework"] = f"总预算：{budget}\\n详细预算分项待财务团队确认。"
    else:
        ctx["budget_framework"] = f"{PLACEHOLDER}：预算总额（budget_total）数据无效或缺失，请提供合法数值。"

    # impact_metrics
    if impact and str(impact).strip() not in ("", "NULL", "null"):
        ctx["impact_metrics"] = str(impact).strip()
    else:
        ctx["impact_metrics"] = f"{PLACEHOLDER}：影响指标（impact_metrics）未提供，请补充可量化目标。"

    # evidence_and_risks
    parts = []
    if evidence and str(evidence).strip() not in ("", "NULL", "null"):
        parts.append(f"支持证据：\\n{evidence}")
    else:
        parts.append(f"{PLACEHOLDER}：证据（evidence）未提供。")
    if risks and str(risks).strip() not in ("", "NULL", "null"):
        parts.append(f"\\n主要风险：\\n{risks}")
    else:
        parts.append(f"\\n{PLACEHOLDER}：风险说明（risks）未提供。")
    ctx["evidence_and_risks"] = "\\n".join(parts)

    return ctx

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    spec = load_json(SPEC_PATH)
    input_data = load_json(args.input)
    template_src = TEMPLATE_PATH.read_text(encoding="utf-8")

    ctx = process(input_data, spec)
    rendered = Template(template_src).render(**ctx)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    print(f"[run.py] Output written to: {out}")

if __name__ == "__main__":
    main()
""")
(skill_base / "scripts" / "run.py").write_text(run_py, encoding="utf-8")

# ── smoke-test.md ─────────────────────────────────────────────────────────────
smoke = textwrap.dedent("""\
# 冒烟测试

## 测试用例 1：完整输入
- 输入：examples/complete_input.json
- 期望：所有六个章节均有实质内容，无【待确认项】

## 测试用例 2：缺失预算
- 输入：examples/missing_budget.json
- 期望：预算框架章节包含【待确认项】

## 测试用例 3：缺失受益人
- 输入：examples/missing_bene.json
- 期望：行动方案包含【待确认项】
""")
(skill_base / "tests" / "smoke-test.md").write_text(smoke, encoding="utf-8")

# ── examples ──────────────────────────────────────────────────────────────────
complete_input = {
    "project_name": "乡村数字启航计划",
    "org_name": "启明公益基金会",
    "objective": "为西部农村地区12-18岁青少年提供数字素养培训，缩小城乡数字鸿沟。",
    "beneficiaries": "四川省凉山州贫困农村青少年，预计直接受益 1200 人",
    "budget_total": "CNY 480,000",
    "duration_months": 18,
    "impact_metrics": "完成率≥80%；数字技能测评提升≥30分；就业转化率≥15%",
    "evidence": "2023年全国互联网发展报告显示城乡宽带接入率差距仍达 22 个百分点。",
    "risks": "网络基础设施不稳定；师资流动性高；季节性辍学率。"
}
(skill_base / "examples" / "complete_input.json").write_text(
    json.dumps(complete_input, ensure_ascii=False, indent=2), encoding="utf-8"
)

(skill_base / "examples" / "complete_output.md").write_text(
    "# 完整输出示例（参考用，勿直接复制）\n见 template.md 渲染结果。\n", encoding="utf-8"
)

# ── THE MESSY TASK INPUT ──────────────────────────────────────────────────────
# Deliberately: budget_total is CORRUPTED, impact_metrics is missing, risks is null
task_input = {
    "project_name": "山区儿童阅读素养提升项目",
    "org_name": "明日之光公益协会",
    "objective": "在云南省怒江州三个深度贫困县的小学中建立流动图书角，为6-12岁儿童提供阅读指导与素养培训，改善当地儿童识字率与阅读习惯。",
    "beneficiaries": "云南省怒江州福贡县、贡山县、兰坪县农村小学在校学生",
    "budget_total": "CORRUPTED",
    "duration_months": 24,
    "impact_metrics": None,
    "evidence": "教育部2022年抽样调查显示怒江州农村小学生课外阅读量仅为全国平均水平的18%，图书角覆盖率不足5%。",
    "risks": None
}
task_input_path = WORKSPACE / "project_brief" / "shanqu_reading_project.json"
task_input_path.parent.mkdir(parents=True, exist_ok=True)
task_input_path.write_text(
    json.dumps(task_input, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── 2. Distractor files ───────────────────────────────────────────────────────
distractor_root = WORKSPACE / "archive"
distractor_root.mkdir(exist_ok=True)

# Old abandoned proposals
for i in range(1, 4):
    d = distractor_root / f"proposal_2022_v{i}"
    d.mkdir(exist_ok=True)
    (d / "notes.txt").write_text(
        f"废弃草案 v{i}：预算未核实，受益人数据有误，请勿参考。\n", encoding="utf-8"
    )
    (d / "budget_estimate.csv").write_text(
        "item,amount\n人员费,120000\n设备,80000\n差旅,30000\n", encoding="utf-8"
    )

# Fake config files
(WORKSPACE / "config" / "org_settings.yaml").parent.mkdir(exist_ok=True)
(WORKSPACE / "config" / "org_settings.yaml").write_text(
    "org_name: 明日之光公益协会\nfiscal_year: 2024\napproved_programs: []\n", encoding="utf-8"
)
(WORKSPACE / "config" / "submission_deadlines.json").write_text(
    json.dumps({"Q1": "2024-03-31", "Q2": "2024-06-30"}, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Irrelevant compliance docs
compliance_dir = WORKSPACE / "compliance"
compliance_dir.mkdir(exist_ok=True)
for fname in ["audit_checklist.txt", "legal_disclaimer.txt", "fiscal_policy.md"]:
    (compliance_dir / fname).write_text(
        f"[合规文件] {fname} — 仅供内部审核使用，不构成申请材料。\n", encoding="utf-8"
    )

# Irrelevant data files
data_dir = WORKSPACE / "internal_data"
data_dir.mkdir(exist_ok=True)
(data_dir / "beneficiary_survey_RAW.csv").write_text(
    "id,age,county,literacy_score\n1,8,福贡,42\n2,10,贡山,55\n3,7,兰坪,38\n", encoding="utf-8"
)
(data_dir / "donor_list_REDACTED.txt").write_text(
    "捐赠人名单已脱敏处理，请勿外传。\n[REDACTED]\n", encoding="utf-8"
)
(data_dir / "program_metrics_template_OLD.xlsx.txt").write_text(
    "旧版指标模板，已弃用，参见 spec.json 中的 output_sections 定义。\n", encoding="utf-8"
)

# A red-herring "output" folder with a stale draft
stale_dir = WORKSPACE / "outputs" / "stale_draft"
stale_dir.mkdir(parents=True, exist_ok=True)
(stale_dir / "draft_v0.md").write_text(
    "# 旧草案（作废）\n\n## 项目摘要\n内容已过时，请重新生成。\n", encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Task input: {task_input_path}")
print(f"Skill base: {skill_base}")