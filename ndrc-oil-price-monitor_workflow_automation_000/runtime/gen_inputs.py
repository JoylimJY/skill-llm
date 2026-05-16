import os
import random
import json
import yaml
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── 1. Skill directory structure (files "already exist" per SKILL.md) ──────────
skill_dir = workspace / "oil-price-monitor"
skill_dir.mkdir(parents=True, exist_ok=True)

# __init__.py
(skill_dir / "__init__.py").write_text(
    '"""NDRC oil price monitor package."""\n'
    'from .oil_price_monitor import OilPriceMonitor\n'
    '__all__ = ["OilPriceMonitor"]\n'
)

# requirements.txt
(skill_dir / "requirements.txt").write_text(
    "requests>=2.28.0\n"
    "beautifulsoup4>=4.11.0\n"
    "chinese-workdays>=0.2.0\n"
    "pyyaml>=6.0\n"
    "pytz>=2023.3\n"
    "lxml>=4.9.0\n"
)

# The main monitor script – fully functional
monitor_py = r'''#!/usr/bin/env python3
"""NDRC Oil Price Monitor - 国家发改委成品油价格监控器"""

import argparse
import json
import sys
import os
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any

import pytz
import yaml
import requests
from bs4 import BeautifulSoup

try:
    import chinese_workdays as cw
    HAS_WORKDAYS = True
except ImportError:
    HAS_WORKDAYS = False

SHANGHAI_TZ = pytz.timezone("Asia/Shanghai")

DEFAULT_CONFIG = {
    "start_date": "2026-04-07",
    "window_interval": 10,      # working days
    "check_time": "17:30",
    "timezone": "Asia/Shanghai",
    "ndrc_url": "http://localhost:5099/xwdt/xwfb/",
    "keywords": ["成品油", "油价调整", "汽油", "柴油"],
    "feishu_webhook": "",
}


def load_config(config_path: str = None) -> Dict[str, Any]:
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
        merged = {**DEFAULT_CONFIG, **user_cfg}
        return merged
    return dict(DEFAULT_CONFIG)


def next_workday(d: date) -> date:
    """Return next working day after d (using chinese-workdays if available)."""
    candidate = d + timedelta(days=1)
    if HAS_WORKDAYS:
        while not cw.is_workday(candidate):
            candidate += timedelta(days=1)
    else:
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
    return candidate


def add_working_days(start: date, n: int) -> date:
    """Add n working days to start (inclusive of start as day 0)."""
    current = start
    added = 0
    while added < n:
        current = next_workday(current)
        added += 1
    return current


def compute_windows(start_str: str, interval: int, count: int = 5) -> List[Dict[str, Any]]:
    """Compute the next `count` adjustment windows."""
    start = date.fromisoformat(start_str)
    windows = []
    current = start
    for i in range(count):
        windows.append({
            "index": i + 1,
            "date": current.isoformat(),
            "weekday": current.strftime("%A"),
            "is_workday": cw.is_workday(current) if HAS_WORKDAYS else current.weekday() < 5,
        })
        current = add_working_days(current, interval)
    return windows


def fetch_ndrc_news(url: str, keywords: List[str]) -> List[Dict[str, Any]]:
    """Fetch and parse NDRC news page for oil price announcements."""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    results = []

    # Try multiple common list structures
    for item in soup.select("li, .news-item, .list-item, article"):
        text = item.get_text(" ", strip=True)
        if any(kw in text for kw in keywords):
            link_tag = item.find("a")
            href = link_tag["href"] if link_tag and link_tag.get("href") else "#"
            if href.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"
            results.append({
                "title": text[:120],
                "url": href,
                "raw": text,
            })
    return results


def format_announcement(window: Dict, items: List[Dict]) -> str:
    lines = [
        "🛢️  成品油价格调整公告",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📅 窗口期: {window['date']} (第{window['index']}个窗口)",
        "📢 发布机构: 国家发改委",
        f"🕐 发布时间: {datetime.now(SHANGHAI_TZ).strftime('%Y-%m-%d %H:%M')}",
        "",
        "💵 调整内容:",
    ]
    for item in items:
        lines.append(f"  {item['title']}")
    lines.append("")
    if items:
        lines.append(f"🔗 原文链接: {items[0]['url']}")
    return "\n".join(lines)


class OilPriceMonitor:
    def __init__(self, config_path: str = None):
        self.cfg = load_config(config_path)

    def get_next_windows(self, count: int = 3) -> List[Dict[str, Any]]:
        return compute_windows(
            self.cfg["start_date"],
            self.cfg["window_interval"],
            count=count,
        )

    def run_test(self) -> None:
        windows = self.get_next_windows(count=3)
        current_window = windows[0]
        items = fetch_ndrc_news(self.cfg["ndrc_url"], self.cfg["keywords"])
        if items:
            print(format_announcement(current_window, items))
        else:
            print(f"[INFO] No matching announcements found. Window: {current_window['date']}")

    def run_recent(self) -> None:
        items = fetch_ndrc_news(self.cfg["ndrc_url"], self.cfg["keywords"])
        if not items:
            print("[INFO] No recent announcements found.")
            return
        for item in items[:5]:
            print(f"  • {item['title']}")
            print(f"    {item['url']}")

    def run_next_window(self) -> None:
        windows = self.get_next_windows(count=3)
        for w in windows:
            workday_flag = "✅ 工作日" if w["is_workday"] else "⚠️  非工作日"
            print(f"  第{w['index']}个窗口: {w['date']} ({w['weekday']}) [{workday_flag}]")


def main():
    parser = argparse.ArgumentParser(description="NDRC Oil Price Monitor")
    parser.add_argument("--test", action="store_true", help="Force check and output")
    parser.add_argument("--next-window", action="store_true", dest="next_window",
                        help="Show next adjustment windows")
    parser.add_argument("--recent", action="store_true", help="Show recent announcements")
    parser.add_argument("--config", default=None, help="Config file path")
    parser.add_argument("--windows-json", default=None, dest="windows_json",
                        help="Output windows as JSON to a file")
    parser.add_argument("--count", type=int, default=3, help="Number of windows to compute")
    args = parser.parse_args()

    monitor = OilPriceMonitor(config_path=args.config)

    if args.next_window:
        monitor.run_next_window()
    elif args.test:
        monitor.run_test()
    elif args.recent:
        monitor.run_recent()
    elif args.windows_json:
        windows = monitor.get_next_windows(count=args.count)
        with open(args.windows_json, "w", encoding="utf-8") as f:
            json.dump({"windows": windows, "config": monitor.cfg}, f, ensure_ascii=False, indent=2)
        print(f"[OK] Saved {len(windows)} windows to {args.windows_json}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
'''
(skill_dir / "oil_price_monitor.py").write_text(monitor_py)
os.chmod(skill_dir / "oil_price_monitor.py", 0o755)

