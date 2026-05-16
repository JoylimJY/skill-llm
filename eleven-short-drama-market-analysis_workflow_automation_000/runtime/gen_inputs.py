import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ---------- SKILL.md ----------
skill_md = """\
---
name: short-drama-market-analysis
description: 短剧/动漫剧/AI剧市场分析技能。用于分析短剧、AI漫剧市场动态、爆款作品追踪、平台政策解读、竞品分析、选剧决策支持。触发词：市场分析、选剧分析、短剧市场、动漫剧市场、AI漫剧市场行情、热门作品分析。
---

# 短剧/动漫剧/AI剧市场分析

> 本技能读取市场动态、平台政策、爆款数据，辅助选剧和制定策略。

## 数据来源优先级

1. 读取 `references/market-data.md` — 市场规模、主要平台一览
2. 读取 `references/trending-works.md` — 最新爆款作品列表（按题材/平台分类）
3. 读取 `references/toolchain.md` — 制作工具与大模型对比
4. 读取 `references/distribution.md` — 发行渠道与变现模式
5. 读取 `references/strategy.md` — 选剧策略框架

## 分析维度

每次分析须覆盖以下维度：

```
① 市场规模 & 增速
② 平台格局（抖音/快手/红果/微信视频号/海外）
③ 最新爆款题材 & 内容趋势
④ 制作成本 & 效率标杆
⑤ 政策合规动态（备案制度、审核红线）
⑥ 变现模式优先级
⑦ 竞品动态（同类公司最近动作）
⑧ 机会与风险提示
```

## 选剧决策框架

根据以下维度给每个候选IP/题材打分（1-10分）：

| 维度 | 权重 | 评分要点 |
|------|------|---------|
| 市场热度 | 20% | 当前搜索量、平台播放量、话题量 |
| 竞争程度 | 15% | 同类作品数量、头部集中度 |
| 改编难度 | 15% | IP授权状态、世界观复杂度 |
| 合规风险 | 20% | 封建迷信/低俗/版权风险 |
| 变现潜力 | 15% | 付费意愿、IP衍生价值 |
| 制作成本 | 15% | 场景数、角色数、特效量 |

综合得分最高的题材优先立项。

## 分析报告输出模板

```
## 【短剧/AI漫剧市场分析】{日期}
### 一、宏观概况
### 二、平台动态
### 三、爆款案例分析
### 四、竞争格局
### 五、选剧建议（TOP3题材）
### 六、风险提示
### 七、本周值得关注的数据
```
"""

