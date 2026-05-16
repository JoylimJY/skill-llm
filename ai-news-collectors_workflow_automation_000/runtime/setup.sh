#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace
chmod +x /workspace/tools/scrapers/rss_scraper.py 2>/dev/null || true
chmod +x /workspace/tools/parsers/html_parser.py 2>/dev/null || true

echo "Workspace ready."
echo "Directory tree:"
tree /workspace 2>/dev/null || find /workspace -type f | sort