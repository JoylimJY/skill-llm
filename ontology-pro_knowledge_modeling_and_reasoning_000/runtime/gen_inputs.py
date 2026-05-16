import os
import json
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "references",
    "scripts",
    "data/raw",
    "data/processed",
    "data/archive",
    "reports/2024Q1",
    "reports/2024Q2",
    "reports/2024Q3",
    "models/v1",
    "models/v2",
    "logs",
    "config",
    "tmp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── SKILL reference documents ────────────────────────────────────────────────

(workspace / "references" / "cognitive-graph.md").write_text("""# Cognitive Graph — 三元组抽取协议

## 实体类型（Entity Types）
- concept  : 抽象概念、体系、方法论
- actor    : 机构、公司、角色
- event    : 事件、现象、状态变化
- product  : 具体产品、物质、组件
- region   : 地理区域、市场区域
- metric   : 可量化指标

## 关系类型（Relation Types）
- includes   : A 包含 B
- causes     : A 导致 B
- depends_on : A 依赖于 B
- produces   : A 生产 B
- affects    : A 影响 B
- belongs_to : A 属于 B
- located_in : A 位于 B
- competes_with : A 竞争于 B

## 三元组抽取规则
1. 每个实体必须有唯一 ID（格式 e001, e002, ...，全局唯一，合并时不重置）
2. 每条关系的 source 和 target 必须引用有效实体 ID（而非名称）
3. 关系权重 weight 取值范围 [0.0, 1.0]，反映证据强度
4. evidence 字段引用原文或推理依据
5. 实体 attributes 字段包含 category 和 aliases 两个子字段
""", encoding="utf-8")

(workspace / "references" / "reasoning-engine.md").write_text("""# Reasoning Engine — 推理引擎模板

## 推理步骤
1. **因果关系识别**：从图谱中寻找 causes / affects 类关系链
2. **关键变量提取**：识别出现频次高、连接度高的核心实体
3. **路径探索**：从风险源实体出发，追踪到最终影响实体的完整路径
4. **推理链输出**：每个推理步骤需标注参与实体 ID 和关系类型

## 推理链格式
```
[因果链] EntityA (e00x) --causes--> EntityB (e00y) --affects--> EntityC (e00z)
[关键变量] e00x: <名称>, e00y: <名称>
[路径] e00x → e00y → e00z (风险传导路径)
```
""", encoding="utf-8")

(workspace / "references" / "strategy-output.md").write_text("""# Strategy Output — 决策输出模板

## 策略优先级分级
- **P0（紧急）**：需立即行动，影响核心业务连续性
- **P1（重要）**：需在 30 天内响应，影响中期竞争力
- **P2（可选）**：在资源允许时推进，属于优化项

## 输出格式
每条策略必须包含：
- 优先级标签（P0 / P1 / P2）
- 具体行动项（动词开头）
- 关联风险点说明

## 策略文件结构（JSON）
```json
{
  "strategy_version": "1.0",
  "domain": "<领域>",
  "generated_at": "<ISO8601时间戳>",
  "reasoning_summary": "<多步推理摘要>",
  "strategies": [
    {
      "priority": "P0",
      "action": "<具体行动>",
      "risk": "<关联风险>",
      "entity_refs": ["e001", "e002"]
    }
  ]
}
```
""", encoding="utf-8")

(workspace / "references" / "memory-protocol.md").write_text("""# Memory Protocol — 持久记忆协议

## 存储格式
图谱以 JSON 存储，核心结构：
```json
{
  "version": "1.0.0",
  "domain": "<领域>",
  "updated_at": "<ISO8601带时区>",
  "entities": [...],
  "relations": [...],
  "metadata": {
    "total_entities": <int>,
    "total_relations": <int>,
    "sessions_analyzed": <int>
  }
}
```

## 增量更新规则
1. **实体去重**：按 entity.name 去重，已存在的实体保留原 ID，仅合并新属性
2. **关系去重**：source+target+type 三元组相同则视为重复，不追加
3. **sessions_analyzed**：每次增量更新 +1（不得重置）
4. **total_entities / total_relations**：更新后重新计数实际值
5. **version**：主版本号不变，次版本号 +1（如 1.0.0 → 1.1.0）
6. **ID 连续性**：新实体 ID 在全局最大 ID 基础上递增，不得重用或重置

## 加载上下文
合并时以现有图谱为基础，新数据作为增量追加。
""", encoding="utf-8")

# ── stub scripts (agents must NOT replace these, they already exist) ─────────

