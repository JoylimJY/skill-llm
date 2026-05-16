---
name: Bookmark Ninja
version: 1.0.0
description: Universal bookmark-to-knowledge-base converter. Ingests browser HTML bookmark exports (Chrome, Firefox, Edge, Brave), parses hierarchical structure, and outputs machine-readable JSON/CSV indexes for agent consumption.


Supports incremental merging, conflict resolution, and optional URL liveness verification. Use for research libraries, OSINT source management, legal discovery archives, or any profession requiring organized bookmark collections as queryable knowledge bases.
homepage: https://clawhub.ai/samaritanoc/bookmark-ninja
metadata:
  openclaw:
    requires:
      bins:
        - python3
    install:
      - kind: uv
        package: requests
        bins: []
---

# Bookmark Ninja — Universal Bookmark Knowledge Base

## Purpose Notice


This skill transforms browser bookmark exports into structured, machine-readable knowledge bases. 


While originally developed for OSINT source management, it's profession-agnostic: researchers organizing academic papers, lawyers managing case law databases, journalists tracking sources, developers cataloging technical references, or anyone who has accumulated bookmarks and wants their AI agent to search and use them intelligently.


The skill processes standard Netscape HTML bookmark format (exported by Chrome, Firefox, Edge, Brave) and produces JSON/CSV indexes with full category hierarchy, metadata, and optional liveness verification.

---

## When to Use This Skill


Use Bookmark Ninja whenever you need to:


* **Convert browser bookmarks to agent-queryable format** — Transform exported HTML into structured JSON/CSV
* **Build a living knowledge base** — Incrementally add new bookmarks or HTML exports without wiping existing data
* **Organize accumulated research** — Preserve folder hierarchy as category breadcrumb paths
* **Verify link validity** — Optional HEAD request checks to identify dead URLs
* **Merge multiple bookmark sources** — Combine exports from different browsers or time periods
* **Share curated resource lists** — Export portable indexes others can query programmatically
* **Archive before cleanup** — Snapshot current bookmarks before browser migration or folder reorganization


Always prefer this skill over manual bookmark management when you need:
* **Programmatic search across large bookmark collections
* **Deduplication and conflict resolution
* **Category-based filtering and organization
* **Historical tracking via date_added timestamps
* **Cross-browser bookmark consolidation

---

## Core Capabilities

### 1. Parse Standard Bookmark Exports

Reads Netscape HTML format (the universal export format):
```bash
python3 bookmark-parser.py bookmarks.html
```

Extracts:
- **URL** — The bookmark link
- **Title** — Page title or user-defined name
- **Category** — Full folder hierarchy as breadcrumb (e.g., "Research > AI > Papers")
- **Description** — Metadata attribute if present
- **Date Added** — Timestamp converted to ISO 8601
- **Icon** — Favicon URL if present

Output: `bookmarks-index.json` (default)

### 2. Incremental Merging

Add new bookmarks to existing index without wiping data:
```bash
# Initial import
python3 bookmark-parser.py bookmarks-2024.html -o my-index.json

# Later: merge new export
python3 bookmark-parser.py bookmarks-2025.html -o my-index.json --merge
```

**Conflict handling:**
- Detects when same URL exists with different title/category/description
- Prompts for resolution: keep old, keep new, or skip
- Automate with `--keep-old` or `--keep-new` flags

### 3. URL Liveness Check

Verify links are still accessible:
```bash
python3 bookmark-parser.py bookmarks.html --check-alive
```

Performs HEAD request to each URL, adds `"alive": true/false` field.
Requires `requests` library (auto-installed via skill metadata).

### 4. Multiple Output Formats
```bash
# JSON only (default)
python3 bookmark-parser.py bookmarks.html

# CSV only
python3 bookmark-parser.py bookmarks.html --format csv

# Both formats
python3 bookmark-parser.py bookmarks.html --format both
```

### 5. Statistics & Analysis

Preview without saving:
```bash
python3 bookmark-parser.py bookmarks.html --stats
```

Shows:
- Total entries
- Category count
- Top 10 categories by entry count
- Alive/dead URL counts (if `--check-alive` used)

---

## Usage Examples

### Basic Import
```bash
# Export bookmarks from Chrome: Menu > Bookmarks > Bookmark Manager > ⋮ > Export bookmarks
# Firefox: Menu > Bookmarks > Manage Bookmarks > Import and Backup > Export Bookmarks to HTML

python3 bookmark-parser.py ~/Downloads/bookmarks.html
# Output: bookmarks-index.json
```

### Custom Output Location
```bash
python3 bookmark-parser.py bookmarks.html -o ~/research/sources.json
```

