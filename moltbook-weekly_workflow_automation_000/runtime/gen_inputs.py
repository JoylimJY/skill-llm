#!/usr/bin/env python3
"""
Generate the sandbox workspace for the weekly-report-skill evaluation task.
"""

import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─────────────────────────────────────────────
# 1. Directory structure + distractor files
# ─────────────────────────────────────────────
dirs = [
    "scripts",
    "data",
    "data/archive",
    "data/archive/2025-03",
    "data/raw",
    "logs",
    "configs",
    "tests",
    "tests/fixtures",
    "docs",
    "docs/internal",
    "output",
    ".git/refs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "configs/app_config.yaml": "environment: production\nlog_level: INFO\nretry_count: 3\n",
    "configs/database.yaml": "host: localhost\nport: 5432\nname: analytics_db\n",
    "logs/app.log": "2025-03-28 10:00:00 INFO Service started\n2025-03-28 10:05:12 WARN Retry attempt 1\n2025-03-28 10:05:15 INFO Success\n",
    "logs/error.log": "2025-03-29 09:12:33 ERROR Connection timeout\n",
    "docs/internal/architecture.md": "# System Architecture\n\nThis document describes the internal architecture.\n",
    "docs/internal/deployment.md": "# Deployment Guide\n\nSee runbook for details.\n",
    "tests/fixtures/sample_response.json": json.dumps({"status": "ok", "code": 200}, indent=2),
    "tests/test_data_pipeline.py": "import pytest\n\ndef test_pipeline_runs():\n    assert True\n",
    "data/archive/2025-03/summary.json": json.dumps({
        "week": "2025-03-17/2025-03-23",
        "v35_runs": 44,
        "instreet_replies": 140
    }, indent=2),
    "data/raw/raw_events.jsonl": '{"ts":1711612800,"event":"deploy","status":"ok"}\n{"ts":1711616400,"event":"reply","status":"ok"}\n',
    ".git/refs/HEAD": "ref: refs/heads/main\n",
    "output/.gitkeep": "",
}
for path, content in distractors.items():
    fp = WORKSPACE / path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content)

# ─────────────────────────────────────────────
# 2. Messy / broken data source files
#    The script expects specific JSON schemas;
#    these files are intentionally malformed or
#    have wrong field names to test agent's ability
#    to read SKILL.md and understand data sources.
# ─────────────────────────────────────────────

# v35_stats.json — wrong key names, missing fields
bad_v35 = {
    "total_runs": 50,          # correct key
    "avg_likes": 35.2,         # correct key
    "accuracy_pct": 75,        # correct key
    "EXTRA_GARBAGE": "ignore"
}
(WORKSPACE / "data" / "v35_stats.json").write_text(json.dumps(bad_v35, indent=2))

# instreet_stats.json — partially correct
bad_instreet = {
    "total_replies": 156,
    "success_rate_pct": 91,
    "morning_peak_activations": 12,
    "junk_field": None
}
(WORKSPACE / "data" / "instreet_stats.json").write_text(json.dumps(bad_instreet, indent=2))

# price_monitor.json — valid but with extra noise
price_data = {
    "products_monitored": 8,
    "alerts_triggered": 3,
    "avg_price_drop_pct": 4.2,
    "debug_trace": [1, 2, 3]
}
(WORKSPACE / "data" / "price_monitor.json").write_text(json.dumps(price_data, indent=2))

# kimi_search.json — valid
kimi_data = {
    "industry_news_count": 24,
    "relevant_hits": 7,
    "top_topic": "LLM cost optimization"
}
(WORKSPACE / "data" / "kimi_search.json").write_text(json.dumps(kimi_data, indent=2))

