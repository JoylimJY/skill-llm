import os
import random

random.seed(42)

# Create directory structure
dirs = [
    "scripts",
    "docs/guides",
    "docs/api",
    "docs/tutorials",
    "staging_site",
    "staging_site/about",
    "staging_site/blog",
    "staging_site/products",
    "assets/css",
    "assets/js",
    "config",
    "tests",
    "build",
    "reports",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── dead_link_scanner.py ──────────────────────────────────────────────────────
scanner_code = r'''#!/usr/bin/env python3
import argparse
import json
import sys
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import re

def check_url(url, timeout=10):
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True,
                             headers={"User-Agent": "DeadLinkScanner/1.0"})
        if resp.status_code == 405:
            resp = requests.get(url, timeout=timeout, allow_redirects=True,
                                headers={"User-Agent": "DeadLinkScanner/1.0"})
        return resp.status_code, None
    except requests.exceptions.ConnectionError as e:
        return None, f"ConnectionError: {e}"
    except requests.exceptions.Timeout:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)

def extract_links_from_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        full = urljoin(base_url, href)
        links.append(full)
    return links

def extract_links_from_markdown(text, base_url=None):
    pattern = r'\[([^\]]*)\]\(([^)]+)\)'
    links = []
    for m in re.finditer(pattern, text):
        url = m.group(2).strip()
        if url.startswith("#") or url.startswith("mailto:"):
            continue
        if base_url and not url.startswith("http"):
            url = urljoin(base_url, url)
        if url.startswith("http"):
            links.append(url)
    return links

def is_same_domain(url, base):
    return urlparse(url).netloc == urlparse(base).netloc

def cmd_scan(args):
    start_url = args.url
    depth = args.depth
    timeout = args.timeout
    use_json = args.json
    broken_only = args.broken_only
    internal_only = args.internal_only
    max_urls = args.max_urls
    delay = args.delay

    visited_pages = set()
    checked_links = {}  # url -> (status, error, found_on)
    queue = [(start_url, 0)]
    visited_pages.add(start_url)
    results = []

    while queue and len(checked_links) < max_urls:
        page_url, current_depth = queue.pop(0)
        try:
            resp = requests.get(page_url, timeout=timeout,
                                headers={"User-Agent": "DeadLinkScanner/1.0"})
            html = resp.text
        except Exception as e:
            results.append({"url": page_url, "status": None, "error": str(e), "found_on": page_url})
            continue

        links = extract_links_from_html(html, page_url)

        for link in links:
            if internal_only and not is_same_domain(link, start_url):
                continue
            if link not in checked_links:
                if len(checked_links) >= max_urls:
                    break
                time.sleep(delay)
                status, error = check_url(link, timeout)
                checked_links[link] = (status, error, page_url)
                results.append({"url": link, "status": status, "error": error, "found_on": page_url})

            if (current_depth < depth and is_same_domain(link, start_url)
                    and link not in visited_pages):
                visited_pages.add(link)
                queue.append((link, current_depth + 1))

    if broken_only:
        results = [r for r in results if r["status"] is None or r["status"] >= 400]

    if use_json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            if r["status"] and r["status"] < 400:
                mark = "✓"
                print(f"{mark} {r['status']}  {r['url']}")
            else:
                mark = "✗"
                status_str = str(r["status"]) if r["status"] else "ERR"
                err_suffix = f" — {r['error']}" if r["error"] else ""
                print(f"{mark} {status_str}  {r['url']}  (found on: {r['found_on']}){err_suffix}")

        broken = [r for r in results if r["status"] is None or r["status"] >= 400]
        total = len(results)
        ok = total - len(broken)
        print(f"\nChecked {total} links: {ok} OK, {len(broken)} broken")

def cmd_file(args):
    paths = args.paths
    timeout = args.timeout
    use_json = args.json
    broken_only = args.broken_only

    results = []
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            results.append({"url": path, "status": None, "error": str(e), "found_on": path})
            continue

        if path.endswith(".md"):
            links = extract_links_from_markdown(content)
        else:
            links = extract_links_from_html(content, "file://" + path)

        for link in links:
            status, error = check_url(link, timeout)
            results.append({"url": link, "status": status, "error": error, "found_on": path})

    if broken_only:
        results = [r for r in results if r["status"] is None or r["status"] >= 400]

    if use_json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            if r["status"] and r["status"] < 400:
                mark = "✓"
                print(f"{mark} {r['status']}  {r['url']}")
            else:
                mark = "✗"
                status_str = str(r["status"]) if r["status"] else "ERR"
                err_suffix = f" — {r['error']}" if r["error"] else ""
                print(f"{mark} {status_str}  {r['url']}  (found on: {r['found_on']}){err_suffix}")

        broken = [r for r in results if r["status"] is None or r["status"] >= 400]
        total = len(results)
        ok = total - len(broken)
        print(f"\nChecked {total} links: {ok} OK, {len(broken)} broken")

def main():
    parser = argparse.ArgumentParser(prog="dead_link_scanner")
    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan")
    scan_p.add_argument("url")
    scan_p.add_argument("--depth", type=int, default=1)
    scan_p.add_argument("--timeout", type=int, default=10)
    scan_p.add_argument("--json", action="store_true")
    scan_p.add_argument("--broken-only", action="store_true")
    scan_p.add_argument("--internal-only", action="store_true")
    scan_p.add_argument("--max-urls", type=int, default=200)
    scan_p.add_argument("--delay", type=float, default=0.2)

    file_p = sub.add_parser("file")
    file_p.add_argument("paths", nargs="+")
    file_p.add_argument("--timeout", type=int, default=10)
    file_p.add_argument("--json", action="store_true")
    file_p.add_argument("--broken-only", action="store_true")

    args = parser.parse_args()
    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "file":
        cmd_file(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''

with open("scripts/dead_link_scanner.py", "w") as f:
    f.write(scanner_code)

os.chmod("scripts/dead_link_scanner.py", 0o755)

# ── Mock Flask server ─────────────────────────────────────────────────────────
flask_server_code = r'''#!/usr/bin/env python3
"""
Mock staging site server for link audit testing.
Port: 7891
"""
from flask import Flask, abort, redirect

app = Flask(__name__)

@app.route("/")
def index():
    return """<!DOCTYPE html>
<html><head><title>Acme Docs Home</title></head><body>
<h1>Acme Product Suite</h1>
<ul>
  <li><a href="/about">About Us</a></li>
  <li><a href="/products/widget">Widget Product</a></li>
  <li><a href="/blog/post-1">Blog Post 1</a></li>
  <li><a href="/legacy/old-feature">Legacy Feature</a></li>
  <li><a href="https://external-cdn.example.com/lib.js">External CDN</a></li>
</ul>
</body></html>"""

@app.route("/about")
def about():
    return """<!DOCTYPE html>
<html><head><title>About</title></head><body>
<h1>About Acme</h1>
<ul>
  <li><a href="/team">Team Page</a></li>
  <li><a href="/contact">Contact</a></li>
  <li><a href="/products/widget">Widget</a></li>
</ul>
</body></html>"""

@app.route("/products/widget")
def product_widget():
    return """<!DOCTYPE html>
<html><head><title>Widget</title></head><body>
<h1>Widget Product</h1>
<ul>
  <li><a href="/docs/widget-api">Widget API Docs</a></li>
  <li><a href="/pricing">Pricing</a></li>
  <li><a href="/products/gadget">Gadget Product</a></li>
</ul>
</body></html>"""

@app.route("/blog/post-1")
def blog_post1():
    return """<!DOCTYPE html>
<html><head><title>Blog Post 1</title></head><body>
<h1>Introducing Widget 2.0</h1>
<ul>
  <li><a href="/blog/post-2">Next Post</a></li>
  <li><a href="/about">About</a></li>
  <li><a href="/archive/2019/announcement">Old Announcement</a></li>
</ul>
</body></html>"""

@app.route("/team")
def team():
    return """<!DOCTYPE html><html><body><h1>Team</h1>
<a href="/">Home</a></body></html>"""

@app.route("/contact")
def contact():
    return """<!DOCTYPE html><html><body><h1>Contact</h1>
<a href="/">Home</a></body></html>"""

@app.route("/pricing")
def pricing():
    return """<!DOCTYPE html><html><body><h1>Pricing</h1>
<a href="/">Home</a></body></html>"""

# These routes intentionally return 404
@app.route("/legacy/old-feature")
def legacy():
    abort(404)

@app.route("/docs/widget-api")
def docs_widget_api():
    abort(404)

@app.route("/archive/2019/announcement")
def archive_announcement():
    abort(404)

@app.route("/blog/post-2")
def blog_post2():
    abort(404)

@app.route("/products/gadget")
def product_gadget():
    abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7891, debug=False)
