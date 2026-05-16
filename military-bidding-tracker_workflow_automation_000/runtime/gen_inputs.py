import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────
dirs = [
    "procurement/announcements/2026",
    "procurement/announcements/2025",
    "procurement/contracts/active",
    "procurement/contracts/archive",
    "procurement/reports/monthly",
    "procurement/reports/annual",
    "internal/hr/staff",
    "internal/finance/budget",
    "internal/finance/invoices",
    "tools/templates",
    "tools/scripts",
    "logs/system",
    "logs/audit",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────
distractors = {
    "procurement/contracts/active/contract_2025_087.txt": "合同编号：2025-087\n甲方：某军工集团\n金额：¥3,200,000\n签署日期：2025-11-15",
    "procurement/contracts/archive/contract_2024_031.txt": "归档合同，已完结。项目：雷达维护服务采购。",
    "procurement/reports/monthly/2025_12_summary.csv": "month,projects,won,lost\n2025-12,4,2,2",
    "procurement/reports/annual/2025_annual.txt": "年度报告：2025年共参与招投标12项，中标7项，胜率58.3%",
    "internal/hr/staff/team_roster.csv": "姓名,职务,联系方式\n张经理,项目负责人,13811112222\n李经理,项目负责人,13833334444\n王总监,总监,13800000000",
    "internal/finance/budget/2026_q1_budget.txt": "Q1预算分配：\n- 标书采购费：50,000\n- 差旅费：30,000\n- 其他：20,000",
    "internal/finance/invoices/inv_20260115.txt": "发票号：20260115-001\n金额：2,500元\n项目：某系统标书购买",
    "tools/templates/bid_register_template.txt": "项目登记模板（旧版）\n项目名：\n预算：\n开标时间：\n负责人：",
    "tools/scripts/remind.sh": "#!/bin/bash\n# 开标提醒脚本（已弃用）\necho '请检查即将开标的项目'",
    "logs/system/2026_01.log": "[2026-01-15 09:00] system started\n[2026-01-15 09:01] db initialized",
    "logs/audit/access_2026_01.log": "2026-01-15 张经理 登录\n2026-01-16 李经理 登录",
    "procurement/announcements/2025/notice_2025_099.txt": "2025年某采购公告（已过期）",
}
for path, content in distractors.items():
    (workspace / path).write_text(content, encoding="utf-8")

# ── Procurement Announcement 1 (messy, unstructured) ─────────────────
# Project: 某型通信设备维护保障采购项目
# Manager: 张经理
# This one will be WON
announcement_1 = """
军工采购公告

一、采购项目名称：某型通信设备维护保障采购项目

二、采购方（甲方）：华北某军工研究所

三、招标代理机构：北京军采招标代理有限公司

四、预算金额：人民币 128 万元整（¥1,280,000.00）

五、标书购买：
  - 截止时间：2026年3月5日 下午5时整（17:00）
  - 购买地点：北京市朝阳区军采大厦B座301室
  - 标书售价：人民币500元/套（含税）
  - 所需材料：营业执照复印件、授权委托书

六、报名截止：2026年3月8日 17:00
    报名地点：同标书购买地点

七、开标时间：2026年3月20日 上午10时（10:00）
    开标地点：北京市朝阳区军采大厦B座一楼会议室

负责人联系方式：张经理 138-1111-2222

注意：本项目涉及加密通信设备，投标人须具备相关资质证书。
"""
(workspace / "procurement/announcements/2026/notice_2026_comm_equipment.txt").write_text(
    announcement_1, encoding="utf-8"
)

# ── Procurement Announcement 2 (messy, unstructured) ─────────────────
# Project: 军用无人机零部件采购项目
# Manager: 李经理
# This one will be LOST
announcement_2 = """
招标公告

项目：军用无人机零部件采购项目

甲方单位：西南某航空技术研究院

代理机构：成都军工招标服务中心

项目预算：预计 85万元（¥850,000）

标书购买信息：
    时间：2026-03-10 截止，每天上午9:00至下午4:30可购买
    截止日期: 2026年3月10日16:30
    地点：成都市武侯区航天路88号综合楼2楼
    价格：免费领取（需登记）
    报名所需材料：有效营业执照、保密资质证书、法人授权书

报名截止：2026年03月12日 下午16:00

开标：
    时间：2026年3月25日 14时30分
    地址：成都市武侯区航天路88号综合楼3楼开标室

负责人：李经理，联系方式：138-3333-4444

备注：本次采购为紧急采购，投标人须在开标前48小时完成封标寄送。
"""
(workspace / "procurement/announcements/2026/notice_2026_drone_parts.txt").write_text(
    announcement_2, encoding="utf-8"
)

# ── Task instruction file ─────────────────────────────────────────────
task_note = """任务说明（内部流转单）

请处理以下两份新到招标公告（位于 procurement/announcements/2026/），完成全流程跟踪：

1. 通信设备维护保障项目：
   - 负责人：张经理（差旅天数：2天）
   - 最终结果：我方中标，我方报价 125万元，中标价 125万元

2. 无人机零部件项目：
   - 负责人：李经理（差旅天数：3天）
   - 最终结果：我方未中标，我方报价 82万元，中标价 78万元，中标单位"西南飞翔科技有限公司"，备注"报价略高"

完成后，请将按负责人汇总的统计数据保存至工作目录根目录的 manager_stats.json 文件。
"""
(workspace / "task_brief.txt").write_text(task_note, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")