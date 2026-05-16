import os
import random
from pathlib import Path

random.seed(42)

home = Path("/root")

# Create distractor directories that should NOT be the workspace
distractor_dirs = [
    home / "documents" / "recipes_old",
    home / "documents" / "grocery_notes",
    home / "notes" / "food",
    home / "notes" / "misc",
    home / "projects" / "cooking_app" / "src",
    home / "projects" / "cooking_app" / "tests",
    home / "downloads" / "meal_pdfs",
    home / "desktop" / "random_stuff",
    home / "tmp" / "old_lists",
    home / "backup" / "2023_meals",
]

for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files with misleading content
distractor_files = {
    home / "documents" / "recipes_old" / "spaghetti.txt": "Spaghetti bolognese - my old recipe from 2019\nIngredients: pasta, beef, tomatoes",
    home / "documents" / "recipes_old" / "curry.txt": "Chicken curry recipe\nServes 4\nTakes forever",
    home / "documents" / "grocery_notes" / "last_week.txt": "Milk\nBread\nEggs\nButter",
    home / "documents" / "grocery_notes" / "random_list.md": "# Random grocery list\n- apples\n- oranges",
    home / "notes" / "food" / "ideas.txt": "Maybe try Thai food sometime\nBBQ on weekends?",
    home / "notes" / "food" / "budget.txt": "Trying to keep weekly food budget under $150",
    home / "notes" / "misc" / "todo.txt": "- Buy new pots\n- Check recipes online\n- Plan meals somehow",
    home / "projects" / "cooking_app" / "src" / "main.py": "# Cooking app - WIP\n# Not finished yet",
    home / "projects" / "cooking_app" / "tests" / "test_main.py": "# Tests for cooking app\n# TODO",
    home / "downloads" / "meal_pdfs" / "README.txt": "Downloaded some meal plan PDFs, need to organize",
    home / "desktop" / "random_stuff" / "note.txt": "Remember to buy groceries on Thursday",
    home / "tmp" / "old_lists" / "jan_list.txt": "Old January shopping list:\nPasta, sauce, chicken",
    home / "backup" / "2023_meals" / "week1.txt": "Old 2023 week 1 plan:\nMon: pizza\nTue: burgers",
    home / "backup" / "2023_meals" / "notes.txt": "These old meal plans didn't work well",
}

for filepath, content in distractor_files.items():
    filepath.write_text(content)

# Create the task specification file that the agent will read as their instructions
# This is the "business brief" given to the agent — messy, informal, realistic
task_brief = home / "meal_planning_request.txt"
task_brief.write_text("""Hi! I need help getting my meal planning organized for Week 11 of 2024.

Here's my situation:
- Family of 4 (two adults, two kids)
- Wednesday and Friday are hectic work nights — I need something FAST or we'll order out
- I want to do a big batch cook on Sunday so Monday lunch uses those leftovers
- Tuesday I want something vegetarian
- I hate mushrooms, and my kid is dairy-free

Please set up my meal workspace from scratch and plan out the week using these specific meals I like:

MEALS I WANT IN MY DATABASE:
1. Chicken Stir-Fry
   - Prep: 15 min, Cook: 15 min
   - Serves 4
   - Dairy-free, gluten-free (if using tamari)
   - Quick weeknight
   - Ingredients: chicken breast (500g), bell peppers (2), soy sauce (3 tbsp), sesame oil (1 tbsp), ginger (1 tsp), cornstarch (2 tbsp), vegetable oil (2 tbsp)

2. Lentil Soup
   - Prep: 10 min, Cook: 30 min
   - Serves 6
   - Vegetarian, vegan, dairy-free, gluten-free
   - Make ahead, freezer-friendly
   - Ingredients: red lentils (400g), onion (1), carrots (2), cumin (1 tsp), turmeric (1 tsp), vegetable stock (1.5L), lemon juice (2 tbsp), olive oil (2 tbsp)

3. Sheet Pan Salmon with Roasted Veg
   - Prep: 10 min, Cook: 25 min
   - Serves 4
   - Dairy-free, gluten-free
   - One-pot/sheet pan
   - Ingredients: salmon fillets (4), broccoli (1 head), cherry tomatoes (200g), olive oil (3 tbsp), lemon (1), garlic (3 cloves), paprika (1 tsp)

4. Black Bean Tacos
   - Prep: 10 min, Cook: 15 min
   - Serves 4
   - Vegetarian, vegan, dairy-free
   - Under 30 minutes
   - Ingredients: black beans (2 cans), corn tortillas (8), avocado (2), lime (1), red onion (1), cilantro (handful), cumin (1 tsp), smoked paprika (1 tsp)

WEEKLY PLAN I WANT:
- Sunday: Big batch Lentil Soup (make extra for Monday)
- Monday: Leftovers from Sunday (Lentil Soup)
- Tuesday: Black Bean Tacos (vegetarian night)
- Wednesday: Chicken Stir-Fry (quick — busy night)
- Thursday: Sheet Pan Salmon with Roasted Veg
- Friday: Takeout (too busy)
- Weekend: Flexible

After setting this up, please generate a shopping list for the week (shopping list file should be named week-11-shopping.md). I always have these pantry items so don't include them in my shopping list: salt, pepper, olive oil, garlic, cumin, smoked paprika, turmeric, paprika, soy sauce, sesame oil, cornstarch, vegetable oil, ginger.

Save my dietary info and dislikes somewhere too.
""")

print("Workspace generated successfully.")
print(f"Task brief at: {task_brief}")
print("Distractor files created in various subdirectories.")