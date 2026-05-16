#!/usr/bin/env python3
"""
bookmark-parser.py — Universal bookmark-to-knowledge-base converter

Ingests browser HTML bookmark exports, parses structure, and outputs
machine-readable JSON index for agent consumption.

Supports: Chrome, Firefox, Edge, Brave (Netscape bookmark format)
"""

import sys
import json
import csv
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import argparse

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class BookmarkParser(HTMLParser):
    """Parses Netscape HTML bookmark format."""

    def __init__(self):
        super().__init__()
        self.entries = []
        self.category_stack = []
        self.current_href = None
        self.current_attrs = {}
        self.capture_title = False
        self.current_title = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "h3":
            # Category header
            self.capture_title = True
            self.current_title = ""

        elif tag == "a":
            # Bookmark link
            self.current_href = attrs_dict.get("href", "")
            self.current_attrs = attrs_dict
            self.capture_title = True
            self.current_title = ""

        elif tag == "dl":
            # Descending into a category
            pass

    def handle_endtag(self, tag):
        if tag == "h3":
            # End of category header - push to stack
            category = self.current_title.strip()
            if category:
                self.category_stack.append(category)
            self.capture_title = False

        elif tag == "a":
            # End of bookmark link - record entry
            if self.current_href:
                category_path = " > ".join(self.category_stack) if self.category_stack else "Uncategorized"

                # Parse ADD_DATE (Unix timestamp)
                add_date = self.current_attrs.get("add_date", "")
                date_added = ""
                if add_date:
                    try:
                        date_added = datetime.fromtimestamp(int(add_date)).isoformat()
                    except (ValueError, OSError):
                        pass

                self.entries.append({
                    "url": self.current_href,
                    "title": self.current_title.strip(),
                    "category": category_path,
                    "description": self.current_attrs.get("description", ""),
                    "date_added": date_added,
                    "icon": self.current_attrs.get("icon", ""),
                })

            self.current_href = None
            self.current_attrs = {}
            self.capture_title = False

        elif tag == "dl":
            # Ascending from a category
            if self.category_stack:
                self.category_stack.pop()

    def handle_data(self, data):
        if self.capture_title:
            self.current_title += data


def parse_bookmarks(html_file):
    """Parse HTML bookmark file and return entries."""
    with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    parser = BookmarkParser()
    parser.feed(content)
    return parser.entries


def check_url_alive(url, timeout=5):
    """Check if URL is accessible via HEAD request."""
    if not REQUESTS_AVAILABLE:
        return None

    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        return False


def merge_entries(existing, new, conflict_resolution="prompt"):
    """
    Merge new entries into existing index.

    Args:
        existing: list of existing entries
        new: list of new entries
        conflict_resolution: "keep-old", "keep-new", "prompt"

    Returns:
        merged list, conflict count
    """
    existing_map = {e["url"]: e for e in existing}
    conflicts = []

    for entry in new:
        url = entry["url"]

        if url in existing_map:
            old_entry = existing_map[url]

            # Check if anything changed
            if (old_entry["title"] != entry["title"] or
                old_entry["category"] != entry["category"] or
                old_entry["description"] != entry["description"]):

                conflicts.append({
                    "url": url,
                    "old": old_entry,
                    "new": entry
                })
        else:
            existing_map[url] = entry

    # Handle conflicts
    if conflicts and conflict_resolution == "prompt":
        print(f"\n⚠️  Found {len(conflicts)} conflicting entries:\n")

        for i, conflict in enumerate(conflicts, 1):
            print(f"Conflict {i}/{len(conflicts)}: {conflict['url']}")
            print(f"  OLD: [{conflict['old']['category']}] {conflict['old']['title']}")
            print(f"  NEW: [{conflict['new']['category']}] {conflict['new']['title']}")

            choice = input("  Keep (o)ld, (n)ew, or (s)kip? [o/n/s]: ").strip().lower()

            if choice == "n":
                existing_map[conflict["url"]] = conflict["new"]
            elif choice == "s":
                pass  # Keep old by default
            # else keep old

    elif conflicts and conflict_resolution == "keep-new":
        for conflict in conflicts:
            existing_map[conflict["url"]] = conflict["new"]

    # conflict_resolution == "keep-old" does nothing

    return list(existing_map.values()), len(conflicts)


