import os
import random
import json

random.seed(42)

BASE = "/workspace"
os.makedirs(BASE, exist_ok=True)

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "research/raw_data",
    "research/competitor_notes",
    "research/customer_feedback",
    "research/trends",
    "archive/old_ideas",
    "archive/2022_brainstorm",
    "finances/projections",
    "finances/expenses",
    "marketing/drafts",
    "marketing/social",
    "ops/legal",
    "ops/vendors",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "archive/old_ideas/concept_v1.txt": "Original idea: flashcard app for kids. Abandoned 2022.",
    "archive/old_ideas/pricing_scratch.txt": "Tried $5/mo, too low. $50/mo too high for B2C.",
    "archive/2022_brainstorm/notes.txt": "Thinking about EdTech but too broad.\nMaybe language niche?",
    "finances/projections/2023_forecast.csv": "month,revenue\nJan,0\nFeb,0\nMar,200\nApr,400",
    "finances/expenses/startup_costs.txt": "Domain: $12/yr\nHosting: $20/mo\nTools: $80/mo",
    "marketing/drafts/tagline_ideas.txt": "Learn faster. Speak sooner. Real conversation, no fluff.",
    "marketing/social/twitter_ideas.txt": "Tweet ideas:\n- 'Most apps teach vocabulary. We teach survival.'",
    "ops/legal/tos_notes.txt": "Need ToS before launch. Contact lawyer Q2.",
    "ops/vendors/hosting_comparison.txt": "Fly.io vs Railway vs Render — Railway easiest for MVP.",
    "marketing/drafts/landing_copy_v2.txt": "Hero: 'Finally speak the language you've been studying for years.'",
    "ops/legal/gdpr_checklist.txt": "GDPR: consent banner, data deletion endpoint, privacy policy.",
    "finances/expenses/tool_licenses.txt": "Loom, Notion, Linear — all on free tiers for now.",
}
for path, content in distractors.items():
    with open(os.path.join(BASE, path), "w") as f:
        f.write(content)

# ── RAW DATA FILE 1: population & market stats (messy, needs interpretation) ──
population_stats = """\
# Raw Market Stats — Adult Language Learning SaaS (scraped notes, unverified)
# Source: various public reports, BLS, Statista snippets

Global English-language internet users: ~1.5 billion
Adults (18+) actively studying a foreign language globally: ~1.2 billion (estimate, UNESCO adjacent)
Adults studying language in English-speaking markets (US, UK, CA, AU, NZ): ~68 million

Percent who use a digital app or SaaS tool for language learning: ~30%
  -> Calculated: 68M * 0.30 = ~20.4M potential SAM base

Of those digital learners, percent who experience "intermediate plateau" (our core pain):
  -> Forum surveys, Reddit polls: roughly 25% cite frustration with progress stalling
  -> That gives: 20.4M * 0.25 = ~5.1M with acute pain point

Realistic ARPU for B2C language SaaS (annual subscription): $96/yr ($8/mo)
  -> Some charge $15/mo, some $6/mo; $8 is defensible midpoint

Year 1 realistic market capture for new entrant: 1% to 3% of reachable SAM
  -> Conservative (1%): 5.1M * 0.01 = 51,000 users
  -> Optimistic (3%): 5.1M * 0.03 = 153,000 users

Note: Year-1 SOM revenue range:
  -> Conservative: 51,000 * $96 = $4,896,000
  -> Optimistic: 153,000 * $96 = $14,688,000

BLS data point: 1.8M adults enrolled in formal language courses in the US alone (2022).
Grand View Research snippet: Global language learning market $61.8B by 2028, CAGR 18.7%.
"""
with open(os.path.join(BASE, "research/raw_data/market_stats_raw.txt"), "w") as f:
    f.write(population_stats)

