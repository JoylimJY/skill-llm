import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "lab/meetings/2024-q1",
    "lab/meetings/2024-q2",
    "lab/members/alumni",
    "lab/members/current",
    "lab/projects/nlp-core",
    "lab/projects/cv-side",
    "lab/resources/papers",
    "lab/resources/datasets",
    "lab/admin/budget",
    "lab/admin/hr",
    "scripts",
    "refs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# distractor files
distractor_files = {
    "lab/meetings/2024-q1/notes.txt": "Weekly sync notes. Topics: GPU allocation, paper deadlines.",
    "lab/meetings/2024-q2/notes.txt": "Q2 planning. Focus: NLP benchmark, new hires.",
    "lab/members/alumni/zhang_wei.md": "# Zhang Wei\nAlumnus. PhD 2023. Now at Tencent.",
    "lab/members/current/roster.csv": "name,role,join_year\nLi Ming,PhD,2022\nWang Fang,PostDoc,2021",
    "lab/projects/nlp-core/README_old.md": "Old NLP core project readme. Deprecated.",
    "lab/projects/cv-side/status.txt": "On hold pending GPU budget approval.",
    "lab/resources/papers/reading_list.txt": "1. Attention is All You Need\n2. BERT\n3. GPT-4 Technical Report",
    "lab/resources/datasets/index.json": json.dumps({"datasets": ["C3", "DRCD", "SQuAD-zh"]}),
    "lab/admin/budget/fy2024.csv": "category,amount\nGPU,50000\nTravel,8000\nMisc,2000",
    "lab/admin/hr/onboarding_checklist.txt": "1. Sign NDA\n2. Setup VPN\n3. Join Feishu group",
    "scripts/sync_papers.py": "# placeholder sync script\nprint('syncing papers...')",
    "refs/feishu_api_note.txt": "Internal note: local mock API runs on port 8765.",
}

for fpath, content in distractor_files.items():
    full = os.path.join(workspace, fpath)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

# ── THE CORE PROBLEM FILES ────────────────────────────────────────────────

# 1. The existing Feishu document state (simulated as a JSON in the mock server state dir)
#    This represents a document already live on the mock Feishu server.
#    The agent must NOT overwrite this; it must append/insert into it.

existing_doc = {
    "document_id": "doc_onboarding_2024",
    "title": "NLP Lab 新成员入门指南 2024",
    "blocks": [
        {
            "block_id": "blk_001",
            "type": "heading1",
            "content": "欢迎加入 NLP 实验室"
        },
        {
            "block_id": "blk_002",
            "type": "paragraph",
            "content": "本文档面向所有新加入实验室的同学，帮助你快速了解实验室的基本运作方式。"
        },
        {
            "block_id": "blk_003",
            "type": "heading2",
            "content": "基础环境配置"
        },
        {
            "block_id": "blk_004",
            "type": "paragraph",
            "content": "请按照以下步骤完成本地开发环境配置：安装 Python 3.10+，克隆核心仓库，配置 VPN 访问。"
        },
        {
            "block_id": "blk_005",
            "type": "heading2",
            "content": "实验室规范"
        },
        {
            "block_id": "blk_006",
            "type": "paragraph",
            "content": "每周五提交周报，代码必须经过 review，数据集访问需申请权限。"
        }
    ],
    "url": "http://localhost:8765/docs/doc_onboarding_2024"
}

os.makedirs(os.path.join(workspace, "mock_server_state"), exist_ok=True)
with open(os.path.join(workspace, "mock_server_state", "doc_onboarding_2024.json"), "w", encoding="utf-8") as f:
    json.dump(existing_doc, f, ensure_ascii=False, indent=2)

# 2. The raw MESSY chat-style draft that must be formalized into a proposal section
#    This is what the agent receives as input material to transform.
chat_draft = """
跟大家说下我们想申请的那个项目：

就是想做一个自动摘要的事情，主要是中文长文档那种，现在市面上的方案都不太行，
要么抽取式、要么太短、要么中文支持差。

背景嘛就是实验室有一堆医疗病历文本没法处理，大概十万篇左右，然后有个合作方想要自动化摘要能力，
给了一点经费支持大概20万。

然后我们的想法是：
- 先做一个数据清洗流程
- 然后 fine-tune 一个小模型（大概7B左右）
- 再做个评估系统，用 ROUGE 和人工对比

周期大概6个月？然后需要两个人全职做，再加一个实习生。

预期产出就是一篇 ACL 级别的论文，然后给合作方一个可用的系统。

我觉得这个挺靠谱的，大家觉得呢
"""

with open(os.path.join(workspace, "raw_proposal_draft.txt"), "w", encoding="utf-8") as f:
    f.write(chat_draft)

# 3. A task instruction file telling the agent what to do (business context only, no skill hints)
task_instruction = """任务说明（内部文档）

背景：
实验室的「新成员入门指南 2024」飞书文档（文档 ID：doc_onboarding_2024）目前已有基础内容，
正在持续更新中。现在需要在该文档末尾正式加入一个新的研究课题申请板块，
把 raw_proposal_draft.txt 里的聊天记录整理成可以对外提交的正式提案。

要求：
1. 不要破坏文档已有内容，只在现有内容后面追加新板块。
2. 把聊天草稿改成正式申请材料风格（去掉口语、重建论证结构）。
3. 文档内容要做到即使脱离当前聊天也能独立成立（补充必要上下文）。
4. 完成后，把文档链接返回出来。

Mock API 端点（本地）：
- GET  http://localhost:8765/docs/<doc_id>           # 读取文档
- POST http://localhost:8765/docs/<doc_id>/update    # 更新文档
- GET  http://localhost:8765/docs/<doc_id>/url       # 获取文档链接

请完成上述任务。
"""

with open(os.path.join(workspace, "TASK.md"), "w", encoding="utf-8") as f:
    f.write(task_instruction)

# 4. Write an operation log file that the agent must append to after completing the task
#    This simulates a real workflow requirement
with open(os.path.join(workspace, "operation_log.txt"), "w", encoding="utf-8") as f:
    f.write("# Operation Log\n")
    f.write("# Format: [timestamp] action | doc_id | detail\n")
    f.write("2024-01-15 10:23 | create | doc_onboarding_2024 | Initial document created\n")
    f.write("2024-02-01 14:05 | update | doc_onboarding_2024 | Added environment setup section\n")

print("Workspace initialized successfully.")
print(f"Files created in {workspace}")