def save_json(entries, output_file):
    """Save entries as JSON."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved JSON: {output_file} ({len(entries)} entries)")


def save_csv(entries, output_file):
    """Save entries as CSV."""
    if not entries:
        return

    fieldnames = ["url", "title", "category", "description", "date_added", "icon", "alive"]

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)

    print(f"✓ Saved CSV: {output_file} ({len(entries)} entries)")


def main():
    parser = argparse.ArgumentParser(
        description="Convert browser bookmarks to machine-readable index",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse bookmark file
  %(prog)s bookmarks.html

  # Specify output location
  %(prog)s bookmarks.html -o output.json

  # Merge into existing index
  %(prog)s bookmarks.html -o index.json --merge

  # Check URL liveness (slow)
  %(prog)s bookmarks.html --check-alive

  # Handle conflicts automatically
  %(prog)s bookmarks.html -o index.json --merge --keep-new
        """
    )

    parser.add_argument("input", help="HTML bookmark file to parse")
    parser.add_argument("-o", "--output", help="Output file path (default: bookmarks-index.json)")
    parser.add_argument("--format", choices=["json", "csv", "both"], default="json",
                        help="Output format (default: json)")
    parser.add_argument("--merge", action="store_true",
                        help="Merge with existing index file")
    parser.add_argument("--keep-old", action="store_true",
                        help="On merge conflict, keep old entry (default: prompt)")
    parser.add_argument("--keep-new", action="store_true",
                        help="On merge conflict, keep new entry (default: prompt)")
    parser.add_argument("--check-alive", action="store_true",
                        help="Check URL liveness via HEAD request (adds latency)")
    parser.add_argument("--stats", action="store_true",
                        help="Print statistics only, don't save")

    args = parser.parse_args()

    # Validate input file
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)

    # Determine output file
    if args.output:
        output_file = args.output
    else:
        output_file = "bookmarks-index.json"

    # Parse bookmarks
    print(f"📖 Parsing: {args.input}")
    entries = parse_bookmarks(args.input)
    print(f"✓ Parsed {len(entries)} entries")

    # Check liveness if requested
    if args.check_alive:
        if not REQUESTS_AVAILABLE:
            print("⚠️  Warning: requests library not available, skipping liveness check")
        else:
            print(f"🔍 Checking URL liveness (this may take a while)...")
            for i, entry in enumerate(entries, 1):
                alive = check_url_alive(entry["url"])
                entry["alive"] = alive
                if (i % 10 == 0) or (i == len(entries)):
                    print(f"  Progress: {i}/{len(entries)}")

    # Handle merge
    if args.merge and Path(output_file).exists():
        print(f"🔄 Merging with existing index: {output_file}")

        with open(output_file, "r", encoding="utf-8") as f:
            existing = json.load(f)

        conflict_resolution = "keep-old" if args.keep_old else ("keep-new" if args.keep_new else "prompt")
        entries, conflict_count = merge_entries(existing, entries, conflict_resolution)

        if conflict_count > 0:
            print(f"✓ Resolved {conflict_count} conflicts")

    # Print statistics
    categories = {}
    for entry in entries:
        cat = entry["category"]
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\n📊 Statistics:")
    print(f"  Total entries: {len(entries)}")
    print(f"  Categories: {len(categories)}")

    if args.check_alive and REQUESTS_AVAILABLE:
        alive_count = sum(1 for e in entries if e.get("alive") == True)
        dead_count = sum(1 for e in entries if e.get("alive") == False)
        print(f"  Alive URLs: {alive_count}")
        print(f"  Dead URLs: {dead_count}")

    if args.stats:
        print("\nTop categories:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:10]:
            print(f"  {cat}: {count}")
        sys.exit(0)

    # Save output
    print(f"\n💾 Saving output...")

    if args.format == "json" or args.format == "both":
        save_json(entries, output_file)

    if args.format == "csv" or args.format == "both":
        csv_file = output_file.replace(".json", ".csv") if output_file.endswith(".json") else output_file + ".csv"
        save_csv(entries, csv_file)

    print(f"\n✅ Complete!")


if __name__ == "__main__":
    main()