# SKILL.md (the spec file – agent must read this)
skill_md = """---
name: ndrc-oil-price
description: Monitor NDRC website for oil price adjustment announcements. Searches news releases every 10 working days at 17:30 starting from 2026-04-07 and pushes notifications via Feishu.
license: MIT
---

# 成品油价格监控器

## Quick Start

```bash
# 测试运行（强制检查）
python oil_price_monitor.py --test

# 查看下一个窗口期
python oil_price_monitor.py --next-window

# 查看最近公告
python oil_price_monitor.py --recent

# 输出窗口期JSON报告
python oil_price_monitor.py --windows-json output.json --count 5
```

## 配置

在 `config.yaml` 中可覆盖默认值：

```yaml
start_date: "2026-04-07"    # 起始窗口日期
window_interval: 10          # 每10个工作日
check_time: "17:30"
timezone: "Asia/Shanghai"
ndrc_url: "http://localhost:5099/xwdt/xwfb/"
keywords:
  - 成品油
  - 油价调整
  - 汽油
  - 柴油
```

## 调价窗口计算

- 起始日期: 2026-04-07
- 窗口间隔: 10 个工作日（按中国工作日历，含法定节假日和补班日）
- 使用 `chinese-workdays` 库精确计算

## 输出示例 (--windows-json)

```json
{
  "windows": [
    {"index": 1, "date": "2026-04-07", "weekday": "Tuesday", "is_workday": true},
    {"index": 2, "date": "2026-04-21", "weekday": "Tuesday", "is_workday": true}
  ],
  "config": { ... }
}
```
"""
(skill_dir / "SKILL.md").write_text(skill_md)

# Broken/partial config.yaml left by a previous engineer — wrong values, agent must fix
bad_config = {
    "start_date": "2025-01-01",   # WRONG – should be overridden per task
    "window_interval": 5,          # WRONG – should be 10 per spec
    "check_time": "09:00",
    "timezone": "UTC",             # WRONG
    "ndrc_url": "http://localhost:5099/xwdt/xwfb/",
    "keywords": ["石油"],          # WRONG – incomplete keywords
}
with open(skill_dir / "config.yaml", "w", encoding="utf-8") as f:
    yaml.dump(bad_config, f, allow_unicode=True, default_flow_style=False)

# ── 2. Distractor files (deeply nested, realistic) ─────────────────────────────

# energy-data/
energy_dir = workspace / "energy-data"
(energy_dir / "historical" / "2024").mkdir(parents=True, exist_ok=True)
(energy_dir / "historical" / "2025").mkdir(parents=True, exist_ok=True)
(energy_dir / "forecasts").mkdir(parents=True, exist_ok=True)

(energy_dir / "historical" / "2024" / "q4_prices.csv").write_text(
    "date,gasoline_price,diesel_price,unit\n"
    "2024-10-01,7820,7560,元/吨\n"
    "2024-11-01,7650,7400,元/吨\n"
    "2024-12-01,7580,7320,元/吨\n"
)
(energy_dir / "historical" / "2025" / "q1_prices.csv").write_text(
    "date,gasoline_price,diesel_price,unit\n"
    "2025-01-15,7600,7340,元/吨\n"
    "2025-02-20,7700,7450,元/吨\n"
    "2025-03-21,7550,7290,元/吨\n"
)
(energy_dir / "forecasts" / "2026_model.json").write_text(json.dumps({
    "model": "linear_extrapolation",
    "base_price": 7600,
    "trend": "+1.2%/quarter",
    "note": "Not for production use"
}, ensure_ascii=False, indent=2))
(energy_dir / "README_internal.txt").write_text(
    "Internal energy price archive. Do not distribute.\n"
    "Contact: energy-team@example.com\n"
)