# ─────────────────────────────────────────────
# 3. The main script: scripts/create_weekly_report.py
#    This is the reference implementation the agent
#    must invoke correctly.
# ─────────────────────────────────────────────
script_content = r'''#!/usr/bin/env python3
"""
create_weekly_report.py  -  Weekly Report Generator (weekly-report-skill v1.0.0)

Usage:
  python3 scripts/create_weekly_report.py --title "TITLE" --output PATH
  python3 scripts/create_weekly_report.py --title "TITLE" --auto-publish

The --title value MUST match the pattern:  <name> (<YYYY.MM.DD-MM.DD>)
e.g.  "MoltbookAgent 周报 (2025.03.24-03.30)"

Data sources (all relative to the workspace root):
  data/v35_stats.json        keys: total_runs, avg_likes, accuracy_pct
  data/instreet_stats.json   keys: total_replies, success_rate_pct, morning_peak_activations
  data/price_monitor.json    keys: products_monitored, alerts_triggered
  data/kimi_search.json      keys: industry_news_count, relevant_hits

Exit codes:
  0  success
  1  missing or invalid --title  (pattern not matched)
  2  one or more data source files missing / unreadable
  3  --output path not writable
"""

import argparse
import json
import re
import sys
import os
from datetime import datetime
from pathlib import Path

TITLE_PATTERN = re.compile(
    r'^.+\s*\(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\)$'
)

WORKSPACE_ROOT = Path(__file__).parent.parent

def load_json(path: Path) -> dict:
    if not path.exists():
        print(f"[ERROR] Data file not found: {path}", file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"[ERROR] Cannot parse {path}: {e}", file=sys.stderr)
        sys.exit(2)


def build_report(title: str, v35: dict, instreet: dict, price: dict, kimi: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # -- section 1: work summary --
    v35_runs      = v35.get("total_runs", "N/A")
    v35_likes     = v35.get("avg_likes", "N/A")
    v35_accuracy  = v35.get("accuracy_pct", "N/A")

    instreet_total   = instreet.get("total_replies", "N/A")
    instreet_success = instreet.get("success_rate_pct", "N/A")
    instreet_morning = instreet.get("morning_peak_activations", "N/A")

    # -- section 2: key metrics table --
    v35_likes_last     = v35.get("avg_likes_last_week", 32.8)
    instreet_suc_last  = instreet.get("success_rate_last_week", 89)

    def pct_change(cur, prev):
        try:
            delta = (float(cur) - float(prev)) / float(prev) * 100
            sign = "+" if delta >= 0 else ""
            return f"{sign}{delta:.1f}%"
        except Exception:
            return "N/A"

    v35_change     = pct_change(v35_likes, v35_likes_last)
    instreet_change = pct_change(instreet_success, instreet_suc_last)

    # -- section 3: next week plan --
    price_products = price.get("products_monitored", "N/A")
    kimi_hits      = kimi.get("relevant_hits", "N/A")

    report = f"""# {title}

## 本周工作总结

### v3.5 生产部署器
- 运行次数: {v35_runs}次
- 平均赞数: {v35_likes}
- 预测准确度: {v35_accuracy}%

### InStreet 自动回复
- 回复总数: {instreet_total}条
- 成功率: {instreet_success}%
- 早高峰模式: {instreet_morning}次

## 关键指标

| 指标 | 本周 | 上周 | 变化 |
|------|------|------|------|
| v3.5 平均赞 | {v35_likes} | {v35_likes_last} | {v35_change} |
| InStreet 成功率 | {instreet_success}% | {instreet_suc_last}% | {instreet_change} |

## 下周计划

- [ ] 优化 v3.5 探索策略
- [ ] 新增价格监控产品 (当前监控: {price_products}个)
- [ ] 完善周报自动化
- [ ] 跟进 kimi_search 行业动态 (本周命中: {kimi_hits}条)

## 风险与问题

- 无

---
生成时间: {now}
"""
    return report


def main():
    parser = argparse.ArgumentParser(description="Weekly Report Generator")
    parser.add_argument("--title", required=True,
                        help='Report title, e.g. "MoltbookAgent 周报 (2025.03.24-03.30)"')
    parser.add_argument("--output", default=None,
                        help="Write report to this local file path")
    parser.add_argument("--auto-publish", action="store_true",
                        help="Publish to WeChat Work doc (requires WECOM credentials)")
    args = parser.parse_args()

    # -- validate title format --
    if not TITLE_PATTERN.match(args.title):
        print(
            "[ERROR] --title must match pattern: '<name> (YYYY.MM.DD-MM.DD)'\n"
            f"        Got: {args.title!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    # -- load data --
    v35      = load_json(WORKSPACE_ROOT / "data" / "v35_stats.json")
    instreet = load_json(WORKSPACE_ROOT / "data" / "instreet_stats.json")
    price    = load_json(WORKSPACE_ROOT / "data" / "price_monitor.json")
    kimi     = load_json(WORKSPACE_ROOT / "data" / "kimi_search.json")

    report = build_report(args.title, v35, instreet, price, kimi)

    # -- output --
    if args.output:
        out_path = Path(args.output)
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(report, encoding="utf-8")
            print(f"[OK] Report written to {out_path}")
        except OSError as e:
            print(f"[ERROR] Cannot write to {args.output}: {e}", file=sys.stderr)
            sys.exit(3)

    if args.auto_publish:
        print("[WARN] --auto-publish requires WECOM_CORPID / WECOM_SECRET env vars. Skipping.")

    if not args.output and not args.auto_publish:
        print(report)


if __name__ == "__main__":
    main()
'''

