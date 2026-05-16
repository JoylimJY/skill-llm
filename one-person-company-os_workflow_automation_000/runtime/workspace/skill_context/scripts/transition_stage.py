#!/usr/bin/env python3
"""Transition the company to another stage."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    default_role_ids_for_stage,
    emit_runtime_report,
    load_role_specs,
    load_state,
    normalize_stage,
    now_string,
    preflight_status,
    print_step,
    render_workspace,
    role_spec,
    save_state,
    state_path,
    stage_label,
    write_record,
)
from localization import normalize_round_status, pick_text, round_status_label


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="切换公司阶段。")
    parser.add_argument("company_dir", help="公司工作区目录")
    parser.add_argument("--stage", required=True, help="新阶段")
    parser.add_argument("--reason", required=True, help="切换原因")
    parser.add_argument("--first-round-name", default="", help="新阶段首个回合名称")
    parser.add_argument("--first-round-goal", default="", help="新阶段首个回合目标")
    parser.add_argument("--first-round-owner", default="control-tower", help="新阶段首个回合负责人")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    company_dir = Path(args.company_dir).expanduser().resolve()
    state = load_state(company_dir)
    language = state.get("language", "zh-CN")

    print_step(1, 5, "模式判定", language=language)
    print_step(2, 5, "preflight 与保存策略检查", language=language)
    runtime = preflight_status(company_dir, language=language)
    if not runtime["runnable"]:
        parser.error(f"runtime not runnable: {runtime['runtime_error']}")

    print_step(3, 5, "草案 / 变更提议 / 当前状态装载", status=pick_text(language, "已完成（加载当前状态）", "Completed (loaded current state)"), language=language)
    role_specs = load_role_specs()
    new_stage_id = normalize_stage(args.stage)

    state["stage_id"] = new_stage_id
    state["stage_label"] = stage_label(new_stage_id, language)
    state["active_roles"] = default_role_ids_for_stage(new_stage_id)
    state["current_bottleneck"] = args.reason

    if args.first_round_name or args.first_round_goal:
        owner = args.first_round_owner
        if owner not in role_specs:
            parser.error(f"unknown role id: {owner}")
        owner_name = role_spec(owner, role_specs, language)["display_name"]
        state["current_round"] = {
            "round_id": pick_text(language, f"{state['stage_label']}-首回合", f"{state['stage_label']}-first-round"),
            "name": args.first_round_name or pick_text(language, "新阶段首回合", "First Round Of The New Stage"),
            "goal": args.first_round_goal or pick_text(language, "待定义", "Undefined"),
            "status_id": normalize_round_status("已拆解"),
            "status": round_status_label("planned", language),
            "owner_role_id": owner,
            "owner_role_name": owner_name,
            "artifact": pick_text(language, "待定义", "Undefined"),
            "blocker": pick_text(language, "无", "None"),
            "next_action": pick_text(language, "启动新阶段的第一个最小动作", "Start the first minimum action of the new stage"),
            "success_criteria": pick_text(language, "首个新阶段产物完成", "The first new-stage artifact is completed"),
            "started_at": now_string(),
            "updated_at": now_string(),
        }
    else:
        state["current_round"]["status_id"] = normalize_round_status("待定义")
        state["current_round"]["status"] = round_status_label("undefined", language)
        state["current_round"]["updated_at"] = now_string()

    print_step(4, 5, "执行与落盘", language=language)
    save_state(company_dir, state)
    render_workspace(company_dir, state)
    stage_saved_paths = [
        company_dir / "00-经营总盘.md",
        company_dir / "04-产品与上线状态.md",
        company_dir / "05-客户交付与回款.md",
        company_dir / "08-风险与关键决策.md",
        company_dir / "09-本周唯一主目标.md",
    ]
    if new_stage_id == "launch":
        stage_saved_paths.extend(
            [
                company_dir / "产物" / "04-部署与生产" / "01-部署与回滚清单.docx",
                company_dir / "产物" / "04-部署与生产" / "02-生产观测与告警清单.docx",
                company_dir / "产物" / "05-上线与增长" / "01-上线公告与反馈回收清单.docx",
            ]
        )
    elif new_stage_id == "operate":
        stage_saved_paths.extend(
            [
                company_dir / "产物" / "04-部署与生产" / "01-部署与回滚清单.docx",
                company_dir / "产物" / "04-部署与生产" / "02-生产观测与告警清单.docx",
                company_dir / "产物" / "04-部署与生产" / "03-事故响应与复盘记录.docx",
                company_dir / "产物" / "05-上线与增长" / "01-上线公告与反馈回收清单.docx",
            ]
        )
    elif new_stage_id == "grow":
        stage_saved_paths.extend(
            [
                company_dir / "产物" / "04-部署与生产" / "01-部署与回滚清单.docx",
                company_dir / "产物" / "04-部署与生产" / "02-生产观测与告警清单.docx",
                company_dir / "产物" / "05-上线与增长" / "01-增长实验与经营复盘.docx",
            ]
        )

    record = write_record(
        company_dir,
        "决策记录",
        pick_text(language, "阶段切换", "stage-transition"),
        pick_text(language, f"阶段切换到 {state['stage_label']}", f"Transitioned To {state['stage_label']}"),
        [
            pick_text(language, f"- 新阶段: {state['stage_label']}", f"- New Stage: {state['stage_label']}"),
            pick_text(language, f"- 切换原因: {args.reason}", f"- Transition Reason: {args.reason}"),
            pick_text(
                language,
                f"- 默认激活角色: {'、'.join(role_spec(role_id, role_specs, language)['display_name'] for role_id in state['active_roles'])}",
                f"- Default Active Roles: {', '.join(role_spec(role_id, role_specs, language)['display_name'] for role_id in state['active_roles'])}",
            ),
        ],
    )

    print_step(5, 5, "验证与回报", language=language)
    emit_runtime_report(
        mode=pick_text(language, "切换阶段", "Transition Stage"),
        phase="验证与回报",
        stage=state["stage_label"],
        round_name=state["current_round"]["name"],
        role=state["current_round"]["owner_role_name"],
        artifact=pick_text(language, "阶段切换记录", "Stage transition record"),
        next_action=state["current_round"]["next_action"],
        needs_confirmation=pick_text(language, "否", "No"),
        persistence_mode="script-execution",
        company_dir=company_dir,
        saved_paths=stage_saved_paths + [record, state_path(company_dir)],
        work_scope=[
            pick_text(language, "切换公司当前阶段，并刷新默认激活角色。", "Transition the company into a new stage and refresh the default active roles."),
            pick_text(language, "如果指定了新阶段首回合，就同步创建首回合定义。", "If a first round for the new stage was provided, create it in the same run."),
            pick_text(language, "同步刷新该阶段要求的实际交付文档、部署资料和生产资料。", "Refresh the stage-specific deliverable documents, deployment materials, and production materials."),
            pick_text(language, "把阶段切换的理由与结果写入工作区。", "Write the transition reason and outcome into the workspace."),
        ],
        non_scope=[
            pick_text(language, "不会在没有阶段变更理由的情况下硬切阶段。", "Do not force a stage transition without a reason."),
            pick_text(language, "不会保留旧阶段的错误角色配置不更新。", "Do not leave stale role activation from the previous stage."),
        ],
        changes=[
            pick_text(language, f"已把当前阶段切换为 {state['stage_label']}。", f"Transitioned the company stage to {state['stage_label']}."),
            pick_text(language, f"当前瓶颈更新为 {args.reason}。", f"Updated the bottleneck to {args.reason}."),
            pick_text(language, f"当前回合现为 {state['current_round']['name']}。", f"The current round is now {state['current_round']['name']}."),
        ],
        language=language,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
