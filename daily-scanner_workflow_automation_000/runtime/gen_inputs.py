import os
import random
import time
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── 1.  Build the full Obsidian-like directory tree (distractors included) ──────

dirs = [
    "Desktop/Obsidian/sky的知识库/00-Inbox/录音文件/Get笔记",
    "Desktop/Obsidian/sky的知识库/00-Inbox/录音文件/其他录音",
    "Desktop/Obsidian/sky的知识库/00-Inbox/图片",
    "Desktop/Obsidian/sky的知识库/01-Projects/项目A",
    "Desktop/Obsidian/sky的知识库/01-Projects/项目B",
    "Desktop/Obsidian/sky的知识库/02-Areas/个人成长",
    "Desktop/Obsidian/sky的知识库/02-Areas/健康",
    "Desktop/Obsidian/sky的知识库/03-Resources/模板",
    "Desktop/Obsidian/sky的知识库/03-Resources/参考资料",
    "Desktop/Obsidian/sky的知识库/04-Archive/2023",
    "Desktop/Obsidian/sky的知识库/04-Archive/2024",
    "Desktop/Obsidian/sky的知识库/05-MOC",
    "Desktop/Obsidian/sky的知识库/Daily Notes",
    "Desktop/tmp/old_recordings",
    "Desktop/tmp/processed",
    "Documents/contracts",
    "Documents/finance",
    "Downloads/软件安装包",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── 2.  Helper: set a file's mtime ──────────────────────────────────────────────

def set_mtime(path: Path, hours_ago: float):
    ts = time.time() - hours_ago * 3600
    os.utime(path, (ts, ts))

# ── 3.  DISTRACTOR files (old / wrong location / irrelevant) ────────────────────

distractor_files = {
    "Desktop/Obsidian/sky的知识库/00-Inbox/录音文件/其他录音/会议回顾-2024-01-10.txt": (
        "关于Q4复盘的一些想法，主要是内部流程问题。", 30
    ),
    "Desktop/Obsidian/sky的知识库/00-Inbox/录音文件/Get笔记/old-灵感-20231201.txt": (
        "灵感：做一个AI驱动的内容推荐引擎，想法很有趣。启发来自最近读的论文。", 48.5
    ),
    "Desktop/Obsidian/sky的知识库/00-Inbox/录音文件/Get笔记/already-processed-客户ABC.txt": (
        "客户ABC，报价50万，GEO项目，需求很明确，已跟进。", 72
    ),
    "Desktop/Obsidian/sky的知识库/01-Projects/项目A/需求文档.md": (
        "# 项目A需求\n- 功能1\n- 功能2\n- 接口对接", 5
    ),
    "Desktop/Obsidian/sky的知识库/03-Resources/模板/日报模板.md": (
        "## 日报模板\n今日完成：\n明日计划：\n遇到问题：", 10
    ),
    "Desktop/Obsidian/sky的知识库/Daily Notes/2024-06-01.md": (
        "今天天气不错，早上跑步5公里，读了一本书。", 15
    ),
    "Desktop/tmp/old_recordings/backup-note.txt": (
        "客户沟通记录备份，合同已签。", 36
    ),
    "Documents/contracts/合同模板2024.txt": (
        "甲方：xxx 乙方：yyy 合同金额：100万", 100
    ),
    "Desktop/Obsidian/sky的知识库/04-Archive/2024/年终总结.md": (
        "2024年总结：完成了15个客户项目，渠道拓展了8个合作伙伴。", 200
    ),
    "Desktop/Obsidian/sky的知识库/02-Areas/个人成长/阅读笔记.md": (
        "读《原则》：保持开放心态，拥抱痛苦。", 7
    ),
    "Downloads/软件安装包/软件说明.txt": (
        "安装步骤：1. 解压 2. 运行安装程序 3. 重启", 50
    ),
}

for rel_path, (content, hours_ago) in distractor_files.items():
    p = workspace / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    set_mtime(p, hours_ago)

# ── 4.  VALID Get笔记 files (within 24 hours, to be classified) ─────────────────

get_note_dir = workspace / "Desktop/Obsidian/sky的知识库/00-Inbox/录音文件/Get笔记"

valid_notes = {
    # 客户沟通 (2 files)
    "note-20240615-客户北京鑫达.txt": {
        "content": (
            "和北京鑫达科技的负责人王总通话，讨论了GEO培训项目合作方案。"
            "客户对我们的方案很感兴趣，需要我们提交一份详细报价，预算在80万左右。"
            "他们的核心需求是帮助销售团队提升GEO技能，合同周期6个月。"
            "下周二王总会带采购部门一起开会确认细节。"
        ),
        "hours_ago": 3,
    },
    "note-20240615-客户上海明途.txt": {
        "content": (
            "上海明途教育张经理沟通，他们有培训需求，涉及合作和合同签署流程。"
            "对方希望了解我们的报价体系，以及是否可以做定制化方案。"
            "张经理说明途今年预算紧，可能需要分期付款，合同金额预计30万。"
            "这个客户需要跟进，下周发送正式报价单。"
        ),
        "hours_ago": 6,
    },
    # 内部会议 (1 file)
    "note-20240615-内部对齐会议.txt": {
        "content": (
            "今天下午的内部会议，主要是Q3策略对齐和分工安排。"
            "决策：渠道团队重点攻华南区域，内容团队本季度聚焦短视频矩阵。"
            "待办事项：\n"
            "1. 李明负责整理华南渠道名单，截止6月20日\n"
            "2. 陈梅负责制定内容排期，截止6月18日\n"
            "3. 全员参与下周一的进度同步会，张总主持\n"
            "整体团队进度良好，但需要加快销售漏斗转化速度。"
        ),
        "hours_ago": 8,
    },
    # 渠道合作 (1 file)
    "note-20240615-渠道新合作伙伴.txt": {
        "content": (
            "今天接触了一个新的渠道合作伙伴——成都智联教育，他们做职业培训联盟。"
            "关键人是赵总，专门做渠道推荐和介绍业务，他们有200多家企业客户资源。"
            "合作模式：他们介绍客户，我们给15%的渠道佣金。"
            "赵总表示很有意愿合作，建议签一个渠道合作协议。"
        ),
        "hours_ago": 12,
    },
    # 灵感/想法 (1 file)
    "note-20240615-产品灵感.txt": {
        "content": (
            "灵感：今天看到一篇关于AI辅助学习的文章，启发很大。"
            "想法：能不能开发一个自动生成企业培训课程的工具？"
            "思路：用AI分析企业岗位需求，自动匹配课程内容，生成个性化学习路径。"
            "这个感悟来自和几个HR聊天，他们都说手工制定培训计划太耗时了。"
        ),
        "hours_ago": 15,
    },
    # 内容创作 (1 file)
    "note-20240615-短视频选题.txt": {
        "content": (
            "内容创作规划：短视频脚本方向讨论。"
            "选题1：《5个让销售业绩翻倍的AI工具》— 干货类，适合公众号和短视频双发。"
            "选题2：《老板必看！用AI做员工培训，效率提升300%》— 素材已整理好。"
            "下周开始拍摄，需要准备脚本和场景布置，目标是发布3条短视频。"
        ),
        "hours_ago": 18,
    },
    # 低价值 / 无价值 note (should be skipped)
    "note-20240615-无内容备忘.txt": {
        "content": (
            "嗯……这个……等一下再说，先记录一下，回头处理。好的就这样。"
        ),
        "hours_ago": 2,
    },
}

for filename, info in valid_notes.items():
    p = get_note_dir / filename
    p.write_text(info["content"], encoding="utf-8")
    set_mtime(p, info["hours_ago"])

# ── 5.  投资决策 note (within 24h) ─────────────────────────────────────────────

investment_note = get_note_dir / "note-20240615-投资BP讨论.txt"
investment_note.write_text(
    "今天和一位天使投资人聊了融资的事情。"
    "对方问了我们的BP，对估值逻辑很感兴趣。"
    "目前我们估值2000万，计划融资500万，出让25%股权。"
    "投资人说需要看详细的财务模型和BP，下周发给他。",
    encoding="utf-8"
)
set_mtime(investment_note, 20)

# ── 6.  Sanity-check print ──────────────────────────────────────────────────────

print("Workspace structure created.")
print(f"Get笔记 files: {list(get_note_dir.iterdir())}")