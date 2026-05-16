#!/usr/bin/env python3
import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ─── Deep directory structure with distractor files ───────────────────────────

dirs = [
    "hr_system/raw_data/boss_zhipin",
    "hr_system/raw_data/liepin",
    "hr_system/raw_data/lagou",
    "hr_system/processed",
    "hr_system/archives/2025",
    "hr_system/archives/2024",
    "hr_system/templates",
    "hr_system/reports/weekly",
    "hr_system/reports/monthly",
    "company_docs/jd",
    "company_docs/hr_policy",
    "tools/scripts",
    "tools/configs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "hr_system/templates/old_jd_template.txt": "Java Developer JD - 5 years experience required...\nSkills: Spring Boot, MySQL, Redis\nSalary: 15K-25K",
    "hr_system/archives/2025/q1_summary.txt": "Q1 2025 Summary: Hired 3 engineers, rejected 12 candidates.",
    "hr_system/archives/2024/annual_report.txt": "Annual Report 2024: Total headcount grew by 15%.",
    "hr_system/reports/weekly/week10_report.txt": "Week 10: Reviewed 20 resumes, scheduled 5 interviews.",
    "hr_system/reports/monthly/march_kpi.txt": "March KPI: Time-to-hire target 30 days.",
    "company_docs/jd/java_senior.md": "# Senior Java Engineer\nRequirements: 5+ years Java, Spring Cloud, microservices architecture",
    "company_docs/jd/frontend_react.md": "# Senior Frontend Engineer\nRequirements: 3+ years React, TypeScript",
    "company_docs/hr_policy/leave_policy.pdf.txt": "[Binary PDF placeholder - leave policy document]",
    "company_docs/hr_policy/recruitment_sop.txt": "Recruitment SOP v2.1: Screen -> Phone -> Technical -> HR -> Offer",
    "tools/scripts/export_csv.sh": "#!/bin/bash\necho 'Exporting candidate data to CSV...'",
    "tools/configs/db_config.yml": "database:\n  host: localhost\n  port: 5432\n  name: hr_db",
    "hr_system/processed/PLACEHOLDER_DO_NOT_DELETE.txt": "This directory is for processed output files.",
}
for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w", encoding="utf-8") as f:
        f.write(content)

# ─── PROBLEM INPUT FILES ──────────────────────────────────────────────────────

# File 1: Boss Zhipin raw dump (messy CSV with inconsistent formatting)
boss_data = """候选人姓名,职位,申请时间,当前进度,备注,联系方式
张伟,高级Java开发工程师,2026-04-01,初步筛选通过,Spring Boot 4年 MySQL Redis经验丰富 薪资期望18K,zhangwei@email.com
陈静,前端工程师,2026-03-28,已安排一面(2026-04-03),React TypeScript 3年经验 上家是互联网大厂,chenjing@email.com
刘洋,Java开发工程师,2026-03-20,二面已完成(2026-04-01) 等待三面,架构设计能力强 7年经验 期望25K,liuyang@email.com
赵磊,高级Java开发工程师,2026-03-10,已发offer(22K) 候选人3天前已看到未回复,5年架构经验 强烈推荐,zhaolei@email.com
孙芳,前端工程师,2026-03-05,初筛,React Vue都熟悉 2年经验,sunfang@email.com
"""

with open(os.path.join(workspace, "hr_system/raw_data/boss_zhipin/april_batch.csv"), "w", encoding="utf-8") as f:
    f.write(boss_data)

# File 2: Liepin raw dump (different messy format - plain text notes)
liepin_data = """【猎聘渠道候选人记录 - 2026年4月】

候选人: 王强
职位: 架构师
来源: 猎聘
投递日期: 2026-03-15
最后跟进: 2026-03-18 (距今已超过18天未联系)
进度: 初筛通过，等待安排面试
技能: Java/Go双修，分布式系统，10年经验
薪资期望: 40K
HR备注: 高价值候选人，务必尽快跟进！

---

候选人: 李梅
职位: Java开发工程师
来源: 猎聘
投递日期: 2026-03-30
最后跟进: 2026-04-02
进度: 一面已通过（技术面）
技能: Spring Cloud 微服务 5年经验 阿里系背景
薪资期望: 22K
HR备注: 表现优秀，建议尽快安排二面

---

候选人: 吴浩
职位: 前端工程师
来源: 猎聘
投递日期: 2026-02-10
最后跟进: 2026-02-12
进度: 简历投递
技能: React 1年经验 应届生
薪资期望: 8K
HR备注: 经验不足，建议放入人才库观察
"""

with open(os.path.join(workspace, "hr_system/raw_data/liepin/march_april.txt"), "w", encoding="utf-8") as f:
    f.write(liepin_data)

# File 3: Lagou channel - JSON but with wrong/incomplete fields
lagou_data = {
    "channel": "拉勾网",
    "export_date": "2026-04-05",
    "candidates": [
        {
            "full_name": "周建国",
            "apply_position": "DevOps工程师",
            "apply_date": "2026-04-02",
            "interview_status": "offer_accepted",  # wrong format - needs mapping
            "skills_raw": "Docker Kubernetes CI/CD Jenkins 4年",
            "expected_salary": "20K",
            "recruiter_note": "已接受offer，预计4月20日入职",
            "last_updated": "2026-04-04"
        },
        {
            "full_name": "郑云",
            "apply_position": "Java开发工程师",
            "apply_date": "2026-04-01",
            "interview_status": "screening",
            "skills_raw": "Spring Boot MyBatis 2年经验",
            "expected_salary": "12K",
            "recruiter_note": "简历还不错，待初筛",
            "last_updated": "2026-04-01"
        }
    ]
}

with open(os.path.join(workspace, "hr_system/raw_data/lagou/lagou_export.json"), "w", encoding="utf-8") as f:
    json.dump(lagou_data, f, ensure_ascii=False, indent=2)

# File 4: Operations instruction file - what the agent must do
operations_instruction = """# 候选人追踪系统 - 操作指令

## 今日日期: 2026-04-05

## 操作要求:

### 操作1: 添加/导入所有候选人
将以下渠道的所有候选人导入系统:
- Boss直聘批次 (april_batch.csv)
- 猎聘渠道记录 (march_april.txt)
- 拉勾网导出 (lagou_export.json)

### 操作2: 状态映射规则
请将原始状态映射到系统标准状态:
- "初步筛选通过" / "初筛" / "简历投递" / "待初筛" / "screening" → 初筛
- "一面" / "二面" / "三面" / "面试中" → 面试
- "已发offer" / "offer谈判" / "offer_accepted" → 根据实际情况判断 (接受→入职, 发出未确认→Offer)
- "人才库" / 经验不足建议储备 → 人才库

### 操作3: 生成提醒
- 为所有超过7天未跟进的候选人生成高优先级提醒
- 为Offer已发出超过3天未确认的候选人生成提醒
- 为面试通过但超过5天未安排下一轮的候选人生成中优先级提醒

### 操作4: 生成标签
根据每位候选人的技能、经验年限、薪资期望自动生成标签

### 操作5: 输出
生成完整的候选人追踪报告，包含:
- 完整JSON数据 (保存为: candidate_tracking_report.json)
- Markdown格式看板 (保存为: candidate_dashboard.md)
"""

with open(os.path.join(workspace, "hr_system/operations_instruction.md"), "w", encoding="utf-8") as f:
    f.write(operations_instruction)

# Reference date context file
with open(os.path.join(workspace, "hr_system/context.txt"), "w", encoding="utf-8") as f:
    f.write("Current date for this exercise: 2026-04-05\nAll date calculations should use this as today's date.\n")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")