(WORKSPACE / "scripts" / "create_weekly_report.py").write_text(script_content)

# ─────────────────────────────────────────────
# 4. SKILL.md in the workspace root
# ─────────────────────────────────────────────
skill_md = """\
---
name: weekly-report-skill
description: 自动生成周报并写入企业微信文档。支持数据汇总、Markdown报告生成、一键发布，适合项目周报、团队同步、数据报告场景。
author: MoltbookAgent
version: 1.0.0
tags: [weekly, report, wecom, automation, team]
---

# Weekly Report Skill

## 一句话说明

自动生成周报并写入企业微信文档。

## 适用场景

- 📊 创建项目周报
- 📈 汇总数据报告
- 👥 团队进展同步
- 📝 周期性数据汇报

## 快速开始

### 生成并发布周报

```bash
python3 scripts/create_weekly_report.py --title "MoltbookAgent 周报" --auto-publish
```

### 只生成本地报告

```bash
python3 scripts/create_weekly_report.py --output /tmp/report.md
```

## 功能详解

### 1. 数据自动汇总

自动收集以下数据源：
- v3.5 生产部署器运行数据
- InStreet 自动回复统计
- 价格监控模块数据
- kimi_search 行业动态

### 2. 报告生成

生成结构化 Markdown 周报：
- 本周工作总结
- 关键指标数据
- 下周计划
- 风险与问题

### 3. 一键发布

自动创建企业微信文档并写入内容：
- 支持自定义文档标题
- 自动格式化排版
- 生成文档分享链接

## 示例输出

```markdown
# MoltbookAgent 周报 (2025.03.24-03.30)

## 本周工作总结

### v3.5 生产部署器
- 运行次数: 50次
- 平均赞数: 35.2
- 预测准确度: 75%

### InStreet 自动回复
- 回复总数: 156条
- 成功率: 91%
- 早高峰模式: 12次

## 关键指标

| 指标 | 本周 | 上周 | 变化 |
|------|------|------|------|
| v3.5 平均赞 | 35.2 | 32.8 | +7.3% |
| InStreet 成功率 | 91% | 89% | +2.2% |

## 下周计划

- [ ] 优化 v3.5 探索策略
- [ ] 新增价格监控产品
- [ ] 完善周报自动化

## 风险与问题

- 无

---
生成时间: 2025-03-30 18:00
```

## 与其他 Skill 配合

| Skill | 配合方式 |
|-------|---------|
| test-report-skill | 获取 v3.5 测试数据 |
| instreet-analytics-skill | 获取 InStreet 统计数据 |
| price-monitor-skill | 获取价格监控数据 |
| wecom-doc-manager | 发布到企业微信文档 |
| auto-weekly-system | 定时自动生成周报 |

## 更新日志

### v1.0.0 (2025-03-26)
- ✅ 自动数据汇总
- ✅ Markdown 报告生成
- ✅ 企业微信文档发布

## 反馈与贡献

如有问题或建议，欢迎反馈。
"""
(WORKSPACE / "SKILL.md").write_text(skill_md)

print("Workspace generation complete.")
print(f"Files created under {WORKSPACE}:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")