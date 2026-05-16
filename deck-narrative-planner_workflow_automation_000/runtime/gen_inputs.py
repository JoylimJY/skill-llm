import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

BASE = Path("/workspace")

# ─── 1. Build the skill directory structure (simulating a real OpenClaw skill bundle) ───

SKILL_BASE = BASE / "skills" / "deck-narrative-planner"

dirs = [
    SKILL_BASE / "scripts",
    SKILL_BASE / "resources",
    SKILL_BASE / "examples" / "case_a",
    SKILL_BASE / "examples" / "case_b",
    SKILL_BASE / "tests",
    SKILL_BASE / "logs",
    SKILL_BASE / "tmp",
    BASE / "raw_materials" / "clinical",
    BASE / "raw_materials" / "market",
    BASE / "raw_materials" / "financials",
    BASE / "archive" / "old_decks",
    BASE / "archive" / "unused_templates",
    BASE / "config",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ─── 2. Create spec.json (the binding spec for output validation) ───

spec = {
    "version": "1.0.0",
    "output_sections": [
        {
            "id": "main_narrative",
            "label": "整体主线",
            "required": True,
            "min_sentences": 1,
            "description": "One or two sentences capturing the central argument of the deck"
        },
        {
            "id": "slide_titles",
            "label": "页级标题",
            "required": True,
            "min_items": 6,
            "max_items": 14,
            "description": "One-sentence title per slide, numbered"
        },
        {
            "id": "evidence_requirements",
            "label": "证据需求",
            "required": True,
            "description": "Per-slide listing of required evidence, data, or citations"
        },
        {
            "id": "transitions",
            "label": "过渡语",
            "required": True,
            "description": "Bridging sentences connecting adjacent slides"
        },
        {
            "id": "risk_slide",
            "label": "风险页",
            "required": True,
            "description": "Explicit risks, mitigations, and compliance flags"
        },
        {
            "id": "closing_action",
            "label": "结尾行动",
            "required": True,
            "description": "The final call-to-action or next step requested of the audience"
        }
    ],
    "draft_before_checklist": True,
    "task_brief_required": True,
    "pending_items_on_missing_info": True,
    "forbidden": ["fabricate_evidence", "generate_visual_assets"]
}

(SKILL_BASE / "resources" / "spec.json").write_text(
    json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ─── 3. Create template.md (the canonical output template) ───

template_md = textwrap.dedent("""\
# 演示叙事规划 — 可审阅草案

## 任务书（重组后）
<!-- 把用户信息重组为结构化任务说明 -->

## 待确认项
<!-- 显式列出缺失信息，不编造 -->

---

## 整体主线
<!-- 一到两句核心论点 -->

## 页级标题
<!-- 每页一句，编号，例如：
1. 标题一
2. 标题二
-->

## 证据需求
<!-- 按页列出需要的数据/引用 -->

## 过渡语
<!-- 相邻页之间的衔接句 -->

## 风险页
<!-- 风险、缓解措施、合规说明 -->

## 结尾行动
<!-- 行动号召或下一步 -->

---

# 可执行清单
<!-- 审阅草案之后，给出可直接使用的清单 -->
""")

(SKILL_BASE / "resources" / "template.md").write_text(template_md, encoding="utf-8")

# ─── 4. Create the run.py script (the canonical entry point) ───

run_py = textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"
deck-narrative-planner run.py
Reads an input markdown/text file and renders a structured deck narrative
conforming to spec.json, written to the output file.
\"\"\"
import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
SPEC_PATH = BASE_DIR / "resources" / "spec.json"
TEMPLATE_PATH = BASE_DIR / "resources" / "template.md"

def load_spec():
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))

def extract_section(text, heading):
    \"\"\"Very simple extractor: returns text under a ## heading until next ##\"\"\"
    lines = text.splitlines()
    in_section = False
    result = []
    for line in lines:
        if line.strip().startswith("## ") and heading.lower() in line.lower():
            in_section = True
            continue
        elif line.strip().startswith("## ") and in_section:
            break
        elif in_section:
            result.append(line)
    return "\\n".join(result).strip()

