import os
import random
import json

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "workspace/content_ops/drafts/2024/q1",
    "workspace/content_ops/drafts/2024/q2",
    "workspace/content_ops/published/wechat",
    "workspace/content_ops/published/weibo",
    "workspace/content_ops/analytics/monthly",
    "workspace/content_ops/analytics/weekly",
    "workspace/tools/config",
    "workspace/tools/logs",
    "workspace/templates/article",
    "workspace/templates/report",
    "workspace/archive/2023",
    "workspace/archive/2022",
]
for d in dirs:
    os.makedirs(f"/{d}", exist_ok=True)

# Distractor files - realistic but misleading
distractors = {
    "/workspace/content_ops/drafts/2024/q1/draft_analysis.txt": """
分析草稿 - 未完成
标题: 暂定
结构: TBD
""",
    "/workspace/content_ops/drafts/2024/q2/article_notes.md": """
# 文章笔记
- 需要找更多数据支撑
- 标题还需打磨
""",
    "/workspace/content_ops/published/wechat/article_list.csv": """id,title,date,reads
1,职场干货大全,2024-01-15,50000
2,副业赚钱秘籍,2024-02-01,80000
3,时间管理神器,2024-03-10,120000
""",
    "/workspace/content_ops/analytics/monthly/jan_2024.json": json.dumps({
        "month": "2024-01",
        "total_articles": 12,
        "avg_reads": 45000,
        "top_article": "职场干货大全"
    }, ensure_ascii=False, indent=2),
    "/workspace/content_ops/analytics/weekly/week10.txt": "Week 10 summary: 3 articles published, avg read rate 62%",
    "/workspace/tools/config/fetch_config.yaml": """
timeout: 30
retry: 3
user_agent: Mozilla/5.0
""",
    "/workspace/tools/logs/fetch_errors.log": """
2024-03-01 10:23:11 ERROR: timeout on mp.weixin.qq.com
2024-03-01 10:23:45 INFO: retry successful
2024-03-05 14:10:02 WARN: rate limit hit
""",
    "/workspace/templates/article/standard_template.md": """
# 文章标题

## 引言

## 正文

## 结语
""",
    "/workspace/templates/report/old_report_format.txt": """
旧版报告格式（废弃）
1. 摘要
2. 内容
3. 建议
""",
    "/workspace/archive/2023/best_articles_2023.json": json.dumps([
        {"title": "2023最火职场文", "reads": 500000},
        {"title": "副业指南2023", "reads": 300000}
    ], ensure_ascii=False, indent=2),
    "/workspace/archive/2022/content_strategy.md": "# 2022内容策略\n已归档，请参考2024版本。",
    "/workspace/content_ops/published/weibo/weibo_posts.txt": "微博发文记录...\n2024-01-01: 新年快乐\n2024-01-15: 干货分享"
}