### Merge New Bookmarks
```bash
# Import initial collection
python3 bookmark-parser.py old-bookmarks.html -o index.json

# Later: add new bookmarks (prompts on conflicts)
python3 bookmark-parser.py new-bookmarks.html -o index.json --merge

# Auto-keep newer data
python3 bookmark-parser.py new-bookmarks.html -o index.json --merge --keep-new
```

### Verify Links Are Alive
```bash
python3 bookmark-parser.py bookmarks.html --check-alive -o verified.json
# Adds "alive": true/false to each entry
# Note: Adds latency (5s timeout per URL)
```

### Export as CSV
```bash
python3 bookmark-parser.py bookmarks.html --format csv
# Output: bookmarks-index.csv
```

### Quick Statistics
```bash
python3 bookmark-parser.py bookmarks.html --stats
```

---

## Output Format

### JSON Structure
```json
[
  {
    "url": "https://example.com",
    "title": "Example Site",
    "category": "Research > Web Dev > Tools",
    "description": "Useful web development tool",
    "date_added": "2024-03-15T10:30:00",
    "icon": "https://example.com/favicon.ico",
    "alive": true
  }
]
```

### CSV Columns
```
url,title,category,description,date_added,icon,alive
https://example.com,"Example Site","Research > Web Dev > Tools","Useful tool",2024-03-15T10:30:00,https://example.com/favicon.ico,True
```

---

## Agent Integration Patterns

### Search by Keyword
```python
import json

with open("bookmarks-index.json") as f:
    bookmarks = json.load(f)

# Search titles and descriptions
keyword = "machine learning"
matches = [
    b for b in bookmarks 
    if keyword.lower() in b["title"].lower() 
    or keyword.lower() in b["description"].lower()
]
```

### Filter by Category
```python
category = "OSINT > Email Search"
matches = [b for b in bookmarks if category in b["category"]]
```

### Get All Categories
```python
categories = sorted(set(b["category"] for b in bookmarks))
```

### Find Dead Links
```python
dead = [b for b in bookmarks if b.get("alive") == False]
```

### Recent Bookmarks
```python
from datetime import datetime, timedelta

recent_date = datetime.now() - timedelta(days=30)
recent = [
    b for b in bookmarks 
    if b["date_added"] and datetime.fromisoformat(b["date_added"]) > recent_date
]
```

---

## Command Reference
```
usage: bookmark-parser.py [-h] [-o OUTPUT] [--format {json,csv,both}]
                          [--merge] [--keep-old] [--keep-new]
                          [--check-alive] [--stats]
                          input

Convert browser bookmarks to machine-readable index

positional arguments:
  input                 HTML bookmark file to parse

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file path (default: bookmarks-index.json)
  --format {json,csv,both}
                        Output format (default: json)
  --merge               Merge with existing index file
  --keep-old            On merge conflict, keep old entry (default: prompt)
  --keep-new            On merge conflict, keep new entry (default: prompt)
  --check-alive         Check URL liveness via HEAD request (adds latency)
  --stats               Print statistics only, don't save
```

---

## Workflow: Building a Research Library

1. **Initial import**
```bash
   python3 bookmark-parser.py research-bookmarks.html -o research-library.json
```

2. **Add new sources monthly**
```bash
   python3 bookmark-parser.py bookmarks-march.html -o research-library.json --merge --keep-new
```

3. **Verify links quarterly**
```bash
   python3 bookmark-parser.py bookmarks-current.html --check-alive -o research-library.json --merge --keep-new
```

4. **Agent queries the index**
```bash
   # Using jq for CLI queries
   cat research-library.json | jq '.[] | select(.category | contains("AI")) | .title'
   
   # Or load into Python/agent for programmatic search
```

---

## Troubleshooting

**"requests library not available" warning**
- Liveness check requires `requests` package
- Skill metadata auto-installs via `uv` if available
- Manual install: `pip install requests`


**Encoding errors on import**
- Parser uses `errors="ignore"` for malformed HTML
- If issues persist, re-export bookmarks from browser


**Category hierarchy looks wrong**
- Bookmark format nests categories via `<DL>` tags
- Verify export includes folder structure (not flat list)
- Chrome/Firefox: ensure "Include folder structure" is checked during export


**Merge conflicts on every entry**
- Date/time format changes trigger conflicts
- Use `--keep-new` to auto-accept updated metadata

---

## Related Skills

- **google-dorks** — Precision web search operators for research


- Use Bookmark Ninja to organize discovered sources from dork queries
- Export curated source lists as shareable bookmark HTML

---

## Version History

**1.0.3** (2025-03-30)
- Initial release
- Netscape HTML bookmark parsing
- JSON/CSV output
- Incremental merging with conflict resolution
- Optional URL liveness verification
- Category hierarchy preservation
