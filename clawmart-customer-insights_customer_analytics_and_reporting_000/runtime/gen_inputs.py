import os
import json
import random
import csv
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "raw_data/wechat",
    "raw_data/email",
    "raw_data/crm",
    "raw_data/archive",
    "raw_data/temp",
    "config",
    "scripts",
    "logs",
    "reports/drafts",
    "reports/archive",
    "docs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
(workspace / "config" / "app_config.yaml").write_text(
    "app:\n  name: InsightsPlatform\n  version: 2.1.0\n  locale: zh-CN\ndatabase:\n  host: localhost\n  port: 5432\n"
)
(workspace / "config" / "sources.json").write_text(
    json.dumps({
        "sources": {"wechat": "微信聊天记录", "email": "邮件往来", "crm": "CRM 系统（可选）"}
    }, ensure_ascii=False, indent=2)
)
(workspace / "scripts" / "sync_crm.py").write_text(
    "# CRM sync utility\nimport requests\ndef sync(): pass\n"
)
(workspace / "scripts" / "export_wechat.sh").write_text(
    "#!/bin/bash\necho 'Exporting WeChat logs...'\n"
)
(workspace / "logs" / "system.log").write_text(
    "2026-03-10 08:00:01 INFO  System started\n2026-03-10 08:01:00 INFO  Data sync completed\n"
)
(workspace / "logs" / "errors.log").write_text(
    "2026-03-09 22:15:33 ERROR CRM connection timeout\n"
)
(workspace / "reports" / "drafts" / "draft_q1.txt").write_text(
    "Q1 Draft report - incomplete\nTBD\n"
)
(workspace / "reports" / "archive" / "2025_annual.md").write_text(
    "# 2025 Annual Report\nArchived.\n"
)
(workspace / "docs" / "onboarding.md").write_text(
    "# Onboarding Guide\nWelcome to the InsightsPlatform.\n"
)
(workspace / "raw_data" / "archive" / "2025_customers.csv").write_text(
    "id,name,value\n1,Old Customer A,50000\n2,Old Customer B,20000\n"
)
(workspace / "raw_data" / "temp" / "import_staging.json").write_text(
    json.dumps({"status": "pending", "records": []}, ensure_ascii=False)
)