for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# Create the SKILL.md in workspace
skill_content = """---
name: article-analyzer
description: 爆款文章拆解分析工具。当用户发来公众号文章链接（mp.weixin.qq.com）或其他网页链接并要求拆解、分析、学习、拆文时触发。支持：结构分析、金句提取、选题逻辑、情绪曲线、复刻建议。也支持将分析结果写入飞书文档。
---

# 爆文拆解分析

## 触发条件

- 用户发来公众号/网页链接 + "拆解""分析""拆文""学习这篇文章"等关键词
- 用户说"分析这篇爆文""帮我拆解这篇文章结构"

## 工作流

### Step 1: 抓取全文

```bash
# 微信公众号文章：用 browser 工具（web_fetch 反爬）
browser open url=<用户链接>
browser snapshot format=ai maxChars=15000
```

- 微信文章 **必须用 browser**，不用 web_fetch（反爬）
- 其他网站可用 web_fetch 或 browser 均可
- 目标：获取完整正文内容

### Step 2: 拆解分析

对抓取到的全文执行以下分析维度：

#### 2.1 结构分析
- 标题拆解（标题用了什么技巧？数字？疑问？反差？痛点？）
- 开头手法（故事？数据？提问？场景？共鸣？）
- 段落逻辑（总分总？递进？并列？对比？故事线？）
- 结尾方式（金句收尾？行动号召？开放问题？反转？）

#### 2.2 金句提取
- 提取5-10条最有记忆点的句子
- 标注金句类型：比喻/对比/数据/金句体/反常识

#### 2.3 选题逻辑
- 目标读者画像（是谁？痛点是什么？）
- 情绪曲线（开头什么情绪→中间怎么推→结尾什么情绪）
- 选题角度（是什么让它值得写？独家信息？新视角？争议点？实用价值？）

#### 2.4 可复刻点
- 这个标题模式我可以怎么用？
- 开头手法可以套用在什么主题上？
- 哪些金句可以改编？
- 整体结构适合写什么类型的内容？

### Step 3: 输出报告

默认直接在聊天中输出。如用户要求写文档：

```bash
# 创建飞书文档
feishu_doc create title=<标题> content=<Markdown格式的分析报告>
```

## 报告模板

```markdown
# 🔪 爆文拆解：{文章标题}

## 📊 基本信息
- 标题：{原标题}
- 来源：{公众号名}
- 字数：{估算}
- 阅读量：{如果能获取}

## 🏗️ 结构分析
- 标题技巧：{分析}
- 开头手法：{分析}
- 段落逻辑：{分析}
- 结尾方式：{分析}

## ✍️ 金句TOP5
1. "{金句}" — {类型标注}
2. ...

## 🎯 选题逻辑
- 目标读者：{画像}
- 情绪曲线：{描述}
- 选题价值：{为什么这篇能火}

## 💡 复刻建议
- 标题复刻：{套用模板}
- 开头复刻：{适用场景}
- 结构复刻：{适合什么内容类型}
- 金句改编：{改编示例}
```

## 快速模式

如果用户只说"快速拆解"或"简单看看"，跳过详细分析，只输出：
1. 标题技巧（一句话）
2. 文章结构（一句话）
3. 金句TOP3
4. 能学什么（一句话）
"""

with open("/workspace/SKILL.md", "w", encoding="utf-8") as f:
    f.write(skill_content)

# Create the article server content - a realistic viral article about workplace/career
article_html = """<!DOCTYPE html>
<html>
<head><title>普通人逆袭的秘密：我用这3个方法，从月薪5千到年薪50万 | 职场进化论</title></head>
<body>
<div class="article-content">
<h1>普通人逆袭的秘密：我用这3个方法，从月薪5千到年薪50万</h1>
<p class="source">来源：职场进化论</p>
<p class="reads">阅读量：238,000</p>

<p>你有没有想过，同样是普通家庭出身，同样没有背景、没有资源，为什么有人能在30岁之前实现财务自由，而大多数人却一直在原地打转？</p>

<p>我叫张明，三年前的我，是上海一家小公司的普通文员，税前月薪5000元，租住在合租房里，每个月还完房租和生活费，存款几乎为零。</p>

<p>今天，我在一家互联网公司担任产品总监，年薪超过50万。这中间只用了三年时间。</p>

<p>很多人问我：你是不是运气好？是不是有贵人相助？</p>

<p>不。我只是做对了三件事。</p>

<h2>第一件事：停止用时间换金钱</h2>

<p>绝大多数职场人最大的误区，就是把"努力工作"等同于"拼命加班"。你加班到凌晨，你比任何人都勤奋，但你的老板看到的只是一个"能压榨"的员工，而不是一个"值得培养"的人才。</p>

<p>真正的职场价值，不在于你花了多少时间，而在于你解决了多少问题。</p>

<p>我转变的第一步，是开始用"成果思维"替代"时间思维"——每天下班前，我问自己：今天我创造了什么可量化的价值？</p>

<p>三个月后，我的月薪从5000涨到了8000。</p>

<h2>第二件事：把自己当成一个产品来打造</h2>

<p>你的简历，就是你的产品说明书。你的工作成果，就是你的用户评价。你的人际关系，就是你的渠道网络。</p>

<p>大多数人从来没有认真思考过：我这个"产品"的核心竞争力是什么？我能为谁解决什么问题？</p>

<p>当我开始用产品经理的思维来管理自己的职业发展，一切都不同了。我开始有意识地积累可迁移技能，主动拓展人脉圈，用数据证明自己的价值。</p>

<p>数据不会说谎：我主导的项目让公司转化率提升了37%，这个数字帮我敲开了大厂的门。</p>

<h2>第三件事：让钱为你工作，而不是你为钱工作</h2>

<p>穷人和富人最大的区别，不在于收入，而在于现金流的方向。穷人的钱从口袋流出去，富人的钱从外面流进来。</p>

<p>我用第一年多出来的积蓄，投入了自己的技能提升。我报了产品经理认证课程，花了8000元。很多人觉得我疯了。</p>

<p>但那8000元，在一年内帮我涨薪了60000元。投资回报率：750%。</p>

<p>后来我开始写作，输出行业洞察，积累了一批高质量的读者。这些"软资产"，让我的职业发展有了更多可能性。</p>

<h2>最后想说</h2>

<p>逆袭从来不是一夜之间发生的。它是无数个清醒的选择叠加在一起的结果。</p>

<p>你不需要比别人聪明，你只需要比别人更早想清楚：你想成为什么样的人，然后用系统的方法，一步一步去实现它。</p>

<p>现在，就是最好的开始时机。</p>

<p>如果这篇文章对你有启发，转发给同样在努力的朋友。</p>
</div>
</body>
</html>"""

