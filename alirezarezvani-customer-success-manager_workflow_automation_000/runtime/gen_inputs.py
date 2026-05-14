import json
import os
import random

random.seed(42)

# ── directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "workspace/scripts",
    "workspace/assets",
    "workspace/references",
    "workspace/reports",
    "workspace/data/raw",
    "workspace/data/archive",
    "workspace/logs",
    "workspace/config",
    "workspace/templates",
    "workspace/exports",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "workspace/config/pipeline_config.yaml": "version: 2\nretries: 3\ntimeout: 120\noutput_dir: reports/\n",
    "workspace/config/segments.json": json.dumps({"enterprise": {"min_arr": 100000}, "mid_market": {"min_arr": 25000}, "smb": {"min_arr": 5000}}),
    "workspace/logs/pipeline_run_20260101.log": "INFO 2026-01-01 09:00:00 Pipeline started\nINFO 2026-01-01 09:05:00 3 customers processed\nINFO 2026-01-01 09:05:01 Pipeline complete\n",
    "workspace/logs/errors_20260101.log": "ERROR 2026-01-01 09:02:15 Customer C-009 missing field: contract_end_date\n",
    "workspace/data/archive/customers_2025Q3.json": json.dumps([{"customer_id": "C-OLD-001", "name": "Archived Corp", "arr": 50000}]),
    "workspace/data/raw/leads_pipeline.csv": "lead_id,company,stage\nL-001,Momentum Inc,Qualified\nL-002,Apex Solutions,Demo\n",
    "workspace/exports/health_scores_2025Q3.csv": "customer_id,score,status\nC-001,82,Green\nC-002,61,Yellow\n",
    "workspace/templates/email_template_churn.txt": "Subject: We noticed some changes in your usage...\n\nHi {name},\n\nWe wanted to reach out...\n",
    "workspace/templates/qbr_agenda.txt": "1. Review health metrics\n2. Discuss open support tickets\n3. Expansion opportunities\n4. Action items\n",
    "workspace/references/old_scoring_model_v0.9.md": "# Deprecated Scoring Model\nDo not use. Replaced by health_score_calculator.py v1.0\n",
    "workspace/assets/benchmark_notes.txt": "NRR target: 115%+\nGRR floor: 85%\nChurn rate acceptable: <5% annually\n",
    "workspace/data/raw/nps_survey_responses.json": json.dumps([{"customer_id": "C-101", "nps": 8}, {"customer_id": "C-102", "nps": 4}]),
}
for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

