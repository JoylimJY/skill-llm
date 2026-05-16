import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(exist_ok=True)

# ── Deep directory structure with distractors ──────────────────────────────────

dirs = [
    "project_docs/internal",
    "project_docs/external",
    "team_profiles",
    "financials/q1",
    "financials/q2",
    "market_research/competitors",
    "market_research/reports",
    "tech_specs/v1",
    "tech_specs/v2",
    "admin/contracts",
    "admin/hr",
    "lab_records/2022",
    "lab_records/2023",
    "pitch_archive/round1",
    "pitch_archive/round2",
]

for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────

distractors = {
    "project_docs/internal/meeting_notes_2023_11.txt": (
        "团队内部会议纪要 2023-11-15\n"
        "议题：专利申请进度、实验室搬迁、报销流程\n"
        "结论：推迟到下季度讨论商业化\n"
    ),
    "project_docs/external/investor_email_draft.txt": (
        "Draft: Dear Investor,\nWe are a deep-tech team from Tsinghua University.\n"
        "Our LiDAR-on-chip solution targets autonomous vehicles.\n"
        "(未完成草稿，数据待补充)\n"
    ),
    "team_profiles/cv_zhang_wei.md": (
        "# 张伟 – 首席科学家\n"
        "教育背景：清华大学物理系博士\n"
        "研究方向：集成光子学、片上LiDAR\n"
        "发表论文：18篇，授权专利：3项\n"
        "创业经验：无\n"
    ),
    "team_profiles/cv_li_mengnan.md": (
        "# 李梦楠 – 联合创始人（在读博士生）\n"
        "研究方向：信号处理、嵌入式系统\n"
        "曾参加挑战杯获省级二等奖\n"
        "负责产品化工作\n"
    ),
    "team_profiles/cv_chen_rui.md": (
        "# 陈睿 – MBA（外部引进）\n"
        "背景：某咨询公司3年，熟悉汽车行业\n"
        "加入时间：2024年3月（兼职）\n"
    ),
    "financials/q1/budget_draft.xlsx.txt": (
        "[占位符] 季度预算草稿，数字待CFO确认\n"
        "研发费用：约120万\n"
        "人力成本：待定\n"
    ),
    "financials/q2/runway_calc.txt": (
        "当前现金储备：约80万人民币\n"
        "月燃烧率：估算15-20万\n"
        "Runway：4-5个月\n"
    ),
    "market_research/competitors/competitor_list.csv": (
        "公司名,国家,融资轮次,技术路线\n"
        "Luminar,美国,IPO,机械式LiDAR\n"
        "Innoviz,以色列,C轮,MEMS LiDAR\n"
        "禾赛科技,中国,IPO,机械+MEMS混合\n"
        "速腾聚创,中国,上市,MEMS LiDAR\n"
    ),
    "market_research/reports/tam_notes.txt": (
        "备注：全球LiDAR市场TAM数据引用来源不一，\n"
        "Yole预测2028年约50亿美元，IDC数据差异较大。\n"
        "具体细分市场数据需进一步核实。\n"
    ),
    "tech_specs/v1/chip_spec_draft_v1.txt": (
        "片上LiDAR规格（草稿v1）\n"
        "扫描角度：±30°\n"
        "测距精度：±2cm @100m\n"
        "功耗：<5W\n"
        "芯片尺寸：10mm×5mm\n"
        "备注：v1仅实验室验证，未做量产评估\n"
    ),
    "tech_specs/v2/chip_spec_draft_v2.txt": (
        "片上LiDAR规格（草稿v2，更新于2024-02）\n"
        "扫描角度：±45°\n"
        "测距精度：±1.5cm @120m\n"
        "功耗：<4W（目标值，未验证）\n"
        "芯片尺寸：8mm×4mm\n"
        "备注：v2性能数据为仿真结果，流片计划2024Q3\n"
    ),
    "admin/contracts/nda_template.txt": (
        "[保密协议模板，非正式版本]\n"
        "本协议由______与______签署，保密期限______年。\n"
    ),
    "admin/hr/headcount_plan.txt": (
        "招聘计划：\n"
        "- 硬件工程师 x2（Q2）\n"
        "- 销售/BD x1（Q3，待融资后）\n"
        "- 算法工程师 x1（Q3）\n"
    ),
    "lab_records/2022/experiment_log_2022.txt": (
        "实验记录 2022：\n"
        "- 完成单模波导损耗测试\n"
        "- 光栅耦合效率达到82%\n"
        "- 与合作企业联合测试失败（对方提前退出）\n"
    ),
    "lab_records/2023/patent_filings.txt": (
        "专利申请记录 2023：\n"
        "- CN202310XXXXX.X《一种集成光子芯片LiDAR扫描方法》（受理中）\n"
        "- PCT/CN2023/XXXXXX（国际申请，审查中）\n"
    ),
    "pitch_archive/round1/pitch_deck_feedback.txt": (
        "评委反馈（挑战杯省赛，2023年10月）：\n"
        "1. 技术亮点突出，但商业模式不清晰\n"
        "2. 目标客户描述过于宽泛（'所有自动驾驶企业'）\n"
        "3. 竞争壁垒需强化，价格优势说服力不足\n"
        "4. 团队商业化能力薄弱\n"
    ),
    "pitch_archive/round2/competition_plan_notes.txt": (
        "计划参加：\n"
        "- 全国挑战杯（2024年6月提交）\n"
        "- 某创投机构Demo Day（2024年9月）\n"
        "当前准备状态：材料散乱，无完整路演逻辑\n"
    ),
}

