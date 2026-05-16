import os
import random
import json

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a deeply nested distractor directory structure
structure = {
    "hr_department": {
        "recruitment": {
            "2023": {
                "finance_dept": {
                    "jd_finance_manager.txt": "Finance Manager - 5+ years experience in budgeting and financing. Real estate background preferred.",
                    "shortlist_candidates.csv": "Name,Score,Status\nZhang Wei,85,Pending\nLi Ming,78,Pending\nWang Fang,91,Pending",
                    "interview_schedule_q3.txt": "Interviews scheduled: Monday 9am, Tuesday 2pm, Wednesday 10am",
                },
                "notes_raw.txt": "Need structured questions for finance manager role - real estate industry context important",
            },
            "templates": {
                "old_interview_form_v1.docx.txt": "Legacy template - DO NOT USE - replaced by new system",
                "generic_hr_questions.txt": "1. Tell me about yourself.\n2. What are your strengths?\n3. Where do you see yourself in 5 years?",
                "competency_framework_draft.txt": "Draft competency framework - not finalized\nBudget Management\nFinancing Planning\nRisk Control\nTeam Leadership",
            },
        },
        "training": {
            "interviewer_guide_2022.txt": "Old guide for interviewers - outdated format",
            "bias_avoidance_checklist.txt": "Checklist: Avoid leading questions, ensure consistency across candidates",
        },
    },
    "finance_dept": {
        "budget": {
            "2024_budget_draft.xlsx.txt": "Q1: 5M, Q2: 6M, Q3: 5.5M, Q4: 7M",
            "variance_report_jun.txt": "June variance: -3.2% vs budget",
        },
        "financing": {
            "bond_issuance_record.txt": "2023 Bond: 500M CNY, 5-year term, 3.8% coupon",
            "bank_credit_lines.txt": "Industrial Bank: 200M, China Merchants: 150M",
        },
        "internal_policies": {
            "treasury_policy_v3.txt": "Cash concentration policy, intercompany lending rules",
            "budget_approval_workflow.txt": "Budget approval: Dept Head -> CFO -> Board",
        },
    },
    "legal": {
        "contracts": {
            "template_nda.txt": "Non-disclosure agreement template",
            "employment_contract_standard.txt": "Standard employment contract clauses",
        }
    },
    "it_systems": {
        "erp_config_notes.txt": "SAP FICO module configuration notes",
        "data_access_request_form.txt": "Form for requesting financial system access",
    },
}

def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

create_structure(workspace, structure)

# Create the main task briefing file (messy, informal HR note)
task_brief = """
HR招聘需求 - 内部备忘录
日期: 2024年7月15日
发件人: 人力资源部 王主任
收件人: 招聘团队

事项：财务经理岗位面试准备

我们房地产集团正在招聘一名财务经理（Finance Manager），这个人将主要负责
集团旗下项目的预算管控和融资统筹工作。

面试对象定位：有5-8年经验的中层骨干，不是高管级别，也不是刚毕业的新人。

重点考察两个能力方向：
1. 预算管理方面的实际操练经验
2. 融资筹划的实务能力

请帮我出一套结构化的面试问题，用于本周三的面试官培训。
面试官是第一次做结构化面试，所以问题要规范、专业。

输出文件请命名为 interview_questions.md

谢谢！
"""

with open(os.path.join(workspace, "hr_department", "recruitment", "2023", "finance_dept", "task_brief.txt"), 'w', encoding='utf-8') as f:
    f.write(task_brief)

# Create a red-herring "example" file with WRONG format to mislead the agent
wrong_example = """
示例面试问题（非正式版）：
Q1: 你有没有做过预算？
Q2: 你了解融资吗？
Q3: 你怎么处理压力？

注意：这个版本格式不规范，仅供参考，不要直接使用
"""

with open(os.path.join(workspace, "hr_department", "recruitment", "templates", "bad_example_donotuse.txt"), 'w', encoding='utf-8') as f:
    f.write(wrong_example)

print("Workspace created successfully.")
print(f"Files created in {workspace}")