import os
import json
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── Skill directory structure (simulating an installed OpenClaw skill) ─────────
skill_base = WORKSPACE / "skills" / "legal-matter-intake-summarizer"
for d in [
    skill_base / "scripts",
    skill_base / "resources",
    skill_base / "examples",
    skill_base / "tests",
    skill_base / "logs",
    skill_base / "cache",
]:
    d.mkdir(parents=True, exist_ok=True)

# ── spec.json ──────────────────────────────────────────────────────────────────
spec = {
    "version": "1.0.0",
    "output_sections": [
        "事实摘要",
        "争议点",
        "已知证据",
        "缺失材料",
        "需进一步确认",
        "风险提示"
    ],
    "rules": {
        "no_legal_conclusion": True,
        "missing_info_as_pending": True,
        "high_risk_requires_boundary": True,
        "default_mode": "draft_review"
    },
    "boundary_triggers": ["个人隐私", "个人数据", "health", "medical", "privacy", "discrimination"],
    "forbidden_phrases": [
        "构成违法", "胜诉", "败诉", "赔偿金额为", "法院将判决",
        "建议起诉", "应当赔偿", "违反了法律", "依法应承担"
    ]
}
(skill_base / "resources" / "spec.json").write_text(
    json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── template.md ────────────────────────────────────────────────────────────────
template_md = textwrap.dedent("""\
# 接案摘要

## 事实摘要
<!-- 从材料中提炼的核心事实，不加主观判断 -->

## 争议点
<!-- 双方存在分歧的核心问题，条列呈现 -->

## 已知证据
<!-- 材料中明确提及的文件、记录、证人等 -->

## 缺失材料
<!-- 目前尚未收到但应当存在的材料 -->

## 需进一步确认
<!-- 待确认项：信息不完整或存在矛盾，需向当事人核实 -->

## 风险提示
<!-- 高风险、隐私、权限或合规问题，必须附边界说明 -->
<!-- ⚠️ 边界说明：本摘要为材料整理，不构成法律意见，不替代律师审查。 -->
""")
(skill_base / "resources" / "template.md").write_text(template_md, encoding="utf-8")

# ── run.py ─────────────────────────────────────────────────────────────────────
run_py = textwrap.dedent("""\
#!/usr/bin/env python3
\"\"\"
legal-matter-intake-summarizer :: run.py
Reads a raw intake memo (plain text), structures it per spec.json & template.md.
\"\"\"
import argparse, json, re, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SPEC = json.loads((BASE / "resources" / "spec.json").read_text(encoding="utf-8"))
TEMPLATE = (BASE / "resources" / "template.md").read_text(encoding="utf-8")

def extract_section(text, keywords):
    lines, capture, result = text.splitlines(), False, []
    for line in lines:
        if any(kw in line for kw in keywords):
            capture = True
        if capture and line.strip():
            result.append(line.strip())
        if capture and line.strip() == "" and result:
            break
    return " ".join(result[1:]) if len(result) > 1 else ""

def run(input_path: Path, output_path: Path):
    raw = input_path.read_text(encoding="utf-8")
    sections = SPEC["output_sections"]
    triggers = SPEC["boundary_triggers"]

    # ── Detect high-risk triggers ──────────────────────────────────────────────
    has_risk = any(t.lower() in raw.lower() for t in triggers)

    # ── Build structured output from template ──────────────────────────────────
    output_lines = ["# 接案摘要\\n"]

    # 事实摘要
    output_lines.append("## 事实摘要")
    facts = []
    for line in raw.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and len(line) > 10:
            facts.append(f"- {line}")
    output_lines.extend(facts[:12] if facts else ["- （无可提取事实）"])
    output_lines.append("")

    # 争议点
    output_lines.append("## 争议点")
    disputes = [l.strip() for l in raw.splitlines()
                if any(k in l for k in ["争议","纠纷","不认可","否认","拒绝","主张"])]
    if disputes:
        for d in disputes[:6]:
            output_lines.append(f"- {d}")
    else:
        output_lines.append("- 待梳理：当事各方立场尚未完整描述")
    output_lines.append("")

    # 已知证据
    output_lines.append("## 已知证据")
    evidence = [l.strip() for l in raw.splitlines()
                if any(k in l for k in ["合同","记录","邮件","截图","证人","工资单","协议","文件","录音"])]
    if evidence:
        for e in evidence[:8]:
            output_lines.append(f"- {e}")
    else:
        output_lines.append("- （暂无明确证据材料描述）")
    output_lines.append("")

    # 缺失材料
    output_lines.append("## 缺失材料")
    missing = [l.strip() for l in raw.splitlines()
               if any(k in l for k in ["缺少","未提供","没有","尚未","不清楚","未知"])]
    if missing:
        for m in missing[:6]:
            output_lines.append(f"- {m}")
    else:
        output_lines.append("- 劳动合同原件（未见提及）")
        output_lines.append("- 书面解除通知（未见提及）")
    output_lines.append("")

    # 需进一步确认
    output_lines.append("## 需进一步确认")
    pending_keywords = ["不确定","待确认","需核实","不清楚","未明确","?","？"]
    pending = [l.strip() for l in raw.splitlines()
               if any(k in l for k in pending_keywords)]
    if pending:
        for p in pending[:6]:
            output_lines.append(f"- 待确认项：{p}")
    else:
        output_lines.append("- 待确认项：当事人是否保存了完整的薪资发放记录")
        output_lines.append("- 待确认项：解除劳动关系的具体日期是否有书面凭证")
    output_lines.append("")

    # 风险提示
    output_lines.append("## 风险提示")
    if has_risk:
        output_lines.append("- 材料涉及个人隐私或敏感数据，处理时须遵守隐私合规要求。")
        output_lines.append("- 如涉及员工健康信息或歧视性指控，需在律师指导下处理。")
    output_lines.append("- 时效风险：需确认劳动仲裁申请时效是否已届满或临近。")
    output_lines.append("")
    output_lines.append(
        "> ⚠️ 边界说明：本摘要为接案材料整理，不构成法律意见，不替代律师审查。"
        "所有结论性判断须由具备执业资质的律师作出。"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\\n".join(output_lines), encoding="utf-8")
    print(f"[run.py] 输出已写入: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="法务接案摘要器")
    parser.add_argument("--input",  required=True, help="原始材料文件路径")
    parser.add_argument("--output", required=True, help="摘要输出文件路径")
    args = parser.parse_args()
    run(Path(args.input), Path(args.output))
""")
(skill_base / "scripts" / "run.py").write_text(run_py, encoding="utf-8")
os.chmod(skill_base / "scripts" / "run.py", 0o755)

# ── smoke-test.md ──────────────────────────────────────────────────────────────
smoke = textwrap.dedent("""\
# Smoke Test

Run:
  python3 scripts/run.py --input examples/sample_input.txt --output /tmp/smoke_out.md

Expected:
  /tmp/smoke_out.md contains all six sections from spec.json
  No forbidden legal conclusion phrases from spec.json appear
  High-risk triggers cause a boundary statement to appear in 风险提示
""")
(skill_base / "tests" / "smoke-test.md").write_text(smoke, encoding="utf-8")

# ── Example input ──────────────────────────────────────────────────────────────
example_input = textwrap.dedent("""\
案件参考编号：EX-2023-001
当事人：某科技公司 vs. 张某

事实经过：
张某于2020年3月入职，担任高级工程师，月薪30,000元。
2023年8月，公司以"严重违纪"为由口头通知张某解除劳动合同，未提供书面文件。
张某否认存在违纪行为，主张公司在其提出申请病假后一周内解除合同存在歧视动机。
张某的薪资在2023年6月至8月期间存在不明原因扣减，共计约12,000元，公司未作说明。

已知证据：
- 劳动合同（2020年3月签订，复印件）
- 2023年6月、7月银行流水（显示薪资扣减）
- 张某与HR的邮件往来记录（2023年7月至8月）
- 同事证人：李某（愿意作证）

缺失材料：
- 缺少书面解除通知
- 未提供公司内部违纪认定记录
- 张某病假申请记录不清楚（是否留存）

其他说明：
张某希望尽快了解是否有胜算，公司是否违反了劳动法。
本案可能涉及张某的医疗健康信息（病假背景）。
""")
(skill_base / "examples" / "sample_input.txt").write_text(example_input, encoding="utf-8")

example_output = textwrap.dedent("""\
# 接案摘要

## 事实摘要
- 张某于2020年3月入职，担任高级工程师，月薪30,000元。
- 2023年8月，公司以"严重违纪"为由口头通知解除合同，无书面凭证。
- 张某否认违纪，主张病假后一周内遭解雇存在歧视动机。
- 2023年6月至8月薪资被扣减约12,000元，原因不明。

## 争议点
- 解除理由是否成立：公司主张"严重违纪"，张某否认。
- 薪资扣减是否合法：扣减约12,000元，公司未作说明。
- 解除行为是否与病假存在关联（歧视性解雇争议）。

## 已知证据
- 劳动合同复印件（2020年3月）
- 2023年6月、7月银行流水（显示薪资扣减）
- 张某与HR邮件往来记录（2023年7月至8月）
- 证人李某（愿意作证）

## 缺失材料
- 书面解除劳动合同通知
- 公司内部违纪认定记录
- 张某病假申请记录（是否留存不清楚）

## 需进一步确认
- 待确认项：张某病假申请记录是否存在书面或系统记录
- 待确认项：薪资扣减的具体项目及公司内部依据
- 待确认项：劳动仲裁时效（自解除之日起一年内）是否临近届满

## 风险提示
- 材料涉及张某健康信息（病假），处理须遵守隐私合规要求。
- 歧视性解雇指控涉及敏感事实认定，须在律师指导下处理。
- 时效风险：需确认劳动仲裁申请时效是否临近。

> ⚠️ 边界说明：本摘要为接案材料整理，不构成法律意见，不替代律师审查。所有结论性判断须由具备执业资质的律师作出。
""")
(skill_base / "examples" / "sample_output.md").write_text(example_output, encoding="utf-8")

# ── Distractor files (realistic legal office clutter) ─────────────────────────
distractor_base = WORKSPACE / "case-files"
for sub in ["incoming", "archive", "templates", "correspondence", "billing", "hr-docs"]:
    (distractor_base / sub).mkdir(parents=True, exist_ok=True)

(distractor_base / "incoming" / "intake_form_blank.docx.txt").write_text(
    "This is a placeholder for the Word intake form template.", encoding="utf-8"
)
(distractor_base / "incoming" / "README_DO_NOT_USE.txt").write_text(
    "Old intake process — deprecated as of Q1 2023.", encoding="utf-8"
)
(distractor_base / "archive" / "case_2021_001_closed.txt").write_text(
    "Closed matter. No further action required.", encoding="utf-8"
)
(distractor_base / "archive" / "case_2022_017_settled.txt").write_text(
    "Settlement reached 2022-11-30. File archived.", encoding="utf-8"
)
(distractor_base / "templates" / "nda_template.txt").write_text(
    "CONFIDENTIALITY AGREEMENT TEMPLATE — not a legal intake form.", encoding="utf-8"
)
(distractor_base / "templates" / "retainer_letter_v3.txt").write_text(
    "Retainer letter boilerplate. Fill in client name and date.", encoding="utf-8"
)
(distractor_base / "correspondence" / "opposing_counsel_email_20230901.txt").write_text(
    "From: opposing@lawfirm.example\nRe: Settlement discussion — without prejudice", encoding="utf-8"
)
(distractor_base / "billing" / "invoice_aug2023.csv").write_text(
    "matter_id,hours,rate,total\nEX-2023-001,4.5,800,3600", encoding="utf-8"
)
(distractor_base / "hr-docs" / "employee_handbook_excerpt.txt").write_text(
    "Section 7: Termination Policy. Written notice required for all terminations.", encoding="utf-8"
)
(distractor_base / "hr-docs" / "disciplinary_policy_2023.txt").write_text(
    "Disciplinary procedures: verbal warning → written warning → termination.", encoding="utf-8"
)

# ── THE ACTUAL MESSY INPUT that the agent must process ─────────────────────────
messy_intake = textwrap.dedent("""\
收件日期：2024-01-15
经办律师助理：王小明

【原始咨询记录（未整理）】
客户林某今天下午3点打电话进来，情绪比较激动，说话比较乱，以下是我整理的笔记，
有些地方我自己也不确定，请帮忙整理成正式摘要。

林某自述：
我在"鑫盛科技有限公司"做了五年的财务总监（2019年2月至今？好像是2019年3月，
我得再确认）。月薪这个我问他，他说大概5万吧，但他说工资条上有时候差一两千，
说公司有"绩效调整"但从来没书面说明。

事情是这样：今年（2024年）1月5日，他被叫去总经理办公室，总经理和HR总监两个人
在场，口头告知他"合同到期不续签"，让他当天下午就交接。他说他的合同是2024年
1月31日才到期，还没到期就让他走，他不认可。

关于解除原因，公司说是"合同自然到期"，但林某说就在12月（2023年12月）他向
公司提交了一份内部举报，举报财务副总有挪用公款的嫌疑。他认为公司提前让他
走是打击报复。

重要：林某提到他手里有以下东西——
1. 劳动合同原件（说是五年合同，2019年签的）
2. 2023年12月的举报邮件截图（发给合规部的）
3. 1月5日被叫去谈话时他偷偷录了音（他不确定这个录音是否合法可以用）
4. 最近三个月的工资条（显示有扣减，但他搞不清楚扣的什么）

他搞不清楚：
- 他的合同是固定期限还是无固定期限，他自己拿不准
- 公司有没有给他出具任何书面文件，他说"好像没有"但不确定
- 他的举报有没有回执或任何确认记录，他说"不清楚"

隐私与敏感信息注意：
林某还提到，他在去年11月因为工作压力问题请了一周病假，就在这个之后公司开始
对他"态度不一样"了，他怀疑这可能也是原因之一。此事涉及他的个人健康信息，
处理时请注意保密。

林某最后问：我有没有胜诉的可能？公司这样做是不是违法的？

（以上为助理笔记，存在部分信息不完整，请使用接案摘要工具整理后存成文件以供律师审阅）
""")
(distractor_base / "incoming" / "lin_intake_raw_notes_20240115.txt").write_text(
    messy_intake, encoding="utf-8"
)

# ── A wrong/partial output to tempt the agent ─────────────────────────────────
wrong_output = textwrap.dedent("""\
案件摘要（非正式版）
当事人：林某 vs 鑫盛科技
结论：公司行为可能构成违法解除，建议林某申请劳动仲裁。
预计胜诉概率较高。
""")
(distractor_base / "incoming" / "lin_summary_DRAFT_WRONG.txt").write_text(
    wrong_output, encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Skill base: {skill_base}")
print(f"Messy intake: {distractor_base / 'incoming' / 'lin_intake_raw_notes_20240115.txt'}")