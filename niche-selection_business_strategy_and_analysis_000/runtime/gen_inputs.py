import os
import json
import random

random.seed(42)

# Create workspace directory structure
base = "/workspace"
dirs = [
    "market_notes",
    "market_notes/competitors",
    "market_notes/trends",
    "research/communities",
    "research/pricing",
    "archive/old_ideas",
    "archive/2023_brainstorm",
    "team_notes",
    "financials",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files ---

# 1. market_notes/competitor_research.csv
with open(os.path.join(base, "market_notes", "competitor_research.csv"), "w") as f:
    f.write("Tool,Category,Price,Users\n")
    f.write("Clio,Practice Management,$49/mo,150000\n")
    f.write("MyCase,Practice Management,$49/mo,80000\n")
    f.write("Smokeball,Document Automation,$99/mo,30000\n")
    f.write("LawPay,Payment Processing,$0+2.9%,50000\n")
    f.write("Docketbird,Court Docketing,$29/mo,15000\n")

# 2. market_notes/trends/saas_trends_2024.md
with open(os.path.join(base, "market_notes", "trends", "saas_trends_2024.md"), "w") as f:
    f.write("# SaaS Trends 2024\n\n")
    f.write("- AI-assisted document review growing 40% YoY\n")
    f.write("- Legal ops automation attracting VC interest\n")
    f.write("- Solo attorneys underserved by enterprise tools\n")
    f.write("- E-discovery costs remain high for SMBs\n")
    f.write("- Client portal demand rising post-COVID\n")

# 3. market_notes/competitors/clio_reviews.txt
with open(os.path.join(base, "market_notes", "competitors", "clio_reviews.txt"), "w") as f:
    f.write("Negative reviews from G2:\n")
    f.write("- 'Too expensive for solo practitioners'\n")
    f.write("- 'Billing module is confusing'\n")
    f.write("- 'No automated client status updates'\n")
    f.write("- 'Mobile app is clunky'\n")
    f.write("- 'Onboarding took 3 weeks'\n")

# 4. research/communities/reddit_analysis.txt
with open(os.path.join(base, "research", "communities", "reddit_analysis.txt"), "w") as f:
    f.write("Subreddits analyzed:\n")
    f.write("r/LawFirm - 12,400 members, 5-10 posts/day\n")
    f.write("r/soloattorney - 3,200 members, 2-3 posts/day\n")
    f.write("r/legaltech - 8,900 members, 4-6 posts/day\n")
    f.write("r/paralegal - 22,000 members, 8-12 posts/day\n")
    f.write("\nTop complaints in r/soloattorney:\n")
    f.write("- Client intake forms still paper-based\n")
    f.write("- Invoice follow-up is manual and embarrassing\n")
    f.write("- Trust accounting (IOLTA) is error-prone\n")

# 5. research/pricing/pricing_benchmarks.md
with open(os.path.join(base, "research", "pricing", "pricing_benchmarks.md"), "w") as f:
    f.write("# Legaltech Pricing Benchmarks\n\n")
    f.write("| Segment | Typical Price | Notes |\n")
    f.write("|---|---|---|\n")
    f.write("| Solo attorney tools | $29-$79/mo | Price-sensitive |\n")
    f.write("| Small firm (2-10) | $79-$199/mo | WTP moderate |\n")
    f.write("| Mid-size firm | $500-$2000/mo | Enterprise sales |\n")
    f.write("| Paralegal tools | $19-$49/mo | Very price-sensitive |\n")
    f.write("| Court filing automation | $49-$149/mo | Niche, sticky |\n")

# 6. archive/old_ideas/2022_niche_list.txt
with open(os.path.join(base, "archive", "old_ideas", "2022_niche_list.txt"), "w") as f:
    f.write("Old brainstorm from 2022 (ABANDONED - do not use):\n")
    f.write("- Legal podcasting platform\n")
    f.write("- Bar exam prep app\n")
    f.write("- Legal dictionary API\n")
    f.write("- Lawyer matchmaking for clients\n")

# 7. archive/2023_brainstorm/scoring_attempt.txt
with open(os.path.join(base, "archive", "2023_brainstorm", "scoring_attempt.txt"), "w") as f:
    f.write("INCOMPLETE - do not use this scoring, it used wrong weights\n")
    f.write("We tried equal weighting (1/6 each) which was wrong.\n")
    f.write("Niche A: avg 3.5\n")
    f.write("Niche B: avg 2.8\n")
    f.write("Niche C: avg 4.1\n")
    f.write("(abandoned because scoring methodology was flawed)\n")

# 8. team_notes/meeting_2024_03.txt
with open(os.path.join(base, "team_notes", "meeting_2024_03.txt"), "w") as f:
    f.write("Meeting notes - March 2024\n")
    f.write("Attendees: Jordan, Sam, Alex\n")
    f.write("- We need to pick ONE niche by end of Q2\n")
    f.write("- Jordan pushed back on trust accounting niche (too regulated)\n")
    f.write("- Sam likes the client intake angle\n")
    f.write("- Alex wants data before deciding\n")
    f.write("Action: Score all 10 candidates properly this time.\n")

# 9. financials/runway.txt
with open(os.path.join(base, "financials", "runway.txt"), "w") as f:
    f.write("Current runway: 14 months\n")
    f.write("Minimum viable MRR target: $8,000/month\n")
    f.write("At $79/month per customer: need ~102 paying customers\n")
    f.write("At $49/month per customer: need ~164 paying customers\n")

# 10. market_notes/background_notes.md (distractor with partial info)
with open(os.path.join(base, "market_notes", "background_notes.md"), "w") as f:
    f.write("# Background Research Notes\n\n")
    f.write("The legaltech market is estimated at $27.6B by 2030.\n")
    f.write("Solo attorneys (~450,000 in US) are the most underserved.\n")
    f.write("Key pain: billing, client communication, document automation.\n")
    f.write("Our founder has 4 years as a paralegal + 2 years building B2B SaaS.\n")
    f.write("We have warm intros to 3 solo attorney communities via LinkedIn.\n")


# --- THE MAIN PROBLEM FILE ---
# raw_ideas.txt: 10 niche candidates with raw scores (no weighted totals)
# Scores: pain_intensity, personal_advantage, market_size, monetization, competition, growth (all 1-5)

niche_candidates = [
    {
        "id": 1,
        "name": "Automated IOLTA trust accounting for solo attorneys",
        "description": "Software that auto-reconciles trust accounts and generates compliance reports for solo practitioners managing client funds",
        "scores": {
            "pain_intensity": 5,
            "personal_advantage": 4,
            "market_size": 3,
            "monetization": 5,
            "competition": 3,
            "growth": 3
        }
    },
    {
        "id": 2,
        "name": "Client intake automation for immigration lawyers",
        "description": "Automated intake forms, document collection, and status updates for immigration attorneys managing high case volumes",
        "scores": {
            "pain_intensity": 5,
            "personal_advantage": 3,
            "market_size": 4,
            "monetization": 4,
            "competition": 3,
            "growth": 5
        }
    },
    {
        "id": 3,
        "name": "Court deadline tracking for solo family law attorneys",
        "description": "Automated docket monitoring and deadline alerts synced to state court calendars for family law solo practitioners",
        "scores": {
            "pain_intensity": 4,
            "personal_advantage": 5,
            "market_size": 4,
            "monetization": 3,
            "competition": 2,
            "growth": 3
        }
    },
    {
        "id": 4,
        "name": "AI contract review for startup founders",
        "description": "Plain-language AI review of vendor and employment contracts for non-legal startup founders before signing",
        "scores": {
            "pain_intensity": 4,
            "personal_advantage": 2,
            "market_size": 5,
            "monetization": 4,
            "competition": 2,
            "growth": 5
        }
    },
    {
        "id": 5,
        "name": "Invoice follow-up automation for solo attorneys",
        "description": "Automated, professional payment reminder sequences for solo attorneys who avoid awkward invoice follow-up conversations",
        "scores": {
            "pain_intensity": 4,
            "personal_advantage": 4,
            "market_size": 3,
            "monetization": 3,
            "competition": 4,
            "growth": 3
        }
    },
    {
        "id": 6,
        "name": "Legal document template marketplace for paralegals",
        "description": "Curated, jurisdiction-specific document templates sold to independent paralegals and virtual assistants",
        "scores": {
            "pain_intensity": 3,
            "personal_advantage": 3,
            "market_size": 3,
            "monetization": 2,
            "competition": 2,
            "growth": 2
        }
    },
    {
        "id": 7,
        "name": "Deposition scheduling and logistics for litigation support firms",
        "description": "Automated deposition coordination: scheduling, court reporter booking, and exhibit prep for litigation support vendors",
        "scores": {
            "pain_intensity": 3,
            "personal_advantage": 2,
            "market_size": 2,
            "monetization": 3,
            "competition": 4,
            "growth": 2
        }
    },
    {
        "id": 8,
        "name": "Client portal and status updates for solo estate planning attorneys",
        "description": "Lightweight client-facing portal for estate planning attorneys to share document status, collect signatures, and reduce phone tag",
        "scores": {
            "pain_intensity": 4,
            "personal_advantage": 5,
            "market_size": 4,
            "monetization": 4,
            "competition": 3,
            "growth": 4
        }
    },
    {
        "id": 9,
        "name": "Continuing legal education (CLE) tracking for bar compliance",
        "description": "Automated CLE credit tracking and state bar reporting for individual attorneys managing compliance deadlines",
        "scores": {
            "pain_intensity": 3,
            "personal_advantage": 2,
            "market_size": 4,
            "monetization": 2,
            "competition": 2,
            "growth": 2
        }
    },
    {
        "id": 10,
        "name": "Flat-fee billing package builder for small criminal defense firms",
        "description": "Tools to structure, price, and present flat-fee service packages for criminal defense attorneys moving away from hourly billing",
        "scores": {
            "pain_intensity": 4,
            "personal_advantage": 3,
            "market_size": 3,
            "monetization": 4,
            "competition": 4,
            "growth": 3
        }
    }
]

with open(os.path.join(base, "raw_ideas.txt"), "w") as f:
    f.write("LEGALTECH NICHE CANDIDATES - Raw Scoring Data\n")
    f.write("=" * 60 + "\n")
    f.write("Scores are on a 1-5 scale for each dimension.\n")
    f.write("NOTE: Weighted totals NOT computed yet — that's the next step.\n\n")
    for n in niche_candidates:
        f.write(f"--- Niche {n['id']}: {n['name']} ---\n")
        f.write(f"Description: {n['description']}\n")
        f.write(f"  Pain intensity:      {n['scores']['pain_intensity']}\n")
        f.write(f"  Personal advantage:  {n['scores']['personal_advantage']}\n")
        f.write(f"  Market size:         {n['scores']['market_size']}\n")
        f.write(f"  Monetization:        {n['scores']['monetization']}\n")
        f.write(f"  Competition:         {n['scores']['competition']}\n")
        f.write(f"  Growth trajectory:   {n['scores']['growth']}\n\n")


# --- VALIDATION DATA FILE ---
# Provides pass/fail results for the 5 validation checks for the top candidates
# The agent must score first to know which are top 3, then read this file

# Pre-computed weighted scores (for our reference):
# Weights: pain=0.25, advantage=0.20, market=0.20, monetization=0.15, competition=0.10, growth=0.10
# Niche 1: 5*0.25 + 4*0.20 + 3*0.20 + 5*0.15 + 3*0.10 + 3*0.10 = 1.25+0.80+0.60+0.75+0.30+0.30 = 4.00
# Niche 2: 5*0.25 + 3*0.20 + 4*0.20 + 4*0.15 + 3*0.10 + 5*0.10 = 1.25+0.60+0.80+0.60+0.30+0.50 = 4.05
# Niche 3: 4*0.25 + 5*0.20 + 4*0.20 + 3*0.15 + 2*0.10 + 3*0.10 = 1.00+1.00+0.80+0.45+0.20+0.30 = 3.75
# Niche 4: 4*0.25 + 2*0.20 + 5*0.20 + 4*0.15 + 2*0.10 + 5*0.10 = 1.00+0.40+1.00+0.60+0.20+0.50 = 3.70
# Niche 5: 4*0.25 + 4*0.20 + 3*0.20 + 3*0.15 + 4*0.10 + 3*0.10 = 1.00+0.80+0.60+0.45+0.40+0.30 = 3.55
# Niche 6: 3*0.25 + 3*0.20 + 3*0.20 + 2*0.15 + 2*0.10 + 2*0.10 = 0.75+0.60+0.60+0.30+0.20+0.20 = 2.65
# Niche 7: 3*0.25 + 2*0.20 + 2*0.20 + 3*0.15 + 4*0.10 + 2*0.10 = 0.75+0.40+0.40+0.45+0.40+0.20 = 2.60
# Niche 8: 4*0.25 + 5*0.20 + 4*0.20 + 4*0.15 + 3*0.10 + 4*0.10 = 1.00+1.00+0.80+0.60+0.30+0.40 = 4.10
# Niche 9: 3*0.25 + 2*0.20 + 4*0.20 + 2*0.15 + 2*0.10 + 2*0.10 = 0.75+0.40+0.80+0.30+0.20+0.20 = 2.65
# Niche 10: 4*0.25 + 3*0.20 + 3*0.20 + 4*0.15 + 4*0.10 + 3*0.10 = 1.00+0.60+0.60+0.60+0.40+0.30 = 3.50

# Top 3 by weighted score: Niche 8 (4.10), Niche 2 (4.05), Niche 1 (4.00)

# Validation check results for top 3:
# Niche 8 (client portal for estate planning): passes 4/5 (fails only pricing reality check - marginal)
# Niche 2 (client intake for immigration): passes 3/5 (fails community check and talk-to-people check)
# Niche 1 (IOLTA trust accounting): passes 2/5 (fails search volume and community checks) → KILL

validation_data = {
    "explanation": "Validation check results for top-scoring niche candidates. Each check is PASS or FAIL.",
    "niches": {
        "niche_8": {
            "name": "Client portal and status updates for solo estate planning attorneys",
            "checks": {
                "search_volume": "PASS - 'estate planning attorney client portal' shows growing Google Trends over 12 months",
                "community": "PASS - r/EstatePlanning (18K members), active Facebook group 'Estate Planning Attorneys Network' (9K members, daily posts)",
                "competitor_gap": "PASS - Clio and MyCase reviews show repeated complaints about 'client-facing portal is too complex' and 'clients can't figure out how to upload documents'",
                "pricing_reality": "PASS - Existing tools charge $49-$99/month; room for $59/month focused tool",
                "talk_to_people": "PASS - 4 conversations confirmed: estate attorneys hate phone tag and chasing document uploads"
            },
            "checks_passed": 5,
            "checks_failed": 0
        },
        "niche_2": {
            "name": "Client intake automation for immigration lawyers",
            "checks": {
                "search_volume": "PASS - 'immigration lawyer intake software' shows steady upward trend on Google Trends",
                "community": "FAIL - r/immigration is client-focused (not attorneys); no active attorney-specific Slack or Discord found with 5K+ members",
                "competitor_gap": "PASS - Negative reviews of Docketbird and MyCase cite 'no multilingual intake support' and 'document collection is manual'",
                "pricing_reality": "PASS - Immigration tools charge $79-$149/month; market expects paid solutions",
                "talk_to_people": "FAIL - Only 1 attorney conversation completed; person was lukewarm about switching tools ('it works well enough')"
            },
            "checks_passed": 3,
            "checks_failed": 2
        },
        "niche_1": {
            "name": "Automated IOLTA trust accounting for solo attorneys",
            "checks": {
                "search_volume": "FAIL - 'IOLTA software solo attorney' shows flat/declining trend on Google Trends; very low absolute volume",
                "community": "FAIL - No subreddit or active community specifically for IOLTA/trust accounting found; r/soloattorney has 3,200 members (below 5K threshold)",
                "competitor_gap": "PASS - TrustBooks and Clio reviews show complaints about 'reconciliation is still manual'",
                "pricing_reality": "PASS - TrustBooks charges $49/month; room exists for a premium solution",
                "talk_to_people": "PASS - 3 attorneys interviewed, all expressed frustration with end-of-month reconciliation errors"
            },
            "checks_passed": 3,
            "checks_failed": 2
        }
    }
}

with open(os.path.join(base, "validation_data.json"), "w") as f:
    json.dump(validation_data, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created in {base}:")
for root, dirs_list, files in os.walk(base):
    level = root.replace(base, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")