with open("/workspace/tools/article_server_content.html", "w", encoding="utf-8") as f:
    f.write(article_html)

# Create the article server Python script
server_script = '''#!/usr/bin/env python3
from flask import Flask, Response
import os

app = Flask(__name__)

@app.route("/article")
def article():
    content_path = "/workspace/tools/article_server_content.html"
    with open(content_path, "r", encoding="utf-8") as f:
        content = f.read()
    return Response(content, mimetype="text/html; charset=utf-8")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
'''
with open("/workspace/tools/article_server.py", "w", encoding="utf-8") as f:
    f.write(server_script)

# Create mock web_fetch script
web_fetch_script = '''#!/usr/bin/env python3
"""
Mock web_fetch tool: fetches a URL and prints the content.
Usage: web_fetch <url>
"""
import sys
import urllib.request
import urllib.error

if len(sys.argv) < 2:
    print("Usage: web_fetch <url>", file=sys.stderr)
    sys.exit(1)

url = sys.argv[1]
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        content = response.read().decode("utf-8", errors="replace")
        print(content)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
'''
with open("/workspace/tools/web_fetch", "w", encoding="utf-8") as f:
    f.write(web_fetch_script)

# Create mock feishu_doc script
feishu_doc_script = '''#!/usr/bin/env python3
"""
Mock feishu_doc tool.
Usage: feishu_doc create title=<title> content=<markdown_content>
Saves the document to /workspace/feishu_output/ directory.
"""
import sys
import os
import json
import re
from datetime import datetime

args = " ".join(sys.argv[1:])

# Parse title= and content=
title_match = re.search(r'title=(.+?)(?=\s+content=)', args, re.DOTALL)
content_match = re.search(r'content=(.+)', args, re.DOTALL)

if not title_match or not content_match:
    # Try alternative: title and content as separate args
    title = None
    content = None
    for arg in sys.argv[1:]:
        if arg.startswith("title="):
            title = arg[6:].strip('"\'')
        elif arg.startswith("content="):
            content = arg[8:].strip('"\'')
    if not title or not content:
        print("ERROR: Missing title= or content= parameter", file=sys.stderr)
        sys.exit(1)
else:
    title = title_match.group(1).strip().strip('"\'')
    content = content_match.group(1).strip().strip('"\'')

output_dir = "/workspace/feishu_output"
os.makedirs(output_dir, exist_ok=True)

doc_data = {
    "title": title,
    "content": content,
    "created_at": datetime.now().isoformat(),
    "doc_id": "mock_doc_" + datetime.now().strftime("%Y%m%d_%H%M%S")
}

output_path = os.path.join(output_dir, "latest_doc.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(doc_data, f, ensure_ascii=False, indent=2)

# Also save the raw content as markdown
md_path = os.path.join(output_dir, "latest_doc.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write(f"# {title}\\n\\n")
    f.write(content)

print(f"SUCCESS: Feishu document created.")
print(f"  Title: {title}")
print(f"  Doc ID: {doc_data[\'doc_id\']}")
print(f"  Saved to: {output_path}")
'''
with open("/workspace/tools/feishu_doc", "w", encoding="utf-8") as f:
    f.write(feishu_doc_script)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs, files in os.walk("/workspace"):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")