import os
import random

random.seed(42)

workspace = "/workspace"

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    ".claude",
    ".cursor",
    "src/core",
    "src/analysis",
    "src/utils",
    "docs/marketing",
    "docs/internal",
    "config",
    "tests/unit",
    "tests/integration",
    "scripts",
    "design/mockups",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── realistic project-context.md ───────────────────────────────────────────
project_context = """\
# Project Context: CodeLens

## Product
CodeLens is a B2B SaaS static-analysis and code-review automation platform.
It integrates with GitHub, GitLab, and Bitbucket to surface security vulnerabilities,
style violations, and complexity hotspots inside pull requests.

## Audience
Primary ICP: engineering teams at mid-market software companies (50–500 engineers).
Secondary audience: CS / software-engineering students learning professional code-review
practices, and bootcamp graduates entering the industry.

## Pricing (current)
| Plan       | Price/mo (per seat) |
|------------|---------------------|
| Starter    | $12                 |
| Pro        | $29                 |
| Team       | $49                 |
| Enterprise | custom              |

Students are expected to start on the Pro plan with a discount applied.

## Notes
- Sales-assisted for Enterprise; self-serve for all other tiers.
- Annual billing gives 2 months free (on top of any discounts).
- We have no active student or education program yet.
"""

with open(os.path.join(workspace, ".claude/project-context.md"), "w") as f:
    f.write(project_context)

# ── distractor files ───────────────────────────────────────────────────────
distractors = {
    "src/core/analyzer.py": """\
# Core analysis engine
class Analyzer:
    def run(self, repo_url: str) -> dict:
        raise NotImplementedError
""",
    "src/analysis/complexity.py": """\
# Cyclomatic complexity module
def cyclomatic(ast_node):
    pass
""",
    "src/utils/cache.py": """\
import functools
lru = functools.lru_cache(maxsize=256)
""",
    "docs/marketing/q2_campaigns.md": """\
# Q2 Campaign Ideas
- LinkedIn ads targeting CTOs
- Sponsor GitHub Changelog newsletter
- Product Hunt launch (scheduled May)
""",
    "docs/internal/pricing_notes.txt": """\
Revisit pricing in Q3.
Consider usage-based add-ons for large Enterprise seats.
Annual discount: 2 months free currently.
""",
    "docs/internal/referral_draft.md": """\
# Referral Program (Draft)
Give $20 credit for each successful referral.
Referred user must upgrade within 30 days.
Status: not launched.
""",
    "config/feature_flags.yaml": """\
flags:
  dark_mode: true
  ai_suggestions: false
  student_portal: false
""",
    "tests/unit/test_analyzer.py": """\
import unittest
class TestAnalyzer(unittest.TestCase):
    def test_placeholder(self):
        self.assertTrue(True)
""",
    "tests/integration/test_github_hook.py": """\
# Integration test placeholder
def test_webhook_payload():
    pass
""",
    "scripts/deploy.sh": """\
#!/bin/bash
set -e
echo "Deploying CodeLens..."
docker build -t codelens:latest .
docker push codelens:latest
""",
    "design/mockups/pricing_page_v2.txt": """\
Mockup notes:
- Move 'Enterprise' to far right
- Add 'Most Popular' badge on Pro
- Student block placeholder below table
""",
    "config/stripe_config.json": """\
{
  "currency": "usd",
  "tax_behavior": "exclusive",
  "billing_scheme": "per_unit"
}
""",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace initialised.")
print("Files created:")
for p in distractors:
    print(f"  {p}")
print("  .claude/project-context.md")