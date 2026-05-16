import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "skill-case-study-factory/scripts",
    "skill-case-study-factory/resources",
    "skill-case-study-factory/examples/ex01",
    "skill-case-study-factory/examples/ex02",
    "skill-case-study-factory/tests",
    "project_inbox/raw_notes",
    "project_inbox/attachments",
    "archive/2023/q3",
    "archive/2023/q4",
    "team_docs/marketing",
    "team_docs/engineering",
    "tmp_scratch",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

BASE = WORKSPACE / "skill-case-study-factory"

# ── resources/spec.json ──────────────────────────────────────────────────────
spec = {
    "version": "1.0.0",
    "required_sections": [
        "项目背景",
        "关键动作",
        "结果与指标",
        "经验总结",
        "可复用方法",
        "对外版本注意事项"
    ],
    "pending_marker": "待确认项",
    "anonymization_notice": "【保密提醒】本文档含脱敏信息，发布前请完成匿名化审核。",
    "script_signature": "## [case-study-factory v1.0.0]",
    "missing_field_placeholder": "【待确认】",
    "max_fabrication": 0,
    "rules": {
        "no_fabrication": True,
        "explicit_pending": True,
        "default_draft_first": True
    }
}
(BASE / "resources" / "spec.json").write_text(
    json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── resources/template.md ────────────────────────────────────────────────────
template_md = textwrap.dedent("""\
    ## [case-study-factory v1.0.0]

    【保密提醒】本文档含脱敏信息，发布前请完成匿名化审核。

    ---

    # {title}

    ## 项目背景

    {background}

    ## 关键动作

    {actions}

    ## 结果与指标

    {results}

    ## 经验总结

    {lessons}

    ## 可复用方法

    {reusable}

    ## 对外版本注意事项

    {external_notes}

    ---

    ## 待确认项

    {pending_items}
""")
(BASE / "resources" / "template.md").write_text(template_md, encoding="utf-8")

# ── scripts/run.py ────────────────────────────────────────────────────────────
run_py = textwrap.dedent(r'''
    #!/usr/bin/env python3
    """
    case-study-factory: run.py
    Usage:
        python3 run.py --input <input_file> --output <output_file>

    Reads a raw project debrief (Markdown), applies spec.json validation,
    fills template.md, and writes a structured case study draft.
    Missing required fields are flagged as 【待确认】 and collected in
    the "待确认项" section. The anonymization notice is always injected.
    """
    import argparse
    import json
    import re
    import sys
    from pathlib import Path

    SCRIPT_DIR = Path(__file__).parent
    BASE_DIR   = SCRIPT_DIR.parent
    SPEC_PATH  = BASE_DIR / "resources" / "spec.json"
    TMPL_PATH  = BASE_DIR / "resources" / "template.md"

    # ── field extraction heuristics ──────────────────────────────────────────
    FIELD_PATTERNS = {
        "title":          [r"(?:项目名称|title|project)[：:]\s*(.+)"],
        "background":     [r"(?:背景|background|项目背景)[：:]\s*([\s\S]+?)(?=\n#{1,3}\s|\n[a-zA-Z\u4e00-\u9fa5]+[：:]|\Z)"],
        "actions":        [r"(?:动作|actions?|关键动作|措施)[：:]\s*([\s\S]+?)(?=\n#{1,3}\s|\n[a-zA-Z\u4e00-\u9fa5]+[：:]|\Z)"],
        "results":        [r"(?:结果|results?|指标|成效)[：:]\s*([\s\S]+?)(?=\n#{1,3}\s|\n[a-zA-Z\u4e00-\u9fa5]+[：:]|\Z)"],
        "lessons":        [r"(?:经验|lessons?|总结|教训)[：:]\s*([\s\S]+?)(?=\n#{1,3}\s|\n[a-zA-Z\u4e00-\u9fa5]+[：:]|\Z)"],
        "reusable":       [r"(?:可复用|reusable|复用方法|方法论)[：:]\s*([\s\S]+?)(?=\n#{1,3}\s|\n[a-zA-Z\u4e00-\u9fa5]+[：:]|\Z)"],
        "external_notes": [r"(?:对外|external|注意事项|风险)[：:]\s*([\s\S]+?)(?=\n#{1,3}\s|\n[a-zA-Z\u4e00-\u9fa5]+[：:]|\Z)"],
    }

    def extract_fields(raw_text: str) -> dict:
        fields = {}
        for field, patterns in FIELD_PATTERNS.items():
            for pat in patterns:
                m = re.search(pat, raw_text, re.IGNORECASE | re.MULTILINE)
                if m:
                    fields[field] = m.group(1).strip()
                    break
        return fields

    def main():
        parser = argparse.ArgumentParser(description="case-study-factory runner")
        parser.add_argument("--input",  required=True, help="Path to raw input file")
        parser.add_argument("--output", required=True, help="Path to output case-study file")
        args = parser.parse_args()

        input_path  = Path(args.input)
        output_path = Path(args.output)

        if not input_path.exists():
            print(f"[ERROR] Input file not found: {input_path}", file=sys.stderr)
            sys.exit(1)

        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        template = TMPL_PATH.read_text(encoding="utf-8")
        raw = input_path.read_text(encoding="utf-8")

        fields = extract_fields(raw)

        pending = []
        section_keys = ["title", "background", "actions", "results",
                         "lessons", "reusable", "external_notes"]
        readable_names = {
            "title":          "项目名称",
            "background":     "项目背景",
            "actions":        "关键动作",
            "results":        "结果与指标",
            "lessons":        "经验总结",
            "reusable":       "可复用方法",
            "external_notes": "对外版本注意事项",
        }
        for key in section_keys:
            if key not in fields or not fields[key]:
                fields[key] = spec["missing_field_placeholder"]
                pending.append(f"- {readable_names[key]}：尚未提供，请补充后重新生成。")

        pending_block = "\n".join(pending) if pending else "（无待确认项）"

        output_text = template.format(
            title          = fields.get("title", spec["missing_field_placeholder"]),
            background     = fields.get("background", spec["missing_field_placeholder"]),
            actions        = fields.get("actions", spec["missing_field_placeholder"]),
            results        = fields.get("results", spec["missing_field_placeholder"]),
            lessons        = fields.get("lessons", spec["missing_field_placeholder"]),
            reusable       = fields.get("reusable", spec["missing_field_placeholder"]),
            external_notes = fields.get("external_notes", spec["missing_field_placeholder"]),
            pending_items  = pending_block,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")
        print(f"[OK] Case study written to: {output_path}")
        missing_count = len(pending)
        if missing_count:
            print(f"[WARN] {missing_count} field(s) missing — see 待确认项 section.")

    if __name__ == "__main__":
        main()
''')
(BASE / "scripts" / "run.py").write_text(run_py, encoding="utf-8")

# ── examples/ex01 ────────────────────────────────────────────────────────────
ex01_input = textwrap.dedent("""\
    项目名称：医院HIS系统升级迁移

    背景：某三甲医院的门诊挂号系统使用老旧HIS，响应慢，每天有大量超时投诉。

    动作：
    1. 对接新版云端HIS API
    2. 双轨并行运行2周
    3. 灰度切流至新系统

    结果：响应时间从8s降至1.2s，投诉量下降73%，迁移零数据丢失。

    经验：双轨并行是关键，避免了冷切换风险。

    可复用方法：灰度切流SOP已沉淀为团队标准流程。

    对外注意：不披露旧系统供应商名称，不公开具体医院名称。
""")
(BASE / "examples" / "ex01" / "input.md").write_text(ex01_input, encoding="utf-8")

ex01_output = textwrap.dedent("""\
    ## [case-study-factory v1.0.0]

    【保密提醒】本文档含脱敏信息，发布前请完成匿名化审核。

    ---

    # 医院HIS系统升级迁移

    ## 项目背景

    某三甲医院的门诊挂号系统使用老旧HIS，响应慢，每天有大量超时投诉。

    ## 关键动作

    1. 对接新版云端HIS API
    2. 双轨并行运行2周
    3. 灰度切流至新系统

    ## 结果与指标

    响应时间从8s降至1.2s，投诉量下降73%，迁移零数据丢失。

    ## 经验总结

    双轨并行是关键，避免了冷切换风险。

    ## 可复用方法

    灰度切流SOP已沉淀为团队标准流程。

    ## 对外版本注意事项

    不披露旧系统供应商名称，不公开具体医院名称。

    ---

    ## 待确认项

    （无待确认项）
""")
(BASE / "examples" / "ex01" / "output.md").write_text(ex01_output, encoding="utf-8")

# ── examples/ex02 (incomplete — shows pending items) ─────────────────────────
ex02_input = textwrap.dedent("""\
    项目名称：ICU监护数据平台建设

    背景：ICU监护设备数据孤岛，护士需手工录入，效率极低。

    动作：接入设备厂商SDK，开发数据聚合平台。

    # 结果尚未确认，请后续补充
""")
(BASE / "examples" / "ex02" / "input.md").write_text(ex02_input, encoding="utf-8")

# ── tests/smoke-test.md ──────────────────────────────────────────────────────
smoke_test = textwrap.dedent("""\
    # Smoke Test

    Run:
        python3 scripts/run.py --input examples/ex01/input.md --output /tmp/smoke_out.md

    Expected:
    - Exit code 0
    - /tmp/smoke_out.md contains all 6 required section headers
    - 待确认项 section present
    - 保密提醒 notice present
    - Script signature [case-study-factory v1.0.0] present
""")
(BASE / "tests" / "smoke-test.md").write_text(smoke_test, encoding="utf-8")

# ── MESSY RAW INPUT (the actual task input) ──────────────────────────────────
# Intentionally incomplete: missing "结果/results", "经验/lessons", "可复用方法/reusable"
raw_debrief = textwrap.dedent("""\
    # 内部复盘备忘录 — 患者档案数字化项目

    撰写人：王工
    日期：2024-11-18
    状态：草稿，未经审核

    =========================================

    项目名称：某大型综合医院患者纸质档案数字化改造

    背景：
    该医院共有纸质病历约120万份，存放于地下档案室，查阅依赖人工检索，
    平均每次调阅耗时45分钟。数字化改造目标是将全量档案录入电子系统，
    支持关键字检索，缩短调阅时间至5分钟以内。
    由于项目涉及患者隐私数据，合规要求极高，不得向第三方云服务上传原始数据。

    =========================================

    动作：
    - 采购本地OCR服务器（离线部署）
    - 与档案室团队联合建立扫描流水线，每日处理约3000份档案
    - 开发档案索引微服务，支持姓名、病历号、日期多维检索
    - 对所有操作人员进行HIPAA合规培训

    =========================================

    进展备注（非正式）：
    - OCR识别率数据还在统计中，预计下周出报告
    - 调阅时间改善数据：IT部门说已达标，但尚未正式测量
    - 用户满意度调研表还没回收完
    - 项目组还没有开总结会，经验教训尚待梳理

    =========================================

    风险与对外注意：
    - 不得披露具体医院名称及所在城市
    - 不得公开OCR供应商合同价格
    - 患者姓名、病历号等隐私字段在任何对外材料中必须脱敏处理

    =========================================

    附件（仅内部）：
    - scan_pipeline_design_v3.pdf
    - hipaa_training_records_2024.xlsx
    - ocr_accuracy_draft_report.docx  （未完稿）
""")
(WORKSPACE / "project_inbox" / "raw_notes" / "patient_archive_debrief.md").write_text(
    raw_debrief, encoding="utf-8"
)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = [
    ("archive/2023/q3/old_case_study.md",
     "# 旧案例（已归档）\n本文件已过期，请勿参考。\n"),
    ("archive/2023/q4/budget_summary.csv",
     "项目,金额\n档案数字化,250000\nHIS迁移,180000\n"),
    ("team_docs/marketing/brand_guidelines.txt",
     "品牌规范：不使用红色字体，标题使用黑体。\n"),
    ("team_docs/marketing/social_media_calendar.md",
     "# 2024社媒排期\n- 11月：医疗科技周\n- 12月：年终回顾\n"),
    ("team_docs/engineering/deployment_runbook.md",
     "# 部署手册\n1. 执行 ./deploy.sh\n2. 检查健康端点\n3. 回滚：./rollback.sh\n"),
    ("team_docs/engineering/incident_log_2024.txt",
     "2024-10-12 P2: 数据库连接超时，已修复。\n2024-11-01 P3: OCR队列积压，已清理。\n"),
    ("project_inbox/attachments/meeting_notes_nov5.txt",
     "会议记录 2024-11-05\n参与者：王工、李总、张医生\n主要讨论：扫描速度与质量平衡问题\n"),
    ("project_inbox/attachments/vendor_quote_REDACTED.txt",
     "供应商报价（已脱敏）：[REDACTED] 万元\n"),
    ("tmp_scratch/draft_title_ideas.txt",
     "标题备选：\n- 从纸山到数字海\n- 120万份病历的数字化之旅\n- 离线OCR的合规实践\n"),
    ("tmp_scratch/wip_notes.md",
     "TODO: 找王工确认OCR准确率\nTODO: 总结会定在12月初\n"),
    ("tmp_scratch/random_config.yaml",
     "server:\n  host: 192.168.1.100\n  port: 8080\ndebug: false\n"),
]
for rel_path, content in distractors:
    fpath = WORKSPACE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")

print("[gen_inputs] Workspace created successfully.")
print(f"  skill base : {BASE}")
print(f"  raw debrief: {WORKSPACE / 'project_inbox' / 'raw_notes' / 'patient_archive_debrief.md'}")