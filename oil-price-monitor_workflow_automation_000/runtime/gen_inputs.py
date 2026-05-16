import os
import json
from pathlib import Path
import random

random.seed(42)

workspace = Path("/workspace")

# Create a realistic fleet management project structure
dirs = [
    "skills/oil-price-monitor",
    "skills/weather-monitor",
    "skills/traffic-monitor",
    "docs",
    "config",
    "logs/2026",
    "reports/fleet",
    "reports/finance",
    "agents/bot_a",
    "agents/bot_b",
    "memory",
    "data/historical",
    "data/raw",
    "scripts",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── SKILL.md (the real one the agent must read) ──
skill_md = """\
# oil-price-monitor - 国内油价监控 Skill

## 功能
监测国内成品油价格调整窗口，在调价前提醒用户提前加油。

## 触发条件
- 用户询问油价
- 定时任务（调价窗口前 1-2 天自动监测）

## 使用方法

### 1. 手动查询油价
```
查询当前油价情况
油价什么时候调整
最近油价涨了吗
```

### 2. 调用 Tavily 搜索获取最新数据
```
tavily_search(query="2026 年国内油价调整时间表 最新油价", count=5)
```

### 3. 关键信息提取
从搜索结果中提取：
- **下次调价时间**：格式为"月日 24 时"
- **预计涨幅**：元/吨 或 元/升
- **当前油价**：92 号/95 号汽油价格
- **调价方向**：上涨/下跌/搁浅

### 4. 调价窗口规律
国内成品油定价机制：
- **调整周期**：每 10 个工作日调整一次
- **全年窗口**：约 26 次（每月 2 次）
- **触发条件**：国际原油价格变化超过 50 元/吨
- **调控上下限**：130 美元/桶（上限）、40 美元/桶（下限）

## 2026 年调价窗口时间表

| 月份 | 调价时间 1 | 调价时间 2 |
|------|-----------|-----------|
| 1 月 | 1 月 6 日 24 时 | 1 月 20 日 24 时 |
| 2 月 | 2 月 3 日 24 时 | 2 月 24 日 24 时 |
| 3 月 | 3 月 9 日 24 时 | 3 月 23 日 24 时 |
| 4 月 | 4 月 7 日 24 时 | 4 月 21 日 24 时 |
| 5 月 | 5 月 8 日 24 时 | 5 月 21 日 24 时 |
| 6 月 | 6 月 4 日 24 时 | 6 月 18 日 24 时 |
| 7 月 | 7 月 3 日 24 时 | 7 月 17 日 24 时 |
| 8 月 | 8 月 14 日 24 时 | 8 月 28 日 24 时 |
| 9 月 | 9 月 11 日 24 时 | 9 月 24 日 24 时 |
| 10 月 | 10 月 15 日 24 时 | 10 月 29 日 24 时 |
| 11 月 | 11 月 12 日 24 时 | 11 月 26 日 24 时 |
| 12 月 | 12 月 10 日 24 时 | 12 月 24 日 24 时 |

## 定时任务配置建议

在 `docs/cron-jobs.md` 中添加：
```json
{
  "name": "油价监控提醒",
  "cron": "0 9 */2 * *",
  "description": "每 2 天检查一次油价，在调价窗口前 1 天提醒用户",
  "agent": "bot_a",
  "model": "bailian/qwen3.5-plus"
}
```

## 回复模板

### 调价前提醒
```
⛽ 油价调整提醒

下次调价：{日期} 24 时（{倒计时}天）
预计涨幅：{涨幅}元/升（{涨幅吨}元/吨）
调价方向：{上涨/下跌}

建议：{提前加油/观望}
以 50 升油箱计算，调价后加满将多花/少花约{金额}元
```

### 当前油价查询
```
📊 当前油价（{地区}）

92 号汽油：{价格}元/升
95 号汽油：{价格}元/升
0 号柴油：{价格}元/升

下次调价：{日期} 24 时
```

## 注意事项
1. 数据来源优先参考官方渠道（发改委、中国日报网）
2. 涨幅数据需注明是预测值还是已确认
3. 不同地区油价有差异，说明是参考价
4. 民营加油站可能有 0.2-0.5 元/升优惠

## 相关文件
- 技能位置：`skills/oil-price-monitor/SKILL.md`
- 定时任务：`docs/cron-jobs.md`
- 用户记忆：`MEMORY.md`（记录用户关注油价）
"""

(workspace / "skills/oil-price-monitor/SKILL.md").write_text(skill_md, encoding="utf-8")

# ── docs/cron-jobs.md  (existing file with other entries, NO oil-price entry yet) ──
cron_jobs_existing = """\
# Cron Jobs Configuration

This file defines all scheduled tasks for the agent system.

## Active Jobs

```json
{
  "name": "天气预报提醒",
  "cron": "0 7 * * *",
  "description": "每天早上推送天气预报",
  "agent": "bot_a",
  "model": "bailian/qwen3.5-plus"
}
```

```json
{
  "name": "股市开盘提醒",
  "cron": "30 9 * * 1-5",
  "description": "工作日股市开盘前提醒",
  "agent": "bot_b",
  "model": "bailian/qwen3.5-lite"
}
```

```json
{
  "name": "快递跟踪",
  "cron": "0 */4 * * *",
  "description": "每 4 小时检查快递状态",
  "agent": "bot_a",
  "model": "bailian/qwen3.5-plus"
}
```

## Retired Jobs

- ~~汇率监控~~ (已停用，2025-12-01)
"""

(workspace / "docs/cron-jobs.md").write_text(cron_jobs_existing, encoding="utf-8")

# ── MEMORY.md (user memory - distractor) ──
memory_md = """\
# User Memory

## Preferences
- 用户关注油价变动，希望提前加油省钱
- 用户车辆：SUV，油箱容量约 60 升
- 常用加油站：中石化 92 号汽油
- 用户所在城市：上海

## Historical Queries
- 2026-07-15: 询问油价，当时 92 号 7.85 元/升
- 2026-06-18: 油价下调，92 号降至 7.68 元/升
- 2026-05-21: 油价上调，92 号涨至 7.92 元/升
"""

(workspace / "memory/MEMORY.md").write_text(memory_md, encoding="utf-8")

# ── Distractor: outdated oil price data ──
old_data = {
    "date": "2026-07-17",
    "92_gasoline": 7.85,
    "95_gasoline": 8.36,
    "0_diesel": 7.42,
    "next_adjustment": "2026-07-31",
    "note": "OUTDATED - do not use"
}
(workspace / "data/historical/oil_price_2026_q2.json").write_text(
    json.dumps(old_data, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── Distractor: raw search results dump ──
raw_search = """\
[搜索结果 - 2026-08-01]
标题: 发改委：8月成品油价格调整公告
摘要: 国家发改委宣布，根据近期国际原油市场变化，8月将进行两次调价...
URL: http://www.ndrc.gov.cn/...

标题: 国内汽油价格走势分析
摘要: 分析人士预测，受地缘政治影响，下半年油价存在上行压力...
URL: http://finance.china.com/...

[注意：以下数据为历史记录，不代表当前价格]
2026-07-17 调价后：92号 7.85元/升，95号 8.36元/升
"""
(workspace / "data/raw/search_results_20260801.txt").write_text(raw_search, encoding="utf-8")

# ── Distractor: weather skill ──
(workspace / "skills/weather-monitor/SKILL.md").write_text(
    "# weather-monitor\n天气监控技能，使用和风天气API获取实时数据。\n", encoding="utf-8"
)

# ── Distractor: traffic skill ──
(workspace / "skills/traffic-monitor/SKILL.md").write_text(
    "# traffic-monitor\n交通监控技能，实时路况查询。\n", encoding="utf-8"
)

# ── Distractor: agent configs ──
bot_a_config = {
    "id": "bot_a",
    "model": "bailian/qwen3.5-plus",
    "skills": ["weather-monitor", "traffic-monitor"],
    "active": True
}
(workspace / "agents/bot_a/config.json").write_text(
    json.dumps(bot_a_config, ensure_ascii=False, indent=2), encoding="utf-8"
)

bot_b_config = {
    "id": "bot_b",
    "model": "bailian/qwen3.5-lite",
    "skills": ["stock-monitor"],
    "active": True
}
(workspace / "agents/bot_b/config.json").write_text(
    json.dumps(bot_b_config, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── Distractor: finance reports ──
for month in ["06", "07"]:
    (workspace / f"reports/finance/fleet_fuel_cost_2026{month}.csv").write_text(
        f"vehicle_id,date,liters,price_per_liter,total\n"
        f"SH-A0001,2026-{month}-05,45,7.85,353.25\n"
        f"SH-A0002,2026-{month}-12,60,7.85,471.00\n"
        f"SH-B0003,2026-{month}-20,38,7.68,291.84\n",
        encoding="utf-8"
    )

# ── Distractor: logs ──
(workspace / "logs/2026/agent_activity.log").write_text(
    "2026-08-09 08:00:01 [bot_a] weather check completed\n"
    "2026-08-09 09:00:00 [bot_a] oil price check - no adjustment imminent\n"
    "2026-08-10 08:00:01 [bot_a] weather check completed\n",
    encoding="utf-8"
)

# ── Distractor: fleet report template (wrong template - don't use) ──
(workspace / "reports/fleet/report_template.txt").write_text(
    "Fleet Fuel Report\nDate: {date}\nTotal Vehicles: {count}\nAvg Consumption: {avg}L/100km\n",
    encoding="utf-8"
)

# ── Distractor: a fake/wrong 2026 schedule (trap!) ──
fake_schedule = """\
# 注意：此文件已过期，请以 SKILL.md 中的时间表为准

错误的旧版时间表（请勿使用）：
8月: 8月7日、8月21日   <-- WRONG
9月: 9月4日、9月18日   <-- WRONG
"""
(workspace / "data/historical/old_price_schedule_2026.txt").write_text(fake_schedule, encoding="utf-8")

# ── scripts placeholder ──
(workspace / "scripts/fetch_oil_price.py").write_text(
    "#!/usr/bin/env python3\n# Placeholder - uses Tavily API\nprint('Not implemented in offline mode')\n",
    encoding="utf-8"
)

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")