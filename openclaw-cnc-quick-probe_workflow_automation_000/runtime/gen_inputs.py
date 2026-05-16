import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory Structure ---
dirs = [
    "skills",
    "inquiries/incoming",
    "inquiries/processed",
    "inquiries/archived",
    "config",
    "logs",
    "templates",
    "reports/daily",
    "reports/monthly",
    "system/routing",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- SKILL.md placed in workspace/skills/ ---
skill_md = """\
---
name: cnc-quick-probe
version: 1.0.0
priority: P1
description: "CNC快速探明 - 5参数快速收敛。当报价请求参数不全时自动触发，收集材料、数量、精度、表面处理、Ra。收敛度≥80%后自动执行报价。"
author: 海狸 🦫
triggers:
  - 报价参数不全
  - 无图纸报价
  - CNC报价探明
auto_route: true
---

# CNC快速探明 Skill

## 触发条件

| 条件 | 说明 |
|------|------|
| 意图 = CNC报价 | 识别到报价请求 |
| 收敛度 < 80% | 参数不完整 |
| 无文件/文件解析失败 | 缺少STEP/PDF |

## 执行流程

```
检测触发条件
    ↓
启动参数收集器
    ↓
生成5参数提问
    ↓
等待用户回答
    ↓
更新收敛度
    ↓
┌─ ≥80% → 调用报价Skill
└─ <80% → 继续追问
```

## 5个关键参数

| # | 参数 | 必需 | 默认值 |
|---|------|------|--------|
| 1 | 材料 | ✅ | 铝合金6061 |
| 2 | 数量 | ✅ | 1件 |
| 3 | 精度 | ✅ | ±0.1mm |
| 4 | 表面处理 | ✅ | 本色 |
| 5 | Ra | ❌ | Ra 3.2 |

## 输出格式

```
📋 参数收集（收敛度：XX%）

❓ 请提供以下信息：

1. 🔴【材料】？
   □ 铝合金6061
   □ 不锈钢304
   ...

2. 🔴【数量】？
   □ 1件（打样）
   □ 批量
   ...

（继续其他参数）

回复示例：材料6061，数量10件，精度±0.05
```

## 自动路由规则

```python
# 在UniSkill V4中的路由逻辑
if intent == "cnc_quote" and convergence < 0.8:
    # 自动路由到 cnc-quick-probe
    return route_to_skill("cnc-quick-probe", context)
```

## 与其他Skill的关系

```
UniSkill V4 (主入口)
    ├── cnc-quick-probe (参数收集)
    │       ↓ (收敛后)
    └── cnc-quote-system (执行报价)
```

---

🦫 海狸 | 靠得住、能干事、在状态
"""
with open(os.path.join(WORKSPACE, "skills", "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# --- Customer Inquiry JSON Files ---
# inquiry_001: 0 mandatory params provided → convergence 0%
inquiry_001 = {
    "inquiry_id": "INQ-001",
    "customer": "苏州科达机械有限公司",
    "intent": "cnc_quote",
    "message": "你好，我需要加工一批零件，请报价。",
    "provided_params": {}
}

# inquiry_002: 2 mandatory params (材料, 数量) → convergence 50%
inquiry_002 = {
    "inquiry_id": "INQ-002",
    "customer": "深圳精密制造厂",
    "intent": "cnc_quote",
    "message": "材料用不锈钢304，数量50件，其他不清楚。",
    "provided_params": {
        "材料": "不锈钢304",
        "数量": "50件"
    }
}

# inquiry_003: 3 mandatory params (材料, 数量, 精度) → convergence 75%
inquiry_003 = {
    "inquiry_id": "INQ-003",
    "customer": "上海远鑫精工",
    "intent": "cnc_quote",
    "message": "铝合金6061，10件，精度要求±0.05mm",
    "provided_params": {
        "材料": "铝合金6061",
        "数量": "10件",
        "精度": "±0.05mm"
    }
}

# inquiry_004: all 4 mandatory params → convergence 100% → auto-route
inquiry_004 = {
    "inquiry_id": "INQ-004",
    "customer": "宁波海天精工股份",
    "intent": "cnc_quote",
    "message": "钛合金TC4，3件，精度±0.02mm，表面阳极氧化",
    "provided_params": {
        "材料": "钛合金TC4",
        "数量": "3件",
        "精度": "±0.02mm",
        "表面处理": "阳极氧化"
    }
}

# inquiry_005: all 4 mandatory + Ra → convergence 100% → auto-route
inquiry_005 = {
    "inquiry_id": "INQ-005",
    "customer": "成都航空精密部件厂",
    "intent": "cnc_quote",
    "message": "铝合金7075，100件，±0.01mm，喷砂处理，Ra0.8",
    "provided_params": {
        "材料": "铝合金7075",
        "数量": "100件",
        "精度": "±0.01mm",
        "表面处理": "喷砂",
        "Ra": "Ra 0.8"
    }
}

for fname, data in [
    ("inquiry_001.json", inquiry_001),
    ("inquiry_002.json", inquiry_002),
    ("inquiry_003.json", inquiry_003),
    ("inquiry_004.json", inquiry_004),
    ("inquiry_005.json", inquiry_005),
]:
    with open(os.path.join(WORKSPACE, "inquiries", "incoming", fname), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Distractor Files ---

# Old config file
with open(os.path.join(WORKSPACE, "config", "router_config.yaml"), "w") as f:
    f.write("""\
version: 3
routing:
  default_skill: cnc-legacy-probe
  timeout: 30
  retry: 2
deprecated_skills:
  - cnc-manual-probe
  - cnc-v2-probe
""")

# Outdated skill definition
with open(os.path.join(WORKSPACE, "skills", "cnc-legacy-probe.md"), "w", encoding="utf-8") as f:
    f.write("""\
# CNC Legacy Probe (DEPRECATED v0.9)
## Parameters
- Material (required)
- Quantity (required)
- Tolerance (required)
- Finish (optional)
## Convergence Threshold: 70%
## Output: Plain text, no emoji
""")

# Log files
with open(os.path.join(WORKSPACE, "logs", "system_2024-01-15.log"), "w") as f:
    f.write("\n".join([
        "[INFO] 2024-01-15 08:00:01 Router initialized",
        "[INFO] 2024-01-15 08:01:22 INQ-000 routed to cnc-legacy-probe",
        "[WARN] 2024-01-15 08:02:11 Convergence check failed: threshold mismatch",
        "[ERROR] 2024-01-15 08:05:44 Skill not found: cnc-quick-probe",
    ]))

with open(os.path.join(WORKSPACE, "logs", "errors_2024-01-14.log"), "w") as f:
    f.write("No errors recorded.\n")

# CSV distractor
with open(os.path.join(WORKSPACE, "reports", "daily", "quote_summary_2024-01-14.csv"), "w") as f:
    f.write("inquiry_id,customer,status,amount\n")
    f.write("INQ-001,OldCo,pending,0\n")
    f.write("INQ-002,AnotherCo,quoted,1200\n")

# Template file (misleading)
with open(os.path.join(WORKSPACE, "templates", "probe_template_v2.txt"), "w", encoding="utf-8") as f:
    f.write("""\
[DEPRECATED TEMPLATE - DO NOT USE]
Parameters needed: material, qty, tolerance
Threshold: 70%
Format: plain text
""")

with open(os.path.join(WORKSPACE, "templates", "quote_template.txt"), "w", encoding="utf-8") as f:
    f.write("""\
Quote Reference: {quote_id}
Customer: {customer}
Total: {amount} CNY
""")

# Routing rules (old, conflicting)
with open(os.path.join(WORKSPACE, "system", "routing", "rules_v3.json"), "w") as f:
    json.dump({
        "version": "3.0",
        "rules": [
            {"intent": "cnc_quote", "convergence_threshold": 0.7, "route_to": "cnc-legacy-probe"},
            {"intent": "cnc_quote", "convergence_threshold": 0.9, "route_to": "cnc-quote-system"}
        ]
    }, f, indent=2)

# Archived inquiry
with open(os.path.join(WORKSPACE, "inquiries", "archived", "inquiry_old_001.json"), "w", encoding="utf-8") as f:
    json.dump({
        "inquiry_id": "INQ-OLD-001",
        "customer": "Legacy Corp",
        "intent": "cnc_quote",
        "message": "旧询价记录",
        "provided_params": {"材料": "铝合金6061"},
        "status": "archived",
        "note": "processed by old system, do not reprocess"
    }, f, ensure_ascii=False, indent=2)

# Monthly report
with open(os.path.join(WORKSPACE, "reports", "monthly", "jan_2024_summary.txt"), "w") as f:
    f.write("January 2024 CNC Quote Summary\nTotal inquiries: 42\nConverted: 31\nAbandoned: 11\n")

# System note
with open(os.path.join(WORKSPACE, "system", "UPGRADE_NOTES.txt"), "w") as f:
    f.write("""\
System upgrade from V3 to V4 completed 2024-01-01.
Old convergence threshold (70%) replaced by new skill-specific values.
Do NOT use legacy routing rules for new inquiries.
Refer to individual SKILL.md files for current thresholds.
""")

print("Workspace generated successfully.")
print(f"Inquiry files created in: {WORKSPACE}/inquiries/incoming/")
print(f"SKILL.md located at: {WORKSPACE}/skills/SKILL.md")