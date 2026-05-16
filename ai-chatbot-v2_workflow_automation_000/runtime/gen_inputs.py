import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Create realistic deeply nested distractor directory structure ---
dirs = [
    "crm/legacy/exports/2022",
    "crm/legacy/exports/2023",
    "crm/configs/backup",
    "crm/configs/staging",
    "scripts/maintenance",
    "scripts/analytics",
    "knowledge_base/drafts",
    "knowledge_base/archived",
    "reports/monthly",
    "reports/quarterly",
    "logs/system",
    "logs/chat",
    "deployment/k8s",
    "deployment/docker",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files (irrelevant content) ---
distractor_files = {
    "crm/legacy/exports/2022/customers_dump.csv": "id,name,email\n1,Alice,alice@example.com\n2,Bob,bob@example.com\n",
    "crm/legacy/exports/2023/orders_export.json": json.dumps({"orders": [{"id": "ORD-001", "status": "shipped"}, {"id": "ORD-002", "status": "returned"}]}),
    "crm/configs/backup/settings_v1.yaml": "autoReply: false\ntransferThreshold: 5\n",
    "crm/configs/staging/settings_v2.yaml": "autoReply: true\ntransferThreshold: 2\n",
    "scripts/maintenance/cleanup.sh": "#!/bin/bash\n# Remove old logs older than 30 days\nfind /var/log -mtime +30 -delete\n",
    "scripts/analytics/monthly_report.py": "# Placeholder analytics script\nprint('Report not implemented')\n",
    "knowledge_base/drafts/old_faq_draft.txt": "Q: 设备保修期多长?\nA: 待确认\nQ: 如何联系技术支持?\nA: 待完善\n",
    "knowledge_base/archived/v1_faq.json": json.dumps({"version": "1.0", "entries": [{"q": "过期条目", "a": "已废弃"}]}),
    "reports/monthly/2024_01.txt": "January Report: 120 tickets resolved, 15 escalated\n",
    "reports/quarterly/Q1_2024.txt": "Q1 Summary: avg resolution time 4.2 min\n",
    "logs/system/error.log": "[ERROR] 2024-01-15 03:12:44 - Connection timeout\n[WARN] 2024-01-15 03:13:01 - Retry attempt 1\n",
    "logs/chat/session_archive_2023.log": "session_id=abc123 user=patient_001 duration=300s\nsession_id=def456 user=hospital_admin duration=120s\n",
    "deployment/k8s/service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: customer-service\n",
    "deployment/docker/Dockerfile.prod": "FROM python:3.11-slim\nCOPY . /app\nCMD [\"python\", \"main.py\"]\n",
    "tests/unit/test_intent.py": "def test_intent_detection():\n    assert True  # stub\n",
    "tests/integration/test_chat_flow.py": "def test_full_conversation():\n    pass  # not implemented\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE ACTUAL TASK INPUT: FAQ data file for the medical equipment company ---
# This contains structured FAQ pairs that the agent must add to the knowledge base
faq_data = {
    "company": "MedTech供应商",
    "domain": "医疗设备销售与支持",
    "faqs": [
        {
            "question": "血压计的保修期是多长时间？",
            "answer": "我们的血压计提供2年质保，自购买日起计算，非人为损坏免费维修或更换。"
        },
        {
            "question": "设备出现故障如何申请维修？",
            "answer": "请拨打400-800-1234或通过官网提交维修申请，工程师将在48小时内响应并上门检测。"
        },
        {
            "question": "是否支持医院批量采购优惠？",
            "answer": "支持，医院及诊所批量采购10台以上享受8折优惠，联系sales@medtech.com获取报价。"
        }
    ]
}

with open(os.path.join(workspace, "knowledge_base/drafts/medtech_faq_import.json"), "w", encoding="utf-8") as f:
    json.dump(faq_data, f, ensure_ascii=False, indent=2)

# --- Task instruction file: The business requirement document ---
task_brief = """
# MedTech客服系统初始化任务书

## 背景
我们正在为医疗设备供应商部署智能客服系统。需要完成以下工作：

## 任务要求

### 第一步：导入知识库
从 knowledge_base/drafts/medtech_faq_import.json 文件中读取FAQ条目，
将所有3条FAQ添加到客服系统知识库中。

### 第二步：模拟投诉对话测试
依次发送以下3条消息测试客服系统的投诉处理能力：
1. "你好，我想了解一下血压计的售后政策"
2. "我买的设备一个月就坏了，太差了，我要投诉"  
3. "这个质量太让人失望了，我要求退款"

### 第三步：导出统计报告
将对话结束后的系统统计信息保存到文件 service_stats_report.json 中。

## 注意
- 请确保FAQ已成功添加到系统中
- 对话需按顺序执行
- 统计报告必须包含实际的系统数据
"""

with open(os.path.join(workspace, "TASK_BRIEF.md"), "w", encoding="utf-8") as f:
    f.write(task_brief)

print("Workspace initialized successfully.")
print(f"Created {len(distractor_files)} distractor files in nested directories.")
print("Task input file: knowledge_base/drafts/medtech_faq_import.json")
print("Task brief: TASK_BRIEF.md")