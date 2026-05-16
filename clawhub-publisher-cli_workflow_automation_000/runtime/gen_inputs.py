import os
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# ─── Create realistic distractor files ───────────────────────────────────────
distractor_dirs = [
    "projects/analytics-skill/hooks",
    "projects/analytics-skill/tests",
    "projects/weather-skill/hooks",
    "projects/weather-skill/docs",
    "projects/legacy-tool/src",
    "projects/legacy-tool/config",
    "archive/old-releases/v0.1",
    "archive/old-releases/v0.2",
    "team-notes/sprint-12",
    "team-notes/sprint-13",
    "scripts",
    "configs",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

distractor_files = {
    "projects/analytics-skill/SKILL.md": textwrap.dedent("""\
        ---
        name: analytics-skill
        description: Provides analytics capabilities for data pipelines.
        hooks:
          on_invoke: hooks/invoke.js
        ---
        # Analytics Skill
        This skill connects to data warehouses and runs aggregations.
        """),
    "projects/analytics-skill/hooks/invoke.js": "module.exports = async (ctx) => { return ctx.run(); };",
    "projects/analytics-skill/README.md": "# Analytics Skill\nSee SKILL.md for details.",
    "projects/analytics-skill/tests/test_basic.js": "// basic test placeholder",
    "projects/weather-skill/SKILL.md": textwrap.dedent("""\
        ---
        name: weather-skill
        description: Fetches weather data for any location.
        hooks:
          on_invoke: hooks/weather.js
        ---
        # Weather Skill
        Uses public APIs to retrieve weather information.
        """),
    "projects/weather-skill/hooks/weather.js": "module.exports = async ({location}) => ({ temp: 72 });",
    "projects/weather-skill/README.md": "# Weather Skill\nFetches real-time weather.",
    "projects/weather-skill/docs/usage.md": "## Usage\nPass a location string to get temperature.",
    "projects/legacy-tool/src/main.py": "print('legacy tool')",
    "projects/legacy-tool/config/settings.json": '{"debug": true, "version": "0.0.1"}',
    "archive/old-releases/v0.1/bundle.zip": "",  # empty placeholder
    "archive/old-releases/v0.2/CHANGELOG.md": "## v0.2\n- Improved performance",
    "team-notes/sprint-12/standup.md": "- Fixed bugs in analytics-skill\n- Started weather-skill refactor",
    "team-notes/sprint-13/standup.md": "- Completed weather-skill\n- Planning summarizer-skill release",
    "scripts/deploy.sh": "#!/bin/bash\necho 'Deploying...'",
    "scripts/lint.sh": "#!/bin/bash\nnpm run lint",
    "configs/registry.json": '{"registry": "https://clawhub.example.com", "org": "acme-corp"}',
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ─── Create the BROKEN skill folder that the agent must fix ──────────────────
# Skill: "summarizer-skill" — has multiple problems:
#   1. SKILL.md has broken YAML frontmatter (missing 'description' field)
#   2. Hook reference points to a file that doesn't exist
#   3. A hook file that IS listed in hooks/ is completely blank
#   4. No README file at all
#   5. Extra junk files for realism

SKILL_DIR = os.path.join(WORKSPACE, "projects/summarizer-skill")
HOOKS_DIR = os.path.join(SKILL_DIR, "hooks")
os.makedirs(HOOKS_DIR, exist_ok=True)

# Problem 1 & 2: SKILL.md missing 'description', hooks reference a nonexistent file
with open(os.path.join(SKILL_DIR, "SKILL.md"), "w") as f:
    f.write(textwrap.dedent("""\
        ---
        name: summarizer-skill
        hooks:
          on_invoke: hooks/invoke.js
          on_error: hooks/error_handler.js
        ---
        # Summarizer Skill

        This skill takes a long piece of text and returns a concise summary.
        It uses a local model to perform the summarization without external API calls.

        ## Inputs
        - `text` (string): The text to summarize.
        - `max_length` (integer): Maximum number of words in the summary.

        ## Outputs
        - `summary` (string): The generated summary.
        """))

# Problem 3: hooks/invoke.js exists but is completely blank
with open(os.path.join(HOOKS_DIR, "invoke.js"), "w") as f:
    f.write("")  # intentionally blank

# Note: hooks/error_handler.js is referenced in SKILL.md but does NOT exist → broken reference
# Problem 4: No README.md at all

# Extra junk files for realism
with open(os.path.join(SKILL_DIR, "package.json"), "w") as f:
    f.write('{\n  "name": "summarizer-skill",\n  "version": "0.1.0",\n  "private": true\n}\n')

with open(os.path.join(SKILL_DIR, ".gitignore"), "w") as f:
    f.write("node_modules/\n.clawhub-publisher/\n*.zip\n")

with open(os.path.join(SKILL_DIR, "notes.txt"), "w") as f:
    f.write("TODO: finish writing error handler\nTODO: add description to SKILL.md\n")

with open(os.path.join(SKILL_DIR, "hooks/util.js"), "w") as f:
    f.write("// utility helpers\nmodule.exports = { truncate: (s, n) => s.slice(0, n) };\n")

print("Workspace generated successfully.")
print(f"Broken skill located at: {SKILL_DIR}")
print("Problems injected:")
print("  1. SKILL.md missing 'description' in frontmatter")
print("  2. hooks/error_handler.js referenced but missing")
print("  3. hooks/invoke.js is completely blank")
print("  4. No README.md present")