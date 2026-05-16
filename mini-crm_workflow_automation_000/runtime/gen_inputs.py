import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Create realistic distractor directory structure ---
dirs = [
    "archive/2025_q4",
    "archive/2026_q1",
    "internal/templates",
    "internal/contracts",
    "finance/invoices",
    "finance/reports",
    "marketing/campaigns",
    "marketing/assets",
    "tech/projects",
    "tech/proposals",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
(workspace / "archive/2025_q4/q4_summary.txt").write_text(
    "Q4 2025 总结: 共完成12个项目，总收入¥420,000\n存档日期: 2026-01-05"
)
(workspace / "archive/2025_q4/old_clients.csv").write_text(
    "name,contact,value\n旧客户A,13800000001,25000\n旧客户B,13900000002,18000"
)
(workspace / "archive/2026_q1/jan_notes.txt").write_text(
    "一月份备忘: 联系了几个老客户，需要跟进网站维护合同续签"
)
(workspace / "internal/templates/contract_template.txt").write_text(
    "合同模板 v3.2\n甲方: ___\n乙方: 本工作室\n服务内容: ___\n金额: ___"
)
(workspace / "internal/contracts/contract_C001_signed.txt").write_text(
    "合同编号: CNT-2026-001\n客户: 赵总\n金额: ¥35,000\n签署日期: 2026-03-08"
)
(workspace / "finance/invoices/inv_march.txt").write_text(
    "发票记录 - 2026年3月\nINV-001: 赵总 ¥35,000 (已开票)\nINV-002: 钱经理 ¥28,000 (已开票)\nINV-003: 孙先生 ¥18,000 (未开票)"
)
(workspace / "finance/reports/cashflow_feb.json").write_text(json.dumps({
    "month": "2026-02",
    "income": 72000,
    "expenses": 12000,
    "net": 60000
}, ensure_ascii=False, indent=2))
(workspace / "marketing/campaigns/juejin_promo.txt").write_text(
    "掘金平台推广计划\n预算: ¥2,000/月\n目标: 每月带来8-10个咨询\n效果评估: 转化率约10%"
)
(workspace / "marketing/assets/service_list.txt").write_text(
    "服务目录:\n1. 网站开发: ¥20,000 - ¥60,000\n2. 小程序开发: ¥15,000 - ¥40,000\n3. APP开发: ¥30,000 - ¥80,000\n4. SEO优化: ¥3,000 - ¥8,000/月"
)
(workspace / "tech/projects/active_projects.txt").write_text(
    "进行中项目:\n- 赵总官网 (进行中, 预计完成2026-04-15)\n- 李经理小程序 (设计阶段)\n- 新项目: 待确认需求"
)
(workspace / "tech/proposals/proposal_template.md").write_text(
    "# 项目方案模板\n\n## 需求分析\n## 技术方案\n## 报价\n## 时间计划\n"
)

# --- The REAL messy input: raw sales notes from the team ---
# This is the primary data the agent must process
# Intentionally messy, inconsistent formatting, mixed Chinese/English

raw_sales_notes = """
=== 客户跟进记录 - 2026年3月 ===
导出时间: 2026-03-15
负责人: 小王

--- 客户1 ---
姓名: 张总
公司: ABC科技有限公司
微信: zhang123
邮箱: zhang@abc.com
预算: 5万
来源: 掘金文章
状态: 洽谈中
首次联系: 2026-03-01 - 询问网站开发服务
跟进1: 2026-03-05 - 发送报价¥35,000
最后联系: 2026-03-10
备注: 客户对价格有些犹豫，需要再跟进

--- 客户2 ---
姓名: 李经理
公司: 顺达贸易公司
微信: li_mgr_88
邮箱: li@shunda.com
预算: 3万
来源: 知乎
状态: 洽谈中
首次联系: 2026-03-03 - 咨询小程序开发
跟进1: 2026-03-07 - 详细了解需求
跟进2: 2026-03-13 - 发送详细方案
最后联系: 2026-03-13
备注: 意向较强，方案已确认，等待审批

--- 客户3 ---
姓名: 王先生
公司: 王氏餐饮管理
微信: wangxs_catering
邮箱: wang@wangcatering.cn
预算: ¥15000
来源: 朋友推荐
状态: 洽谈中
首次联系: 2026-03-08 - 点餐小程序咨询
跟进1: 2026-03-14 - 发送报价¥12,000
最后联系: 2026-03-14
备注: 预算有限，提供了简化版方案

--- 客户4 ---
姓名: 赵总
公司: 赵氏地产
微信: zhao_boss
邮箱: zhao@zhaorealty.com
预算: 4万
来源: 掘金文章
状态: 已成交
首次联系: 2026-02-20 - 官网重建咨询
跟进1: 2026-02-25 - 发送报价
跟进2: 2026-03-01 - 客户确认方案
成交日期: 2026-03-08
成交金额: ¥35,000
服务内容: 网站开发
回款情况: 已回款¥25,000，待收¥10,000
最后联系: 2026-03-08

--- 客户5 ---
姓名: 钱经理
公司: 钱记连锁超市
微信: qian_supermarket
邮箱: qian@qianjichains.com
预算: 3万
来源: 掘金文章
状态: 已成交
首次联系: 2026-02-28 - 收银小程序询价
跟进1: 2026-03-04 - 发送报价¥28,000
跟进2: 2026-03-06 - 客户接受报价
成交日期: 2026-03-10
成交金额: ¥28,000
服务内容: 小程序
回款情况: 已回款¥28,000，待收¥0
最后联系: 2026-03-10

--- 客户6 ---
姓名: 孙先生
公司: 孙博士学习平台
微信: sun_edutech
邮箱: sun@sundoctor.net
预算: 2万
来源: 知乎
状态: 已成交
首次联系: 2026-03-02 - APP开发咨询
跟进1: 2026-03-06 - 发送报价¥18,000
成交日期: 2026-03-12
成交金额: ¥18,000
服务内容: APP开发
回款情况: 已回款¥12,000，待收¥6,000
最后联系: 2026-03-12

--- 客户7 ---
姓名: 周女士
公司: 周记烘焙坊
微信: zhou_bakery
邮箱: zhou@zhoubakery.com
预算: ¥8000
来源: 朋友推荐
状态: 已流失
首次联系: 2026-03-01 - 网站建设咨询
跟进1: 2026-03-03 - 发送报价¥9,000
最后联系: 2026-03-05
备注: 预算不足，选择了其他供应商

--- 客户8 ---
姓名: 吴总
公司: 吴氏物流科技
微信: wu_logistics
邮箱: wu@wulogistics.com.cn
预算: 10万
来源: 掘金文章
状态: 洽谈中
首次联系: 2026-03-10 - 物流管理系统咨询
跟进1: 2026-03-12 - 初步了解需求，提供方案思路
最后联系: 2026-03-12
备注: 大客户，需要重点跟进，下周安排现场拜访

--- 客户9 ---
姓名: 郑经理
公司: 郑华教育集团
微信: zheng_edu
邮箱: zheng@zhenghuaedu.com
预算: 6万
来源: 掘金文章
状态: 首次咨询
首次联系: 2026-03-14 - 在线教育平台咨询
最后联系: 2026-03-14
备注: 刚接触，需要准备详细方案

--- 客户10 ---
姓名: 陈小姐
公司: 陈记美发连锁
微信: chen_salon
邮箱: chen@chensalon.cn
预算: ¥12000
来源: 知乎
状态: 首次咨询
首次联系: 2026-03-15 - 预约管理小程序咨询
最后联系: 2026-03-15
备注: 今天刚来询问，需要跟进了解需求
"""

(workspace / "raw_sales_notes_march2026.txt").write_text(raw_sales_notes, encoding="utf-8")

# Additional messy data: a partial old JSON that is WRONG format (to confuse agents)
old_broken_json = {
    "client_list": [  # Wrong key name - should be "customers"
        {
            "client_id": "OLD001",  # Wrong field name
            "full_name": "历史客户甲",  # Wrong field name
            "budget_amount": 20000,  # Wrong field name
            "current_status": "closed"
        }
    ],
    "export_date": "2025-12-31"
}
(workspace / "archive/2025_q4/old_crm_export.json").write_text(
    json.dumps(old_broken_json, ensure_ascii=False, indent=2)
)

# A confusing "template" that has wrong output format to trap agents
(workspace / "internal/templates/report_template_WRONG.txt").write_text("""
CUSTOMER DASHBOARD REPORT
==========================
Total Customers: {total}
Active Deals: {active}
Closed Deals: {closed}
Lost: {lost}

Top Priority Follow-ups:
{followups}

Monthly Revenue: {revenue}
""")

# Finance crosscheck data
(workspace / "finance/reports/march_payments.txt").write_text(
    "2026年3月回款记录:\n赵氏地产 - ¥25,000 (2026-03-10)\n钱记连锁超市 - ¥28,000 (2026-03-10)\n孙博士学习平台 - ¥12,000 (2026-03-14)\n合计: ¥65,000"
)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")