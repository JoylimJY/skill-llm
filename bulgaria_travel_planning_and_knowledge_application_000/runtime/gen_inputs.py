import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── 1. Create the skill config directory ~/bulgaria/ with the core SKILL files ──
# In the container, HOME is /root
bulgaria_dir = Path("/root/bulgaria")
bulgaria_dir.mkdir(parents=True, exist_ok=True)

# Write SKILL.md (the entry point)
skill_md = """\
---
name: Bulgaria
slug: bulgaria
version: 1.0.0
homepage: https://clawic.com/skills/bulgaria
description: Plan Bulgaria with local context on Sofia, Plovdiv, the Black Sea, mountain routes, food, and tourist-trap avoidance.
changelog: Added a Bulgaria travel guide covering cities, coast, mountains, food, and practical trip planning.
metadata: {"clawdbot":{"emoji":"🇧🇬","requires":{"bins":[],"config":["~/bulgaria/"]},"os":["linux","darwin","win32"]}}
---

## Setup

If `~/bulgaria/` does not exist or is empty, read `setup.md` and start naturally.

## When to Use

User is planning a trip to Bulgaria or needs local context on cities, beaches, mountain trips, food, transport, winter resorts, or practical travel logistics.

## Architecture

Memory lives in `~/bulgaria/`. If `~/bulgaria/` does not exist, run `setup.md`. See `memory-template.md` for structure.

```
~/bulgaria/
└── memory.md     # Trip context and learned preferences
```

## Quick Reference

| Topic | File |
|-------|------|
| Setup process | `setup.md` |
| Memory template | `memory-template.md` |
| **Cities** | |
| Sofia complete guide | `sofia.md` |
| Plovdiv complete guide | `plovdiv.md` |
| Varna complete guide | `varna.md` |
| Bansko complete guide | `bansko.md` |
| **Planning** | |
| Sample itineraries | `itineraries.md` |
| Where to stay by style | `accommodation.md` |
| Useful apps | `apps.md` |
| **Food & Drink** | |
| Dishes, markets, ordering norms | `food-guide.md` |
| Wine regions and grape varieties | `wine.md` |
| **Experiences** | |
| Day trips and standout experiences | `experiences.md` |
| Black Sea beach guide | `beaches.md` |
| Hiking and mountain routes | `hiking.md` |
| Nightlife by city and season | `nightlife.md` |
| **Reference** | |
| Regional differences | `regions.md` |
| Customs, timing, etiquette | `culture.md` |
| Traveling with children | `with-kids.md` |
| **Practical** | |
| Flights, rail, buses, driving | `transport.md` |
| SIMs, roaming, coverage | `telecoms.md` |
| Emergencies and safety | `emergencies.md` |

## Core Rules

### 1. Specific Beats Generic
Do not say "try Bulgarian food". Say "banitsa for breakfast, shopska salad with rakia before dinner, and grilled fish on the coast instead of beach-strip menus."

### 2. Distinguish Bulgaria's Travel Modes
Match the plan to what the user actually wants:
- Sofia and Plovdiv for city + history
- Varna, Sozopol, and Sinemorets for coast
- Bansko, Rila, and Rhodopes for mountains
- Melnik and Thracian Valley for wine

### 3. Call Out Seasonal Reality
Timing changes the answer:
- Ski towns peak in winter and hiking peaks in summer
- Black Sea resorts feel best in June and September
- Sofia and Plovdiv are easier than the coast in deep winter
- Mountain weather turns fast even in warm months

### 4. Flag Tourist Traps Early
Warn about the common misses:
- Sunny Beach if the user wants quiet or local Bulgaria
- all-inclusive beach strips if they want food or culture
- driving mountain roads in winter without preparation
- assuming every "traditional" restaurant is actually good

### 5. Explain Practical Friction
Bulgaria is easy once the frictions are named:
- intercity buses are often more useful than trains
- cards work in cities, but some rural spots still prefer cash
- English is common in tourist areas, weaker in small towns
- prices and opening hours should be checked before booking

### 6. Match Traveler Style

| Traveler | Focus on |
|----------|----------|
| Foodie | `food-guide.md`, `wine.md`, `plovdiv.md` |
| Beach | `beaches.md`, `varna.md`, `regions.md` |
| Culture | `sofia.md`, `plovdiv.md`, `experiences.md` |
| Hiking | `hiking.md`, `bansko.md`, `regions.md` |
| Family | `with-kids.md`, `beaches.md`, `itineraries.md` |
| Nightlife | `nightlife.md`, `sofia.md`, `varna.md` |

## Common Traps

- Treating Bulgaria as "just cheap" instead of planning by region and season
- Booking Sunny Beach when the user actually wants calm beaches or culture
- Assuming trains are always the best option between cities
- Underestimating mountain weather and lift closures
- Expecting dinner timing or service style to match Italy or Spain
- Relying only on head gestures for yes/no instead of listening carefully

## Security & Privacy

**Data that stays local:**
- Trip preferences in `~/bulgaria/`
- Saved notes on cities, budget, pace, and dislikes

**This skill does NOT:**
- Access files outside `~/bulgaria/`
- Make network requests on its own
- Book or purchase anything without user direction

## Related Skills
Install with `clawhub install <slug>` if user confirms:
- `travel` - General trip planning and logistics
- `food` - Restaurant thinking, dishes, and meal planning
- `bulgarian` - Bulgarian language help for phrases, menus, and messaging

## Feedback

- If useful: `clawhub star bulgaria`
- Stay updated: `clawhub sync`
"""

