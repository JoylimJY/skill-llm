import os
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic deeply nested distractor directory structure
dirs = [
    "drafts/2024/january",
    "drafts/2024/february",
    "drafts/2024/march",
    "archive/old_articles",
    "archive/deleted_sections",
    "references",
    "assets/images",
    "assets/diagrams",
    "notes/research",
    "notes/ideas",
    "publish/ready",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files (unrelated to task)
distractor_files = {
    "drafts/2024/january/draft_travel.md": "# 旅行记录\n\n一段旅行的回忆。\n",
    "drafts/2024/february/draft_food.md": "# 美食探店\n\n这家餐厅真的很好吃。\n",
    "drafts/2024/march/ideas_random.txt": "想法：写一篇关于读书的文章\n",
    "archive/old_articles/remote_work_v1.md": "# 远程工作初探\n\n最初的草稿，已废弃。\n",
    "archive/deleted_sections/cut_section.md": "这段内容被删除了，保留备用。\n",
    "references/productivity_links.txt": "https://example.com/productivity\nhttps://example.com/remote\n",
    "assets/images/placeholder.txt": "(image placeholder)\n",
    "assets/diagrams/workflow.txt": "step1 -> step2 -> step3\n",
    "notes/research/stats_remote.txt": "2023年远程工作数据：全球约有16%的公司完全远程\n",
    "notes/ideas/future_topics.md": "## 未来写作方向\n\n- 冥想\n- 运动习惯\n- 阅读\n",
    "publish/ready/example_published.md": "# 已发布文章示例\n\n这是一篇已经发布的文章。\n",
    ".markdownlint.json": '{"default": true, "MD013": false}',
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN PROBLEM FILE: a messy Chinese article draft about remote work productivity
# It contains:
# - Language violations (Step 3): passive voice, abstract noun subjects, redundant phrases, weak verbs
# - Style violations (Step 5): "不是……而是……" patterns, >3 bolds per section, AI-flavor quoted humor
# - Markdown violations (Step 6): skipped heading level (H2->H4), mixed list markers (- and *), 
#   a heading with too many bolds
# - Content that should be preserved in 素材.md (clearly marked as "可删除" in comments)

article_content = """# 远程工作的效率密码

## 前言

在过去的两年里，收入减少改变了很多人对工作的看法——不是被迫的，而是主动选择了新的生活方式。**远程工作**已经不再是少数人的特权，它变成了一种普遍的**工作形态**。**很多人开始思考**怎么在家里保持高效。说实话，这个问题**困扰了我很久**。

对于这种新型的工作方式，适应是一个过程。问题被解决了，但新的挑战又出现了。

## 时间管理的核心

#### 为什么时间总是不够用

有关时间管理的问题，基于这个原因，很多人会作出努力去尝试各种方法。但是「哲学式」的焦虑往往让人原地打转。

不是方法不对，而是没有找到适合自己的节奏。

* 早上固定时间起床
* 设置工作开始和结束的仪式
- 中午休息不超过一小时
- 避免在工作时间刷社交媒体

**时间管理的关键**是建立节奏，**而不是追求完美**，**因为完美往往是效率的敌人**，**节奏一旦建立就难以打破**。

## 专注力的修炼

### 环境对专注力的影响

专注力的提升被认为是远程工作成功的关键。**一个好的工作环境**对于专注力有着重要的**影响作用**。

这里有几个我试过的方法：

1. 噪音消除耳机的使用
2. 自然光的引入
3. 桌面整洁的维持

### 数字极简主义

不是要你完全戒掉手机，而是要学会和手机「和平共处」。对数字工具的过度依赖让人焦虑。

关闭通知的做法被很多人推崇。**手机的摆放位置**会显著**影响**你的**专注时长**，**这是经过研究证明的**。

## 结语

效率的提升是一个漫长的过程。对个人习惯的建立和坚持的重视需要时间。希望这些经验对你有帮助。

"""

article_path = os.path.join(workspace, "article.md")
with open(article_path, "w", encoding="utf-8") as f:
    f.write(article_content)

print("Workspace generated successfully.")
print(f"Main article: {article_path}")