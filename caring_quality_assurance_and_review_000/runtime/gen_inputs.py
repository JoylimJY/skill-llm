import os
import random

random.seed(42)

# --- Build deeply nested distractor directory structure ---
dirs = [
    "workspace/projects/data_infra/drafts",
    "workspace/projects/data_infra/meetings",
    "workspace/projects/data_infra/archive",
    "workspace/projects/crm_migration/specs",
    "workspace/projects/crm_migration/reviews",
    "workspace/hr/onboarding/templates",
    "workspace/hr/policies",
    "workspace/finance/q3_reports",
    "workspace/finance/budget_2024",
    "workspace/it/infrastructure/network",
    "workspace/it/infrastructure/security",
    "workspace/communications/stakeholder_updates",
    "workspace/communications/internal_memos",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- Distractor files ---
distractors = {
    "workspace/projects/data_infra/meetings/kickoff_notes.txt": (
        "Kickoff meeting - March 4th\n"
        "Attendees: J. Harris, P. Zhao, M. Okonkwo\n"
        "Action items:\n"
        "- Finalise vendor shortlist by EOW\n"
        "- Schedule stakeholder interviews\n"
        "- Draft initial proposal (owner: M. Okonkwo)\n"
    ),
    "workspace/projects/data_infra/archive/old_proposal_v1.txt": (
        "DEPRECATED - do not use\n"
        "Initial braindump from Jan 2024. Superseded by current draft.\n"
    ),
    "workspace/projects/data_infra/archive/vendor_comparison_DRAFT.csv": (
        "Vendor,Price,Notes\n"
        "Snowflake,TBD,Needs scoping\n"
        "BigQuery,TBD,Needs scoping\n"
        "Redshift,TBD,Needs scoping\n"
    ),
    "workspace/projects/crm_migration/specs/migration_scope.txt": (
        "Scope of CRM migration:\n"
        "- Export all customer records from Salesforce Classic\n"
        "- Transform to new schema\n"
        "- Import into Salesforce Lightning\n"
        "Estimated timeline: 6 months\n"
    ),
    "workspace/projects/crm_migration/reviews/peer_review_template.txt": (
        "Peer Review Template\n"
        "Reviewer:\n"
        "Date:\n"
        "Summary of feedback:\n"
        "Approved: Y/N\n"
    ),
    "workspace/hr/onboarding/templates/welcome_email.txt": (
        "Hi [NAME],\n\n"
        "Welcome to the team! Your first day is [DATE].\n"
        "Please bring your ID and complete the forms attached.\n\n"
        "Best,\nHR Team\n"
    ),
    "workspace/hr/policies/remote_work_policy.txt": (
        "Remote Work Policy v2.1\n"
        "Employees may work remotely up to 3 days per week.\n"
        "Core hours: 10am-3pm local time.\n"
        "VPN required for all internal systems.\n"
    ),
    "workspace/finance/q3_reports/q3_summary.txt": (
        "Q3 2024 Financial Summary\n"
        "Revenue: $4.2M (vs $3.8M Q3 2023)\n"
        "OpEx: $3.1M\n"
        "EBITDA: $1.1M\n"
        "Key variance: higher-than-expected cloud spend (+18%)\n"
    ),
    "workspace/finance/budget_2024/data_infra_budget.txt": (
        "Data Infrastructure Budget 2024\n"
        "Approved headcount: 3 FTE\n"
        "Tool budget: $180,000\n"
        "Contingency: 10%\n"
        "Note: Any overrun >15% requires VP approval.\n"
    ),
    "workspace/it/infrastructure/network/topology_notes.txt": (
        "Network topology last updated: 2023-11-01\n"
        "Primary DC: us-east-1\n"
        "DR site: us-west-2\n"
        "VPN gateway: 10.0.0.1\n"
    ),
    "workspace/it/infrastructure/security/access_control.txt": (
        "Access Control Policy\n"
        "All new services must go through IAM review.\n"
        "MFA required for admin accounts.\n"
        "Quarterly access audits mandatory.\n"
    ),
    "workspace/communications/stakeholder_updates/update_march.txt": (
        "Stakeholder Update - March 2024\n"
        "Data infra proposal in progress.\n"
        "Expected to share with leadership by end of April.\n"
        "No blockers at this time.\n"
    ),
    "workspace/communications/internal_memos/data_team_memo.txt": (
        "TO: Data Team\n"
        "FROM: J. Harris\n"
        "RE: Proposal review\n\n"
        "Please review the attached proposal draft before it goes to leadership.\n"
        "We need to make sure it's up to standard.\n"
    ),
}

for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

# --- THE MAIN ARTIFACT: a half-assed project proposal ---
proposal = """\
PROJECT PROPOSAL: Data Infrastructure Modernisation

Prepared by: M. Okonkwo, Senior Data Analyst
Date: April 2024
Status: Draft

---

EXECUTIVE SUMMARY

Our current data infrastructure has some challenges that are impacting the business.
This proposal recommends that we modernise our data stack to address these issues
and position ourselves for future growth.

---

PROBLEM STATEMENT

The existing setup is not meeting our needs. There are performance issues, and the
team has expressed frustration with the current tools. Things take too long and
costs are higher than they should be. We need a better solution.

---

PROPOSED SOLUTION

We propose to migrate to a modern cloud data platform. This will involve:

- Moving data to a cloud warehouse (options TBD)
- Implementing better data governance
- Training the team on new tools
- Improving reporting capabilities

The new platform will be faster, more reliable, and more cost-effective.

---

TIMELINE

We expect the project to take several months. A detailed timeline will be developed
once the approach is finalised.

---

BUDGET

Costs will depend on the vendor selected and the scope of the project. We will
provide a more detailed budget estimate after further analysis.

---

EXPECTED BENEFITS

- Improved performance
- Better data quality
- Cost savings
- Happier team

---

RISKS

There are some risks associated with this project that will need to be managed.
Mitigation strategies will be developed as part of the planning process.

---

NEXT STEPS

The team will continue to work on this and provide updates as the project progresses.
We welcome feedback from stakeholders.

---

CONCLUSION

This project represents an important opportunity for the company. We look forward
to moving forward with leadership support.
"""

with open("workspace/projects/data_infra/drafts/data_infra_proposal_DRAFT.txt", "w") as f:
    f.write(proposal)

print("Workspace generated successfully.")
print("Key file: workspace/projects/data_infra/drafts/data_infra_proposal_DRAFT.txt")