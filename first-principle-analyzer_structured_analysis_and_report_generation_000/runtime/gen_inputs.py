import os
import random
import json

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── skill directory (the "installed" skill) ─────────────────────────────────
skill_dir = os.path.join(workspace, "skills", "first-principle-analyzer")
examples_dir = os.path.join(skill_dir, "examples")
os.makedirs(examples_dir, exist_ok=True)

# Write SKILL.md
skill_md = r"""# first-principle-analyzer - 第一性原理分析器

**版本**：v0.1.0  
**定位**：底层思维引擎 - 用第一性原理分解复杂问题，提取基本真理，重构创新方案

---

## 📖 技能说明

第一性原理分析器是一个结构化的思维框架，强制用户完成「质疑 - 分解 - 验证 - 重构」的完整流程，并提供外部视角挑战隐含假设。

**核心价值**：
- 摆脱类比思维（「别人怎么做」）
- 回归基本真理（「物理上可能的是什么」）
- 重构创新方案（从基本真理演绎）

---

## 🎯 使用场景

| 场景类型 | 示例问题 |
|----------|----------|
| **技术架构** | 「如何设计一个更好的技能系统？」 |
| **商业决策** | 「我们应该进入这个市场吗？」 |
| **产品方向** | 「这个功能值得做吗？」 |
| **人生选择** | 「我应该换工作还是创业？」 |
| **学术研究** | 「这个研究方向有前景吗？」 |

---

## 🚀 使用方法

### 方式 1：直接调用

```
请对以下问题进行第一性原理分析：

[你的问题]
```

### 方式 2：分阶段交互

**阶段 1：问题接收**
```
启动 first-principle-analyzer
```

**阶段 2：假设识别**
技能会识别问题中的隐含假设，并逐个质疑

**阶段 3：逐层分解**
技能会引导你进行至少 5 层「为什么」追问

**阶段 4：基本真理验证**
技能会提供验证标准，确认已到达基本真理

**阶段 5：重构方案**
技能会从基本真理演绎出至少 2 个创新方案

**阶段 6：报告生成**
输出完整的 Markdown 分析报告

---

## 📋 分析流程

```
┌─────────────────────────────────────────────────────────┐
│  阶段 1: 问题接收与初步分析                               │
│  - 接收问题                                              │
│  - 问题分类（技术/商业/人生/学术）                       │
│  - 初步假设识别                                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  阶段 2: 假设识别与质疑                                   │
│  - 识别至少 3 个隐含假设                                  │
│  - 逐个质疑：「这个假设一定成立吗？」                    │
│  - 记录质疑结果                                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  阶段 3: 逐层分解                                         │
│  - 第 1 层「为什么」                                      │
│  - 第 2 层「为什么」                                      │
│  - 第 3 层「为什么」                                      │
│  - 第 4 层「为什么」                                      │
│  - 第 5 层「为什么」→ 基本真理                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  阶段 4: 基本真理验证                                     │
│  - 验证标准 1：不可再分                                  │
│  - 验证标准 2：不证自明                                  │
│  - 验证标准 3：独立于其他命题                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  阶段 5: 重构方案生成                                     │
│  - 从基本真理演绎方案 A                                  │
│  - 从基本真理演绎方案 B                                  │
│  - 从基本真理演绎方案 C（可选）                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  阶段 6: 类比方案对比                                     │
│  - 传统类比方案是什么                                    │
│  - 创新方案的差异点                                      │
│  - 创新方案的优势                                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  阶段 7: 报告生成                                         │
│  - 输出结构化 Markdown 报告                               │
│  - 包含完整分析链路                                      │
│  - 可分享和存档                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 输出示例

### 输入
```
请对以下问题进行第一性原理分析：

如何创建一个更好的技能系统？
```

### 输出（摘要）
```markdown
# 第一性原理分析报告

## 问题分类
技术架构设计

## 识别的假设
1. 「技能系统」必须是集中式的
2. 技能必须由人类创建
3. 技能发现必须通过搜索

## 假设质疑
1. 为什么技能系统必须是集中式的？
   → 历史原因（npm/pip 模式），非技术必然
   
2. 为什么技能必须由人类创建？
   → 当前 AI 能力限制，非永恒真理
   
3. 为什么技能发现必须通过搜索？
   → 信息组织方式限制，非最优解

## 分解到基本真理
1. 技能的本质是什么？
   → 可复用的能力单元
   
2. 为什么需要技能？
   → 避免重复造轮子
   
3. 技能的核心属性？
   → 原子性、可组合性、可发现性

## 重构方案
方案 A：基于能力图谱的自动发现系统
方案 B：AI 自动生成技能的系统
方案 C：去中心化的技能市场

## 与类比方案对比
传统方案：参考 npm/pip/cargo 的设计
创新方案：从第一原理出发的能力图谱系统

创新点：
1. 从「人找技能」变为「技能找人」
2. 从「集中式市场」变为「去中心化网络」
3. 从「手动创建」变为「AI 辅助生成」
```

---

## 🧠 核心思维模式

### Elon Musk 模式
> 「从物理学角度思考：什么是真正正确的？什么是可能的？然后从那里往上推理。」

**应用**：
- 质疑「一直如此」的假设
- 分解到物理/经济/逻辑的基本真理
- 从基本真理重新构建

### Linux Kernel 模式
> 「文档与代码同等重要，过程透明化降低协作成本。」

**应用**：
- 分析流程必须文档化
- 每个阶段有明确输出物
- 分层让不同用户快速找到所需

### 亚里士多德模式
> 「第一原理是一个基本的、不证自明的命题，不能被从任何其他命题中推导出来。」

**应用**：
- 定义什么是「基本真理」
- 验证机制确认已到达基本真理
- 重构必须是演绎推理，而非归纳

---

## ⚠️ 使用注意

### 何时使用
- ✅ 复杂问题需要深度思考
- ✅ 传统方案不满意，寻求创新
- ✅ 重大决策需要严谨分析
- ✅ 学习专家思维模式

### 何时不使用
- ❌ 简单问题（杀鸡用牛刀）
- ❌ 紧急决策（时间不够）
- ❌ 已有明确最佳实践的问题
"""

