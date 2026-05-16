#!/usr/bin/env python3
"""Initialize a Chinese-first One Person Company OS workspace."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    default_role_ids_for_stage,
    emit_runtime_report,
    normalize_stage,
    now_string,
    preflight_status,
    print_step,
    render_workspace,
    safe_workspace_name,
    save_state,
    state_path,
    stage_label,
)
from localization import normalize_language, pick_text, round_status_label
from state_v3 import default_state_v3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a One Person Company OS workspace.")
    parser.add_argument("company_name", help="公司名称")
    parser.add_argument("--path", required=True, help="工作区父目录")
    parser.add_argument("--product-name", default="未命名产品", help="产品名称")
    parser.add_argument("--stage", default="验证期", help="当前阶段，如 验证期、构建期、上线期")
    parser.add_argument("--target-user", default="待确认用户", help="目标用户")
    parser.add_argument("--core-problem", default="待确认核心问题", help="核心问题")
    parser.add_argument("--product-pitch", default="待补充产品一句话定义", help="产品一句话定义")
    parser.add_argument("--company-goal", default="先跑通最小闭环并拿到第一轮真实反馈", help="当前主目标")
    parser.add_argument("--current-bottleneck", default="尚未定义首个回合", help="当前瓶颈")
    parser.add_argument("--language", default="auto", help="工作语言，如 zh-CN、en-US 或 auto")
    parser.add_argument("--force", action="store_true", help="允许写入已存在目录")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    language = normalize_language(
        args.language,
        args.company_name,
        args.product_name,
        args.stage,
        args.target_user,
        args.core_problem,
        args.product_pitch,
    )
    if args.product_name == "未命名产品" and language == "en-US":
        args.product_name = "Untitled Product"
    if args.target_user == "待确认用户" and language == "en-US":
        args.target_user = "Target user to be confirmed"
    if args.core_problem == "待确认核心问题" and language == "en-US":
        args.core_problem = "Core problem to be confirmed"
    if args.product_pitch == "待补充产品一句话定义" and language == "en-US":
        args.product_pitch = "Add the one-line product pitch"
    if args.company_goal == "先跑通最小闭环并拿到第一轮真实反馈" and language == "en-US":
        args.company_goal = "Ship the smallest useful loop and collect the first real feedback"
    if args.current_bottleneck == "尚未定义首个回合" and language == "en-US":
        args.current_bottleneck = "The first round has not been defined yet"

    print_step(1, 5, "模式判定", language=language)
    stage_id = normalize_stage(args.stage)
    root = Path(args.path).expanduser().resolve()
    company_dir = root / safe_workspace_name(args.company_name)
    if company_dir.exists() and not args.force:
        parser.error(f"target already exists: {company_dir}")

    print_step(2, 5, "preflight 与保存策略检查", language=language)
    runtime = preflight_status(company_dir, language=language)
    if not runtime["runnable"]:
        parser.error(f"runtime not runnable: {runtime['runtime_error']}")
    if not runtime["writable"]:
        parser.error(f"target not writable: {runtime['writable_target']}")

    print_step(
        3,
        5,
        "草案 / 变更提议 / 当前状态装载",
        status=pick_text(language, "已完成（组装初始状态）", "Completed (assembled the initial state)"),
        language=language,
    )
    active_roles = default_role_ids_for_stage(stage_id)
    current_round = {
        "round_id": pick_text(language, "未启动", "Not Started"),
        "name": pick_text(language, "未启动", "Not Started"),
        "goal": pick_text(language, "定义本周唯一结果", "Define the single weekly outcome"),
        "status_id": "undefined",
        "status": round_status_label("undefined", language),
        "owner_role_id": active_roles[1] if len(active_roles) > 1 else active_roles[0],
        "owner_role_name": pick_text(language, "总控台", "Control Tower"),
        "artifact": pick_text(language, "经营总盘与主工作面", "Operating dashboard and main work surfaces"),
        "blocker": args.current_bottleneck,
        "next_action": pick_text(language, "先定义今天最短动作", "Define the shortest action for today"),
        "success_criteria": pick_text(language, "主工作面可直接进入推进", "The main work surfaces are ready for execution"),
        "started_at": now_string(),
        "updated_at": now_string(),
    }
    state = default_state_v3(
        company_name=args.company_name,
        product_name=args.product_name,
        language=language,
        target_user=args.target_user,
        core_problem=args.core_problem,
        product_pitch=args.product_pitch,
        company_goal=args.company_goal,
        current_bottleneck=args.current_bottleneck,
        stage_id=stage_id,
        active_roles=active_roles,
        current_round=current_round,
    )

    print_step(4, 5, "执行与落盘", language=language)
    save_state(company_dir, state)
    render_workspace(company_dir, state)

    print_step(5, 5, "验证与回报", language=language)
    emit_runtime_report(
        mode="创建公司" if language == "zh-CN" else "Create Company",
        phase="验证与回报",
        stage=stage_label(stage_id, language),
        round_name=state["current_round"]["name"],
        role=pick_text(language, "总控台", "Control Tower"),
        artifact=pick_text(language, "经营总盘", "Operating dashboard"),
        next_action=pick_text(language, "先进入主工作面，继续收敛价值承诺、产品和成交路径", "Enter the main work surfaces and continue tightening the offer, product, and revenue path"),
        needs_confirmation=pick_text(language, "否", "No"),
        persistence_mode="script-execution",
        company_dir=company_dir,
        saved_paths=[
            company_dir / "00-经营总盘.md",
            company_dir / "01-创始人约束.md",
            company_dir / "02-价值承诺与报价.md",
            company_dir / "03-机会与成交管道.md",
            company_dir / "04-产品与上线状态.md",
            company_dir / "05-客户交付与回款.md",
            company_dir / "角色智能体" / "角色清单.md",
            company_dir / "产物" / "01-实际交付" / "01-实际产出总表.docx",
            state_path(company_dir),
        ],
        work_scope=[
            pick_text(language, "创建一人公司经营工作区与 v3 状态文件。", "Create the one-person-company operating workspace and the v3 state file."),
            pick_text(language, "直接生成经营总盘、价值承诺、成交管道、产品状态、交付回款等主工作面。", "Generate the main work surfaces for the dashboard, offer, revenue pipeline, product status, and delivery plus cash."),
            pick_text(language, "明确这次是否已真实保存以及下一步怎么继续。", "Explain clearly what was persisted and what should happen next."),
        ],
        non_scope=[
            pick_text(language, "不会替创始人自动做高风险商业决策。", "Do not make high-risk business decisions on behalf of the founder."),
            pick_text(language, "不会跳过确认边界去伪造不存在的角色执行结果。", "Do not fake role execution outcomes by skipping approval boundaries."),
        ],
        changes=[
            pick_text(language, "已创建经营总盘、价值承诺、成交管道、产品状态、交付回款和当前状态文件。", "Created the operating dashboard, value offer, revenue pipeline, product status, delivery plus cash view, and current-state file."),
            pick_text(language, "已把工作区切到经营闭环模型，同时保留旧脚本兼容字段。", "Shifted the workspace to the business-loop model while keeping legacy script compatibility fields."),
            pick_text(language, "当前公司已进入可继续推进产品、成交、交付和回款的状态。", "The company workspace is now ready to advance product, sales, delivery, and cash collection."),
        ],
        language=language,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
