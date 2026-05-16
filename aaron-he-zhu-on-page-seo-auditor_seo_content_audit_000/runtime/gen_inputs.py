#!/usr/bin/env python3
import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "memory/audits/on-page-seo-auditor",
    "memory/open-loops",
    "memory/decisions",
    "assets/css",
    "assets/js",
    "assets/images",
    "content/drafts",
    "content/published",
    "config",
    "scripts",
    "reports/2024-q1",
    "reports/2024-q2",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# distractor files
distractors = {
    "config/site.json": json.dumps({
        "site_name": "TrailPeak Gear",
        "domain": "https://trailpeak.example.com",
        "default_language": "en",
        "theme": "eco-minimal"
    }, indent=2),

    "config/seo-config.yaml": """\
default_title_suffix: " | TrailPeak Gear"
default_keywords: ["camping", "eco gear", "sustainable outdoor"]
sitemap_url: "/sitemap.xml"
robots_policy: "index,follow"
""",

    "content/drafts/tent-review-draft.md": """\
# Best Eco-Friendly Tents for 2024

Draft content for tent review page.
Target keyword: eco friendly camping tent

## Introduction
...
""",

    "content/published/sleeping-bags.html": """\
<!DOCTYPE html>
<html>
<head>
<title>Sustainable Sleeping Bags - TrailPeak Gear</title>
<meta name="description" content="Explore our range of eco-friendly sleeping bags made from recycled materials. Perfect for conscious campers who care about the environment. Shop now and save 20%.">
</head>
<body>
<h1>Eco-Friendly Sleeping Bags</h1>
<h2>Top Picks for 2024</h2>
<p>Content here...</p>
</body>
</html>
""",

    "assets/css/main.css": "body { font-family: sans-serif; } h1 { color: #2d6a4f; }",
    "assets/css/seo-preview.css": ".title-preview { font-size: 18px; color: #1a0dab; }",
    "assets/js/analytics.js": "console.log('TrailPeak Analytics loaded');",
    "assets/js/lazy-load.js": "// lazy load images",

    "reports/2024-q1/organic-traffic.csv": """\
page,sessions,bounce_rate,avg_position
/sleeping-bags,1200,0.65,8.2
/tents,800,0.70,12.5
/backpacks,950,0.60,6.1
""",

    "reports/2024-q2/keyword-rankings.csv": """\
keyword,position,change
eco camping gear,15,-3
sustainable backpack,22,+1
recycled sleeping bag,18,0
""",

    "scripts/generate-sitemap.py": """\
#!/usr/bin/env python3
# Placeholder sitemap generator
import datetime
print(f"Sitemap generated at {datetime.datetime.now()}")
""",

    "memory/open-loops/pending.md": """\
# Open Loops

- [ ] Fix duplicate title tags on /tents and /tents-2024
- [ ] Add schema markup to product pages
- [ ] Update meta descriptions for Q3 campaign
""",

    "memory/decisions/2024-06-15-keyword-strategy.md": """\
# Keyword Strategy Decision

**Date**: 2024-06-15
**Decision**: Focus on long-tail eco camping keywords
**Rationale**: Lower competition, higher conversion intent
""",
}

for path, content in distractors.items():
    full_path = workspace / path
    full_path.write_text(content)

# ── THE PROBLEM: the page to audit (served by mock server) ──────────────────
# This HTML has DELIBERATE SEO issues:
# 1. Title too long (78 chars) and keyword NOT at front
# 2. Meta description too short (82 chars) 
# 3. NO H1 tag at all
# 4. Skipped header levels (H2 → H4, no H3)
# 5. Multiple issues to find and prioritize
# 6. Images without alt text
# 7. Internal links with poor anchor text ("click here")

audit_page_html = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Ultimate Guide to Buying Camping Equipment for Your Next Outdoor Adventure Trip - TrailPeak</title>
    <meta name="description" content="Buy eco camping gear at TrailPeak. Best prices guaranteed.">
    <link rel="canonical" href="http://localhost:8765/eco-camping-gear">
</head>
<body>

    <h2>Welcome to TrailPeak Gear</h2>
    <p>We offer the best sustainable camping equipment. Our <a href="/about">click here</a> page tells you more about us.
    Looking for eco-friendly camping gear that doesn't cost the earth? You're in the right place.</p>

    <h2>Our Best Eco Camping Gear Picks</h2>
    <p>Whether you're a seasoned hiker or weekend warrior, our curated selection of recycled and sustainable
    camping equipment will elevate your outdoor experience. All products are certified by the Outdoor Gear
    Sustainability Council (OGSC) and made from post-consumer recycled materials.</p>

    <h4>Recycled Tents</h4>
    <p>Our tents are made from 100% recycled nylon. Lightweight, durable, and environmentally responsible.</p>

    <h4>Eco Sleeping Bags</h4>
    <p>Crafted from reclaimed goose down and recycled polyester shells. Warm to -10°C.</p>

    <h2>Why Choose Sustainable Camping Gear?</h2>
    <p>Traditional camping equipment production contributes significantly to pollution. By choosing recycled
    and sustainably-sourced materials, you reduce your carbon footprint without sacrificing performance.</p>

    <h4>Environmental Impact</h4>
    <p>Every purchase offsets 2kg of CO2 through our reforestation partnership.</p>

    <h2>Customer Reviews</h2>
    <p>Our customers love the quality and sustainability of our eco camping gear. <a href="/reviews">click here</a> to read more.</p>

    <img src="/images/eco-tent.jpg">
    <img src="/images/sleeping-bag-recycled.jpg">
    <img src="/images/backpack-green.jpg">

    <h2>Shop Now</h2>
    <p>Find the perfect eco camping gear for your next adventure. <a href="/shop">click here</a> to browse our full catalogue.</p>

</body>
</html>
"""

(workspace / "mock_page.html").write_text(audit_page_html)

# ── mock server script ───────────────────────────────────────────────────────
mock_server_script = """\
#!/usr/bin/env python3
from flask import Flask, Response
from pathlib import Path

app = Flask(__name__)
html_content = Path('/workspace/mock_page.html').read_text()

@app.route('/')
@app.route('/eco-camping-gear')
def serve_page():
    return Response(html_content, mimetype='text/html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765)
"""
(workspace / "scripts" / "mock_server.py").write_text(mock_server_script)

# ── task brief ────────────────────────────────────────────────────────────────
task_brief = """\
# SEO Audit Task

Target URL: http://localhost:8765/eco-camping-gear
Target Keyword: eco camping gear
Page Type: product/category landing page
"""
(workspace / "task_brief.txt").write_text(task_brief)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")