#!/usr/bin/env python3
"""Persist a checkpoint for the current company workspace state."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import emit_runtime_report, load_state, now_string, preflight_status, print_step, render_workspace, save_state, state_path, write_record
from localization import pick_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="把当前公司状态保存为一个检查点。")
    parser.add_argument("company_dir", help="公司工作区目录")
    parser.add_argument("--reason", required=True, help="为什么要保存这个检查点")
    parser.add_argument("--artifact", help="当前关键产物，默认读取当前回合")
    parser.add_argument("--next-action", help="下一步最短动作，默认读取当前回合")
    parser.add_argument("--note", default="", help="补充说明")
    parser.add_argument("--needs-founder-approval", action="store_true", help="是否需要创始人确认")
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
    current_round = state["current_round"]
    artifact = args.artifact or current_round.get("artifact", pick_text(language, "待定义", "Undefined"))
    next_action = args.next_action or current_round.get("next_action", pick_text(language, "待定义", "Undefined"))

    state["last_checkpoint"] = {
        "saved_at": now_string(),
        "reason": args.reason,
        "artifact": artifact,
        "next_action": next_action,
        "needs_founder_approval": args.needs_founder_approval,
        "note": args.note,
    }

    print_step(4, 5, "执行与落盘", language=language)
    save_state(company_dir, state)
    render_workspace(company_dir, state)
    lines = [
        pick_text(language, f"- 保存时间: {state['last_checkpoint']['saved_at']}", f"- Saved At: {state['last_checkpoint']['saved_at']}"),
        pick_text(language, f"- 当前阶段: {state['stage_label']}", f"- Current Stage: {state['stage_label']}"),
        pick_text(language, f"- 当前回合: {current_round['name']}", f"- Current Round: {current_round['name']}"),
        pick_text(language, f"- 当前状态: {current_round['status']}", f"- Current Status: {current_round['status']}"),
        pick_text(language, f"- 当前关键产物: {artifact}", f"- Current Key Artifact: {artifact}"),
        pick_text(language, f"- 当前阻塞: {current_round['blocker']}", f"- Current Blocker: {current_round['blocker']}"),
        pick_text(language, f"- 下一步最短动作: {next_action}", f"- Shortest Next Action: {next_action}"),
        pick_text(language, f"- 保存原因: {args.reason}", f"- Save Reason: {args.reason}"),
        pick_text(language, f"- 是否需要创始人确认: {'是' if args.needs_founder_approval else '否'}", f"- Needs Founder Approval: {'Yes' if args.needs_founder_approval else 'No'}"),
    ]
    if args.note:
        lines.append(pick_text(language, f"- 备注: {args.note}", f"- Note: {args.note}"))
    checkpoint = write_record(company_dir, "检查点", pick_text(language, "检查点", "checkpoint"), pick_text(language, f"检查点 {current_round['name']}", f"Checkpoint {current_round['name']}"), lines)

    print_step(5, 5, "验证与回报", language=language)
    emit_runtime_report(
        mode=pick_text(language, "保存检查点", "Save Checkpoint"),
        phase="验证与回报",
        stage=state["stage_label"],
        round_name=current_round["name"],
        role=current_round["owner_role_name"],
        artifact=artifact,
        next_action=next_action,
        needs_confirmation=pick_text(language, "是", "Yes") if args.needs_founder_approval else pick_text(language, "否", "No"),
        persistence_mode="script-execution",
        company_dir=company_dir,
        saved_paths=[
            checkpoint,
            company_dir / "00-经营总盘.md",
            company_dir / "10-今日最短动作.md",
            state_path(company_dir),
        ],
        work_scope=[
            pick_text(language, "把当前阶段、当前回合和下一步动作保存成一个可恢复检查点。", "Save the current stage, current round, and next action as a recoverable checkpoint."),
            pick_text(language, "把检查点理由与备注写入记录文件。", "Write the checkpoint reason and note into the record file."),
            pick_text(language, "确认这次检查点是否需要创始人进一步拍板。", "State whether this checkpoint still needs founder approval."),
        ],
        non_scope=[
            pick_text(language, "不会只在聊天里说已保存而不落盘。", "Do not claim the checkpoint was saved without persisting it."),
            pick_text(language, "不会丢失当前回合的关键上下文。", "Do not lose the critical current-round context."),
        ],
        changes=[
            pick_text(language, f"已保存新的检查点，原因是：{args.reason}。", f"Saved a new checkpoint for this reason: {args.reason}."),
            pick_text(language, f"检查点覆盖当前关键产物：{artifact}。", f"The checkpoint now covers this key artifact: {artifact}."),
            pick_text(language, f"下一步最短动作记录为：{next_action}。", f"The checkpoint records this shortest next action: {next_action}."),
        ],
        language=language,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
