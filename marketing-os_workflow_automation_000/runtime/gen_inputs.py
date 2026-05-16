import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "marketing-os/skills/virtual-cmo",
    "marketing-os/skills/marketing-operator",
    "marketing-os/prompts",
    "marketing-os/schemas",
    "marketing-os/workflows",
    "marketing-os/memory",
    "marketing-os/logs",
    "marketing-os/configs",
    "marketing-os/adapters",
    "company-data/raw-signals",
    "company-data/competitors",
    "company-data/audience-research",
    "company-data/financials",
    "internal-docs/legal",
    "internal-docs/product",
    "internal-docs/hr",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── SKILL.md (the actual skill documentation) ────────────────────────────────
skill_md = r"""---
name: marketing-os
description: AI Agent 营销操作系统
tags: [marketing, strategy, campaign-management]
version: "1.0.0"
---

# Marketing OS

## 技能调用格式

```yaml
skill: marketing-os
input:
  mode: market_discovery | offer_selection | campaign_planning | execution_sprint
  business_context:
    company_name: "公司名称"
    products: ["产品1", "产品2"]
    target_market: "目标市场"
    budget_range: "预算范围"
    brand_positioning: "品牌定位"
  market_data:
    search_trends: []
    competitor_moves: []
    audience_signals: []
  mission_id: "xxx"
  auto_mode: false
```

## Virtual CMO — 战略分析

**执行步骤**：
```
Step 1: 收集市场数据（信号、趋势、竞争对手动态）
Step 2: 分析信号 — 分类、评分（signal_strength 1-10）
Step 3: 识别机会 — 聚类相关信号，评估市场规模/竞争/匹配度
Step 4: 计算优先级 — priority_score = (信号强度×0.3) + (市场规模×0.25) + (能力匹配×0.25) + (紧迫度×0.2)
Step 5: 生成策略 — 定位、渠道推荐、KPI、风险评估
Step 6: 输出任务简报 — 传递给 Marketing Operator
```

**输出格式**（CMO Output）：
```json
{
  "analysis_id": "UUID",
  "market_opportunities": [{"title": "...", "priority_score": 85, "confidence": "high"}],
  "target_segments": [{"name": "...", "pain_points": ["..."]}],
  "recommended_actions": [{"action": "...", "priority": "high", "owner": "operator"}],
  "risks": [{"description": "...", "severity": 7, "mitigation": "..."}],
  "next_steps": [{"action": "...", "owner": "operator", "deadline_type": "immediate"}],
  "confidence_level": 78
}
```

## Marketing Operator — 任务执行

**执行步骤**：
```
Step 1: 验证 CMO Mission Brief
Step 2: 任务分解 — 将 action 拆成原子任务（每个任务有 owner/deadline/expected_result）
Step 3: 资源分配 — 预算、渠道、工具映射
Step 4: Campaign 组装 — 聚合任务，设置 KPI 目标
Step 5: 执行追踪 — 状态管理（pending → in_progress → completed/blocked/failed）
Step 6: 指标收集 — 量化（曝光/点击/转化）+ 定性（互动质量/品牌感知）
Step 7: 生成反馈 — 向 CMO 报告结果、学习、建议调整
```

## 协作协议

CMO → Operator 通信格式：
```json
{
  "mission_id": "UUID",
  "objective": "明确的可衡量目标",
  "target_audience": {"segment_name": "...", "pain_points": ["..."]},
  "strategy": {"positioning": "...", "approach": "..."},
  "priority": "critical | high | medium | low",
  "recommended_channels": [{"channel": "LinkedIn", "priority_rank": 1}],
  "actions": [{"action": "...", "priority": "high"}],
  "success_criteria": {"primary_kpi": {"metric": "conversions", "target": "100"}}
}
```

Operator → CMO 反馈格式：
```json
{
  "feedback_id": "UUID",
  "execution_result": "事实总结",
  "metrics": {"impressions": 15000, "clicks": 450, "conversions": 23},
  "learnings": ["[MEASURED] LinkedIn 数据驱动标题 3x 互动率"],
  "recommendations": ["将 30% 预算从 Display 转移到 LinkedIn"]
}
```

## 行为规则

> [!IMPORTANT]
> - ❌ 不允许模糊建议（"考虑"、"或许"、"可以试试" 一律禁止）
> - ✅ 必须给出优先级（critical / high / medium / low）
> - ✅ 必须给出下一步行动
> - ✅ 必须给出风险评估
> - ✅ 必须区分 [FACT] / [INFERENCE] / [RECOMMENDATION]
> - ✅ 信号强度 < 4 必须标记 "uncertain"
> - ✅ 信息不足必须明确声明 "INSUFFICIENT DATA"
"""