with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# Write VERSION_HISTORY.md
version_history = r"""# first-principle-analyzer - 版本演进档案

## 版本总览

| 版本 | 日期 | 核心改进 | 状态 |
|------|------|----------|------|
| v0.1.0 | 2026-03-27 | 初始版本 - 基础分解框架 | ✅ 当前 |
| v0.2.0 | - | 规划中 | 📋 规划 |

## v0.1.0 功能需求

| 编号 | 功能 | 验收标准 |
|------|------|--------|
| F1 | 问题接收与初步分析 | 能接收任意复杂问题，输出问题类型分类 |
| F2 | 假设识别与质疑 | 识别问题中的隐含假设，逐个质疑 |
| F3 | 逐层分解 | 支持至少 5 层「为什么」追问 |
| F4 | 基本真理验证 | 提供验证标准，确认已到达基本真理 |
| F5 | 重构方案生成 | 从基本真理演绎出至少 2 个方案 |
| F6 | 类比方案对比 | 与传统类比方案对比，凸显创新点 |
| F7 | 分析报告生成 | 输出结构化 Markdown 报告 |

## 验收标准

- [ ] 能接收任意复杂问题并分类
- [ ] 能识别至少 3 个隐含假设
- [ ] 支持至少 5 层「为什么」追问
- [ ] 提供基本真理验证标准（不可再分、不证自明、独立于其他命题）
- [ ] 从基本真理演绎出至少 2 个方案
- [ ] 输出结构化 Markdown 报告
"""

with open(os.path.join(skill_dir, "VERSION_HISTORY.md"), "w", encoding="utf-8") as f:
    f.write(version_history)

