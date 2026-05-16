# One Person Company OS

[English](./README.md) | [简体中文](./README.zh-CN.md)

**One Person Company OS is a business-loop operating system for AI-native solo founders.**

It is not a business-plan generator, not a round-only project tracker, and not a pile of startup templates.
It is designed to help one founder move through the real loop:

`promise -> buyer -> product capability -> delivery -> cash -> learning -> asset`

## What It Does

On a serious run, the system helps a solo founder:

- define a sellable promise
- narrow the first paying customer
- push an MVP toward something demoable, testable, launchable, and sellable
- track opportunities, delivery, receivables, and cash
- persist the operating state into a real workspace
- keep shipping real deliverables, including numbered DOCX artifacts where formal delivery is needed

## The Real Workspace Model

The generated workspace now centers on operating surfaces instead of stage-first guidance:

- `00-经营总盘.md`
- `01-创始人约束.md`
- `02-价值承诺与报价.md`
- `03-机会与成交管道.md`
- `04-产品与上线状态.md`
- `05-客户交付与回款.md`
- `06-现金流与经营健康.md`
- `07-资产与自动化.md`
- `08-风险与关键决策.md`
- `09-本周唯一主目标.md`
- `10-今日最短动作.md`
- `11-协作记忆.md`
- `12-会话交接.md`

Supporting directories:

- `product/`
- `sales/`
- `delivery/`
- `ops/`
- `assets/`
- `records/`
- `automation/`
- `产物/`

Legacy stage and round materials are still supported for compatibility, but they are no longer the primary product surface.

## State Model

The state file stays at `自动化/当前状态.json`, but the core model is now v3 and business-loop driven:

- `founder`
- `focus`
- `offer`
- `pipeline`
- `product`
- `delivery`
- `cash`
- `assets`
- `risk`

Legacy `stage_id` and `current_round` fields are still written so older scripts can keep running.

## Default Interaction Contract

Every serious run should answer:

- what the primary goal is
- what the primary bottleneck is
- which arena is primary right now: `sales / product / delivery / cash / asset`
- what the shortest action today is
- what changed on disk
- what to open next

The fixed `Step 1/5 -> Step 5/5` execution flow, persistence reporting, and runtime recovery are still part of the contract.

## Local Commands

```bash
python3 scripts/preflight_check.py --mode create-company
python3 scripts/ensure_python_runtime.py
python3 scripts/init_business.py "北辰实验室" --path ./workspace --product-name "北辰助手" --stage 构建期
python3 scripts/update_focus.py ./workspace/北辰实验室 --primary-goal "把 MVP 推到可演示并拿到第一批对话" --primary-arena product --today-action "先补 homepage hero 的价值表达和 CTA 路径"
python3 scripts/advance_product.py ./workspace/北辰实验室 --state prototype --current-version "v0.1 hero"
python3 scripts/advance_pipeline.py ./workspace/北辰实验室 --talking 3 --proposal 1 --next-revenue-action "把首版 demo 发给 3 位独立开发者并约反馈"
python3 scripts/advance_delivery.py ./workspace/北辰实验室 --active-customers 1 --delivery-status "首位试用客户已进入 onboarding" --receivable 2999
python3 scripts/update_cash.py ./workspace/北辰实验室 --cash-in 2999 --cash-out 500 --monthly-target 10000
python3 scripts/record_asset.py ./workspace/北辰实验室 --kind templates --item "首位试用客户 onboarding 话术"
python3 scripts/generate_artifact_document.py ./workspace/北辰实验室 --title "Homepage Hero Spec" --category software
python3 scripts/checkpoint_save.py ./workspace/北辰实验室 --reason "end of current session"
python3 scripts/validate_release.py
```

## One-Line Install

```bash
clawhub install one-person-company-os
```

## One-Line Start

```text
I am building a one-person company around an AI product. Use one-person-company-os. Do not give me a business-plan template. First help me define the sellable promise, the first buyer, and the shortest path to a demoable and sellable MVP. Then create the operating workspace, tell me the current bottleneck, and update the real files directly.
```

## Language Behavior

- Chinese prompt in -> Chinese runtime and materials out by default
- English prompt in -> English runtime and materials out by default
- canonical on-disk paths stay stable for automation

## Validation

Run:

```bash
python3 scripts/validate_release.py
```

It validates:

- runtime recovery logic
- business-loop workspace generation
- new business scripts
- legacy compatibility path
- DOCX artifact generation
- release SVG assets