# ── RAW DATA FILE 2: competitor notes (messy, incomplete, needs profile schema) ──
competitor_notes = """\
=== COMPETITOR SCRAPE NOTES (messy, fill in gaps from logic) ===

-- Duolingo --
site: duolingo.com
founded: 2011
funding: IPO 2021, ~$521M raised pre-IPO, public (DUOL)
serves: mass market, all ages, all levels
why customers pick it: free, gamified, habit-forming
pricing: free tier + Super Duolingo ~$6.99/mo or $83.99/yr
good at: retention mechanics, breadth of languages, mobile UX, streaks
bad at: doesnt get you to conversational fluency, repetitive, no real conversation practice
traffic estimate: ~200M MAU (SimilarWeb top 500 globally)

-- Babbel --
site: babbel.com
founded: 2007
funding: ~$60M raised, profitable per 2019 reports, tried IPO 2021 cancelled
serves: adult learners wanting structured curriculum
why customers choose: structured lessons, feels more "serious" than Duo
pricing: $12.95/mo, $83.99/yr, lifetime $299
good at: grammar structure, European languages, adult-focused tone
bad at: speaking practice thin, no community, expensive vs Duolingo
traffic: ~10M MAU

-- italki --
site: italki.com
founded: 2009
funding: undisclosed, likely bootstrapped/small seed
serves: adults wanting human tutors, 1-on-1 sessions
why: real human tutors, any language, flexible scheduling
pricing: marketplace — tutors $5-$80/hr, platform takes 15% cut
good at: human connection, variety of tutors, community language exchange
bad at: inconsistent tutor quality, no structured curriculum, no progress tracking
traffic: ~2M MAU

-- Pimsleur --
site: pimsleur.com
founded: 1963 (audio method), now owned by Simon & Schuster
funding: corporate subsidiary
serves: busy professionals, commuters, audio learners
why: audio-first, proven spaced repetition method
pricing: $14.95/mo per language, $20.95/mo all access
good at: audio quality, pronunciation, commuter-friendly
bad at: dated UX, no writing/reading, expensive, no community
traffic: ~500K MAU

-- Preply --
site: preply.com
founded: 2012
funding: $70M Series C (2021), total ~$115M
serves: adults and some corporate clients wanting tutor matching
why: subscription model for recurring tutor sessions, better UX than italki
pricing: subscription plans from $8/hr to $30/hr depending on tutor tier
good at: subscription model, business language packages, UX
bad at: pricey for casual learners, tutors still variable quality, no self-study path
traffic: ~3M MAU
"""
with open(os.path.join(BASE, "research/competitor_notes/competitors_raw.txt"), "w") as f:
    f.write(competitor_notes)

# ── RAW DATA FILE 3: customer reviews / forum posts (needs persona extraction) ──
customer_feedback = """\
=== RAW CUSTOMER FEEDBACK — pulled from Reddit, App Store, G2 ===
(subreddits: r/languagelearning, r/learnspanish, r/French, App Store reviews)

[Reddit - u/MarcoT_Berlin]:
"I've been on Duolingo for 3 years. I can read Spanish okay but the moment someone speaks fast I'm lost. 
I need something that bridges me to REAL conversation. Duolingo keeps me engaged but it's not getting me fluent."
Role context: software engineer, 34, remote worker, uses Slack/Notion daily.

[App Store - 3 stars - Babbel]:
"Good structure but I hit a wall at intermediate. There's nothing that challenges me beyond canned sentences.
I'm a project manager, I need to speak in meetings with our Mexico City office. That's my goal and Babbel can't help."
Demographic signals: professional, B2B adjacent need, 30s.

[Reddit - u/NightOwl_Nurse]:
"I work nights so I study during the day when my family's asleep. I need something async, no live sessions at 
weird hours. italki requires scheduling and I always cancel. I need AI conversation practice I can do at 3am."
Role context: nurse, irregular hours, 28-40 age range implied.

[G2 review - Preply - 2 stars]:
"Too expensive for what it is. I'm a freelance graphic designer, I don't have a company paying for this. 
$200/mo for decent tutors? I can't justify it. There has to be a middle ground between $7 Duolingo and $200 Preply."
Signals: freelancer, price-sensitive, wants professional-grade output.

[Reddit - u/RetiredTeacher_Pam]:
"I'm 61, learning Italian for our move to Tuscany in 2 years. I don't want gamification, I'm not a child.
I want something that respects my intelligence and focuses on real-life scenarios. All the apps feel like toys."
Signals: older adult learner, lifestyle motivated, anti-gamification, has money (retiring abroad).

[Reddit - u/SarahK_MBA]:
"My company is expanding to Germany. I'm leading the Berlin office opening. I have 8 months.
I need structured, fast, measurable progress. B2 level is the goal. I'd pay whatever it takes if I could 
see a credible path. None of the apps give me confidence I'll actually get there."
Signals: high-income professional, outcome-driven, B2B-ish need, tight deadline.

[App Store - 1 star - Duolingo]:
"Addictive but useless for actual fluency. The streak mechanic is manipulative. I've wasted 500 days on this app."
[App Store - 4 stars - Duolingo]:
"Perfect for commuting. I learn a few words on the subway. Not trying to become fluent, just want some basics for vacation."
[Reddit general]:
"Why is there no app for intermediate learners? Everything either assumes you're a beginner or requires you to already be advanced."
[Reddit - language learning]:
"Intermediate plateau is REAL. You understand 60% of a conversation but that 40% gap is demoralizing."
"""
with open(os.path.join(BASE, "research/customer_feedback/reviews_raw.txt"), "w") as f:
    f.write(customer_feedback)

