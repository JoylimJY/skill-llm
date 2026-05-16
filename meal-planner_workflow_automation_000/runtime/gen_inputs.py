import os
import random
from pathlib import Path

random.seed(42)

# Base meal-planner directory
base = Path.home() / "meal-planner"

# Create full directory structure
for d in ["weeks", "recipes", "shopping", "inventory", "templates", "archive"]:
    (base / d).mkdir(parents=True, exist_ok=True)

# ── memory.md ── (realistic, messy, has critical dietary info)
(base / "memory.md").write_text("""\
# Meal Planner Memory

## Household
- Adults: 2 (Alex, Jordan)
- Kids: 1 (Sam, age 7)
- Typical guests: occasional (grandparents ~1x/month)

## Dietary Restrictions
### Alex
- **ALLERGY (life-threatening): Tree nuts** (cashews, almonds, walnuts, pistachios — EpiPen required)
- Preference: dislikes fish

### Jordan
- **Intolerance: Lactose** — avoid cow dairy in large amounts (hard cheese OK in small portions, no milk/cream/ice cream)
- Preference: loves spicy food

### Sam (kid)
- Preference: picky — likes pasta, chicken, plain rice
- Dislikes: anything "green and mushy" (peas, cooked spinach)

## Budget
- Weekly grocery target: $120
- Preferred stores: Whole Foods (produce), Costco (bulk proteins), Trader Joe's (pantry staples)

## Cooking Skills
- Alex: intermediate
- Jordan: advanced (enjoys batch cooking on Sundays)

## Time Constraints
- Weeknights: max 30 min active cooking
- Weekends: up to 90 min

## Cuisine Preferences
- Favorites: Mediterranean, Mexican, Asian stir-fry
- Disliked: heavy cream-based sauces (Jordan's intolerance), anything with tree nuts

## Past Notes
- 2025-03-10: Thai peanut noodles — AVOID (peanuts border concern for Alex, family prefers caution)
- 2025-02-14: Chicken tikka masala with coconut milk (dairy-free sub) — huge hit
- 2025-01-20: Beef tacos — Sam loved them, make again
- 2024-12-05: Walnut brownie incident — Alex had reaction, NEVER again
""")

# ── inventory/pantry.md ── (partially stale, realistic)
(base / "inventory" / "pantry.md").write_text("""\
## Pantry — Updated 2025-03-15

### Grains & Pasta
| Item | Status | Notes |
|------|--------|-------|
| White rice | Full | 5 lb bag, Costco |
| Penne pasta | Full | 2 boxes |
| Quinoa | Low | ~1 cup left |
| Bread crumbs | Out | Need to buy |

### Canned Goods
| Item | Status | Notes |
|------|--------|-------|
| Diced tomatoes | Half | 3 cans |
| Coconut milk | Full | 4 cans |
| Chickpeas | Full | 4 cans |
| Black beans | Half | 2 cans |
| Chicken broth | Low | 1 box, opened |

### Spices & Condiments
| Item | Status | Notes |
|------|--------|-------|
| Olive oil | Full | large bottle |
| Soy sauce | Half | |
| Cumin | Full | |
| Paprika | Full | |
| Chili powder | Half | |
| Garlic powder | Full | |

### Pantry Staples
| Item | Status | Notes |
|------|--------|-------|
| All-purpose flour | Half | |
| Sugar | Full | |
| Salt | Full | |
""")

# ── inventory/fridge.md ── (current snapshot)
(base / "inventory" / "fridge.md").write_text("""\
## Fridge — Updated 2025-04-01

### Proteins
| Item | Amount | Expires |
|------|--------|---------|
| Eggs | 8 | Apr 10 |
| Ground beef | 1 lb | Apr 3 — USE SOON |

### Produce
| Item | Amount | Expires |
|------|--------|---------|
| Bell peppers | 2 red | Apr 5 |
| Onions | 3 | Apr 15 |
| Garlic | 1 head | Apr 20 |
| Lemons | 2 | Apr 8 |

### Dairy & Alternatives
| Item | Amount | Expires |
|------|--------|---------|
| Parmesan cheese | Half block | Apr 12 |
| Oat milk | 1 carton | Apr 6 — LOW |

### Leftovers
| Item | Amount | Expires |
|------|--------|---------|
| Cooked rice | 2 cups | Apr 3 — USE SOON |
""")

# ── A few saved recipes (distractors + useful references) ──

(base / "recipes" / "chicken-tikka-masala.md").write_text("""\
# Chicken Tikka Masala (Dairy-Free)

**Time:** Prep 15 min | Cook 30 min
**Serves:** 4 (easily doubled)
**Difficulty:** Medium
**Dietary:** dairy-free, gluten-free, nut-free

## Ingredients
- 1.5 lb chicken breast — substitute: chickpeas for vegetarian
- 2 cans coconut milk
- 1 can diced tomatoes
- 1 onion, diced
- 4 cloves garlic
- 2 tbsp tikka masala spice blend
- 1 tbsp olive oil

## Instructions
1. Sauté onion and garlic in olive oil
2. Add chicken, brown 5 min
3. Add spices, tomatoes, coconut milk
4. Simmer 25 min

## Notes
- Pairs well with: basmati rice, naan
- Storage: 4 days fridge, 3 months freezer
- Kid modification: use mild tikka spice for Sam

## History
- 2025-02-14: Made it, family loved it — Jordan said "make this monthly"
""")

