import os
import random
from pathlib import Path

random.seed(42)

# Base workspace path
base = Path("/workspace/projects/workspace/memory/xiyue")

# Create full directory structure
dirs = [
    base,
    base / "subjects",
    base / "daily",
    base / "records",
    base / "references",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ── profile.md ──────────────────────────────────────────────────────────────
(base / "profile.md").write_text("""---
name: 喜悦
birth: 2019-10
tags: [喜悦/档案]
---

# 喜悦基本资料

- 出生日期：2019年10月
- 当前年龄：6岁半（2026年4月）
- 稳定兴趣：跳绳、街舞
- 性格特点：活泼、好奇心强、对批评较敏感
""", encoding="utf-8")

# ── README.md ───────────────────────────────────────────────────────────────
(base / "README.md").write_text("""# 喜悦成长档案总览

本档案记录喜悦的成长数据与观察，基于8维发展模型（V2）。

## 文件结构
- profile.md — 基本资料
- milestones.md — 里程碑
- sports.md — 运动档案
- subjects/ — 学科档案
- records/ — 成长记录
- references/ — 参考模板
""", encoding="utf-8")

# ── milestones.md ────────────────────────────────────────────────────────────
(base / "milestones.md").write_text("""---
tags: [喜悦/里程碑]
---

# 成长里程碑

## 2025年
- 2025-09：跳绳首次突破100个/分钟
- 2025-11：街舞参加学校汇演，主动报名

## 2026年
- 2026-01：识字量突破800字
- 2026-02：自主阅读绘本，每天约20分钟
""", encoding="utf-8")

# ── sports.md ────────────────────────────────────────────────────────────────
(base / "sports.md").write_text("""---
tags: [喜悦/运动档案]
last_updated: 2026-03-28
---

# 运动档案

## 跳绳数据（能力参考）
| 日期 | 最高记录 | 稳定水平 | 备注 |
|:---|:---|:---|:---|
| 2026-01 | 118个/分钟 | 105个 | 状态稳定 |
| 2026-02 | 122个/分钟 | 110个 | 有提升 |
| 2026-03 | 125个/分钟 | 112个 | 本月最高 |

## 观察记录
- 2026-03：训练主动性强，经常自己要求加练
- 2026-02：遇到断绳会重新开始，挫折耐受好
""", encoding="utf-8")

# ── subjects/math.md ─────────────────────────────────────────────────────────
(base / "subjects" / "math.md").write_text("""---
tags: [喜悦/学业/数学]
---

# 数学档案

## 数据记录
- 2026-03：20以内加减法正确率 92%
- 每次作业完成时间：约15分钟

## 观察
- 遇到不会的题会主动问"为什么是这个答案"
- 对数字游戏感兴趣
""", encoding="utf-8")

# ── subjects/chinese.md ──────────────────────────────────────────────────────
(base / "subjects" / "chinese.md").write_text("""---
tags: [喜悦/学业/语文]
---

# 语文档案

## 数据记录
- 2026-03：累计识字量约850字
- 每周新学字：约15-20字

## 观察
- 主动阅读频率增加
- 喜欢读有插图的故事书
""", encoding="utf-8")

# ── subjects/english.md ──────────────────────────────────────────────────────
(base / "subjects" / "english.md").write_text("""---
tags: [喜悦/学业/英语]
---

# 英语档案

## 数据记录
- 2026-03：认识基础单词约80个

## 观察
- 对英语儿歌感兴趣，会主动哼唱
""", encoding="utf-8")

# ── references/喜悦成长跟踪模型V2.md ──────────────────────────────────────────
(base / "references" / "喜悦成长跟踪模型V2.md").write_text("""# 8维发展模型 V2

D0 关系与安全感
D1 运动与体能
D2 学业与知识
D3 认知与思维
D4 社交与情绪
D5 习惯与自律
D6 内在动机
D7 兴趣结构
""", encoding="utf-8")

# ── references/模板-月度速记.md ──────────────────────────────────────────────
(base / "references" / "模板-月度速记.md").write_text("""---
tags: [喜悦/月度速记]
date: YYYY-MM
---

# 月度速记 · YYYY年MM月

## ✅ 本月惊喜
（一个让你意外或高兴的时刻）

## ⚠️ 本月担心
（一个让你有些不安的信号）

## 💎 内驱信号
（一个主动、沉浸、或坚持的例子）

## 8维简评
| 维度 | 信号 | 备注 |
|:---|:---|:---|
| D0 关系 | 🟢/🟡/🔴 | |
| D1 运动 | 🟢/🟡/🔴 | |
| D2 学业 | 🟢/🟡/🔴 | |
| D3 认知 | 🟢/🟡/🔴 | |
| D4 社交 | 🟢/🟡/🔴 | |
| D5 习惯 | 🟢/🟡/🔴 | |
| D6 动机 | 🟢/🟡/🔴 | |
| D7 兴趣 | 🟢/🟡/🔴 | |

## 综合评估
- 发展阶段：
- 内驱状态：
- 风险信号：
""", encoding="utf-8")

# ── references/模板-季度评估.md ──────────────────────────────────────────────
(base / "references" / "模板-季度评估.md").write_text("""---
tags: [喜悦/季度评估]
date: YYYY-QN
---

# 季度评估 · YYYY年第N季度

（详细8维分析，每维包含数据+观察+判断）
""", encoding="utf-8")

# ── daily/ — some existing daily notes ──────────────────────────────────────
(base / "daily" / "2026-03-15.md").write_text("""# 2026-03-15 日记

跳绳练了30分钟，最高跳了125个。
今天状态很好，主动要求多练一组。
""", encoding="utf-8")

(base / "daily" / "2026-03-22.md").write_text("""# 2026-03-22 日记

数学作业完成，正确率高。
晚上主动要求妈妈给她读故事。
""", encoding="utf-8")

# ── records/ — one old record ────────────────────────────────────────────────
(base / "records" / "2026-03-01-月度速记.md").write_text("""---
tags: [喜悦/月度速记]
date: 2026-03
---

# 月度速记 · 2026年3月

## ✅ 本月惊喜
跳绳单次最高125个，自己突破历史记录后特别开心，跑来告诉我。

## ⚠️ 本月担心
有一次因为跳绳断了，情绪有点低落，约5分钟后自己恢复了。

## 💎 内驱信号
连续三天主动说"妈妈我要去跳绳"，不需要催促。

## 8维简评
| 维度 | 信号 | 备注 |
|:---|:---|:---|
| D0 关系 | 🟢 | 亲密正常 |
| D1 运动 | 🟢 | 持续进步 |
| D2 学业 | 🟢 | 稳定 |
| D3 认知 | 🟢 | 正常 |
| D4 社交 | 🟢 | 正常 |
| D5 习惯 | 🟢 | 较好 |
| D6 动机 | 🟢 | 内在驱动明显 |
| D7 兴趣 | 🟢 | 跳绳/街舞稳定 |

## 综合评估
- 发展阶段：积累期
- 内驱状态：↑ 增强
- 风险信号：无
""", encoding="utf-8")

# ── THE MAIN INPUT: raw messy notes for April 2026 ───────────────────────────
# This is the file the agent must process to create the monthly record
raw_notes = """=== 喜悦4月观察记录（乱序笔记，待整理）===
日期范围：2026年4月

【4月3日】
今天让喜悦跳绳，她说"不想跳"，我说"你再不练就跟不上了"，
她就跳了，但是全程没什么精神，跳了不到10分钟就说累了。
跳绳数据：最高87个，比上个月差很多。

【4月7日】
因为作业写太慢批评了她，她哭了，然后整个晚上都不来找我，
自己在房间里待着。第二天早上也没有像以前那样来抱我。
我当时说了"这么简单的题都不会，要多少时间"。

【4月10日】
街舞课，老师说她今天没什么状态，动作都做得很机械。
往常她都是班里最积极的，今天老师专门跟我说了。
喜悦出来以后问她怎么了，她说"跳了也没意思"。

【4月12日】
数学考试得了85分，上次是93分。
她拿到卷子看了一眼，没有问我为什么错了，
直接把卷子塞进书包，说"没事的妈妈"。

【4月15日】
今天喜悦主动来找我讲学校的事情，说班里有个小朋友很好玩，
她们一起玩了新游戏。讲得很开心，眼睛亮亮的。
这是这个月难得的一次。

【4月18日】
晚上催她复习，她说"学了也没用，我就是学不好"。
这句话让我很担心，以前她不会这样说的。
跳绳今天干脆没练，说不想练。

【4月20日】
发现她最近睡前会悄悄哭，问她也不说为什么。
关灯后听到小声抽泣，进去她就说"没事没事我没哭"。
她以前从来不会隐藏情绪的。

【4月23日】
今天我换了方式，没有催，就坐在旁边陪她，
她自己拿起了跳绳跳了一会儿，跳了约50个，
但是她说"还是跳不好"，情绪还是低落。

【4月25日】
语文认字测试，认出了18/20个，老师说进步了。
但是喜悦自己说"就认对了这点，有什么用"。
这种自我否定是本月第二次出现了。

【4月末总结感受】
这个月感觉孩子整个人都不对，不知道是什么原因，
跳绳退步了，情绪也不好，和我的关系感觉也疏远了一些。
不知道要不要加强训练让她找回状态？还是报个补习班？
"""

input_file = Path("/workspace/raw_april_notes.txt")
input_file.write_text(raw_notes, encoding="utf-8")

# ── Extra distractor files ────────────────────────────────────────────────────
distractor_dir = Path("/workspace/other_files")
distractor_dir.mkdir(exist_ok=True)

(distractor_dir / "shopping_list.txt").write_text("牛奶 鸡蛋 苹果 面包\n", encoding="utf-8")
(distractor_dir / "recipe_notes.md").write_text("# 食谱\n红烧肉：五花肉500g，酱油适量\n", encoding="utf-8")
(distractor_dir / "work_todo.txt").write_text("明天开会 准备PPT 发邮件给张总\n", encoding="utf-8")
(distractor_dir / "budget_april.csv").write_text("类别,金额\n餐饮,1200\n交通,300\n教育,800\n", encoding="utf-8")
(distractor_dir / "school_calendar.txt").write_text("4月5日 清明节假期\n4月30日 劳动节前夕\n", encoding="utf-8")
(distractor_dir / "old_template_v1.md").write_text("# 旧模板V1（已废弃）\n不要使用此模板\n", encoding="utf-8")

# Another distractor: a partial/wrong record
(distractor_dir / "draft_record.md").write_text("""---
date: 2026-04
---
# 草稿
孩子这个月表现一般（未整理）
""", encoding="utf-8")

print("✅ Workspace generated successfully.")
print(f"Input file: {input_file}")
print(f"Memory base: {base}")