# Write example case files (condensed versions)
case1 = r"""# 案例 1：SpaceX 火箭成本分析

## 分析结构示例

```markdown
# 第一性原理分析报告

## 问题分类
技术/商业

## 识别的假设
1. 「火箭一直都很贵」
2. 「必须购买现成零部件」
3. 「火箭是一次性的」

## 假设质疑
1. 为什么火箭一直都很贵？
   → 组织方式问题，非物理规律
2. 为什么必须购买现成零部件？
   → 行业惯例，非最优解
3. 为什么火箭是一次性的？
   → 工程惯例，非技术必然

## 分解到基本真理
第1层：为什么火箭贵？→ 制造成本高
第2层：为什么制造成本高？→ 供应链层级多
第3层：为什么供应链层级多？→ 行业分工固化
第4层：为什么行业分工固化？→ 无人挑战
第5层：材料本身多少钱？→ 材料成本仅占2%

验证：材料市场价格（不可再分、不证自明、独立于其他命题）

## 重构方案
方案 A：垂直整合，自主制造
方案 B：可回收设计，火箭复用

## 与类比方案对比
传统方案：向现有供应商采购
创新方案：自建供应链 + 可回收
差异：成本降低 90%+
```
"""

with open(os.path.join(examples_dir, "case-1-spaceX-rocket-cost.md"), "w", encoding="utf-8") as f:
    f.write(case1)

case2 = r"""# 案例 2：电池成本分析

电池材料成本约$80/kWh，市场价$600/kWh，差距来自供应链。

分析遵循7阶段流程，包含至少3个假设识别、5层为什么分解、基本真理验证、2个重构方案、类比方案对比。
"""

with open(os.path.join(examples_dir, "case-2-battery-cost.md"), "w", encoding="utf-8") as f:
    f.write(case2)

# ── client project directory ────────────────────────────────────────────────
project_dir = os.path.join(workspace, "projects", "av-sensor-analysis")
os.makedirs(project_dir, exist_ok=True)

# Background brief (the "messy input" — unstructured raw notes)
brief_content = """INTERNAL MEMO - AV Sensor Cost Task Force
==========================================
Date: 2026-04-01
Prepared by: Market Intelligence Team

RAW RESEARCH NOTES (unstructured, needs proper analysis):

Current LiDAR situation:
- Velodyne HDL-64E: used to cost ~$75,000 per unit (2010)
- Current mechanical spinning LiDAR: still $5,000-$15,000 range
- Solid-state LiDAR (new): some companies claiming $200-$500 target
- MEMS mirrors, OPA (optical phased arrays), FMCW approaches all competing

What everyone assumes:
- "LiDAR is inherently expensive because of precision optics"
- "You need mechanical spinning parts which are costly to manufacture"  
- "The laser safety requirements force expensive Class 1 laser components"
- "Small production volumes keep costs high"
- "Automotive-grade certification adds unavoidable cost"

What we don't know:
- What does a LiDAR actually NEED to do? (measure distance, point cloud, FOV)
- What are the actual raw material costs for photodetectors, lasers, optics?
- How much of the cost is manufacturing process vs. materials?
- Could different physics approaches change the cost structure fundamentally?

Competitor observations:
- Luminar: betting on InGaAs receivers at 1550nm (eye-safe, longer range)
- Ouster: digital LiDAR, using CMOS instead of analog APD arrays
- Innoviz: solid-state MEMS approach
- Hesai: Chinese manufacturer, aggressive pricing
- Everyone is doing "incremental improvements" to existing LiDAR paradigm

Business question from CEO:
"Can we ever get LiDAR below $100 for mass market autonomy, or should we
pivot to camera-only? I need a rigorous analysis, not just market research."

Random cost data points (unverified):
- VCSEL laser array: ~$3-8 per unit at volume
- SPAD detector array: ~$5-15 per unit at volume  
- MEMS mirror: ~$2-5 per unit at volume
- Optics/lens: ~$1-3 per unit at volume
- Processing ASIC: ~$10-20 per unit at volume
- PCB + housing: ~$5-10 per unit

Team debate notes:
- Alex: "We should just benchmark against Waymo's approach"
- Sam: "Copy what Mobileye is doing, they have scale"
- Jordan: "The physics haven't changed, we need to accept the cost floor"
- CEO: "I want someone to challenge ALL of these assumptions from scratch"
"""

