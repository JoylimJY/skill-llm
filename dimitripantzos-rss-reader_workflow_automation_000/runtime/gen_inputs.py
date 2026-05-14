import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/root/clawd")

# ─── Directory structure (distractors) ──────────────────────────────────────
dirs = [
    "skills/rss-reader/scripts",
    "skills/rss-reader/rss-reader",
    "skills/social-monitor/scripts",
    "skills/email-digest/config",
    "skills/email-digest/templates",
    "projects/biotech-research/notes",
    "projects/biotech-research/data",
    "projects/competitive-intel/reports",
    "projects/competitive-intel/raw",
    "logs/archive",
    "config/backups",
    "tmp/downloads",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ────────────────────────────────────────────────────────
distractor_files = {
    "skills/social-monitor/scripts/twitter.js": "// twitter monitor stub\nmodule.exports = {};",
    "skills/social-monitor/config.json": json.dumps({"platform": "twitter", "keywords": []}),
    "skills/email-digest/config/settings.json": json.dumps({"smtp": "localhost", "port": 587}),
    "skills/email-digest/templates/daily.html": "<html><body>{{content}}</body></html>",
    "projects/biotech-research/notes/competitors.md": textwrap.dedent("""\
        # Competitor Tracking Notes
        - GenomicsX: announced phase 2 trial Q1
        - BioNovate: new CRISPR delivery platform
        - ClinPath: FDA fast-track designation
    """),
    "projects/biotech-research/data/pipeline_summary.csv": "company,drug,stage,indication\nGenomicsX,GX-101,Phase2,Oncology\nBioNovate,BN-EDIT,Preclinical,Rare Disease\n",
    "projects/competitive-intel/reports/q1_2024.txt": "Q1 2024 competitive report placeholder. See full analysis in shared drive.",
    "projects/competitive-intel/raw/scraped_20240301.json": json.dumps([
        {"source": "pubmed", "title": "CRISPR advances in 2024", "date": "2024-03-01"},
        {"source": "clinicaltrials.gov", "title": "Phase 3 FDA approval pathway", "date": "2024-02-28"},
    ]),
    "logs/archive/rss_old_20231201.log": "2023-12-01 08:00:00 INFO checked 3 feeds, 12 new items\n2023-12-02 08:00:01 INFO checked 3 feeds, 7 new items\n",
    "config/backups/feeds_backup_20231115.json": json.dumps({
        "feeds": [
            {"url": "https://old-biotech-blog.example.com/rss", "name": "Old Blog", "category": "archive", "enabled": False}
        ],
        "settings": {"maxItemsPerFeed": 10, "maxAgeDays": 30, "summaryEnabled": False}
    }),
    "tmp/downloads/test_feed_sample.xml": textwrap.dedent("""\
        <?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <title>Test</title>
            <item><title>Old item</title><link>http://example.com/1</link></item>
          </channel>
        </rss>
    """),
}

for rel_path, content in distractor_files.items():
    fp = workspace / rel_path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content)