for rel_path, content in distractors.items():
    fpath = WORKSPACE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")


# ── THE CORE PROBLEM FILE: messy, unstructured project brief ──────────────────
# This is the raw input the agent must process.

project_brief = """\
项目名称：LightSense（暂定）

来源：清华大学光子与微纳电子学研究所，张伟教授课题组。技术基础是2019年以来
在集成光子芯片上实现的固态LiDAR扫描方案，已有实验室原型，核心创新点是把
传统机械旋转部件完全集成在硅光芯片上，体积缩小90%、理论成本可降低60%。

团队现状：
- 张伟教授（导师，技术总负责，持有核心专利，兼职参与，不出任CEO）
- 李梦楠（在读博士四年级，全职，承担所有对外沟通和产品化，角色未正式定义）
- 陈睿（MBA，汽车行业背景，兼职，2024年3月才加入，和教授之间沟通不顺畅）
- 缺：全职CEO、市场/销售、量产工程师

当前进展：
- 实验室原型完成，精度指标在v1已验证，v2仍在仿真阶段
- 申请了2项专利（1项受理、1项PCT国际审查中）
- 参加过挑战杯省赛，评委说商业模式不清楚
- 没有付费客户，没有正式的PoC合作
- 接触过3家自动驾驶公司（L4级别整车厂），都没有推进
- 没有做过系统性的用户访谈
- 资金快撑不住了（runway约4-5个月）

目标客户的困惑：
团队最初锁定"所有自动驾驶整车厂"，但评委说太宽泛。
内部讨论过工业机器人、无人机、港口自动化等方向，没有结论。
陈睿认为应该先做汽车Tier1供应商，教授认为应该直接和整车厂谈，
李梦楠倾向于先找小场景验证（比如AGV或仓储机器人）。

核心困难（团队自述）：
1. 不知道先做哪个市场
2. 不知道怎么把技术语言变成客户能理解的价值主张
3. 教授和学生之间权责不清，决策经常卡壳
4. 参加全国挑战杯（2024年6月）路演材料一团糟，不知道怎么重构

希望获得：
1. 一份针对我们项目的诊断+路线图报告
2. 帮我们把路演材料重构成一个逻辑清晰的框架（不用写完整PPT，给出结构和核心论点就行）
"""

(WORKSPACE / "project_docs" / "raw_project_brief.txt").write_text(
    project_brief, encoding="utf-8"
)

# ── Instruction file for agent ──────────────────────────────────────────────
# This file states the task without leaking methodology.

task_instruction = """\
任务说明（请仔细阅读）

你是一位受委托的创业方法论顾问。你的客户是一支来自清华大学的硬科技创业团队，
他们的项目信息保存在 project_docs/raw_project_brief.txt。

请完成以下两项交付：

1. 生成一份项目诊断与路线图报告，保存为 diagnosis_roadmap.md
2. 生成一份路演重构框架文档，保存为 pitch_reconstruction.md

两份文档都应直接保存在 /workspace 目录下。
"""

(WORKSPACE / "task_instruction.txt").write_text(task_instruction, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Files created: {len(list(WORKSPACE.rglob('*')))} items")