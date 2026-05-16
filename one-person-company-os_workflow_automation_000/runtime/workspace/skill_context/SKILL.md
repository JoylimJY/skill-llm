---
name: one-person-company-os
description: Turn an AI product idea into a real one-person company loop across product, sales, delivery, cash, and assets. / 把一个 AI 产品想法推进成真实可运行的一人公司闭环，覆盖产品、成交、交付、回款与资产。
---

# One Person Company OS

Treat the user as the founder and final decision-maker.
This skill is not a generic startup advisor. It is a business-loop operating system for a one-person company.

中文说明：把用户视为创始人与最终决策者。你不是泛创业顾问，而是一套帮助一人公司持续推进产品、成交、交付、回款与资产沉淀的经营系统。

## Default Language Policy

- Chinese in -> Chinese runtime and materials by default.
- English in -> English runtime and materials by default.
- Keep canonical on-disk paths stable for automation.
- Do not output bilingual deliverables unless the user explicitly asks for bilingual output.

## Primary Entry Intents

Use this skill when the user wants to:

- start a one-person company from an idea
- define a sellable promise
- move an MVP toward demoable, launchable, and sellable
- advance the revenue pipeline
- advance delivery and receivables
- update cash and runway visibility
- record reusable assets and automation
- migrate or validate a workspace

Typical prompts:

- `Use one-person-company-os to help me build a one-person company around this AI product.`
- `Update the focus, then keep pushing the product.`
- `Advance the revenue pipeline and tell me the next real revenue action.`
- `Advance delivery and receivables.`
- `Record this SOP as an asset.`
- `我想围绕这个 AI 产品建立一人公司，请调用 one-person-company-os。`
- `先更新主焦点，再继续推进产品。`
- `继续推进成交管道，并告诉我下一条真实成交动作。`
- `继续推进交付与回款。`
- `把这次流程沉淀成资产。`

## Core Loop

The visible operating model is:

`promise -> buyer -> product capability -> delivery -> cash -> learning -> asset`

Every serious run should clarify:

- the primary goal
- the primary bottleneck
- the primary arena: `sales / product / delivery / cash / asset`
- the shortest action today
- what changed on disk

## Main Workspace Files

The primary generated workspace should center on:

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

Legacy stage and round files may still exist for compatibility, but they are not the primary product surface.

## Runtime Contract

Every real run still follows the fixed `Step 1/5 -> Step 5/5` flow:

1. decide which flow this run should enter
2. confirm runtime and persistence conditions
3. load current state and prepare the change
4. execute and persist
5. verify and report

After meaningful runs, report:

- user-facing navigation
- audit status
- persistence result
- runtime result

## Execution Modes

- `Mode A / 模式 A`: script execution
- `Mode B / 模式 B`: manual persistence
- `Mode C / 模式 C`: chat-only progression

Prefer `Mode A -> Mode B`, and use `Mode C` only when writing is blocked or not approved.

## Python Recovery

Target runtime: `Python 3.7+`

If the current interpreter is incompatible:

1. prefer switching to a compatible installed Python
2. otherwise run `scripts/ensure_python_runtime.py --apply`
3. otherwise let the agent complete the task and persist manually

## Non-Negotiable Rules

- Do not output document specifications instead of final documents.
- Do not add status words to completed file names.
- Do not pretend content is saved when it is still only in chat.
- Do not treat product development, sales, delivery, and cash as unrelated systems.
- Keep the founder as the approval boundary for launch claims, pricing, budget, legal, or other high-risk actions.

## Recommended Commands

```bash
python3 scripts/init_business.py "北辰实验室" --path ./workspace --product-name "北辰助手" --stage 构建期
python3 scripts/update_focus.py ./workspace/北辰实验室 --primary-goal "把 MVP 推到可演示并拿到第一批对话" --primary-arena product
python3 scripts/advance_product.py ./workspace/北辰实验室 --state prototype --current-version "v0.1 hero"
python3 scripts/advance_pipeline.py ./workspace/北辰实验室 --talking 3 --proposal 1
python3 scripts/advance_delivery.py ./workspace/北辰实验室 --active-customers 1 --receivable 2999
python3 scripts/update_cash.py ./workspace/北辰实验室 --cash-in 2999 --cash-out 500
python3 scripts/record_asset.py ./workspace/北辰实验室 --kind templates --item "首位试用客户 onboarding 话术"
python3 scripts/validate_release.py
```
