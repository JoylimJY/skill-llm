import os
import json
import random

random.seed(42)

BASE = "/workspace"

# --- Directory structure with distractor files ---
dirs = [
    "crm/raw_leads",
    "crm/processed",
    "crm/archive",
    "crm/config",
    "reports/weekly",
    "reports/monthly",
    "ads/meta",
    "ads/google",
    "ads/tiktok",
    "ops/sla_rules",
    "ops/escalation",
    "finance/budget",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "crm/config/crm_settings.json": json.dumps({
        "crm_version": "4.2.1",
        "default_owner": "unassigned",
        "max_pipeline_stages": 7,
        "currency": "USD"
    }, indent=2),
    "crm/archive/leads_2024_Q4.json": json.dumps([
        {"lead_id": "L-20241201-01", "status": "closed_won", "source": "Google Ads"},
        {"lead_id": "L-20241215-02", "status": "closed_lost", "source": "Meta"},
    ], indent=2),
    "reports/weekly/week_48_summary.txt": "Week 48 summary: 312 leads processed, 18% close rate.\nTop source: Google Ads.\nAction items: Review TikTok budget allocation.",
    "reports/monthly/nov_pipeline.csv": "lead_id,stage,value\nL-001,discovery,12000\nL-002,proposal,34000\nL-003,closed_won,8000",
    "ads/meta/campaign_brief_Q1.txt": "Campaign: Spring Launch 2026\nObjective: Lead generation\nBudget: $45,000\nTargeting: 25-45, interests: SaaS, project management\nCreative: A/B test 3 variants",
    "ads/google/keyword_list.txt": "project management software\nbest pm tool 2026\nteam collaboration software\nasana alternative\njira alternative\nmonday.com competitor",
    "ads/tiktok/creative_notes.md": "# TikTok Creative Notes\n- Short-form 15s videos perform best\n- Hook in first 2 seconds\n- CTA: 'Start free trial'\n- Test 4 creative variants per week",
    "ops/sla_rules/response_times.txt": "Tier 1 (Enterprise): 2 hours\nTier 2 (SMB): 8 hours\nTier 3 (SMB basic): 24 hours\nUnqualified: 72 hours",
    "ops/escalation/escalation_contacts.json": json.dumps({
        "sales_lead": "sarah.chen@company.com",
        "ops_lead": "mike.torres@company.com",
        "finance_escalation": "cfo@company.com"
    }, indent=2),
    "finance/budget/q1_2026_allocation.json": json.dumps({
        "total_budget": 180000,
        "meta": 60000,
        "google_ads": 75000,
        "tiktok": 30000,
        "youtube": 15000
    }, indent=2),
    "crm/config/pipeline_stages.json": json.dumps({
        "stages": ["new", "enrichment", "qualified", "discovery", "proposal", "negotiation", "closed_won", "closed_lost"],
        "stage_owners": {
            "new": "intake-bot",
            "enrichment": "data-team",
            "qualified": "sdr-team",
            "discovery": "ae-team"
        }
    }, indent=2),
    "crm/processed/.gitkeep": "",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(BASE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE MAIN PROBLEM: Raw messy lead batch ---
# Mixed quality, multiple platforms, some missing critical fields,
# mixed regions, high/low intent signals, varying scores

raw_leads = [
    {
        "lead_id": "L-20260303-01",
        "lead_source": "Meta",
        "timestamp": "2026-03-03T08:15:00Z",
        "first_name": "Aisha",
        "last_name": "Okonkwo",
        "email": "aisha.okonkwo@techcorp.ng",
        "company": "TechCorp NG",
        "company_size": "250",
        "region": "EU",
        "job_title": "Head of Operations",
        "intent_score": 45,
        "fit_score": 38,
        "urgency_score": 22,
        "ad_campaign": "Spring_Lead_Gen_EU_Meta",
        "form_fields_completed": ["first_name", "last_name", "email", "company", "company_size", "job_title"],
        "qualification_goal": "book_demo"
    },
    {
        "lead_id": "L-20260303-02",
        "lead_source": "Google Ads",
        "timestamp": "2026-03-03T09:02:00Z",
        "first_name": "Marcus",
        "last_name": "Bellini",
        "email": "m.bellini@entgroup.it",
        "company": "ENT Group",
        "company_size": "1200",
        "region": "EU",
        "job_title": "CTO",
        "intent_score": 38,
        "fit_score": 40,
        "urgency_score": 15,
        # CRITICAL FIELD MISSING: qualification_goal is absent
        "ad_campaign": "GoogleAds_Enterprise_EU",
        "form_fields_completed": ["first_name", "last_name", "email", "company", "company_size", "job_title"],
        "notes": "Searched 'enterprise project management platform comparison'"
    },
    {
        "lead_id": "L-20260303-03",
        "lead_source": "TikTok Ads",
        "timestamp": "2026-03-03T09:45:00Z",
        "first_name": "Jordan",
        "last_name": "Park",
        # CRITICAL FIELD MISSING: email is absent
        "company": "StartupXYZ",
        "company_size": "12",
        "region": "US",
        "job_title": "CEO",
        "intent_score": 30,
        "fit_score": 25,
        "urgency_score": 20,
        "ad_campaign": "TikTok_SMB_US",
        "form_fields_completed": ["first_name", "last_name", "company", "job_title"],
        "qualification_goal": "free_trial_signup"
    },
    {
        "lead_id": "L-20260303-04",
        "lead_source": "Meta",
        "timestamp": "2026-03-03T10:30:00Z",
        "first_name": "Priya",
        "last_name": "Sharma",
        "email": "priya.sharma@scaleworks.in",
        "company": "ScaleWorks",
        "company_size": "85",
        "region": "US",
        "job_title": "VP of Product",
        "intent_score": 35,
        "fit_score": 32,
        "urgency_score": 18,
        "ad_campaign": "Meta_SMB_US_Retarget",
        "form_fields_completed": ["first_name", "last_name", "email", "company", "company_size", "job_title"],
        "qualification_goal": "book_demo"
    },
    {
        "lead_id": "L-20260303-05",
        "lead_source": "Google Ads",
        "timestamp": "2026-03-03T11:00:00Z",
        "first_name": "Chen",
        "last_name": "Wei",
        "email": "chen.wei@megatrade.cn",
        "company": "MegaTrade",
        "company_size": "5000",
        "region": "US",
        "job_title": "Director of IT",
        "intent_score": 40,
        "fit_score": 42,
        "urgency_score": 30,
        "ad_campaign": "GoogleAds_Enterprise_US",
        "form_fields_completed": ["first_name", "last_name", "email", "company", "company_size", "job_title"],
        "qualification_goal": "book_demo",
        "notes": "Searched 'replace jira enterprise 2026', visited pricing page 3x"
    },
    {
        "lead_id": "L-20260303-06",
        "lead_source": "TikTok Ads",
        "timestamp": "2026-03-03T12:15:00Z",
        "first_name": "Sofia",
        "last_name": "Mendez",
        "email": "sofia.m@creativeagency.mx",
        "company": "Creative Agency MX",
        "company_size": "8",
        "region": "US",
        "job_title": "Founder",
        "intent_score": 15,
        "fit_score": 10,
        "urgency_score": 5,
        "ad_campaign": "TikTok_SMB_US",
        "form_fields_completed": ["first_name", "email", "company"],
        "qualification_goal": "free_trial_signup"
    },
    {
        "lead_id": "L-20260303-07",
        "lead_source": "Meta",
        "timestamp": "2026-03-03T13:00:00Z",
        "first_name": "David",
        "last_name": "Kowalski",
        "email": "d.kowalski@buildfast.pl",
        "company": "BuildFast",
        "company_size": "320",
        "region": "EU",
        "job_title": "Operations Manager",
        "intent_score": 40,
        "fit_score": 35,
        "urgency_score": 28,
        "ad_campaign": "Spring_Lead_Gen_EU_Meta",
        "form_fields_completed": ["first_name", "last_name", "email", "company", "company_size", "job_title"],
        "qualification_goal": "book_demo"
    },
    {
        "lead_id": "L-20260303-08",
        "lead_source": "Google Ads",
        "timestamp": "2026-03-03T13:45:00Z",
        "first_name": "Natalie",
        "last_name": "Brooks",
        "email": "n.brooks@finserve.us",
        "company": "FinServe US",
        "company_size": "780",
        "region": "US",
        "job_title": "COO",
        "intent_score": 40,
        "fit_score": 42,
        "urgency_score": 30,
        # Missing lead_source qualification context but has all fields
        "ad_campaign": "GoogleAds_Enterprise_US",
        "form_fields_completed": ["first_name", "last_name", "email", "company", "company_size", "job_title"],
        "qualification_goal": "book_demo",
        "notes": "Clicked on 'enterprise pricing' ad, visited ROI calculator"
    },
    {
        "lead_id": "L-20260303-09",
        "lead_source": "Meta",
        "timestamp": "2026-03-03T14:20:00Z",
        # CRITICAL FIELD MISSING: first_name, last_name absent
        "email": "unknown@domain.com",
        "company": "",
        "company_size": "",
        "region": "EU",
        "job_title": "",
        "intent_score": 20,
        "fit_score": 10,
        "urgency_score": 8,
        "ad_campaign": "Spring_Lead_Gen_EU_Meta",
        "form_fields_completed": ["email"],
        "qualification_goal": "book_demo"
    },
    {
        "lead_id": "L-20260303-10",
        "lead_source": "TikTok Ads",
        "timestamp": "2026-03-03T15:00:00Z",
        "first_name": "James",
        "last_name": "Oduya",
        "email": "james.oduya@rapidscale.io",
        "company": "RapidScale",
        "company_size": "45",
        "region": "US",
        "job_title": "Growth Lead",
        "intent_score": 38,
        "fit_score": 32,
        "urgency_score": 18,
        "ad_campaign": "TikTok_SMB_US",
        "form_fields_completed": ["first_name", "last_name", "email", "company", "company_size", "job_title"],
        "qualification_goal": "free_trial_signup"
    },
]

# Also write a routing rules config and SLA config (partial/incomplete, agent must infer from skill)
routing_config = {
    "routing_rules": {
        "high_priority_threshold": 80,
        "teams": {
            "team-a": {"region": "US", "focus": "enterprise", "min_company_size": 200},
            "team-b": {"region": "EU", "focus": "enterprise", "min_company_size": 200},
            "team-c": {"region": "US", "focus": "smb", "max_company_size": 199},
            "team-d": {"region": "EU", "focus": "smb", "max_company_size": 199},
            "enrichment-queue": {"purpose": "leads with missing critical fields"},
        }
    },
    "response_sla": {
        "high_intent_same_day_hours": 4,
        "standard_hours": 24,
        "low_fit_hours": 72
    }
}

with open(os.path.join(BASE, "crm/raw_leads/batch_20260303.json"), "w") as f:
    json.dump(raw_leads, f, indent=2)

with open(os.path.join(BASE, "crm/config/routing_config.json"), "w") as f:
    json.dump(routing_config, f, indent=2)

# Additional distractor: an old pipeline plan from 2024 (NOT what agent should output)
old_plan = {
    "date": "2024-11-15",
    "note": "This is an ARCHIVED plan from Q4 2024. Do not use.",
    "leads_processed": 45,
    "routing": "all to team-a"
}
with open(os.path.join(BASE, "crm/archive/pipeline_plan_2024_Q4.json"), "w") as f:
    json.dump(old_plan, f, indent=2)

print("Workspace initialized successfully.")
print(f"Leads batch written: crm/raw_leads/batch_20260303.json ({len(raw_leads)} leads)")