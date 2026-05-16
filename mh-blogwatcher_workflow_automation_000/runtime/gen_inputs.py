import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "team/content/newsletters",
    "team/content/social",
    "team/content/reports/q1",
    "team/content/reports/q2",
    "team/devrel/outreach",
    "team/devrel/drafts",
    "infra/monitoring/alerts",
    "infra/monitoring/logs",
    "infra/scripts",
    "archive/2023/feeds",
    "archive/2023/digests",
    "archive/2024/feeds",
    "tmp/scratch",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files (realistic but irrelevant)
distractor_files = {
    "team/content/newsletters/issue_42.md": "# Newsletter Issue 42\nThis week in tech...\n",
    "team/content/social/twitter_drafts.txt": "Draft 1: Excited to share our new post!\nDraft 2: Check out this article!\n",
    "team/content/reports/q1/summary.csv": "source,articles,reads\nblog_a,12,10\nblog_b,7,7\n",
    "team/content/reports/q2/summary.csv": "source,articles,reads\nblog_c,15,9\nblog_d,3,3\n",
    "team/devrel/outreach/contacts.json": json.dumps({"contacts": ["alice@example.com", "bob@example.com"]}),
    "team/devrel/drafts/post_draft.md": "# Why We Track Blogs\nContent monitoring is essential...\n",
    "infra/monitoring/alerts/config.yaml": "alerts:\n  - name: high_cpu\n    threshold: 90\n",
    "infra/monitoring/logs/access.log": "2024-01-01 12:00:00 GET /feed 200\n2024-01-01 12:01:00 GET /feed 200\n",
    "infra/scripts/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "archive/2023/feeds/old_feed_list.txt": "https://old-blog.example.com/feed\nhttps://archive-news.example.com/rss\n",
    "archive/2023/digests/digest_dec.txt": "December digest: 23 articles reviewed.\n",
    "archive/2024/feeds/feed_registry.json": json.dumps({"feeds": [], "last_updated": "2024-01-15"}),
    "tmp/scratch/notes.txt": "TODO: set up new feed tracker\nAsk team which blogs to follow\n",
}
for path, content in distractor_files.items():
    (workspace / path).write_text(content)

# ── Mock RSS/Atom feeds ──────────────────────────────────────────────────────
feeds_dir = workspace / "mock_feeds"
feeds_dir.mkdir(exist_ok=True)

# Feed 1: "CloudNative Weekly" - RSS 2.0 with 3 articles
rss_feed_1 = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>CloudNative Weekly</title>
    <link>http://localhost:8765/feeds/cloudnative</link>
    <description>Weekly news on cloud native technologies</description>
    <item>
      <title>Kubernetes 1.30 Released</title>
      <link>http://localhost:8765/articles/k8s-130</link>
      <description>The latest Kubernetes release brings new features.</description>
      <pubDate>Mon, 01 Apr 2024 10:00:00 +0000</pubDate>
      <guid>http://localhost:8765/articles/k8s-130</guid>
    </item>
    <item>
      <title>eBPF in Production: Lessons Learned</title>
      <link>http://localhost:8765/articles/ebpf-prod</link>
      <description>How teams are using eBPF at scale.</description>
      <pubDate>Mon, 08 Apr 2024 10:00:00 +0000</pubDate>
      <guid>http://localhost:8765/articles/ebpf-prod</guid>
    </item>
    <item>
      <title>Service Mesh Showdown 2024</title>
      <link>http://localhost:8765/articles/service-mesh-2024</link>
      <description>Comparing Istio, Linkerd, and Cilium.</description>
      <pubDate>Mon, 15 Apr 2024 10:00:00 +0000</pubDate>
      <guid>http://localhost:8765/articles/service-mesh-2024</guid>
    </item>
  </channel>
