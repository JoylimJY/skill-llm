import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Skill directory structure ──────────────────────────────────────────────────
skill_dir = os.path.join(workspace, "公众号写手")
docs_dir  = os.path.join(skill_dir, "docs")
os.makedirs(docs_dir, exist_ok=True)

# SKILL.md
skill_md = """\
---
name: 公众号写手
version: 2.0.0
description: |
  专业公众号内容创作专家，支持多平台文章写作（公众号/小红书/知乎等）。
  基于传播学原理和新媒体运营实践，创作具有传播力、高质量的内容。
  集成去AI痕迹技术，确保内容自然流畅、富有感染力。

allowed-tools:
  - Read
  - Write
  - Edit
  - AskUserQuestion

metadata:
  trigger: 公众号文章创作、内容优化、AI痕迹去除、多平台适配
  source: 基于传播学理论和新媒体运营实践
---

# 公众号写手技能

## 触发场景

- 创作公众号文章、小红书推文
- 优化文章标题、结构、配图
- 去除AI痕迹，让内容更自然
- 多平台内容适配

---

## 爆款推文五步法

```
Step 1: 爆款标题创作 → 输出5个标题方案
Step 2: 内容排版优化 → 优化结构、节奏
Step 3: 智能配图插入 → 建议配图位置和类型
Step 4: 封面设计方案 → 输出封面建议
Step 5: 最终输出 → 完整文章+排版建议
```

---

## 标题创作规则

详见 `docs/爆款方法论.md`

### 五种爆款标题

| 类型 | 特点 | 示例 |
|------|------|------|
| 悬念型 | 制造好奇 | "为什么90%的人都做错了？" |
| 痛点型 | 直击问题 | "别再浪费时间了" |
| 反差型 | 打破认知 | "你以为的常识，其实是误区" |
| 数字型 | 具体量化 | "3个方法，效率提升200%" |
| 身份型 | 锁定人群 | "写给30岁迷茫的你" |

---

## 内容结构规则

详见 `docs/写作技巧.md`

### 爆款结构四模式

| 模式 | 适用场景 |
|------|---------|
| 金字塔模式 | 观点类文章 |
| 故事模式 | 人物故事、案例 |
| 问题模式 | 教程类、科普类 |
| 清单模式 | 工具推荐、方法汇总 |

### 爆款开头五法

| 方法 | 特点 |
|------|------|
| 痛点开头 | "你是不是也遇到过..." |
| 故事开头 | "那天，我看到..." |
| 数据开头 | "根据调查，67%的人..." |
| 反差开头 | "很多人以为，但其实..." |
| 悬念开头 | "答案可能和你想的不一样..." |

---

## 去AI味规则

详见 `docs/去AI味指南.md`

### AI高频词替换

| AI词 | 替换建议 |
|------|---------|
| 此外 | 删除或直接写下一句 |
| 确保 | 直接说结果 |
| 强调 | 用具体例子代替 |
| 培养 | 用"学会"、"掌握" |

### 公式结构打破

- 避免"不仅仅……而且……"
- 不要用三段式列举
- 避免戏剧性分段

---

## 输出格式

### 完整文章输出

```markdown
# 标题：[推荐标题]

## 封面建议
- 尺寸：900x500（公众号标准）
- 主题：[封面主题描述]
- 配色：[配色建议]

## 正文

[开篇：痛点引入]

[正文内容]

[金句：可截图转发]

[结尾：总结或反问]

## 配图建议
- 插图位置：第X段后
- 插图类型：[数据图/表情包/场景图]

## 排版建议
- 段落长度：每段不超过5行
- 粗体使用：仅强调关键词
- 行间距：建议1.5倍
```

---

## 资源文件

```
公众号写手/
├── SKILL.md           # 本文件（核心流程）
└── docs/
    ├── 爆款方法论.md   # 标题创作、结构原则
    ├── 写作技巧.md     # 结构模板、开头结尾
    └── 去AI味指南.md   # 去AI痕迹规则
```
"""

with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)

