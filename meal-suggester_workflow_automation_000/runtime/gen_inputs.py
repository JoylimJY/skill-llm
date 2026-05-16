import os
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# --- Directory structure ---
dirs = [
    "meal-suggester/preferences",
    "meal-suggester/inventory",
    "meal-suggester/scripts",
    "meal-suggester/logs/2024",
    "meal-suggester/logs/2025",
    "meal-suggester/archive/recipes",
    "meal-suggester/archive/old-lists",
    "meal-suggester/config",
    "meal-suggester/docs",
    "meal-suggester/tmp",
    "meal-suggester/exports",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- SKILL.md (entry point) ---
skill_md = textwrap.dedent("""\
    ---
    name: meal-suggester
    description: Quick dinner companion blending taste profiles, inventory tracking, and learning-based recipe rotation. Use to generate ≤25‑minute meals, log ingredients, and build shopping suggestions that respect both your and your partner's preferences.
    ---

    # Meal Suggester Skill

    Suggest quick dinner recipes (≤25 min) tailored to your household's tastes and available ingredients.

    ## Features

    - **Daily suggestions at 19:00** via cron job
    - **Taste profiles** for you and your partner (preferences, dislikes, dietary needs)
    - **Ingredient inventory** — markdown-based kitchen stock tracker
    - **Learning system** — feedback improves future suggestions
    - **Recipe matching** — respects time, tastes, and available ingredients
    - **Ingredient tracking** — logs what you use to build a shopping list
    - **Variety** — 15+ recipes that rotate, no monotony

    ## Files

    - `SKILL.md` — this file
    - `README.md` — setup & usage
    - `preferences/user1.md` — first person's taste profile
    - `preferences/user2.md` — second person's taste profile
    - `inventory/stock.md` — current kitchen ingredients
    - `inventory/history.md` — past suggestions & feedback
    - `inventory/shopping-list.md` — suggested shopping list based on usage patterns
    - `scripts/suggest-meal.sh` — main suggestion script

    ## Usage

    ### Get a suggestion
    ```bash
    clawdbot skill run meal-suggester
    ```

    ### Log ingredients used
    After cooking, just tell me: "on a utilisé lardons, pois chiches, une carotte"
    I'll automatically update `stock.md` and track what needs reordering.

    ### Update inventory
    Add items to `inventory/stock.md` with quantities and categories.

    ### Provide feedback
    Edit `inventory/history.md` with what you cooked + feedback (liked/disliked/would-repeat).

    ### View shopping suggestions
    Check `inventory/shopping-list.md` for items that are running low or needed.

    ### View profiles
    Check `preferences/user1.md` and `preferences/user2.md` to see what the system knows about each user.

    ## How It Works

    1. **Reads current inventory** from `inventory/stock.md`
    2. **Checks preferences** from both taste profiles
    3. **Tracks usage** — you tell me what you used, I update stock
    4. **Suggests shopping** — when stock runs low, I build a shopping list
    5. **Generates recipe** that:
       - Uses ingredients you have on hand
       - Respects both people's preferences
       - Takes ≤25 minutes
       - Avoids dislikes
       - Rotates through variety (15+ recipes)
    6. **Logs suggestion** to history for learning

    ## Cron Schedule

    Daily at 19:00 (7 PM) — a reminder with a recipe idea lands in your chat.

    ## Feedback Loop

    - Try the recipe → tell me what you think + what you used
    - System learns from "I loved this" / "too spicy" / "we'd make this again"
    - Stock updates automatically
    - Shopping list builds itself
    - Next suggestions get smarter

    ---

    *A kitchen memory that learns and never gets boring.*
""")
with open(os.path.join(BASE, "meal-suggester", "SKILL.md"), "w") as f:
    f.write(skill_md)

# --- preferences/user1.md ---
user1_md = textwrap.dedent("""\
    # User 1 — Taste Profile

    ## Loves
    - Italian cuisine
    - Pasta, risotto
    - Garlic, olive oil
    - Chicken, salmon

    ## Dislikes
    - Extremely spicy food
    - Cilantro

    ## Dietary needs
    - None

    ## Notes
    - Prefers light dinners on weekdays
    - Enjoys experimenting with new flavors occasionally
""")
with open(os.path.join(BASE, "meal-suggester", "preferences", "user1.md"), "w") as f:
    f.write(user1_md)

# --- preferences/user2.md ---
user2_md = textwrap.dedent("""\
    # User 2 — Taste Profile

    ## Loves
    - Mediterranean food
    - Chickpeas, lentils
    - Feta cheese
    - Roasted vegetables

    ## Dislikes
    - Red meat
    - Very heavy sauces

    ## Dietary needs
    - Vegetarian (mostly)

    ## Notes
    - Likes quick stir-fries
    - Enjoys salads with protein
""")
with open(os.path.join(BASE, "meal-suggester", "preferences", "user2.md"), "w") as f:
    f.write(user2_md)

# --- inventory/stock.md (messy/realistic state before weekend trip) ---
stock_md = textwrap.dedent("""\
    # Kitchen Stock

    _Last updated: 2025-06-01_

    ## Proteins
    - lardons — 200g
    - chicken breast — 2 pieces
    - canned tuna — 2 cans
    - eggs — 6

    ## Vegetables & Legumes
    - pois chiches (canned) — 2 cans
    - carrot — 3
    - courgette — 2
    - onion — 4
    - garlic — 1 bulb
    - cherry tomatoes — 250g
    - spinach — 100g

    ## Grains & Pasta
    - penne — 500g
    - basmati rice — 1kg
    - couscous — 400g

    ## Dairy
    - feta cheese — 150g
    - parmesan — 80g
    - butter — 125g

    ## Pantry
    - olive oil — 500ml
    - canned tomatoes — 3 cans
    - vegetable stock cubes — 4
    - soy sauce — 200ml
    - cumin — full jar
    - paprika — full jar
    - salt, pepper — always stocked

    ## Fresh Herbs
    - flat-leaf parsley — small bunch
    - basil — potted plant (low)
""")
with open(os.path.join(BASE, "meal-suggester", "inventory", "stock.md"), "w") as f:
    f.write(stock_md)

# --- inventory/history.md (existing entries, more to be added by agent) ---
history_md = textwrap.dedent("""\
    # Suggestion & Feedback History

    ## 2025-05-30
    - **Suggested:** Penne arrabbiata
    - **Cooked:** Yes
    - **Feedback:** liked | would-repeat
    - **Ingredients used:** penne, canned tomatoes, garlic, olive oil, parsley

    ## 2025-05-28
    - **Suggested:** Chickpea & courgette stir-fry
    - **Feedback:** liked
    - **Ingredients used:** pois chiches, courgette, onion, cumin, olive oil

    ## 2025-05-25
    - **Suggested:** Tuna pasta salad
    - **Feedback:** disliked — too bland
    - **Ingredients used:** penne, canned tuna, cherry tomatoes, parmesan
""")
with open(os.path.join(BASE, "meal-suggester", "inventory", "history.md"), "w") as f:
    f.write(history_md)

# --- inventory/shopping-list.md (existing, partial) ---
shopping_list_md = textwrap.dedent("""\
    # Shopping List

    _Auto-generated from usage patterns_

    ## To restock
    - basil (potted, low)
    - parmesan (running low after pasta dishes)

    ## Optional
    - fresh mozzarella
    - sun-dried tomatoes
""")
with open(os.path.join(BASE, "meal-suggester", "inventory", "shopping-list.md"), "w") as f:
    f.write(shopping_list_md)

# --- scripts/suggest-meal.sh (stub, exists per SKILL.md) ---
suggest_sh = textwrap.dedent("""\
    #!/usr/bin/env bash
    # Meal suggester main script
    echo "Suggest a meal based on inventory and preferences..."
    # (stub - logic handled by clawdbot)
""")
with open(os.path.join(BASE, "meal-suggester", "scripts", "suggest-meal.sh"), "w") as f:
    f.write(suggest_sh)

# --- Distractor files ---

# logs/2024
with open(os.path.join(BASE, "meal-suggester", "logs", "2024", "november.log"), "w") as f:
    f.write("2024-11-01 19:00 Suggested: Risotto ai funghi\n2024-11-02 19:00 Suggested: Greek salad bowl\n")

with open(os.path.join(BASE, "meal-suggester", "logs", "2024", "december.log"), "w") as f:
    f.write("2024-12-24 19:00 Suggested: Salmon en papillote\n2024-12-31 19:00 Suggested: Lentil soup\n")

# logs/2025
with open(os.path.join(BASE, "meal-suggester", "logs", "2025", "january.log"), "w") as f:
    f.write("2025-01-15 19:00 Suggested: Couscous with roasted veg\n")

with open(os.path.join(BASE, "meal-suggester", "logs", "2025", "may.log"), "w") as f:
    f.write("2025-05-01 Suggested: Spinach omelette\n2025-05-10 Suggested: Pasta primavera\n")

# archive/recipes
with open(os.path.join(BASE, "meal-suggester", "archive", "recipes", "risotto.md"), "w") as f:
    f.write("# Risotto ai Funghi\nTime: 25 min\nIngredients: arborio rice, mushrooms, parmesan, butter, stock\n")

with open(os.path.join(BASE, "meal-suggester", "archive", "recipes", "lentil-soup.md"), "w") as f:
    f.write("# Lentil Soup\nTime: 20 min\nIngredients: lentils, onion, carrot, cumin, vegetable stock\n")

with open(os.path.join(BASE, "meal-suggester", "archive", "recipes", "greek-salad.md"), "w") as f:
    f.write("# Greek Salad Bowl\nTime: 10 min\nIngredients: cucumber, cherry tomatoes, feta, olives, olive oil\n")

# archive/old-lists
with open(os.path.join(BASE, "meal-suggester", "archive", "old-lists", "shopping-2024-12.md"), "w") as f:
    f.write("# Shopping List Dec 2024\n- arborio rice\n- mushrooms\n- salmon fillets\n- lentils\n")

# config
with open(os.path.join(BASE, "meal-suggester", "config", "cron.conf"), "w") as f:
    f.write("0 19 * * * clawdbot skill run meal-suggester\n")

with open(os.path.join(BASE, "meal-suggester", "config", "settings.yaml"), "w") as f:
    f.write("max_suggestion_time_minutes: 25\nrotation_min_recipes: 15\nnotify_channel: chat\n")

# docs
with open(os.path.join(BASE, "meal-suggester", "docs", "onboarding.md"), "w") as f:
    f.write("# Onboarding\nWelcome! Fill in your taste profiles and stock the kitchen inventory.\n")

# tmp (junk distractor)
with open(os.path.join(BASE, "meal-suggester", "tmp", "draft-recipe.txt"), "w") as f:
    f.write("DRAFT: Quick chickpea curry\nStatus: NOT REVIEWED\n")

# exports
with open(os.path.join(BASE, "meal-suggester", "exports", "week-summary-2025-05.json"), "w") as f:
    f.write('{"week":"2025-05","suggestions":["Penne arrabbiata","Chickpea stir-fry","Tuna pasta salad"],"avg_feedback":"liked"}\n')

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_, files in os.walk(os.path.join(BASE, "meal-suggester")):
    for fname in files:
        print(" ", os.path.join(root, fname).replace(BASE + "/", ""))