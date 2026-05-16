import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create a realistic, deeply nested SaaS company website project structure
dirs = [
    "website/src/pages/legal",
    "website/src/pages/blog",
    "website/src/pages/pricing",
    "website/src/components/footer",
    "website/src/components/header",
    "website/src/components/modals",
    "website/src/assets/images",
    "website/src/assets/fonts",
    "website/config/seo",
    "website/config/i18n",
    "website/scripts/build",
    "website/scripts/deploy",
    "docs/internal",
    "docs/api",
    "compliance/drafts",
    "compliance/archive",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files — realistic but irrelevant to the task
distractor_files = {
    "website/src/pages/blog/gdpr-explained.md": """# GDPR Explained
A blog post about what GDPR means for businesses.
Published: 2024-01-15
""",
    "website/src/pages/pricing/index.html": """<!DOCTYPE html>
<html><head><title>Pricing - TaskFlow</title></head>
<body><h1>Simple, transparent pricing</h1></body></html>
""",
    "website/src/components/footer/footer.jsx": """import React from 'react';
export default function Footer() {
  return (
    <footer>
      <a href="/privacy">Privacy Policy</a>
      <a href="/terms">Terms of Service</a>
    </footer>
  );
}
""",
    "website/src/components/header/nav.jsx": """import React from 'react';
export default function Nav() {
  return <nav><a href="/">Home</a><a href="/pricing">Pricing</a></nav>;
}
""",
    "website/config/seo/robots.txt": """User-agent: *
Allow: /
Disallow: /admin/
""",
    "website/config/seo/sitemap.xml": """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.2">
  <url><loc>https://taskflow.io/</loc></url>
  <url><loc>https://taskflow.io/pricing</loc></url>
</urlset>
""",
    "website/config/i18n/en.json": """{
  "nav.home": "Home",
  "nav.pricing": "Pricing",
  "footer.privacy": "Privacy Policy",
  "footer.terms": "Terms of Service"
}
""",
    "website/config/i18n/de.json": """{
  "nav.home": "Startseite",
  "nav.pricing": "Preise",
  "footer.privacy": "Datenschutzerklärung",
  "footer.terms": "Nutzungsbedingungen"
}
""",
    "website/scripts/build/compile.sh": """#!/bin/bash
echo "Building website..."
npm run build
""",
    "website/scripts/deploy/push.sh": """#!/bin/bash
echo "Deploying to production..."
rsync -avz ./dist/ user@server:/var/www/
""",
    "docs/api/endpoints.md": """# API Endpoints
GET /api/v1/users
POST /api/v1/projects
DELETE /api/v1/tasks/:id
""",
    "docs/internal/onboarding.md": """# Onboarding Guide
Welcome to TaskFlow engineering.
See wiki for architecture overview.
""",
    "compliance/drafts/privacy_policy_draft.txt": """DRAFT - NOT FINAL
Privacy Policy for TaskFlow
Last updated: [DATE]
We collect: name, email, usage data.
We do not sell your data.
Contact: privacy@taskflow.io
""",
    "compliance/archive/old_terms_2022.txt": """ARCHIVED - DO NOT USE
Terms of Service v1.0 (2022)
Superseded by current terms.
""",
    "compliance/archive/old_privacy_2021.txt": """ARCHIVED
Old privacy policy from 2021.
No longer valid.
""",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content, encoding="utf-8")

# The "messy input" the agent must work from:
# A rough internal notes file that is clearly incomplete and unstructured —
# the agent must produce a proper structured document, NOT just clean up this file.
messy_input = workspace / "compliance" / "cookie_policy_raw_notes.txt"
messy_input.write_text("""INTERNAL NOTES - Cookie Policy - TaskFlow SaaS
Author: Sarah (Legal Coordinator)
Date: 2024-11-01

We need a cookie policy for TaskFlow. Users are mostly EU-based so GDPR applies.
TaskFlow is a B2B project management SaaS.

We use cookies for:
- keeping users logged in (session stuff)
- google analytics (we track page views, bounce rate)
- intercom chat widget
- A/B testing via optimizely
- some preferences like dark mode / language

Not sure how to organize this. Also not sure if the page should show up in Google.
Legal hasn't reviewed anything yet.

Need to put a link somewhere in the website footer probably.

Sarah
""", encoding="utf-8")

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")