# docs/爆款方法论.md
baokuan_md = """\
# 爆款方法论

## 标题创作核心原则

好标题的三要素：**引发情绪**、**制造期待**、**精准定位**

### 五种爆款标题详解

#### 1. 悬念型
- 核心：制造知识缺口，让读者想知道答案
- 关键词：为什么、秘密、真相、你不知道的
- 示例：
  - "为什么99%的人手机用法都是错的？"
  - "那个每天睡8小时还是累的人，终于找到原因了"

#### 2. 痛点型
- 核心：直接说出读者的困扰
- 关键词：还在、别再、停止、放弃
- 示例：
  - "你还在用意志力戒手机？这方法注定失败"
  - "每晚刷完手机睡不着，不是你的问题"

#### 3. 反差型
- 核心：打破固有认知，产生认知冲突
- 关键词：其实、反而、没想到、竟然
- 示例：
  - "戒掉手机的人，反而更焦虑了"
  - "你以为的健康作息，其实是另一种伤害"

#### 4. 数字型
- 核心：用具体数字增加可信度和吸引力
- 规则：数字要精确，不要用"很多"、"大量"
- 示例：
  - "21天数字排毒实验，我发现了3个意想不到的变化"
  - "每天减少2小时刷手机，90天后发生了什么"

#### 5. 身份型
- 核心：明确圈定目标读者，产生"这是写给我的"感
- 关键词：写给…的你、X岁、做X的人
- 示例：
  - "写给那些白天上班、晚上刷手机的打工人"
  - "给每天手机在手、内心空洞的你"

---

## 标题组合策略

- 单篇文章提供5个标题，覆盖不同类型
- 优先推荐1个最匹配内容调性的标题
- 其余4个作为备选，标注各自类型

---

## 内容结构原则

### 爆款内容的"三段式情绪弧"

1. **共鸣**：开头让读者感到"这说的就是我"
2. **转折**：中间给出反直觉的信息或方法
3. **行动**：结尾给出可执行的建议或金句

### 节奏控制

- 每300-500字设置一个情绪转折点
- 长段落（超过5行）必须拆分
- 善用短句制造呼吸感
"""

with open(os.path.join(docs_dir, "爆款方法论.md"), "w", encoding="utf-8") as f:
    f.write(baokuan_md)

# docs/写作技巧.md
writing_md = """\
# 写作技巧

## 爆款开头详解

开头的目标：在3秒内抓住读者，让他继续读下去。

### 五种爆款开头模板

#### 痛点开头（推荐指数：★★★★★）
触发读者的情绪记忆，让他感到被理解。

模板：
> 你是不是也有过这种感觉：明明什么都没做，但手机就是放不下。

#### 故事开头（推荐指数：★★★★）
用一个具体场景把读者拉进来。

模板：
> 那天，我朋友发给我一张截图。她的屏幕时间显示：每天平均7小时23分。

#### 数据开头（推荐指数：★★★★）
用数据制造冲击感。

模板：
> 根据最新研究，中国人平均每天解锁手机超过80次。

#### 反差开头（推荐指数：★★★）
打破读者的预期。

模板：
> 很多人以为，只要下定决心就能戒掉手机。但其实，意志力根本不够用。

#### 悬念开头（推荐指数：★★★）
让读者想知道答案才继续读。

模板：
> 答案可能和你想的不一样——最难戒掉的，不是手机，是无聊。

---

## 爆款结尾技巧

### 四种结尾方式

1. **总结式**：一句话概括全文核心观点
2. **反问式**：抛出一个问题，引发读者思考和评论
3. **行动式**：给读者一个今天就能做的小动作
4. **金句式**：一句可以截图转发的话

### 示例结尾（数字排毒主题）

> **反问式**：你上次把手机扣在桌上，专心陪家人吃完一顿饭，是什么时候的事了？
>
> **行动式**：今晚睡前，试着把手机充电器放到卧室门口。就这一步。
>
> **金句式**：我们花了所有时间刷别人的生活，却忘了自己的生活还没开始活。

---

## 金句创作原则

- 字数控制在25字以内
- 有对比、有张力
- 可以脱离文章独立传播
- 避免说教感

---

## 结构模板

### 问题模式（适合数字排毒类科普）

```
开头：提出读者面临的问题（100字）
↓
现象分析：为什么会这样（200字）
↓
核心方法：具体怎么做（400字，2-3个方法）
↓
案例/数据佐证（200字）
↓
结尾：金句或反问（50字）
```
"""

with open(os.path.join(docs_dir, "写作技巧.md"), "w", encoding="utf-8") as f:
    f.write(writing_md)

