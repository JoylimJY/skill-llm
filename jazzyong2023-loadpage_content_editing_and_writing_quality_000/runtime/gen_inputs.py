import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── distractor directory tree ──────────────────────────────────────────────
dirs = [
    "docs/legal",
    "docs/internal/hr",
    "marketing/assets/images",
    "marketing/drafts/archived",
    "marketing/campaigns/q3",
    "engineering/specs",
    "engineering/changelogs",
    "product/roadmap",
    "product/research/user_interviews",
    "finance/reports",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────
distractor_files = {
    "docs/legal/tos_v3.txt":
        "Terms of Service — Version 3.0\nLast updated: 2024-01-15\nBy using this service you agree to the following terms...",

    "docs/internal/hr/onboarding_checklist.md":
        "# Onboarding checklist\n- [ ] Set up email\n- [ ] Complete compliance training\n- [ ] Meet your manager",

    "marketing/assets/images/placeholder.txt":
        "Image assets stored externally in CDN. See asset_manifest.json.",

    "marketing/drafts/archived/launch_v1_DEPRECATED.txt":
        "Old draft — do not use. Superseded by launch_v2.",

    "marketing/campaigns/q3/budget.csv":
        "channel,spend,cpa\nemail,12000,8.50\npaid_search,45000,22.10\nsocial,18000,14.75",

    "engineering/specs/api_v2_spec.yaml":
        "openapi: 3.0.0\ninfo:\n  title: DataStream API\n  version: 2.0.0\npaths:\n  /ingest:\n    post:\n      summary: Ingest events",

    "engineering/changelogs/CHANGELOG_2024.md":
        "## 2024-Q2\n- Fixed race condition in event processor\n- Added retry logic for failed webhooks",

    "product/roadmap/q4_themes.txt":
        "Q4 themes: reliability, developer experience, enterprise compliance",

    "product/research/user_interviews/summary_aug2024.txt":
        "Key finding: users want faster onboarding. Average time-to-value is 11 days. Target: 3 days.",

    "finance/reports/arr_snapshot.txt":
        "ARR as of 2024-09: $4.2M\nNet revenue retention: 118%\nNew logos Q3: 34",
}

for path, content in distractor_files.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# ── THE ACTUAL TASK FILE ───────────────────────────────────────────────────
# A heavily AI-generated blog post draft packed with every major pattern from
# SKILL.md.  The agent must humanize it and write the result to
#  marketing/drafts/launch_announcement_final.md

raw_draft = '''\
## Exciting New Features And Major Platform Enhancements

Here is an overview of our latest product update. I hope this helps clarify what\u2019s new! Let me know if you\u2019d like me to expand on any section.

DataStream 3.0 serves as a testament to our unwavering commitment to innovation and excellence. This groundbreaking release marks a pivotal moment in the evolving landscape of data infrastructure\u2014underscoring our enduring mission to empower teams across the globe. The platform now boasts a vibrant, rich ecosystem of integrations, nestled within a breathtaking developer experience that is truly second to none.

- \u2728 **Real-Time Processing:** The platform now processes events in real time, ensuring that teams can act on fresh data instantly.
- \u2705 **Reliability Improvements:** Reliability has been significantly enhanced through robust fault-tolerance mechanisms.
- \u2b50 **Security Hardening:** Security has been strengthened with end-to-end encryption and zero-trust architecture.

It\u2019s not just an update\u2014it\u2019s a revolution. It\u2019s not merely a release; it\u2019s a statement about the future of data.

The new release features powerful integrations, seamless workflows, and unparalleled performance\u2014showcasing the company\u2019s pivotal role in shaping the future of analytics. Industry experts believe this will have a lasting impact on the data infrastructure sector, highlighting the platform\u2019s crucial contributions to the evolving technological landscape.

As of my last training update, the specifics of certain enterprise features are based on available information and may not reflect the most current details.

Experts argue that modern data platforms face several challenges. Despite these challenges, DataStream continues to thrive. Despite its growing complexity, the platform faces challenges typical of enterprise software\u2014including scalability bottlenecks and integration overhead. Despite these challenges, with its strategic vision and ongoing initiatives, DataStream continues to set the stage for the next era of data infrastructure.

The main system processes events efficiently. The core platform handles data with care. The central engine manages pipelines reliably. The primary solution orchestrates workflows seamlessly.

Our journey through data has taken us from the chaos of unstructured logs to the precision of real-time analytics, from the uncertainty of batch jobs to the confidence of streaming pipelines.

Great question\u2014you\u2019re absolutely right that observability is complex! That\u2019s an excellent point about the tracing features.

The platform\u2019s color palette of blue and silver reflects broader trends in enterprise branding, symbolizing trust and the enduring nature of data, reflecting the community\u2019s deep connection to reliable infrastructure.

It could potentially possibly be argued that the migration tooling might have some effect on reducing onboarding friction.

The future looks bright for DataStream. Exciting times lie ahead as we continue our journey toward excellence. This represents a major step in the right direction.

He said \u201cthe pipeline ran in under 200ms\u201d and the team was thrilled.
'''

draft_path = os.path.join(workspace, "marketing/drafts/launch_announcement_draft.md")
with open(draft_path, "w", encoding="utf-8") as f:
    f.write(raw_draft)

print("Workspace generated successfully.")
print(f"Draft file written to: {draft_path}")