(bulgaria_dir / "SKILL.md").write_text(skill_md)

# Write setup.md
setup_md = """\
# Setup

This skill stores all trip context in `~/bulgaria/memory.md`.

## Steps

1. Create `~/bulgaria/` if it does not exist.
2. Copy `memory-template.md` into `~/bulgaria/memory.md`.
3. Ask the user about their trip to populate the memory fields.

## Fields to populate
- traveler_style: one of Foodie, Beach, Culture, Hiking, Family, Nightlife
- travel_dates: ISO date range
- travel_party: solo, couple, family, group
- budget_level: budget, mid-range, luxury
- destination_focus: list of regions
- dislikes: comma-separated list of things to avoid
- notes: free text
"""
(bulgaria_dir / "setup.md").write_text(setup_md)

# Write memory-template.md
memory_template = """\
# Bulgaria Trip Memory

<!-- This file is auto-populated by the Bulgaria skill. Do not edit manually unless prompted. -->

## Traveler Profile

- **traveler_style**: <!-- e.g. Beach, Foodie, Culture, Hiking, Family, Nightlife -->
- **travel_dates**: <!-- e.g. 2025-06-15 to 2025-06-29 -->
- **travel_party**: <!-- solo | couple | family | group -->
- **budget_level**: <!-- budget | mid-range | luxury -->

## Destination Focus

- **regions**: <!-- comma-separated: Sofia, Plovdiv, Varna, Bansko, Black Sea Coast, Rhodopes, Melnik -->
- **avoid**: <!-- comma-separated dislikes, e.g. Sunny Beach, all-inclusive resorts, crowded markets -->

## Preferences

- **food_notes**: <!-- specific dishes liked/disliked -->
- **accommodation_notes**: <!-- boutique, hostel, resort, apartment -->
- **transport_notes**: <!-- car rental, bus, train preference -->

## Session Notes

<!-- Free text updated each session -->

"""
(bulgaria_dir / "memory-template.md").write_text(memory_template)