def validate_output(content, spec):
    errors = []
    for section in spec["output_sections"]:
        label = section["label"]
        if label not in content:
            errors.append(f"Missing required section: {label}")
        elif section.get("min_items"):
            # Count numbered items
            import re
            items = re.findall(r"^\\d+[.、．]", content, re.MULTILINE)
            if len(items) < section["min_items"]:
                errors.append(
                    f"Section '{label}' needs at least {section['min_items']} numbered items, found {len(items)}"
                )
    if spec.get("draft_before_checklist"):
        draft_pos = content.find("可审阅草案")
        checklist_pos = content.find("可执行清单")
        if draft_pos == -1:
            errors.append("Missing '可审阅草案' header")
        if checklist_pos == -1:
            errors.append("Missing '可执行清单' header")
        if draft_pos != -1 and checklist_pos != -1 and draft_pos > checklist_pos:
            errors.append("'可审阅草案' must appear BEFORE '可执行清单'")
    if spec.get("task_brief_required") and "任务书" not in content:
        errors.append("Missing '任务书' section (task brief restructure required)")
    if spec.get("pending_items_on_missing_info") and "待确认项" not in content:
        errors.append("Missing '待确认项' section for unresolved information")
    return errors

def main():
    parser = argparse.ArgumentParser(description="Deck Narrative Planner")
    parser.add_argument("--input", required=True, help="Path to input file")
    parser.add_argument("--output", required=True, help="Path to output file")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    raw_content = input_path.read_text(encoding="utf-8")
    spec = load_spec()
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # The script expects the agent to have ALREADY written a structured output
    # to the output file following the template. This script VALIDATES it.
    # If the output file exists, validate it; if not, scaffold from template.
    if output_path.exists():
        output_content = output_path.read_text(encoding="utf-8")
        errors = validate_output(output_content, spec)
        if errors:
            print("VALIDATION ERRORS:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            sys.exit(2)
        else:
            print("OK: Output passes spec validation.")
            sys.exit(0)
    else:
        # Scaffold mode: write template to output, agent must fill it in
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(template, encoding="utf-8")
        print(f"SCAFFOLDED: Template written to {output_path}. Fill in and re-run to validate.")
        sys.exit(0)

if __name__ == "__main__":
    main()
""")

(SKILL_BASE / "scripts" / "run.py").write_text(run_py, encoding="utf-8")
(SKILL_BASE / "scripts" / "run.py").chmod(0o755)

# ─── 5. Create example inputs/outputs for case_a ───

example_a_input = textwrap.dedent("""\
# 示例输入 A：远程办公效率工具推介

目标受众：中型企业IT采购委员会
核心结论：我们的工具将团队协作效率提升40%，且部署成本低于竞品30%。

材料：
- Q3用户调研：500名用户，满意度4.2/5
- 竞品对比表（附件）
- 客户案例：某制造企业节省200小时/月
- 定价方案：基础版$10/用户/月，企业版$25
""")

example_a_output = textwrap.dedent("""\
# 演示叙事规划 — 可审阅草案

## 任务书（重组后）
为IT采购委员会制作推介Deck，核心论点为效率与成本优势，目标是获得采购决策或下一步PoC授权。

## 待确认项
- 竞品对比表具体内容（仅提及"附件"但未提供）
- 演示时长限制

---

## 整体主线
我们的远程协作工具在已验证的用户数据支持下，以更低成本实现显著效率提升，是当前市场最优选择。

## 页级标题
1. 封面：重新定义远程团队协作效率
2. 问题：现有工具的三大痛点
3. 解决方案：我们的核心功能矩阵
4. 数据验证：Q3调研——500用户，满意度4.2/5
5. 客户案例：某制造企业节省200小时/月
6. 竞品对比：成本低30%，效率高40%
7. 定价方案：灵活分层，快速落地
8. 实施路径：30天上线计划
9. 风险与缓解：迁移风险评估
10. 结尾：立即启动PoC，30天见成效

## 证据需求
- 页4：Q3调研报告原始数据
- 页5：客户书面证言或案例研究
- 页6：竞品官网定价截图（需法务确认可引用）

## 过渡语
- 页2→3：了解了痛点，让我们看看我们如何系统性解决它。
- 页3→4：方案不靠猜测，数据说话。
- 页6→7：优势明确之后，我们来谈谈如何以最低成本引入。

## 风险页
- 数据迁移风险：提供迁移工具包，保证零停机
- 竞品引用合规：需法务审查后方可在正式材料中使用竞品对比数据

## 结尾行动
请委员会批准启动为期30天的PoC项目，下周五前确认参与团队名单。

---

# 可执行清单
- [ ] 补充竞品对比表数据
- [ ] 获取客户案例书面授权
- [ ] 法务审查竞品引用
- [ ] 确认演示时长并调整页数
""")

(SKILL_BASE / "examples" / "case_a" / "input.md").write_text(example_a_input, encoding="utf-8")
(SKILL_BASE / "examples" / "case_a" / "output.md").write_text(example_a_output, encoding="utf-8")

# ─── 6. Create example case_b (simpler, partial) ───

example_b_input = textwrap.dedent("""\
# 示例输入 B：新员工入职培训Deck

目标受众：新入职员工（应届生为主）
核心结论：公司文化与成长路径
材料：HR手册摘要、历年晋升数据（内部）
""")

(SKILL_BASE / "examples" / "case_b" / "input.md").write_text(example_b_input, encoding="utf-8")

# ─── 7. Create smoke test ───

smoke_test = textwrap.dedent("""\
# Smoke Test

## 测试步骤
1. 准备输入文件 `tests/smoke_input.md`
2. 运行：`python3 scripts/run.py --input tests/smoke_input.md --output tests/smoke_output.md`
3. 确认输出包含所有6个必填节（见 spec.json）
4. 确认"可审阅草案"出现在"可执行清单"之前
5. 确认"任务书"节存在
6. 确认"待确认项"节存在

## 预期结果
脚本输出 "OK: Output passes spec validation." 并以退出码0结束。
""")

(SKILL_BASE / "tests" / "smoke-test.md").write_text(smoke_test, encoding="utf-8")

# ─── 8. THE ACTUAL PROBLEM INPUT — messy, incomplete medical/fundraising material ───

# This is the raw material the agent must process.
# Deliberately missing: target audience (must be flagged as 待确认项)
# Contains: scattered notes, redundant info, unstructured paragraphs

raw_input = textwrap.dedent("""\
# NovaPulse Medical — Board Deck 材料包（草稿，内部勿外传）

## 背景与核心结论
NovaPulse 开发了一种可穿戴心脏监测贴片 CardioTag™，目前已完成 II 期临床试验。
核心结论：CardioTag™ 在高风险患者群体中将房颤早期检出率提升了 67%，误报率低于现有 Holter 监测仪 40%。
我们正在寻求 B 轮融资 3000 万美元，用于 III 期试验及 FDA 510(k) 申报。

## 临床数据（II 期）
- 受试者：320名，年龄50-75岁，既往有短暂性脑缺血发作史
- 试验周期：12周连续监测
- 主要终点：房颤检出率 vs 标准Holter
  - CardioTag™：82% 检出率
  - 标准Holter：49% 检出率（同期对照）
- 误报率：CardioTag™ 3.1%，标准Holter 5.2%
- 不良事件：皮肤轻微刺激（12例，均自行缓解），无严重不良事件
- 数据来源：NovaPulse ClinicalOps 内部数据库，待第三方审计

## 市场信息
- 全球可穿戴心脏监测市场规模2023年约$42亿，CAGR 18%（来源：Frost & Sullivan 报告，需购买完整版确认）
- 主要竞品：iRhythm Zio Patch（美国市占率约35%），BioTelemetry（已被飞利浦收购）
- 差异化：CardioTag™ 贴片持续时长28天（竞品通常14天），AI算法实时推送预警

## 融资与财务
- 已融资：A轮 $800万（2022年，某家族办公室+天使）
- 本轮目标：$3000万 B轮
- 资金用途：
  - III期试验：$1200万
  - FDA 510(k) 申报及监管费用：$400万
  - 商业化准备（销售团队+渠道）：$900万
  - 运营储备：$500万
- 当前月度燃烧率：$38万/月，预计资金可撑至2024年Q3

## 团队
- CEO：Dr. Mei Lin，心脏病专家，前任职于梅奥诊所，发表SCI论文28篇
- CTO：Alex Novak，前苹果HealthKit工程师
- CMO：Dr. Raj Patel，FDA申报经验（2次510(k)成功获批）
- 顾问：某知名心内科主任（需确认是否可公开署名）

## 其他散乱笔记（请整理）
- 要提一下竞品iRhythm最近的负面新闻（裁员+Medicare报销削减），但注意不要过度攻击
- 投资人会问III期风险，要提前准备好对策
- PPT风格：简洁，数据驱动，避免过度堆砌文字
- 可能需要一页专门讲"为什么现在"（市场时机）
- 顾问名字还没定，先留白
- 目标受众：[待填写——Leo说要先确认是专业医疗投资人还是综合PE]
""")

# Save the raw input as the agent's working file
input_path = BASE / "raw_materials" / "clinical" / "novapu lse_board_deck_draft.md"
# Use a clean filename
input_path = BASE / "raw_materials" / "clinical" / "novapulse_board_deck_draft.md"
input_path.write_text(raw_input, encoding="utf-8")

# ─── 9. Distractor files ───

# Old deck outlines
(BASE / "archive" / "old_decks" / "series_a_deck_2022.md").write_text(
    "# Series A Deck 2022\n这是旧版A轮材料，已归档，请勿使用。\n", encoding="utf-8"
)
(BASE / "archive" / "old_decks" / "ipo_draft_abandoned.md").write_text(
    "# IPO Draft (Abandoned)\n监管环境不成熟，项目搁置。\n", encoding="utf-8"
)

# Unused templates
(BASE / "archive" / "unused_templates" / "beamer_template.tex").write_text(
    "% LaTeX Beamer template — not used by this skill\n\\documentclass{beamer}\n", encoding="utf-8"
)
(BASE / "archive" / "unused_templates" / "powerpoint_macro.vba").write_text(
    "' VBA macro for old deck generation\nSub GenerateSlide()\nEnd Sub\n", encoding="utf-8"
)

# Market data files (distractors)
(BASE / "raw_materials" / "market" / "frost_sullivan_excerpt.txt").write_text(
    "Frost & Sullivan: Wearable Cardiac Monitor Market, 2023-2028.\n"
    "Excerpt only. Full report requires purchase.\n"
    "CAGR: 18.2%, Base Year Value: $4.2B USD\n", encoding="utf-8"
)
(BASE / "raw_materials" / "market" / "competitor_notes.txt").write_text(
    "iRhythm Q2 2023: Revenue $113M, but Medicare reimbursement cut by CMS.\n"
    "BioTelemetry: acquired by Philips 2021 for $2.8B.\n", encoding="utf-8"
)

# Financial spreadsheet stub
(BASE / "raw_materials" / "financials" / "burn_rate_q3.csv").write_text(
    "Month,Burn ($k)\n2024-01,380\n2024-02,382\n2024-03,385\n", encoding="utf-8"
)
(BASE / "raw_materials" / "financials" / "cap_table_snapshot.txt").write_text(
    "Cap table as of 2024-01-01. Founders: 58%, Series A investors: 32%, Options pool: 10%\n", encoding="utf-8"
)

# Config distractors
(BASE / "config" / "pipeline.yaml").write_text(
    "pipeline:\n  name: deck-gen\n  version: legacy\n  deprecated: true\n", encoding="utf-8"
)
(BASE / "config" / "env.json").write_text(
    json.dumps({"env": "production", "log_level": "warn", "skill": "deck-narrative-planner"}, indent=2),
    encoding="utf-8"
)

# Skill logs (distractors)
(SKILL_BASE / "logs" / "run_20240101.log").write_text(
    "[2024-01-01 09:00:00] INFO: run.py started\n[2024-01-01 09:00:01] INFO: Scaffolded template\n",
    encoding="utf-8"
)
(SKILL_BASE / "tmp" / ".gitkeep").write_text("", encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Skill base: {SKILL_BASE}")
print(f"Input file: {input_path}")