(base / "recipes" / "beef-tacos.md").write_text("""\
# Beef Tacos

**Time:** Prep 10 min | Cook 15 min
**Serves:** 4
**Difficulty:** Easy
**Dietary:** gluten-free (corn tortillas), nut-free, dairy-free optional

## Ingredients
- 1 lb ground beef
- 1 packet taco seasoning (check label — no hidden nuts)
- 8 corn tortillas
- 1 onion, diced
- 1 bell pepper, diced
- Toppings: salsa, guacamole, lime

## Instructions
1. Brown beef with onion and pepper
2. Add taco seasoning and 1/4 cup water
3. Serve in corn tortillas with toppings

## Notes
- Pairs well with: black beans, rice
- Storage: meat filling 3 days fridge
- Kid modification: Sam loves this as-is

## History
- 2025-01-20: Big hit, Sam asked for seconds
""")

(base / "recipes" / "pasta-arrabiata.md").write_text("""\
# Pasta Arrabiata

**Time:** Prep 5 min | Cook 20 min
**Serves:** 4
**Difficulty:** Easy
**Dietary:** vegan, nut-free

## Ingredients
- 1 box penne pasta
- 1 can diced tomatoes
- 4 cloves garlic
- 2 tbsp olive oil
- 1 tsp chili flakes (adjust for Sam)
- Parmesan — optional garnish (small amount OK for Jordan)

## Instructions
1. Boil pasta per package
2. Sauté garlic in olive oil, add tomatoes and chili
3. Simmer 10 min, toss with pasta

## Notes
- Sam modification: no chili, add parmesan
- Storage: 3 days fridge

## History
- 2025-03-01: Quick weeknight win
""")

(base / "recipes" / "walnut-brownies.md").write_text("""\
# Walnut Brownies ⚠️ DO NOT MAKE

**Time:** Prep 10 min | Cook 25 min
**Serves:** 12
**Difficulty:** Easy
**Dietary:** contains TREE NUTS (walnuts) — UNSAFE FOR ALEX

## Ingredients
- 2 cups walnuts — ALLERGEN
- 2 cups chocolate chips
- 4 eggs

## Instructions
1. DO NOT MAKE THIS
2. Alex had a severe reaction — 2024-12-05

## Notes
- ARCHIVED for reference only, never serve to this household
""")

(base / "recipes" / "greek-chickpea-salad.md").write_text("""\
# Greek Chickpea Salad

**Time:** Prep 15 min | Cook 0 min
**Serves:** 4
**Difficulty:** Easy
**Dietary:** vegan, gluten-free, nut-free

## Ingredients
- 2 cans chickpeas, drained
- 1 cucumber, diced
- 1 bell pepper, diced
- 1/4 red onion
- 2 tbsp olive oil
- 1 lemon, juiced
- Cumin, paprika to taste

## Instructions
1. Combine all ingredients
2. Toss with olive oil and lemon

## Notes
- Storage: 3 days fridge (gets better overnight)
""")

# ── templates (distractors) ──
(base / "templates" / "quick-weeknight.md").write_text("""\
# Quick Weeknight Template

Use for busy weeknights — max 30 min total.

- Protein: pre-marinated or leftover
- Starch: rice (use batch-cooked) or pasta
- Veg: frozen or pre-chopped

## Sample
**Dinner:** Stir-fry protein + veg over rice | Prep: 15 min
""")

(base / "templates" / "batch-cooking-sunday.md").write_text("""\
# Sunday Batch Cooking Template

## Typical batch tasks:
- [ ] Cook 4 cups dry rice
- [ ] Roast sheet pan vegetables
- [ ] Marinate proteins for Mon-Wed
- [ ] Make one sauce/soup for lunches
""")

# ── archive (old weeks, distractors) ──
(base / "archive" / "2025-W10.md").write_text("""\
# Week 2025-W10

## Overview
- Budget target: $115
- Dietary focus: Reducing dairy
- Special events: None

## Monday
**Breakfast:** Oatmeal with oat milk | Prep: 5 min
**Lunch:** Chickpea salad | Prep: 10 min
**Dinner:** Chicken tikka masala | Prep: 15 min | Cook: 30 min

## Notes
- Spent $118, slightly over budget
- Sam refused chickpea salad
""")

(base / "archive" / "2025-W11.md").write_text("""\
# Week 2025-W11

## Overview
- Budget target: $120
- Special events: Grandparents visiting Saturday

## Monday
**Breakfast:** Eggs and toast | Prep: 10 min
**Lunch:** Leftover tikka masala | Prep: 2 min
**Dinner:** Beef tacos | Prep: 10 min | Cook: 15 min

## Notes
- Grandparents loved the beef tacos
- Under budget: $107
""")

# ── shopping (old list, distractor) ──
(base / "shopping" / "2025-03-24.md").write_text("""\
## Shopping List — 2025-03-24

### Produce
- [x] Onions (4) — stir-fry, tacos
- [x] Bell peppers (3) — tacos, salad

### Proteins
- [x] Ground beef (2 lb) — tacos, bolognese

### Pantry
- [x] Penne pasta (2 boxes)

**Budget estimate:** $65
**Actual spent:** $61
""")

# ── A stray file to test contextual awareness ──
(base / "notes.md").write_text("""\
# Misc Notes

- Jordan wants to try a new Mediterranean bowl recipe
- Sam's school has a nut-free policy — pack nut-free lunches always
- Grandparents coming April 19-20 (they are vegetarian!)
- Jordan's birthday is April 18 — plan something special
- Consider meal prepping more — work gets busy in Q2
""")

print("Workspace generated successfully.")
print(f"Base dir: {base}")
print("Files created:")
for f in sorted(base.rglob("*")):
    if f.is_file():
        print(f"  {f}")