# docs/去AI味指南.md
deai_md = """\
# 去AI味指南

## 为什么要去AI味

AI生成的文章有明显的模式特征，读者会感到"违和"、"不像人写的"。
去AI味的核心是：**让文字有温度，有个人视角，有不完美的真实感**。

---

## AI高频词黑名单（必须避免）

| 词语/句式 | 问题 | 替换建议 |
|----------|------|---------|
| 此外 | 过于书面、机械衔接 | 删除，直接写下一句；或用"还有一点" |
| 确保 | 官方腔，无感情 | 直接说结果，如"这样你就不会再……" |
| 强调 | 空洞，像PPT语言 | 用具体例子代替，展示而非说明 |
| 培养 | 生硬，像教科书 | 改用"学会"、"慢慢掌握"、"找到感觉" |
| 总的来说 | 模板结尾，一看就是AI | 直接写结论，或改用反问 |
| 在……方面 | 冗余结构 | 直接说具体内容 |
| 值得注意的是 | 说教感强 | 删除，直接写内容 |
| 综上所述 | 最典型AI结尾词 | 直接写金句或反问 |
| 需要指出的是 | 论文腔 | 删除 |
| 深刻影响 | 用词夸张空洞 | 用具体影响代替 |

---

## 公式结构打破

### 禁止使用的结构

1. **三段式列举**（第一，……；第二，……；第三，……）
   - 改为：叙述性展开，用故事或例子穿插说明

2. **"不仅仅……而且……"** 句式
   - 这个句式太机械，改为分两句自然表达

3. **戏剧性分段**（如用省略号或感叹号单独成段）
   - 改为：让节奏通过内容本身体现，不靠标点制造假感情

4. **"首先/其次/最后"三段式**
   - 改用：自然过渡词，或直接省略过渡词，让内容衔接

---

## 去AI味实战技巧

### 技巧1：加入"不完美"的表达
- AI总是说"这很重要"，人会说"我也是后来才明白的"
- 加入个人视角：我觉得、我发现、说实话

### 技巧2：用口语化短句打破节奏
- "说真的，这一点很多人都忽略了。"
- "但问题是——"

### 技巧3：避免"总结性段落"
- 人写文章一般不会在结尾专门总结
- 直接用金句或反问收尾

### 技巧4：删除所有"起承转合"的信号词
- 删掉：首先、其次、最后、总的来说、综上所述
- 让段落自然流动

---

## 检查清单

在完成文章后，逐项检查：

- [ ] 全文没有出现"此外"
- [ ] 全文没有出现"确保"
- [ ] 全文没有出现"强调"（作为动词用于结构）
- [ ] 全文没有出现"培养"
- [ ] 全文没有出现"总的来说"
- [ ] 全文没有出现"综上所述"
- [ ] 没有三段式列举（第一/第二/第三）
- [ ] 没有"不仅仅……而且……"结构
- [ ] 开头属于五种爆款开头之一
- [ ] 结尾有金句或反问
"""

with open(os.path.join(docs_dir, "去AI味指南.md"), "w", encoding="utf-8") as f:
    f.write(deai_md)

# ── Distractor files (realistic content team workspace) ─────────────────────
distractor_dir = os.path.join(workspace, "content_team")
os.makedirs(distractor_dir, exist_ok=True)

# Old draft files to create confusion
old_drafts_dir = os.path.join(distractor_dir, "drafts", "2024_Q1")
os.makedirs(old_drafts_dir, exist_ok=True)

with open(os.path.join(old_drafts_dir, "draft_v1_health.md"), "w", encoding="utf-8") as f:
    f.write("# 旧版草稿\n\n这是一篇旧稿，格式不正确，请勿参考。\n\n确保读者能够获得帮助。\n此外，文章还需要优化。\n强调健康的重要性。\n培养良好习惯。\n")

with open(os.path.join(old_drafts_dir, "brief_digital_wellness.txt"), "w", encoding="utf-8") as f:
    f.write("主题：数字健康/数字排毒\n目标读者：25-35岁都市白领\n核心卖点：帮助用户减少手机依赖\n发布平台：微信公众号\n字数要求：800-1200字\n")

with open(os.path.join(old_drafts_dir, "competitor_analysis.md"), "w", encoding="utf-8") as f:
    f.write("# 竞品分析\n\n## 头部账号标题风格\n- 账号A：偏数字型\n- 账号B：偏情感型\n- 账号C：偏干货型\n\n结论：数字+痛点组合效果最好。\n")

