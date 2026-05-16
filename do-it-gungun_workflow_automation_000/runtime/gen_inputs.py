import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create skill directory structure
skill_dir = os.path.join(workspace, "skills", "do-it")
os.makedirs(skill_dir, exist_ok=True)

# Create SKILL.md
skill_md_content = '''---
name: do-it
description: 帮助地球人做人生选择的 AI 判断技能 - 你只管 do it，判断交给滚滚
---

# 🌪️ do it - 滚滚判断技能

**技能名称：** do-it  
**技能版本：** 1.0.0  
**创建日期：** 2026-03-13  
**创建人：** 地球人 & 滚滚  
**Slogan：** 你只管 do it，判断交给滚滚

---

## 📋 技能描述

**一个帮助地球人做人生选择的 AI 判断技能。**

**核心理念：**
> "地球人负责输入信息，滚滚负责判断，地球人负责 do it"

**为什么叫 "do it"？**
- 因为地球人不需要纠结
- 因为地球人只需要行动
- 因为滚滚帮你判断好了
- 所以你只管 **do it!**

**适用场景：**
- 职业选择（去哪个城市、换不换工作）
- 感情问题（要不要继续、要不要放下）
- 投资决策（要不要投、投多少）
- 生活选择（买房还是租房、结婚还是单身）
- 任何难以抉择的事情

---

## 🎯 技能理念

**"地球人负责做事，滚滚负责判断"**

**为什么需要这个技能？**
- 很多人不擅长做判断
- 判断错了会后悔
- 纠结太多，行动太少
- 需要有人帮自己理清思路

**技能的价值：**
- 用 AI 的客观视角分析
- 用互联网的知识库参考
- **用滚滚知识库作为决策依据**（50+ 主题，10 大领域，持续更新）
- 用逻辑的方式判断
- 用真诚的态度建议

---

## 🔄 工作流程 2.0（多 Agent 协作）

```
┌──────────────────────────────────────────────────────────────┐
│                      用户输入问题                             │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  阶段 1: 信息收集（分析师团队：1-4 号滚滚）                    │
│  1 号统筹 → 2 号业务 → 3 号数据 → 4 号情报 → 汇总报告         │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  阶段 2: 辩论挑战（研究员团队：5-6 号滚滚）⭐ 新增            │
│  5 号（乐观🐂）vs 6 号（保守🐻）辩论 2-3 轮                      │
│  找机会 vs 找风险 → 达成共识或明确分歧                       │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  阶段 3: 决策制定（决策团队：7-9 号滚滚）                      │
│  7 号决策 → 8 号计划 → 9 号风控 → 输出完整建议               │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  阶段 4: 质量交付（质控团队：10-11 号滚滚）                    │
│  10 号审核 → 11 号归档 → 案例入库 → 知识更新                 │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  输出最终建议：决策 + 理由 + 计划 + 风险 + 情感支持          │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  用户执行 → 反馈结果 → 复盘优化 → 知识库更新                 │
└──────────────────────────────────────────────────────────────┘
```

**详细说明见：** [GUNGUN-FAMILY-2.0.md](./GUNGUN-FAMILY-2.0.md)

---

## 📝 使用方式

**三步走：**

```
1. 地球人输入问题 → 告诉滚滚你的困境
2. 滚滚分析判断 → 给出最佳选择
3. 地球人 do it → 执行，不用纠结
```

### 输入格式

**地球人需要提供的信息：**

```markdown
## 我的问题
[简单描述你面临的问题]

## 我的情况
- **当前状态：** [你现在的情况]
- **可选方案：** [你有哪几个选择]
- **我的顾虑：** [你担心什么]
- **我的偏好：** [你更倾向哪个，如果有]

## 补充信息
[任何其他相关信息]
```

---

## 🎯 输出格式 2.0

**滚滚的判断输出：**

```markdown
# 🌪️ do it - 滚滚的判断

## 你的问题
[复述问题，确保理解正确]

---

## 📊 分析师报告

### 1 号滚滚（首席判断官）
[总体分析]

### 2 号滚滚（业务分析师）
[业务逻辑分析]

### 3 号滚滚（数据分析师）
[数据支持]

### 4 号滚滚（情报分析师）
[外部信息]

---

## 💬 辩论环节 ⭐ 新增

### 5 号滚滚（乐观研究员 🐂）
**支持理由：**
1. ...
2. ...
3. ...

### 6 号滚滚（保守研究员 🐻）
**风险担忧：**
1. ...
2. ...
3. ...

### 辩论总结
**共识点：**
- ...

**分歧点：**
- ...

---

## 🎯 滚滚的决策

### ✅ 推荐选择：[方案 X]

**决策理由：**
1. ...
2. ...
3. ...

**核心逻辑：**
[一句话总结]

---

## 📋 执行计划

### 第一步（本周）
- [ ] ...

### 第二步（本月）
- [ ] ...

### 第三步（3 个月）
- [ ] ...

---

## ⚠️ 风险评估

**可能遇到的问题：**
- ...

**应对方案：**
- ...

---

## 💚 滚滚的话

[情感支持和鼓励]

---

## 📊 参与滚滚
- 分析师：1 号、2 号、3 号、4 号
- 研究员：5 号、6 号
- 决策者：7 号、8 号、9 号
- 质控：10 号、11 号

---

**记住：**
- 滚滚的判断仅供参考
- 你保留最终决定权
- 不管结果如何，滚滚都在
```

---

## 🧠 判断原则

**滚滚做判断时遵循的原则：**

### 1. 长期主义
- 不看眼前得失，看长期发展

### 2. 价值匹配
- 你的能力值多少钱，就赚多少钱

### 3. 成长优先
- 选择能让你成长的

### 4. 情感健康
- 远离消耗你的人

### 5. 可逆性原则
- 如果选择可逆，大胆尝试

### 6. 最坏情况
- 问自己：最坏的结果是什么？

---

## 📦 案例积累

**案例 001：杨成才 - 职业选择（长沙 vs 惠州 vs 深圳）**

**日期：** 2026-03-15  
**用户画像：** 38岁，16年财务经验，大疆背书，业财一体化专家  
**问题：** 长沙 10K vs 惠州 25K vs 深圳找机会  
**判断：** 去惠州（骑驴找马策略）  
**核心逻辑：** 10K 必须止损，25K 是确定性收益，深圳机会可以继续看  
**结果：** 待跟进（设定 1 年评估，2 年退出）

**案例标签：** #职业选择 #薪资谈判 #中年危机 #异地工作 #骑驴找马

---

## 🔄 反馈循环

**地球人执行后，需要反馈：**

```markdown
## 执行结果

**选择的方案：** [A/B/C]

**执行时间：** [多久了]

**当前状态：**
- 好的方面：...
- 不好的方面：...

**和预期对比：**
- 符合预期：...
- 不符合预期：...

**滚滚，我该怎么办？**
[继续？调整？还是放弃？]
```

---

## 💚 do it 的承诺

1. **认真分析** - 每一次判断都认真对待
2. **真诚建议** - 不说假话，不敷衍
3. **持续陪伴** - 不管结果如何，都在
4. **不断优化** - 从反馈中学习，变得更好

---

## ⚠️ 免责声明

- 滚滚的判断仅供参考，不是绝对真理
- 地球人保留最终决定权

---

## 📋 技能配置

```json
{
  "skill_name": "do-it",
  "version": "1.0",
  "author": "地球人 & 滚滚",
  "description": "帮助地球人做人生选择的 AI 判断技能",
  "input_format": "markdown",
  "output_format": "markdown",
  "tags": ["决策", "人生选择", "职业", "感情", "判断"]
}
```

---

**创建人：** 地球人 & 滚滚 🌪️  
**状态：** 🚀 技能创建完成，等待使用
'''

