import os
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic deeply nested design system project structure with distractors
dirs = [
    "design-system/tokens/color",
    "design-system/tokens/spacing",
    "design-system/tokens/typography",
    "design-system/components/button",
    "design-system/components/card",
    "design-system/components/modal",
    "design-system/components/badge",
    "design-system/components/avatar",
    "design-system/docs",
    "design-system/build/css",
    "design-system/build/tailwind",
    "design-system/scripts",
    "design-system/tests",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files — realistic but unrelated to the task
distractor_files = {
    "design-system/tokens/color/palette.json": '{"primary": "#3B82F6", "secondary": "#8B5CF6", "danger": "#EF4444"}',
    "design-system/tokens/spacing/scale.json": '{"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px"}',
    "design-system/tokens/typography/fonts.css": "body { font-family: 'Inter', sans-serif; font-size: 16px; }",
    "design-system/components/button/button.css": ".btn { padding: 8px 16px; cursor: pointer; }",
    "design-system/components/button/button.html": '<button class="btn btn-primary">Click me</button>',
    "design-system/components/card/card.css": ".card { box-shadow: 0 2px 8px rgba(0,0,0,0.1); padding: 16px; }",
    "design-system/components/modal/modal.css": ".modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; }",
    "design-system/components/badge/badge.html": '<span class="badge badge-info">New</span>',
    "design-system/components/avatar/avatar.css": ".avatar { width: 40px; height: 40px; overflow: hidden; }",
    "design-system/docs/contributing.md": "# Contributing\nPlease read the contribution guidelines before submitting a PR.",
    "design-system/docs/changelog.md": "# Changelog\n## v2.1.0\n- Added new badge variants\n## v2.0.0\n- Major redesign",
    "design-system/build/tailwind/tailwind.config.js": "module.exports = { content: ['./src/**/*.{html,js}'], theme: { extend: {} } }",
    "design-system/scripts/build.sh": "#!/bin/bash\nnpm run build:css && npm run build:js",
    "design-system/tests/snapshot.test.js": "describe('snapshot', () => { it('renders correctly', () => {}); });",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# The actual task input: a messy, informal component spec sheet
# This is what the agent must read and process
component_spec = """# Component Border Radius Spec Sheet
# (Draft — needs proper CSS + Tailwind output file generated)

Below are the corner radius requirements for each component in our design system.
Please generate the final reference file: border_radius_reference.json

Components:

1. PillBadge
   Shape: Full pill / circle

2. BlobCard
   Shape: Blob

3. LeafIcon
   Shape: Leaf

4. StandardCard
   All corners: 12px

5. HeroImage
   Top-left: 0px, Top-right: 40px, Bottom-right: 40px, Bottom-left: 0px

6. BrokenInput
   All corners: -5px
   (designer made a mistake, use the corrected value)

7. OverflowWidget
   All corners: 10500px
   (cap to maximum allowed value)

8. TabPanel
   Top-left: 16px, Top-right: 16px, Bottom-right: 0px, Bottom-left: 0px

9. RemUnit
   All corners specified as: 1.5rem
   (non-px unit — handle appropriately)
"""

with open(os.path.join(workspace, "design-system/docs/component_spec_draft.txt"), "w") as f:
    f.write(component_spec)

print("Workspace initialized.")
print("Task: Read the component spec draft and produce border_radius_reference.json")