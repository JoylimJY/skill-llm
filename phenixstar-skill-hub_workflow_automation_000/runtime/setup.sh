#!/usr/bin/env bash
set -e

WORKSPACE=/workspace

# ── skill-hub-search.py mock ─────────────────────────────────────────────────
cat > "$WORKSPACE/scripts/skill-hub-search.py" << 'PYEOF'
#!/usr/bin/env python3
"""Mock skill-hub-search.py"""
import argparse, json, sys
from pathlib import Path

CATALOG = Path("/workspace/catalog/catalog.json")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default=None)
    parser.add_argument("--category", default=None)
    parser.add_argument("--min-score", type=int, default=0)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--installed", action="store_true")
    parser.add_argument("--not-installed", action="store_true")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    skills = json.loads(CATALOG.read_text())

    if args.category:
        skills = [s for s in skills if s["category"].lower() == args.category.lower()]
    if args.query:
        q = args.query.lower()
        skills = [s for s in skills if q in s["name"].lower() or q in s["description"].lower() or q in s["slug"].lower()]
    if args.installed:
        skills = [s for s in skills if s["installed"]]
    if args.not_installed:
        skills = [s for s in skills if not s["installed"]]
    skills = [s for s in skills if s["score"] >= args.min_score]
    skills = skills[:args.limit]

    for s in skills:
        tier = "Trusted" if s["score"] >= 85 else ("Good" if s["score"] >= 60 else ("Unvetted" if s["score"] >= 30 else "Caution"))
        print(f"[{tier}] {s['slug']} (score={s['score']}, category={s['category']}): {s['description']}")

    if not skills:
        print("No skills found matching criteria.")

if __name__ == "__main__":
    main()
PYEOF

# ── skill-hub-vet.py mock ────────────────────────────────────────────────────
cat > "$WORKSPACE/scripts/skill-hub-vet.py" << 'PYEOF'
#!/usr/bin/env python3
"""Mock skill-hub-vet.py"""
import argparse, json, sys
from pathlib import Path

CATALOG = Path("/workspace/catalog/catalog.json")
VET_DATA = Path("/workspace/catalog/vet_data.json")
VET_RESULTS_DIR = Path("/workspace/catalog/vet-results")

def vet_slug(slug, vet_data):
    if slug not in vet_data:
        print(f"[ERROR] Slug '{slug}' not found in vet database.")
        return None
    result = vet_data[slug]
    status = "PASS" if result["passed"] else "FAIL"
    print(f"=== Vetting: {slug} ===")
    print(f"Status: {status}")
    print(f"Credibility Score: {result['score']}")
    print("Code Checks:")
    for k, v in result["code_checks"].items():
        flag = "⚠ DETECTED" if v else "✓ clear"
        print(f"  {k}: {flag}")
    print("NLP/Prompt Checks:")
    for k, v in result["nlp_checks"].items():
        flag = "⚠ DETECTED" if v else "✓ clear"
        print(f"  {k}: {flag}")
    print(f"Summary: {result['summary']}")
    print()
    out_path = VET_RESULTS_DIR / f"{slug}.json"
    out_path.write_text(json.dumps(result, indent=2))
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default=None)
    parser.add_argument("--all-installed", action="store_true")
    parser.add_argument("--category", default=None)
    parser.add_argument("--top", type=int, default=None)
    args = parser.parse_args()

    vet_data = json.loads(VET_DATA.read_text())
    catalog = json.loads(CATALOG.read_text())

    slugs_to_vet = []
    if args.slug:
        slugs_to_vet = [args.slug]
    elif args.all_installed:
        slugs_to_vet = [s["slug"] for s in catalog if s["installed"]]
    elif args.category:
        slugs_to_vet = [s["slug"] for s in catalog if s["category"].lower() == args.category.lower()]
    elif args.top:
        slugs_to_vet = [s["slug"] for s in catalog if s["slug"] in vet_data][:args.top]

    for slug in slugs_to_vet:
        vet_slug(slug, vet_data)

if __name__ == "__main__":
    main()
PYEOF

# ── skill-hub-table-export.py mock ──────────────────────────────────────────
cat > "$WORKSPACE/scripts/skill-hub-table-export.py" << 'PYEOF'
#!/usr/bin/env python3
"""Mock skill-hub-table-export.py"""
import argparse, json
from pathlib import Path

CATALOG = Path("/workspace/catalog/catalog.json")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", default="terminal", choices=["terminal", "markdown"])
    parser.add_argument("--category", default=None)
    args = parser.parse_args()

    skills = json.loads(CATALOG.read_text())
    if args.category:
        skills = [s for s in skills if s["category"].lower() == args.category.lower()]

    if args.format == "markdown":
        print(f"# Skill Catalog{' - ' + args.category if args.category else ''}")
        print()
        print("| Slug | Name | Category | Score | Tier | Description |")
        print("|------|------|----------|-------|------|-------------|")
        for s in skills:
            tier = "Trusted" if s["score"] >= 85 else ("Good" if s["score"] >= 60 else ("Unvetted" if s["score"] >= 30 else "Caution"))
            print(f"| {s['slug']} | {s['name']} | {s['category']} | {s['score']} | {tier} | {s['description']} |")
    else:
        header = f"{'Slug':<30} {'Name':<25} {'Category':<12} {'Score':>6} {'Tier':<10} Description"
        print(header)
        print("-" * len(header))
        for s in skills:
            tier = "Trusted" if s["score"] >= 85 else ("Good" if s["score"] >= 60 else ("Unvetted" if s["score"] >= 30 else "Caution"))
            print(f"{s['slug']:<30} {s['name']:<25} {s['category']:<12} {s['score']:>6} {tier:<10} {s['description']}")

if __name__ == "__main__":
    main()
PYEOF

# ── skill-hub-status.py mock ─────────────────────────────────────────────────
cat > "$WORKSPACE/scripts/skill-hub-status.py" << 'PYEOF'
#!/usr/bin/env python3
"""Mock skill-hub-status.py"""
import json
from pathlib import Path

CATALOG = Path("/workspace/catalog/catalog.json")
skills = json.loads(CATALOG.read_text())
installed = [s for s in skills if s["installed"]]
total = len(skills)
inst_count = len(installed)
unvetted = [s for s in skills if s["score"] < 60]
print(f"=== Skill Hub Status ===")
print(f"Total catalog: {total} skills")
print(f"Installed: {inst_count}")
print(f"Unvetted (score < 60): {len(unvetted)}")
print(f"Coverage: {inst_count/total*100:.1f}%")
PYEOF

# ── skill-hub-sync.py mock ───────────────────────────────────────────────────
cat > "$WORKSPACE/scripts/skill-hub-sync.py" << 'PYEOF'
#!/usr/bin/env python3
"""Mock skill-hub-sync.py"""
print("Syncing catalog from GitHub awesome-list...")
print("No changes detected. Catalog is up to date.")
PYEOF

# ── skill-hub-quick-check.py mock ───────────────────────────────────────────
cat > "$WORKSPACE/scripts/skill-hub-quick-check.py" << 'PYEOF'
#!/usr/bin/env python3
"""Mock skill-hub-quick-check.py"""
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--sync", action="store_true")
parser.add_argument("--query", default=None)
args = parser.parse_args()
print("Quick check: No new skills added since last sync (2024-01-10T12:00:07Z).")
if args.query:
    print(f"No new skills matching '{args.query}' found.")
PYEOF

chmod +x "$WORKSPACE/scripts/"*.py

echo "Mock scripts installed and ready."