# ── WeChat logs (messy, mixed Chinese/English, inconsistent dates) ─────────────
wechat_data = [
    {
        "file": "wechat_zhang_zong.txt",
        "content": """[微信聊天记录 - 张总]
2026/01/05 10:23 张总: 你好，我们公司对你们的企业版很感兴趣
2026/01/05 10:25 我方: 非常感谢！请问贵公司规模大概是多少人？
2026/01/05 10:30 张总: 500人左右，IT部门约50人
2026/01/06 09:15 我方: 给您发了产品介绍，请查收
2026/01/15 14:00 张总: 已收到，我们决定购买，合同金额120000元
2026/01/20 16:00 张总: 合同已签，款项已付，非常满意
2026/02/10 11:00 张总: 想再追加购买模块B，预算30000
2026/02/15 10:00 张总: 已付款，继续合作愉快
2026/03/01 10:00 张总: 请问有新产品吗？我们有新需求
购买记录: 2次, 累计¥150,000
最后联系: 2026-03-01
"""
    },
    {
        "file": "wechat_li_jingli.txt",
        "content": """[微信聊天记录 - 李经理]
2026-01-10 09:00 李经理: 你好，朋友推荐你们的
2026-01-10 09:05 我方: 您好！请问有什么可以帮到您？
2026-01-12 14:30 李经理: 我们需要CRM集成方案
2026-01-20 10:00 李经理: 好的我们决定合作，金额85000
2026-02-01 11:00 李经理: 第一次付款完成
2026-02-20 15:00 李经理: 追加服务，再付了一笔
2026-03-05 09:00 李经理: 问一下新功能上线了吗？
购买次数: 3次, 累计金额: ¥85,000 (含追加)
最后联系: 2026-03-05
"""
    },
    {
        "file": "wechat_wang_xiansheng.txt",
        "content": """[微信聊天记录 - 王先生]
2026/02/01 10:00 王先生: 你好，我想了解一下你们的产品
2026/02/01 10:10 我方: 您好，欢迎！
2026/02/05 14:00 王先生: 我们预算50000，能满足我们需求吗？
2026/02/10 11:00 王先生: 方案看了，很不错
2026/02/20 16:00 王先生: 还在考虑中，再给我一些案例
2026/03/08 09:00 王先生: 案例收到了，下周我们开会讨论
咨询次数: 3次
预算: ¥50,000
最后联系: 2026-03-08
状态: 未成交，高意向
"""
    },
    {
        "file": "wechat_zhao_nvshi.txt",
        "content": """[微信聊天记录 - 赵女士]
2026/02/15 10:00 赵女士: 你们有小企业版本吗
2026/02/15 10:05 我方: 有的，请问贵公司多少人？
2026/02/16 14:00 赵女士: 我们20人，预算30000
2026/02/25 11:00 赵女士: 正在申请预算审批
咨询次数: 2次
预算: ¥30,000
最后联系: 2026-02-25
状态: 未成交，意向较高
"""
    },
    {
        "file": "wechat_chen_laoshi.txt",
        "content": """[WeChat Log - 陈老师]
Jan 03 2026 10:00 陈老师: 你好
Jan 03 2026 10:05 我方: 您好，有什么可以帮您？
(no further messages)
最后联系: 2026-01-03
状态: 无后续
"""
    },
    {
        "file": "wechat_liu_zong.txt",
        "content": """[微信聊天记录 - 刘总]
2025/11/01 09:00 刘总: 有兴趣了解
2025/11/05 10:00 刘总: 好的我看看
(长期无回复)
最后联系: 2025-11-05
距今: 4个月以上未联系
"""
    },
    {
        "file": "wechat_sun_jingli.txt",
        "content": """[微信聊天记录 - 孙经理]
2025/10/10 14:00 孙经理: 你们产品如何收费
2025/10/10 14:30 我方: 按模块收费...
2025/10/11 09:00 孙经理: 好的谢谢
(无后续)
最后联系: 2025-10-11
距今: 5个月以上
"""
    },
]
for item in wechat_data:
    (workspace / "raw_data" / "wechat" / item["file"]).write_text(item["content"], encoding="utf-8")

# ── Email records ─────────────────────────────────────────────────────────────
email_data = [
    {
        "file": "emails_wang_xiansheng.txt",
        "content": """From: wang.jun@techcorp.com
Date: 2026-02-01
Subject: 产品咨询

您好，我们公司正在评估CRM工具，预算50000元以内，请发送详细资料。

---
From: sales@ourcompany.com  
Date: 2026-02-02
Subject: RE: 产品咨询

已发送完整方案，期待您的反馈。

---
From: wang.jun@techcorp.com
Date: 2026-02-10
Subject: RE: 产品咨询

方案收到，很感兴趣，下周安排演示？

---
From: wang.jun@techcorp.com
Date: 2026-03-08
Subject: 跟进

开会讨论了，有几个问题想电话沟通，方便吗？
"""
    },
    {
        "file": "emails_zhou_总.txt",
        "content": """From: zhou.ming@startup.io
Date: 2026-03-01
Subject: 价格咨询

你好，朋友推荐，想了解定价。

---
From: sales@ourcompany.com
Date: 2026-03-02  
Subject: RE: 价格咨询

已回复定价方案。
"""
    },
    {
        "file": "emails_wu_manager.txt",
        "content": """From: wu.li@enterprise.com
Date: 2025-09-15
Subject: Initial inquiry

Hello, we are looking for a solution.

(no further correspondence)
最后联系: 2025-09-15
"""
    },
]
for item in email_data:
    (workspace / "raw_data" / "email" / item["file"]).write_text(item["content"], encoding="utf-8")