with open(os.path.join(WORKSPACE, "marketing-os", "SKILL.md"), "w") as f:
    f.write(skill_md)

# ── Raw messy market signals (the "problem input") ───────────────────────────
# These are intentionally messy, unstructured, with some signals having strength < 4
raw_signals = {
    "data_dump_date": "2026-03-15",
    "source": "mixed-internal-external",
    "signals": [
        {
            "id": "sig_001",
            "raw_text": "CFO survey Q1-2026: 67% of mid-market CFOs cite real-time cash visibility as top pain point",
            "category": "audience_pain_point",
            "signal_strength": 8,
            "market_size_score": 7,
            "capability_match_score": 9,
            "urgency_score": 8
        },
        {
            "id": "sig_002",
            "raw_text": "Google Trends: searches for 'treasury management software' up 43% YoY in North America",
            "category": "search_trend",
            "signal_strength": 7,
            "market_size_score": 8,
            "capability_match_score": 7,
            "urgency_score": 6
        },
        {
            "id": "sig_003",
            "raw_text": "Competitor Kyriba raised $160M Series E, expanding into SMB segment",
            "category": "competitor_move",
            "signal_strength": 6,
            "market_size_score": 9,
            "capability_match_score": 6,
            "urgency_score": 7
        },
        {
            "id": "sig_004",
            "raw_text": "Unverified rumor: some banks may offer integrated treasury tools — no official announcement",
            "category": "competitor_move",
            "signal_strength": 3,
            "market_size_score": 5,
            "capability_match_score": 4,
            "urgency_score": 3
        },
        {
            "id": "sig_005",
            "raw_text": "LinkedIn engagement: posts about 'working capital optimization' averaging 4.2% engagement rate among CFO audience",
            "category": "audience_signal",
            "signal_strength": 6,
            "market_size_score": 6,
            "capability_match_score": 8,
            "urgency_score": 5
        },
        {
            "id": "sig_006",
            "raw_text": "Internal product team estimate: real-time treasury feature ready in 6 weeks",
            "category": "internal_capability",
            "signal_strength": 2,
            "market_size_score": 0,
            "capability_match_score": 9,
            "urgency_score": 8
        }
    ]
}

with open(os.path.join(WORKSPACE, "company-data/raw-signals", "market_signals_q1_2026.json"), "w") as f:
    json.dump(raw_signals, f, indent=2)

# ── Business context file ────────────────────────────────────────────────────
business_context = {
    "company_name": "CashLens Analytics",
    "products": ["CashLens Pro (real-time treasury management)", "CashLens Lite (basic cash flow)"],
    "target_market": "Mid-market CFOs, North America, companies $50M-$500M revenue",
    "budget_range": "$120,000 USD for Q2 launch campaign",
    "brand_positioning": "The only real-time treasury intelligence platform built for speed-obsessed CFOs"
}

with open(os.path.join(WORKSPACE, "company-data", "business_context.json"), "w") as f:
    json.dump(business_context, f, indent=2)

# ── Distractor files ─────────────────────────────────────────────────────────
# Old outdated marketing plan (wrong format, should be ignored)
with open(os.path.join(WORKSPACE, "marketing-os/memory", "old_campaigns_2024.json"), "w") as f:
    json.dump({"campaigns": [], "note": "deprecated — 2024 data only", "format_version": "0.3"}, f, indent=2)

