#!/usr/bin/env python3
"""Start a new round in an existing One Person Company OS workspace."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    emit_runtime_report,
    load_role_specs,
    load_state,
    now_string,
    preflight_status,
    print_step,
    render_workspace,
    role_spec,
    round_id_now,
    save_state,
    state_path,
    write_record,
)
from localization import normalize_round_status, pick_text, round_status_label


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="启动一个新回合。")
    parser.add_argument("company_dir", help="公司工作区目录")
    parser.add_argument("--round-name", required=True, help="回合名称")
    parser.add_argument("--goal", required=True, help="回合目标")
    parser.add_argument("--owner", default="control-tower", help="负责角色 id")
    parser.add_argument("--artifact", default="待定义", help="关键产物")
    parser.add_argument("--next-action", default="开始执行第一个最小动作", help="下一步最短动作")
    parser.add_argument("--success-criteria", default="关键产物完成并可判断下一步", help="完成标准")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    company_dir = Path(args.company_dir).expanduser().resolve()
    state = load_state(company_dir)
    language = state.get("language", "zh-CN")
    if args.artifact == "待定义" and language == "en-US":
        args.artifact = "Undefined"
    if args.next_action == "开始执行第一个最小动作" and language == "en-US":
        args.next_action = "Start the first minimum action"
    if args.success_criteria == "关键产物完成并可判断下一步" and language == "en-US":
        args.success_criteria = "The key artifact is completed and the next move can be judged"

    print_step(1, 5, "模式判定", language=language)
    print_step(2, 5, "preflight 与保存策略检查", language=language)
    runtime = preflight_status(company_dir, language=language)
    if not runtime["runnable"]:
        parser.error(f"runtime not runnable: {runtime['runtime_error']}")

    print_step(3, 5, "草案 / 变更提议 / 当前状态装载", status=pick_text(language, "已完成（加载当前状态）", "Completed (loaded current state)"), language=language)
    role_specs = load_role_specs()

    if args.owner not in role_specs:
        parser.error(f"unknown role id: {args.owner}")

    round_id = round_id_now()
    owner_spec = role_spec(args.owner, role_specs, language)
    state["current_round"] = {
        "round_id": round_id,
        "name": args.round_name,
        "goal": args.goal,
        "status_id": normalize_round_status("已拆解"),
        "status": round_status_label("planned", language),
        "owner_role_id": args.owner,
        "owner_role_name": owner_spec["display_name"],
        "artifact": args.artifact,
        "blocker": pick_text(language, "无", "None"),
        "next_action": args.next_action,
        "success_criteria": args.success_criteria,
        "started_at": now_string(),
        "updated_at": now_string(),
    }
    state["current_bottleneck"] = args.goal

    print_step(4, 5, "执行与落盘", language=language)
    save_state(company_dir, state)
    render_workspace(company_dir, state)

    owner_name = state["current_round"]["owner_role_name"]
    record = write_record(
        company_dir,
        "推进日志",
        pick_text(language, "启动回合", "start-round"),
        pick_text(language, f"启动回合 {args.round_name}", f"Start round {args.round_name}"),
        [
            pick_text(language, f"- 回合编号: {round_id}", f"- Round ID: {round_id}"),
            pick_text(language, f"- 回合目标: {args.goal}", f"- Round Goal: {args.goal}"),
            pick_text(language, f"- 负责角色: {owner_name}", f"- Owner: {owner_name}"),
            pick_text(language, f"- 关键产物: {args.artifact}", f"- Key Artifact: {args.artifact}"),
            pick_text(language, f"- 下一步最短动作: {args.next_action}", f"- Shortest Next Action: {args.next_action}"),
        ],
    )

    print_step(5, 5, "验证与回报", language=language)
    emit_runtime_report(
        mode=pick_text(language, "启动回合", "Start Round"),
        phase="验证与回报",
        stage=state["stage_label"],
        round_name=args.round_name,
        role=owner_name,
        artifact=args.artifact,
        next_action=args.next_action,
        needs_confirmation=pick_text(language, "否", "No"),
        persistence_mode="script-execution",
        company_dir=company_dir,
        saved_paths=[
            company_dir / "09-本周唯一主目标.md",
            company_dir / "10-今日最短动作.md",
            company_dir / "04-产品与上线状态.md",
            record,
            state_path(company_dir),
        ],
        work_scope=[
            pick_text(language, "定义一个新的当前推进回合，并把负责人、目标和产物写清楚。", "Define a new execution round and make the owner, goal, and artifact explicit."),
            pick_text(language, "同步刷新本周主目标、今日动作和主工作面。", "Refresh the weekly goal, today's action, and the main work surfaces."),
            pick_text(language, "给出这回合的下一步最短动作。", "Set the shortest next action for this round."),
        ],
        non_scope=[
            pick_text(language, "不会同时启动多个当前回合。", "Do not start multiple current rounds at once."),
            pick_text(language, "不会跳过回合定义直接进入大段泛化建议输出。", "Do not skip round definition and jump straight into generic advisory output."),
        ],
        changes=[
            pick_text(language, f"已启动新回合：{args.round_name}。", f"Started a new round: {args.round_name}."),
            pick_text(language, f"已把负责人设为 {owner_name}，并写入关键产物与下一步动作。", f"Set the owner to {owner_name} and wrote the key artifact plus the next action."),
            pick_text(language, "已新增一条启动回合记录，方便后续审计和接力。", "Added a start-round record for later audit and handoff."),
        ],
        language=language,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
