import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Deep distractor directory structure ──────────────────────────────────────
dirs = [
    "logs/archive/2024",
    "logs/archive/2023",
    "logs/current",
    "config/openclaw",
    "config/network",
    "data/faa_cache",
    "data/easa_cache",
    "data/caac_cache",
    "data/mro_feeds",
    "scripts/utils",
    "reports/archive",
    "tmp/scratch",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "logs/archive/2024/openclaw_2024-01-15.log": "INFO: openclaw started\nINFO: health check passed\nWARN: disk usage 78%\n",
    "logs/archive/2023/system_summary.log": "System OK - legacy log\n",
    "logs/current/access.log": "GET /api/health 200\nGET /api/status 200\n",
    "config/openclaw/settings.yaml": "host: localhost\nport: 8080\ntimeout: 30\n",
    "config/network/firewall.conf": "ALLOW tcp 443\nALLOW tcp 80\nDENY ALL\n",
    "data/faa_cache/faa_ads_raw.json": json.dumps({
        "ads": [
            {"id": "2024-NE-01", "subject": "CFM56 Engine Inspection", "effective": "2024-01-10"},
            {"id": "2024-SW-03", "subject": "Boeing 737 Wing Spar", "effective": "2024-01-12"},
            {"id": "2024-NM-07", "subject": "LEAP-1B Fuel System", "effective": "2024-01-14"},
        ],
        "fetched_at": "2024-01-15T08:00:00Z"
    }, ensure_ascii=False, indent=2),
    "data/easa_cache/easa_ads_raw.json": json.dumps({
        "ads": [
            {"id": "EASA-2024-0012", "type": "Emergency AD", "subject": "Trent 1000 Turbine Blade"},
            {"id": "EASA-2024-0018", "type": "AD", "subject": "A320 EFIS Display Unit"},
        ],
        "fetched_at": "2024-01-15T08:00:00Z"
    }, ensure_ascii=False, indent=2),
    "data/caac_cache/caac_ads_raw.json": json.dumps({
        "ads": [
            {"id": "CAAC-2024-001", "subject": "C919 TCAS Upgrade"},
        ],
        "fetched_at": "2024-01-15T08:00:00Z"
    }, ensure_ascii=False, indent=2),
    "data/mro_feeds/industry_news.json": json.dumps({
        "articles": [
            {"title": "Boeing 737 MAX Fleet Update", "source": "Simple Flying", "date": "2024-01-15"},
            {"title": "Airbus A220 Landing Gear AD", "source": "Leeham News", "date": "2024-01-14"},
            {"title": "PW1100G Engine Inspection Campaign", "source": "Avionics International", "date": "2024-01-13"},
            {"title": "CAAC Issues Emergency Directive", "source": "Air Cargo News", "date": "2024-01-15"},
            {"title": "FAA ADS-B Mandate Update", "source": "Aviation Herald", "date": "2024-01-14"},
        ],
        "fetched_at": "2024-01-15T08:00:00Z"
    }, ensure_ascii=False, indent=2),
    "scripts/utils/fetch_ads.py": "#!/usr/bin/env python3\n# Utility to fetch AD data\nprint('fetch_ads: not implemented')\n",
    "reports/archive/healthcheck_2024-01-14.txt": "Old report - archived\n",
    "tmp/scratch/temp_parse.json": '{"status": "temp"}\n',
    "config/cron_schedule.txt": "aviation-healthcheck:daily @ 09:00,15:00,21:00\n",
}

for rel_path, content in distractors.items():
    fp = workspace / rel_path
    fp.write_text(content, encoding="utf-8")

print("Distractor files created.")

# ── SKILL.md placement ────────────────────────────────────────────────────────
skill_md = r"""---
name: aviation-healthcheck
description: 航空维修健康检查 - FAA/EASA/CAAC适航指令、航空安全通告、MRO行业新闻、波音空客技术通告、OpenClaw状态、磁盘空间
---

# 航空维修健康检查系统

## 概述

贾维斯的航空维修资讯与系统健康双重检查。

## 检查项目

### 1. 航空维修资讯 (每日)

#### FAA Airworthiness Directives (AD)
- **来源**: https://ad.faa.gov
- **关注**: 发动机、电子系统、结构相关AD
- **频率**: 每日检查

#### EASA Airworthiness Directives
- **来源**: https://ad.easa.europa.eu
- **关注**: 紧急AD、发动机相关指令
- **频率**: 每日检查

#### CAAC适航指令
- **来源**: https://www.caac.gov.cn (适航审定司)
- **关注**: 国内航空公司受影响的相关指令
- **频率**: 每日检查

#### 航空安全通告
- FAA Safety Alerts: https://www.faa.gov/news/safety_alerts
- EASA Safety Information: https://www.easa.europa.eu/safety-info

#### MRO行业新闻
- Avionics International: https://www.aviationtoday.com/category/mro/
- Leeham News: https://leehamnews.com
- Simple Flying: https://simpleflying.com
- Air Cargo News: https://aircargonews.com
- Aviation Herald: https://avherald.com

#### 波音/空客服务通告
- Boeing ADS: https://myboeingfleet.com
- Airbus Airworthiness: https://myairbusfleet.com

### 2. 系统健康检查

#### OpenClaw 状态
```bash
openclaw status
openclaw health --json
```

#### 磁盘空间
```bash
df -h
```

#### 安全审计
```bash
openclaw security audit
openclaw update status
```

## 执行流程

1. **航空资讯收集**: 搜索并汇总最新适航指令和行业新闻
2. **系统状态检查**: OpenClaw 运行状态、磁盘空间
3. **生成报告**: 输出格式化检查报告

## 输出格式

```
═══════════════════════════════════════
        ✈️ 航空维修健康检查报告
═══════════════════════════════════════

📅 检查时间: YYYY-MM-DD HH:mm

【航空资讯更新】
✓ FAA AD: X 条新指令
✓ EASA AD: X 条新指令  
✓ CAAC: X 条新指令
✓ 行业新闻: X 条更新
✓ 重要事件: X 条

【系统状态】
✓ OpenClaw: 运行中/异常
✓ 磁盘空间: XX% 可用
✓ 安全审计: 通过/需关注

【建议事项】
• ...

═══════════════════════════════════════
```

## Cron 调度建议

建议每日定时执行 (通过 openclaw cron add):

- `aviation-healthcheck:daily` - 每日航空资讯 + 系统检查
- 时间: 09:00, 15:00, 21:00 (参考 HEARTBEAT.md)

## 资讯关键词

搜索时关注:
- Engine (发动机): CFM56, LEAP, PW1100G, Trent 1000
- Avionics (航空电子): EFIS, FMS, TCAS, ADS-B
- Structure (结构): Fuselage, Wing, Landing Gear
- Airworthiness (适航): AD, Emergency AD, SFAR
"""
(workspace / "SKILL.md").write_text(skill_md, encoding="utf-8")
print("SKILL.md written.")

print("All gen_inputs done.")