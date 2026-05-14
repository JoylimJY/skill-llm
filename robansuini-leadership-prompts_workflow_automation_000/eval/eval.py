import sys
import json
import subprocess
from pathlib import Path

workspace = sys.argv[1]
checks = []
passed_all = True

def add_check(name, passed, detail):
    global passed_all
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# --- Load prompts.json ---
prompts_path = Path(workspace) / "prompts.json"
try:
    with open(prompts_path, "r") as f:
        prompts = json.load(f)
    add_check("prompts.json is valid JSON", True, f"Loaded {len(prompts)} prompts.")
except FileNotFoundError:
    add_check("prompts.json is valid JSON", False, "prompts.json not found.")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)
except json.JSONDecodeError as e:
    add_check("prompts.json is valid JSON", False, f"JSON parse error: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# --- Check total count is 29 ---
total_count = len(prompts)
add_check(
    "Total prompt count is 29",
    total_count == 29,
    f"Found {total_count} prompts, expected 29."
)

# --- Helper: find new prompts ---
ORIGINAL_IDS = {
    "one-on-one-underperformer", "one-on-one-star-retention", "one-on-one-skip-level",
    "one-on-one-career-goals", "team-health-conflict", "team-health-post-layoff",
    "team-health-remote-disconnect", "team-health-rough-quarter", "incident-retro-blameless",
    "incident-retro-repeat", "incident-retro-exec-comms", "tech-strategy-build-vs-buy",
    "tech-strategy-quarterly-review", "tech-strategy-architecture-review", "tech-strategy-tech-debt",
    "hiring-job-description", "hiring-interview-debrief", "hiring-closing-candidate",
    "career-dev-promotion", "career-dev-feedback", "career-dev-pip", "career-dev-ic-to-lead",
    "stakeholder-exec-update", "stakeholder-saying-no", "stakeholder-reorg-comms",
    "stakeholder-cross-functional"
}
new_prompts = [p for p in prompts if p.get("id") not in ORIGINAL_IDS]
add_check(
    "Exactly 3 new prompts added",
    len(new_prompts) == 3,
    f"Found {len(new_prompts)} new prompts (expected 3). IDs: {[p.get('id') for p in new_prompts]}"
)

# --- Check all original prompts are intact ---
original_ids_present = {p.get("id") for p in prompts if p.get("id") in ORIGINAL_IDS}
add_check(
    "All 26 original prompts preserved",
    len(original_ids_present) == 26,
    f"Original prompts present: {len(original_ids_present)}/26."
)

# --- Schema validation for all new prompts ---
REQUIRED_FIELDS = {"id", "category", "title", "prompt", "context", "output_format", "example"}
schema_errors = []
for p in new_prompts:
    missing = REQUIRED_FIELDS - set(p.keys())
    if missing:
        schema_errors.append(f"Prompt '{p.get('id', 'UNKNOWN')}' missing fields: {missing}")
    for field in REQUIRED_FIELDS:
        if field in p and (not isinstance(p[field], str) or not p[field].strip()):
            schema_errors.append(f"Prompt '{p.get('id', 'UNKNOWN')}' has empty/non-string field: {field}")

add_check(
    "All new prompts have required schema fields",
    len(schema_errors) == 0,
    f"Schema errors: {schema_errors}" if schema_errors else "All required fields present and non-empty."
)

# --- Check category assignments ---
category_checks = {
    "1-on-1 Prep": False,
    "Team Health": False,
    "Stakeholder Communication": False
}
for p in new_prompts:
    cat = p.get("category", "")
    if cat in category_checks:
        category_checks[cat] = True

all_cats_correct = all(category_checks.values())
add_check(
    "New prompts cover all three required categories",
    all_cats_correct,
    f"Category coverage: { {k: ('FOUND' if v else 'MISSING') for k, v in category_checks.items()} }"
)

# --- Check IDs follow kebab-case naming convention with category prefix ---
import re
id_pattern = re.compile(r'^[a-z][a-z0-9]*(-[a-z0-9]+)+$')
id_errors = []
for p in new_prompts:
    pid = p.get("id", "")
    if not id_pattern.match(pid):
        id_errors.append(f"ID '{pid}' does not follow kebab-case convention.")

add_check(
    "New prompt IDs follow kebab-case convention",
    len(id_errors) == 0,
    f"ID errors: {id_errors}" if id_errors else "All IDs are valid kebab-case."
)

# --- Check prompts contain {variable} placeholders ---
placeholder_pattern = re.compile(r'\{[^}]+\}')
placeholder_errors = []
for p in new_prompts:
    prompt_text = p.get("prompt", "")
    example_text = p.get("example", "")
    if not placeholder_pattern.search(prompt_text):
        placeholder_errors.append(f"Prompt '{p.get('id')}' has no {{variable}} placeholders in 'prompt' field.")
    # Example should NOT have unresolved placeholders (it should be filled in)
    if placeholder_pattern.search(example_text):
        # This is acceptable - the example might still show filled-in context
        pass

add_check(
    "New prompts contain {variable} placeholders in prompt text",
    len(placeholder_errors) == 0,
    f"Placeholder errors: {placeholder_errors}" if placeholder_errors else "All prompts have placeholder variables."
)

# --- Check example field looks like a filled-in instance (not identical to prompt) ---
example_errors = []
for p in new_prompts:
    prompt_text = p.get("prompt", "")
    example_text = p.get("example", "")
    if example_text.strip() == prompt_text.strip():
        example_errors.append(f"Prompt '{p.get('id')}': 'example' is identical to 'prompt' (should be filled-in).")
    if len(example_text.strip()) < 30:
        example_errors.append(f"Prompt '{p.get('id')}': 'example' is too short (< 30 chars).")

add_check(
    "New prompt 'example' fields are filled-in instances (not copies of prompt)",
    len(example_errors) == 0,
    f"Example errors: {example_errors}" if example_errors else "All example fields are properly filled in."
)

# --- CLI Integration: `list` command shows new categories ---
try:
    result = subprocess.run(
        ["node", "scripts/leadership-prompts.js", "list"],
        cwd=workspace,
        capture_output=True, text=True, timeout=10
    )
    list_output = result.stdout
    add_check(
        "CLI 'list' command executes successfully",
        result.returncode == 0,
        f"stdout: {list_output[:300]} stderr: {result.stderr[:100]}"
    )
except Exception as e:
    add_check("CLI 'list' command executes successfully", False, str(e))

# --- CLI Integration: `show` command works for each new prompt ---
cli_show_errors = []
for p in new_prompts:
    pid = p.get("id", "")
    try:
        result = subprocess.run(
            ["node", "scripts/leadership-prompts.js", "show", pid],
            cwd=workspace,
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0 or "Prompt not found" in result.stdout:
            cli_show_errors.append(f"'show {pid}' failed: {result.stdout[:100]}")
        elif p.get("title", "") not in result.stdout:
            cli_show_errors.append(f"'show {pid}' output doesn't include title: {p.get('title')}")
    except Exception as e:
        cli_show_errors.append(f"'show {pid}' threw exception: {e}")

add_check(
    "CLI 'show' command works for all 3 new prompts",
    len(cli_show_errors) == 0,
    f"CLI show errors: {cli_show_errors}" if cli_show_errors else "All new prompts retrievable by ID."
)

# --- CLI Integration: `category` command returns new prompts ---
cli_cat_errors = []
for cat in ["1-on-1 Prep", "Team Health", "Stakeholder Communication"]:
    try:
        result = subprocess.run(
            ["node", "scripts/leadership-prompts.js", "category", cat],
            cwd=workspace,
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            cli_cat_errors.append(f"'category \"{cat}\"' exited with code {result.returncode}")
        elif "No prompts in category" in result.stdout:
            cli_cat_errors.append(f"'category \"{cat}\"' returned no results.")
        else:
            # Check that the new prompt for this category is listed
            for p in new_prompts:
                if p.get("category") == cat:
                    if p.get("id") not in result.stdout and p.get("title", "") not in result.stdout:
                        cli_cat_errors.append(f"New prompt '{p.get('id')}' not in 'category {cat}' output.")
    except Exception as e:
        cli_cat_errors.append(f"'category \"{cat}\"' threw exception: {e}")

add_check(
    "CLI 'category' command returns new prompts in correct categories",
    len(cli_cat_errors) == 0,
    f"CLI category errors: {cli_cat_errors}" if cli_cat_errors else "All new prompts found in correct categories."
)

# --- CLI Integration: `search` command finds new prompts by keyword ---
search_keywords = ["onboard", "burnout", "budget"]
search_errors = []
for kw in search_keywords:
    try:
        result = subprocess.run(
            ["node", "scripts/leadership-prompts.js", "search", kw],
            cwd=workspace,
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            search_errors.append(f"'search {kw}' failed with code {result.returncode}")
        elif "No prompts found" in result.stdout:
            search_errors.append(f"'search {kw}' returned no results — new prompts may not contain this keyword.")
    except Exception as e:
        search_errors.append(f"'search {kw}' threw exception: {e}")

add_check(
    "CLI 'search' finds new prompts by relevant keywords (onboard, burnout, budget)",
    len(search_errors) == 0,
    f"Search errors: {search_errors}" if search_errors else "All keyword searches returned results."
)

# --- Compute score ---
total_checks = len(checks)
passed_checks = sum(1 for c in checks if c["passed"])
score = passed_checks / total_checks if total_checks > 0 else 0.0

print(json.dumps({
    "passed": passed_all,
    "score": round(score, 3),
    "checks": checks
}, indent=2))