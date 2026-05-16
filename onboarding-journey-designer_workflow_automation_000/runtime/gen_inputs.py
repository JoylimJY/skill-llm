import os
import json
import random

random.seed(42)

BASE = "/workspace"

# --- Directory structure ---
dirs = [
    "onboarding-journey-designer/resources",
    "onboarding-journey-designer/scripts",
    "onboarding-journey-designer/examples",
    "onboarding-journey-designer/tests",
    "onboarding-journey-designer/drafts",
    "onboarding-journey-designer/archive",
    "hr_docs/policies",
    "hr_docs/contracts",
    "compliance/training",
    "compliance/audits",
    "ops/runbooks",
    "ops/checklists",
    "comms/templates",
    "comms/announcements",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

skill_base = os.path.join(BASE, "onboarding-journey-designer")

# --- spec.json (authoritative validation spec) ---
spec = {
    "version": "1.0.0",
    "output_format": "markdown",
    "required_sections": [
        "第1天",
        "第7天",
        "第30天",
        "关键里程碑",
        "阻塞预警",
        "衡量指标"
    ],
    "section_header_level": 2,
    "min_bullets_per_section": 3,
    "industry_compliance_rules": {
        "healthcare": {
            "阻塞预警_must_contain_one_of": ["合规", "隐私", "HIPAA", "患者数据", "风险", "审计", "权限"]
        },
        "fintech": {
            "阻塞预警_must_contain_one_of": ["合规", "KYC", "AML", "风险", "审计", "监管"]
        }
    },
    "day1_required_keywords_source": "target_audience",
    "notes": "第1天 section must mention at least one token from the target_audience field of the input JSON."
}
with open(os.path.join(skill_base, "resources/spec.json"), "w", encoding="utf-8") as f:
    json.dump(spec, f, ensure_ascii=False, indent=2)

# --- template.md ---
template_md = """# Onboarding Journey: {role}

## 第1天
<!-- Day 1: Orientation, system access, introductions. Must mention target audience context. -->
- 

## 第7天
<!-- Day 7: First tasks, shadowing, initial deliverables. -->
- 

## 第30天
<!-- Day 30: Independent contribution, feedback loop, milestone check. -->
- 

## 关键里程碑
<!-- Key milestones and success criteria. -->
- 

## 阻塞预警
<!-- Blockers, risks, compliance/privacy issues that could derail onboarding. -->
- 

## 衡量指标
<!-- Measurable KPIs and success metrics. -->
- 
"""
with open(os.path.join(skill_base, "resources/template.md"), "w", encoding="utf-8") as f:
    f.write(template_md)

# --- run.py (the proprietary validation + generation script) ---
run_py = r'''#!/usr/bin/env python3
"""
Onboarding Journey Designer - run.py
Validates input JSON, then validates the output Markdown against spec.json.
Usage: python3 run.py --input <input_json> --output <output_md>
"""
import argparse
import json
import sys
import os
import re

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_md(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_sections(md_text):
    """Extract ## sections and their content."""
    pattern = re.compile(r'^## (.+)$', re.MULTILINE)
    headers = list(pattern.finditer(md_text))
    sections = {}
    for i, m in enumerate(headers):
        title = m.group(1).strip()
        start = m.end()
        end = headers[i+1].start() if i+1 < len(headers) else len(md_text)
        content = md_text[start:end]
        sections[title] = content
    return sections

def count_bullets(content):
    lines = content.split('\n')
    return sum(1 for l in lines if re.match(r'^\s*[-*]\s+\S', l))

def validate_output(md_text, spec, input_data):
    errors = []
    required = spec["required_sections"]
    min_bullets = spec["min_bullets_per_section"]
    sections = get_sections(md_text)

    for sec in required:
        if sec not in sections:
            errors.append(f"Missing required section: ## {sec}")
        else:
            bc = count_bullets(sections[sec])
            if bc < min_bullets:
                errors.append(f"Section '## {sec}' has {bc} bullet(s); need >= {min_bullets}.")

    # Day 1 must mention target_audience token
    target_audience = input_data.get("target_audience", "")
    tokens = [t.strip() for t in re.split(r'[\s,、/]+', target_audience) if t.strip()]
    if "第1天" in sections:
        day1_content = sections["第1天"]
        found_token = any(tok in day1_content for tok in tokens)
        if not found_token:
            errors.append(
                f"Section '## 第1天' must mention at least one token from target_audience: {tokens}"
            )

    # Industry compliance check
    industry = input_data.get("industry", "").lower()
    compliance_rules = spec.get("industry_compliance_rules", {})
    if industry in compliance_rules:
        must_contain = compliance_rules[industry].get("阻塞预警_must_contain_one_of", [])
        if "阻塞预警" in sections:
            blocker_content = sections["阻塞预警"]
            if not any(kw in blocker_content for kw in must_contain):
                errors.append(
                    f"Industry '{industry}': '## 阻塞预警' must contain one of: {must_contain}"
                )
        else:
            errors.append("Missing '## 阻塞预警' section (required for compliance industries).")

    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input JSON file")
    parser.add_argument("--output", required=True, help="Output Markdown file to validate")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    input_data = load_json(args.input)

    required_input_fields = ["target_audience", "industry", "core_actions", "success_criteria"]
    missing = [f for f in required_input_fields if f not in input_data]
    if missing:
        print(f"ERROR: Input JSON missing fields: {missing}", file=sys.stderr)
        sys.exit(1)

    spec_path = os.path.join(os.path.dirname(__file__), "..", "resources", "spec.json")
    if not os.path.exists(spec_path):
        print(f"ERROR: spec.json not found at {spec_path}", file=sys.stderr)
        sys.exit(1)
    spec = load_json(spec_path)

    if not os.path.exists(args.output):
        print(f"ERROR: Output file not found: {args.output}", file=sys.stderr)
        sys.exit(1)

    md_text = load_md(args.output)
    errors = validate_output(md_text, spec, input_data)

    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(2)
    else:
        print("VALIDATION PASSED: Onboarding journey document is compliant.")
        sys.exit(0)

if __name__ == "__main__":
    main()
'''
with open(os.path.join(skill_base, "scripts/run.py"), "w", encoding="utf-8") as f:
    f.write(run_py)

# --- examples/ ---
example_input = {
    "target_audience": "临床试验协调员",
    "industry": "healthcare",
    "core_actions": ["学习GCP合规规范", "配置CTMS账号", "观摩首次患者筛查"],
    "success_criteria": "30天内独立完成首个试验启动访视",
    "cohorts": 3,
    "notes": "三个不同地区的团队同时入职"
}
with open(os.path.join(skill_base, "examples/example_input.json"), "w", encoding="utf-8") as f:
    json.dump(example_input, f, ensure_ascii=False, indent=2)

example_output = """# Onboarding Journey: 临床试验协调员

## 第1天
- 参加公司全员介绍会，了解组织架构（临床试验协调员职责重点介绍）
- 领取工作设备，完成IT账号初始配置
- 签署保密协议及患者数据处理授权书

## 第7天
- 完成GCP（良好临床实践）在线培训并通过考核
- 在导师带领下观摩首次患者筛查流程
- 配置并验证CTMS（临床试验管理系统）账号权限

## 第30天
- 独立完成首个试验启动访视（Site Initiation Visit）
- 提交第一份协调日志并获得主管审核通过
- 参加月度试验进展回顾会议并汇报

## 关键里程碑
- 第1天：完成系统账号配置与合规签署
- 第7天：通过GCP培训考核
- 第30天：独立完成首个SIV

## 阻塞预警
- 患者数据隐私合规培训若未完成，将阻止参与任何现场访视（合规风险）
- CTMS系统权限审批周期可能长达5个工作日，需提前申请
- 跨地区团队可能面临不同的伦理委员会审批流程差异

## 衡量指标
- GCP培训通过率（目标：100%，第7天前）
- 首个SIV独立完成率（目标：100%，第30天前）
- 入职满意度调查评分（目标：≥4.2/5，第30天）
"""
with open(os.path.join(skill_base, "examples/example_output.md"), "w", encoding="utf-8") as f:
    f.write(example_output)

# --- smoke-test.md ---
smoke_test = """# Smoke Test

## Test 1: Basic run
- Input: examples/example_input.json
- Expected: VALIDATION PASSED

## Test 2: Missing section
- Ensure output without ## 阻塞预警 fails with VALIDATION FAILED

## Test 3: Industry compliance
- healthcare industry must trigger compliance check in 阻塞预警
"""
with open(os.path.join(skill_base, "tests/smoke-test.md"), "w", encoding="utf-8") as f:
    f.write(smoke_test)

# ====== THE ACTUAL PROBLEM INPUT (messy, real-world) ======
# This is the intake form the agent must process — deliberately messy and incomplete-looking
problem_input = {
    "target_audience": "临床数据管理员",
    "industry": "healthcare",
    "core_actions": [
        "熟悉EDC系统（电子数据采集）操作规程",
        "完成数据清洗与一致性核查培训",
        "参与方案偏差报告流程演练",
        "学习21 CFR Part 11电子记录合规要求"
    ],
    "success_criteria": "第30天可独立完成数据库锁定前的核查清单，错误率低于0.5%",
    "cohorts": 2,
    "headcount_per_cohort": 6,
    "region": ["华东", "华南"],
    "notes": "两批次同步入职，部分成员有CRA背景但无CDM经验；需重点关注数据隐私与审计追踪培训",
    "priority": "high",
    "start_date": "2024-09-01",
    "STATUS": "DRAFT - NOT REVIEWED",
    "IGNORE_THIS": "legacy field from old HR system",
    "old_template_version": "v0.3",
    "redundant_info": "copied from previous cohort form - verify before use"
}

os.makedirs(os.path.join(BASE, "intake_forms"), exist_ok=True)
with open(os.path.join(BASE, "intake_forms/cdm_cohort_intake_2024.json"), "w", encoding="utf-8") as f:
    json.dump(problem_input, f, ensure_ascii=False, indent=2)

# ====== DISTRACTOR FILES ======
distractor_files = {
    "hr_docs/policies/leave_policy_2024.txt": "Annual leave: 15 days. Sick leave: 10 days. See HR handbook v3.2.",
    "hr_docs/policies/code_of_conduct.txt": "All employees must adhere to the company's ethical standards...",
    "hr_docs/contracts/nda_template.docx.txt": "[NDA TEMPLATE - NOT FOR DISTRIBUTION]",
    "compliance/training/gcp_training_log.csv": "employee_id,completion_date,score\n001,2024-07-01,92\n002,2024-07-03,88",
    "compliance/audits/q2_2024_audit_summary.txt": "Q2 audit completed. 3 minor findings. Corrective actions pending.",
    "ops/runbooks/ctms_setup_guide.txt": "1. Submit IT ticket\n2. Await approval (3-5 days)\n3. Configure MFA",
    "ops/checklists/site_initiation_checklist.txt": "[ ] Protocol reviewed\n[ ] IRB approval obtained\n[ ] Staff trained",
    "comms/templates/welcome_email_template.txt": "Subject: Welcome to the team!\nDear {name}, we are thrilled...",
    "comms/announcements/q3_onboarding_announcement.txt": "Q3 onboarding cohorts: CDM and CRA tracks starting Sept 2024.",
    "onboarding-journey-designer/drafts/old_onboarding_draft_v1.txt": "DRAFT - DO NOT USE\nDay 1: Orientation\nDay 7: Training\nDay 30: Assessment",
    "onboarding-journey-designer/archive/deprecated_template_v02.md": "# OLD TEMPLATE\n## Day 1\n- todo\n## Day 30\n- todo",
}
for path, content in distractor_files.items():
    full_path = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Problem input: {os.path.join(BASE, 'intake_forms/cdm_cohort_intake_2024.json')}")
print(f"Skill base: {skill_base}")