# ─── The REAL rss.js script ──────────────────────────────────────────────────
# This is the actual script from the skill. We write it as per SKILL.md spec.
rss_js = r"""#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

// Resolve feeds.json relative to this script's location
const FEEDS_FILE = path.join(__dirname, '..', 'rss-reader', 'feeds.json');

function loadFeeds() {
  if (!fs.existsSync(FEEDS_FILE)) {
    return {
      feeds: [],
      settings: {
        maxItemsPerFeed: 10,
        maxAgeDays: 7,
        summaryEnabled: true
      }
    };
  }
  return JSON.parse(fs.readFileSync(FEEDS_FILE, 'utf8'));
}

function saveFeeds(data) {
  const dir = path.dirname(FEEDS_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(FEEDS_FILE, JSON.stringify(data, null, 2));
}

function parseArgs(argv) {
  const args = { flags: {}, positional: [] };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) {
      const key = argv[i].slice(2);
      if (i + 1 < argv.length && !argv[i+1].startsWith('--')) {
        args.flags[key] = argv[++i];
      } else {
        args.flags[key] = true;
      }
    } else {
      args.positional.push(argv[i]);
    }
  }
  return args;
}

async function fetchFeed(url) {
  let fetch;
  try {
    fetch = require('node-fetch');
  } catch(e) {
    console.error('node-fetch not installed. Run: npm install node-fetch');
    process.exit(1);
  }
  let xml2js;
  try {
    xml2js = require('xml2js');
  } catch(e) {
    console.error('xml2js not installed. Run: npm install xml2js');
    process.exit(1);
  }

  const res = await fetch(url, { timeout: 10000 });
  const text = await res.text();
  const parsed = await xml2js.parseStringPromise(text, { explicitArray: false });

  const items = [];
  // RSS 2.0
  if (parsed.rss && parsed.rss.channel) {
    const ch = parsed.rss.channel;
    const rawItems = Array.isArray(ch.item) ? ch.item : (ch.item ? [ch.item] : []);
    for (const it of rawItems) {
      items.push({
        title: it.title || '',
        link: it.link || '',
        pubDate: it.pubDate || it['dc:date'] || '',
        description: it.description || '',
        content: it['content:encoded'] || it.description || ''
      });
    }
  }
  // Atom
  if (parsed.feed && parsed.feed.entry) {
    const entries = Array.isArray(parsed.feed.entry) ? parsed.feed.entry : [parsed.feed.entry];
    for (const en of entries) {
      const link = en.link ? (typeof en.link === 'string' ? en.link : (en.link.$ ? en.link.$.href : '')) : '';
      items.push({
        title: en.title ? (typeof en.title === 'string' ? en.title : en.title._) : '',
        link: link,
        pubDate: en.updated || en.published || '',
        description: en.summary ? (typeof en.summary === 'string' ? en.summary : en.summary._) : '',
        content: en.content ? (typeof en.content === 'string' ? en.content : en.content._) : ''
      });
    }
  }
  return items;
}

function matchesKeywords(item, keywords) {
  if (!keywords || keywords.length === 0) return true;
  const text = (item.title + ' ' + item.description + ' ' + item.content).toLowerCase();
  return keywords.some(k => text.includes(k.toLowerCase()));
}

function timeAgo(dateStr) {
  if (!dateStr) return 'unknown';
  const d = new Date(dateStr);
  if (isNaN(d)) return 'unknown';
  const diff = Date.now() - d.getTime();
  const h = Math.floor(diff / 3600000);
  if (h < 1) return 'just now';
  if (h < 24) return h + 'h ago';
  return Math.floor(h/24) + 'd ago';
}

async function cmdCheck(flags, data) {
  const category = flags.category;
  const format = flags.format || 'list';
  const keywords = flags.keywords ? flags.keywords.split(',').map(k => k.trim()) : [];
  const since = flags.since;

  let sinceDate = null;
  if (since) {
    const m = since.match(/^(\d+)h$/);
    if (m) sinceDate = new Date(Date.now() - parseInt(m[1]) * 3600000);
    const dm = since.match(/^(\d+)d$/);
    if (dm) sinceDate = new Date(Date.now() - parseInt(dm[1]) * 86400000);
  }

  const feeds = data.feeds.filter(f => f.enabled !== false && (!category || f.category === category));

  if (format === 'json') {
    const results = [];
    for (const feed of feeds) {
      try {
        const items = await fetchFeed(feed.url);
        const filtered = items
          .filter(it => matchesKeywords(it, keywords))
          .filter(it => {
            if (!sinceDate) return true;
            const d = new Date(it.pubDate);
            return !isNaN(d) && d >= sinceDate;
          })
          .slice(0, data.settings.maxItemsPerFeed);
        results.push({ feed: feed.name, category: feed.category, items: filtered });
      } catch(e) {
        results.push({ feed: feed.name, category: feed.category, error: e.message });
      }
    }
    console.log(JSON.stringify(results, null, 2));
    return;
  }

  if (format === 'ideas') {
    console.log('## Content Ideas from RSS' + (since ? ' (Last ' + since + ')' : ''));
    console.log('');
    const byCategory = {};
    for (const feed of feeds) {
      try {
        const items = await fetchFeed(feed.url);
        const filtered = items
          .filter(it => matchesKeywords(it, keywords))
          .filter(it => {
            if (!sinceDate) return true;
            const d = new Date(it.pubDate);
            return !isNaN(d) && d >= sinceDate;
          })
          .slice(0, data.settings.maxItemsPerFeed);
        if (!byCategory[feed.category]) byCategory[feed.category] = [];
        for (const it of filtered) {
          byCategory[feed.category].push({ item: it, feed: feed });
        }
      } catch(e) {
        // skip failed feeds silently in ideas format
      }
    }
    for (const [cat, entries] of Object.entries(byCategory)) {
      if (entries.length === 0) continue;
      console.log('### ' + cat.charAt(0).toUpperCase() + cat.slice(1));
      for (const { item, feed } of entries) {
        console.log('- **"' + item.title + '"** - [' + feed.name + ']');
        const desc = item.description.replace(/<[^>]+>/g, '').trim().slice(0, 120);
        console.log('  Key points: ' + (desc || 'N/A'));
        console.log('  Angle: How this relates to your niche');
      }
      console.log('');
    }
    return;
  }

  // Default list format
  for (const feed of feeds) {
    try {
      const items = await fetchFeed(feed.url);
      const filtered = items
        .filter(it => matchesKeywords(it, keywords))
        .filter(it => {
          if (!sinceDate) return true;
          const d = new Date(it.pubDate);
          return !isNaN(d) && d >= sinceDate;
        })
        .slice(0, data.settings.maxItemsPerFeed);
      for (const it of filtered) {
        console.log('[' + feed.category + '] ' + feed.name + ' - "' + it.title + '" (' + timeAgo(it.pubDate) + ')');
        console.log('  ' + it.link);
      }
    } catch(e) {
      console.error('Error fetching ' + feed.url + ': ' + e.message);
    }
  }
}

async function main() {
  const argv = process.argv.slice(2);
  if (argv.length === 0) {
    console.log('Usage: node rss.js <command> [options]');
    console.log('Commands: add, remove, list, check');
    process.exit(0);
  }

  const cmd = argv[0];
  const rest = parseArgs(argv.slice(1));
  const data = loadFeeds();

  if (cmd === 'add') {
    const url = rest.positional[0];
    if (!url) { console.error('URL required'); process.exit(1); }
    const category = rest.flags.category || 'general';
    const name = rest.flags.name || url.replace(/^https?:\/\//, '').split('/')[0];
    const existing = data.feeds.find(f => f.url === url);
    if (existing) {
      console.log('Feed already exists: ' + url);
      return;
    }
    data.feeds.push({
      url,
      name,
      category,
      enabled: true,
      lastChecked: null,
      lastItemDate: null
    });
    saveFeeds(data);
    console.log('Added feed: ' + url + ' [' + category + ']');
  }

  else if (cmd === 'remove') {
    const url = rest.positional[0];
    if (!url) { console.error('URL required'); process.exit(1); }
    const before = data.feeds.length;
    data.feeds = data.feeds.filter(f => f.url !== url);
    if (data.feeds.length < before) {
      saveFeeds(data);
      console.log('Removed feed: ' + url);
    } else {
      console.log('Feed not found: ' + url);
    }
  }

  else if (cmd === 'list') {
    if (data.feeds.length === 0) {
      console.log('No feeds configured.');
      return;
    }
    for (const f of data.feeds) {
      const status = f.enabled !== false ? 'enabled' : 'disabled';
      console.log('[' + f.category + '] ' + f.name + ' (' + status + ')');
      console.log('  ' + f.url);
    }
  }

  else if (cmd === 'check') {
    await cmdCheck(rest.flags, data);
  }

  else {
    console.error('Unknown command: ' + cmd);
    process.exit(1);
  }
}

main().catch(e => { console.error(e); process.exit(1); });
"""