# ── stub scripts (simulate the real CLI tools already present in workspace) ───
# health_score_calculator.py
health_script = r'''#!/usr/bin/env python3
"""Health Score Calculator - Customer Success Manager v1.0"""
import json, sys, argparse, math

WEIGHTS = {"usage": 0.30, "engagement": 0.25, "support": 0.20, "relationship": 0.25}

def score_usage(u):
    lf = min(u.get("login_frequency", 0) / 30.0, 1.0) * 100
    fa = min(u.get("feature_adoption", 0), 100)
    dm = min(u.get("dau_mau_ratio", 0) / 0.5, 1.0) * 100
    return (lf + fa + dm) / 3.0

def score_engagement(e):
    stv = max(0, 100 - e.get("support_ticket_volume", 0) * 5)
    ma  = e.get("meeting_attendance", 0)
    nps = (e.get("nps_score", 0) + 100) / 2.0
    cs  = e.get("csat_score", 0)
    return (stv + ma + nps + cs) / 4.0

def score_support(s):
    ot  = max(0, 100 - s.get("open_tickets", 0) * 10)
    er  = max(0, 100 - s.get("escalation_rate", 0) * 200)
    rh  = max(0, 100 - s.get("avg_resolution_hours", 0) / 2.4)
    return (ot + er + rh) / 3.0

def score_relationship(r):
    ese = r.get("executive_sponsor_engagement", 0)
    mtd = min(r.get("multi_threading_depth", 0) / 5.0, 1.0) * 100
    rs  = r.get("renewal_sentiment", 0)
    return (ese + mtd + rs) / 3.0

def classify(score):
    if score >= 75: return "Green"
    if score >= 50: return "Yellow"
    return "Red"

def analyze(customers):
    results = []
    for c in customers:
        u = score_usage(c["usage"])
        e = score_engagement(c["engagement"])
        s = score_support(c["support"])
        r = score_relationship(c["relationship"])
        total = u * WEIGHTS["usage"] + e * WEIGHTS["engagement"] + s * WEIGHTS["support"] + r * WEIGHTS["relationship"]
        total = round(min(max(total, 0), 100), 2)
        prev  = c.get("previous_period", {}).get("health_score", total)
        trend = "improving" if total > prev else ("declining" if total < prev else "stable")
        results.append({
            "customer_id": c["customer_id"],
            "name": c["name"],
            "segment": c["segment"],
            "arr": c["arr"],
            "health_score": total,
            "status": classify(total),
            "trend": trend,
            "dimension_scores": {"usage": round(u,2), "engagement": round(e,2), "support": round(s,2), "relationship": round(r,2)}
        })
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--format", default="text", choices=["text","json"])
    args = parser.parse_args()
    with open(args.input_file) as f:
        data = json.load(f)
    customers = data if isinstance(data, list) else data.get("customers", [])
    results = analyze(customers)
    if args.format == "json":
        print(json.dumps({"health_scores": results}, indent=2))
    else:
        for r in results:
            print(f"[{r['status']}] {r['name']} ({r['segment']}) - Score: {r['health_score']} | Trend: {r['trend']}")

if __name__ == "__main__":
    main()
'''

# churn_risk_analyzer.py
churn_script = r'''#!/usr/bin/env python3
"""Churn Risk Analyzer - Customer Success Manager v1.0"""
import json, sys, argparse
from datetime import datetime, date

WEIGHTS = {"usage_decline": 0.30, "engagement_drop": 0.25, "support_issues": 0.20,
           "relationship_signals": 0.15, "commercial_factors": 0.10}

def score_usage_decline(ud):
    lt  = max(0, min(ud.get("login_trend", 0), 100))
    fac = max(0, min(ud.get("feature_adoption_change", 0), 100))
    dmc = max(0, min(ud.get("dau_mau_change", 0), 100))
    return (lt + fac + dmc) / 3.0

def score_engagement_drop(ed):
    mc  = max(0, min(ed.get("meeting_cancellations", 0), 100))
    rt  = max(0, min(ed.get("response_time_increase", 0), 100))
    nc  = max(0, min(ed.get("nps_change", 0), 100))
    return (mc + rt + nc) / 3.0

def score_support_issues(si):
    oe  = max(0, min(si.get("open_escalations", 0), 100))
    uc  = max(0, min(si.get("unresolved_critical", 0), 100))
    st  = max(0, min(si.get("satisfaction_trend", 0), 100))
    return (oe + uc + st) / 3.0

def score_relationship(rs):
    cl  = 100 if rs.get("champion_left", False) else 0
    sc  = 100 if rs.get("sponsor_change", False) else 0
    cm  = max(0, min(rs.get("competitor_mentions", 0), 100))
    return (cl + sc + cm) / 3.0

def score_commercial(cf):
    ct  = 0 if cf.get("contract_type","annual") == "annual" else 40
    pc  = 100 if cf.get("pricing_complaints", False) else 0
    bc  = 100 if cf.get("budget_cuts", False) else 0
    return (ct + pc + bc) / 3.0

def tier(score):
    if score >= 80: return "Critical"
    if score >= 60: return "High"
    if score >= 40: return "Medium"
    return "Low"

def days_to_renewal(date_str):
    try:
        end = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (end - date.today()).days
    except:
        return 999

def analyze(customers):
    results = []
    for c in customers:
        ud = score_usage_decline(c["usage_decline"])
        ed = score_engagement_drop(c["engagement_drop"])
        si = score_support_issues(c["support_issues"])
        rs = score_relationship(c["relationship_signals"])
        cf = score_commercial(c["commercial_factors"])
        total = (ud * WEIGHTS["usage_decline"] + ed * WEIGHTS["engagement_drop"] +
                 si * WEIGHTS["support_issues"] + rs * WEIGHTS["relationship_signals"] +
                 cf * WEIGHTS["commercial_factors"])
        total = round(min(max(total, 0), 100), 2)
        dtr = days_to_renewal(c.get("contract_end_date","2099-01-01"))
        results.append({
            "customer_id": c["customer_id"],
            "name": c["name"],
            "segment": c["segment"],
            "arr": c["arr"],
            "risk_score": total,
            "risk_tier": tier(total),
            "days_to_renewal": dtr,
            "signal_scores": {"usage_decline": round(ud,2), "engagement_drop": round(ed,2),
                              "support_issues": round(si,2), "relationship_signals": round(rs,2),
                              "commercial_factors": round(cf,2)}
        })
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--format", default="text", choices=["text","json"])
    args = parser.parse_args()
    with open(args.input_file) as f:
        data = json.load(f)
    customers = data if isinstance(data, list) else data.get("customers", [])
    results = analyze(customers)
    if args.format == "json":
        print(json.dumps({"churn_risks": results}, indent=2))
    else:
        for r in results:
            print(f"[{r['risk_tier']}] {r['name']} ({r['segment']}) - Risk: {r['risk_score']} | Renewal in {r['days_to_renewal']}d")

if __name__ == "__main__":
    main()
'''

