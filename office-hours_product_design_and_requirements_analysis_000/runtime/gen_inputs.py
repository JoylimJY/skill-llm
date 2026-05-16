import os
import random

random.seed(42)

base = "/workspace"

# --- Directory structure ---
dirs = [
    "conversations",
    "market_research",
    "competitor_notes",
    "funding",
    "team",
    "legal",
    "misc",
    "design_docs/archived",
    "design_docs/templates_old",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files ---

# market_research/china_legaltech_2024.txt
with open(os.path.join(base, "market_research", "china_legaltech_2024.txt"), "w", encoding="utf-8") as f:
    f.write("""中国法律科技市场报告 2024
==========================================
市场规模：预计2027年突破500亿人民币
年增长率：28.3%
主要玩家：无讼、法大大、合同机器人、iCourt
痛点分析：
- 中小律所文书处理效率低
- 案件检索成本高
- 合规审查人工依赖重
投资趋势：2023年共有47起融资事件，平均轮次A轮
结论：法律AI赛道持续热门，头部效应明显
""")

# market_research/survey_notes.txt
with open(os.path.join(base, "market_research", "survey_notes.txt"), "w", encoding="utf-8") as f:
    f.write("""用户调研笔记（问卷形式，n=200）
------------------------------
Q: 您每周花多少时间写诉状？
A: 平均6.2小时

Q: 您愿意为文书自动化工具付费吗？
A: 76%表示"挺有意思"，22%表示"可能会用"

Q: 现有工具满意度
A: 平均3.1/5

注：本数据来源于律师行业微信群问卷，回收率41%
""")

# competitor_notes/competitors.txt
with open(os.path.join(base, "competitor_notes", "competitors.txt"), "w", encoding="utf-8") as f:
    f.write("""竞品分析
==================
1. 无讼案例
   定位：法律数据库+文书模板
   价格：9800元/年/律所
   弱点：模板固定，无AI生成能力

2. 法大大
   定位：合同管理+电子签名
   价格：按签章数收费
   弱点：不涉及诉讼文书

3. ChatLaw (学术)
   定位：研究性质LLM微调
   弱点：无商业化产品

我们的差异点：基于案件事实自动生成起诉状/答辩状，律师只需输入关键事实
""")

# funding/pitch_outline.txt
with open(os.path.join(base, "funding", "pitch_outline.txt"), "w", encoding="utf-8") as f:
    f.write("""融资材料大纲（未完成）
=======================
Slide 1: 封面 - LawDraft.ai
Slide 2: 问题 - 律师每周浪费XX小时
Slide 3: 解决方案
Slide 4: 市场规模 - TAM/SAM/SOM
Slide 5: 产品截图 [TODO]
Slide 6: 商业模式 [TODO]
Slide 7: 团队
Slide 8: 融资需求：300万人民币种子轮

注：Slide 5和6需要产品上线后补充
""")

# team/bios.txt
with open(os.path.join(base, "team", "bios.txt"), "w", encoding="utf-8") as f:
    f.write("""团队介绍
========
创始人：王磊
- 前阿里法律部高级顾问，8年诉讼经验
- 西南政法大学法律硕士
- 曾代理超过300件民商事案件

联合创始人：李思远  
- 前字节跳动NLP工程师，5年AI经验
- 负责技术架构

顾问：张教授（某大学法学院院长）
""")

# legal/incorporation.txt
with open(os.path.join(base, "legal", "incorporation.txt"), "w", encoding="utf-8") as f:
    f.write("""公司注册信息
=============
公司名称：法稿科技（上海）有限公司
注册地：上海市浦东新区
注册资本：100万人民币
成立日期：2024年3月
经营范围：软件开发、法律信息服务
""")

# misc/todos.txt
with open(os.path.join(base, "misc", "todos.txt"), "w", encoding="utf-8") as f:
    f.write("""待办事项
=========
[ ] 完成产品原型
[ ] 联系潜在用户做demo
[ ] 确定定价策略
[ ] 注册域名
[ ] 招聘全栈工程师
[ ] 参加下个月的法律AI峰会
[ ] 回复投资人邮件
""")

# misc/random_notes.txt
with open(os.path.join(base, "misc", "random_notes.txt"), "w", encoding="utf-8") as f:
    f.write("""零散想法
========
- 能不能做成SaaS？按文书数量收费？
- 要不要先做合同审查，门槛低一点？
- 微信小程序 vs web app？
- 数据安全怎么处理——律所对数据很敏感
- 要不要先找10家律所做免费内测？
""")

# design_docs/archived/old_spec_v0.txt
with open(os.path.join(base, "design_docs", "archived", "old_spec_v0.txt"), "w", encoding="utf-8") as f:
    f.write("""旧版功能规格（已废弃）
========================
版本：v0.1 (2024-01)
功能列表：
1. 用户注册登录
2. 案件信息录入
3. 文书模板选择
4. PDF导出

状态：已废弃，架构重新设计中
""")

# design_docs/templates_old/template_v1.txt  
with open(os.path.join(base, "design_docs", "templates_old", "template_v1.txt"), "w", encoding="utf-8") as f:
    f.write("""旧模板（格式错误，不要使用）
==============================
标题：
背景：
需求：
TODO：
""")

# misc/glossary.txt
with open(os.path.join(base, "misc", "glossary.txt"), "w", encoding="utf-8") as f:
    f.write("""法律术语表
==========
起诉状：原告提起诉讼的书面文件
答辩状：被告回应诉讼的书面文件
仲裁申请书：提请仲裁的书面文件
管辖权：法院审理案件的权力范围
诉讼时效：提起诉讼的时间限制
""")

# --- THE MAIN INPUT: Founder conversation transcript ---
# Stage: Has users (20 law firms using it for free) but NO paying customers yet
# → According to skill: 已有用户 → Q2, Q4, Q5 should be the focus
# The transcript contains direct quotes that must appear in the design doc

conversation = """# 产品想法对话记录
## 项目：法稿AI — 诉讼文书自动生成工具
## 日期：2024-11-15
## 参与者：王磊（创始人）

---

[王磊]: 我想做一个工具，帮律师自动生成诉讼文书。输入案件关键事实，输出起诉状、答辩状、仲裁申请书这类文件。

[产品顾问]: 现在有多少律所在用？

[王磊]: 我们现在有20家律所在用内测版本，都是免费的。每天大概生成50-80份文书。

[产品顾问]: 他们怎么用的？你有没有坐下来看过他们用？

[王磊]: 有！这里有个让我很意外的事——本来设计是给主办律师用的，结果发现很多律所是让实习生和助理在用，主办律师只看最终文书做修改。这个用法完全不是我们设计的。

[产品顾问]: 他们现在如果不用你们，怎么写这些文书的？

[王磊]: 大部分律所用的是Word模板库，有的买了无讼的年费套餐拿模板。写一份起诉状大概要2-3小时，助理写完律师还要大改。有家律所告诉我，他们光文书这一块每个月要花掉两个全职助理40%的时间。

[产品顾问]: 你们最窄的切入口是什么？

[王磊]: 我一直在想这个问题。我觉得起诉状是最标准化的，格式相对固定，而且民事借贷纠纷案件量最大、模式最像。如果只做"民事借贷纠纷起诉状自动生成"，可能本周就能让人付钱。

[产品顾问]: 为什么是本周？

[王磊]: 因为已经有3家律所的主任问过我们什么时候开始收费了。其中一家——上海浦东的张律师，他手下7个助理，他说如果我们出正式版他愿意直接签一年合同。

[产品顾问]: 数据安全这块怎么考虑的？

[王磊]: 这是最大的风险。律所对案件数据极其敏感，不太愿意上传到云端。我们在考虑私有化部署方案，但这会大幅增加复杂度。

[产品顾问]: 如果3年后AI能力大幅提升，你们的产品是变得更有用还是更没用？

[王磊]: 我觉得是更有用。核心原因是：文书质量依赖法律判例数据库，我们在持续积累的垂直数据和律所工作流适配才是真正的护城河——通用大模型不会专门优化这些。

[产品顾问]: 好。基于这些，我来梳理一下前提假设。

---

[备注：对话结束，需要基于以上内容生成完整设计文档]
"""

with open(os.path.join(base, "conversations", "founder_interview_transcript.md"), "w", encoding="utf-8") as f:
    f.write(conversation)

print("Workspace generated successfully.")
print(f"Files created in {base}:")
for root, dirs_list, files in os.walk(base):
    level = root.replace(base, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')