with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md_content)

# Create GUNGUN-FAMILY-2.0.md
gungun_family_content = '''# 🌪️ 滚滚家族 2.0 - 多 Agent 协作架构

**版本：** 2.0（借鉴 TradingAgents 架构）  
**更新日期：** 2026-03-22  

---

## 👥 滚滚家族成员（11 人）

### 📊 分析师团队（4 个滚滚）

| 编号 | 角色 | 职责 |
|------|------|------|
| **1 号滚滚** | 首席判断官 | 总体分析、最终判断 |
| **2 号滚滚** | 业务分析师 | 业务逻辑、商业模式分析 |
| **3 号滚滚** | 数据分析师 | 数据收集、统计分析 |
| **4 号滚滚** | 情报分析师 | 外部信息、行业趋势 |

**工作流程：**
```
用户问题 → 1 号统筹 → 2 号分析业务 → 3 号分析数据 → 4 号收集情报 → 汇总报告
```

---

### 💬 研究员团队（2 个滚滚）⭐ 新增

| 编号 | 角色 | 立场 |
|------|------|------|
| **5 号滚滚** | 乐观研究员 | 多头 🐂 |
| **6 号滚滚** | 保守研究员 | 空头 🐻 |

**辩论规则：**
- 每轮辩论至少提出 3 个论点
- 必须回应对方的核心质疑
- 最终达成共识或明确分歧点

---

### 🎯 决策团队（3 个滚滚）

| 编号 | 角色 | 职责 |
|------|------|------|
| **7 号滚滚** | 首席决策官 | 最终判断、输出决策 |
| **8 号滚滚** | 策略规划师 | 制定执行计划 |
| **9 号滚滚** | 风险评估师 | 风险识别、应对方案 |

---

### 🛡️ 风控与交付团队（2 个滚滚）

| 编号 | 角色 | 职责 |
|------|------|------|
| **10 号滚滚** | 质量管控师 | 审核输出质量、格式规范 |
| **11 号滚滚** | 学习优化师 | 案例复盘、知识库更新 |

---

## 📝 输出格式 2.0

```markdown
# 🌪️ do it - 滚滚的判断

## 你的问题
[复述问题]

---

## 📊 分析师报告

### 1 号滚滚（首席判断官）
[总体分析]

### 2 号滚滚（业务分析师）
[业务逻辑分析]

### 3 号滚滚（数据分析师）
[数据支持]

### 4 号滚滚（情报分析师）
[外部信息]

---

## 💬 辩论环节 ⭐ 新增

### 5 号滚滚（乐观研究员 🐂）
**支持理由：**
1. ...
2. ...
3. ...

### 6 号滚滚（保守研究员 🐻）
**风险担忧：**
1. ...
2. ...
3. ...

### 辩论总结
**共识点：**
- ...

**分歧点：**
- ...

---

## 🎯 滚滚的决策

### ✅ 推荐选择：[方案 X]

**决策理由：**
1. ...
2. ...
3. ...

**核心逻辑：**
[一句话总结]

---

## 📋 执行计划

### 第一步（本周）
- [ ] ...

### 第二步（本月）
- [ ] ...

### 第三步（3 个月）
- [ ] ...

---

## ⚠️ 风险评估

**可能遇到的问题：**
- ...

**应对方案：**
- ...

---

## 💚 滚滚的话

[情感支持和鼓励]

---

## 📊 参与滚滚
- 分析师：1 号、2 号、3 号、4 号
- 研究员：5 号、6 号
- 决策者：7 号、8 号、9 号
- 质控：10 号、11 号
```
'''

