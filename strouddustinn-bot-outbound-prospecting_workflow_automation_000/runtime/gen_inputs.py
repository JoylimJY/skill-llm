import os
import json
import stat

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure with distractor files ──────────────────────────────────
dirs = [
    "workspace/leads/archive",
    "workspace/leads/pending",
    "workspace/templates/email",
    "workspace/templates/social",
    "workspace/research/competitors",
    "workspace/research/market",
    "workspace/crm/exports",
    "workspace/crm/imports",
    "workspace/scripts/utils",
    "workspace/scripts/reports",
    "workspace/config",
    "workspace/logs",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────────
distractor_files = {
    "workspace/leads/archive/old_prospect_acme.json": json.dumps({
        "company": "Acme Corp", "status": "cold", "last_contact": "2023-01-10",
        "notes": "No response after 3 follow-ups"
    }, indent=2),
    "workspace/leads/archive/old_prospect_zenith.json": json.dumps({
        "company": "Zenith Solutions", "status": "closed-lost", "last_contact": "2023-06-15"
    }, indent=2),
    "workspace/leads/pending/queue.csv": "company,domain,priority\nRiverStone LLC,riverstone.com,low\nNovaBuild Inc,novabuild.io,medium",
    "workspace/templates/email/generic_intro.txt": (
        "Hi [Name],\n\nI wanted to reach out about [service].\n\nBest,\n[Your Name]"
    ),
    "workspace/templates/email/follow_up.txt": (
        "Hi [Name],\n\nJust following up on my previous message.\n\nBest,\n[Your Name]"
    ),
    "workspace/templates/social/linkedin_connect.txt": (
        "Hi [Name], I came across your profile and thought it would be great to connect."
    ),
    "workspace/research/competitors/analysis_2023.txt": (
        "Top competitors in AEC project management:\n1. Procore\n2. Autodesk Construction Cloud\n3. PlanGrid\nMarket share data pending."
    ),
    "workspace/research/market/tam_notes.txt": (
        "Total Addressable Market for AEC SaaS: ~$4.2B by 2026.\nKey growth driver: digital transformation in construction."
    ),
    "workspace/crm/exports/contacts_export_2024Q1.csv": (
        "id,name,title,company,email,last_activity\n"
        "1,Sarah Kim,VP Sales,BuildRight,skim@buildright.com,2024-01-05\n"
        "2,Tom Allen,CEO,FrameWorks,tallen@frameworks.net,2024-02-20"
    ),
    "workspace/crm/imports/template_schema.json": json.dumps({
        "required_fields": ["company", "contact_name", "title", "email_draft"],
        "optional_fields": ["phone", "linkedin_url", "notes"]
    }, indent=2),
    "workspace/config/settings.json": json.dumps({
        "search_engine": "mock_local",
        "fetch_timeout": 10,
        "output_dir": "workspace/leads/pending",
        "draft_format": "markdown"
    }, indent=2),
    "workspace/logs/activity_2024.log": (
        "2024-03-01 09:12 - Searched: site:linkedin.com Procore CEO\n"
        "2024-03-01 09:15 - Fetched: https://procore.com/about\n"
        "2024-03-01 09:20 - Draft saved: procore_outreach.md\n"
    ),
    "workspace/scripts/utils/dedupe.py": (
        "# Utility: deduplication of leads\ndef dedupe(leads):\n    seen = set()\n    return [l for l in leads if l['company'] not in seen and not seen.add(l['company'])]\n"
    ),
    "workspace/scripts/reports/weekly_summary.py": (
        "# Weekly summary generator\nimport json\nprint('Generating weekly prospecting summary...')\n"
    ),
}

for path, content in distractor_files.items():
    full_path = os.path.join("/", path)
    with open(full_path, "w") as f:
        f.write(content)

# ── Mock server script ─────────────────────────────────────────────────────────
mock_server_script = r"""
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

SEARCH_RESULTS = {
    "bridgepoint engineering group site:bridgepoint-eng.com": [
        {"url": "http://localhost:8765/homepage", "title": "Bridgepoint Engineering Group - Home", "snippet": "Civil and structural engineering firm serving the Pacific Northwest since 1998."}
    ],
    "bridgepoint engineering group official website": [
        {"url": "http://localhost:8765/homepage", "title": "Bridgepoint Engineering Group - Home", "snippet": "Civil and structural engineering firm serving the Pacific Northwest since 1998."},
        {"url": "http://localhost:8765/about", "title": "About Us - Bridgepoint Engineering Group", "snippet": "Learn about our 25-year history and team of licensed engineers."},
        {"url": "http://localhost:8765/blog", "title": "News & Insights - Bridgepoint Engineering Group", "snippet": "Read the latest from our team."}
    ],
    "bridgepoint engineering group news recent": [
        {"url": "http://localhost:8765/blog", "title": "Bridgepoint Blog - Recent News", "snippet": "Bridgepoint recently won a $14M contract for the Cascade River Bridge retrofit project."}
    ],
    "site:linkedin.com bridgepoint engineering group ceo": [
        {"url": "https://www.linkedin.com/in/marcus-holt-bridgepoint", "title": "Marcus Holt - CEO at Bridgepoint Engineering Group | LinkedIn", "snippet": "Marcus Holt is the Chief Executive Officer at Bridgepoint Engineering Group, based in Portland, OR."}
    ],
    "site:linkedin.com bridgepoint engineering group founder": [
        {"url": "https://www.linkedin.com/in/marcus-holt-bridgepoint", "title": "Marcus Holt - Founder & CEO at Bridgepoint Engineering Group | LinkedIn", "snippet": "Marcus Holt founded Bridgepoint Engineering Group in 1998."}
    ],
    "site:linkedin.com bridgepoint engineering group head of marketing": [
        {"url": "https://www.linkedin.com/in/diane-wu-bridgepoint", "title": "Diane Wu - Head of Marketing at Bridgepoint Engineering Group | LinkedIn", "snippet": "Diane Wu leads marketing and business development at Bridgepoint."}
    ],
    "bridgepoint engineering group services products": [
        {"url": "http://localhost:8765/services", "title": "Services - Bridgepoint Engineering Group", "snippet": "Structural analysis, civil infrastructure, environmental consulting, and project oversight."}
    ],
}

PAGES = {
    "/homepage": """
<html><body>
<h1>Bridgepoint Engineering Group</h1>
<p>A trusted civil and structural engineering partner since 1998, headquartered in Portland, Oregon.</p>
<p>We serve clients across the Pacific Northwest, specializing in bridge design, seismic retrofits, and urban infrastructure.</p>
<p>Our team of 87 licensed engineers delivers projects on time and within budget.</p>
<p>Recent highlight: We were awarded the $14M Cascade River Bridge retrofit contract in Q1 2024.</p>
<p>Contact us at info@bridgepoint-eng.com</p>
</body></html>
""",
    "/about": """
<html><body>
<h1>About Bridgepoint Engineering Group</h1>
<p>Founded in 1998 by Marcus Holt, Bridgepoint Engineering Group has grown from a 3-person consultancy to an 87-person firm.</p>
<p>We are licensed in Washington, Oregon, Idaho, and California.</p>
<p>Our project management currently relies on a combination of spreadsheets and legacy MS Project files, creating coordination overhead across field teams.</p>
<p>In 2023, we expanded our environmental consulting division with 12 new hires.</p>
<p>We pride ourselves on long-term client relationships, with 74% of revenue from repeat clients.</p>
</body></html>
""",
    "/blog": """
<html><body>
<h1>News & Insights</h1>
<article>
<h2>Bridgepoint Wins Cascade River Bridge Retrofit Contract - March 2024</h2>
<p>We are proud to announce the award of the $14M Cascade River Bridge retrofit, our largest single contract to date.</p>
<p>This project will require close coordination between 4 field teams and our Portland HQ office over an 18-month timeline.</p>
</article>
<article>
<h2>2023 Year in Review - January 2024</h2>
<p>2023 saw a 22% revenue increase and the addition of our environmental consulting division.</p>
<p>However, project delays due to siloed communication cost us an estimated 9% of billable hours.</p>
</article>
<article>
<h2>New Hire Announcement - December 2023</h2>
<p>Please welcome 12 new engineers and consultants joining our environmental division in Q4 2023.</p>
</article>
</body></html>
""",
    "/services": """
<html><body>
<h1>Our Services</h1>
<ul>
<li>Structural Engineering and Analysis</li>
<li>Civil Infrastructure Design</li>
<li>Seismic Retrofit and Rehabilitation</li>
<li>Environmental Consulting</li>
<li>Project Oversight and Management</li>
</ul>
<p>We manage multi-team projects using internal coordination tools built on spreadsheets and email chains.</p>
</body></html>
"""
}

@app.route('/search')
def search():
    query = request.args.get('q', '').lower().strip()
    results = []
    for key, val in SEARCH_RESULTS.items():
        if all(word in query for word in key.split() if len(word) > 2):
            results.extend(val)
    seen = set()
    unique = []
    for r in results:
        if r['url'] not in seen:
            seen.add(r['url'])
            unique.append(r)
    return jsonify({"results": unique[:5]})

@app.route('/fetch')
def fetch():
    url = request.args.get('url', '')
    for path, content in PAGES.items():
        if path in url or url.endswith(path):
            return content
    return "<html><body><p>Page not found</p></body></html>", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8765, debug=False)
"""

with open("/workspace/scripts/mock_server.py", "w") as f:
    f.write(mock_server_script)

# ── web_search tool script ─────────────────────────────────────────────────────
web_search_script = r"""#!/usr/bin/env python3
"""
web_search_script += r'''
import sys
import json
import urllib.request
import urllib.parse

if len(sys.argv) < 2:
    print(json.dumps({"error": "Usage: web_search <query>"}))
    sys.exit(1)

query = " ".join(sys.argv[1:])
encoded = urllib.parse.urlencode({"q": query})
url = f"http://localhost:8765/search?{encoded}"
try:
    with urllib.request.urlopen(url, timeout=5) as resp:
        data = json.loads(resp.read().decode())
        print(json.dumps(data, indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
'''

with open("/workspace/scripts/web_search", "w") as f:
    f.write(web_search_script)
os.chmod("/workspace/scripts/web_search", 0o755)

# ── web_fetch tool script ──────────────────────────────────────────────────────
web_fetch_script = r"""#!/usr/bin/env python3
"""
web_fetch_script += r'''
import sys
import urllib.request
import urllib.parse

if len(sys.argv) < 2:
    print("Usage: web_fetch <url>")
    sys.exit(1)

url = sys.argv[1]
# Reroute known domain to localhost mock
reroute_map = {
    "bridgepoint-eng.com/": "http://localhost:8765/homepage",
    "bridgepoint-eng.com": "http://localhost:8765/homepage",
    "about": "http://localhost:8765/about",
    "blog": "http://localhost:8765/blog",
    "services": "http://localhost:8765/services",
}
fetch_url = url
if "localhost:8765" not in url:
    for key, rerouted in reroute_map.items():
        if key in url:
            fetch_url = rerouted
            break

try:
    req = urllib.request.Request(fetch_url, headers={"User-Agent": "MockBrowser/1.0"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        print(resp.read().decode())
except Exception as e:
    print(f"Error fetching {fetch_url}: {e}")
    sys.exit(1)
'''

with open("/workspace/scripts/web_fetch", "w") as f:
    f.write(web_fetch_script)
os.chmod("/workspace/scripts/web_fetch", 0o755)

# ── Task brief file (business context only, no hints) ─────────────────────────
task_brief = """TARGET ACCOUNT: Bridgepoint Engineering Group
Domain: bridgepoint-eng.com

This account has been flagged as a high-priority prospect by the VP of Sales.
Please complete a full outreach package so the sales team can review before making contact.

Expected deliverable: bridgepoint_outreach.md
"""

with open("/workspace/leads/pending/TARGET_ACCOUNT.txt", "w") as f:
    f.write(task_brief)

print("Workspace generated successfully.")