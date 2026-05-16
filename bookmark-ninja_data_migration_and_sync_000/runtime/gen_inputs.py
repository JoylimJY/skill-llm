#!/usr/bin/env python3
"""
Generate the sandbox workspace for the Bookmark Ninja legal research task.
Produces:
  - bookmark-parser.py  (the actual skill script, pre-existing)
  - attorney_bookmarks_q1.html  (first team member's export, older)
  - attorney_bookmarks_q2.html  (second team member's export, newer, with conflicts)
  - Various distractor files
"""

import os
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# ── 1. The actual bookmark-parser.py skill script ────────────────────────────
PARSER_SCRIPT = r'''#!/usr/bin/env python3
"""Bookmark Ninja v1.0.0 — bookmark-parser.py"""
import argparse, csv, json, os, sys
from datetime import datetime
from html.parser import HTMLParser

class BookmarkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.bookmarks = []
        self._stack = []          # folder name stack
        self._in_a = False
        self._current = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h3":
            self._stack.append("")   # placeholder; filled by handle_data
            self._in_h3 = True
        elif tag == "a":
            self._in_a = True
            add_date = attrs.get("add_date", "")
            try:
                ts = int(add_date)
                iso = datetime.utcfromtimestamp(ts).isoformat()
            except (ValueError, TypeError, OSError):
                iso = None
            self._current = {
                "url": attrs.get("href", ""),
                "title": "",
                "category": " > ".join(f for f in self._stack if f),
                "description": attrs.get("shortcuturl", attrs.get("description", "")),
                "date_added": iso,
                "icon": attrs.get("icon_uri", attrs.get("icon", "")),
                "alive": None,
            }
        elif tag == "dl":
            pass  # depth increases implicitly via H3 pushes

    def handle_endtag(self, tag):
        if tag == "h3":
            self._in_h3 = False
        elif tag == "a":
            if self._current.get("url"):
                self.bookmarks.append(dict(self._current))
            self._in_a = False
            self._current = {}
        elif tag == "dl":
            if self._stack:
                self._stack.pop()

    def handle_data(self, data):
        if hasattr(self, "_in_h3") and self._in_h3 and self._stack:
            self._stack[-1] = data.strip()
        elif self._in_a:
            self._current["title"] = data.strip()


def load_html(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    p = BookmarkParser()
    p.feed(raw)
    return p.bookmarks


def check_alive(bookmarks):
    try:
        import requests
    except ImportError:
        print("WARNING: requests library not available; skipping liveness check", file=sys.stderr)
        return bookmarks
    for b in bookmarks:
        try:
            r = requests.head(b["url"], timeout=5, allow_redirects=True)
            b["alive"] = r.status_code < 400
        except Exception:
            b["alive"] = False
    return bookmarks


def save_json(bookmarks, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bookmarks, f, indent=2, ensure_ascii=False)


def save_csv(bookmarks, path):
    fields = ["url", "title", "category", "description", "date_added", "icon", "alive"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(bookmarks)


def merge_indexes(existing_path, new_bookmarks, keep_policy):
    """Returns merged list. keep_policy: 'old', 'new', or 'prompt'."""
    try:
        with open(existing_path, encoding="utf-8") as f:
            existing = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing = []

    existing_map = {b["url"]: b for b in existing}
    result = list(existing)

    for nb in new_bookmarks:
        url = nb["url"]
        if url not in existing_map:
            result.append(nb)
        else:
            ob = existing_map[url]
            differs = (ob.get("title") != nb.get("title") or
                       ob.get("category") != nb.get("category") or
                       ob.get("description") != nb.get("description"))
            if not differs:
                continue  # identical, skip
            if keep_policy == "new":
                idx = next(i for i, b in enumerate(result) if b["url"] == url)
                result[idx] = nb
            elif keep_policy == "old":
                pass  # keep existing
            else:
                print(f"CONFLICT for {url}")
                print(f"  OLD: {ob}")
                print(f"  NEW: {nb}")
                choice = input("Keep [o]ld / [n]ew / [s]kip? ").strip().lower()
                if choice == "n":
                    idx = next(i for i, b in enumerate(result) if b["url"] == url)
                    result[idx] = nb
                elif choice == "s":
                    result = [b for b in result if b["url"] != url]
    return result


def print_stats(bookmarks):
    from collections import Counter
    print(f"Total entries : {len(bookmarks)}")
    cats = [b["category"] for b in bookmarks]
    uniq_cats = set(cats)
    print(f"Category count: {len(uniq_cats)}")
    top = Counter(cats).most_common(10)
    print("Top 10 categories:")
    for cat, cnt in top:
        print(f"  {cnt:4d}  {cat or '(root)'}")
    alive = sum(1 for b in bookmarks if b.get("alive") is True)
    dead  = sum(1 for b in bookmarks if b.get("alive") is False)
    if alive + dead:
        print(f"Alive: {alive}  Dead: {dead}")


def main():
    ap = argparse.ArgumentParser(description="Convert browser bookmarks to machine-readable index")
    ap.add_argument("input", help="HTML bookmark file to parse")
    ap.add_argument("-o", "--output", default="bookmarks-index.json", help="Output file path (default: bookmarks-index.json)")
    ap.add_argument("--format", choices=["json", "csv", "both"], default="json", help="Output format (default: json)")
    ap.add_argument("--merge", action="store_true", help="Merge with existing index file")
    ap.add_argument("--keep-old", action="store_true", help="On merge conflict, keep old entry")
    ap.add_argument("--keep-new", action="store_true", help="On merge conflict, keep new entry")
    ap.add_argument("--check-alive", action="store_true", help="Check URL liveness via HEAD request")
    ap.add_argument("--stats", action="store_true", help="Print statistics only, don't save")
    args = ap.parse_args()

    bookmarks = load_html(args.input)

    if args.check_alive:
        bookmarks = check_alive(bookmarks)

    if args.stats:
        print_stats(bookmarks)
        return

    if args.merge:
        policy = "new" if args.keep_new else ("old" if args.keep_old else "prompt")
        bookmarks = merge_indexes(args.output, bookmarks, policy)

    # Determine base path (strip .json or .csv extension for --format both)
    base = args.output
    for ext in (".json", ".csv"):
        if base.endswith(ext):
            base = base[:-len(ext)]
            break

    if args.format in ("json", "both"):
        save_json(bookmarks, base + ".json")
        print(f"Saved JSON → {base}.json  ({len(bookmarks)} entries)")
    if args.format in ("csv", "both"):
        save_csv(bookmarks, base + ".csv")
        print(f"Saved CSV  → {base}.csv  ({len(bookmarks)} entries)")


if __name__ == "__main__":
    main()
'''