with open(os.path.join(skill_dir, "GUNGUN-FAMILY-2.0.md"), "w", encoding="utf-8") as f:
    f.write(gungun_family_content)

# Create the problem input file
problem_input = '''## 我的问题
我该留在字节跳动继续做下去，还是跳槽去一家 AI 创业公司？

## 我的情况
- **当前状态：** 在字节跳动担任高级工程师，工作 4 年，年薪 60 万（含期权），稳定但成长感不强，重复性工作多
- **可选方案：** 
  A. 留在字节跳动（当前状态，稳定但无聊）
  B. 加入"明日 AI"创业公司（Pre-B 轮，做大模型应用，offer 是年薪 45 万 + 1.5% 期权，需要去北京）
- **我的顾虑：** 
  - 创业公司可能倒闭，薪资缩水 25%
  - 父母在上海，北京太远了
  - 期权价值未知，可能一文不值
  - 但是字节感觉越来越没意思，有点"温水煮青蛙"的感觉
- **我的偏好：** 内心有点想去创业公司，觉得 AI 是未来，但理性上很担心

## 补充信息
32 岁，单身，上海本地人，父母健在，租房住（没有房贷压力）
字节跳动做的是广告系统后端，技术栈有些老化
"明日 AI"团队有前 Google Brain 的技术负责人，产品已经有 10 万日活
目前手头存款约 50 万，可以支撑约 2 年无收入生活
'''