# expansion_opportunity_scorer.py
expansion_script = r'''#!/usr/bin/env python3
"""Expansion Opportunity Scorer - Customer Success Manager v1.0"""
import json, sys, argparse

TIER_UPGRADES = {"starter": "growth", "growth": "professional", "professional": "enterprise", "enterprise": None}
TIER_MULTIPLIERS = {"starter": 1.5, "growth": 1.4, "professional": 1.3, "enterprise": 0}

def score_seat_expansion(contract):
    licensed = contract.get("licensed_seats", 0)
    active   = contract.get("active_seats", 0)
    if licensed == 0: return 0, 0
    utilization = active / licensed
    if utilization >= 0.85:
        additional = max(1, int(licensed * 0.25))
        arr_per_seat = 0  # unknown without price, use placeholder
        return round(utilization * 100, 2), additional
    return round(utilization * 100, 2), 0

def score_upsell(contract):
    current_tier = contract.get("plan_tier", "starter")
    available    = contract.get("available_tiers", [])
    next_tier    = TIER_UPGRADES.get(current_tier)
    if next_tier and next_tier in available:
        multiplier = TIER_MULTIPLIERS.get(current_tier, 0)
        return True, next_tier, multiplier
    return False, None, 0

def score_crosssell(product_usage):
    modules = product_usage.get("modules", {})
    opportunities = []
    for mod, info in modules.items():
        if isinstance(info, dict):
            if not info.get("adopted", False):
                opportunities.append(mod)
    return opportunities

def score_dept_expansion(departments):
    current  = set(departments.get("current", []))
    potential = set(departments.get("potential", []))
    new_depts = potential - current
    return list(new_depts)

def priority(arr, upsell, crosssell_count, dept_count, seat_expansion):
    score = 0
    if arr >= 100000: score += 40
    elif arr >= 25000: score += 25
    else: score += 10
    if upsell: score += 30
    score += crosssell_count * 8
    score += dept_count * 7
    if seat_expansion > 0: score += 15
    if score >= 70: return "High"
    if score >= 40: return "Medium"
    return "Low"

def analyze(customers):
    results = []
    for c in customers:
        contract = c.get("contract", {})
        prod_usage = c.get("product_usage", {})
        departments = c.get("departments", {})
        util_pct, seat_exp = score_seat_expansion(contract)
        upsell_avail, next_tier, multiplier = score_upsell(contract)
        crosssell_opps = score_crosssell(prod_usage)
        dept_opps = score_dept_expansion(departments)
        pri = priority(c["arr"], upsell_avail, len(crosssell_opps), len(dept_opps), seat_exp)
        estimated_expansion_arr = 0
        if upsell_avail: estimated_expansion_arr += int(c["arr"] * (multiplier - 1))
        estimated_expansion_arr += len(dept_opps) * 8000
        estimated_expansion_arr += seat_exp * 1200
        results.append({
            "customer_id": c["customer_id"],
            "name": c["name"],
            "segment": c["segment"],
            "arr": c["arr"],
            "priority": pri,
            "seat_utilization_pct": util_pct,
            "seat_expansion_recommended": seat_exp,
            "upsell_available": upsell_avail,
            "upsell_target_tier": next_tier,
            "crosssell_opportunities": crosssell_opps,
            "department_expansion_opportunities": dept_opps,
            "estimated_expansion_arr": estimated_expansion_arr
        })
    results.sort(key=lambda x: ({"High":0,"Medium":1,"Low":2}[x["priority"]], -x["arr"]))
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--format", default="text", choices=["text","json"])
    args = parser.parse_args()
    with open(args.input_file) as f:
        data = json.load(f)
    customers = data if isinstance(data, list) else data.get("customers", [])
    results = analyze(customers)
    if args.format == "json":
        print(json.dumps({"expansion_opportunities": results}, indent=2))
    else:
        for r in results:
            print(f"[{r['priority']}] {r['name']} ({r['segment']}) - Est. Expansion ARR: ${r['estimated_expansion_arr']:,}")

if __name__ == "__main__":
    main()
'''