# ── RAW DATA FILE 4: trend signals (needs 5-part assessment) ─────────────────
trend_signals = """\
=== TREND SIGNALS — adult language SaaS ===

SIGNAL A: Conversational AI / LLM-powered language tutors
- OpenAI launched ChatGPT; multiple startups (Speak, Langotalk, Ablo) now use GPT-4 for conversation simulation
- Speak raised $16M in 2022, $27M Series B 2023 specifically for AI conversation practice
- Google integrated Gemini into Google Translate with conversational mode
- Adoption: still early — most mainstream apps haven't shipped it yet; <15% of language learners use AI conversation tools
- Implication: AI conversation practice is the gap all incumbents are racing to fill

SIGNAL B: Remote work → business language demand spike
- LinkedIn data: job postings requiring bilingual skills up 34% since 2020
- Harvard Business Review piece: multilingual employees earn 5-20% wage premium
- Corporate language training market growing separately from consumer — $7B segment
- Duolingo for Business launched but received mixed enterprise reviews (still too casual)
- Adoption: business language need is growing ~25-30% YoY per corporate L&D surveys

SIGNAL C: Subscription fatigue / value scrutiny
- Consumer subscription cancellation rates hit 40% in 2023 (Zuora State of Subscriptions report)
- Language app churn: Duolingo disclosed ~47% of subscribers churn within first year
- Users increasingly compare "did I actually learn vs. did I feel busy"
- Price sensitivity up post-2022 inflation; willingness to pay drops for entertainment-adjacent SaaS

SIGNAL D: Aging demographics / silver economy
- Adults 55+ are the fastest-growing segment of language app downloads (App Annie 2022)
- This cohort has higher disposable income, more time, lifestyle-driven motivation (travel, retirement abroad)
- Most apps NOT designed for this segment — gamification, streaks, and childlike UI alienate them
- Adoption of language apps by 55+ still low, ~8% of total users, but growing 40% YoY

SIGNAL E: Immersive content (podcasts, Netflix, YouTube) emerging as learning tools
- "Comprehensible input" method gaining Reddit/YouTube traction — millions of views
- Netflix launched language learning mode in some markets
- Shifts learner expectation toward entertainment-aligned study, not drills
- Risk: reduces paid subscription willingness if free content perceived as sufficient
"""
with open(os.path.join(BASE, "research/trends/trend_signals_raw.txt"), "w") as f:
    f.write(trend_signals)

# ── RAW DATA FILE 5: research questions scratch (messy, agent must use these) ──
research_questions = """\
my questions before i start — rough draft
1. is the adult language SaaS market big enough for a one-person business to survive?
2. who are the real competitors and what are they actually bad at?
3. what trends are going to matter in the next 1-2 years?
4. who exactly is the customer — what do they look like, what do they want?
5. what should i actually build/do next?
"""
with open(os.path.join(BASE, "research/raw_data/my_questions_draft.txt"), "w") as f:
    f.write(research_questions)

print("Workspace generated successfully.")
print(f"Files created under {BASE}/")