import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "brand/research",
    "brand/mood_board",
    "brand/competitors",
    "product/specs",
    "product/roadmap",
    "marketing/campaigns",
    "marketing/social",
    "legal/trademarks",
    "ops/infra",
    "ops/monitoring",
    "data/raw",
    "data/processed",
    "docs/internal",
    "docs/external",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractor_files = {
    "brand/research/competitor_analysis.txt": (
        "Competitors in AI recipe space:\n"
        "- TasteAI (tasteai.com) - Series A, $5M raised\n"
        "- RecipeBot (recipebot.io) - YC W22\n"
        "- ChefMind (chefmind.ai) - stealth mode\n"
        "Notes: Most .com in food-AI space already taken. Need creative naming.\n"
    ),
    "brand/research/naming_brainstorm_raw.txt": (
        "Initial brainstorm - NOT verified:\n"
        "flavr, yumly, recipy, savorai, dishcraft, cookgenius, mealbot,\n"
        "spoonful, forkwise, pantrypal, cuisineiq, bitesize, chompai,\n"
        "grubgenius, tastecraft, plately, spoonio, noshly, culinaryai\n"
        "** domain availability NOT checked yet **\n"
    ),
    "brand/mood_board/fonts.txt": "Font candidates: Playfair Display, Lora, Nunito\n",
    "brand/mood_board/colors.txt": "Palette: #FF6B35 (Tangerine), #2EC4B6 (Teal), #FFFFFF\n",
    "brand/competitors/market_map.json": json.dumps({
        "tier1": ["yummly.com", "allrecipes.com", "foodnetwork.com"],
        "tier2": ["sidechef.com", "mealime.com", "paprika.com"],
        "ai_native": ["plantjammer.com", "chef.ai", "whisk.com"],
    }, indent=2),
    "product/specs/mvp_features.md": (
        "# MVP Feature List\n"
        "1. Ingredient-based recipe search\n"
        "2. Dietary restriction filtering (vegan, gluten-free, keto)\n"
        "3. AI-powered substitution suggestions\n"
        "4. Weekly meal plan generation\n"
        "5. Grocery list export\n"
    ),
    "product/roadmap/q3_2025.txt": (
        "Q3 Goals:\n"
        "- Launch beta with 500 users\n"
        "- Finalize brand name and domain\n"
        "- File trademark for chosen brand\n"
        "- Set up social handles\n"
    ),
    "marketing/campaigns/launch_ideas.txt": (
        "Launch campaign concepts:\n"
        "- 'Cook Smarter' — focus on AI angle\n"
        "- 'No More Boring Dinners' — emotional hook\n"
        "- 'Your Pantry, Reinvented' — ingredient-first messaging\n"
    ),
    "marketing/social/handle_availability.txt": (
        "Social handle research (Instagram/Twitter):\n"
        "@flavrai - available\n"
        "@savorly - taken\n"
        "@dishiq - available\n"
        "@mealcraftai - available\n"
        "Note: domain availability still needs to be verified separately\n"
    ),
    "legal/trademarks/prior_art_notes.txt": (
        "USPTO preliminary search notes:\n"
        "- 'Savory AI' - possible conflict with SavoryAI LLC (Class 43)\n"
        "- 'FlavrAI' - no exact match found\n"
        "- 'DishCraft' - conflict with DishCraft Inc (Class 21, kitchenware)\n"
        "- Always confirm with IP attorney before filing\n"
    ),
    "ops/infra/stack_notes.txt": (
        "Planned infra stack:\n"
        "- Frontend: Next.js on Vercel\n"
        "- Backend: FastAPI on Fly.io\n"
        "- DB: Supabase (Postgres)\n"
        "- ML: Modal for inference\n"
        "- CDN: Cloudflare\n"
    ),
    "ops/monitoring/alerts_config.yaml": (
        "alerts:\n"
        "  - name: api_latency\n"
        "    threshold_ms: 500\n"
        "    channel: slack-ops\n"
        "  - name: error_rate\n"
        "    threshold_pct: 1.0\n"
        "    channel: slack-oncall\n"
    ),
    "data/raw/user_survey_snippets.txt": (
        "Survey Q: 'What would you name an AI cooking assistant?'\n"
        "Responses (n=47):\n"
        "- 'Something with Chef or Cook in the name'\n"
        "- 'Make it sound smart but friendly'\n"
        "- 'Avoid gimmicky robot names'\n"
        "- 'FlavourBot, MealMind, RecipeGenius'\n"
        "- 'Keep it short, max 8 chars'\n"
    ),
    "docs/internal/brand_brief.md": (
        "# Brand Brief: AI Recipe App\n\n"
        "## Target Audience\nMillennials and Gen-Z home cooks, 25-40, urban, health-conscious.\n\n"
        "## Brand Personality\nWarm, intelligent, approachable, modern.\n\n"
        "## Naming Criteria\n"
        "- Short (ideally ≤10 characters)\n"
        "- Memorable and pronounceable\n"
        "- Evokes food, intelligence, or discovery\n"
        "- Domain must be available (.com, .ai, or .io preferred)\n\n"
        "## Timeline\nBrand name decision needed by end of sprint (2 weeks).\n"
    ),
    "docs/external/press_kit_draft.txt": (
        "[DRAFT - DO NOT DISTRIBUTE]\n"
        "Company: [NAME TBD]\n"
        "Tagline: 'The kitchen intelligence that knows your pantry.'\n"
        "Founded: 2025\n"
        "HQ: San Francisco, CA\n"
        "Contact: press@[DOMAIN TBD]\n"
    ),
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# ── The real check_domains.sh script (deterministic mock) ──────────────────
# This script simulates whois + DNS cross-verification with deterministic
# outcomes based on domain name hashing, so the sandbox is reproducible.
# The output format matches exactly what the SKILL.md specifies.

check_domains_script = r"""#!/usr/bin/env bash
# check_domains.sh — Domain availability checker
# Uses whois + DNS NS + DNS A cross-verification.
# Waits 1 second between queries to avoid rate limiting.

set -euo pipefail

# Deterministic "database" of domain verdicts for sandbox environment.
# In production this uses real whois + dig; here we simulate realistic outcomes.
declare -A DOMAIN_DB=(
    # .com food/AI names - most taken
    ["flavrai.com"]="AVAILABLE"
    ["savorly.com"]="TAKEN"
    ["dishiq.com"]="AVAILABLE"
    ["mealcraftai.com"]="AVAILABLE"
    ["recipemind.com"]="TAKEN"
    ["cookgenius.com"]="TAKEN"
    ["pantrypal.com"]="TAKEN"
    ["forkwise.com"]="AVAILABLE"
    ["spoonful.com"]="TAKEN"
    ["bitesize.com"]="TAKEN"
    ["chompai.com"]="AVAILABLE"
    ["noshly.com"]="TAKEN"
    ["plately.com"]="TAKEN"
    ["cuisineiq.com"]="TAKEN"
    ["tastecraft.com"]="TAKEN"
    ["grubgenius.com"]="TAKEN"
    ["mealbot.com"]="TAKEN"
    ["culinaryai.com"]="TAKEN"
    ["dishcraft.com"]="TAKEN"
    # .ai TLD
    ["flavr.ai"]="TAKEN"
    ["savorly.ai"]="AVAILABLE"
    ["dishiq.ai"]="TAKEN"
    ["forkwise.ai"]="AVAILABLE"
    ["chompai.ai"]="TAKEN"
    ["recipemind.ai"]="AVAILABLE"
    ["cookgenius.ai"]="LIKELY_TAKEN"
    ["pantrypal.ai"]="AVAILABLE"
    ["mealcraft.ai"]="AVAILABLE"
    ["tastecraft.ai"]="TAKEN"
    # .io TLD
    ["flavrai.io"]="TAKEN"
    ["savorly.io"]="TAKEN"
    ["dishiq.io"]="AVAILABLE"
    ["forkwise.io"]="TAKEN"
    ["chompai.io"]="AVAILABLE"
    ["recipemind.io"]="TAKEN"
    ["pantrypal.io"]="TAKEN"
    ["mealcraft.io"]="LIKELY_TAKEN"
    ["tastecraft.io"]="AVAILABLE"
    ["grubgenius.io"]="UNKNOWN"
    # .net
    ["flavrai.net"]="AVAILABLE"
    ["savorly.net"]="TAKEN"
    ["dishiq.net"]="AVAILABLE"
    # .org
    ["flavrai.org"]="TAKEN"
    ["mealcraftai.org"]="AVAILABLE"
)

check_single() {
    local domain="$1"
    local verdict="${DOMAIN_DB[$domain]:-UNKNOWN}"

    case "$verdict" in
        AVAILABLE)
            echo "✅ AVAILABLE   $domain"
            ;;
        TAKEN)
            echo "❌ TAKEN       $domain"
            ;;
        LIKELY_TAKEN)
            echo "⚠️ LIKELY TAKEN $domain"
            ;;
        UNKNOWN|*)
            echo "❓ UNKNOWN     $domain"
            ;;
    esac

    # Rate limiting: wait 1 second between queries
    sleep 1
}

# Accept domains from args or stdin
if [ $# -gt 0 ]; then
    DOMAINS=("$@")
else
    # Read from stdin, split on whitespace/newlines
    read -ra DOMAINS <<< "$(cat | tr '\n' ' ')"
fi

if [ ${#DOMAINS[@]} -eq 0 ]; then
    echo "Usage: $0 domain1.com domain2.ai ..." >&2
    exit 1
fi

echo "Checking ${#DOMAINS[@]} domain(s)..."
echo "---"

for domain in "${DOMAINS[@]}"; do
    check_single "$domain"
done

echo "---"
echo "Done."
"""

script_path = workspace / "scripts" / "check_domains.sh"
script_path.write_text(check_domains_script)

print("Workspace initialized successfully.")
print(f"Files created: {len(distractor_files) + 1} (including check_domains.sh)")