# Partial/broken schema files (distractors)
with open(os.path.join(WORKSPACE, "marketing-os/schemas", "cmo_output.schema.json"), "w") as f:
    json.dump({"$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
               "note": "stub — see SKILL.md for canonical format"}, f, indent=2)

with open(os.path.join(WORKSPACE, "marketing-os/schemas", "cmo_to_operator.schema.json"), "w") as f:
    json.dump({"$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
               "note": "stub — see SKILL.md for canonical format"}, f, indent=2)

# Competitor research noise file
with open(os.path.join(WORKSPACE, "company-data/competitors", "kyriba_notes.txt"), "w") as f:
    f.write("Kyriba Series E: $160M. Focus: enterprise. Moving into SMB. Watch for pricing pressure.\n"
            "Other players: Coupa Treasury, GTreasury, ION. All enterprise-focused.\n")

with open(os.path.join(WORKSPACE, "company-data/audience-research", "icp_notes.txt"), "w") as f:
    f.write("ICP: CFO at mid-market manufacturing/distribution firm. Pain: manual treasury ops, "
            "Excel-based cash forecasting, no real-time visibility.\n"
            "Channels: LinkedIn (primary), CFO Connect community, Gartner Peer Insights.\n")

with open(os.path.join(WORKSPACE, "company-data/financials", "q1_budget.txt"), "w") as f:
    f.write("Q1 actual spend: $34,200. Q2 allocated: $120,000. Breakdown TBD by marketing.\n")

# Workflow stubs
with open(os.path.join(WORKSPACE, "marketing-os/workflows", "market_discovery.flow.json"), "w") as f:
    json.dump({"flow_id": "market_discovery", "steps": [], "status": "template"}, f, indent=2)

with open(os.path.join(WORKSPACE, "marketing-os/workflows", "campaign_planning.flow.json"), "w") as f:
    json.dump({"flow_id": "campaign_planning", "steps": [], "status": "template"}, f, indent=2)

# Config stub
with open(os.path.join(WORKSPACE, "marketing-os/configs", "system.config.json"), "w") as f:
    json.dump({"version": "1.0.0", "auto_mode": False, "adapters": {}}, f, indent=2)

# Log stub
with open(os.path.join(WORKSPACE, "marketing-os/logs", "execution.log"), "w") as f:
    f.write("# Execution log — empty, awaiting first run\n")

# HR/Legal distractors
with open(os.path.join(WORKSPACE, "internal-docs/legal", "privacy_policy_draft.txt"), "w") as f:
    f.write("Draft privacy policy — not relevant to marketing OS.\n")

with open(os.path.join(WORKSPACE, "internal-docs/hr", "headcount_plan.txt"), "w") as f:
    f.write("Marketing headcount: 2 FTE planned for Q2. Hiring Sr. Content Marketer.\n")

with open(os.path.join(WORKSPACE, "internal-docs/product", "roadmap_q2.txt"), "w") as f:
    f.write("Real-time treasury feature: ETA 6 weeks. API integrations: NetSuite, SAP.\n")

# Adapter stubs
with open(os.path.join(WORKSPACE, "marketing-os/adapters", "crm.adapter.md"), "w") as f:
    f.write("# CRM Adapter\nStatus: not configured. Placeholder only.\n")

with open(os.path.join(WORKSPACE, "marketing-os/adapters", "content.adapter.md"), "w") as f:
    f.write("# Content Adapter\nStatus: not configured. Placeholder only.\n")

print("Workspace initialized successfully.")
print(f"Key input files:")
print(f"  - {WORKSPACE}/company-data/raw-signals/market_signals_q1_2026.json")
print(f"  - {WORKSPACE}/company-data/business_context.json")
print(f"  - {WORKSPACE}/marketing-os/SKILL.md")