(workspace / "scripts" / "graph_visualize.py").write_text("""#!/usr/bin/env python3
\"\"\"Generates a Mermaid diagram string from a knowledge graph JSON file.\"\"\"
import json, sys
from pathlib import Path

def visualize(graph_path: str) -> str:
    g = json.loads(Path(graph_path).read_text(encoding='utf-8'))
    id2name = {e['id']: e['name'] for e in g.get('entities', [])}
    lines = ['graph LR']
    for r in g.get('relations', []):
        src = id2name.get(r['source'], r['source'])
        tgt = id2name.get(r['target'], r['target'])
        lines.append(f'  {r["source"]}["{src}"] -->|{r["type"]}| {r["target"]}["{tgt}"]')
    return '\\n'.join(lines)

if __name__ == '__main__':
    print(visualize(sys.argv[1]))
""", encoding="utf-8")

(workspace / "scripts" / "memory_manager.py").write_text("""#!/usr/bin/env python3
\"\"\"Knowledge graph persistence manager.\"\"\"
import json, sys
from pathlib import Path
from datetime import datetime, timezone

def load_graph(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save_graph(graph: dict, path: str):
    Path(path).write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding='utf-8')

def merge_graphs(base: dict, increment: dict) -> dict:
    existing_names = {e['name'] for e in base['entities']}
    max_id = max((int(e['id'][1:]) for e in base['entities']), default=0)
    for e in increment.get('entities', []):
        if e['name'] not in existing_names:
            max_id += 1
            e['id'] = f'e{max_id:03d}'
            base['entities'].append(e)
            existing_names.add(e['name'])
    existing_rels = {(r['source'], r['target'], r['type']) for r in base['relations']}
    for r in increment.get('relations', []):
        key = (r['source'], r['target'], r['type'])
        if key not in existing_rels:
            base['relations'].append(r)
            existing_rels.add(key)
    base['metadata']['total_entities'] = len(base['entities'])
    base['metadata']['total_relations'] = len(base['relations'])
    base['metadata']['sessions_analyzed'] += 1
    parts = base['version'].split('.')
    parts[1] = str(int(parts[1]) + 1)
    base['version'] = '.'.join(parts)
    base['updated_at'] = datetime.now(timezone.utc).isoformat()
    return base

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'load':
        print(json.dumps(load_graph(sys.argv[2]), ensure_ascii=False, indent=2))
    elif cmd == 'merge':
        base = load_graph(sys.argv[2])
        inc  = load_graph(sys.argv[3])
        merged = merge_graphs(base, inc)
        save_graph(merged, sys.argv[2])
        print(f'Merged. entities={merged[\"metadata\"][\"total_entities\"]} relations={merged[\"metadata\"][\"total_relations\"]} sessions={merged[\"metadata\"][\"sessions_analyzed\"]}')
""", encoding="utf-8")

# ── EXISTING knowledge graph (session 1, already analysed) ───────────────────
# This is the "base" graph the agent must load and INCREMENTALLY update.

session1_graph = {
    "version": "1.0.0",
    "domain": "pharmaceutical_supply_chain",
    "updated_at": "2024-11-15T08:00:00+00:00",
    "entities": [
        {
            "id": "e001",
            "name": "Active Pharmaceutical Ingredient",
            "type": "product",
            "attributes": {"category": "raw_material", "aliases": ["API", "原料药"]}
        },
        {
            "id": "e002",
            "name": "China",
            "type": "region",
            "attributes": {"category": "geography", "aliases": ["中国", "PRC"]}
        },
        {
            "id": "e003",
            "name": "Contract Manufacturing Organization",
            "type": "actor",
            "attributes": {"category": "supplier", "aliases": ["CMO", "合同生产商"]}
        },
        {
            "id": "e004",
            "name": "FDA Approval",
            "type": "event",
            "attributes": {"category": "regulatory", "aliases": ["FDA审批", "NDA"]}
        },
        {
            "id": "e005",
            "name": "Supply Disruption",
            "type": "event",
            "attributes": {"category": "risk", "aliases": ["供应中断", "短缺"]}
        }
    ],
    "relations": [
        {
            "source": "e002",
            "target": "e001",
            "type": "produces",
            "weight": 0.9,
            "evidence": "China produces >70% of global APIs"
        },
        {
            "source": "e003",
            "target": "e001",
            "type": "produces",
            "weight": 0.75,
            "evidence": "CMOs are primary API manufacturers"
        },
        {
            "source": "e005",
            "target": "e004",
            "type": "affects",
            "weight": 0.6,
            "evidence": "Supply disruptions can delay FDA submission timelines"
        }
    ],
    "metadata": {
        "total_entities": 5,
        "total_relations": 3,
        "sessions_analyzed": 1
    }
}