# ── 2. Write stub reference files (realistic distractor content) ──
stubs = {
    "sofia.md": "# Sofia\n\nFull city guide content. (stub)\n\nKey areas: Center, Lozenets, Studentski grad.\nMust-see: Alexander Nevsky Cathedral, Vitosha Boulevard, Central Market Hall.\n",
    "plovdiv.md": "# Plovdiv\n\nFull city guide content. (stub)\n\nKey areas: Old Town (Kapana), Karshiyaka.\nFood scene: Strong cafe culture, craft beer, traditional mehanas in Old Town.\n",
    "varna.md": "# Varna\n\nFull city guide content. (stub)\n\nKey areas: Sea Garden, City center, Chaika.\nNote: Better base than Sunny Beach for a local experience.\n",
    "bansko.md": "# Bansko\n\nFull city guide content. (stub)\n\nSki resort in winter, hiking base in summer.\nOld town mehanas with traditional food.\n",
    "beaches.md": "# Black Sea Beach Guide\n\nSozopol: Charming old town + beaches, quieter than Sunny Beach.\nSinemorets: Remote, clean, local.\nSunny Beach: Avoid if seeking quiet or local culture — mass tourism.\nKavatsite: Nudist-friendly, quiet, near Sozopol.\n",
    "food-guide.md": "# Food Guide\n\nBreakfast: banitsa (cheese pastry), mekitsi with jam, ayran.\nLunch: shopska salad, tarator (cold cucumber soup).\nDinner: kavarma, grilled fish on the coast, kebapche.\nRituals: rakia before dinner is standard.\nAvoid: beach-strip menus — overpriced and generic.\n",
    "wine.md": "# Wine Guide\n\nMelnik: indigenous Melnik grape, bold reds.\nThracian Valley: Mavrud, Rubin varieties.\nWine tourism: Starosel winery complex near Plovdiv.\n",
    "transport.md": "# Transport\n\nBuses: Intercity buses (Etap, Biomet) often faster and more frequent than trains.\nTrains: Scenic but slow; Sofia–Plovdiv is fine, Sofia–Varna is very long.\nCar: Best for Rhodopes, Melnik, rural areas. Check winter road conditions.\nNote: Do not assume trains are best — buses usually win.\n",
    "accommodation.md": "# Accommodation\n\nBoutique: Old town Plovdiv, Sozopol, Sofia center.\nHostels: Sofia (Hostel Mostel, etc.), budget travelers.\nResorts: Black Sea — avoid all-inclusive strips if food matters.\nApartments: Varna and Sofia for longer stays.\n",
    "itineraries.md": "# Sample Itineraries\n\n## 7-day Beach + Culture\nDays 1-2: Sofia (Alexander Nevsky, Vitosha)\nDays 3-4: Plovdiv (Old Town, Kapana)\nDays 5-7: Sozopol or Sinemorets (quiet beach)\n\n## 7-day Foodie\nDays 1-2: Sofia (Central Market, wine bars)\nDays 3-4: Plovdiv (mehanas, Kapana cafes)\nDays 5-7: Melnik + Thracian Valley wineries\n",
    "experiences.md": "# Experiences\n\nRila Monastery day trip from Sofia.\nKoprivshtitsa (historic village, 2hr from Sofia).\nBelogradchik Rocks.\nStancioff beach near Sinemorets.\n",
    "hiking.md": "# Hiking\n\nRila: Seven Rila Lakes (peak July–Sept). Musala peak (2925m).\nPirin: Bansko base, Vihren peak.\nRhodopes: Trigrad gorge, Yagodinska cave.\nWarning: Mountain weather turns fast — always check forecast.\n",
    "nightlife.md": "# Nightlife\n\nSofia: Studentski grad (cheap, local), Lozenets (upscale).\nVarna: Seasonal summer nightlife along the beach strip.\nPlovdiv: Kapana district, jazz bars, live music.\nBansko: Après-ski in winter, quiet in summer.\n",
    "regions.md": "# Regional Differences\n\nNorth: Danube plain, less touristy.\nSouth: Plovdiv, Rhodopes, Thracian Valley — strong food/wine.\nBlack Sea: Eastern coast, seasonal.\nMountains: Rila, Pirin, Balkan, Rhodopes.\n",
    "culture.md": "# Culture & Etiquette\n\nHead gestures: YES = shake side to side. NO = nod up and down. Opposite of Western norms.\nDo not rely only on head gestures — listen carefully.\nDining: Dinner starts late (8–9pm). Service is slower than Western Europe.\nTipping: 10% is appreciated but not mandatory.\n",
    "with-kids.md": "# Traveling with Children\n\nBest beaches: Sozopol (calm water), Albena (shallow, family resort).\nActivities: Rila Monastery, Belogradchik, Sofia Zoo.\nAvoid: Long mountain drives in unpredictable weather with young children.\n",
    "apps.md": "# Useful Apps\n\nBus times: Etap-Adres app, Rome2rio for rough routing.\nMaps: Maps.me offline, Google Maps for cities.\nTranslation: Google Translate (Bulgarian Cyrillic keyboard).\nFood: TripAdvisor filtered by local reviews, not tourist rank.\n",
    "telecoms.md": "# Telecoms\n\nSIMs: A1, Telenor, Vivacom available at airports and malls.\nCoverage: Good in cities, patchy in mountains and rural Rhodopes.\nRoaming: EU roaming applies for EU travelers.\n",
    "emergencies.md": "# Emergencies & Safety\n\nEmergency: 112 (EU standard).\nPolice: 166. Ambulance: 150. Fire: 160.\nHospitals: Pirogov in Sofia is the main trauma center.\nSafety: Generally safe. Pickpocketing in tourist areas. Mountain rescue: 1410.\n",
}

for fname, content in stubs.items():
    (bulgaria_dir / fname).write_text(content)

# ── 3. Create workspace distractor files ──
# Simulate a travel agency's messy project folder