scripts = {
    "workspace/scripts/health_score_calculator.py": health_script,
    "workspace/scripts/churn_risk_analyzer.py": churn_script,
    "workspace/scripts/expansion_opportunity_scorer.py": expansion_script,
}
for path, content in scripts.items():
    with open(path, "w") as f:
        f.write(content)

# ── the messy customer data file the agent must use ──────────────────────────
# This file contains 4 customers. All three scripts need DIFFERENT schema shapes.
# The agent must figure out that all three scripts take THE SAME file and it must
# contain combined fields for all three scripts.
# We design one unified customer list that satisfies all three scripts' schemas.

customers = [
    {
        # ENTERPRISE - High ARR, borderline Green health (76 → Green), Medium churn risk,
        # High expansion priority (upsell + dept expansion)
        "customer_id": "C-ENT-001",
        "name": "Axiom Workforce Solutions",
        "segment": "Enterprise",
        "arr": 180000,
        "contract_end_date": "2026-08-15",
        # --- health_score_calculator fields ---
        "usage": {
            "login_frequency": 22,        # 22/30 * 100 = 73.3
            "feature_adoption": 78,       # 78
            "dau_mau_ratio": 0.38         # 0.38/0.5 * 100 = 76
        },
        "engagement": {
            "support_ticket_volume": 3,   # 100 - 3*5 = 85
            "meeting_attendance": 80,
            "nps_score": 42,              # (42+100)/2 = 71
            "csat_score": 88
        },
        "support": {
            "open_tickets": 2,            # 100 - 2*10 = 80
            "escalation_rate": 0.05,      # 100 - 0.05*200 = 90
            "avg_resolution_hours": 18    # 100 - 18/2.4 = 92.5
        },
        "relationship": {
            "executive_sponsor_engagement": 72,
            "multi_threading_depth": 4,   # 4/5*100 = 80
            "renewal_sentiment": 75
        },
        "previous_period": {"health_score": 70},
        # --- churn_risk_analyzer fields ---
        "usage_decline": {
            "login_trend": 15,
            "feature_adoption_change": 10,
            "dau_mau_change": 8
        },
        "engagement_drop": {
            "meeting_cancellations": 20,
            "response_time_increase": 15,
            "nps_change": 10
        },
        "support_issues": {
            "open_escalations": 30,
            "unresolved_critical": 20,
            "satisfaction_trend": 15
        },
        "relationship_signals": {
            "champion_left": False,
            "sponsor_change": False,
            "competitor_mentions": 20
        },
        "commercial_factors": {
            "contract_type": "annual",
            "pricing_complaints": False,
            "budget_cuts": False
        },
        # --- expansion_opportunity_scorer fields ---
        "contract": {
            "licensed_seats": 100,
            "active_seats": 92,           # 92% utilization → seat expansion
            "plan_tier": "growth",
            "available_tiers": ["professional", "enterprise"]
        },
        "product_usage": {
            "modules": {
                "core_hr": {"adopted": True, "usage_pct": 95},
                "payroll": {"adopted": True, "usage_pct": 88},
                "performance": {"adopted": False, "usage_pct": 0},
                "learning": {"adopted": False, "usage_pct": 0},
                "analytics": {"adopted": True, "usage_pct": 72}
            }
        },
        "departments": {
            "current": ["HR", "Finance", "Operations"],
            "potential": ["HR", "Finance", "Operations", "Sales", "Engineering"]
        }
    },
    {
        # MID-MARKET - Declining Yellow health, High churn risk, Low expansion priority
        "customer_id": "C-MM-002",
        "name": "Crestline HR Partners",
        "segment": "Mid-Market",
        "arr": 48000,
        "contract_end_date": "2026-03-31",
        "usage": {
            "login_frequency": 10,        # 33.3
            "feature_adoption": 42,
            "dau_mau_ratio": 0.18         # 36
        },
        "engagement": {
            "support_ticket_volume": 8,   # 100-40=60
            "meeting_attendance": 45,
            "nps_score": 5,               # (5+100)/2=52.5
            "csat_score": 55
        },
        "support": {
            "open_tickets": 6,            # 40
            "escalation_rate": 0.25,      # 100-50=50
            "avg_resolution_hours": 48    # 100-20=80 ... wait 48/2.4=20 → 100-20=80
        },
        "relationship": {
            "executive_sponsor_engagement": 30,
            "multi_threading_depth": 2,   # 2/5=40
            "renewal_sentiment": 35
        },
        "previous_period": {"health_score": 68},
        "usage_decline": {
            "login_trend": 65,
            "feature_adoption_change": 55,
            "dau_mau_change": 70
        },
        "engagement_drop": {
            "meeting_cancellations": 80,
            "response_time_increase": 60,
            "nps_change": 75
        },
        "support_issues": {
            "open_escalations": 70,
            "unresolved_critical": 80,
            "satisfaction_trend": 65
        },
        "relationship_signals": {
            "champion_left": True,
            "sponsor_change": False,
            "competitor_mentions": 60
        },
        "commercial_factors": {
            "contract_type": "monthly",
            "pricing_complaints": True,
            "budget_cuts": False
        },
        "contract": {
            "licensed_seats": 50,
            "active_seats": 28,           # 56% → no seat expansion
            "plan_tier": "starter",
            "available_tiers": ["growth"]
        },
        "product_usage": {
            "modules": {
                "core_hr": {"adopted": True, "usage_pct": 55},
                "payroll": {"adopted": False, "usage_pct": 0},
                "performance": {"adopted": False, "usage_pct": 0},
                "learning": {"adopted": False, "usage_pct": 0},
                "analytics": {"adopted": False, "usage_pct": 0}
            }
        },
        "departments": {
            "current": ["HR"],
            "potential": ["HR", "Finance"]
        }
    },
    {
        # ENTERPRISE - Strong Green health, Low churn risk, High expansion priority
        "customer_id": "C-ENT-003",
        "name": "Meridian People Group",
        "segment": "Enterprise",
        "arr": 250000,
        "contract_end_date": "2027-01-15",
        "usage": {
            "login_frequency": 28,        # 93.3
            "feature_adoption": 88,
            "dau_mau_ratio": 0.46         # 92
        },
        "engagement": {
            "support_ticket_volume": 1,   # 95
            "meeting_attendance": 92,
            "nps_score": 68,              # (68+100)/2=84
            "csat_score": 94
        },
        "support": {
            "open_tickets": 1,            # 90
            "escalation_rate": 0.02,      # 96
            "avg_resolution_hours": 8     # 100-8/2.4=96.7
        },
        "relationship": {
            "executive_sponsor_engagement": 90,
            "multi_threading_depth": 5,   # 100
            "renewal_sentiment": 92
        },
        "previous_period": {"health_score": 88},
        "usage_decline": {
            "login_trend": 5,
            "feature_adoption_change": 3,
            "dau_mau_change": 4
        },
        "engagement_drop": {
            "meeting_cancellations": 5,
            "response_time_increase": 5,
            "nps_change": 3
        },
        "support_issues": {
            "open_escalations": 5,
            "unresolved_critical": 0,
            "satisfaction_trend": 5
        },
        "relationship_signals": {
            "champion_left": False,
            "sponsor_change": False,
            "competitor_mentions": 0
        },
        "commercial_factors": {
            "contract_type": "annual",
            "pricing_complaints": False,
            "budget_cuts": False
        },
        "contract": {
            "licensed_seats": 200,
            "active_seats": 195,          # 97.5% → seat expansion
            "plan_tier": "professional",
            "available_tiers": ["enterprise"]
        },
        "product_usage": {
            "modules": {
                "core_hr": {"adopted": True, "usage_pct": 99},
                "payroll": {"adopted": True, "usage_pct": 95},
                "performance": {"adopted": True, "usage_pct": 88},
                "learning": {"adopted": False, "usage_pct": 0},
                "analytics": {"adopted": True, "usage_pct": 85}
            }
        },
        "departments": {
            "current": ["HR", "Finance", "Operations", "Legal"],
            "potential": ["HR", "Finance", "Operations", "Legal", "Sales", "Engineering", "Marketing"]
        }
    },
    {
        # SMB - Red health (deep at-risk), Critical churn risk, Low expansion
        "customer_id": "C-SMB-004",
        "name": "Talentflow SMB Inc",
        "segment": "SMB",
        "arr": 12000,
        "contract_end_date": "2026-02-28",
        "usage": {
            "login_frequency": 4,         # 13.3
            "feature_adoption": 18,
            "dau_mau_ratio": 0.06         # 12
        },
        "engagement": {
            "support_ticket_volume": 12,  # 100-60=40
            "meeting_attendance": 20,
            "nps_score": -22,             # (-22+100)/2=39
            "csat_score": 32
        },
        "support": {
            "open_tickets": 8,            # 20
            "escalation_rate": 0.45,      # 100-90=10
            "avg_resolution_hours": 96    # 100-40=60
        },
        "relationship": {
            "executive_sponsor_engagement": 15,
            "multi_threading_depth": 1,   # 20
            "renewal_sentiment": 18
        },
        "previous_period": {"health_score": 45},
        "usage_decline": {
            "login_trend": 95,
            "feature_adoption_change": 90,
            "dau_mau_change": 92
        },
        "engagement_drop": {
            "meeting_cancellations": 95,
            "response_time_increase": 90,
            "nps_change": 88
        },
        "support_issues": {
            "open_escalations": 100,
            "unresolved_critical": 95,
            "satisfaction_trend": 92
        },
        "relationship_signals": {
            "champion_left": True,
            "sponsor_change": True,
            "competitor_mentions": 95
        },
        "commercial_factors": {
            "contract_type": "monthly",
            "pricing_complaints": True,
            "budget_cuts": True
        },
        "contract": {
            "licensed_seats": 20,
            "active_seats": 6,            # 30% → no seat expansion
            "plan_tier": "starter",
            "available_tiers": ["growth"]
        },
        "product_usage": {
            "modules": {
                "core_hr": {"adopted": True, "usage_pct": 22},
                "payroll": {"adopted": False, "usage_pct": 0},
                "performance": {"adopted": False, "usage_pct": 0},
                "learning": {"adopted": False, "usage_pct": 0},
                "analytics": {"adopted": False, "usage_pct": 0}
            }
        },
        "departments": {
            "current": ["HR"],
            "potential": ["HR"]
        }
    }
]

