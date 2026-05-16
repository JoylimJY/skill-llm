#!/usr/bin/env python3
"""State model helpers for the business-loop version of One Person Company OS."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from localization import normalize_language, pick_text, round_status_label, stage_label


STATE_VERSION = "3.0"
STATE_PATH_PARTS = ("自动化", "当前状态.json")
STATE_FILE = Path(*STATE_PATH_PARTS)

PRODUCT_STATE_ORDER = (
    "idea",
    "defined",
    "prototype",
    "internal",
    "external",
    "launchable",
    "live",
)


def state_path(company_dir: Path) -> Path:
    return company_dir.joinpath(*STATE_PATH_PARTS)


def default_round(language: str, owner_role_id: str = "control-tower") -> dict[str, Any]:
    owner_name = pick_text(language, "总控台", "Control Tower")
    return {
        "round_id": pick_text(language, "未启动", "Not Started"),
        "name": pick_text(language, "未启动", "Not Started"),
        "goal": pick_text(language, "待定义", "Undefined"),
        "status_id": "undefined",
        "status": round_status_label("undefined", language),
        "owner_role_id": owner_role_id,
        "owner_role_name": owner_name,
        "artifact": pick_text(language, "待定义", "Undefined"),
        "blocker": pick_text(language, "无", "None"),
        "next_action": pick_text(language, "先确认本周唯一主目标", "Confirm the single weekly target first"),
        "success_criteria": pick_text(language, "本周主目标被明确并进入推进", "The weekly target is clear and execution has started"),
        "started_at": "",
        "updated_at": "",
    }


def default_state_v3(
    *,
    company_name: str,
    product_name: str,
    language: str,
    target_user: str = "",
    core_problem: str = "",
    product_pitch: str = "",
    company_goal: str = "",
    current_bottleneck: str = "",
    stage_id: str = "validate",
    active_roles: list[str] | None = None,
    current_round: dict[str, Any] | None = None,
) -> dict[str, Any]:
    language = normalize_language(language, company_name, product_name, product_pitch, target_user, core_problem)
    round_state = deepcopy(current_round) if current_round else default_round(language)
    primary_arena = arena_from_stage(stage_id)
    state = {
        "version": STATE_VERSION,
        "language": language,
        "company_name": company_name,
        "product_name": product_name,
        "founder": {
            "goal_mode": "validation",
            "time_budget": pick_text(language, "待确认", "To be confirmed"),
            "cash_pressure": pick_text(language, "待确认", "To be confirmed"),
            "strengths": [],
            "constraints": [],
            "working_mode": pick_text(language, "单人主控", "Solo control"),
        },
        "focus": {
            "primary_goal": company_goal or pick_text(language, "先跑通最小价值闭环", "Run the smallest value loop first"),
            "primary_bottleneck": current_bottleneck or pick_text(language, "还没有识别当前主瓶颈", "The primary bottleneck has not been identified yet"),
            "primary_arena": primary_arena,
            "today_action": round_state.get("next_action") or pick_text(language, "先定义今天最短动作", "Define the shortest action for today"),
            "week_outcome": round_state.get("goal") or pick_text(language, "先定义本周唯一结果", "Define the single weekly outcome"),
        },
        "offer": {
            "promise": product_pitch or pick_text(language, "待补充价值承诺", "Add the value promise"),
            "target_customer": target_user or pick_text(language, "待确认首批付费用户", "Confirm the first paying user"),
            "scenario": core_problem or pick_text(language, "待确认高频使用场景", "Confirm the high-frequency scenario"),
            "pricing": pick_text(language, "待设计", "To be designed"),
            "proof": [],
        },
        "pipeline": {
            "stage_summary": {
                "discovering": 0,
                "talking": 0,
                "trial": 0,
                "proposal": 0,
                "won": 0,
                "lost": 0,
            },
            "next_revenue_action": pick_text(language, "先补齐第一条真实成交动作", "Add the first real revenue action"),
            "opportunities": [],
        },
        "product": {
            "state": product_state_from_stage(stage_id),
            "current_version": pick_text(language, "v0.1 草案", "v0.1 draft"),
            "core_capability": [product_pitch] if product_pitch else [],
            "current_gap": [core_problem] if core_problem else [],
            "launch_blocker": current_bottleneck or pick_text(language, "待识别", "To be identified"),
            "repository": "",
            "launch_path": "",
        },
        "delivery": {
            "active_customers": 0,
            "delivery_status": pick_text(language, "还没有成交客户", "No signed customers yet"),
            "blocking_issue": pick_text(language, "无", "None"),
            "next_delivery_action": pick_text(language, "先为第一位客户设计交付闭环", "Design the delivery loop for the first customer"),
        },
        "cash": {
            "cash_in": 0,
            "cash_out": 0,
            "receivable": 0,
            "monthly_target": 0,
            "runway_note": pick_text(language, "待补充现金安全边界", "Add the runway note"),
        },
        "assets": {
            "sops": [],
            "templates": [],
            "cases": [],
            "automations": [],
            "reusable_code": [],
        },
        "risk": {
            "top_risks": [current_bottleneck] if current_bottleneck else [],
            "pending_decisions": [],
        },
        "active_roles": list(active_roles or ["founder-ceo", "control-tower", "product-strategist"]),
        "current_round": round_state,
    }
    return sync_legacy_fields(state)


def arena_from_stage(stage_id: str) -> str:
    mapping = {
        "validate": "sales",
        "build": "product",
        "launch": "product",
        "operate": "delivery",
        "grow": "cash",
    }
    return mapping.get(stage_id, "sales")


def product_state_from_stage(stage_id: str) -> str:
    mapping = {
        "validate": "idea",
        "build": "prototype",
        "launch": "launchable",
        "operate": "live",
        "grow": "live",
    }
    return mapping.get(stage_id, "idea")


def stage_from_product_and_focus(product_state: str, primary_arena: str, won: int, active_customers: int) -> str:
    if product_state in {"defined", "prototype", "internal"}:
        return "build"
    if product_state in {"external", "launchable"}:
        return "launch"
    if product_state == "live":
        if primary_arena == "cash" and (won > 0 or active_customers > 0):
            return "grow"
        return "operate" if active_customers > 0 else "launch"
    if active_customers > 0 and primary_arena in {"delivery", "asset"}:
        return "operate"
    if primary_arena == "cash" and (won > 0 or active_customers > 0):
        return "grow"
    if primary_arena == "product":
        return "build"
    return "validate"


def sync_legacy_fields(state: dict[str, Any]) -> dict[str, Any]:
    language = normalize_language(
        state.get("language"),
        state.get("company_name"),
        state.get("product_name"),
        state.get("offer", {}).get("promise"),
        state.get("offer", {}).get("target_customer"),
    )
    state["language"] = language
    focus = state.setdefault("focus", {})
    offer = state.setdefault("offer", {})
    product = state.setdefault("product", {})
    pipeline = state.setdefault("pipeline", {})
    delivery = state.setdefault("delivery", {})
    cash = state.setdefault("cash", {})
    risk = state.setdefault("risk", {})
    founder = state.setdefault("founder", {})
    assets = state.setdefault("assets", {})
    current_round = state.setdefault("current_round", default_round(language))

    focus.setdefault("primary_goal", pick_text(language, "先跑通最小价值闭环", "Run the smallest value loop first"))
    focus.setdefault("primary_bottleneck", pick_text(language, "还没有识别当前主瓶颈", "The primary bottleneck has not been identified yet"))
    focus.setdefault("primary_arena", "sales")
    focus.setdefault("today_action", current_round.get("next_action") or pick_text(language, "先定义今天最短动作", "Define the shortest action for today"))
    focus.setdefault("week_outcome", current_round.get("goal") or pick_text(language, "先定义本周唯一结果", "Define the single weekly outcome"))

    offer.setdefault("promise", pick_text(language, "待补充价值承诺", "Add the value promise"))
    offer.setdefault("target_customer", pick_text(language, "待确认首批付费用户", "Confirm the first paying user"))
    offer.setdefault("scenario", pick_text(language, "待确认高频使用场景", "Confirm the high-frequency scenario"))
    offer.setdefault("pricing", pick_text(language, "待设计", "To be designed"))
    offer.setdefault("proof", [])

    pipeline.setdefault("stage_summary", {})
    for key in ("discovering", "talking", "trial", "proposal", "won", "lost"):
        pipeline["stage_summary"].setdefault(key, 0)
    pipeline.setdefault("next_revenue_action", pick_text(language, "先补齐第一条真实成交动作", "Add the first real revenue action"))
    pipeline.setdefault("opportunities", [])

    product.setdefault("state", "idea")
    product.setdefault("current_version", pick_text(language, "v0.1 草案", "v0.1 draft"))
    product.setdefault("core_capability", [])
    product.setdefault("current_gap", [])
    product.setdefault("launch_blocker", focus["primary_bottleneck"])
    product.setdefault("repository", "")
    product.setdefault("launch_path", "")

    delivery.setdefault("active_customers", 0)
    delivery.setdefault("delivery_status", pick_text(language, "还没有成交客户", "No signed customers yet"))
    delivery.setdefault("blocking_issue", pick_text(language, "无", "None"))
    delivery.setdefault("next_delivery_action", pick_text(language, "先为第一位客户设计交付闭环", "Design the delivery loop for the first customer"))

    cash.setdefault("cash_in", 0)
    cash.setdefault("cash_out", 0)
    cash.setdefault("receivable", 0)
    cash.setdefault("monthly_target", 0)
    cash.setdefault("runway_note", pick_text(language, "待补充现金安全边界", "Add the runway note"))

    risk.setdefault("top_risks", [])
    risk.setdefault("pending_decisions", [])

    founder.setdefault("goal_mode", "validation")
    founder.setdefault("time_budget", pick_text(language, "待确认", "To be confirmed"))
    founder.setdefault("cash_pressure", pick_text(language, "待确认", "To be confirmed"))
    founder.setdefault("strengths", [])
    founder.setdefault("constraints", [])
    founder.setdefault("working_mode", pick_text(language, "单人主控", "Solo control"))

    assets.setdefault("sops", [])
    assets.setdefault("templates", [])
    assets.setdefault("cases", [])
    assets.setdefault("automations", [])
    assets.setdefault("reusable_code", [])

    current_round.setdefault("status_id", "undefined")
    current_round["status"] = round_status_label(current_round.get("status_id", "undefined"), language)
    current_round.setdefault("owner_role_id", "control-tower")
    current_round.setdefault("owner_role_name", pick_text(language, "总控台", "Control Tower"))
    current_round.setdefault("round_id", pick_text(language, "未启动", "Not Started"))
    current_round.setdefault("name", pick_text(language, "未启动", "Not Started"))
    current_round.setdefault("goal", focus["week_outcome"])
    current_round.setdefault("artifact", pick_text(language, "经营闭环更新", "Business loop update"))
    current_round.setdefault("blocker", focus["primary_bottleneck"])
    current_round.setdefault("next_action", focus["today_action"])
    current_round.setdefault("success_criteria", pick_text(language, "当前主瓶颈向前推进一格", "Move the current bottleneck forward by one step"))
    current_round.setdefault("started_at", "")
    current_round.setdefault("updated_at", "")

    product_state = product.get("state", "idea")
    won = int(pipeline["stage_summary"].get("won", 0) or 0)
    active_customers = int(delivery.get("active_customers", 0) or 0)
    stage_id = stage_from_product_and_focus(product_state, focus["primary_arena"], won, active_customers)

    state["version"] = STATE_VERSION
    state["stage_id"] = stage_id
    state["stage_label"] = stage_label(stage_id, language)
    state["company_goal"] = focus["primary_goal"]
    state["current_bottleneck"] = focus["primary_bottleneck"]
    state["target_user"] = offer["target_customer"]
    state["core_problem"] = offer["scenario"]
    state["product_pitch"] = offer["promise"]
    state.setdefault("active_roles", ["founder-ceo", "control-tower", "product-strategist"])

    current_round["goal"] = current_round.get("goal") or focus["week_outcome"]
    current_round["next_action"] = current_round.get("next_action") or focus["today_action"]
    current_round["blocker"] = current_round.get("blocker") or focus["primary_bottleneck"]

    focus["week_outcome"] = current_round["goal"]
    focus["today_action"] = current_round["next_action"]
    focus["primary_bottleneck"] = current_round["blocker"]

    return state


def upgrade_legacy_state(state: dict[str, Any]) -> dict[str, Any]:
    language = normalize_language(
        state.get("language"),
        state.get("company_name"),
        state.get("product_name"),
        state.get("product_pitch"),
        state.get("target_user"),
        state.get("core_problem"),
    )
    if str(state.get("version", "")).startswith("3"):
        return sync_legacy_fields(deepcopy(state))

    upgraded = default_state_v3(
        company_name=state.get("company_name", pick_text(language, "未命名公司", "Untitled Company")),
        product_name=state.get("product_name", pick_text(language, "未命名产品", "Untitled Product")),
        language=language,
        target_user=state.get("target_user", ""),
        core_problem=state.get("core_problem", ""),
        product_pitch=state.get("product_pitch", ""),
        company_goal=state.get("company_goal", ""),
        current_bottleneck=state.get("current_bottleneck", ""),
        stage_id=state.get("stage_id", "validate"),
        active_roles=state.get("active_roles"),
        current_round=state.get("current_round"),
    )
    upgraded["founder"]["goal_mode"] = {
        "validate": "validation",
        "build": "product",
        "launch": "product",
        "operate": "cash",
        "grow": "cash",
    }.get(state.get("stage_id", "validate"), "validation")
    return sync_legacy_fields(upgraded)


def read_state_any_version(company_dir: Path) -> dict[str, Any]:
    path = state_path(company_dir)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return upgrade_legacy_state(payload)


def write_state_v3(company_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    upgraded = upgrade_legacy_state(state)
    path = state_path(company_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(upgraded, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return upgraded
