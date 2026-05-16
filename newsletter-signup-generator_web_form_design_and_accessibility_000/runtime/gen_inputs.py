import os
import random

random.seed(42)

workspace = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    ".claude",
    "src/components",
    "src/pages",
    "src/styles",
    "src/assets/images",
    "src/assets/fonts",
    "tests/unit",
    "tests/e2e",
    "docs/brand",
    "docs/legal",
    "config",
    "scripts",
    "public",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Project context file (MUST be read by agent) ─────────────────────────────
project_context = """\
# Project Context: Serenity Coaching Platform

## About
Serenity is a boutique online wellness coaching service helping time-poor executives
build sustainable mindfulness habits. The platform targets professionals aged 30–55
who have limited time and high skepticism toward generic wellness advice.

## Audience
- Primary: C-suite and senior managers, predominantly mobile users (68% mobile traffic)
- Pain points: No time, distrust of "fluffy" content, privacy-conscious
- Value: Practical, science-backed 5-minute daily practices

## Current Signup Incentive
Lead magnet: **"7-Day Executive Mindfulness Starter Kit"** (PDF, 24 pages)
- Sent immediately upon confirmed subscription
- Weekly newsletter thereafter: every Tuesday, 07:00 local time

## Existing Forms on the Page
- There is already an **inline referral form** embedded mid-page in the blog post body
  that collects emails for a friend-referral programme.

## Platform
Web (desktop + mobile). Mobile is primary.

## Privacy & Compliance
Operates in EU and California. GDPR and CCPA compliance mandatory.
Double opt-in is required by policy.

## Brand Voice
Direct, no-hype, evidence-based. Avoid exclamation marks in body copy.
"""
with open(os.path.join(workspace, ".claude/project-context.md"), "w") as f:
    f.write(project_context)

# ── Distractor files ─────────────────────────────────────────────────────────

# 1. Existing page with inline referral form (agent should NOT place competing form inline)
existing_page = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Serenity Blog</title></head>
<body>
  <header><nav><a href="/">Home</a></nav></header>
  <main>
    <article>
      <h1>5 Science-Backed Breathing Techniques for Busy Executives</h1>
      <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit...</p>

      <!-- EXISTING INLINE REFERRAL FORM — do not place new signup form here -->
      <section class="referral-form">
        <h2>Refer a Colleague</h2>
        <form id="referral" action="/api/refer" method="post">
          <label for="ref-email">Your colleague's email</label>
          <input type="email" id="ref-email" name="ref_email" placeholder="colleague@company.com">
          <button type="submit">Send Invite</button>
        </form>
      </section>

      <p>More article content here...</p>
    </article>
  </main>
  <footer><p>&copy; 2024 Serenity Coaching</p></footer>
</body>
</html>
"""
with open(os.path.join(workspace, "src/pages/blog-post.html"), "w") as f:
    f.write(existing_page)

# 2. Outdated/broken signup attempt (agent must NOT copy this; it has accessibility violations)
bad_signup = """\
<!-- OLD SIGNUP ATTEMPT — DO NOT USE: fails accessibility audit -->
<div class="signup-old">
  <input type="text" placeholder="Enter your email here..." name="email">
  <div onclick="submit()" style="background:blue;color:white;padding:5px 10px;cursor:pointer;">
    Go
  </div>
</div>
"""
with open(os.path.join(workspace, "src/components/signup-old.html"), "w") as f:
    f.write(bad_signup)

# 3. Brand guidelines
brand_guide = """\
# Serenity Brand Guidelines

## Colors
- Primary: #2D6A4F (forest green)
- Secondary: #74C69D (light mint)
- Neutral: #F8F9FA (off-white background)
- Text: #1B1B1B

## Typography
- Headings: 'Playfair Display', serif
- Body: 'Inter', sans-serif

## Tone
Scientific, calm, direct. No exclamation marks. No hype.

## Button Style
Rounded corners (border-radius: 4px). Padding: 12px 24px minimum.
"""
with open(os.path.join(workspace, "docs/brand/guidelines.md"), "w") as f:
    f.write(brand_guide)

# 4. Privacy policy stub
privacy_policy = """\
# Privacy Policy
Last updated: 2024-01-15

Serenity Coaching Ltd processes personal data in accordance with GDPR (EU) 2016/679
and the California Consumer Privacy Act (CCPA).

## Data We Collect
- Email address (for newsletter subscription)

## How We Use It
- Send the requested lead magnet
- Weekly newsletter (you may unsubscribe at any time)

## Your Rights
GDPR: Right to access, rectify, erase, port, restrict, object.
CCPA: Right to know, delete, opt-out.

Policy URL: https://serenitycoaching.com/privacy
"""
with open(os.path.join(workspace, "docs/legal/privacy-policy.md"), "w") as f:
    f.write(privacy_policy)

# 5. Config files (distractors)
with open(os.path.join(workspace, "config/site.json"), "w") as f:
    f.write('{"site_name": "Serenity Coaching", "locale": "en-EU", "double_optin": true}\n')

with open(os.path.join(workspace, "config/email-provider.json"), "w") as f:
    f.write('{"provider": "Mailchimp", "list_id": "abc123def", "double_optin": true}\n')

# 6. Existing footer (distractor showing footer already has something)
footer_html = """\
<footer class="site-footer">
  <div class="footer-links">
    <a href="/privacy">Privacy Policy</a>
    <a href="/terms">Terms of Service</a>
    <a href="/contact">Contact</a>
  </div>
  <p class="copyright">&copy; 2024 Serenity Coaching Ltd. All rights reserved.</p>
</footer>
"""
with open(os.path.join(workspace, "src/components/footer.html"), "w") as f:
    f.write(footer_html)

# 7. Partial styles (distractor)
with open(os.path.join(workspace, "src/styles/main.css"), "w") as f:
    f.write("""\
/* Serenity Coaching - Main Stylesheet */
:root {
  --color-primary: #2D6A4F;
  --color-secondary: #74C69D;
  --color-bg: #F8F9FA;
  --color-text: #1B1B1B;
  --font-heading: 'Playfair Display', serif;
  --font-body: 'Inter', sans-serif;
}
body { font-family: var(--font-body); color: var(--color-text); }
""")

# 8. Test stubs (distractors)
with open(os.path.join(workspace, "tests/unit/form.test.js"), "w") as f:
    f.write("// Unit tests for form validation — TODO\n")

with open(os.path.join(workspace, "tests/e2e/signup.spec.js"), "w") as f:
    f.write("// E2E tests for signup flow — TODO\n")

# 9. Scripts directory
with open(os.path.join(workspace, "scripts/deploy.sh"), "w") as f:
    f.write("#!/bin/bash\necho 'Deploy script placeholder'\n")

# 10. Public placeholder
with open(os.path.join(workspace, "public/robots.txt"), "w") as f:
    f.write("User-agent: *\nDisallow: /api/\n")

# 11. Another distractor: a CTA component that is NOT a signup form
cta_html = """\
<section class="cta-block">
  <h2>Book a Free Discovery Call</h2>
  <a href="/book" class="cta-button">Schedule Now</a>
</section>
"""
with open(os.path.join(workspace, "src/components/cta-discovery.html"), "w") as f:
    f.write(cta_html)

# 12. Fonts list
with open(os.path.join(workspace, "src/assets/fonts/fonts.txt"), "w") as f:
    f.write("Playfair Display - Google Fonts\nInter - Google Fonts\n")

print("Workspace generated successfully.")