(workspace / "skills/rss-reader/scripts/rss.js").write_text(rss_js)

# ─── parse-feed.js stub (referenced in SKILL.md) ─────────────────────────────
parse_feed_js = """'use strict';
// Feed parser module used internally
module.exports = {};
"""
(workspace / "skills/rss-reader/scripts/parse-feed.js").write_text(parse_feed_js)

# ─── package.json for rss-reader ─────────────────────────────────────────────
pkg = {
    "name": "rss-reader",
    "version": "1.0.0",
    "description": "RSS feed reader skill",
    "main": "scripts/rss.js",
    "dependencies": {
        "xml2js": "^0.6.2",
        "node-fetch": "^2.7.0"
    }
}
(workspace / "skills/rss-reader/package.json").write_text(json.dumps(pkg, indent=2))

# ─── Mock RSS XML feed files (served by mock HTTP server) ────────────────────
# These are written as static files to be served. The mock server script
# is written here as a distractor-free reference. The server script itself
# is written in setup_script.

mock_feeds_dir = workspace / "tmp/mock_feeds"
mock_feeds_dir.mkdir(parents=True, exist_ok=True)

competitor_feed = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>GenomicsX Pipeline Blog</title>
    <link>http://localhost:18080/competitors</link>
    <description>Latest from GenomicsX R&amp;D</description>
    <item>
      <title>GenomicsX Announces CRISPR-Based Oncology Trial</title>
      <link>http://localhost:18080/competitors/post/1</link>
      <pubDate>Tue, 10 Jun 2025 09:00:00 +0000</pubDate>
      <description>GenomicsX today unveiled a new CRISPR delivery mechanism targeting solid tumors in a Phase 2 clinical trial slated for Q3 2025.</description>
    </item>
    <item>
      <title>Quarterly Pipeline Update: Five Programs Advancing</title>
      <link>http://localhost:18080/competitors/post/2</link>
      <pubDate>Mon, 09 Jun 2025 14:00:00 +0000</pubDate>
      <description>Our five lead programs have each cleared IND-enabling studies and are advancing toward first-in-human dosing by year end.</description>
    </item>
    <item>
      <title>Partnership with Leading Academic Medical Center</title>
      <link>http://localhost:18080/competitors/post/3</link>
      <pubDate>Fri, 06 Jun 2025 11:00:00 +0000</pubDate>
      <description>GenomicsX signed a multi-year research collaboration agreement to accelerate rare disease programs.</description>
    </item>
  </channel>
