# Bookmark Ninja

**Universal bookmark-to-knowledge-base converter for AI agents**

Transform browser bookmark exports into structured, queryable knowledge bases. Built for researchers, investigators, lawyers, journalists, developers — anyone who has accumulated bookmarks and wants their AI agent to search and use them intelligently.

## What It Does

- **Parses** standard browser bookmark HTML exports (Chrome, Firefox, Edge, Brave)
- **Preserves** folder hierarchy as category breadcrumb paths
- **Outputs** machine-readable JSON/CSV with full metadata
- **Merges** incremental additions without wiping existing data
- **Resolves** conflicts with interactive or automated strategies
- **Verifies** URL liveness via optional HEAD requests
- **Supports** any domain: OSINT sources, academic papers, case law, technical docs, recipes — anything you bookmark

## Quick Start

### 1. Export Your Bookmarks

**Chrome:** Menu > Bookmarks > Bookmark Manager > ⋮ > Export bookmarks  
**Firefox:** Menu > Bookmarks > Manage Bookmarks > Import and Backup > Export Bookmarks to HTML  
**Edge/Brave:** Same as Chrome

Saves as `bookmarks_[date].html`

### 2. Convert to Knowledge Base
```bash
python3 bookmark-parser.py bookmarks.html
```

**Output:** `bookmarks-index.json` — structured, searchable, agent-ready

### 3. Query Programmatically
```python
import json

with open("bookmarks-index.json") as f:
    bookmarks = json.load(f)

# Search by keyword
results = [b for b in bookmarks if "security" in b["title"].lower()]

# Filter by category
osint = [b for b in bookmarks if "OSINT" in b["category"]]

# Find dead links
dead = [b for b in bookmarks if b.get("alive") == False]
```

## Installation

**Requirements:** Python 3.7+

**Optional:** `requests` library for URL liveness checks
```bash
pip install requests
```

## Usage Examples

### Basic Parsing
```bash
python3 bookmark-parser.py bookmarks.html
```

### Custom Output Location
```bash
python3 bookmark-parser.py bookmarks.html -o ~/research/sources.json
```

### Merge New Bookmarks
```bash
# Initial import
python3 bookmark-parser.py old-bookmarks.html -o index.json

# Add new bookmarks later
python3 bookmark-parser.py new-bookmarks.html -o index.json --merge
```

### Verify Link Validity
```bash
python3 bookmark-parser.py bookmarks.html --check-alive
```

### Export as CSV
```bash
python3 bookmark-parser.py bookmarks.html --format csv
```

### Statistics Only
```bash
python3 bookmark-parser.py bookmarks.html --stats
```

## Output Format

### JSON
```json
[
  {
    "url": "https://example.com",
    "title": "Example Site",
    "category": "Research > Tools > Web",
    "description": "Useful web tool",
    "date_added": "2024-03-15T10:30:00",
    "icon": "https://example.com/favicon.ico",
    "alive": true
  }
]
```

### CSV
```csv
url,title,category,description,date_added,icon,alive
https://example.com,"Example Site","Research > Tools > Web","Useful tool",2024-03-15T10:30:00,https://example.com/favicon.ico,True
```

## Conflict Resolution

When merging, if a URL exists with different metadata:

**Interactive mode (default):**
```
⚠️  Found 3 conflicting entries:

Conflict 1/3: https://example.com
  OLD: [Research > Tools] Example Site
  NEW: [Web Dev > Resources] Example Site - Updated
  Keep (o)ld, (n)ew, or (s)kip? [o/n/s]:
```

**Automated modes:**
```bash
# Always keep old entries
python3 bookmark-parser.py bookmarks.html -o index.json --merge --keep-old

# Always keep new entries
python3 bookmark-parser.py bookmarks.html -o index.json --merge --keep-new
```

## Command Reference
```
usage: bookmark-parser.py [-h] [-o OUTPUT] [--format {json,csv,both}]
                          [--merge] [--keep-old] [--keep-new]
                          [--check-alive] [--stats]
                          input

positional arguments:
  input                 HTML bookmark file to parse

options:
  -o OUTPUT             Output file path (default: bookmarks-index.json)
  --format              Output format: json, csv, or both (default: json)
  --merge               Merge with existing index file
  --keep-old            On conflict, keep old entry (default: prompt)
  --keep-new            On conflict, keep new entry (default: prompt)
  --check-alive         Verify URL liveness (adds latency)
  --stats               Show statistics only, don't save
```

## Use Cases

**OSINT Investigators**  
Organize 1000+ intelligence sources with full category trees, verify links quarterly, share curated collections with team

**Academic Researchers**  
Track paper databases, journal archives, dataset repositories across multiple research projects with date-stamped additions

**Legal Teams**  
Build searchable case law libraries, regulatory database collections, court record portals organized by jurisdiction

**Journalists**  
Maintain source directories, document archives, public records portals with incremental updates as stories develop

**Developers**  
Catalog technical documentation, API references, GitHub repos, Stack Overflow threads by language and framework

**General Knowledge Workers**  
Convert chaotic browser bookmark folders into structured, searchable knowledge bases your AI agent can query

## License

MIT-0 (Public Domain equivalent)

## Author

Published by [samaritanoc](https://clawhub.ai/samaritanoc) on ClawHub

---

## Support The Samaritan Project

This is an active, build-in-public project focused on developing replicable, private agentic AI infrastructure that can be deployed across any industry or use case. If you're interested in where local-first AI is headed, and want to support the hardware and infrastructure that makes this possible, follow along and contribute at **https://buymeacoffee.com/thesamaritanproject**
