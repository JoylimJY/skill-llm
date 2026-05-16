import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create the skill reference structure
references_dir = workspace / "references"
references_dir.mkdir(exist_ok=True)

# Write the templates.md as per SKILL.md
templates_content = '''# 书籍整理输出模板参考

## 完整版模板

```markdown
# 《书名》深度整理

> 作者：xxx | 出版社：xxx | 出版年份：xxx | 分类：xxx

---

## 📚 书籍信息

| 属性 | 内容 |
|------|------|
| 书名 | 《书名》 |
| 作者 | xxx |
| 出版社 | xxx |
| 出版年份 | xxxx年 |
| 页数 | xxx页 |
| ISBN | xxx |
| 分类 | xxx |

---

## 📖 内容简介

（书籍简介，100-300字）

---

## 🗂️ 章节结构与摘要

### 第一部分：xxx

#### 第x章 章节标题
- **核心内容**：一句话概括
- **关键知识点**：
  - 要点1
  - 要点2

---

## 💡 核心概念

| 序号 | 概念 | 英文 | 简明解释 | 章节 | 应用场景 |
|------|------|------|---------|------|----------|
| 1 | 概念名 | Concept | 解释 | 第x章 | 场景 |

---

## ✨ 金句摘录

### 关于人生
> "xxx"
> —— 作者/书名/第x页

### 关于成长
> "xxx"
> —— 作者/书名/第x页

### 关于智慧
> "xxx"
> —— 作者/书名/第x页

---

## 🎯 核心观点

### 观点一：xxx
**论述**：xxx

### 观点二：xxx
**论述**：xxx

---

## 💭 读后感

### 📌 一句话总结
（用一句话总结这本书）

### 🎯 核心收获
1. **认知提升**：xxx
2. **技能习得**：xxx
3. **情感共鸣**：xxx

### 👍 优点
- 优点1
- 优点2

### 👎 不足
- 不足1
- 不足2

### 📎 适合谁读
- 适合人群1
- 适合人群2

### ⭐ 我的评分
★★★★☆（4/5星）

---

## 🧠 知识体系

### 知识框架
- 大框架
  - 子要点
  - 子要点

### 实践应用
（书中知识如何应用到实际）

### 相关推荐
- 《相关书籍1》
- 《相关书籍2》

---

*整理时间：2026-01-01*
```

## 思维导图模板（Mermaid 格式）

```markdown
## 🌟 思维导图

```mermaid
graph TD
    A[书籍主题] --> B[第一部分]
    A --> C[第二部分]
    A --> D[第三部分]
    
    B --> B1[章节1]
    B --> B2[章节2]
    
    C --> C1[章节3]
    C --> C2[章节4]
    
    D --> D1[章节5]
    D --> D2[章节6]
```
```

## 概念表格模板

```markdown
## 核心概念速查

| 序号 | 概念 | 英文 | 简明解释 | 章节 | 应用场景 |
|------|------|------|---------|------|----------|
| 1 | 概念名 | Concept | 解释 | 第x章 | 场景 |
```

## 金句模板

```markdown
## ✨ 金句摘录

### 关于人生
> "xxx"
> —— 作者/书名/第x页

### 关于成长
> "xxx"
> —— 作者/书名/第x页

### 关于智慧
> "xxx"
> —— 作者/书名/第x页
```

## 读后感模板

```markdown
## 💭 读后感

### 📌 一句话总结
（用一句话总结这本书）

### 🎯 核心收获
1. **认知提升**：xxx
2. **技能习得**：xxx
3. **情感共鸣**：xxx

### 👍 优点
- 优点1
- 优点2

### 👎 不足
- 不足1
- 不足2

### 📎 适合谁读
- 适合人群1
- 适合人群2

### ⭐ 我的评分
★★★★☆（4/5星）
```
'''

(references_dir / "templates.md").write_text(templates_content, encoding="utf-8")

# Create realistic distractor directory structure
distractor_dirs = [
    workspace / "projects" / "q1_review",
    workspace / "projects" / "team_learning",
    workspace / "notes" / "meetings" / "2024",
    workspace / "notes" / "personal",
    workspace / "books" / "archive",
    workspace / "books" / "wishlist",
    workspace / "templates" / "reports",
    workspace / "data" / "surveys",
]

for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    workspace / "projects" / "q1_review" / "kpi_summary.md": "# Q1 KPI Summary\n\n- Team velocity: 42 points\n- Books read: 3\n- Training hours: 24\n",
    workspace / "projects" / "team_learning" / "reading_list.txt": "1. The Mythical Man-Month\n2. Clean Code\n3. Designing Data-Intensive Applications\n4. The Pragmatic Programmer\n",
    workspace / "projects" / "team_learning" / "schedule.csv": "Week,Book,Presenter\n1,人月神话,Alice\n2,代码整洁之道,Bob\n3,设计数据密集型应用,Carol\n",
    workspace / "notes" / "meetings" / "2024" / "book_club_jan.md": "# Book Club January\n\nDiscussed: 人月神话\nAttendees: Alice, Bob, Carol, Dave\nKey takeaway: Brooks' Law is real.\n",
    workspace / "notes" / "meetings" / "2024" / "retrospective_q4.md": "# Q4 Retrospective\n\n## What went well\n- Completed reading program\n\n## What to improve\n- Better note-taking\n",
    workspace / "notes" / "personal" / "todos.md": "- [ ] Finish reading 人月神话\n- [ ] Write notes on chapter 5\n- [ ] Share insights with team\n",
    workspace / "books" / "archive" / "index.json": '{"archived": ["clean_code_notes.md", "pragmatic_programmer_notes.md"], "last_updated": "2024-12-01"}\n',
    workspace / "books" / "wishlist" / "next_reads.txt": "人月神话 (The Mythical Man-Month)\n领域驱动设计\n微服务架构设计模式\n",
    workspace / "templates" / "reports" / "weekly_report.md": "# Weekly Report Template\n\n## Progress\n\n## Blockers\n\n## Next Steps\n",
    workspace / "data" / "surveys" / "reading_habits.csv": "Name,BooksPerMonth,PreferredFormat\nAlice,2,ebook\nBob,1,physical\nCarol,3,ebook\n",
    workspace / "data" / "surveys" / "satisfaction.json": '{"program": "book_club", "satisfaction": 4.2, "responses": 12}\n',
    workspace / "projects" / "q1_review" / "action_items.txt": "1. Establish book notes template\n2. Share summaries team-wide\n3. Schedule monthly reviews\n",
}

for path, content in distractors.items():
    path.write_text(content, encoding="utf-8")

# Create a partial/incomplete old notes file as a red herring
old_notes = workspace / "books" / "archive" / "人月神话_draft.md"
old_notes.write_text(
    "# 人月神话 草稿\n\n这只是一个草稿，格式不完整，需要重新整理。\n\n## 一些想法\n- 布鲁克斯法则\n- 没有银弹\n",
    encoding="utf-8"
)

print("Workspace initialized successfully.")
print("Directory structure:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")