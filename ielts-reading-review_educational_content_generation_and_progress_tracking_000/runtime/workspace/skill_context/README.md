# IELTS Reading Review 雅思阅读复盘助手

> Finish a reading passage, hand it to AI, get a complete review — error analysis, synonym tracking, vocabulary tagging, and mistake pattern detection, all in one go.

做完阅读题，丢给 AI，自动出复盘笔记——错题拆解、同义替换积累、考点词标注、易错模式追踪，一步到位。

---

## 🚀 快速开始（3 步上手）

### 第一步：安装 Skill

```bash
# ClawHub 安装（推荐）
clawhub install ielts-reading-review

# 或手动复制到 skills 目录
cp -r ielts-reading-review ~/.workbuddy/skills/
```

### 第二步：做完一篇阅读题

用剑桥雅思真题（Cambridge IELTS）做完一篇阅读，准备好：
- ✅ 原文（拍照/截图/粘贴文字都行）
- ✅ 正确答案
- ✅ 你的答案（标出哪些做错了）
- ⭕ 可选：翻译、用时

### 第三步：发给 AI，说"帮我复盘"

就这么简单。AI 会自动生成一份完整的复盘笔记。

---

## 📖 完整使用案例

> 以下是一个真实的使用过程，以剑4 Test 3 Passage 1 为例。

### 你发给 AI 的内容

```
我做完了剑4 Test3 Passage1，帮我复盘。

文章：Micro-Enterprise Credit for Street Youth
用时：34:40
得分：7/13

我的答案 vs 正确答案：
Q1: 我选D → 正确A
Q2: 我选C → 正确D
Q3: ✅
Q4: ✅
Q5: 我填 Sudan and India → 正确 Sudan
Q6: ✅
Q7: 我填 shoe shine → 正确 Shoe Shine Collective
Q8-Q10: ✅
Q11: 我选 NOT GIVEN → 正确 NO
Q12: ✅
Q13: 我选D → 正确A

（然后把原文和翻译也贴上来）
```

### AI 自动产出的复盘笔记

AI 会生成一份结构化的 HTML 复盘笔记，包含以下 5 个模块：

#### 📌 模块一：得分总览 + 核心问题一句话

```
得分：7/13 ｜ 用时：34:40
填空题 4/6 ❌ ｜ 判断题 1/2 ❌ ｜ 选择题 2/5 ❌

⚠️ 核心问题：同义替换识别能力弱——"in association with" = "as part of"、
"exemplify" = "用实例展示" 两组关键替换全部没识别出来，直接丢了 3 题。
```

> 注意：核心问题会精确指出最大的失分模式，不会说"阅读理解有待提升"这种废话。

#### ❌ 模块二：逐题错因分析

每道错题会拆解成 4 个部分：

**示例 — Q1（选择题）：**

| 项目 | 内容 |
|------|------|
| **题目** | The quotations at the beginning of the article... |
| **你选** | D. highlight the benefits **to society** of S.K.I. |
| **正确** | A. **exemplify** the effects of S.K.I. |
| **原文定位** | 引言中 Doreen 说"能给家人买早餐了"，Fan 说"学会了储蓄再投资" |
| **关键词映射** | `exemplify`（举例说明）= 用 Doreen 和 Fan 的个人经历展示 S.K.I. 的效果 |
| **错因分类** | 🏷️ 过度推理 — 引言只说了对个人和家庭的好处，你推断成了"对社会的好处" |
| **教训** | 选项多一个词（"to society"）就可能是陷阱，严格看原文范围 |

**示例 — Q11（判断题 T/F/NG）：**

| 项目 | 内容 |
|------|------|
| **题目** | Only one fixed loan should be given to each child. |
| **你选** | NOT GIVEN |
| **正确** | NO |
| **原文定位** | "Small loans are provided **initially**... the enterprises can be **gradually expanded** and consideration can be given to **increasing loan amounts**." |
| **关键词映射** | `only one` ↔ `initially...increasing`（最初→逐步增加 = 不止一次） |
| **错因分类** | 🏷️ NOT GIVEN/FALSE 混淆 — "initially" 暗示后续还有，"increasing" 直接矛盾 |
| **教训** | 题目出现 only/all/never 等绝对词时，大概率答案是 NO，重点找反驳证据 |

#### 🔄 模块三：同义替换积累表

| 原文表达 | 题目表达 | 中文释义 | 题号 |
|---------|---------|---------|------|
| in association with other types of support | as part of a wider program of aid | 配合其他支持 → 更广泛援助的一部分 | Q13 |
| support the economic lives | give business training and loans | 支持经济生活 → 提供培训和贷款 | Q2 |
| choose entrepreneurship | set up their own business | 选择创业 → 自己开业 | Q4 |

> 这张表会**跨篇累积**——做的题越多，积累越丰富。

#### 📝 模块四：核心词汇表

| 词汇 | 释义 | 雅思高频 | 真题出现 |
|------|------|---------|---------|
| **exemplify** /ɪɡˈzemplɪfaɪ/ | v. 举例说明 | ⭐⭐⭐ 学术高频 | 剑4T3P1 |
| **provision** /prəˈvɪʒn/ | n. 提供；条款 | ⭐⭐⭐ 538考点词 | 剑4T3P1 |
| **a dearth of** /dɜːθ/ | 缺乏（= a lack of） | ⭐⭐ 学术中频 | 剑4T3P1 |

> 每个词标注雅思高频程度（基于 538 考点词 + COCA 5000），不浪费时间背低频词。
> "真题出现"列会随着做题**持续累积**。

#### 💡 模块五：反复犯错追踪