# policy-docs/
policy_dir = workspace / "policy-docs"
(policy_dir / "regulations").mkdir(parents=True, exist_ok=True)
(policy_dir / "circulars").mkdir(parents=True, exist_ok=True)

(policy_dir / "regulations" / "pricing_mechanism_2023.txt").write_text(
    "国家发改委价格司关于完善成品油价格形成机制的通知\n"
    "发改价格[2023] 1845号\n"
    "每10个工作日为一个调价周期，当国际油价变动超过4%时，相应调整国内成品油价格。\n"
)
(policy_dir / "circulars" / "ndrc_2024_q3.pdf.txt").write_text(
    "[PDF placeholder - binary content not shown]\n"
    "Subject: 关于2024年第三季度成品油价格调整的通知\n"
)
(policy_dir / "index.json").write_text(json.dumps({
    "last_updated": "2025-12-01",
    "document_count": 47,
    "categories": ["regulations", "circulars", "notices"]
}, ensure_ascii=False, indent=2))

# monitoring-infra/
infra_dir = workspace / "monitoring-infra"
(infra_dir / "logs").mkdir(parents=True, exist_ok=True)
(infra_dir / "scripts").mkdir(parents=True, exist_ok=True)
(infra_dir / "alerts").mkdir(parents=True, exist_ok=True)

(infra_dir / "logs" / "monitor_2025-12-01.log").write_text(
    "2025-12-01 17:30:01 [INFO] Check triggered\n"
    "2025-12-01 17:30:02 [INFO] Not in window period, skipping\n"
)
(infra_dir / "scripts" / "healthcheck.sh").write_text(
    "#!/bin/bash\ncurl -sf http://localhost:5099/health && echo OK || echo FAIL\n"
)
(infra_dir / "alerts" / "feishu_template.json").write_text(json.dumps({
    "msg_type": "interactive",
    "card": {
        "header": {"title": {"tag": "plain_text", "content": "成品油价格调整提醒"}},
        "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "{{content}}"}}]
    }
}, ensure_ascii=False, indent=2))

# third-party-integrations/
integration_dir = workspace / "third-party-integrations"
(integration_dir / "feishu").mkdir(parents=True, exist_ok=True)
(integration_dir / "wechat").mkdir(parents=True, exist_ok=True)

(integration_dir / "feishu" / "webhook_config_example.yaml").write_text(
    "# Example only - replace with real webhook URL\n"
    "webhook_url: https://open.feishu.cn/open-apis/bot/v2/hook/REPLACE_ME\n"
    "secret: your_signing_secret_here\n"
)
(integration_dir / "wechat" / "corp_api_notes.txt").write_text(
    "WeCom API integration notes\n"
    "corp_id: ww123456789\n"
    "Note: deprecated in favour of Feishu\n"
)

# calendar-utils/ (distractor - looks related but is a different tool)
cal_dir = workspace / "calendar-utils"
(cal_dir / "src").mkdir(parents=True, exist_ok=True)

(cal_dir / "src" / "workday_counter.py").write_text(
    "# Standalone workday counter - NOT the same as chinese-workdays package\n"
    "from datetime import date, timedelta\n\n"
    "def count_workdays(start: date, end: date) -> int:\n"
    "    '''Naive Mon-Fri counter, ignores Chinese holidays'''\n"
    "    count = 0\n"
    "    d = start\n"
    "    while d <= end:\n"
    "        if d.weekday() < 5:\n"
    "            count += 1\n"
    "        d += timedelta(days=1)\n"
    "    return count\n"
)
(cal_dir / "requirements.txt").write_text("# No dependencies\n")
(cal_dir / "DEPRECATED.txt").write_text(
    "This module is deprecated. Use the chinese-workdays package instead.\n"
    "It does NOT account for Chinese public holidays or 补班 (makeup workdays).\n"
)

# old-scripts/ (red herring)
old_dir = workspace / "old-scripts"
old_dir.mkdir(parents=True, exist_ok=True)
(old_dir / "ndrc_scraper_v1.py").write_text(
    "# DEPRECATED scraper - uses wrong date logic\n"
    "# DO NOT USE\n"
    "START_DATE = '2025-01-01'\n"
    "INTERVAL_DAYS = 14  # Wrong! Should be 10 working days, not calendar days\n"
)
(old_dir / "price_alert_v2.py").write_text(
    "# Old alert script - hard-coded webhook\n"
    "WEBHOOK = 'https://open.feishu.cn/EXPIRED'\n"
    "INTERVAL = 7  # Wrong interval\n"
)
(old_dir / "config_backup_20250101.yaml").write_text(
    "start_date: 2025-01-01\nwindow_interval: 7\ncheck_time: 08:00\n"
)

print("Workspace generated successfully.")
print(f"Files created under: {workspace}")