(workspace / "data" / "raw" / "pharma_graph_session1.json").write_text(
    json.dumps(session1_graph, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── NEW raw intelligence brief the agent must analyze ─────────────────────────
# Messy, unstructured prose — agent must extract entities/relations from this.

brief = """PHARMA SUPPLY CHAIN INTELLIGENCE BRIEF — Q4 2024
Prepared by: Global Risk Desk
Classification: Internal

OVERVIEW
The global pharmaceutical supply chain is under stress following three converging pressures:
geopolitical tension, post-pandemic demand normalization, and accelerating regulatory divergence.

KEY FINDINGS

1. INDIA CONCENTRATION RISK
India has emerged as the dominant supplier of generic finished-dose formulations (FDFs),
accounting for approximately 40% of US generic drug imports. However, the Indian Pharmaceutical
Alliance (IPA) has flagged severe power shortages in Gujarat and Telangana states, threatening
production continuity at over 120 manufacturing sites. The IPA depends heavily on Chinese API
supply, creating a two-tier concentration risk.

2. COLD CHAIN INFRASTRUCTURE GAPS
Biologic drugs (monoclonal antibodies, mRNA vaccines) require continuous -20°C to -80°C cold
chain logistics. Logistics providers such as DHL Supply Chain and Kuehne+Nagel have reported
capacity shortfalls of 15–22% in the South-East Asia corridor, directly affecting drug delivery
timelines. Cold chain failures cause drug degradation, resulting in patient safety events.

3. REGULATORY DIVERGENCE
The European Medicines Agency (EMA) has issued new Good Manufacturing Practice (GMP) guidelines
(EMA/GMP-2024) requiring dual-source validation for all critical APIs by 2026. Non-compliance
risks market withdrawal. Meanwhile, the US FDA 21 CFR Part 211 remains unchanged, creating
compliance asymmetry for companies exporting to both markets.

4. SINGLE-SOURCE DEPENDENCY
An internal audit across 34 hospital systems revealed that 28% of essential medicines are
single-source: only one qualified supplier exists globally. Single-source dependency is the
primary driver of drug shortages, per the WHO Essential Medicines List analysis.

5. NEARSHORING TREND
Major pharmaceutical companies (Pfizer, Novartis, Roche) are investing in nearshoring
manufacturing to Mexico and Eastern Europe (Poland, Czech Republic) to reduce geopolitical
exposure. This trend is expected to reduce China/India concentration risk by 15–20% by 2028,
but requires 5–7 years of capital expenditure and technology transfer.

CONCLUSION
The convergence of geographic concentration, infrastructure gaps, and regulatory divergence
creates a compounded systemic risk to drug availability. Immediate dual-sourcing mandates and
cold-chain investment are the highest-priority mitigations.
"""

(workspace / "data" / "raw" / "q4_2024_intelligence_brief.txt").write_text(brief, encoding="utf-8")

# ── distractor files ──────────────────────────────────────────────────────────

(workspace / "data" / "archive" / "old_supplier_list.csv").write_text(
    "supplier,country,tier\nAlphaPharm,India,1\nSinoChem,China,1\nMedPack,Germany,2\n"
)
(workspace / "data" / "processed" / "demand_forecast_2024.json").write_text(
    json.dumps({"year": 2024, "forecast": [120, 135, 142, 158], "unit": "million_units"})
)
(workspace / "reports" / "2024Q1" / "quarterly_summary.txt").write_text(
    "Q1 2024: API costs rose 8% YoY. Three supplier audits completed. GMP non-conformances: 2."
)
(workspace / "reports" / "2024Q2" / "quarterly_summary.txt").write_text(
    "Q2 2024: Cold chain incidents up 12%. EMA inspection scheduled for August."
)
(workspace / "reports" / "2024Q3" / "quarterly_summary.txt").write_text(
    "Q3 2024: Nearshoring feasibility study launched. Mexico site identified."
)
(workspace / "models" / "v1" / "risk_model_v1.pkl").write_bytes(b'\x80\x04\x95\x00\x00\x00\x00\x00\x00\x00\x00.')
(workspace / "models" / "v2" / "risk_model_v2.pkl").write_bytes(b'\x80\x04\x95\x00\x00\x00\x00\x00\x00\x00\x00.')
(workspace / "logs" / "system.log").write_text(
    "2024-11-14 08:01:22 INFO graph loaded, entities=5\n2024-11-14 08:05:11 INFO analysis complete\n"
)
(workspace / "config" / "app_config.yaml").write_text(
    "storage:\n  path: data/\n  format: json\nlogging:\n  level: INFO\n"
)
(workspace / "tmp" / ".gitkeep").write_text("")

# Mark workspace ready
print("Workspace generated successfully.")
print(f"  Session-1 graph: data/raw/pharma_graph_session1.json ({session1_graph['metadata']['total_entities']} entities, {session1_graph['metadata']['total_relations']} relations)")
print(f"  Intelligence brief: data/raw/q4_2024_intelligence_brief.txt ({len(brief)} chars)")