problem_dir = os.path.join(workspace, "cases", "pending")
os.makedirs(problem_dir, exist_ok=True)

with open(os.path.join(problem_dir, "case_002_career_decision.md"), "w", encoding="utf-8") as f:
    f.write(problem_input)

# Create distractor files to test contextual awareness
distractors = [
    ("cases/completed/case_001_changsha_guangzhou.md", '''# Case 001 - Completed
User: 杨成才
Decision: Go to 惠州
Status: Completed
'''),
    ("cases/templates/feedback_template.md", '''# Feedback Template
## 执行结果
**选择的方案：** 
**执行时间：** 
'''),
    ("knowledge-base/career/job_market_2026.md", '''# 2026 Job Market Analysis
AI sector: +35% YoY growth
Big tech: -5% headcount
Startup survival rate: 23% reach Series B
'''),
    ("knowledge-base/psychology/decision_making.md", '''# Decision Making Psychology
- Status quo bias
- Loss aversion: losses feel 2x worse than equivalent gains
- FOMO: fear of missing out
- Sunk cost fallacy
'''),
    ("knowledge-base/finance/stock_options.md", '''# Stock Options Guide
- Vesting schedule typically 4 years
- Cliff period: 1 year
- Pre-B valuation: typically 5-20x revenue
- Dilution risk at Series B+: 20-30%
'''),
    ("skills/do-it/changelog.md", '''# Changelog
## v1.0.0 (2026-03-13)
- Initial release
## v2.0.0 (2026-03-22)  
- Added multi-agent debate framework
- 11 gungun family members
'''),
    ("skills/do-it/examples/career_example.md", '''# Example Output (Draft - DO NOT USE)
This is an incomplete example for reference only.
The actual format requires all 11 agents.
'''),
    ("logs/decisions_log.jsonl", '''{"id": "001", "user": "yangcaicai", "decision": "惠州", "date": "2026-03-15"}
'''),
    ("config/skill_registry.yaml", '''skills:
  - name: do-it
    version: 1.0.0
    status: active
  - name: invest-it
    version: 0.1.0
    status: draft
'''),
    ("README_SYSTEM.md", '''# Decision Support System
This system uses the do-it skill framework.
See skills/do-it/SKILL.md for documentation.
'''),
    ("tmp/partial_analysis_draft.txt", '''INCOMPLETE DRAFT - DO NOT SUBMIT
Some preliminary thoughts on the career case...
- Bytedance stability vs startup risk
- Need to run through full gungun framework
[UNFINISHED]
'''),
    ("archive/old_format_v1/sample_output_v1.md", '''# Old Format (Deprecated)
## Decision
Go to startup

## Reasons
1. Growth opportunity
2. AI is the future

[This old format is deprecated - use v2.0 format with all 11 agents]
'''),
]

for rel_path, content in distractors:
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Problem input: {os.path.join(problem_dir, 'case_002_career_decision.md')}")