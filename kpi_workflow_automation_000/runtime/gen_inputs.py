import os
import random
import json
from pathlib import Path

random.seed(42)

# --- Create a realistic, deeply nested distractor workspace ---
workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Distractor directory structure simulating a real SaaS team workspace
dirs = [
    "workspace/projects/q2_campaign/assets",
    "workspace/projects/q2_campaign/data",
    "workspace/projects/q2_campaign/reports",
    "workspace/projects/q1_archive/retrospective",
    "workspace/analytics/dashboards",
    "workspace/analytics/raw_exports",
    "workspace/team/onboarding",
    "workspace/team/org_chart",
    "workspace/tools/scripts",
    "workspace/finance/budgets",
]

for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "workspace/projects/q2_campaign/assets/banner_specs.txt": 
        "Banner size: 1200x628\nFormat: PNG\nBrand colors: #FF6B35, #2C3E50",
    
    "workspace/projects/q2_campaign/data/ad_spend_raw.csv":
        "date,channel,spend_usd\n2024-04-01,Google,1500\n2024-04-01,LinkedIn,800\n2024-05-15,Google,2200\n2024-06-30,LinkedIn,1100",
    
    "workspace/projects/q2_campaign/data/lead_tracker.csv":
        "week,leads_generated,qualified\nW1,45,12\nW2,62,18\nW3,71,21\nW4,88,25\nW5,55,15\nW6,79,22\nW7,94,28\nW8,103,31\nW9,87,26\nW10,112,33\nW11,98,29\nW12,120,36",
    
    "workspace/projects/q2_campaign/reports/channel_breakdown.json":
        json.dumps({
            "Q2_2024": {
                "organic_search": {"sessions": 18500, "leads": 320},
                "paid_search": {"sessions": 12000, "leads": 215},
                "social_linkedin": {"sessions": 8200, "leads": 178},
                "email": {"sessions": 5400, "leads": 101}
            }
        }, indent=2, ensure_ascii=False),
    
    "workspace/projects/q1_archive/retrospective/q1_summary.txt":
        "Q1 2024 Summary\nTotal leads: 512\nMQL conversion: 18.2%\nContent pieces published: 14\nWebinar attendees: 230",
    
    "workspace/analytics/dashboards/traffic_config.yaml":
        "dashboard: traffic_overview\nrefresh_interval: 3600\nmetrics:\n  - sessions\n  - bounce_rate\n  - avg_duration",
    
    "workspace/analytics/raw_exports/ga4_export_june.csv":
        "page,sessions,avg_time_sec,bounce_rate\n/blog,8420,145,0.42\n/pricing,3210,89,0.61\n/demo,1890,203,0.28",
    
    "workspace/team/onboarding/new_hire_checklist.md":
        "# New Hire Checklist\n- [ ] Set up accounts\n- [ ] Complete security training\n- [ ] Meet team leads\n- [ ] Review brand guidelines",
    
    "workspace/team/org_chart/marketing_team.txt":
        "Marketing Director: Sarah Chen\nContent Lead: Alex Wong\nGrowth Manager: James Liu\nSEO Specialist: Maria Garcia\nPaid Ads Manager: Tom Baker",
    
    "workspace/tools/scripts/data_pull.py":
        "# Data pull script for analytics\nimport requests\n# TODO: connect to GA4 API\nprint('Data pull placeholder')",
    
    "workspace/finance/budgets/q2_marketing_budget.csv":
        "category,allocated_usd,spent_usd\nContent Creation,15000,14200\nPaid Ads,20000,18750\nEvents,8000,6500\nTools,3000,2980",
}

for fpath, content in distractors.items():
    p = Path(fpath)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# --- THE CORE PROBLEM: A business brief that the agent must process ---
# This is the raw, unstructured input the agent will be given context about
brief = """
Q2 2024 内容营销团队绩效简报
负责人：Alex Wong（内容主管）
周期：2024-Q2（2024-04-01 至 2024-06-30）

【目标与实际结果】

目标1 - 内容发布量
  描述：每月发布高质量博客/深度文章
  目标：季度发布 18 篇
  实际：发布 22 篇（超额完成）
  主要任务：
    - 建立选题库（已完成，2024-04-15）
    - 招募 3 名外部撰稿人（已完成，2024-05-01）
    - 每篇文章完成 SEO 审校（已完成，2024-06-28）
    - 建立内容日历（已完成，2024-04-10）

目标2 - 官网自然流量增长
  描述：通过 SEO 和内容运营提升官网自然搜索流量
  目标：季度末自然流量较 Q1 增长 30%
  实际：增长 41%（显著超出预期）
  主要任务：
    - 完成 50 个关键词布局（已完成，2024-05-20）
    - 优化现有文章的内链结构（已完成，2024-06-15）
    - 与 SEO 专员完成技术审查（已完成，2024-06-01）
    - 建设 10 个外链（完成 7 个，阻塞：资源不足）

目标3 - 线索获取
  描述：内容渠道（博客、白皮书、Webinar）带来的 MQL 数量
  目标：季度 MQL 260 个
  实际：MQL 214 个（未达标）
  主要任务：
    - 举办 2 场 Webinar（完成 1 场，阻塞：演讲者档期问题）
    - 发布 2 份行业白皮书（已完成，2024-06-20）
    - 设计 3 个高转化落地页（已完成，2024-05-30）
    - 运营邮件培育序列（进行中）

目标4 - 内容转化率（内容页面访客→留资）
  描述：内容页面的平均留资转化率
  目标：2.5%
  实际：2.1%
  主要任务：
    - A/B 测试 CTA 按钮（已完成，2024-06-10）
    - 优化表单字段（已完成，2024-05-25）
    - 新增弹窗召唤（未开始，推迟至 Q3）

【周期总结 by Sarah Chen（市场总监）】
整体而言，本季度内容团队在内容产出和自然流量两个硬指标上均超额完成，展现出强劲执行力。
线索目标偏差主因是 Webinar 缺席（少了约 60 个预期 MQL）以及转化率未达预期。
外链建设因内部资源被抽调支援活动策划而受阻。

高杠杆动作：外部撰稿人体系的建立极大提升了产出速度，值得在 Q3 扩大规模。
可复用经验：选题库+内容日历的组合工作流，在内部审批流程中节省了约 40% 的协调时间，适用于任何需要规模化生产内容的团队。
下周期重点：补足 Webinar 短板（预排 3 场），加强转化率专项优化，完成外链建设目标。
"""

brief_path = Path("workspace/projects/q2_campaign/reports/q2_performance_brief.txt")
brief_path.write_text(brief, encoding="utf-8")

# Ensure the openclaw memory dir exists but kpi.md does NOT yet exist
kpi_dir = Path("/root/.openclaw/workspace/memory")
kpi_dir.mkdir(parents=True, exist_ok=True)

kpi_path = kpi_dir / "kpi.md"
if kpi_path.exists():
    kpi_path.unlink()

print("✅ Workspace generated successfully.")
print(f"📁 Distractor files: {len(distractors)}")
print(f"📄 Business brief: {brief_path}")
print(f"🎯 KPI file location: {kpi_path} (does not exist yet — agent must create it)")