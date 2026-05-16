#!/usr/bin/env python3
"""Generate numbered DOCX artifact documents for One Person Company OS."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    artifact_status_summary_markdown,
    display_path,
    emit_runtime_report,
    load_state,
    now_string,
    planned_docx_path,
    preflight_status,
    print_step,
    render_workspace,
    render_template,
    safe_document_name,
    save_state,
    stage_label,
    write_text,
    write_docx,
    write_record,
)
from localization import pick_text


CATEGORY_DIRS = {
    "delivery": "产物/01-实际交付",
    "software": "产物/02-软件与代码",
    "business": "产物/03-非软件与业务",
    "ops": "产物/04-部署与生产",
    "growth": "产物/05-上线与增长",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成带序号的正式 DOCX 产物。")
    parser.add_argument("company_dir", help="公司工作区目录")
    parser.add_argument("--title", required=True, help="产物标题")
    parser.add_argument("--artifact-type", default="关键产物", help="产物类型")
    parser.add_argument(
        "--category",
        choices=["auto", "delivery", "software", "business", "ops", "growth"],
        default="auto",
        help="产物目录分类",
    )
    parser.add_argument("--summary", default="待补充本次产物摘要", help="产物摘要")
    parser.add_argument("--objective", default="", help="本次产物目标，默认读取当前回合目标")
    parser.add_argument("--owner-role", default="", help="负责人，默认读取当前回合负责人")
    parser.add_argument("--scope-in", action="append", default=[], help="本次纳入范围，可重复")
    parser.add_argument("--scope-out", action="append", default=[], help="本次不纳入范围，可重复")
    parser.add_argument("--deliverable", action="append", default=[], help="交付物，可重复")
    parser.add_argument("--software-output", action="append", default=[], help="软件/代码产出，可重复")
    parser.add_argument("--non-software-output", action="append", default=[], help="非软件产出，可重复")
    parser.add_argument("--evidence", action="append", default=[], help="证据或路径，可重复")
    parser.add_argument("--deployment-item", action="append", default=[], help="部署资料项，可重复")
    parser.add_argument("--production-item", action="append", default=[], help="生产/运维资料项，可重复")
    parser.add_argument("--change", action="append", default=[], help="本次变化，可重复")
    parser.add_argument("--decision", action="append", default=[], help="关键决策，可重复")
    parser.add_argument("--risk", action="append", default=[], help="风险与待确认事项，可重复")
    parser.add_argument("--next-action", default="", help="下一步动作，默认读取当前回合")
    parser.add_argument("--output-dir", help="可选，自定义输出目录")
    return parser


def to_bullets(items: list[str], fallback: str) -> str:
    values = [item for item in items if item]
    if not values:
        values = [fallback]
    return "\n".join(f"- {item}" for item in values)


def resolve_category(requested: str, artifact_type: str, state: dict[str, object]) -> str:
    if requested != "auto":
        return requested

    stage_id = state["stage_id"]
    artifact_key = artifact_type.lower()
    if any(token in artifact_type for token in ("部署", "生产", "回滚", "运维")) or any(
        token in artifact_key for token in ("deploy", "ops", "production")
    ):
        return "ops"
    if any(token in artifact_type for token in ("代码", "软件", "工程", "测试")) or any(
        token in artifact_key for token in ("software", "code", "engineering", "qa")
    ):
        return "software"
    if stage_id in {"launch", "grow"} and any(token in artifact_type for token in ("增长", "上线", "转化")):
        return "growth"
    if any(token in artifact_type for token in ("方案", "培训", "咨询", "销售", "运营", "研究", "材料")):
        return "business"
    return "delivery"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    company_dir = Path(args.company_dir).expanduser().resolve()
    state = load_state(company_dir)
    language = state.get("language", "zh-CN")
    if args.artifact_type == "关键产物" and language == "en-US":
        args.artifact_type = "Key Artifact"
    if args.summary == "待补充本次产物摘要" and language == "en-US":
        args.summary = "Add the summary for this artifact"

    print_step(1, 5, "模式判定", language=language)
    print_step(2, 5, "preflight 与保存策略检查", language=language)
    runtime = preflight_status(company_dir, language=language)
    if not runtime["runnable"]:
        parser.error(f"runtime not runnable: {runtime['runtime_error']}")

    print_step(3, 5, "草案 / 变更提议 / 当前状态装载", status=pick_text(language, "已完成（装载当前状态与文档参数）", "Completed (loaded the current state and document parameters)"), language=language)
    current_round = state["current_round"]
    owner_role = args.owner_role or current_round.get("owner_role_name", pick_text(language, "待指定", "Unassigned"))
    objective = args.objective or current_round.get("goal", pick_text(language, "待定义", "Undefined"))
    next_action = args.next_action or current_round.get("next_action", pick_text(language, "待定义", "Undefined"))
    category = resolve_category(args.category, args.artifact_type, state)

    values = {
        "LANGUAGE": language,
        "COMPANY_NAME": state["company_name"],
        "PRODUCT_NAME": state["product_name"],
        "STAGE_LABEL": stage_label(state["stage_id"], language),
        "CURRENT_ROUND_NAME": current_round.get("name", pick_text(language, "待定义", "Undefined")),
        "ROUND_GOAL": current_round.get("goal", pick_text(language, "待定义", "Undefined")),
        "ROUND_STATUS": current_round.get("status", pick_text(language, "待定义", "Undefined")),
        "ARTIFACT_TITLE": args.title,
        "ARTIFACT_TYPE": args.artifact_type,
        "ARTIFACT_OWNER": owner_role,
        "ARTIFACT_OBJECTIVE": objective,
        "ARTIFACT_SUMMARY": args.summary,
        "ARTIFACT_SCOPE_IN": to_bullets(args.scope_in, pick_text(language, "待补充本次纳入范围", "Add the in-scope items for this run")),
        "ARTIFACT_SCOPE_OUT": to_bullets(args.scope_out, pick_text(language, "待补充本次不纳入范围", "Add the out-of-scope items for this run")),
        "ARTIFACT_DELIVERABLES": to_bullets(args.deliverable, pick_text(language, "待补充交付物", "Add the deliverables")),
        "ARTIFACT_SOFTWARE_OUTPUTS": to_bullets(args.software_output, pick_text(language, "如为软件产品，请补齐代码、脚本、接口、配置或自动化产出", "For software work, add code, scripts, interfaces, configuration, or automation outputs")),
        "ARTIFACT_NON_SOFTWARE_OUTPUTS": to_bullets(
            args.non_software_output,
            pick_text(language, "如为非软件产品，请补齐方案、培训材料、研究成果、销售材料或执行清单", "For non-software work, add plans, training materials, research output, sales collateral, or execution checklists"),
        ),
        "ARTIFACT_EVIDENCE": to_bullets(args.evidence, pick_text(language, "待补充文件路径、仓库地址、演示链接或其他验收证据", "Add file paths, repository links, demo links, or other acceptance evidence")),
        "ARTIFACT_DEPLOYMENT_ITEMS": to_bullets(
            args.deployment_item,
            pick_text(language, "如已进入上线/运营，请补齐部署目标、发布窗口、回滚方案与配置变更", "If this work is in launch or operate stage, add deployment targets, release windows, rollback plans, and configuration changes"),
        ),
        "ARTIFACT_PRODUCTION_ITEMS": to_bullets(
            args.production_item,
            pick_text(language, "如已进入上线/运营，请补齐监控、告警、值守、事故响应和生产观察项", "If this work is in launch or operate stage, add monitoring, alerting, on-call, incident response, and production checks"),
        ),
        "ARTIFACT_CHANGES": to_bullets(args.change, pick_text(language, "待补充本次变化", "Add the changes in this run")),
        "ARTIFACT_DECISIONS": to_bullets(args.decision, pick_text(language, "待补充关键决策", "Add the key decisions")),
        "ARTIFACT_RISKS": to_bullets(args.risk, pick_text(language, "待补充风险与待确认事项", "Add risks and pending confirmations")),
        "ARTIFACT_NEXT_ACTION": next_action,
        "ARTIFACT_STATUS": pick_text(language, "交付就绪版", "Delivery-Ready"),
        "ARTIFACT_PROGRESS_SUMMARY": pick_text(language, "本文件已经进入可交付版本，后续如有改动，直接继续在当前正式文件内精修即可。", "This document is now in a delivery-ready state. Continue refining the same formal file directly if more changes are needed."),
        "ARTIFACT_MISSING_ITEMS": to_bullets(
            args.risk,
            pick_text(language, "如仍有空缺，请补齐证据、负责人或验收结论", "If anything is still missing, complete the evidence, owner, or acceptance conclusion"),
        ),
        "ARTIFACT_FILE_PATH": pick_text(language, "将在落盘后回填", "Will be filled after persistence"),
    }

    print_step(4, 5, "执行与落盘", language=language)
    base_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else company_dir
    output_dir = base_dir / CATEGORY_DIRS[category]
    output_path = planned_docx_path(output_dir, args.title, completed=True)
    output_path_display = display_path(output_path, company_dir)
    values["ARTIFACT_FILE_PATH"] = output_path_display
    rendered = render_template("artifact-docx-ready-template.md", values)
    write_docx(output_path, rendered, title=args.title)
    current_artifact = str(current_round.get("artifact", ""))
    if current_artifact in {
        pick_text(language, "待定义", "Undefined"),
        "",
    } or safe_document_name(args.title) in safe_document_name(current_artifact):
        current_round["artifact"] = output_path_display
        current_round["updated_at"] = now_string()
        save_state(company_dir, state)
        render_workspace(company_dir, state)
    write_text(company_dir / "delivery" / "02-交付目录总览.md", artifact_status_summary_markdown(company_dir, language))

    record = write_record(
        company_dir,
        "推进日志",
        pick_text(language, "文档产物", "artifact-document"),
        pick_text(language, f"生成正式交付文档 {args.title}", f"Generated formal deliverable document {args.title}"),
        [
            pick_text(language, f"- 产物标题: {args.title}", f"- Artifact Title: {args.title}"),
            pick_text(language, f"- 产物类型: {args.artifact_type}", f"- Artifact Type: {args.artifact_type}"),
            pick_text(language, f"- 输出分类: {category}", f"- Output Category: {category}"),
            pick_text(language, f"- 当前阶段: {stage_label(state['stage_id'], language)}", f"- Current Stage: {stage_label(state['stage_id'], language)}"),
            pick_text(language, f"- 当前回合: {current_round.get('name', pick_text(language, '待定义', 'Undefined'))}", f"- Current Round: {current_round.get('name', pick_text(language, '待定义', 'Undefined'))}"),
            pick_text(language, f"- 负责人: {owner_role}", f"- Owner: {owner_role}"),
            pick_text(language, f"- 实际文件: {output_path.name}", f"- Output File: {output_path.name}"),
            pick_text(language, f"- 下一步最短动作: {next_action}", f"- Shortest Next Action: {next_action}"),
        ],
    )

    print_step(5, 5, "验证与回报", language=language)
    emit_runtime_report(
        mode=pick_text(language, "生成正式交付文档", "Generate Formal Deliverable Document"),
        phase="验证与回报",
        stage=stage_label(state["stage_id"], language),
        round_name=current_round.get("name", pick_text(language, "待定义", "Undefined")),
        role=owner_role,
        artifact=f"{args.title} DOCX",
        next_action=next_action,
        needs_confirmation=pick_text(language, "否", "No"),
        persistence_mode="script-execution",
        company_dir=company_dir,
        saved_paths=[output_path, company_dir / "delivery" / "02-交付目录总览.md", record],
        work_scope=[
            pick_text(language, "为关键产物生成带序号的正式 DOCX 文件。", "Generate a numbered formal DOCX file for the key artifact."),
            pick_text(language, "把软件产出、非软件产出、证据以及部署/生产资料写成可交付格式。", "Write software outputs, non-software outputs, evidence, and deployment or production material into a deliverable format."),
            pick_text(language, "将文档真实落盘到工作区，不再只生成 Markdown 草稿。", "Persist the document into the workspace instead of leaving it as a markdown-only draft."),
        ],
        non_scope=[
            pick_text(language, "不会在产物目录里再生成未编号的 Markdown 文件。", "Do not generate extra unnumbered markdown files inside the artifact directory."),
            pick_text(language, "不会把缺少实际证据的内容说成已经完成交付。", "Do not claim delivery is complete when actual evidence is missing."),
        ],
        changes=[
            pick_text(language, f"已生成正式 DOCX：{output_path.name}。", f"Generated a formal DOCX: {output_path.name}."),
            pick_text(language, "已把实际软件/非软件产出、证据、部署与生产资料纳入正式结构。", "Included real software or non-software outputs, evidence, and deployment or production material in the formal structure."),
            pick_text(language, "已新增一条文档产物生成记录，便于审计和回看。", "Added an artifact-generation record for auditing and later review."),
        ],
        language=language,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