# ── CRM data (CSV, messy with inconsistencies) ────────────────────────────────
crm_rows = [
    ["客户ID", "姓名", "公司", "联系方式", "累计金额(元)", "购买次数", "最后联系日期", "状态", "备注"],
    ["C001", "张总", "大华集团", "138xxxx0001", "150000", "2", "2026-03-01", "VIP", "企业版+模块B，高满意度"],
    ["C002", "李经理", "联创科技", "139xxxx0002", "85000", "3", "2026-03-05", "VIP", "多次复购"],
    ["C003", "王先生", "新兴互联", "136xxxx0003", "0", "0", "2026-03-08", "潜在", "预算50000，高意向，咨询3次"],
    ["C004", "赵女士", "微创工坊", "137xxxx0004", "0", "0", "2026-02-25", "潜在", "预算30000，咨询2次"],
    ["C005", "陈老师", "教培中心", "135xxxx0005", "0", "0", "2026-01-03", "冷淡", "单次咨询无跟进"],
    ["C006", "刘总", "旧城贸易", "133xxxx0006", "0", "0", "2025-11-05", "流失风险", "4月以上未联系"],
    ["C007", "孙经理", "南方制造", "132xxxx0007", "0", "0", "2025-10-11", "流失风险", "5月以上未联系"],
    ["C008", "周总", "创业工场", "131xxxx0008", "0", "0", "2026-03-01", "普通", "初次咨询定价"],
    ["C009", "吴经理", "东方企业", "130xxxx0009", "0", "0", "2025-09-15", "流失风险", "6月以上未联系"],
    ["C010", "郑主任", "市政单位", "139xxxx0010", "20000", "1", "2026-01-20", "普通", "单次购买，无复购"],
    ["C011", "冯总", "高新区A公司", "138xxxx0011", "0", "0", "2026-02-01", "普通", "初步了解，无明确预算"],
    ["C012", "蒋先生", "远景科技", "137xxxx0012", "15000", "1", "2026-02-10", "普通", "小额采购"],
]
crm_path = workspace / "raw_data" / "crm" / "customers_export_2026Q1.csv"
with open(crm_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(crm_rows)

# ── Interaction timing log (raw, unanalyzed) ──────────────────────────────────
timing_raw = """# 客户响应时间记录 (原始数据, 未分析)
# 格式: 日期,时间,客户,是否回复(1=是,0=否),星期
2026-01-05,10:23,张总,1,周一
2026-01-06,09:15,张总,1,周二
2026-01-10,09:00,李经理,1,周六
2026-01-12,14:30,李经理,1,周一
2026-02-01,10:00,王先生,1,周日
2026-02-05,14:00,王先生,1,周四
2026-02-10,11:00,王先生,1,周二
2026-02-15,10:00,赵女士,1,周日
2026-02-16,14:00,赵女士,1,周一
2026-02-20,16:00,王先生,1,周五
2026-02-25,11:00,赵女士,1,周三
2026-03-01,10:00,张总,1,周日
2026-03-05,09:00,李经理,1,周四
2026-03-08,09:00,王先生,1,周日
2026-01-03,10:00,陈老师,1,周六
2026-01-20,16:00,郑主任,1,周二
2026-02-01,10:00,冯总,0,周日
2026-02-10,10:00,蒋先生,1,周二
2026-03-01,10:00,周总,1,周日
# 统计区间: 2026-01-01 to 2026-03-10
# 注: 上午10-11点, 下午15-16点, 晚上20-21点回复率最高
# 周二最高52%, 周四48%, 周一周五较低35%
"""
(workspace / "raw_data" / "timing_interactions.txt").write_text(timing_raw, encoding="utf-8")

# ── A misleading partial report (wrong format, to trap the agent) ──────────────
(workspace / "reports" / "drafts" / "partial_analysis.txt").write_text(
    """PARTIAL CUSTOMER ANALYSIS
===========================
VIP Customers: Zhang, Li
Hot Leads: Wang, Zhao
Others: Chen, Liu, Sun
NOTE: This file is incomplete and uses the wrong format. Do not submit this.
""",
    encoding="utf-8"
)

print("Workspace initialized successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")