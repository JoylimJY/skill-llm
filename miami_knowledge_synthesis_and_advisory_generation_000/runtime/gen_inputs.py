import os
import random
import json

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure with distractor files ---
dirs = [
    "company/hr/relocation",
    "company/hr/benefits",
    "company/engineering/onboarding",
    "company/legal/contracts",
    "company/finance/reports",
    "research/cities/austin",
    "research/cities/denver",
    "research/cities/miami",
    "research/cities/nyc",
    "drafts/outdated",
    "drafts/pending",
    "skills/miami",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---

# Outdated NYC relocation guide
with open(os.path.join(WORKSPACE, "research/cities/nyc/relocation_guide.md"), "w") as f:
    f.write("""# NYC Relocation Guide
- Average 1BR: $3,200-4,800
- No state income tax: FALSE
- Public transit: Excellent (MTA)
- Car: Not needed
- Best neighborhoods for tech: Brooklyn, Manhattan
""")

# Austin comparison doc
with open(os.path.join(WORKSPACE, "research/cities/austin/notes.md"), "w") as f:
    f.write("""# Austin Notes
- 1BR rent: $1,800-2,600
- No state income tax: TRUE
- Car required: YES
- Tech scene: Strong (Tesla, Oracle, Apple)
""")

# Denver notes
with open(os.path.join(WORKSPACE, "research/cities/denver/overview.txt"), "w") as f:
    f.write("Denver cost of living moderate. Snow an issue. Outdoor lifestyle popular.")

# Outdated Miami salary data (WRONG/STALE - distractor)
with open(os.path.join(WORKSPACE, "research/cities/miami/OLD_salary_notes.txt"), "w") as f:
    f.write("""OUTDATED 2019 data:
Miami SWE salaries: $85K-110K
Rent 1BR: $1,400-2,000
Car insurance: ~$120/month
No state income tax applies.
Miami considered cheap alternative to NYC and SF.
""")

# HR benefits template (distractor)
with open(os.path.join(WORKSPACE, "company/hr/benefits/standard_package.md"), "w") as f:
    f.write("""# Standard Benefits Package
- Health: $400/mo employer contribution
- 401k: 4% match
- Relocation stipend: $5,000 (domestic)
- Housing allowance: none
""")

# Legal contract template (distractor)
with open(os.path.join(WORKSPACE, "company/legal/contracts/offer_letter_template.txt"), "w") as f:
    f.write("This Employment Agreement is entered into as of [DATE] between [COMPANY] and [EMPLOYEE]...")

# Finance report (distractor)
with open(os.path.join(WORKSPACE, "company/finance/reports/q3_expenses.csv"), "w") as f:
    f.write("department,category,amount\nengineering,travel,12000\nhr,relocation,45000\nmarketing,ads,88000\n")

# Outdated Miami draft (distractor - contains wrong info)
with open(os.path.join(WORKSPACE, "drafts/outdated/miami_2020_draft.md"), "w") as f:
    f.write("""# Miami 2020 Draft (DO NOT USE)
- South Beach best for young professionals
- No need for car downtown
- Miami much cheaper than NYC
- Hurricane season: August-October only
- Car insurance: roughly same as national average
""")

# Pending draft with partial info (distractor)
with open(os.path.join(WORKSPACE, "drafts/pending/miami_draft_partial.json"), "w") as f:
    json.dump({
        "city": "Miami",
        "status": "incomplete",
        "notes": "Need to update neighborhood recommendations and cost figures",
        "profiles": []
    }, f, indent=2)

# Engineering onboarding checklist (distractor)
with open(os.path.join(WORKSPACE, "company/engineering/onboarding/checklist.md"), "w") as f:
    f.write("""# Engineering Onboarding Checklist
- [ ] Laptop setup
- [ ] GitHub access
- [ ] Slack workspace
- [ ] VPN credentials
- [ ] Miami office badge
""")

# --- The actual SKILL.md files the agent should read ---

# Main SKILL.md
with open(os.path.join(WORKSPACE, "skills/miami/SKILL.md"), "w") as f:
    f.write("""---
name: Miami
slug: miami
version: 1.0.0
description: Navigate Miami as visitor, resident, tech worker, student, or entrepreneur with neighborhoods, beaches, costs, safety, and local insights.
metadata: {"clawdbot":{"emoji":"🌴","requires":{"bins":[]},"os":["linux","darwin","win32"]}}
---

## When to Use

User asks about Miami for any purpose: visiting, moving, working, studying, or starting a business. Agent provides practical guidance with current data.

## Quick Reference

| Topic | File |
|-------|------|
| **Visitors** | |
| Attractions & beaches | `visitor-attractions.md` |
| Itineraries (1/3/7 days) | `visitor-itineraries.md` |
| Where to stay | `visitor-lodging.md` |
| Tips & day trips | `visitor-tips.md` |
| **Neighborhoods** | |
| Quick comparison | `neighborhoods-index.md` |
| Downtown & Brickell | `neighborhoods-downtown.md` |
| Miami Beach | `neighborhoods-beach.md` |
| Wynwood & Design District | `neighborhoods-wynwood.md` |
| Coral Gables & Coconut Grove | `neighborhoods-coral.md` |
| North (Aventura, Sunny Isles) | `neighborhoods-north.md` |
| Choosing guide | `neighborhoods-choosing.md` |
| **Food** | |
| Overview & dining scene | `food-overview.md` |
| Cuban cuisine & Little Havana | `food-cuban.md` |
| Latin American flavors | `food-latin.md` |
| Seafood | `food-seafood.md` |
| Best dining areas | `food-areas.md` |
| Dietary & tips | `food-practical.md` |
| **Practical** | |
| Moving & settling | `resident.md` |
| Transport | `transport.md` |
| Cost of living | `cost.md` |
| Safety | `safety.md` |
| Weather & hurricanes | `climate.md` |
| Local services | `local.md` |
| **Career** | |
| Tech industry | `tech.md` |
| Students | `student.md` |
| Startups | `startup.md` |

## Core Rules

### 1. Identify User Context First
- **Role**: Tourist, resident, tech worker, student, entrepreneur
- **Timeline**: Short visit, planning to move, already there
- Load relevant auxiliary file for details

### 2. Safety Context
Miami is generally safe in tourist/residential areas. Main concerns:
- Car break-ins (don't leave valuables visible)
- Petty theft in tourist areas
- Avoid certain neighborhoods at night
See `safety.md` for area-specific guidance.

### 3. Weather Reality
- Hot and humid year-round (avg 77°F/25°C)
- Hurricane season: June 1 - November 30
- Rainy season: May-October (afternoon thunderstorms)
- Best months: November-April (dry, pleasant)
See `climate.md` for hurricane prep.

### 4. Current Data
| Item | Range |
|------|-------|
| 1BR rent | $2,200-3,500 (Brickell/Beach) |
| Senior SWE salary | $120K-180K (no state tax) |
| Student budget | $1,800-2,500/month |
| Car insurance | $200-400/month (FL crisis) |

### 5. Tourist Traps
- Skip: Ocean Drive (overpriced), Bayside Marketplace, chain restaurants
- Do: Little Havana, Wynwood Walls, Key Biscayne, Coral Gables
- Free: South Beach (early morning), Wynwood street art, Brickell City Centre

### 6. Car Is Essential
- Miami is NOT walkable (unlike NYC/London)
- Public transit limited (Metrorail, Metromover downtown only)
- Brightline train to Fort Lauderdale/West Palm useful
- Uber/Lyft expensive for daily use
- Budget for car + parking + insurance

### 7. Neighborhood Matching
| Profile | Best Areas |
|---------|------------|
| Young professionals | Brickell, Edgewater, Midtown |
| Families | Coral Gables, Coconut Grove, Pinecrest |
| Beach lifestyle | Miami Beach, Surfside, Key Biscayne |
| Budget-conscious | Doral, Kendall, Hialeah |
| Tech workers | Wynwood, Brickell, Design District |

## Miami-Specific Traps

- **"Beach party 24/7"** — South Beach is tourists. Locals rarely go.
- **"No need for a car"** — FALSE. Miami is car-dependent.
- **"Cheap alternative to NYC"** — Rent is now comparable, with lower salaries.
- **Ocean Drive** — Tourist trap. Walk to Lincoln Road or Española Way.
- **Hurricane ignorance** — Know your evacuation zone. Get supplies early.
- **Car insurance shock** — Florida has highest rates in US. Budget $3-4K/year.
- **Condo fees** — Post-Surfside reforms mean high assessments. Ask about reserves.
""")

# Auxiliary skill files
with open(os.path.join(WORKSPACE, "skills/miami/tech.md"), "w") as f:
    f.write("""# Tech Industry in Miami

## Scene Overview
Miami's tech scene has grown significantly since 2020 (\"Tech Miami\" wave).
Major hubs: Brickell (finance-tech), Wynwood (startups/creative), Design District (studios/agencies).

## Salaries
- Junior SWE: $75K-100K
- Mid SWE: $95K-130K
- Senior SWE: $120K-180K
- No Florida state income tax (saves ~$8-15K vs NY/CA)

## Top Employers
- Chewy (HQ)
- Carnival Corp
- World Fuel Services
- Emerging: Blockchain/Crypto firms, VC-backed startups

## Best Neighborhoods for Tech Workers
- Wynwood: Startup culture, walkable within district
- Brickell: Finance-tech, upscale, high-rises
- Design District: Creative-tech, boutique offices

## Warnings
- Salaries lower than SF/NYC on average
- No state tax advantage partially offset by high cost of living
- Traffic: Brickell/I-95 corridor brutal during rush hour
""")

with open(os.path.join(WORKSPACE, "skills/miami/startup.md"), "w") as f:
    f.write("""# Startups in Miami

## Ecosystem
- Strong VC presence post-2020 (Founders Fund, a16z interest)
- Crypto/Web3 hub
- Latin America gateway: ideal for LATAM market entry

## Key Areas
- Wynwood: Most startup-friendly vibe
- Brickell: Access to finance/banking partners
- Miami Beach: Less ideal (tourist noise, parking expensive)

## Costs for Founders
- Co-working: $300-600/month (Wynwood, Brickell)
- Office lease: $40-80/sqft/year
- Living (founder): budget $3,000-4,500/month all-in

## Condo/Housing Warning
Post-Surfside building collapse (2021), Florida passed strict new inspection laws.
Many condo buildings now face special assessments of $50K-$200K+ per unit.
Always ask: What are the reserves? Any pending assessments?

## Networking
- eMerge Americas (annual conference)
- Miami Tech Week
- Venture Café Miami (Thursdays, free)

## Traps
- Beautiful weather = distraction culture
- High cost of living reduces runway
- Talent pipeline thinner than NYC/SF (improving)
""")

with open(os.path.join(WORKSPACE, "skills/miami/student.md"), "w") as f:
    f.write("""# Students in Miami

## Universities
- University of Miami (Coral Gables) — private, research university
- Florida International University (FIU) — public, large, Sweetwater/Doral area
- Miami Dade College — community college, multiple campuses

## Monthly Budget Breakdown
| Category | Cost |
|----------|------|
| Rent (shared) | $900-1,400 |
| Food | $300-450 |
| Transport (car or Uber) | $200-350 |
| Utilities | $100-150 |
| Misc | $200-300 |
| **Total** | **$1,800-2,500** |

## Best Areas for Students
- Near UM: Coral Gables, South Miami
- Near FIU: Sweetwater, Doral (cheaper)
- Avoid: South Beach (too expensive, party-heavy)

## Tips
- Get a car or live near campus — transit is poor
- FIU is significantly cheaper than UM
- Summer internships often at tech/finance firms in Brickell
- Free events: Wynwood, Brickell City Centre, Bayside (selective)

## Warning
Student loans + Miami COL = tight budget. Track expenses carefully.
$1,800/month is bare minimum; $2,500 is comfortable.
""")

with open(os.path.join(WORKSPACE, "skills/miami/cost.md"), "w") as f:
    f.write("""# Cost of Living in Miami

## Housing
| Type | Monthly Cost |
|------|-------------|
| Studio | $1,800-2,500 |
| 1BR apartment | $2,200-3,500 |
| 2BR apartment | $3,000-4,800 |
| House rental | $3,500-6,000+ |

## Transportation
- Car payment: $400-700/month
- Car insurance: $200-400/month (Florida = highest in US)
- Gas: ~$60-100/month
- Parking (downtown/Brickell): $150-300/month
- Annual car budget: $10,000-18,000 total

## Food
- Groceries: $300-500/month
- Dining out (moderate): $50-80/week
- Coffee culture strong: $5-7/drink

## Comparison: Miami vs NYC vs Austin
| Item | Miami | NYC | Austin |
|------|-------|-----|--------|
| 1BR rent | $2,200-3,500 | $3,200-4,800 | $1,800-2,600 |
| State income tax | None | 4-10% | None |
| Car necessity | Essential | Not needed | Essential |
| Car insurance | $200-400/mo | $150-250/mo | $100-180/mo |

## Key Warning
"Miami is a cheap alternative to NYC" — THIS IS A MYTH.
Rent now comparable. Salaries lower. Car costs extra. Net take-home often LESS in Miami.

## Condo Assessments
Post-Surfside (2021 Champlain Towers collapse), Florida law requires:
- Mandatory structural inspections
- Fully funded reserve accounts
- Special assessments: $50K-$200K+ per unit common
ASK BEFORE BUYING: What are the current reserves? Any pending assessments?
""")

with open(os.path.join(WORKSPACE, "skills/miami/neighborhoods-choosing.md"), "w") as f:
    f.write("""# Choosing Your Miami Neighborhood

## By Profile

### Young Professionals (20s-30s, no kids)
- **Brickell**: Finance district, upscale bars, walkable within district
- **Edgewater**: Bayfront, artsy, slightly cheaper than Brickell
- **Midtown**: Between Wynwood and Edgewater, good balance

### Tech Workers
- **Wynwood**: Creative hub, startup offices, murals everywhere
- **Brickell**: Finance-tech crossover, high-rises
- **Design District**: Boutique tech/creative studios

### Families
- **Coral Gables**: Top-rated schools, tree-lined streets, Mediterranean architecture
- **Coconut Grove**: Laid-back, bayfront, strong community
- **Pinecrest**: Suburban, excellent schools, safe

### Students
- **Coral Gables / South Miami**: Near University of Miami
- **Sweetwater / Doral**: Near FIU, more affordable
- Avoid: South Beach (expensive, party atmosphere)

### Budget-Conscious
- **Doral**: Suburban, Latin community, reasonable rent
- **Kendall**: Family-friendly, cheaper, long commute to downtown
- **Hialeah**: Very affordable, heavily Cuban community

### Beach Lifestyle
- **Miami Beach**: Iconic but touristy and expensive
- **Surfside**: Quieter, upscale
- **Key Biscayne**: Island feel, family-friendly, pricey but serene

## What to Avoid
- Don't choose South Beach as your primary residence if you're a tech worker — it's tourist-heavy, expensive, poor transit
- Don't choose based on proximity to beaches alone — daily traffic/commute matters more
- Don't ignore condo special assessments — can add $500-2,000/month unexpectedly
""")

with open(os.path.join(WORKSPACE, "skills/miami/transport.md"), "w") as f:
    f.write("""# Transportation in Miami

## The Hard Truth
Miami is car-dependent. Period. Unlike NYC, Chicago, or Boston, you CANNOT realistically live without a car.

## Options
### Car (Recommended)
- Essential for most residents
- Budget: $10,000-18,000/year total (payment + insurance + gas + parking)
- Insurance alone: $200-400/month (Florida highest in US)

### Metrorail
- Limited: North-South corridor only (NW Miami to Dadeland South)
- Useful: Airport connector, UM station, Brickell station
- NOT useful for most daily trips

### Metromover
- Free elevated rail: Downtown Miami loop only
- Good for: Brickell, downtown, Omni
- NOT regional transit

### Brightline
- Private high-speed rail
- Connects: Miami (MiamiCentral) → Fort Lauderdale → West Palm Beach → Orlando
- Useful for: Business trips, airport alternative
- Not for daily commute within Miami

### Uber/Lyft
- Available but EXPENSIVE for daily use
- Average commute: $20-40 each way
- Use for: Nights out, airport runs

## Parking
- Downtown/Brickell: $150-300/month garage
- Wynwood: Challenging, street + paid lots
- Miami Beach: Expensive + restricted zones
- Suburbs: Usually free

## Cycling
- Limited but improving (Citi Bike in some areas)
- Heat and rain make it impractical most of the year
- Not a serious commute option
""")

with open(os.path.join(WORKSPACE, "skills/miami/climate.md"), "w") as f:
    f.write("""# Miami Weather & Climate

## Overview
- Tropical monsoon climate
- Hot and humid year-round
- Average temperature: 77°F/25°C
- No real "winter" (highs 70s-80s Dec-Feb)

## Seasons
| Season | Months | Conditions |
|--------|--------|------------|
| Dry/Pleasant | Nov-Apr | 70-82°F, low humidity, ideal |
| Rainy | May-Oct | 85-95°F, afternoon thunderstorms daily |
| Hurricane | Jun 1-Nov 30 | Overlap with rainy season |

## Hurricane Prep
- Know your evacuation zone (A, B, C, D, E)
- Zone A = highest risk (coastal, barrier islands)
- Zone B/C = moderate risk
- Stock supplies EARLY (stores empty out fast)
- Have a 72-hour emergency kit
- Know your building's age and construction

## Best Time to Visit/Move
- **November-April**: Perfect weather, events season (Art Basel = December)
- **July-August**: Peak heat + humidity + storm risk, avoid for moving

## Impact on Daily Life
- Afternoon thunderstorms (3-6pm) are daily in summer — plan around them
- Power outages common during storms
- AC runs year-round (budget $150-250/month electric bill)
""")

with open(os.path.join(WORKSPACE, "skills/miami/safety.md"), "w") as f:
    f.write("""# Safety in Miami

## General Assessment
Miami is generally safe in tourist and upscale residential areas.

## Main Concerns
1. **Car break-ins**: Most common crime. NEVER leave valuables visible.
2. **Petty theft**: Tourist areas (South Beach, Bayside). Keep bags close.
3. **Neighborhood variation**: Some areas unsafe at night.

## Area Guide
| Area | Safety Level | Notes |
|------|-------------|-------|
| Brickell | Very Safe | Business district, well-lit |
| Miami Beach (Collins/Ocean) | Moderate | Tourist petty theft |
| Wynwood | Generally Safe | Improving rapidly |
| Coral Gables | Very Safe | Residential, low crime |
| Downtown | Moderate | Varies by block |
| Little Haiti | Use Caution at Night | Transitional area |
| Liberty City | Avoid at Night | Higher crime area |
| Overtown | Avoid at Night | Higher crime area |

## Tips
- Don't flash expensive jewelry/electronics in public
- Use hotel/condo parking, not street parking
- Be aware of surroundings at night in unfamiliar areas
- Car break-ins: leave NOTHING visible, not even bags/chargers
""")

# Employee profiles for the task (this is the INPUT the agent must process)
profiles_data = {
    "company": "Vertex Dynamics",
    "relocation_cohort": "Q1 2025",
    "request": "Generate relocation advisory for the following three incoming Miami hires. We need accurate neighborhood recommendations, realistic cost breakdowns, and any critical local warnings they must know before arriving. Output as miami_relocation_advisory.json",
    "employees": [
        {
            "id": "EMP-001",
            "name": "Sarah Chen",
            "role": "Senior Software Engineer",
            "level": "L5",
            "priorities": ["proximity to tech scene", "urban lifestyle", "no commute"],
            "housing_preference": "apartment",
            "moving_from": "San Francisco",
            "assumption": "Miami will be significantly cheaper than SF and I won't need a car near the office"
        },
        {
            "id": "EMP-002",
            "name": "Marcus Webb",
            "role": "Founding Engineer / Startup CTO",
            "level": "founder",
            "priorities": ["startup ecosystem access", "networking", "affordable workspace"],
            "housing_preference": "apartment or condo",
            "moving_from": "New York City",
            "assumption": "Miami is a cheap alternative to NYC with great beach lifestyle near everything"
        },
        {
            "id": "EMP-003",
            "name": "Priya Nair",
            "role": "Graduate Intern",
            "level": "intern",
            "priorities": ["budget", "university proximity", "safe area"],
            "housing_preference": "shared apartment",
            "moving_from": "Boston",
            "assumption": "I can get by without a car using public transit like in Boston"
        }
    ]
}

with open(os.path.join(WORKSPACE, "company/hr/relocation/incoming_hires_q1_2025.json"), "w") as f:
    json.dump(profiles_data, f, indent=2)

# A confusing/wrong reference doc to test the agent's ability to use the CORRECT skill files
with open(os.path.join(WORKSPACE, "company/hr/relocation/miami_notes_UNVERIFIED.txt"), "w") as f:
    f.write("""UNVERIFIED NOTES - DO NOT RELY ON
- South Beach is great for tech workers (convenient)
- Car insurance in Miami ~$100-150/month
- Miami way cheaper than NYC, great deals on condos
- Public transit is decent, Metrorail covers most areas
- Hurricane season only really a concern August-September
- Salary expectations: Senior SWE ~$90-110K
- Student can live comfortably on $1,200-1,500/month
""")

print("Workspace initialized successfully.")
print(f"Files created in {WORKSPACE}")