with open(os.path.join(WORKSPACE, "bookmark-parser.py"), "w") as f:
    f.write(PARSER_SCRIPT)

# ── 2. Q1 bookmarks (older, baseline) ────────────────────────────────────────
# attorney_bookmarks_q1.html: 12 bookmarks across 4 legal categories

Q1_HTML = textwrap.dedent("""\
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks Menu</H1>
<DL><p>
    <DT><H3 ADD_DATE="1680000000" LAST_MODIFIED="1680000000">Legal</H3>
    <DL><p>
        <DT><H3 ADD_DATE="1680000001" LAST_MODIFIED="1680000001">Case Law</H3>
        <DL><p>
            <DT><H3 ADD_DATE="1680000002" LAST_MODIFIED="1680000002">Federal</H3>
            <DL><p>
                <DT><A HREF="https://www.courtlistener.com/" ADD_DATE="1680100000" SHORTCUTURL="">CourtListener — Free Legal Research</A>
                <DT><A HREF="https://www.law.cornell.edu/supremecourt/text/home" ADD_DATE="1680101000" SHORTCUTURL="Supreme Court opinions archive">Cornell LII — Supreme Court</A>
                <DT><A HREF="https://cases.justia.com/" ADD_DATE="1680102000" SHORTCUTURL="">Justia Case Law Database</A>
            </DL><p>
            <DT><H3 ADD_DATE="1680000003" LAST_MODIFIED="1680000003">State</H3>
            <DL><p>
                <DT><A HREF="https://casetext.com/" ADD_DATE="1680103000" SHORTCUTURL="AI-assisted legal research">Casetext Legal Research</A>
                <DT><A HREF="https://www.leagle.com/" ADD_DATE="1680104000" SHORTCUTURL="">Leagle — Case Law Search</A>
            </DL><p>
        </DL><p>
        <DT><H3 ADD_DATE="1680000004" LAST_MODIFIED="1680000004">Statutes</H3>
        <DL><p>
            <DT><A HREF="https://uscode.house.gov/" ADD_DATE="1680105000" SHORTCUTURL="Official US Code">US Code — Office of the Law Revision Counsel</A>
            <DT><A HREF="https://www.govinfo.gov/app/collection/cfr" ADD_DATE="1680106000" SHORTCUTURL="">Code of Federal Regulations — GovInfo</A>
        </DL><p>
    </DL><p>
    <DT><H3 ADD_DATE="1680000010" LAST_MODIFIED="1680000010">Research Tools</H3>
    <DL><p>
        <DT><H3 ADD_DATE="1680000011" LAST_MODIFIED="1680000011">Citation</H3>
        <DL><p>
            <DT><A HREF="https://www.citationmachine.net/" ADD_DATE="1680200000" SHORTCUTURL="">Citation Machine — Legal Style</A>
            <DT><A HREF="https://guides.lib.uchicago.edu/bluebook" ADD_DATE="1680201000" SHORTCUTURL="Bluebook citation guide">UChicago — Bluebook Reference</A>
        </DL><p>
        <DT><H3 ADD_DATE="1680000012" LAST_MODIFIED="1680000012">PACER</H3>
        <DL><p>
            <DT><A HREF="https://pacer.uscourts.gov/" ADD_DATE="1680202000" SHORTCUTURL="Federal court records system">PACER — Federal Court Records</A>
            <DT><A HREF="https://pcl.uscourts.gov/" ADD_DATE="1680203000" SHORTCUTURL="">PACER Case Locator</A>
        </DL><p>
    </DL><p>
</DL><p>
""")