'''

with open("staging_site/mock_server.py", "w") as f:
    f.write(flask_server_code)

os.chmod("staging_site/mock_server.py", 0o755)

# ── Markdown documentation files ──────────────────────────────────────────────
# docs/guides/installation.md — has some broken links
installation_md = """# Installation Guide

Welcome to the Acme Widget installation guide.

## Prerequisites

Before you begin, ensure you have:
- Python 3.8+ installed ([Download Python](https://www.python.org/downloads/))
- Access to the [Acme Dashboard](http://localhost:7891/dashboard)
- Review the [Pricing Page](http://localhost:7891/pricing) for your tier

## Steps

1. Download the package from [Releases](http://localhost:7891/releases/latest)
2. Follow the [Quick Start Guide](http://localhost:7891/docs/quickstart)
3. Register at [User Portal](http://localhost:7891/portal/register)

## Troubleshooting

See the [FAQ](http://localhost:7891/faq) and [Support](http://localhost:7891/contact) pages.
"""

with open("docs/guides/installation.md", "w") as f:
    f.write(installation_md)

# docs/api/reference.md — has some broken links
api_reference_md = """# API Reference

## Authentication

All API calls require a token. See [Auth Guide](http://localhost:7891/docs/auth).

## Endpoints

### GET /api/widgets

Returns list of widgets. Full details at [Widget API Docs](http://localhost:7891/docs/widget-api).

### POST /api/widgets

Create a widget. See [Widget Product Page](http://localhost:7891/products/widget) for context.

### DELETE /api/widgets/{id}

Delete a widget. Deprecated endpoint, see [Migration Guide](http://localhost:7891/docs/migration).

## Rate Limits

See [Pricing](http://localhost:7891/pricing) for rate limit tiers.

## Changelog

Full history at [Archive](http://localhost:7891/archive/2019/announcement).
"""

with open("docs/api/reference.md", "w") as f:
    f.write(api_reference_md)

# docs/tutorials/getting-started.md — mixed broken/ok links
getting_started_md = """# Getting Started

## Overview

This tutorial walks you through setting up your first Acme integration.

## Step 1: Sign Up

Visit the [Registration Page](http://localhost:7891/portal/register) to create an account.

## Step 2: Read the Blog

Check out [Blog Post 1](http://localhost:7891/blog/post-1) for tips.

## Step 3: Explore Products

Browse our [Widget](http://localhost:7891/products/widget) and [Gadget](http://localhost:7891/products/gadget) offerings.

## Step 4: Contact Support

Reach us at the [Contact Page](http://localhost:7891/contact).
"""

with open("docs/tutorials/getting-started.md", "w") as f:
    f.write(getting_started_md)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "config/deploy.yml": "environment: production\nregion: us-east-1\n",
    "config/settings.json": '{"log_level": "info", "max_connections": 100}\n',
    "tests/test_api.py": "# Unit tests placeholder\ndef test_placeholder():\n    pass\n",
    "tests/test_widgets.py": "# Widget tests\ndef test_widget_create():\n    assert True\n",
    "build/manifest.txt": "build: 2024.03.15\nversion: 3.2.1\n",
    "assets/css/main.css": "body { font-family: sans-serif; }\n",
    "assets/js/app.js": "console.log('Acme Widget App loaded');\n",
    "docs/guides/changelog.md": "# Changelog\n\n## v3.2.1\n- Bug fixes\n\n## v3.2.0\n- New features\n",
    "docs/api/authentication.md": "# Authentication\n\nUse Bearer tokens for all API calls.\n",
    "staging_site/about/index.html": "<html><body><h1>About</h1></body></html>\n",
    "staging_site/blog/index.html": "<html><body><h1>Blog</h1></body></html>\n",
    "reports/.gitkeep": "",
}

for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs, files in os.walk("."):
    for file in files:
        full_path = os.path.join(root, file)
        print(f"  {full_path}")