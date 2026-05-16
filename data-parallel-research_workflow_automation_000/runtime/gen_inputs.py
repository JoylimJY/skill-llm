import os
import json
import yaml
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "research_archive/2022/q1",
    "research_archive/2022/q3",
    "research_archive/2023/q2",
    "research_archive/2023/q4",
    "drafts/v1/sections",
    "drafts/v2/sections",
    "references/primary",
    "references/secondary",
    "templates/old",
    "templates/deprecated",
    "coordination/logs",
    "coordination/notes",
    "output/final",
    "output/interim",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - various irrelevant or misleading content
distractor_files = {
    "research_archive/2022/q1/market_brief.txt": "Outdated market analysis from 2022. Do not use for current planning.",
    "research_archive/2022/q3/competitor_notes.md": "# Old Competitor Notes\n- Company A: defunct\n- Company B: merged\n- Company C: unknown status",
    "research_archive/2023/q2/regulatory_scan.txt": "Preliminary regulatory scan - incomplete. Regulatory framework changed in 2024.",
    "research_archive/2023/q4/tech_trends.json": json.dumps({"year": 2023, "trends": ["AI diagnostics", "telemedicine"], "status": "outdated"}),
    "drafts/v1/sections/intro.md": "# Introduction\nThis is a placeholder draft. Replace with final content.",
    "drafts/v1/sections/conclusion.md": "# Conclusion\nTBD - pending research completion.",
    "drafts/v2/sections/executive_summary.txt": "Executive summary placeholder - do not distribute.",
    "references/primary/WHO_report_stub.txt": "WHO Report citation stub: [CITATION NEEDED]",
    "references/secondary/analyst_notes.txt": "Generic analyst notes - not verified. Use with caution.",
    "templates/old/research_template_v1.md": "# Old Research Template (DEPRECATED)\nScope: [fill in]\nNotes: [fill in]\n\nDo not use - replaced by v2.",
    "templates/deprecated/agent_brief_v0.txt": "DEPRECATED AGENT BRIEF FORMAT:\nTopic: ___\nDo research on this topic.\nReturn whatever you find.",
    "coordination/logs/session_001.txt": "Session log: single-agent run on full report. Duration: 14 hours. Quality: poor due to context overflow.",
    "coordination/notes/lessons_learned.txt": "Lesson: Running all research sequentially takes too long. Need better approach.",
    "output/interim/partial_report_draft.txt": "Partial report draft - sections 1 and 2 only. Remaining sections incomplete.",
    "output/final/.gitkeep": "",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE CORE PROBLEM FILE: A messy, complex research brief
# This brief contains 6 subtopics, some independent, some with causal dependencies
research_brief = {
    "project": "中国数字健康市场进入战略研究报告",
    "client": "MedTech Global Ventures",
    "deadline": "2025-08-01",
    "report_language": "Chinese",
    "sections_required": [
        {
            "id": "A",
            "title": "中国数字健康市场规模与增速",
            "description": "分析2023-2025年中国数字健康（含远程医疗、AI诊断、健康管理App）市场的整体规模、历史增速及未来预测。需要量化数据支撑。",
            "key_questions": [
                "2024年中国数字健康市场总规模（人民币/美元）？",
                "过去3年的复合年增长率（CAGR）？",
                "各细分市场（远程医疗/AI诊断/健康管理）的占比？",
                "2025-2027年市场预测数据？"
            ],
            "suggested_sources": ["艾瑞咨询", "弗若斯特沙利文报告", "国家卫健委数据"],
            "notes": "这是基础数据章节，其他章节可能引用此处数据"
        },
        {
            "id": "B",
            "title": "监管政策与合规要求",
            "description": "梳理中国数字健康领域的监管框架，包括互联网医院牌照、数据本地化要求（数据安全法/个人信息保护法）、AI医疗器械审批流程等。",
            "key_questions": [
                "互联网医院牌照的申请条件和流程？",
                "医疗数据跨境传输的限制？",
                "AI辅助诊断产品的NMPA审批类别和周期？",
                "外资进入数字健康领域的股权比例限制？"
            ],
            "suggested_sources": ["国家卫健委官网", "NMPA官网", "中国政府网"],
            "notes": "独立章节，不依赖其他章节结论"
        },
        {
            "id": "C",
            "title": "主要竞争对手分析",
            "description": "对中国数字健康市场Top 5-8家本土企业进行深度画像，包括平安好医生、丁香园、微医、阿里健康、京东健康等。",
            "key_questions": [
                "各竞品的核心产品矩阵和差异化定位？",
                "各竞品2023-2024年的营收规模和盈利状况？",
                "各竞品的技术栈和AI能力对比？",
                "各竞品的市场份额和用户规模？"
            ],
            "suggested_sources": ["各企业年报", "36氪", "动脉网"],
            "notes": "独立章节，不依赖其他章节结论"
        },
        {
            "id": "D",
            "title": "技术架构合规性要求",
            "description": "基于监管政策的具体要求，分析进入中国市场所需的技术架构调整，包括数据本地化部署方案、与NMPA要求匹配的AI模型可解释性要求等。",
            "key_questions": [
                "数据本地化部署的具体技术方案选项？",
                "符合NMPA要求的AI模型文档和验证要求？",
                "与国内医院HIS系统对接的技术标准？",
                "网络安全等级保护2.0的具体技术要求？"
            ],
            "suggested_sources": ["等保2.0标准文档", "NMPA技术指导原则", "卫生信息标准"],
            "notes": "此章节必须在章节B（监管政策）研究完成后才能开展，需要基于B的发现来确定技术要求"
        },
        {
            "id": "E",
            "title": "市场进入定价策略",
            "description": "制定针对中国数字健康市场的定价策略建议，需综合考虑本土竞品定价、市场支付意愿和目标细分市场。",
            "key_questions": [
                "主要竞品的定价模式（订阅/按次/B端合同）和价格区间？",
                "中国医疗机构和个人用户的数字健康服务付费意愿？",
                "差异化定价策略的可行性（地域/机构级别）？",
                "医保接入对定价的影响？"
            ],
            "suggested_sources": ["竞品公开价格信息", "用户调研报告", "医保政策文件"],
            "notes": "定价策略需要基于章节A（市场规模/支付意愿数据）和章节C（竞品定价数据）的发现，三者存在数据依赖关系"
        },
        {
            "id": "F",
            "title": "用户行为与需求洞察",
            "description": "分析中国数字健康用户的核心需求、使用习惯、痛点和决策因素，覆盖B端（医疗机构）和C端（个人用户）两类用户群体。",
            "key_questions": [
                "C端用户最高频使用的数字健康服务类型？",
                "B端医疗机构采购数字健康产品的关键决策因素？",
                "用户对AI辅助诊断的接受度和信任度？",
                "不同年龄层、地域的数字健康使用差异？"
            ],
            "suggested_sources": ["艾瑞咨询用户报告", "中国互联网络信息中心(CNNIC)", "第三方用研报告"],
            "notes": "独立章节，不依赖其他章节结论"
        }
    ],
    "integration_requirements": {
        "cross_validation": "需要检查各章节数据口径一致性（如市场规模数据来源、竞品名称统一）",
        "contradiction_handling": "如不同来源数据有出入，需标注并说明差异原因",
        "final_deliverable": "统一口径的完整报告，各章节数据互相引用时保持一致"
    },
    "special_instructions": "请制定一个研究协调方案，说明如何高效组织这6个章节的研究工作。方案需要说明哪些章节可以同时开展，哪些必须按顺序，以及如何整合各章节成果。"
}

with open(os.path.join(workspace, "research_brief.json"), "w", encoding="utf-8") as f:
    json.dump(research_brief, f, ensure_ascii=False, indent=2)

# Also create a plain text version for accessibility
brief_text = """
项目名称：中国数字健康市场进入战略研究报告
客户：MedTech Global Ventures
截止日期：2025-08-01

本报告共需完成6个研究章节（A-F）。请制定高效的研究协调方案。

章节列表：
A. 中国数字健康市场规模与增速
B. 监管政策与合规要求  
C. 主要竞争对手分析
D. 技术架构合规性要求（注：需在B完成后开展）
E. 市场进入定价策略（注：需在A和C完成后开展）
F. 用户行为与需求洞察

详细内容见 research_brief.json
"""

with open(os.path.join(workspace, "research_brief_summary.txt"), "w", encoding="utf-8") as f:
    f.write(brief_text)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 2} files across {len(dirs)} directories")