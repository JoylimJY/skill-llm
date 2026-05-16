#!/usr/bin/env python3
"""Update the current round state."""

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
    save_state,
    state_path,
    write_record,
)
from localization import pick_text, round_status_label, normalize_round_status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="更新当前回合。")
    parser.add_argument("company_dir", help="公司工作区目录")
    parser.add_argument("--status", help="新状态")
    parser.add_argument("--owner", help="新负责角色 id")
    parser.add_argument("--artifact", help="关键产物")
    parser.add_argument("--blocker", help="当前阻塞")
    parser.add_argument("--next-action", help="下一步最短动作")
    parser.add_argument("--success-criteria", help="完成标准")
    parser.add_argument("--note", default="", help="更新说明")
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
    current_round = state["current_round"]

    if args.owner:
        if args.owner not in role_specs:
            parser.error(f"unknown role id: {args.owner}")
        current_round["owner_role_id"] = args.owner
        current_round["owner_role_name"] = role_spec(args.owner, role_specs, language)["display_name"]
    if args.status:
        current_round["status_id"] = normalize_round_status(args.status)
        current_round["status"] = round_status_label(current_round["status_id"], language)
    if args.artifact:
        current_round["artifact"] = args.artifact
    if args.blocker is not None:
        current_round["blocker"] = args.blocker
    if args.next_action:
        current_round["next_action"] = args.next_action
    if args.success_criteria:
        current_round["success_criteria"] = args.success_criteria

    current_round["updated_at"] = now_string()
    if args.blocker:
        state["current_bottleneck"] = args.blocker

    if "status_id" not in current_round:
        current_round["status_id"] = normalize_round_status(current_round.get("status", "待定义"))
        current_round["status"] = round_status_label(current_round["status_id"], language)

    print_step(4, 5, "执行与落盘", language=language)
    save_state(company_dir, state)
    render_workspace(company_dir, state)

    lines = [
        pick_text(language, f"- 回合编号: {current_round['round_id']}", f"- Round ID: {current_round['round_id']}"),
        pick_text(language, f"- 当前状态: {current_round['status']}", f"- Current Status: {current_round['status']}"),
        pick_text(language, f"- 负责角色: {current_round['owner_role_name']}", f"- Owner: {current_round['owner_role_name']}"),
        pick_text(language, f"- 当前阻塞: {current_round['blocker']}", f"- Current Blocker: {current_round['blocker']}"),
        pick_text(language, f"- 下一步最短动作: {current_round['next_action']}", f"- Shortest Next Action: {current_round['next_action']}"),
    ]
    if args.note:
        lines.append(pick_text(language, f"- 更新说明: {args.note}", f"- Update Note: {args.note}"))
    record = write_record(company_dir, "推进日志", pick_text(language, "回合更新", "round-update"), pick_text(language, f"回合更新 {current_round['name']}", f"Round Update {current_round['name']}"), lines)

    print_step(5, 5, "验证与回报", language=language)
    emit_runtime_report(
        mode=pick_text(language, "推进回合", "Advance Round"),
        phase="验证与回报",
        stage=state["stage_label"],
        round_name=current_round["name"],
        role=current_round["owner_role_name"],
        artifact=current_round["artifact"],
        next_action=current_round["next_action"],
        needs_confirmation=pick_text(language, "是", "Yes") if current_round["status_id"] == "needs-decision" else pick_text(language, "否", "No"),
        persistence_mode="script-execution",
        company_dir=company_dir,
        saved_paths=[
            company_dir / "09-本周唯一主目标.md",
            company_dir / "10-今日最短动作.md",
            company_dir / "00-经营总盘.md",
            record,
            state_path(company_dir),
        ],
        work_scope=[
            pick_text(language, "更新当前回合的状态、负责人、阻塞或下一步动作。", "Update the current round status, owner, blocker, or next action."),
            pick_text(language, "把变化真实写回经营总盘、本周目标和今日动作。", "Write the changes back into the dashboard, weekly goal, and today's action."),
            pick_text(language, "明确这次更新后是否需要创始人确认。", "State clearly whether founder confirmation is required after this update."),
        ],
        non_scope=[
            pick_text(language, "不会重建整套公司设计。", "Do not rebuild the whole company design in this step."),
            pick_text(language, "不会把旧状态留在工作区里不更新。", "Do not leave stale round state in the workspace."),
        ],
        changes=[
            pick_text(language, f"已把当前回合状态更新为 {current_round['status']}。", f"Updated the current round status to {current_round['status']}."),
            pick_text(language, f"当前阻塞为 {current_round['blocker']}。", f"The current blocker is now {current_round['blocker']}."),
            pick_text(language, f"下一步最短动作已更新为 {current_round['next_action']}。", f"Updated the shortest next action to {current_round['next_action']}."),
        ],
        language=language,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