</rss>
"""

clinical_feed = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>ClinicalTrials Weekly Digest</title>
    <link>http://localhost:18080/clinical</link>
    <description>Weekly digest of notable clinical trial results</description>
    <item>
      <title>Phase 3 Results: CRISPR Gene Editing Shows 80% Response Rate</title>
      <link>http://localhost:18080/clinical/post/1</link>
      <pubDate>Wed, 11 Jun 2025 08:00:00 +0000</pubDate>
      <description>A landmark Phase 3 clinical trial of a CRISPR-edited T-cell therapy demonstrated an 80% objective response rate in relapsed/refractory B-cell lymphoma.</description>
    </item>
    <item>
      <title>New Endpoints Guidance for Rare Disease Clinical Trials</title>
      <link>http://localhost:18080/clinical/post/2</link>
      <pubDate>Tue, 10 Jun 2025 10:30:00 +0000</pubDate>
      <description>FDA released draft guidance outlining acceptable surrogate endpoints for clinical trial submissions in ultra-rare pediatric indications.</description>
    </item>
    <item>
      <title>Adaptive Trial Design Gains Traction in Oncology</title>
      <link>http://localhost:18080/clinical/post/3</link>
      <pubDate>Mon, 09 Jun 2025 16:00:00 +0000</pubDate>
      <description>Adaptive clinical trial designs are being adopted more widely, allowing interim analysis to modify dosing arms without compromising statistical integrity.</description>
    </item>
  </channel>
</rss>
"""

regulatory_feed = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>FDA News &amp; Approvals</title>
    <link>http://localhost:18080/regulatory</link>
    <description>Latest FDA approvals, guidance documents, and regulatory actions</description>
    <item>
      <title>FDA Grants Breakthrough Therapy Designation for Novel CAR-T</title>
      <link>http://localhost:18080/regulatory/post/1</link>
      <pubDate>Thu, 12 Jun 2025 07:00:00 +0000</pubDate>
      <description>The FDA has granted Breakthrough Therapy Designation to a next-generation CAR-T construct targeting CD19 and CD22 dual antigens in pediatric ALL.</description>
    </item>
    <item>
      <title>FDA Issues Warning Letter Over GMP Violations at Contract Manufacturer</title>
      <link>http://localhost:18080/regulatory/post/2</link>
      <pubDate>Wed, 11 Jun 2025 13:00:00 +0000</pubDate>
      <description>A contract development and manufacturing organization received an FDA warning letter citing critical GMP deficiencies in viral vector production.</description>
    </item>
    <item>
      <title>PDUFA Dates: Key FDA Decisions Expected This Quarter</title>
      <link>http://localhost:18080/regulatory/post/3</link>
      <pubDate>Tue, 10 Jun 2025 09:45:00 +0000</pubDate>
      <description>Several high-profile PDUFA action dates are approaching, including decisions on gene therapies and a first-in-class FDA-regulated cell therapy platform.</description>
    </item>
  </channel>
</rss>
"""

(mock_feeds_dir / "competitors.xml").write_text(competitor_feed)
(mock_feeds_dir / "clinical.xml").write_text(clinical_feed)
(mock_feeds_dir / "regulatory.xml").write_text(regulatory_feed)

# ─── Write a deliberately stale/wrong feeds.json (agent must overwrite) ──────
# Has wrong settings and NO feeds — agent must add feeds and fix settings
stale_config = {
    "feeds": [],
    "settings": {
        "maxItemsPerFeed": 10,
        "maxAgeDays": 7,
        "summaryEnabled": False
    }
}
feeds_json_path = workspace / "skills/rss-reader/rss-reader/feeds.json"
feeds_json_path.parent.mkdir(parents=True, exist_ok=True)
feeds_json_path.write_text(json.dumps(stale_config, indent=2))

# ─── A red-herring config in a wrong location ─────────────────────────────────
wrong_loc = workspace / "config/backups/feeds_wrong_location.json"
wrong_loc.write_text(json.dumps({
    "feeds": [
        {"url": "http://localhost:18080/competitors.xml", "name": "WRONG", "category": "wrong", "enabled": True}
    ],
    "settings": {"maxItemsPerFeed": 99, "maxAgeDays": 99, "summaryEnabled": False}
}, indent=2))

print("Workspace generated successfully.")
print(f"feeds.json location: {feeds_json_path}")
print(f"Mock feed XMLs: {mock_feeds_dir}")