# Marketing templates (distractors)
templates_dir = os.path.join(distractor_dir, "templates")
os.makedirs(templates_dir, exist_ok=True)

with open(os.path.join(templates_dir, "xiaohongshu_template.md"), "w", encoding="utf-8") as f:
    f.write("# 小红书模板\n\n封面文字：不超过15字\n配色：马卡龙色系\n标签：#健康生活 #数字排毒\n\n（注：本模板仅适用于小红书，不适用于公众号）\n")

with open(os.path.join(templates_dir, "zhihu_format.md"), "w", encoding="utf-8") as f:
    f.write("# 知乎格式规范\n\n- 回答开头必须有观点句\n- 引用需注明来源\n- 建议字数：2000字以上\n")

with open(os.path.join(templates_dir, "cover_sizes_old.txt"), "w", encoding="utf-8") as f:
    f.write("旧版封面尺寸参考（已废弃）:\n公众号: 900x383\n头条: 1440x810\n注意：以上尺寸为2022年标准，请以最新SKILL.md为准\n")

# Data files
data_dir = os.path.join(distractor_dir, "data")
os.makedirs(data_dir, exist_ok=True)

with open(os.path.join(data_dir, "screen_time_stats.csv"), "w", encoding="utf-8") as f:
    f.write("年份,平均每日屏幕时间(小时),样本量\n2020,6.2,1200\n2021,6.8,1500\n2022,7.1,2000\n2023,7.4,2200\n2024,7.9,2500\n")

with open(os.path.join(data_dir, "engagement_report_2024.txt"), "w", encoding="utf-8") as f:
    f.write("2024年公众号数据报告摘要\n\n打开率最高的标题类型：数字型（平均CTR 8.2%）\n其次：痛点型（7.6%）\n最低：身份型（4.1%）\n\n建议：组合使用多种标题类型进行A/B测试\n")

# Config files
config_dir = os.path.join(workspace, "config")
os.makedirs(config_dir, exist_ok=True)

with open(os.path.join(config_dir, "publish_schedule.json"), "w", encoding="utf-8") as f:
    import json
    schedule = {
        "platform": "wechat_official",
        "publish_time": "20:30",
        "frequency": "3x_per_week",
        "next_publish": "2024-03-15",
        "topic": "digital_detox"
    }
    f.write(json.dumps(schedule, ensure_ascii=False, indent=2))

with open(os.path.join(config_dir, "brand_voice.txt"), "w", encoding="utf-8") as f:
    f.write("品牌调性：温暖、专业、接地气\n目标人群：25-35岁都市白领，有健康意识\n禁止：说教、夸大、恐吓式营销\n核心价值观：可持续的生活方式\n")

# Meeting notes (distractors)
meetings_dir = os.path.join(distractor_dir, "meetings")
os.makedirs(meetings_dir, exist_ok=True)

with open(os.path.join(meetings_dir, "2024_03_content_meeting.md"), "w", encoding="utf-8") as f:
    f.write("# 3月内容会议纪要\n\n## 议题\n1. 数字排毒专题策划\n2. 爆款复盘\n\n## 决议\n- 本月主推「数字排毒」话题\n- 要求用最新写作规范（公众号写手 v2.0）\n- 文章输出文件名：article_draft.md\n\n## 下次会议\n3月22日\n")

with open(os.path.join(meetings_dir, "title_brainstorm.txt"), "w", encoding="utf-8") as f:
    f.write("标题头脑风暴（非正式记录，仅供参考，不代表最终输出要求）\n\n- 放下手机，拿起生活\n- 21天不刷手机挑战\n- 你的注意力被偷走了\n\n注：最终需要按标准流程输出5个不同类型标题\n")

# Outdated style guide
with open(os.path.join(distractor_dir, "style_guide_v1.md"), "w", encoding="utf-8") as f:
    f.write("# 旧版写作风格指南 v1.0（已废弃，请使用公众号写手 SKILL.md）\n\n封面尺寸：900x383（旧标准）\n段落：不超过8行\n\n本文件已废弃，请以 公众号写手/SKILL.md 为权威参考。\n")

print("Workspace setup complete.")
print(f"Workspace structure created at: {workspace}")