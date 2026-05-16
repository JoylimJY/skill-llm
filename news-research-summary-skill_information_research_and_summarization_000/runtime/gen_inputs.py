import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# Create deeply nested directory structure with distractor files
dirs = [
    "workspace/research/av_industry",
    "workspace/research/policy_archive",
    "workspace/research/competitors",
    "workspace/drafts/old_reports",
    "workspace/drafts/templates_unused",
    "workspace/data/raw_feeds",
    "workspace/data/processed",
    "workspace/logs",
    "workspace/config",
    "workspace/output/pending",
]

for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# Distractor files — messy, irrelevant, or misleading content

Path("workspace/research/av_industry/notes_raw.txt").write_text(
    "Tesla FSD v13 rollout - check with marketing\n"
    "Waymo Phoenix expansion - Bloomberg article from 3 months ago\n"
    "NHTSA recall database - not updated\n"
    "TODO: find Chinese regulator site\n",
    encoding="utf-8"
)

Path("workspace/research/av_industry/av_links_dump.txt").write_text(
    "https://www.miit.gov.cn/\n"
    "https://www.theverge.com/autonomous-cars\n"
    "https://eurlex.europa.eu/\n"
    "https://www.reuters.com/technology/\n"
    "(scraped 2024-01, possibly stale)\n",
    encoding="utf-8"
)

Path("workspace/research/policy_archive/eu_ai_act_summary_2023.md").write_text(
    "# EU AI Act - 2023 Overview\n\n"
    "This is an old summary from 2023. The final text was adopted in 2024.\n"
    "NOT for distribution. Status: outdated.\n",
    encoding="utf-8"
)

Path("workspace/research/policy_archive/china_av_draft_2022.txt").write_text(
    "Draft: Regulations on Intelligent and Connected Vehicles (ICVs) - 2022 consultation draft.\n"
    "Note: superseded. Final status unknown.\n"
    "Contact: policy team for updated version.\n",
    encoding="utf-8"
)

Path("workspace/research/competitors/waymo_q3_2024_notes.txt").write_text(
    "Waymo Q3 2024: robotaxi miles increased. No China presence.\n"
    "Competitor: Baidu Apollo - L4 permit in Beijing.\n"
    "Note: data is 6+ months old, verify before use.\n",
    encoding="utf-8"
)

Path("workspace/drafts/old_reports/av_weekly_2024_11.md").write_text(
    "# AV Weekly - November 2024 (DRAFT - ABANDONED)\n\n"
    "## Summary\nThis draft was never finished. Data unverified.\n\n"
    "- Item 1: Some claim about EU approval\n"
    "- Item 2: China pilot zone expansion\n",
    encoding="utf-8"
)

Path("workspace/drafts/templates_unused/report_template_v1.txt").write_text(
    "Title:\nDate:\nAuthor:\n\nSection 1: Overview\nSection 2: Details\nSection 3: Sources\n\n"
    "(This is NOT the required format. Internal draft template only.)\n",
    encoding="utf-8"
)

Path("workspace/data/raw_feeds/rss_dump_2025.txt").write_text(
    "\n".join([
        f"Feed item {i}: [AV News {random.randint(2024,2025)}] Headline about autonomous driving regulation or company update #{i}"
        for i in range(1, 30)
    ]),
    encoding="utf-8"
)

Path("workspace/data/processed/entity_list.csv").write_text(
    "entity,type,relevance\n"
    "MIIT,regulator,China\n"
    "CATARC,standards body,China\n"
    "European Commission,regulator,EU\n"
    "UNECE WP.29,standards body,International\n"
    "Baidu Apollo,company,China\n"
    "Huawei HiCar,company,China\n"
    "Waymo,company,USA\n"
    "Mobileye,company,Israel/USA\n"
    "Li Auto,company,China\n"
    "NIO,company,China\n",
    encoding="utf-8"
)

Path("workspace/logs/research_session_2025_01.log").write_text(
    "[2025-01-15 09:00] Search started: 'autonomous driving China regulation 2025'\n"
    "[2025-01-15 09:02] Found 12 results, 3 relevant\n"
    "[2025-01-15 09:05] Search: 'EU autonomous vehicle L3 approval 2025'\n"
    "[2025-01-15 09:08] Session ended — report not completed\n",
    encoding="utf-8"
)

Path("workspace/config/search_config.json").write_text(
    '{"default_language": "zh-CN", "max_sources": 15, "time_window_days": 30, '
    '"priority_domains": ["miit.gov.cn", "ec.europa.eu", "unece.org"], '
    '"WARNING": "This config is unused by the skill. Check SKILL.md for actual defaults."}\n',
    encoding="utf-8"
)

Path("workspace/output/pending/placeholder.txt").write_text(
    "Output will go here. Filename: competitive_briefing.md\n"
    "Status: agent has not yet produced output.\n",
    encoding="utf-8"
)

# A deliberately malformed/incomplete prior attempt at the output
Path("workspace/drafts/old_reports/competitive_briefing_INCOMPLETE.md").write_text(
    "## 结论摘要\n"
    "自动驾驶法规正在快速演变，中欧均有新动态。（此摘要未完成，来源缺失，不可用）\n\n"
    "## 关键要点\n"
    "- 某项进展发生了 https://example.com/bare-url-not-linked\n"
    "- 欧盟发布了某指南（来源：待补充）\n\n"
    "## 来源清单\n"
    "1. 未填写\n",
    encoding="utf-8"
)

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(Path("workspace").rglob("*")):
    if f.is_file():
        print(f"  {f}")