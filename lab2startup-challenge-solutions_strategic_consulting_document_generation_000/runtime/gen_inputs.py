import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor structure
dirs = [
    "archive/2022/q1",
    "archive/2022/q2",
    "archive/2023/reports",
    "archive/2023/internal",
    "team/hr",
    "team/finance",
    "team/tech",
    "projects/alpha",
    "projects/beta",
    "projects/beta/docs",
    "misc",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "archive/2022/q1/budget_draft.txt": "Q1预算草案\n总预算：150万元\n研发：80万\n市场：20万\n运营：50万",
    "archive/2022/q2/meeting_log.txt": "2022年Q2季度会议记录\n参会人：张教授、李明、王芳\n议题：技术路线讨论\n结论：暂缓产品化",
    "archive/2023/reports/annual_summary.txt": "年度总结\n技术进展：完成3项专利申请\n团队规模：8人\n营收：0",
    "archive/2023/internal/ip_register.txt": "知识产权登记\n专利1：柔性传感器制备方法（申请中）\n专利2：信号处理算法（已授权）",
    "team/hr/headcount.txt": "人员统计\n教授：1名\n博士生：3名\n硕士生：2名\n全职工程师：1名\n兼职顾问：1名\n总计：8人",
    "team/finance/cashflow.txt": "现金流状况\n启动资金：200万（学校划拨）\n天使轮：未启动\n月均支出：18万\n预计可用：11个月",
    "team/tech/trl_notes.txt": "内部技术评估备注\n传感器核心模块：已完成实验室原型\n信号处理算法：论文已发表\n系统集成：待完成\n注：以上为非正式评估",
    "projects/alpha/concept.txt": "项目Alpha：运动员疲劳监测\n状态：概念阶段\n潜在客户：体育总局，职业俱乐部",
    "projects/beta/docs/spec_v0.1.txt": "项目Beta技术规格（草稿）\n灵敏度：>95%\n特异性：>90%\n功耗：<50mW\n注：以上为目标值，未验证",
    "misc/random_links.txt": "参考链接（无效）\nhttps://example.com/trl\nhttps://example.com/startup",
    "misc/old_plan.txt": "旧版商业计划（作废）\n请忽略此文件",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE MAIN INPUT: Messy raw interview/situation notes
raw_notes = """
=== 项目情况原始访谈记录 ===
记录人：外部顾问
日期：2024年3月

【背景信息】
项目名称：FlexSense — 柔性可穿戴生化传感器
团队构成：
  - 陈磊教授（PI，材料工程，某985高校）
  - 赵晨（博士毕业，CEO，陈教授学生，负责公司日常运营）
  - 其他成员：2名在读博士（兼职），3名工程师（全职）
成立时间：约15个月前（2023年1月）
融资状态：Pre-A轮，估值洽谈中

【技术状态摘录】
- 核心传感器材料：实验室已完成系统原型，并在小规模现场环境（合作医院病房）完成初步验证测试
- 技术就绪度：团队内部认为"差不多可以卖了"，但工程师反馈量产良率只有约40%
- 成本问题：单个传感器实验室成本约480元，目标市场报价需低于200元才有竞争力
- 赵晨说："教授坚持要把灵敏度做到99%才能出货，但竞争对手的产品83%灵敏度已经在卖了。"

【市场状态摘录】
- 目前已接触约30家潜在客户（医院、运动健康品牌、体检机构）
- 已有2家医院表示"有兴趣试用"，但未付费
- 一家知名运动品牌主动联系，希望联合开发，但谈判停滞了3个月
- 赵晨反映："客户根本不知道柔性传感器能做什么，每次都要从头解释，非常耗时。"
- 目前无付费客户，无收入

【团队冲突摘录】
- 陈教授："产品化是赵晨的事，但我需要对技术方向有最终拍板权。"
- 赵晨："教授总是在我已经和客户谈好的合作上推翻决定，导致我们失去了两个重要客户。"
- 冲突记录：过去6个月，因决策权争议导致3次重要合作机会延误
- 团队有微信群日常沟通，但没有固定的周会或月会机制
- 工程师小组反映：不清楚公司战略方向，经常收到相互矛盾的指令

【财务状态】
- 累计融资：学校科研经费150万 + 政府补贴50万
- 月均支出：约25万
- 距离Pre-A交割：预计3-4个月
- 注：投资方明确要求"Pre-A前必须有付费客户"

【其他信息】
- 团队规模：目前7人（未超过20人）
- 已申请专利：3项（2项在审，1项授权）
"""

with open(os.path.join(workspace, "raw_interview_notes.txt"), "w", encoding="utf-8") as f:
    f.write(raw_notes)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1} total")