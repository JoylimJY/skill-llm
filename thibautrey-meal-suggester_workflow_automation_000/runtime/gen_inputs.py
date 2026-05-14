import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# --- Create full skill directory structure ---
dirs = [
    "preferences",
    "inventory",
    "scripts",
    "logs",
    "archive/2024",
    "archive/2025/january",
    "archive/2025/february",
    "notes",
    "config",
    "tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- DISTRACTOR FILES ---

(WORKSPACE / "SKILL.md").write_text("""\
---
name: meal-suggester
description: Quick dinner companion blending taste profiles, inventory tracking, and learning-based recipe rotation.
---

# Meal Suggester Skill

Suggest quick dinner recipes (≤25 min) tailored to your household's tastes and available ingredients.

## Files

- `preferences/user1.md` — first person's taste profile
- `preferences/user2.md` — second person's taste profile
- `inventory/stock.md` — current kitchen ingredients
- `inventory/history.md` — past suggestions & feedback
- `inventory/shopping-list.md` — suggested shopping list based on usage patterns
- `scripts/suggest-meal.sh` — main suggestion script

## Usage

### Log ingredients used
After cooking, just tell me: "on a utilisé lardons, pois chiches, une carotte"
I'll automatically update `stock.md` and track what needs reordering.

### Provide feedback
Edit `inventory/history.md` with what you cooked + feedback (liked/disliked/would-repeat).

### View shopping suggestions
Check `inventory/shopping-list.md` for items that are running low or needed.

## How It Works

1. Reads current inventory from `inventory/stock.md`
2. Checks preferences from both taste profiles
3. Tracks usage — you tell me what you used, I update stock
4. Suggests shopping — when stock runs low, I build a shopping list
5. Generates recipe that uses ingredients on hand, respects preferences, takes ≤25 minutes
6. Logs suggestion to history for learning
""")

(WORKSPACE / "README.md").write_text("""\
# Meal Suggester Setup

Run `clawdbot skill run meal-suggester` to get a suggestion.
Cron job fires daily at 19:00.
Edit preferences in `preferences/` folder.
""")

(WORKSPACE / "scripts" / "suggest-meal.sh").write_text("""\
#!/bin/bash
# Main suggestion script
echo "Reading inventory..."
cat inventory/stock.md
echo "Checking preferences..."
cat preferences/user1.md
cat preferences/user2.md
echo "Suggestion: Pasta with tomato sauce (18 min)"
""")

(WORKSPACE / "scripts" / "update-stock.sh").write_text("""\
#!/bin/bash
# Helper to update stock after cooking
echo "Stock updated."
""")

(WORKSPACE / "logs" / "cron.log").write_text("""\
2025-01-15 19:00:01 - Suggestion: Pasta Carbonara
2025-01-16 19:00:01 - Suggestion: Stir-fry chicken
2025-01-17 19:00:01 - Suggestion: Omelette with herbs
""")

(WORKSPACE / "archive" / "2024" / "stock-dec.md").write_text("""\
# Stock December 2024
- pasta: 500g
- tomatoes: 4
- olive oil: 1 bottle
""")

(WORKSPACE / "archive" / "2025" / "january" / "history-jan.md").write_text("""\
# January 2025 History
- 2025-01-03: Pasta Carbonara — liked
- 2025-01-10: Chicken stir-fry — would-repeat
""")

(WORKSPACE / "archive" / "2025" / "february" / "shopping-feb.md").write_text("""\
# February 2025 Shopping
- eggs: needed
- bacon: needed
""")

(WORKSPACE / "notes" / "ideas.md").write_text("""\
# Recipe Ideas
- Try shakshuka next week
- Need to buy more chickpeas
- Consider vegetarian days on Tuesdays
""")

(WORKSPACE / "notes" / "allergies.md").write_text("""\
# Known Allergies
- user2: lactose intolerant (mild)
- user1: no known allergies
""")

(WORKSPACE / "config" / "settings.json").write_text("""\
{
  "suggestion_time": "19:00",
  "timezone": "Europe/Paris",
  "max_cook_time_minutes": 25,
  "variety_minimum": 15
}
""")

(WORKSPACE / "tmp" / "last-suggestion.txt").write_text("""\
Suggested: Spaghetti Aglio e Olio (20 min)
Date: 2025-02-10
""")

# --- USER PROFILES ---
(WORKSPACE / "preferences" / "user1.md").write_text("""\
# User1 Taste Profile

## Likes
- pasta dishes
- Mediterranean cuisine
- garlic, olive oil, lemon
- quick stir-fries

## Dislikes
- very spicy food
- cilantro

## Dietary
- no restrictions
- prefers low-sugar meals

## Favourite past meals
- Pasta Aglio e Olio
- Chicken with lemon and capers
""")

(WORKSPACE / "preferences" / "user2.md").write_text("""\
# User2 Taste Profile

## Likes
- vegetables
- legumes (chickpeas, lentils)
- mild flavours
- salads

## Dislikes
- heavy cream sauces
- very fatty meats

## Dietary
- lactose intolerant (avoid heavy dairy)
- occasional vegetarian

## Favourite past meals
- Chickpea curry (mild)
- Lentil soup
- Tabbouleh
""")

# --- STOCK (messy, realistic, with some items running low) ---
(WORKSPACE / "inventory" / "stock.md").write_text("""\
# Kitchen Stock
*Last updated: 2025-02-09*

## Proteins
- lardons (bacon bits): 200g
- chicken breast: 2 pieces
- eggs: 6
- canned tuna: 2 cans

## Legumes
- chickpeas (canned): 3 cans
- lentils (dried): 400g
- black beans: 1 can

## Vegetables
- carrots: 4
- onions: 3
- garlic: 1 head
- cherry tomatoes: 250g
- spinach: 1 bag (150g)
- zucchini: 2

## Pasta & Grains
- spaghetti: 500g
- rice: 1kg
- couscous: 300g

## Pantry
- olive oil: 1 bottle
- soy sauce: half bottle
- cumin: small jar
- paprika: small jar
- vegetable stock cubes: 3

## Dairy
- parmesan: 50g  ← LOW
- butter: 30g  ← LOW

## Fresh Herbs
- flat-leaf parsley: 1 bunch
""")

# --- HISTORY (existing entries, needs a new one added) ---
(WORKSPACE / "inventory" / "history.md").write_text("""\
# Suggestion History & Feedback

## 2025-02-05
- **Suggested:** Chickpea & Spinach Curry (22 min)
- **Cooked:** Yes
- **Feedback:** loved it
- **Would repeat:** yes
- **Ingredients used:** chickpeas (1 can), spinach (half bag), onions (1), garlic (2 cloves), cumin, vegetable stock

## 2025-02-07
- **Suggested:** Pasta Carbonara (18 min)
- **Cooked:** Yes
- **Feedback:** too rich, won't repeat
- **Would repeat:** no
- **Ingredients used:** spaghetti (250g), lardons (100g), eggs (2), parmesan (30g), butter (20g)

## 2025-02-08
- **Suggested:** Lemon Chicken Stir-fry (20 min)
- **Cooked:** No
- **Feedback:** not in the mood
- **Would repeat:** maybe
""")

# --- SHOPPING LIST (existing, needs updating) ---
(WORKSPACE / "inventory" / "shopping-list.md").write_text("""\
# Shopping List
*Auto-generated based on usage patterns*
*Last updated: 2025-02-07*

## Running Low / Out
- parmesan: nearly gone (used frequently)
- butter: nearly gone

## Regularly Used (restock soon)
- chickpeas (canned): used 1 can recently
- spinach: used frequently

## Notes
- Check stock of spaghetti before next purchase
""")

print("Workspace generated successfully.")
print(f"Files created in: {WORKSPACE}")