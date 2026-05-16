import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---
dirs = [
    "crm_ops/workflows",
    "crm_ops/scoring",
    "crm_ops/properties",
    "crm_ops/lifecycle",
    "marketing/campaigns/q1",
    "marketing/campaigns/q2",
    "marketing/email_templates",
    "marketing/reports",
    "sales/sequences",
    "sales/territories",
    "data/raw_exports",
    "data/cleansed",
    "docs/runbooks",
    "docs/sops",
    "infra/scripts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "crm_ops/workflows/lead_routing.json": {
        "workflow_name": "Lead Routing v2",
        "trigger": "Contact property updated",
        "actions": ["assign_owner", "send_notification"],
        "active": True
    },
    "crm_ops/scoring/lead_score_model.json": {
        "model_name": "MQL Score",
        "thresholds": {"mql": 50, "sql": 80},
        "signals": ["page_views", "form_fills", "email_clicks"],
        "version": "3.1"
    },
    "crm_ops/properties/custom_properties.json": {
        "properties": [
            {"name": "icp_tier", "type": "enumeration", "label": "ICP Tier"},
            {"name": "persona_segment", "type": "string", "label": "Persona Segment"},
            {"name": "engagement_score", "type": "number", "label": "Engagement Score"}
        ]
    },
    "crm_ops/lifecycle/stage_definitions.json": {
        "stages": ["Subscriber", "Lead", "MQL", "SQL", "Opportunity", "Customer", "Partner", "Evangelist"],
        "auto_transitions": True
    },
    "marketing/campaigns/q1/q1_plan.json": {
        "campaign_name": "Q1 2024 Outbound",
        "target_segment": "ICP Tier 1",
        "send_date": "2024-01-15",
        "budget": 12000
    },
    "marketing/campaigns/q2/q2_plan.json": {
        "campaign_name": "Q2 2024 Re-engagement",
        "target_segment": "Lapsed Contacts",
        "send_date": "2024-04-01",
        "budget": 8000
    },
    "marketing/email_templates/nurture_sequence.html": "<html><body><p>Hi {{first_name}}, ...</p></body></html>",
    "marketing/reports/monthly_metrics.csv": "month,sends,opens,clicks\n2024-01,10000,2500,600\n2024-02,10500,2700,650",
    "sales/sequences/outbound_touch.json": {
        "sequence_name": "Manufacturing Outbound 5-Touch",
        "steps": [
            {"day": 1, "type": "email", "template": "intro"},
            {"day": 3, "type": "call"},
            {"day": 7, "type": "email", "template": "follow_up"},
            {"day": 14, "type": "linkedin"},
            {"day": 21, "type": "email", "template": "breakup"}
        ]
    },
    "sales/territories/territory_map.json": {
        "regions": {
            "AMER": ["US", "CA", "MX"],
            "EMEA": ["GB", "DE", "FR", "NL"],
            "APAC": ["AU", "SG", "JP"]
        }
    },
    "data/raw_exports/contacts_export_2024_q1.csv": "id,email,lifecycle_stage,icp_tier\n1,john@acme.com,Lead,Tier 1\n2,jane@globalco.com,Customer,Tier 2",
    "data/cleansed/contacts_cleansed.csv": "id,email,lifecycle_stage,icp_tier,unsubscribed,bounced\n1,john@acme.com,Lead,Tier 1,false,false\n2,jane@globalco.com,Customer,Tier 2,false,false",
    "docs/runbooks/icp_tier_assignment.md": "# ICP Tier Assignment\n\nRun the ICP scoring workflow monthly to assign tiers...",
    "docs/sops/campaign_launch_checklist.md": "# Campaign Launch Checklist\n\n1. Verify list sizes\n2. Check unsubscribe rates\n3. Confirm send time\n4. A/B test subject lines",
    "infra/scripts/sync_contacts.sh": "#!/bin/bash\n# Sync contacts from data warehouse\npython3 sync.py --source=warehouse --dest=crm",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    if isinstance(content, (dict, list)):
        with open(full_path, "w") as f:
            json.dump(content, f, indent=2)
    else:
        with open(full_path, "w") as f:
            f.write(content)

# --- Company business profile (the "interview answers" the agent must consume) ---
company_profile = {
    "company_name": "Velochain Technologies",
    "industry_focus": "B2B SaaS for supply chain and logistics",
    "engagement_window_days": 90,
    "reengagement_window_days": 180,
    "target_personas": {
        "titles": [
            "CTO",
            "VP of Operations",
            "Director of Procurement",
            "Head of Logistics",
            "Chief Operating Officer",
            "VP of Supply Chain"
        ]
    },
    "target_industries": [
        "Manufacturing",
        "Logistics",
        "Professional Services",
        "Transportation",
        "Warehousing"
    ],
    "content_keywords": [
        "Download",
        "Guide",
        "Whitepaper",
        "Checklist",
        "E-Book"
    ],
    "notes": "We sell to mid-market and enterprise manufacturers and logistics firms. Our sales cycle is 90-120 days."
}

with open(os.path.join(workspace, "company_profile.json"), "w") as f:
    json.dump(company_profile, f, indent=2)

# --- A partial/wrong draft that the agent must NOT simply copy ---
bad_draft = {
    "lists": [
        {
            "name": "All Contacts",
            "type": "static",
            "filters": [{"field": "email", "operator": "is_known"}]
        },
        {
            "name": "Marketable",
            "type": "static",
            "filters": [
                {"field": "marketing_contact_status", "operator": "is_any_of", "value": "Marketing contact"},
                {"field": "unsubscribed", "operator": "is_not_equal_to", "value": True}
            ]
        }
    ],
    "note": "DRAFT - incomplete, do not use"
}

with open(os.path.join(workspace, "crm_ops/lists_draft_INCOMPLETE.json"), "w") as f:
    json.dump(bad_draft, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in os.walk(workspace) for f in _[2])}")