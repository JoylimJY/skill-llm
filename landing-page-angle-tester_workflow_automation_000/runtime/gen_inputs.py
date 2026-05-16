import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

# ─── Root workspace ───────────────────────────────────────────────────────────
WS = Path("/workspace")

# ─── Skill directory structure ─────────────────────────────────────────────────
skill_dir = WS / "skills" / "landing-page-angle-tester"
(skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
(skill_dir / "resources").mkdir(parents=True, exist_ok=True)
(skill_dir / "examples").mkdir(parents=True, exist_ok=True)
(skill_dir / "tests").mkdir(parents=True, exist_ok=True)

# ─── spec.json ────────────────────────────────────────────────────────────────
spec = {
    "skill": "landing-page-angle-tester",
    "version": "1.0.0",
    "angle_count": 4,
    "required_sections": [
        "角度候选",
        "适配人群",
        "主标题建议",
        "证据需求",
        "风险点",
        "测试顺序"
    ],
    "output_format": "markdown",
    "draft_first": True,
    "input_schema": {
        "product_name": "string",
        "product_description": "string",
        "key_features": ["string"],
        "target_users": ["string"],
        "constraints": ["string"]
    },
    "prohibited": [
        "fabricated_testimonials",
        "exaggerated_features"
    ],
    "test_order_criteria": "audience_size_desc"
}

with open(skill_dir / "resources" / "spec.json", "w", encoding="utf-8") as f:
    json.dump(spec, f, ensure_ascii=False, indent=2)

# ─── template.md ──────────────────────────────────────────────────────────────
template_md = textwrap.dedent("""\
# 落地页角度试验报告

产品：{{ product_name }}

---

## 可审阅草案

{% for angle in angles %}
### 角度 {{ loop.index }}：{{ angle.name }}

**角度候选**
{{ angle.angle_candidate }}

**适配人群**
{{ angle.target_audience }}

**主标题建议**
{{ angle.headline }}

**证据需求**
{{ angle.evidence_required }}

**风险点**
{{ angle.risk_points }}

**测试顺序**
{{ angle.test_order }}

---
{% endfor %}

## 可执行清单

{% for angle in angles %}
- [ ] 角度 {{ loop.index }} ({{ angle.name }})：{{ angle.headline }}
{% endfor %}
""")

with open(skill_dir / "resources" / "template.md", "w", encoding="utf-8") as f:
    f.write(template_md)

# ─── run.py ───────────────────────────────────────────────────────────────────
run_py = textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"
落地页角度试验器 – CLI runner
Usage: python3 run.py --input <input.json> --output <output.md>
\"\"\"
import argparse
import json
import sys
from pathlib import Path

try:
    from jinja2 import Template
except ImportError:
    print("ERROR: jinja2 not installed", file=sys.stderr)
    sys.exit(1)

REQUIRED_INPUT_KEYS = ["product_name", "product_description", "key_features",
                       "target_users", "constraints"]
REQUIRED_ANGLE_KEYS = ["name", "angle_candidate", "target_audience",
                       "headline", "evidence_required", "risk_points", "test_order"]

def validate_input(data: dict) -> list[str]:
    errors = []
    for k in REQUIRED_INPUT_KEYS:
        if k not in data:
            errors.append(f"Missing required input field: {k}")
    return errors

def validate_angles(angles: list) -> list[str]:
    errors = []
    if len(angles) != 4:
        errors.append(f"Must have exactly 4 angles, got {len(angles)}")
    for i, a in enumerate(angles):
        for k in REQUIRED_ANGLE_KEYS:
            if k not in a or not str(a[k]).strip():
                errors.append(f"Angle {i+1} missing or empty field: {k}")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    # Validate top-level input
    errs = validate_input(data)
    if errs:
        for e in errs:
            print(f"VALIDATION ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    # angles must be provided in the input file under key "angles"
    angles = data.get("angles", [])
    errs = validate_angles(angles)
    if errs:
        for e in errs:
            print(f"ANGLE ERROR: {e}", file=sys.stderr)
        sys.exit(3)

    # Check prohibited content
    full_text = json.dumps(data, ensure_ascii=False).lower()
    prohibited_phrases = [
        "用户反馈：", "客户说：", "据客户反映", "100%保证", "绝对安全",
        "fabricated", "testimonial"
    ]
    for phrase in prohibited_phrases:
        if phrase in full_text:
            print(f"PROHIBITED CONTENT detected: '{phrase}'", file=sys.stderr)
            sys.exit(4)

    # Render template
    template_file = Path(__file__).parent.parent / "resources" / "template.md"
    if not template_file.exists():
        print(f"ERROR: template not found at {template_file}", file=sys.stderr)
        sys.exit(1)

    with open(template_file, encoding="utf-8") as f:
        tmpl = Template(f.read())

    rendered = tmpl.render(product_name=data["product_name"], angles=angles)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    print(f"SUCCESS: output written to {output_path}")

if __name__ == "__main__":
    main()
""")

with open(skill_dir / "scripts" / "run.py", "w", encoding="utf-8") as f:
    f.write(run_py)
os.chmod(skill_dir / "scripts" / "run.py", 0o755)

# ─── examples/ ────────────────────────────────────────────────────────────────
example_input = {
    "product_name": "TaskFlow Pro",
    "product_description": "项目管理 SaaS，面向中小型团队",
    "key_features": ["实时协作", "AI 任务分配", "看板视图"],
    "target_users": ["项目经理", "开发团队"],
    "constraints": ["不要强调价格", "避免与 Jira 直接比较"],
    "angles": [
        {
            "name": "效率角度",
            "angle_candidate": "强调节省时间，减少会议",
            "target_audience": "被低效会议困扰的项目经理",
            "headline": "会议减少 40%，交付速度翻倍",
            "evidence_required": "内部时间追踪数据",
            "risk_points": "数据来源需核实",
            "test_order": "1 – 受众最广，优先测试"
        },
        {
            "name": "AI 赋能角度",
            "angle_candidate": "突出 AI 自动分配减少人为决策失误",
            "target_audience": "技术型团队负责人",
            "headline": "让 AI 替你分任务，专注真正重要的事",
            "evidence_required": "AI 准确率基准测试",
            "risk_points": "AI 功能过度承诺风险",
            "test_order": "2 – 技术受众规模中等"
        },
        {
            "name": "协作角度",
            "angle_candidate": "强调实时协作消除信息孤岛",
            "target_audience": "跨职能团队",
            "headline": "全员同频，项目不再失控",
            "evidence_required": "协作用户留存率数据",
            "risk_points": "需区分远程 vs 混合团队场景",
            "test_order": "3 – 细分场景较多"
        },
        {
            "name": "风险规避角度",
            "angle_candidate": "强调可见性和风险预警，降低项目失败率",
            "target_audience": "企业级决策者",
            "headline": "提前预警风险，项目不再超期超预算",
            "evidence_required": "行业项目失败率统计",
            "risk_points": "企业受众决策链长，转化周期慢",
            "test_order": "4 – 转化周期最长，最后测试"
        }
    ]
}

with open(skill_dir / "examples" / "example_input.json", "w", encoding="utf-8") as f:
    json.dump(example_input, f, ensure_ascii=False, indent=2)

# ─── smoke-test.md ────────────────────────────────────────────────────────────
smoke_test = textwrap.dedent("""\
# 冒烟测试

## 测试步骤
1. 运行 `python3 scripts/run.py --input examples/example_input.json --output /tmp/smoke_out.md`
2. 检查 /tmp/smoke_out.md 是否包含 4 个角度
3. 检查每个角度是否含有 6 个必需章节

## 期望结果
- 输出文件存在
- 包含"可审阅草案"和"可执行清单"两部分
- 无报错退出 (exit code 0)
""")

with open(skill_dir / "tests" / "smoke-test.md", "w", encoding="utf-8") as f:
    f.write(smoke_test)

# ─── THE PROBLEM: messy raw brief (what the agent must process) ───────────────
# This is the actual task input - messy, unstructured, NOT a valid JSON
raw_brief_dir = WS / "project" / "clarifai-contract-review"
raw_brief_dir.mkdir(parents=True, exist_ok=True)

messy_brief = textwrap.dedent("""\
PRODUCT BRIEF – ClauseGuard AI  (DRAFT, DO NOT DISTRIBUTE)
============================================================
Written by: Sarah Chen, Head of Growth
Date: 2024-11-15   Status: NEEDS CLEANUP

--- WHAT IS IT ---
ClauseGuard AI is an AI-powered contract review platform designed for law firms
and in-house legal teams. It reads contracts, flags risky clauses, suggests
standard alternatives, and tracks version history with audit logs.

--- KEY SELLING POINTS (brainstorm, unordered) ---
* Cuts contract review time from hours to ~15 minutes per document
* Flags 95% of non-standard clauses (internal benchmark, NOT publicly verified yet)
* Integrates with existing DMS (iManage, NetDocuments, SharePoint)
* Full audit trail for compliance (SOC 2 Type II certified)
* Supports 12 contract types (NDA, MSA, SaaS agreements, employment...)
* Multi-jurisdiction clause library (US, UK, EU)

--- WHO BUYS THIS ---
Main buyers we've identified so far:
1. Am Law 200 firm associates – overwhelmed by volume, want speed
2. In-house counsel at Series B-D startups – lean teams, need to move fast
3. CLO / General Counsel at mid-market companies – care about risk and compliance
4. Legal ops managers – they own the tooling budget, care about ROI and adoption

--- CONSTRAINTS / THINGS TO AVOID ---
- DO NOT claim the AI is "100% accurate" or "guarantees no risk" (legal compliance)
- Do not fabricate user quotes or testimonials
- Avoid direct feature comparison tables with competitors (Ironclad, Kira)
- We are in beta; some features listed above may not be GA yet – flag if needed

--- RANDOM NOTES ---
Sarah: "I feel like we need a 'speed' angle and a 'risk' angle at minimum"
Legal: "Make sure anything about the 95% figure has a disclaimer"
CTO: "The DMS integration story is undersold"
Open Q: should we target associates or partners first?

--- IGNORED FOR NOW ---
Pricing page copy (separate workstream)
Onboarding sequence emails (TBD)
""")

with open(raw_brief_dir / "product_brief_DRAFT.txt", "w", encoding="utf-8") as f:
    f.write(messy_brief)

# ─── Distractor files ──────────────────────────────────────────────────────────
# 1. Old competitor analysis
(WS / "project" / "research").mkdir(parents=True, exist_ok=True)
with open(WS / "project" / "research" / "competitor_analysis_Q3.csv", "w") as f:
    f.write("Competitor,Price,Users,Notable Feature\n")
    f.write("Ironclad,$$$$,5000,Workflow automation\n")
    f.write("Kira,$$$$,3000,ML extraction\n")
    f.write("Luminance,$$$,2000,AI review\n")

# 2. Old marketing brief in wrong format
with open(WS / "project" / "research" / "old_messaging_v1.txt", "w") as f:
    f.write("OLD MESSAGING (DEPRECATED)\nDo not use this file.\nClauseGuard = fast contract review.\n")

# 3. Fake analytics data
(WS / "project" / "analytics").mkdir(parents=True, exist_ok=True)
with open(WS / "project" / "analytics" / "conversion_rates_2024.json", "w") as f:
    json.dump({"q1": 0.032, "q2": 0.041, "q3": 0.038, "q4_forecast": 0.045}, f)

# 4. Random internal memo
with open(WS / "project" / "analytics" / "internal_memo_oct.txt", "w") as f:
    f.write("Re: Q4 budget\nWe have $50k for paid campaigns.\nPrioritize LinkedIn over Google for legal audience.\n")

# 5. Random config files
(WS / "config").mkdir(parents=True, exist_ok=True)
with open(WS / "config" / "deploy.yaml", "w") as f:
    f.write("env: staging\nregion: us-west-2\nscale: 2\n")

with open(WS / "config" / ".env.example", "w") as f:
    f.write("API_KEY=\nDB_URL=\nSECRET=\n")

# 6. Stale requirements file
with open(WS / "config" / "requirements_old.txt", "w") as f:
    f.write("flask==1.1.2\nrequests==2.25.1\n")

# 7. Logs directory with noise
(WS / "logs").mkdir(parents=True, exist_ok=True)
for i in range(3):
    with open(WS / "logs" / f"app_{2024100+i}.log", "w") as f:
        f.write(f"[INFO] Service started\n[WARN] Slow query at t={random.randint(100,999)}ms\n")

# 8. A half-filled template that is NOT the correct input format
with open(WS / "project" / "clarifai-contract-review" / "TEMPLATE_ATTEMPT_broken.json", "w") as f:
    # Intentionally broken / incomplete - missing required fields
    json.dump({
        "product": "ClauseGuard AI",
        "features": ["fast review", "clause flagging"],
        "notes": "incomplete - sarah said fill this in later"
    }, f, ensure_ascii=False, indent=2)

# 9. Another distractor
(WS / "project" / "clarifai-contract-review" / "wireframes").mkdir(parents=True, exist_ok=True)
with open(WS / "project" / "clarifai-contract-review" / "wireframes" / "lp_sketch_notes.txt", "w") as f:
    f.write("Hero section: big headline + CTA\nSection 2: Feature grid\nSection 3: Social proof (TBD)\n")

# 10. Fake AB test results
with open(WS / "project" / "clarifai-contract-review" / "ab_test_results_Q2.csv", "w") as f:
    f.write("variant,impressions,clicks,cvr\ncontrol,10000,320,0.032\nvariant_a,10000,410,0.041\n")

print("Workspace generated successfully.")
print(f"Skill dir: {skill_dir}")
print(f"Raw brief: {raw_brief_dir / 'product_brief_DRAFT.txt'}")