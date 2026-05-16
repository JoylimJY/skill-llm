# One Person Company OS

[English](./README.md) | [简体中文](./README.zh-CN.md)

**One Person Company OS 是一套面向 AI 一人创始人的经营闭环操作系统。**

它不是商业计划书生成器，不是只会推进回合的项目管理器，也不是一堆创业模板。
它真正要解决的是这条闭环：

`价值承诺 -> 买家 -> 产品能力 -> 交付 -> 回款 -> 学习 -> 资产`

## 它到底做什么

一次像样的运行，系统会帮助用户：

- 定义可卖的价值承诺
- 收窄第一批愿意付费的人
- 把 MVP 推到可演示、可测试、可上线、可售卖
- 维护线索、成交、交付、回款和现金状态
- 把经营状态真实落盘到工作区
- 在需要正式交付时，留下编号化 DOCX 与可审计证据

## 新的工作区模型

现在的主工作面不再以“阶段/回合说明”为中心，而直接以经营对象为中心：

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

配套目录：

- `product/`
- `sales/`
- `delivery/`
- `ops/`
- `assets/`
- `records/`
- `automation/`
- `产物/`

旧的阶段/回合材料仍然保留兼容，但不再是产品的第一层主视图。

## 状态模型

状态文件仍然放在 `自动化/当前状态.json`，但核心模型已经升级成 v3：

- `founder`
- `focus`
- `offer`
- `pipeline`
- `product`
- `delivery`
- `cash`
- `assets`
- `risk`

为了兼容旧脚本，`stage_id` 和 `current_round` 仍会继续写入。

## 默认交互协议

每次真正执行，都应该先回答：

- 当前头号目标是什么
- 当前主瓶颈是什么
- 当前主战场是哪一类：`sales / product / delivery / cash / asset`
- 今天最短动作是什么
- 这次真实改了哪些文件
- 接下来该打开哪里继续

固定的 `Step 1/5 -> Step 5/5`、保存透明、运行透明、Python 恢复机制仍然保留。

## 本地命令

```bash
python3 scripts/preflight_check.py --mode 创建公司
python3 scripts/ensure_python_runtime.py
python3 scripts/init_business.py "北辰实验室" --path ./workspace --product-name "北辰助手" --stage 构建期
python3 scripts/update_focus.py ./workspace/北辰实验室 --primary-goal "把 MVP 推到可演示并拿到第一批对话" --primary-arena product --today-action "先补 homepage hero 的价值表达和 CTA 路径"
python3 scripts/advance_product.py ./workspace/北辰实验室 --state prototype --current-version "v0.1 hero"
python3 scripts/advance_pipeline.py ./workspace/北辰实验室 --talking 3 --proposal 1 --next-revenue-action "把首版 demo 发给 3 位独立开发者并约反馈"
python3 scripts/advance_delivery.py ./workspace/北辰实验室 --active-customers 1 --delivery-status "首位试用客户已进入 onboarding" --receivable 2999
python3 scripts/update_cash.py ./workspace/北辰实验室 --cash-in 2999 --cash-out 500 --monthly-target 10000
python3 scripts/record_asset.py ./workspace/北辰实验室 --kind templates --item "首位试用客户 onboarding 话术"
python3 scripts/generate_artifact_document.py ./workspace/北辰实验室 --title "首页首屏规范" --category software
python3 scripts/checkpoint_save.py ./workspace/北辰实验室 --reason "准备结束当前会话"
python3 scripts/validate_release.py
```

## 一句话安装

```bash
clawhub install one-person-company-os
```

## 一句话启动

```text
我正在围绕一个 AI 产品创建一人公司，请调用 one-person-company-os。不要先给我商业计划书模板。先帮我定义可卖承诺、第一批买家、以及把 MVP 推到可演示和可售卖的最短路径，然后直接创建工作区、告诉我当前主瓶颈，并把真实文件改出来。
```

## 语言行为

- 中文输入 -> 默认输出中文运行过程与中文资料
- 英文输入 -> 默认输出英文运行过程与英文资料
- 磁盘路径保持稳定，便于自动化和发布

## 校验

运行：

```bash
python3 scripts/validate_release.py
```

它会校验：

- 运行时恢复逻辑
- 经营闭环工作区生成
- 新业务脚本
- 旧脚本兼容链路
- DOCX 产物生成
- release SVG 资产