with open("workspace/assets/hrtech_customers_q1_2026.json", "w") as f:
    json.dump(customers, f, indent=2)

# ── SKILL.md placed at the expected workspace root ───────────────────────────
skill_md = """\
---
name: "customer-success-manager"
description: Monitors customer health, predicts churn risk, and identifies expansion opportunities using weighted scoring models for SaaS customer success.
license: MIT
metadata:
  version: 1.0.0
  python-tools: health_score_calculator.py, churn_risk_analyzer.py, expansion_opportunity_scorer.py
---

# Customer Success Manager

Production-grade customer success analytics with multi-dimensional health scoring, churn risk prediction, and expansion opportunity identification. Three Python CLI tools provide deterministic, repeatable analysis using standard library only -- no external dependencies, no API calls, no ML models.

## Input Requirements

All scripts accept a JSON file as positional input argument.

### Health Score Calculator
Required fields: customer_id, name, segment, arr, usage (login_frequency, feature_adoption, dau_mau_ratio), engagement (support_ticket_volume, meeting_attendance, nps_score, csat_score), support (open_tickets, escalation_rate, avg_resolution_hours), relationship (executive_sponsor_engagement, multi_threading_depth, renewal_sentiment), previous_period.

### Churn Risk Analyzer
Required fields: customer_id, name, segment, arr, contract_end_date, usage_decline, engagement_drop, support_issues, relationship_signals, commercial_factors.

### Expansion Opportunity Scorer
Required fields: customer_id, name, segment, arr, contract (licensed_seats, active_seats, plan_tier, available_tiers), product_usage (per-module adoption flags), departments (current and potential).

## Output Formats

All scripts support two output formats via the --format flag:
- text (default): Human-readable formatted output
- json: Machine-readable JSON output

## How to Use

```bash
python scripts/health_score_calculator.py customer_data.json --format json
python scripts/churn_risk_analyzer.py customer_data.json --format json
python scripts/expansion_opportunity_scorer.py customer_data.json --format json
```

## Scripts

### 1. health_score_calculator.py
Dimensions and Weights:
| Dimension   | Weight |
|-------------|--------|
| Usage       | 30%    |
| Engagement  | 25%    |
| Support     | 20%    |
| Relationship| 25%    |

Classification:
- Green (75-100): Healthy
- Yellow (50-74): Needs attention
- Red (0-49): At risk

### 2. churn_risk_analyzer.py
Risk Signal Weights:
| Signal             | Weight |
|--------------------|--------|
| Usage Decline      | 30%    |
| Engagement Drop    | 25%    |
| Support Issues     | 20%    |
| Relationship Signals| 15%  |
| Commercial Factors | 10%    |

Risk Tiers:
- Critical (80-100): Immediate executive escalation
- High (60-79): Urgent CSM intervention
- Medium (40-59): Proactive outreach
- Low (0-39): Standard monitoring

### 3. expansion_opportunity_scorer.py
Expansion Types: Upsell, Cross-sell, Expansion (seats/departments)
"""

with open("workspace/SKILL.md", "w") as f:
    f.write(skill_md)

print("Workspace generated successfully.")
print("Customers in input file: 4")
print("Input file: workspace/assets/hrtech_customers_q1_2026.json")