with open(os.path.join(WORKSPACE, "attorney_bookmarks_q1.html"), "w", encoding="utf-8") as f:
    f.write(Q1_HTML)

# ── 3. Q2 bookmarks (newer, with conflicts + new entries) ────────────────────
# Conflicts: CourtListener (title changed), Casetext (description changed)
# New entries: 3 additional bookmarks in new categories

Q2_HTML = textwrap.dedent("""\
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks Menu</H1>
<DL><p>
    <DT><H3 ADD_DATE="1700000000" LAST_MODIFIED="1700000000">Legal</H3>
    <DL><p>
        <DT><H3 ADD_DATE="1700000001" LAST_MODIFIED="1700000001">Case Law</H3>
        <DL><p>
            <DT><H3 ADD_DATE="1700000002" LAST_MODIFIED="1700000002">Federal</H3>
            <DL><p>
                <DT><A HREF="https://www.courtlistener.com/" ADD_DATE="1700100000" SHORTCUTURL="Updated 2025 — includes PACER integration">CourtListener — Free Legal Research (Updated)</A>
                <DT><A HREF="https://www.law.cornell.edu/supremecourt/text/home" ADD_DATE="1680101000" SHORTCUTURL="Supreme Court opinions archive">Cornell LII — Supreme Court</A>
                <DT><A HREF="https://cases.justia.com/" ADD_DATE="1680102000" SHORTCUTURL="">Justia Case Law Database</A>
            </DL><p>
            <DT><H3 ADD_DATE="1700000003" LAST_MODIFIED="1700000003">State</H3>
            <DL><p>
                <DT><A HREF="https://casetext.com/" ADD_DATE="1700103000" SHORTCUTURL="AI-assisted legal research — now with CoCounsel">Casetext Legal Research</A>
                <DT><A HREF="https://www.leagle.com/" ADD_DATE="1680104000" SHORTCUTURL="">Leagle — Case Law Search</A>
            </DL><p>
        </DL><p>
        <DT><H3 ADD_DATE="1700000004" LAST_MODIFIED="1700000004">Statutes</H3>
        <DL><p>
            <DT><A HREF="https://uscode.house.gov/" ADD_DATE="1680105000" SHORTCUTURL="Official US Code">US Code — Office of the Law Revision Counsel</A>
            <DT><A HREF="https://www.govinfo.gov/app/collection/cfr" ADD_DATE="1680106000" SHORTCUTURL="">Code of Federal Regulations — GovInfo</A>
        </DL><p>
        <DT><H3 ADD_DATE="1700000020" LAST_MODIFIED="1700000020">Discovery</H3>
        <DL><p>
            <DT><A HREF="https://www.relativity.com/" ADD_DATE="1700300000" SHORTCUTURL="eDiscovery platform">Relativity — eDiscovery Platform</A>
            <DT><A HREF="https://logikcull.com/" ADD_DATE="1700301000" SHORTCUTURL="Cloud-based eDiscovery">Logikcull — Smart eDiscovery</A>
        </DL><p>
    </DL><p>
    <DT><H3 ADD_DATE="1700000010" LAST_MODIFIED="1700000010">Research Tools</H3>
    <DL><p>
        <DT><H3 ADD_DATE="1700000011" LAST_MODIFIED="1700000011">Citation</H3>
        <DL><p>
            <DT><A HREF="https://www.citationmachine.net/" ADD_DATE="1680200000" SHORTCUTURL="">Citation Machine — Legal Style</A>
            <DT><A HREF="https://guides.lib.uchicago.edu/bluebook" ADD_DATE="1680201000" SHORTCUTURL="Bluebook citation guide">UChicago — Bluebook Reference</A>
        </DL><p>
        <DT><H3 ADD_DATE="1700000012" LAST_MODIFIED="1700000012">PACER</H3>
        <DL><p>
            <DT><A HREF="https://pacer.uscourts.gov/" ADD_DATE="1680202000" SHORTCUTURL="Federal court records system">PACER — Federal Court Records</A>
            <DT><A HREF="https://pcl.uscourts.gov/" ADD_DATE="1680203000" SHORTCUTURL="">PACER Case Locator</A>
        </DL><p>
    </DL><p>
</DL><p>
""")