```
「重复题干词」追踪：
 • 剑4T3P2 Q21：题目有 "years"，又写了 "600 years"（多写了 years）
 • 剑4T3P3 Q39：题目有 "the"，又写了 "The size"（多写了 The）
 → 两次同款错误！填空题必须把答案放回原句读一遍。

「NOT GIVEN vs FALSE 混淆」追踪：
 • 剑4T3P1 Q11：有直接反驳证据（initially→increasing）应选 NO，误选 NG
 → 提目出现绝对词时，优先找反驳证据。
```

> 这个模块**跨篇追踪**你反复犯的错，做的篇数越多越有价值。

### 最终产出

AI 会生成：
1. **HTML 复盘笔记** — 排版美观，可直接在浏览器中打开
2. **PDF 文件**（可选）— A4 格式，适合打印或存档
3. **工作记忆更新** — 你的错误模式和词汇积累会跨 session 保留

---

## 📊 打分 & 进步统计（v1.2.0 新增）

做完一套完整的阅读题（3 篇 Passage），AI 会自动帮你：

### 成绩单

```
📊 成绩单 — 剑5 Test 4

         P1   P2   P3   总计/40   总用时                        雅思分数
剑5 T4   11   11    7   29/40    34:10+35:32+51:13=120:55      6.5-7.0
```

### 多套考试进步趋势

做了多套之后，AI 会自动汇总你的进步趋势：

```
 场景      P1   P2   P3   总计/40   总用时                        雅思分数
 剑4 T3    7    6    3   16/40    34:40+42:53+47:55=125:28      5.0
 剑4 T4    7    7    5   19/40    33:43+30:59+33:50=98:32       5.5
 剑5 T2    8    9    2   19/40    35:52+36:23+53:32=125:47      5.5
 剑5 T3   11    9    6   26/40    32:40+39:34+34:32=106:46      6.0-6.5
 剑5 T4   11   11    7   29/40    34:10+35:32+51:13=120:55      6.5-7.0
```

AI 还会给出简要的进步分析：

> 正确率在上升（5.0→6.5-7.0），好消息。
> 平均用时 100-125 分钟，大约是考试时间的两倍。速度还需要提上来。
> 不过现阶段先追正确率再追速度是对的，等正确率稳在 7 分之后再专项练速度。

---

## 🎯 Features

| 功能 | 说明 |
|------|------|
| **逐题错因分析** | 定位原文、映射同义替换、分类错因（8 类）、给出 1 句话教训 |
| **同义替换积累** | 自动提取题目-原文同义替换对，跨篇持续积累 |
| **考点词标注** | 基于刘洪波 538 考点词（⭐⭐⭐/⭐⭐/⭐）+ COCA 5000 词频 |
| **易错模式追踪** | 跨篇检测反复犯的错（如总把 NG 选成 FALSE） |
| **📊 打分 & Band 换算** | 每套题自动算分，原始分→雅思 Band 分数换算（学术类） |
| **📈 进步趋势统计** | 多套考试成绩汇总表 + 正确率/速度趋势分析 |
| **⏱️ 分段计时** | 记录 P1/P2/P3 各段用时，对比 60 分钟考试限时 |
| **HTML + PDF 输出** | 排版专业的复盘笔记，支持打印和存档 |

## 📂 File Structure

```
ielts-reading-review/
├── SKILL.md                          # Skill 定义（AI 读这个文件理解工作流）
├── README.md                         # 使用说明（你正在看的这个）
├── assets/
│   └── review-template.html          # HTML 模板 + CSS 样式
├── references/
│   ├── error-taxonomy.md             # 8 类错误分类体系
│   ├── 538-keywords-guide.md         # 考点词评级指南
│   └── review-style-guide.md         # 写作风格规范
└── scripts/
    └── generate-pdf.js               # PDF 生成脚本
```

## 🧠 内置做题方法论

### T/F/NG 三步判断法
1. **找话题** — 原文有没有讨论题目说的这个话题？→ 没有 → **NOT GIVEN**
2. **找立场** — 如果话题存在，作者同意还是反对？→ **TRUE** / **FALSE**
3. **验证** — "如果我选 TRUE/FALSE，能指出原文哪一句吗？"指不出来 → 大概率 **NOT GIVEN**

### 填空题防重复规则
答案不要重复题目中已有的词。填完后把答案放回原句完整读一遍。

### 选择题逐词验证法
选项中的**每个关键词**都要在原文找到对应。"大致相关" ≠ "能选"。前半句对但后半句多了信息 → 干扰项。

## 👤 Who It's For

雅思备考者，尤其是：
- 阅读 5-7 分想突破的
- 复盘效率低，做完题不知道怎么分析的
- 同样的错反复犯，需要系统追踪的
- 想把词汇积累和真题练习结合起来的

## ⚙️ Requirements

- 支持 SKILL.md 的 AI Agent（如 OpenClaw、Claude Code、WorkBuddy/CodeBuddy）
- PDF 导出需要：Node.js + puppeteer-core + 本地 Chrome（可选，不装也能用 HTML）

## 🤝 Contact & Feedback

If this Skill helps your IELTS prep, a ⭐ Star would mean a lot!

如果这个 Skill 对你备考有帮助，欢迎点个 ⭐ 支持！

- 💡 **Feature requests / Bug reports**: [Open an Issue](https://github.com/dengjiawei1226/ielts-reading-review/issues)
- 💬 **WeChat group / 微信交流群**: Scan to join 👇

<p align="center">
  <img src="assets/wechat-group-qr.jpg" alt="微信交流群" width="300">
</p>

> ⚠️ QR code refreshes periodically. If expired, please open an Issue and I'll update it.
>
> 二维码会定期更新。如果过期了，提个 Issue 我会及时换新的。

## License

MIT-0