(workspace / "clients").mkdir(exist_ok=True)
(workspace / "clients" / "archive").mkdir(exist_ok=True)
(workspace / "clients" / "active").mkdir(exist_ok=True)
(workspace / "templates").mkdir(exist_ok=True)
(workspace / "templates" / "reports").mkdir(exist_ok=True)
(workspace / "research").mkdir(exist_ok=True)
(workspace / "research" / "destinations").mkdir(exist_ok=True)
(workspace / "research" / "competitors").mkdir(exist_ok=True)
(workspace / "invoices").mkdir(exist_ok=True)
(workspace / "logs").mkdir(exist_ok=True)

# Distractor: old Greece trip plan
(workspace / "clients" / "archive" / "greece_trip_2024.md").write_text(
    "# Greece Trip 2024\nClient: Maria P.\nDestination: Santorini + Athens\nBudget: mid-range\nNotes: Avoid tourist traps in Oia. Prefer local tavernas.\n"
)

# Distractor: generic travel template
(workspace / "templates" / "generic_trip_template.md").write_text(
    "# Trip Plan Template\n\n## Client\n## Destination\n## Dates\n## Budget\n## Notes\n"
)

# Distractor: competitor research note
(workspace / "research" / "competitors" / "sunny_beach_review.txt").write_text(
    "Sunny Beach review 2024: Very crowded, high prices for average food, dominated by party tourism. Not suitable for families or culture seekers.\n"
)

# Distractor: invoice stub
(workspace / "invoices" / "INV-2024-089.txt").write_text(
    "Invoice #2024-089\nClient: Johnson family\nService: Greece itinerary\nAmount: 350 EUR\nPaid: Yes\n"
)

# Distractor: log file
(workspace / "logs" / "agent_activity.log").write_text(
    "2024-12-01 09:00 - Session started\n2024-12-01 09:05 - Client brief received\n2024-12-01 09:30 - Draft sent\n"
)

# Distractor: research notes
(workspace / "research" / "destinations" / "turkey_notes.md").write_text(
    "# Turkey Research\nIstanbul: Sultanahmet crowded in summer. Prefer Karakoy.\nCappadocia: Hot air balloons book out 3 weeks ahead.\n"
)
(workspace / "research" / "destinations" / "romania_notes.md").write_text(
    "# Romania Research\nBucharest: Old Town (Centrul Vechi) lively at night. Transylvania: Brasov better base than Bran.\n"
)

# Distractor: empty placeholder files
(workspace / "templates" / "reports" / "draft_report_v1.md").write_text(
    "# Draft Report v1\n\n[PLACEHOLDER - DO NOT USE]\n"
)
(workspace / "clients" / "active" / "pending_clients.txt").write_text(
    "1. Hendricks - Albania (Q1 2025)\n2. Kowalski - Bulgaria (June 2025) - BRIEF PENDING\n3. Nguyen - Portugal (March 2025)\n"
)

# ── 4. Write the CLIENT BRIEF (the main task input) ──
client_brief = """\
# Client Brief — Kowalski Family

**Received:** 2025-01-15
**Handled by:** Travel Consultant

## Client Details

- **Names:** Andrzej & Beata Kowalski + teenage daughter (16)
- **Travel party:** Family (3)
- **Travel dates:** 2025-06-18 to 2025-07-01 (13 nights)
- **Budget:** mid-range

## What They Want

The Kowalski family is visiting Bulgaria for the first time. Their primary interest is a calm beach holiday — they want to swim, eat well, and relax. Beata is a keen foodie and specifically wants to try local Bulgarian food rather than international menus. Andrzej researched online and mentioned "Sunny Beach" as an option he saw advertised.

They explicitly said:
- NO crowded beach resorts
- NO all-inclusive packages
- They want to experience authentic local food
- The daughter is interested in seeing at least one historic or cultural site

## Questions / Notes

- Andrzej asked whether trains are the best way to get around since he read Bulgaria has a rail network.
- They have not booked transport within Bulgaria yet.
- They are flying into Sofia.

## Deliverable

Produce a personalized trip plan file and update the travel memory for this client.
"""
(workspace / "clients" / "active" / "kowalski_brief.md").write_text(client_brief)

print("Workspace generated successfully.")
print(f"Bulgaria skill dir: {bulgaria_dir}")
print(f"Files in ~/bulgaria/: {[f.name for f in bulgaria_dir.iterdir()]}")
print(f"Workspace files: {list(workspace.rglob('*'))}")