</rss>"""

# Feed 2: "DevSecOps Digest" - Atom feed with 2 articles
atom_feed_2 = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>DevSecOps Digest</title>
  <link href="http://localhost:8765/feeds/devsecops"/>
  <id>http://localhost:8765/feeds/devsecops</id>
  <updated>2024-04-20T10:00:00Z</updated>
  <entry>
    <title>SLSA Framework Adoption Guide</title>
    <link href="http://localhost:8765/articles/slsa-guide"/>
    <id>http://localhost:8765/articles/slsa-guide</id>
    <updated>2024-04-10T09:00:00Z</updated>
    <summary>How to implement SLSA in your CI/CD pipeline.</summary>
  </entry>
  <entry>
    <title>Secrets Management with Vault</title>
    <link href="http://localhost:8765/articles/vault-secrets</link>
    <id>http://localhost:8765/articles/vault-secrets</id>
    <updated>2024-04-17T09:00:00Z</updated>
    <summary>Best practices for managing secrets at scale.</summary>
  </entry>
</feed>"""

# Feed 3: "PlatformEng Pulse" - RSS 2.0 with 4 articles (this blog will be removed)
rss_feed_3 = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>PlatformEng Pulse</title>
    <link>http://localhost:8765/feeds/platformeng</link>
    <description>Platform engineering news and insights</description>
    <item>
      <title>Internal Developer Portals Compared</title>
      <link>http://localhost:8765/articles/idp-compare</link>
      <description>Backstage vs Port vs Cortex.</description>
      <pubDate>Mon, 01 Apr 2024 08:00:00 +0000</pubDate>
      <guid>http://localhost:8765/articles/idp-compare</guid>
    </item>
    <item>
      <title>Golden Paths That Actually Work</title>
      <link>http://localhost:8765/articles/golden-paths</link>
      <description>Designing golden paths developers love.</description>
      <pubDate>Mon, 08 Apr 2024 08:00:00 +0000</pubDate>
      <guid>http://localhost:8765/articles/golden-paths</guid>
    </item>
    <item>
      <title>Terraform vs Pulumi in 2024</title>
      <link>http://localhost:8765/articles/tf-vs-pulumi</link>
      <description>IaC tooling landscape update.</description>
      <pubDate>Mon, 15 Apr 2024 08:00:00 +0000</pubDate>
      <guid>http://localhost:8765/articles/tf-vs-pulumi</guid>
    </item>
    <item>
      <title>GitOps Patterns for Platform Teams</title>
      <link>http://localhost:8765/articles/gitops-platform</link>
      <description>Advanced GitOps strategies.</description>
      <pubDate>Mon, 22 Apr 2024 08:00:00 +0000</pubDate>
      <guid>http://localhost:8765/articles/gitops-platform</guid>
    </item>
  </channel>
</rss>"""

(feeds_dir / "cloudnative.xml").write_text(rss_feed_1)
(feeds_dir / "devsecops.xml").write_text(atom_feed_2)
(feeds_dir / "platformeng.xml").write_text(rss_feed_3)

# ── Task specification file ─────────────────────────────────────────────────
# This tells the agent what sources to track (by name and URL mapping)
# Written as a business briefing, not as a technical hint
task_brief = {
    "content_sources": [
        {
            "display_name": "CloudNative Weekly",
            "url": "http://localhost:8765/feeds/cloudnative"
        },
        {
            "display_name": "DevSecOps Digest",
            "url": "http://localhost:8765/feeds/devsecops"
        },
        {
            "display_name": "PlatformEng Pulse",
            "url": "http://localhost:8765/feeds/platformeng"
        }
    ],
    "initial_review_note": "After the first content sweep, mark the first TWO articles from 'CloudNative Weekly' as already reviewed (they were covered in last month's digest). Also mark ALL articles from 'PlatformEng Pulse' as reviewed - we are dropping this source. Then remove 'PlatformEng Pulse' from the tracking list entirely.",
    "output_requirements": "Produce a file named feed_status_report.json containing: the list of currently tracked source names, and the total count of unread articles remaining across all tracked sources."
}

(workspace / "team/devrel/content_sources_brief.json").write_text(
    json.dumps(task_brief, indent=2)
)

print("Workspace initialized successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")