with open(os.path.join(WORKSPACE, "attorney_bookmarks_q2.html"), "w", encoding="utf-8") as f:
    f.write(Q2_HTML)

# ── 4. Distractor files ───────────────────────────────────────────────────────
os.makedirs(os.path.join(WORKSPACE, "case_files", "2024", "discovery"), exist_ok=True)
os.makedirs(os.path.join(WORKSPACE, "case_files", "2023", "motions"), exist_ok=True)
os.makedirs(os.path.join(WORKSPACE, "templates"), exist_ok=True)
os.makedirs(os.path.join(WORKSPACE, "exports", "raw"), exist_ok=True)
os.makedirs(os.path.join(WORKSPACE, "scripts", "utils"), exist_ok=True)

distractor_files = {
    "case_files/2024/discovery/exhibit_list.txt": "Exhibit A: Contract dated 2022-03-01\nExhibit B: Email chain 2023-06-15\n",
    "case_files/2024/discovery/deposition_notes.md": "# Deposition Notes\n- Witness A confirmed timeline\n- Cross-ref exhibit B\n",
    "case_files/2023/motions/motion_to_dismiss.docx.txt": "[Motion to Dismiss - see attached PDF]\n",
    "case_files/2023/motions/summary_judgment_draft.txt": "DRAFT — NOT FINAL\nSummary Judgment Motion v0.3\n",
    "templates/retainer_agreement_template.txt": "THIS RETAINER AGREEMENT is entered into as of __DATE__\n",
    "templates/discovery_request_template.txt": "REQUEST FOR PRODUCTION NO. 1:\nAll documents relating to...\n",
    "exports/raw/chrome_export_backup.txt": "This is NOT a valid bookmark file - binary garbled content\n\x00\x01\x02",
    "exports/raw/README_IGNORE.txt": "Old raw exports - do not process these files directly\n",
    "scripts/utils/fetch_pacer.py": "# TODO: PACER automation helper\nprint('stub')\n",
    "scripts/utils/cite_checker.py": "# Citation format verifier\ndef check(cite): return True\n",
    ".old_index_backup.json": '[{"url":"https://old.example.com","title":"Old entry","category":"Misc"}]\n',
}

for rel_path, content in distractor_files.items():
    full = os.path.join(WORKSPACE, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", errors="ignore") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"  attorney_bookmarks_q1.html — Q1 baseline export (12 bookmarks)")
print(f"  attorney_bookmarks_q2.html — Q2 export with conflicts + new entries (14 bookmarks)")
print(f"  bookmark-parser.py — skill script")
print(f"  + {len(distractor_files)} distractor files")