with open(os.path.join(workspace, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# ---------- references/ ----------
refs_dir = os.path.join(workspace, "references")
os.makedirs(refs_dir, exist_ok=True)

market_data_md = """\
# 市场数据参考（2025年Q1）

## 市场规模
- 2024年中国短剧市场规模：504亿元（同比+107%）
- 预测2025年突破800亿元
- 海外短剧市场（ReelShort/DramaBox）：年增速超300%

## 主要平台
| 平台 | 月活（亿） | 短剧付费渗透率 | 内容特点 |
|------|-----------|--------------|---------|
| 抖音 | 7.0 | 12% | 精品化、算法驱动 |
| 快手 | 4.0 | 9% | 下沉市场、强互动 |
| 红果免费短剧 | 2.1 | 广告变现为主 | 免费+广告模式 |
| 微信视频号 | 3.5 | 8% | 私域流量、中老年为主 |
| 海外平台 | 增速强劲 | 付费意愿高 | 英语+东南亚市场 |

## 备注
- 数据来源：艾瑞咨询2025Q1报告（内部存档）
- 2025年3月，国家广电总局发布《短剧备案新规》，所有短剧须提前备案
"""

with open(os.path.join(refs_dir, "market-data.md"), "w", encoding="utf-8") as f:
    f.write(market_data_md)

trending_works_md = """\
# 爆款作品追踪（2025年4月更新）

## 霸总/甜宠类
- 《闪婚后被豪门老公宠上天》：抖音播放量破50亿，付费转化率18%
- 《替嫁新娘逃跑记》：快手站内话题量120亿

## 玄幻/修仙类
- 《我在古代当神医》：红果首发，3周充值破2000万
- 《混沌剑神》：AI漫剧形态，制作周期缩短60%

## 现代都市/逆袭类
- 《赘婿归来》系列：微信视频号广告主买量最高品类
- 《重生后我躺平了》：B站二次元向，弹幕互动极强

## 海外爆款
- "Fated to My Forbidden Alpha"：ReelShort北美TOP1，周收入120万美元
- "The Double Life of My Billionaire Husband"：DramaBox东南亚版，下载量破500万

## 内容趋势
- AI漫剧/AI动漫短剧：制作成本降低40-70%，品质接近人工制作
- 竖屏武侠：2025年新兴赛道，头部作品稀少，竞争蓝海
- 中老年甜宠：微信视频号/红果主战场，付费转化率超20%
"""

with open(os.path.join(refs_dir, "trending-works.md"), "w", encoding="utf-8") as f:
    f.write(trending_works_md)

toolchain_md = """\
# 制作工具与大模型对比（2025年4月）

## AI漫剧生成工具
| 工具 | 适用场景 | 成本/集 | 优势 |
|------|---------|--------|------|
| 可灵AI | 写实/动漫 | 800-2000元 | 动作连贯性强 |
| Runway Gen-3 | 西方题材 | 1500-3000元 | 英文内容生成强 |
| 即梦AI | 国风/古装 | 600-1500元 | 中文提示词优化 |
| Pika 2.0 | 快速原型 | 500-1000元 | 迭代速度快 |

## 大模型对比（剧本生成）
- GPT-4o：英文剧本质量最高，中文一般
- Claude 3.5 Sonnet：结构化叙事能力强，适合剧本大纲
- 文心一言4.0：中文短剧台词自然，符合国内审美
- Kimi（月之暗面）：长上下文处理强，适合长篇改编

## 效率标杆
- 传统真人短剧：单集制作成本5-15万元，周期7-14天
- AI漫剧：单集制作成本0.5-3万元，周期1-3天（降本70%）
- 人工+AI混合：单集3-8万元，周期3-7天
"""

with open(os.path.join(refs_dir, "toolchain.md"), "w", encoding="utf-8") as f:
    f.write(toolchain_md)

distribution_md = """\
# 发行渠道与变现模式（2025年Q1）

## 主流变现模式
1. **付费解锁（单集付费）**：抖音/快手/红果主流，转化率8-18%，ARPU 20-60元
2. **广告分成（免费+广告）**：红果免费短剧、B站，适合高流量低转化内容
3. **品牌定制**：化妆品/服装品牌主导，单部定制费50-300万元
4. **海外发行授权**：ReelShort/DramaBox，授权费5-30万美元/部
5. **IP衍生变现**：周边、游戏联动、直播带货（仅头部IP可行）

## 平台分成政策（2025年最新）
- 抖音：平台抽成30%，独家可享流量扶持
- 快手：平台抽成25%，新人扶持计划（前3部免抽成）
- 红果：广告分成模式，CPM 15-35元
- 海外：DramaBox分成40%，ReelShort分成35%

## 发行建议优先级
1. 首选抖音独家（流量最大）
2. 次选快手+红果联合发行
3. 品质达标可同步海外发行
"""

with open(os.path.join(refs_dir, "distribution.md"), "w", encoding="utf-8") as f:
    f.write(distribution_md)

strategy_md = """\
# 选剧策略框架（内部版本 v2.3）

## 核心原则
- 市场热 > 竞争少 > 成本低（优先级顺序）
- 合规风险为一票否决项（合规评分<6分直接淘汰）
- 海外潜力题材加权处理

## 黄金赛道（2025年）
1. **AI漫剧·竖屏武侠**：蓝海，制作成本低，差异化明显
2. **中老年甜宠**：微信视频号/红果付费率极高，竞争相对少
3. **海外向霸总（英文版）**：ReelShort/DramaBox需求旺盛，IP复用价值高

## 红线题材（直接否决）
- 涉鬼神封建迷信（无法备案）
- 低俗擦边内容（平台限流）
- 未授权知名IP改编（版权风险）

## 评分参考标准
- 8-10分：强烈推荐立项
- 6-7分：有条件推荐（需优化某一维度）
- 1-5分：不推荐
"""

with open(os.path.join(refs_dir, "strategy.md"), "w", encoding="utf-8") as f:
    f.write(strategy_md)

# ---------- candidate IPs file ----------
candidates_md = """\
# 候选题材/IP列表（2025年5月决策批次）

以下5个题材需要进行选剧评估，请结合市场数据给出TOP3建议：

## 题材A：《长生道侣》
- 类型：修仙/仙侠，竖屏AI漫剧形态
- IP来源：原创剧本，无授权问题
- 预计成本：单集1.2万元（AI漫剧）
- 备注：竖屏武侠/修仙赛道，当前竞品少

## 题材B：《总裁的替婚新娘》
- 类型：霸总甜宠，真人短剧
- IP来源：网文改编，授权谈判中（尚未确认）
- 预计成本：单集8万元
- 备注：该类型已有大量同类作品，竞争激烈

## 题材C：《阴阳捉鬼师》
- 类型：灵异/捉鬼，真人短剧
- IP来源：原创
- 预计成本：单集6万元
- 备注：涉及封建迷信元素，可能触发备案红线

## 题材D：《五十岁的春天》
- 类型：中老年甜宠，真人短剧
- IP来源：原创剧本
- 预计成本：单集4万元
- 备注：目标受众微信视频号/红果用户，付费意愿强

## 题材E：《Forbidden CEO》
- 类型：海外霸总（英文版），AI漫剧
- IP来源：原创英文剧本
- 预计成本：单集1.5万元
- 备注：面向ReelShort/DramaBox海外市场
"""

with open(os.path.join(workspace, "candidates.md"), "w", encoding="utf-8") as f:
    f.write(candidates_md)

# ---------- DISTRACTOR FILES ----------
# Internal project files, old reports, misc
distractor_dir = os.path.join(workspace, "internal")
os.makedirs(distractor_dir, exist_ok=True)

old_report = """\
# 旧版市场报告（2024年Q3，已过期）

本文件已归档，请勿参考。
市场规模（2023）：373亿元
"""
with open(os.path.join(distractor_dir, "old_report_2024Q3.md"), "w", encoding="utf-8") as f:
    f.write(old_report)

budget_file = """\
# 2025年制作预算规划

第一季度总预算：1200万元
已使用：450万元
"""
with open(os.path.join(distractor_dir, "budget_2025.md"), "w", encoding="utf-8") as f:
    f.write(budget_file)

team_file = """\
# 团队架构
- 制片总监：张明
- AI制作组：6人
- 发行负责人：李华
"""
with open(os.path.join(distractor_dir, "team_structure.md"), "w", encoding="utf-8") as f:
    f.write(team_file)

os.makedirs(os.path.join(workspace, "internal", "contracts"), exist_ok=True)
with open(os.path.join(workspace, "internal", "contracts", "vendor_list.txt"), "w", encoding="utf-8") as f:
    f.write("供应商列表（内部）\n可灵AI - 合同编号: KL2025001\n即梦AI - 合同编号: JM2025003\n")

os.makedirs(os.path.join(workspace, "assets"), exist_ok=True)
with open(os.path.join(workspace, "assets", "logo_spec.txt"), "w") as f:
    f.write("Logo specs: 1080x1080, PNG format\n")

with open(os.path.join(workspace, "assets", "color_palette.txt"), "w") as f:
    f.write("Primary: #FF4444\nSecondary: #2C2C2C\n")

os.makedirs(os.path.join(workspace, "drafts"), exist_ok=True)
with open(os.path.join(workspace, "drafts", "script_template.md"), "w", encoding="utf-8") as f:
    f.write("# 剧本模板\n第一集：[场景描述]\n角色A：[台词]\n")

with open(os.path.join(workspace, "drafts", "pitch_deck_notes.txt"), "w", encoding="utf-8") as f:
    f.write("融资路演备注 - 草稿版本，勿外传\n")

os.makedirs(os.path.join(workspace, "references", "archive"), exist_ok=True)
with open(os.path.join(workspace, "references", "archive", "platform_policy_2023.md"), "w", encoding="utf-8") as f:
    f.write("# 平台政策存档（2023年，已过时）\n抖音旧版分成政策：平台抽成35%\n")

with open(os.path.join(workspace, "references", "archive", "old_scoring_model.md"), "w", encoding="utf-8") as f:
    f.write("# 旧版评分模型（已废弃）\n维度：热度(25%) / 成本(25%) / 风险(25%) / 收益(25%)\n注意：此模型已被新版选剧决策框架取代\n")

print("Workspace generated successfully.")
print(f"Files created under: {workspace}")