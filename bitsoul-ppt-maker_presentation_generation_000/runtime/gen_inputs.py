import os
import random

random.seed(42)

# Create deeply nested directory structure with distractor files
dirs = [
    "workspace/docs/drafts",
    "workspace/docs/final",
    "workspace/assets/images",
    "workspace/assets/fonts",
    "workspace/templates/old",
    "workspace/templates/v2",
    "workspace/scripts/utils",
    "workspace/scripts/build",
    "workspace/notes/meeting",
    "workspace/notes/research",
    "workspace/output/archive",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- Distractor files ---

distractor_files = {
    "workspace/docs/drafts/outline_v1.txt": """# 大纲 v1
1. 行业背景
2. 痛点分析
3. 解决方案
4. 案例
5. 总结
（初稿，未完成）""",

    "workspace/docs/drafts/outline_v2.txt": """# 大纲 v2（废弃）
- 市场规模
- 竞品分析
- 技术路线
这个方向已放弃，请忽略。""",

    "workspace/docs/final/meeting_summary_2024.txt": """会议纪要 2024-11-05
参会人：张总、李工、王产品
议题：Q4战略调整
结论：推迟发布，等待市场反应。""",

    "workspace/assets/fonts/README_fonts.txt": """字体说明：
这里存放的字体文件仅供本地测试，不得商用。
HarmonyOS Sans SC - 华为鸿蒙字体
Inter - Google开源字体""",

    "workspace/templates/old/slide_template_2022.html": """<!DOCTYPE html>
<html><head><title>Old Template</title></head>
<body style="background:white;color:black;">
<h1>Slide Title</h1>
<p>Content goes here</p>
</body></html>""",

    "workspace/templates/old/slide_template_2023.html": """<!DOCTYPE html>
<html>
<head><title>2023 Template</title>
<style>body{background:#1a1a2e;color:#eee;font-family:Arial;}</style>
</head>
<body>
<div class="slide" style="width:1280px;height:720px;">
<h1>Title</h1><p>Body</p>
</div>
</body></html>""",

    "workspace/templates/v2/config.json": """{
  "theme": "dark",
  "ratio": "16:9",
  "font": "Arial",
  "colors": {
    "bg": "#1e293b",
    "text": "#f1f5f9"
  }
}""",

    "workspace/scripts/utils/convert.py": """# 旧版转换脚本（已废弃）
def convert_pptx_to_html(path):
    # TODO: 实现转换逻辑
    pass

def extract_text(pptx):
    raise NotImplementedError("未实现")
""",

    "workspace/scripts/build/deploy.sh": """#!/bin/bash
# 部署脚本
echo "Building..."
npm run build
echo "Deploying to server..."
# rsync -avz dist/ user@server:/var/www/html/
echo "Done." """,

    "workspace/notes/meeting/brainstorm_20241210.txt": """头脑风暴记录
- 用AI自动生成PPT
- 风格参考：乔布斯、罗振宇
- 关键：每页只讲一件事
- 颜色：深色系更有科技感
- 字体大、冲击力强""",

    "workspace/notes/research/competitor_analysis.md": """# 竞品分析

| 产品 | 优点 | 缺点 |
|------|------|------|
| Gamma | AI生成快 | 风格单一 |
| Beautiful.ai | 模板多 | 收费 |
| Slidev | 开发者友好 | 学习成本高 |

结论：市场缺少真正的"罗振宇风格"AI PPT工具。""",

    "workspace/output/archive/presentation_draft_v0.html": """<!DOCTYPE html>
<html>
<head><title>Draft v0 - 废弃</title></head>
<body>
<p>这是最早的草稿，已完全废弃，请勿参考。</p>
<p>背景是白色的，不符合要求。</p>
</body>
</html>""",

    "workspace/scripts/utils/text_processor.py": """# 文本处理工具
import re

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def split_paragraphs(text):
    return [p.strip() for p in text.split('\n\n') if p.strip()]
""",
}

for path, content in distractor_files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# --- THE ACTUAL PROBLEM: Raw, dense lecture script ---
lecture_script = """讲稿：《大模型时代，程序员还剩什么？》

各位同事，大家好。今天我想和大家聊一个让很多程序员晚上睡不着觉的问题——在大语言模型横扫技术圈的今天，我们这些写代码的人，到底还剩什么价值？

先说一个数字。GitHub Copilot的官方数据显示，使用AI辅助编程的工程师，代码产出效率提升了55%。这不是小数字。55%，意味着理论上，100个人的工程团队，只需要65个人就能完成同样的工作。

我见过很多工程师的第一反应是否认："AI写的代码质量不行""复杂业务它搞不定""我们的代码库太特殊了"。我理解这种心理，因为这是人类面对威胁时的本能防御。但我必须说，这种防御是危险的。

真正的问题不是AI能不能完全替代程序员，而是：用AI的程序员，会不会替代不用AI的程序员？答案，已经越来越清晰。

那么，在这个新时代，程序员的核心价值在哪里？我认为有三个维度：

第一，系统思维。AI能写函数，但它无法理解为什么你的系统需要这样设计。你选择微服务还是单体架构，选择事件驱动还是请求响应——这些决策背后是对业务的深刻理解，是AI暂时无法替代的判断力。

第二，问题定义能力。大多数情况下，把问题定义清楚，比解决问题更难。一个能精准提问的工程师，能让AI的输出质量提升十倍。这就是"Prompt Engineering"背后真正的价值——不是会用工具，而是能把模糊的业务需求，翻译成精确的技术语言。

第三，质量判断力。AI生成的代码，谁来review？谁来保证它在边界条件下不出错？谁来保证它的安全性？这个守门员的角色，至少在未来五年，仍然是人类程序员不可替代的价值所在。

最后我想说，历史上每一次技术革命，都消灭了一批旧职业，同时创造了更多新职业。蒸汽机消灭了马车夫，但创造了火车司机；互联网消灭了实体书店，但创造了电商运营。大模型时代也不例外。

问题不是"我会不会被替代"，而是"我是否在进化"。

谢谢。
"""

with open("workspace/docs/final/lecture_script.txt", 'w', encoding='utf-8') as f:
    f.write(lecture_script)

print("Workspace initialized successfully.")
print("Files created:")
for path in list(distractor_files.keys()) + ["workspace/docs/final/lecture_script.txt"]:
    print(f"  {path}")