with open(os.path.join(project_dir, "raw_research_notes.txt"), "w", encoding="utf-8") as f:
    f.write(brief_content)

# A partial, incomplete "analysis attempt" that is WRONG (missing stages, no structure)
bad_attempt = """LiDAR Cost Analysis - Draft 1
==============================

LiDAR sensors are expensive. The main reasons are:
1. Complex manufacturing
2. Small volumes  
3. Precision requirements

To reduce costs, we should:
- Increase production volume
- Find cheaper suppliers
- Maybe use cameras instead

Conclusion: LiDAR will eventually become cheaper as the market matures.
This is similar to how LCD screens became cheap over time.
"""

with open(os.path.join(project_dir, "incomplete_draft.txt"), "w", encoding="utf-8") as f:
    f.write(bad_attempt)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_dir = os.path.join(workspace, "archive")
os.makedirs(distractor_dir, exist_ok=True)

distractors = {
    "old_analysis_template.md": "# Analysis Template\n\nThis is an old template. Do not use.\n",
    "competitor_report_2023.txt": "Velodyne Q3 2023 Report\nRevenue down 12%.\nLooking for acquisition targets.\n",
    "team_meeting_notes.txt": "Meeting 2026-03-15\n- Discussed Q2 roadmap\n- Need better analysis tools\n- Action: hire consultant\n",
    "budget_2026.csv": "category,amount\nR&D,500000\nMarketing,200000\nSales,300000\n",
    "sensor_specs_comparison.json": json.dumps({
        "velodyne": {"channels": 64, "range": 120, "price": 8000},
        "luminar": {"channels": "N/A", "range": 250, "price": 1000},
        "ouster": {"channels": 128, "range": 150, "price": 3000}
    }, indent=2),
    "email_thread.txt": "From: CEO\nTo: Team\nSubject: LiDAR analysis needed urgently\n\nPlease produce a rigorous analysis. Not just market research. Challenge assumptions.\n",
}

for fname, content in distractors.items():
    with open(os.path.join(distractor_dir, fname), "w", encoding="utf-8") as f:
        f.write(content)

# More distractors in a nested structure
nested_dir = os.path.join(workspace, "archive", "previous_projects", "2025")
os.makedirs(nested_dir, exist_ok=True)

nested_distractors = {
    "radar_cost_analysis.md": "# Radar Cost Analysis 2025\n\nRadar is cheap. This is a different technology.\n",
    "camera_benchmark.txt": "Camera sensor BOM cost: $12-45 per unit\nProcessing: $50-80\nTotal: $62-125\n",
    "vendor_quotes.txt": "Vendor A: $4500/unit for 128-channel LiDAR\nVendor B: $3800/unit\nVendor C: $6200/unit\n",
    "strategy_deck_outline.txt": "Slide 1: Executive Summary\nSlide 2: Market Overview\nSlide 3: Competitive Landscape\nSlide 4: Recommendations\n",
}

for fname, content in nested_distractors.items():
    with open(os.path.join(nested_dir, fname), "w", encoding="utf-8") as f:
        f.write(content)

# One more nested level
deep_dir = os.path.join(workspace, "archive", "previous_projects", "2025", "drafts")
os.makedirs(deep_dir, exist_ok=True)

with open(os.path.join(deep_dir, "analysis_attempt_v1.txt"), "w", encoding="utf-8") as f:
    f.write("Draft v1 - incomplete\nJust listing costs without deeper analysis\nAbandoned 2025-11-03\n")

with open(os.path.join(deep_dir, "analysis_attempt_v2.txt"), "w", encoding="utf-8") as f:
    f.write("Draft v2 - still incomplete\nTried SWOT analysis but CEO rejected it\nNeeds different methodology\n")

print("Workspace generated successfully.")
print(f"Structure:")
for root, dirs, files in os.walk(workspace):
    level = root.replace(workspace, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')